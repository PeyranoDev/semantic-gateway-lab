"""Exploratory post hoc analysis: exact reachability predictions for recorded salon campaigns.

Usage:
  python scripts/analyze_history_depth.py build      # record tables from the HTTP/SQL backend
  python scripts/analyze_history_depth.py replay     # recorded campaigns reproduced on the tables
  python scripts/analyze_history_depth.py analyze    # depth, exact predictions, observed outcomes
  python scripts/analyze_history_depth.py stats      # exact McNemar, A12 and Holm for planned contrasts
"""
from copy import deepcopy
from dataclasses import asdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from integrations.salon.model import VARIANT_TARGET, legitimate_seeds
from integrations.salon_ablation.programs import bank
from integrations.salon_depth.model import (Episode, Table, detection_curve, extend_episode,
                                            mutation_episode, random_episode, run_program,
                                            shortest_witness, summary)

OUT = ROOT / "results/history-depth"
VARIANTS = ("fixed", "read_scope", "slot_capacity", "confirm_unpaid", "refund_replay")
STUDIES = {"v0.5": "salon-v05", "v0.6": "salon-v06", "v0.8": "salon-v08"}
EXACT_MODES = ("random", "random_bootstrap", "seed_replay", "seed_extend",
               "mutation_unseeded", "sequence_uniform")
SOURCES = ("backends/salon/app.py", "backends/salon/auth.py", "backends/salon/db.py",
           "backends/salon/service.py", "integrations/salon/adapter.py",
           "integrations/salon/model.py", "integrations/salon/oracle.py",
           "integrations/salon/generator.py", "integrations/salon_ablation/programs.py",
           "integrations/salon_depth/table.py", "integrations/salon_depth/model.py")

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def table_path(variant):
    return OUT / "tables" / (variant + ".json.gz")

def load(variant):
    return json.loads(gzip.decompress(table_path(variant).read_bytes()))

def rows(study):
    return [json.loads(line) for line in gzip.open(ROOT / "results" / STUDIES[study] / "raw.jsonl.gz")]

def build():
    import os
    import time
    from integrations.salon_depth.table import explore_parallel
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        started = time.time()
        table = explore_parallel(variant, levels=7, workers=os.cpu_count() or 4)
        payload = json.dumps(table, sort_keys=True, separators=(",", ":")).encode()
        table_path(variant).write_bytes(gzip.compress(payload, mtime=0))
        print(variant, "states", len(table["states"]), "expanded", len(table["edges"]),
              "seconds", round(time.time() - started), flush=True)

class CopyingTableAdapter:
    """TableAdapter that returns copies, so campaigns cannot alter recorded states."""

    def __init__(self, inner):
        self.inner = inner

    def reset(self):
        self.inner.reset()

    def snapshot(self):
        return deepcopy(self.inner.snapshot())

    def execute(self, action):
        return deepcopy(self.inner.execute(action))

