"""Exact detection probabilities over a recorded transition table.

No backend imports. Episodes stop at their first oracle violation, exactly as in
the campaign implementations, so only violation-free transitions continue.
"""
from dataclasses import replace
from fractions import Fraction

from integrations.salon.model import ACTORS, OPERATIONS, RESOURCES
from .table import ACTIONS, INDEX

FIELDS = {"operation": OPERATIONS, "actor": ACTORS, "resource": RESOURCES}

def matches(target, violations):
    return bool(violations) if target == "ANY" else target in violations

class Table:
    def __init__(self, raw):
        self.edges = {int(k): [(row[0], tuple(row[2])) for row in v] for k, v in raw["edges"].items()}
        self.states = raw["states"]

    def step(self, state, action):
        return self.edges[state][INDEX[action]]

def shortest_witness(table, target):
    """Breadth-first shortest action sequence whose last call violates `target`.

    Returns (depth, witness, count) where count is the number of distinct action
    sequences of that depth that are violation-free before their final call.
    """
    parents = {0: None}
    level, depth = {0: 1}, 0
    while level:
        depth += 1
        hits, following = 0, {}
        witness = None
        for state, paths in level.items():
            for index, (successor, violations) in enumerate(table.edges[state]):
                if violations:
                    if matches(target, violations):
                        hits += paths
                        if witness is None:
                            witness = _path(parents, state) + [ACTIONS[index]]
                    continue
                if successor not in parents:
                    parents[successor] = (state, index)
                    following[successor] = 0
                if successor in following:
                    following[successor] += paths
        if hits:
            return depth, witness, hits
        level = {s: n for s, n in following.items() if s in table.edges}
    return None, None, 0

def _path(parents, state):
    path = []
    while parents[state] is not None:
        state, index = parents[state]
        path.append(ACTIONS[index])
    return path[::-1]

def run_program(table, program, target):
    """Deterministic outcome of one episode: (calls, detected)."""
    state = 0
    for calls, action in enumerate(program, 1):
        state, violations = table.step(state, action)
        if violations:
            return calls, matches(target, violations)
    return len(program), False

class Episode:
    """Distribution of one episode: detect[c] and stop[c] for c calls consumed."""

    def __init__(self, depth):
        self.detect = [Fraction(0)] * (depth + 1)
        self.stop = [Fraction(0)] * (depth + 1)

    def add_program(self, table, program, target, weight):
        calls, detected = run_program(table, program, target)
        (self.detect if detected else self.stop)[calls] += weight

    def probability(self):
        return sum(self.detect)

def random_episode(table, target, depth=8):
    """Program length uniform on 1..depth, each action uniform on the finite domain."""
    episode = Episode(depth)
    uniform = Fraction(1, len(ACTIONS))
    for length in range(1, depth + 1):
        mass = {0: Fraction(1, depth)}
        for call in range(1, length + 1):
            following = {}
            for state, p in mass.items():
                for successor, violations in table.edges[state]:
                    q = p * uniform
                    if violations:
                        (episode.detect if matches(target, violations) else episode.stop)[call] += q
                    else:
                        following[successor] = following.get(successor, 0) + q
            mass = following
        episode.stop[length] += sum(mass.values())
    return episode

def extend_episode(table, target, programs, depth=8):
    """Uniform valid prefix followed by a uniform random suffix (seed_extend)."""
    episode = Episode(depth)
    for prefix in programs:
        lengths = range(1, depth - len(prefix) + 1)
        for length in lengths:
            weight = Fraction(1, len(programs) * len(lengths))
            _extend(table, target, prefix, length, weight, episode)
    return episode

def _extend(table, target, prefix, length, weight, episode):
    state = 0
    for calls, action in enumerate(prefix, 1):
        state, violations = table.step(state, action)
        if violations:
            (episode.detect if matches(target, violations) else episode.stop)[calls] += weight
            return
    mass, uniform = {state: weight}, Fraction(1, len(ACTIONS))
    for call in range(len(prefix) + 1, len(prefix) + length + 1):
        following = {}
        for s, p in mass.items():
            for successor, violations in table.edges[s]:
                q = p * uniform
                if violations:
                    (episode.detect if matches(target, violations) else episode.stop)[call] += q
                else:
                    following[successor] = following.get(successor, 0) + q
        mass = following
    episode.stop[len(prefix) + length] += sum(mass.values())

def mutations(source, donor, depth=8):
    """Exact output distribution of integrations.salon.generator.Mutator.mutate."""
    out = []
    n = len(source)
    for index in range(n):
        base = Fraction(1, 6 * n)
        for field, domain in FIELDS.items():
            for value in domain:
                seq = list(source)
                seq[index] = replace(seq[index], **{field: value})
                out.append((seq, base / (3 * len(domain))))
        for action in ACTIONS:
            seq = list(source)
            seq.insert(index, action)
            out.append((seq, base / len(ACTIONS)))
        sizes = range(1, min(3, n - index) + 1)
        for size in sizes:
            seq = list(source)
            seq[index + size:index + size] = seq[index:index + size]
            out.append((seq, base / len(sizes)))
        seq = list(source)
        if n > 1:
            del seq[index]
        out.append((seq, base))
        for other in range(n):
            seq = list(source)
            seq[index], seq[other] = seq[other], seq[index]
            out.append((seq, base / n))
        for start in range(len(donor)):
            sizes = range(1, min(3, len(donor) - start) + 1)
            for size in sizes:
                seq = list(source)
                seq[index:index] = donor[start:start + size]
                out.append((seq, base / (len(donor) * len(sizes))))
    return [(seq[:depth], p) for seq, p in out]

def mutation_episode(table, target, programs, depth=8):
    """Uniform source and donor from the bank, then one generic mutation."""
    episode = Episode(depth)
    pair = Fraction(1, len(programs) ** 2)
    for source in programs:
        for donor in programs:
            for program, p in mutations(source, donor, depth):
                episode.add_program(table, program, target, pair * p)
    return episode

def detection_curve(episode, budget, prefix=()):
    """P(first detection at call t) for t <= budget, after deterministic prefix episodes.

    `prefix` holds (calls, detected) outcomes executed before i.i.d. episodes,
    such as the charged valid bootstrap.
    """
    first = [0.0] * (budget + 1)
    detect = [float(p) for p in episode.detect]
    stop = [float(p) for p in episode.stop]
    offset = 0
    for calls, detected in prefix:
        if offset + calls > budget:
            return first
        if detected:
            first[offset + calls] = 1.0
            return first
        offset += calls
    boundary = [0.0] * (budget + 1)
    boundary[offset] = 1.0
    for n in range(offset, budget):
        p = boundary[n]
        if not p:
            continue
        for c in range(1, len(detect)):
            if n + c > budget:
                break
            first[n + c] += p * detect[c]
            boundary[n + c] += p * stop[c]
    return first

def summary(first, budget):
    """Detection probability and expected capped first-failure call index."""
    detected = sum(first)
    capped = sum(t * p for t, p in enumerate(first)) + budget * (1 - detected)
    return float(detected), float(capped)
