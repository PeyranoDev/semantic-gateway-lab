"""Exploratory search for known properties on one unmodified service version."""
from collections import Counter
from dataclasses import asdict
import random
import time

from fuzzlab.feedback import Corpus
from .feedback import canonical, project
from .generator import Mutator
from .model import PROPERTIES, legitimate_seeds
from .oracle import check

MODES = ("random", "sequence_uniform", "sequence_enabled", "sequence_enriched")

def replay(adapter, program, target=None):
    adapter.reset()
    trace = []
    for action in program:
        before = adapter.snapshot()
        response = adapter.execute(action)
        after = adapter.snapshot()
        violations = check(before, action, response, after)
        trace.append({"action": asdict(action), "response": response, "before": before,
                      "after": after, "violations": violations})
        if target and target in violations:
            break
    return trace

def minimize(adapter, program, target):
    current, calls = list(program), 0
    index = 0
    while index < len(current):
        candidate = current[:index]+current[index+1:]
        if not candidate:
            index += 1
            continue
        trace = replay(adapter, candidate, target)
        calls += len(trace)
        if any(target in step["violations"] for step in trace):
            current = candidate[:len(trace)]
            index = 0
        else:
            index += 1
    return current, calls

def campaign(adapter, mode, target, seed, budget, depth=8, capacity=64):
    if mode not in MODES or target not in PROPERTIES or budget < 1 or depth < 2 or capacity < 1:
        raise ValueError("invalid campaign settings")
    started = time.perf_counter()
    rng = random.Random(seed)
    mutate = Mutator(rng, depth)
    corpus = Corpus(capacity)
    seeds = legitimate_seeds()
    calls, episodes, bootstrap_calls = 0, 0, 0
    observed, operator_counts, other_errors = set(), Counter(), Counter()
    witness = None
    seed_index = 0
    while calls < budget and witness is None:
        bootstrap = mode != "random" and seed_index < len(seeds)
        if bootstrap:
            program = seeds[seed_index]
            seed_index += 1
        elif mode == "random":
            program = [mutate.random_action() for _ in range(rng.randint(1, depth))]
        else:
            source = (corpus.select(rng) if mode in ("sequence_enabled", "sequence_enriched")
                      and corpus.entries and rng.random() < .8 else rng.choice(seeds))
            program, operator = mutate.mutate(source, rng.choice(seeds))
            operator_counts[operator] += 1
        adapter.reset()
        episodes += 1
        trace, safe = [], True
        for action in program:
            if calls == budget:
                break
            before = adapter.snapshot()
            response = adapter.execute(action)
            after = adapter.snapshot()
            errors = check(before, action, response, after)
            calls += 1
            bootstrap_calls += int(bootstrap)
            observed.update((canonical(before), canonical(after)))
            step = {"action": asdict(action), "response": response, "before": before,
                    "after": after, "violations": errors}
            trace.append(step)
            other_errors.update(e for e in errors if e != target)
            if target in errors:
                witness = trace
                break
            safe = safe and not errors
            if safe and mode in ("sequence_enabled", "sequence_enriched"):
                edge = canonical([project(before, mode), action.operation,
                                  200 <= response["status"] < 300, project(after, mode)])
                corpus.remember(edge, program[:len(trace)])
            if errors:
                break  # Other property fails: end episode, continue target campaign.
    minimal, shrink_calls, minimal_trace = [], 0, []
    if witness:
        original = [type(seeds[0][0])(**step["action"]) for step in witness]
        minimal, shrink_calls = minimize(adapter, original, target)
        minimal_trace = replay(adapter, minimal, target)
        if not any(target in step["violations"] for step in minimal_trace):
            raise AssertionError("minimized witness no longer violates target")
    return {"mode": mode, "target": target, "seed": seed, "budget": budget, "depth": depth,
            "calls": calls, "detected": witness is not None, "right_censored": witness is None,
            "episodes": episodes, "bootstrap_calls": bootstrap_calls,
            "observed_states": len(observed), "corpus_entries": len(corpus.entries),
            "corpus_evictions": corpus.evictions, "operators": dict(operator_counts),
            "other_errors": dict(other_errors), "trace": witness or [],
            "minimal_trace": minimal_trace, "shrink_calls": shrink_calls,
            "elapsed_s": time.perf_counter()-started}