def replay():
    """Rerun every recorded campaign on the table; semantic fields must be identical."""
    from integrations.salon.adapter import Adapter
    from integrations.salon_depth.table import TableAdapter
    from integrations.salon import experiment as v05
    from integrations.salon_ablation import experiment as v06
    from integrations.salon_portfolio import experiment as v08
    report = {}
    for variant in VARIANTS:
        fallback = Adapter(variant)
        table = load(variant)
        try:
            for study in STUDIES:
                compared = mismatched = 0
                for row in rows(study):
                    if row["variant"] != variant:
                        continue
                    inner = TableAdapter(table, fallback)
                    adapter = CopyingTableAdapter(inner)
                    if study == "v0.5":
                        got = v05.campaign(adapter, row["mode"], row["target"], row["seed"], row["budget"])
                    elif study == "v0.6":
                        got = v06.campaign(adapter, row["mode"], row["target"], row["seed"], row["budget"])
                    else:
                        got = v08.campaign(adapter, row["mode"], row["seed"], row["budget"])
                    keys = set(got) & set(row) - {"elapsed_s"}
                    compared += 1
                    mismatched += any(got[k] != row[k] for k in keys)
                report.setdefault(study, {})[variant] = {"campaigns": compared, "mismatched": mismatched}
                print(study, variant, compared, "mismatched", mismatched, flush=True)
        finally:
            fallback.close()
    (OUT / "replay.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report

def binomial_p(k, n, p):
    """Two-sided exact binomial p-value (sum of outcomes no more likely than k)."""
    probs = [math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(q for q in probs if q <= probs[k] * (1 + 1e-9)))

def episode_for(table, target, mode, seed):
    seeds = legitimate_seeds()
    if mode in ("random", "random_bootstrap"):
        return random_episode(table, target)
    if mode == "seed_replay":
        episode = Episode(8)
        for program in seeds:
            episode.add_program(table, program, target, 1 / len(seeds))
        return episode
    if mode == "seed_extend":
        return extend_episode(table, target, seeds)
    if mode == "sequence_uniform":
        return mutation_episode(table, target, seeds)
    if mode == "mutation_unseeded":
        return mutation_episode(table, target, bank(mode, seed))
    raise ValueError(mode)

def prefix_for(table, target, mode, seed):
    if mode == "random":
        return []
    programs = bank(mode, seed) if mode == "mutation_unseeded" else legitimate_seeds()
    return [run_program(table, program, target) for program in programs]

def analyze():
    tables = {v: Table(load(v)) for v in VARIANTS}
    depth = {}
    for variant in VARIANTS:
        target = "ANY" if variant == "fixed" else VARIANT_TARGET[variant]
        k, witness, count = shortest_witness(tables[variant], target)
        depth[variant] = {"target": target, "shortest_depth": k, "shortest_witnesses": count,
                          "witness": [asdict(a) for a in witness] if witness else None,
                          "expanded_states": len(tables[variant].edges)}
    cells = []
    cache = {}
    for study in STUDIES:
        groups = {}
        for row in rows(study):
            if row["variant"] == "fixed" or row["mode"] not in EXACT_MODES:
                continue
            groups.setdefault((row["mode"], row["variant"], row["budget"], row["target"]), []).append(row)
        for (mode, variant, budget, target), group in sorted(groups.items()):
            curves = []
            for row in group:
                seed = row["seed"] if mode == "mutation_unseeded" else None
                key = (variant, target, mode, seed)
                if key not in cache:
                    cache[key] = episode_for(tables[variant], target, mode, seed)
                prefix = prefix_for(tables[variant], target, mode, row["seed"])
                curves.append(detection_curve(cache[key], budget, prefix))
            first = [sum(c[t] for c in curves) / len(curves) for t in range(budget + 1)]
            p, capped = summary(first, budget)
            hits = [r["calls"] for r in group if r["detected"]]
            n, k = len(group), len(hits)
            cells.append({"study": study, "mode": mode, "variant": variant, "target": target,
                          "budget": budget, "n": n, "observed": k,
                          "predicted_probability": round(p, 6),
                          "predicted_detections": round(n * p, 3),
                          "binomial_p": round(binomial_p(k, n, p), 6),
                          "observed_mean_capped": round(sum(r["calls"] if r["detected"] else budget
                                                            for r in group) / n, 3),
                          "predicted_mean_capped": round(capped, 3),
                          "observed_first_failure": sorted(hits),
                          "predicted_cdf": [round(sum(first[:t + 1]), 6) for t in range(budget + 1)]})
    manifest = {"status": "exploratory post hoc analysis of existing campaigns",
                "source_sha256": {s: sha256(ROOT / s) for s in SOURCES},
                "table_sha256": {v: sha256(table_path(v)) for v in VARIANTS},
                "raw_sha256": {s: sha256(ROOT / "results" / d / "raw.jsonl.gz") for s, d in STUDIES.items()}}
    result = {"manifest": manifest, "depth": depth, "cells": cells}
    (OUT / "summary.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return result

def stats():
    """Planned v0.6 and v0.8 contrasts; Holm adjustment within each study's family."""
    from integrations.salon_ablation.analysis import CONTRASTS as V06
    from integrations.salon_portfolio.analysis import CONTRASTS as V08
    from integrations.salon_depth.stats import a12, holm, mcnemar_exact
    families = {"v0.6": [(l, r) for l, r, _ in V06], "v0.8": list(V08)}
    output = {}
    for study, contrasts in families.items():
        data = rows(study)
        by = {(r["variant"], r["mode"], r["budget"], r["seed"]): r for r in data}
        tests = []
        for variant in VARIANTS[1:]:
            for budget in sorted({r["budget"] for r in data}):
                seeds = sorted({r["seed"] for r in data if r["variant"] == variant and r["budget"] == budget})
                for left, right in contrasts:
                    pairs = [(by[variant, left, budget, s], by[variant, right, budget, s]) for s in seeds]
                    lo = sum(a["detected"] and not b["detected"] for a, b in pairs)
                    ro = sum(b["detected"] and not a["detected"] for a, b in pairs)
                    tests.append({"variant": variant, "budget": budget, "left": left, "right": right,
                                  "pairs": len(pairs),
                                  "left_detected": sum(a["detected"] for a, _ in pairs),
                                  "right_detected": sum(b["detected"] for _, b in pairs),
                                  "left_only": lo, "right_only": ro,
                                  "mcnemar_exact_p": mcnemar_exact(lo, ro),
                                  "a12_capped_calls": a12([a["calls"] for a, _ in pairs],
                                                          [b["calls"] for _, b in pairs])})
        for test, adjusted in zip(tests, holm([t["mcnemar_exact_p"] for t in tests])):
            test["holm_p"] = adjusted
        output[study] = {"family_size": len(tests), "tests": tests}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "paired-tests.json").write_text(json.dumps(output, indent=1, sort_keys=True) + "\n")
    return output

if __name__ == "__main__":
    {"build": build, "replay": replay, "analyze": analyze, "stats": stats}[sys.argv[1]]()
