"""Independent-service test: specification-derived predictions versus live crAPI campaigns.

  python scripts/crapi_study.py predict        # exact predictions from the spec model; freeze
  python scripts/crapi_study.py run [seeds]    # live crAPI campaigns (needs the stack up)
  python scripts/crapi_study.py compare        # frozen predictions versus observed

Protocol: docs/crapi-protocol.md. Freeze predictions before running.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from integrations.crapi.experiment import MODES
from integrations.crapi.model import DOCUMENTED_DEFECTS, FIELDS, PROPERTIES, legitimate_seeds
from integrations.crapi.reach import explore
from integrations.salon_depth.model import (Episode, detection_curve, extend_episode,
                                            mutation_episode, random_episode, run_program, summary)

OUT = ROOT / "results/crapi"
BUDGET, DEPTH = 60, 8
SEEDS = tuple(range(700, 730))
SOURCES = ("integrations/crapi/model.py", "integrations/crapi/reach.py",
           "integrations/crapi/generator.py", "integrations/crapi/experiment.py",
           "integrations/crapi/adapter.py")

def _episode(table, target, mode):
    seeds = legitimate_seeds()
    if mode == "random":
        return random_episode(table, target, DEPTH), []
    prefix = [run_program(table, p, target) for p in seeds]
    if mode == "seed_extend":
        return extend_episode(table, target, seeds, DEPTH), prefix
    return mutation_episode(table, target, seeds, DEPTH, FIELDS), prefix

def predict():
    rows = []
    for target in PROPERTIES:
        table = explore(DOCUMENTED_DEFECTS, target, levels=7)
        modes = {}
        for mode in MODES:
            episode, prefix = _episode(table, target, mode)
            p, capped = summary(detection_curve(episode, BUDGET, prefix), BUDGET)
            modes[mode] = {"p_detect": round(p, 6), "mean_capped_calls": round(capped, 3)}
        rows.append({"target": target, "expanded_states": len(table.edges), "modes": modes,
                     "predicted_order": sorted(MODES, key=lambda m: -modes[m]["p_detect"])})
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"status": "frozen specification-derived predictions; no live crAPI executed",
               "budget": BUDGET, "depth": DEPTH, "seeds": list(SEEDS), "modes": list(MODES),
               "documented_defects": sorted(DOCUMENTED_DEFECTS), "predictions": rows}
    path = OUT / "predictions.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print("predictions sha256", hashlib.sha256(path.read_bytes()).hexdigest())
    for r in rows:
        print(f'{r["target"]:23} ' + "  ".join(f'{m} {r["modes"][m]["p_detect"]:.3f}' for m in MODES))

def run(seeds=None):
    from integrations.crapi.adapter import Adapter
    from integrations.crapi.experiment import campaign
    if not (OUT / "predictions.json").exists():
        raise SystemExit("freeze predictions first")
    chosen = SEEDS if seeds is None else tuple(range(700, 700 + int(seeds)))
    adapter = Adapter()
    rows = []
    for target in PROPERTIES:
        for mode in MODES:
            for seed in chosen:
                row = campaign(adapter, mode, target, seed, BUDGET, DEPTH)
                row.pop("trace")
                rows.append(row)
        # Checkpoint after each target so a stopped run keeps completed targets.
        payload = "\n".join(json.dumps(r, sort_keys=True) for r in rows).encode()
        (OUT / "raw.jsonl.gz").write_bytes(gzip.compress(payload, mtime=0))
        print("done", target, "- checkpointed", len(rows), "rows", flush=True)
    print("campaigns", len(rows), "detected", sum(r["detected"] for r in rows))

def binomial_p(k, n, p):
    probs = [math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(q for q in probs if q <= probs[k] * (1 + 1e-9)))

def compare():
    frozen = json.loads((OUT / "predictions.json").read_text())
    rows = [json.loads(l) for l in gzip.decompress((OUT / "raw.jsonl.gz").read_bytes()).splitlines()]
    prob = {(p["target"], m): v["p_detect"] for p in frozen["predictions"] for m, v in p["modes"].items()}
    cells, order_hits, order_total = [], 0, 0
    for prediction in frozen["predictions"]:
        counts = {}
        for mode in MODES:
            group = [r for r in rows if r["target"] == prediction["target"] and r["mode"] == mode]
            counts[mode] = sum(r["detected"] for r in group)
            p = prob[prediction["target"], mode]
            cells.append({"target": prediction["target"], "mode": mode, "n": len(group),
                          "observed": counts[mode], "predicted": round(p * len(group), 2),
                          "binomial_p": round(binomial_p(counts[mode], len(group), p), 4)})
        for i, a in enumerate(MODES):
            for b in MODES[i + 1:]:
                if abs(prob[prediction["target"], a] - prob[prediction["target"], b]) >= 0.1:
                    order_total += 1
                    order_hits += ((prob[prediction["target"], a] > prob[prediction["target"], b])
                                   == (counts[a] > counts[b]) and counts[a] != counts[b])
    result = {"cells": cells, "pairwise_order_agreement": [order_hits, order_total],
              "source_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
              "predictions_sha256": hashlib.sha256((OUT / "predictions.json").read_bytes()).hexdigest()}
    (OUT / "comparison.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    for c in cells:
        print(f'{"!" if c["binomial_p"] < 0.05 else " "}{c["target"]:23} {c["mode"]:16} '
              f'obs {c["observed"]:2}/{c["n"]}  pred {c["predicted"]:5.1f}  p={c["binomial_p"]:.3f}')
    print("pairwise order agreement", order_hits, "/", order_total)

if __name__ == "__main__":
    {"predict": predict, "run": run, "compare": compare}[sys.argv[1]](*sys.argv[2:])
