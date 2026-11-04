"""Exploratory: per-episode reach probabilities in the document benchmark (Monte Carlo).

Random: one legacy random episode (budget = depth = 20).
Mutation: one SequenceMutator episode from a uniform valid source and donor, as in
sequence_uniform after its bootstrap. Both use the unchanged campaign components.
Usage: python scripts/analyze_document_reach.py [samples]
"""
import gzip
import json
from pathlib import Path
import random
import sys
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from fuzzlab.fuzzer import Campaign
from fuzzlab.model import MUTANTS
from fuzzlab.mutation import SequenceMutator, legitimate_seeds
from fuzzlab.oracle import inspect
from fuzzlab.reserved import RESERVED, gateway

DEPTH, BUDGET = 20, 3000

def random_episode(mutant, seed):
    with patch("fuzzlab.fuzzer.Gateway", gateway):
        row = Campaign("random", mutant, seed, DEPTH, DEPTH).run()
    return row["detected"], row["calls"]

def mutation_episode(mutant, rng, mutator, seeds):
    source, donor = list(rng.choice(seeds)), rng.choice(seeds)
    program, _ = mutator.mutate(source, donor)
    service = gateway(mutant)
    for calls, action in enumerate(program, 1):
        before = service.state.snapshot()
        response = service.execute(action)
        if inspect(before, action, response, service.state.snapshot()):
            return True, calls
    return False, len(program)

def bootstrap_calls(seeds):
    return sum(len(p) for p in seeds)

def measure(job):
    mutant, samples = job
    seeds = [p[:DEPTH] for p in legitimate_seeds()]
    rnd = [random_episode(mutant, 10_000_000 + i) for i in range(samples)]
    rng = random.Random(f"document-reach:{mutant}")
    mutator = SequenceMutator(rng, DEPTH)
    mut = [mutation_episode(mutant, rng, mutator, seeds) for _ in range(samples)]
    return mutant, rnd, mut, bootstrap_calls(seeds)

def main(samples=4000):
    from multiprocessing import Pool
    samples = int(samples)
    raw = [json.loads(line) for line in gzip.open(ROOT / "results/sequence-v02/raw.jsonl.gz")]
    observed = {}
    for row in raw:
        observed.setdefault((row["mutant"], row["strategy"]), []).append(row["detected"])
    out = []
    with Pool() as pool:
        measured = pool.map(measure, [(m, samples) for m in (*MUTANTS, *RESERVED)])
    for mutant, rnd, mut, boot in measured:
        p_random = sum(d for d, _ in rnd) / samples
        p_mutation = sum(d for d, _ in mut) / samples
        mean_mutation_calls = sum(c for _, c in mut) / samples
        episodes_random = BUDGET / DEPTH
        episodes_mutation = (BUDGET - boot) / mean_mutation_calls
        out.append({"mutant": mutant, "samples": samples,
                    "p_random_episode": p_random, "p_mutation_episode": p_mutation,
                    "mean_mutation_episode_calls": round(mean_mutation_calls, 3),
                    "approx_p_random_3000": 1 - (1 - p_random) ** episodes_random,
                    "approx_p_mutation_3000": 1 - (1 - p_mutation) ** episodes_mutation,
                    "observed_random": sum(observed[mutant, "random"]),
                    "observed_sequence_uniform": sum(observed[mutant, "sequence_uniform"]),
                    "runs": len(observed[mutant, "random"])})
        r = out[-1]
        print(f'{mutant:24} p_rand {p_random:.4f} p_mut {p_mutation:.4f} '
              f'-> pred {r["approx_p_random_3000"]*10:4.1f} vs {r["approx_p_mutation_3000"]*10:4.1f} '
              f'| obs {r["observed_random"]} vs {r["observed_sequence_uniform"]}', flush=True)
    target = ROOT / "results/history-depth/document-reach.json"
    target.write_text(json.dumps({"status": "exploratory Monte Carlo; legacy random uses its own action sampler",
                                  "cells": out}, indent=1, sort_keys=True) + "\n")

if __name__ == "__main__":
    main(*sys.argv[1:])
