"""Same campaign mechanics, with explicitly separated initial-bank policies."""
from collections import Counter
from dataclasses import asdict
import random
import time

from fuzzlab.feedback import Corpus
from integrations.salon.feedback import canonical, project
from integrations.salon.generator import Mutator
from integrations.salon.model import Action, PROPERTIES
from integrations.salon.oracle import check
from .programs import MODES, bank, bank_digest, next_program

def matches(target, violations):
    return bool(violations) if target == "ANY" else target in violations

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
        if target and matches(target, violations):
            break
    return trace

def minimize(adapter, program, target):
    current, calls, index = list(program), 0, 0
    while index < len(current):
        candidate = current[:index]+current[index+1:]
        if not candidate:
            index += 1
            continue
        trace = replay(adapter, candidate, target)
        calls += len(trace)
        if any(matches(target, step["violations"]) for step in trace):
            current = candidate[:len(trace)]
            index = 0
        else:
            index += 1
    return current, calls

def campaign(adapter, mode, target, seed, budget, depth=8, capacity=64):
    if (mode not in MODES or target not in (*PROPERTIES, "ANY") or budget < 1
            or depth < 5 or capacity < 1):
        raise ValueError("invalid campaign settings")
    started = time.perf_counter()
    rng = random.Random(seed)
    mutate = Mutator(rng, depth)
    corpus = Corpus(capacity)
    programs = bank(mode, seed)
    calls, episodes, bootstrap_calls = 0, 0, 0
    observed, operator_counts, other_errors = set(), Counter(), Counter()
    witness = None
    seed_index = 0
    while calls < budget and witness is None:
        bootstrap = mode != "random" and seed_index < len(programs)
        if bootstrap:
            program = programs[seed_index]
            seed_index += 1
        else:
            program, operator = next_program(mode, programs, corpus, rng, mutate, depth)
            if mode not in ("random", "random_bootstrap"):
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
            trace.append({"action": asdict(action), "response": response, "before": before,
                          "after": after, "violations": errors})
            other_errors.update(e for e in errors if target != "ANY" and e != target)
            if matches(target, errors):
                witness = trace
                break
            safe = safe and not errors
            if safe and mode in ("sequence_enabled", "sequence_enriched"):
                edge = canonical([project(before, mode), action.operation,
                                  200 <= response["status"] < 300, project(after, mode)])
                corpus.remember(edge, program[:len(trace)])
            if errors:
                break
    minimal_trace, shrink_calls = [], 0
    if witness:
        original = [Action(**step["action"]) for step in witness]
        minimal, shrink_calls = minimize(adapter, original, target)
        minimal_trace = replay(adapter, minimal, target)
        assert any(matches(target, s["violations"]) for s in minimal_trace)
    return {"mode": mode, "target": target, "seed": seed, "budget": budget, "depth": depth,
            "calls": calls, "detected": witness is not None, "right_censored": witness is None,
            "episodes": episodes, "bootstrap_calls": bootstrap_calls,
            "observed_states": len(observed), "corpus_entries": len(corpus.entries),
            "corpus_evictions": corpus.evictions, "operators": dict(operator_counts),
            "other_errors": dict(other_errors), "trace": witness or [],
            "minimal_trace": minimal_trace, "shrink_calls": shrink_calls,
            "elapsed_s": time.perf_counter()-started,
            "initial_bank_sha256": bank_digest(programs)}
