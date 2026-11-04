"""crAPI campaign loop: same three generators and stopping rule as the salon study."""
from dataclasses import asdict
import random

from .generator import Mutator
from .model import ACTIONS, legitimate_seeds, violations

MODES = ("random", "seed_extend", "sequence_uniform")

def _program(mode, bank, rng, mutator, depth, seed_index):
    if mode == "random":
        return [rng.choice(ACTIONS) for _ in range(rng.randint(1, depth))]
    if seed_index < len(bank):
        return list(bank[seed_index])  # charged bootstrap of the valid bank
    if mode == "seed_extend":
        prefix = list(rng.choice(bank))
        if len(prefix) >= depth:
            return prefix[:depth]
        suffix = [rng.choice(ACTIONS) for _ in range(rng.randint(1, depth - len(prefix)))]
        return prefix + suffix
    program, _ = mutator.mutate(rng.choice(bank), rng.choice(bank))
    return program

def campaign(adapter, mode, target, seed, budget, depth=8):
    if mode not in MODES:
        raise ValueError("unknown mode")
    rng = random.Random(seed)
    mutator = Mutator(rng, depth)
    bank = legitimate_seeds() if mode != "random" else []
    calls, seed_index, witness = 0, 0, None
    while calls < budget and witness is None:
        program = _program(mode, bank, rng, mutator, depth, seed_index)
        if mode != "random" and seed_index < len(bank):
            seed_index += 1
        adapter.reset()
        trace = []
        for action in program:
            if calls == budget:
                break
            before = adapter.snapshot()
            allowed = adapter.execute(action)["allowed"]
            after = adapter.snapshot()
            errors = violations(before, action, allowed, after)
            calls += 1
            trace.append({"action": asdict(action), "allowed": allowed, "violations": errors})
            if target in errors:
                witness = trace
                break
            if errors:
                break
    return {"mode": mode, "target": target, "seed": seed, "budget": budget,
            "calls": calls, "detected": witness is not None,
            "trace": witness or []}
