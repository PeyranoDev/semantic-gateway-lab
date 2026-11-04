"""Prospective test: specification-derived predictions for systematic salon mutants.

  python scripts/prospective_salon.py predict   # specification models only; freeze before running
  python scripts/prospective_salon.py run       # real HTTP/SQL campaigns on implementation mutants
  python scripts/prospective_salon.py compare   # frozen predictions versus observed campaigns

Protocol: docs/prospective-protocol.md. Predictions must be committed before `run`.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from integrations.salon.model import legitimate_seeds
from integrations.salon_depth.model import (Table, detection_curve, extend_episode,
                                            mutation_episode, random_episode, run_program,
                                            shortest_witness, summary)
from integrations.salon_prospective.mutants import sites

OUT = ROOT / "results/prospective"
MODES = ("random", "seed_extend", "sequence_uniform")
SEEDS = tuple(range(900, 930))
BUDGET, TARGET = 120, "ANY"

def new_sites():
    return [s["id"] for s in sites() if s["existing_variant"] is None]

def _initial():
    raw = json.loads(gzip.decompress((ROOT / "results/history-depth/tables/fixed.json.gz").read_bytes()))
    return raw["states"][0]

def _predict_site(site_id):
    from integrations.salon_depth.table import explore
    from integrations.salon_prospective.spec import SpecAdapter, mutant_expected
    table = Table(explore(SpecAdapter(mutant_expected(site_id), _initial()), levels=7))
    depth, witness, count = shortest_witness(table, TARGET)
    seeds = legitimate_seeds()
    prefix = [run_program(table, p, TARGET) for p in seeds]
    episodes = {"random": (random_episode(table, TARGET), []),
                "seed_extend": (extend_episode(table, TARGET, seeds), prefix),
                "sequence_uniform": (mutation_episode(table, TARGET, seeds), prefix)}
    modes = {}
    for mode, (episode, pre) in episodes.items():
        p, capped = summary(detection_curve(episode, BUDGET, pre), BUDGET)
        modes[mode] = {"p_episode": float(episode.probability()), "p_detect": round(p, 6),
                       "mean_capped_calls": round(capped, 3)}
    ranked = sorted(MODES, key=lambda m: -modes[m]["p_detect"])
    return {"site": site_id, "shortest_depth": depth, "shortest_witnesses": count,
            "witness": [a.__dict__ for a in witness] if witness else None,
            "modes": modes, "predicted_order": ranked}

def predict():
    from multiprocessing import Pool
    with Pool() as pool:
        rows = pool.map(_predict_site, new_sites())
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"status": "frozen specification-derived predictions; no implementation mutant executed",
               "budget": BUDGET, "target": TARGET, "seeds": list(SEEDS), "modes": list(MODES),
               "oracle_sha256": hashlib.sha256((ROOT / "integrations/salon/oracle.py").read_bytes()).hexdigest(),
               "predictions": rows}
    path = OUT / "predictions.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print("predictions sha256", hashlib.sha256(path.read_bytes()).hexdigest())
    for r in rows:
        m = r["modes"]
        print(f'{r["site"]:17} depth {r["shortest_depth"]}  '
              + "  ".join(f'{k} {m[k]["p_detect"]:.3f}' for k in MODES))

def _run_job(job):
    from integrations.salon.adapter import Adapter
    from integrations.salon_ablation.experiment import campaign
    from integrations.salon_prospective.mutants import injected
    site_id, mode = job
    with injected(site_id):
        adapter = Adapter("fixed")
    try:
        rows = []
        for seed in SEEDS:
            row = campaign(adapter, mode, TARGET, seed, BUDGET)
            row.update(site=site_id)
            row.pop("elapsed_s")
            rows.append(row)
        return rows
    finally:
        adapter.close()

def check_injection(levels=2):
    """Injected AST mutants of the four known sites must reproduce the recorded variant tables."""
    from integrations.salon.adapter import Adapter
    from integrations.salon_depth.table import explore
    from integrations.salon_prospective.mutants import EXISTING, injected
    for site_id, variant in EXISTING.items():
        recorded = json.loads(gzip.decompress(
            (ROOT / "results/history-depth/tables" / (variant + ".json.gz")).read_bytes()))
        with injected(site_id):
            adapter = Adapter("fixed")
        try:
            table = explore(adapter, levels)
        finally:
            adapter.close()
        ids = {json.dumps(s, sort_keys=True): i for i, s in enumerate(recorded["states"])}
        for sid, row in table["edges"].items():
            state = json.dumps(table["states"][int(sid)], sort_keys=True)
            expected = recorded["edges"][str(ids[state])]
            for (successor, response, violations), (r_successor, r_response, r_violations) in zip(row, expected):
                same = (table["states"][successor] == recorded["states"][r_successor]
                        and table["responses"][response] == recorded["responses"][r_response]
                        and violations == r_violations)
                if not same:
                    raise SystemExit(f"injected mutant {site_id} differs from recorded {variant}")
    print("injection check passed for", len(EXISTING), "known sites")

def run():
    from multiprocessing import get_context
    if not (OUT / "predictions.json").exists():
        raise SystemExit("freeze predictions first")
    check_injection()
    jobs = [(s, m) for s in new_sites() for m in MODES]
    with get_context("fork").Pool() as pool:
        rows = [r for chunk in pool.map(_run_job, jobs) for r in chunk]
    payload = "\n".join(json.dumps(r, sort_keys=True) for r in rows).encode()
    (OUT / "raw.jsonl.gz").write_bytes(gzip.compress(payload, mtime=0))
    print("campaigns", len(rows), "detected", sum(r["detected"] for r in rows))

def binomial_p(k, n, p):
    probs = [math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(q for q in probs if q <= probs[k] * (1 + 1e-9)))

def compare():
    frozen = json.loads((OUT / "predictions.json").read_text())
    rows = [json.loads(l) for l in gzip.decompress((OUT / "raw.jsonl.gz").read_bytes()).splitlines()]
    cells, order_hits, order_total = [], 0, 0
    for prediction in frozen["predictions"]:
        observed = {m: [r for r in rows if r["site"] == prediction["site"] and r["mode"] == m] for m in MODES}
        counts = {m: sum(r["detected"] for r in observed[m]) for m in MODES}
        for m in MODES:
            p = prediction["modes"][m]["p_detect"]
            cells.append({"site": prediction["site"], "mode": m, "n": len(observed[m]),
                          "observed": counts[m], "predicted": round(p * len(observed[m]), 2),
                          "binomial_p": round(binomial_p(counts[m], len(observed[m]), p), 4)})
        # Pairwise winner agreement where the frozen prediction separates by >= 0.1.
        for i, a in enumerate(MODES):
            for b in MODES[i + 1:]:
                pa, pb = prediction["modes"][a]["p_detect"], prediction["modes"][b]["p_detect"]
                if abs(pa - pb) >= 0.1:
                    order_total += 1
                    order_hits += (pa > pb) == (counts[a] > counts[b]) and counts[a] != counts[b]
    result = {"cells": cells, "pairwise_order_agreement": [order_hits, order_total],
              "cells_binomial_p_below_0.05": sum(c["binomial_p"] < 0.05 for c in cells),
              "predictions_sha256": hashlib.sha256((OUT / "predictions.json").read_bytes()).hexdigest()}
    (OUT / "comparison.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    for c in cells:
        print(f'{"!" if c["binomial_p"] < 0.05 else " "}{c["site"]:17} {c["mode"]:17} '
              f'obs {c["observed"]:2}/{c["n"]}  pred {c["predicted"]:5.1f}  p={c["binomial_p"]:.3f}')
    print("pairwise order agreement", order_hits, "/", order_total,
          "| cells with p<0.05:", result["cells_binomial_p_below_0.05"], "of", len(cells))

if __name__ == "__main__":
    {"predict": predict, "run": run, "compare": compare}[sys.argv[1]]()
