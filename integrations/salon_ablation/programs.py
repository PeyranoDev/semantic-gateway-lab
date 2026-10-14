"""Program selection without oracle, mutant labels or backend imports."""
from dataclasses import asdict
import hashlib
import json
import random
from integrations.salon.generator import Mutator
from integrations.salon.model import legitimate_seeds

MODES = ("random", "random_bootstrap", "seed_replay", "seed_extend",
         "mutation_unseeded", "sequence_uniform", "sequence_enabled", "sequence_enriched")

def bank(mode, seed):
    if mode not in MODES:
        raise ValueError("unknown engine")
    valid = legitimate_seeds()
    if mode != "mutation_unseeded":
        return valid
    # Independent RNG preserves the campaign's mutation RNG initialization.
    rng = random.Random(f"{seed}:salon-ablation-bank-v1")
    mutate = Mutator(rng, 8)
    return [[mutate.random_action() for _ in program] for program in valid]

def bank_digest(programs):
    payload = json.dumps([[asdict(a) for a in p] for p in programs],
                         sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

def next_program(mode, programs, corpus, rng, mutate, depth):
    if mode in ("random", "random_bootstrap"):
        return [mutate.random_action() for _ in range(rng.randint(1, depth))], "random"
    if mode == "seed_replay":
        return list(rng.choice(programs)), "replay"
    if mode == "seed_extend":
        prefix = list(rng.choice(programs))
        if len(prefix) >= depth:
            raise ValueError("seed extension requires depth larger than every seed")
        suffix = [mutate.random_action() for _ in range(rng.randint(1, depth-len(prefix)))]
        return prefix + suffix, "append"
    source = (corpus.select(rng) if mode in ("sequence_enabled", "sequence_enriched")
              and corpus.entries and rng.random() < .8 else rng.choice(programs))
    return mutate.mutate(source, rng.choice(programs))
