"""Bounded counterexample search for action distinguishability of abstractions.

This checks a finite action subalphabet, not the full runtime or LLM safety.
Transitions are executed and independently checked; none is pre-labelled bad.
"""
from collections import deque
from dataclasses import asdict
from .abstraction import abstract, concrete_key
from .backend import Gateway
from .fuzzer import replay
from .model import Action

SUBALPHABET = (Action("initiate_share", target="bob"),
               Action("initiate_share", target="mallory"),
               Action("accept_share", actor="bob"),
               Action("accept_share", actor="mallory"), Action("revoke_share"))

def distinguishability(depth=3):
    if depth < 0:
        raise ValueError("depth must be nonnegative")
    queue = deque([[]])
    seen, states = set(), []
    while queue:
        trace = queue.popleft()
        if replay(trace)["violations"]:
            raise RuntimeError("fixed implementation disagrees with independent oracle")
        g = Gateway()
        for action in trace:
            g.execute(action)
        snapshot = g.state.snapshot()
        key = concrete_key(snapshot)
        if key in seen:
            continue
        seen.add(key)
        outcomes = []
        for action in SUBALPHABET:
            branch = Gateway()
            for prior in trace:
                branch.execute(prior)
            outcomes.append(branch.execute(action)["allowed"])
        states.append((trace, snapshot, outcomes))
        if len(trace) < depth:
            queue.extend(trace + [action] for action in SUBALPHABET)
    collisions = {}
    for mode in ("enabled", "enriched"):
        groups = {}
        witness = None
        for trace, state, outcomes in states:
            key = abstract(state, mode)
            if key in groups:
                previous_trace, previous_outcomes = groups[key]
                for index, (old, new) in enumerate(zip(previous_outcomes, outcomes)):
                    if old != new:
                        witness = {"first_prefix": [asdict(a) for a in previous_trace],
                                   "second_prefix": [asdict(a) for a in trace],
                                   "distinguishing_action": asdict(SUBALPHABET[index]),
                                   "first_allowed": old, "second_allowed": new}
                        break
            else:
                groups[key] = trace, outcomes
            if witness:
                break
        collisions[mode] = witness
    return {"max_depth": depth, "subalphabet_size": len(SUBALPHABET),
            "reachable_states_observed": len(states), "collisions": collisions,
            "scope": "bounded finite subalphabet; no general soundness proof"}
