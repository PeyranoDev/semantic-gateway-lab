"""Prespecified paired, seed-level descriptive effects; no system-level inference."""
from collections import defaultdict
import hashlib
import random

from fuzzlab.report import wilson

CONTRASTS = (
    ("mutation_unseeded", "sequence_uniform", "valid initial bank under matched mutation"),
    ("seed_extend", "sequence_uniform", "whole-program mutation versus append-only extension"),
    ("seed_replay", "sequence_uniform", "perturbation versus valid-workflow replay sanity control"),
    ("random", "random_bootstrap", "charged valid warmup without retaining its state"),
    ("random_bootstrap", "sequence_uniform", "workflow reuse plus mutation after matched warmup"),
    ("sequence_enabled", "sequence_enriched", "feedback projection replication"),
)

def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["variant"], row["target"], row["mode"])].append(row)
    return [{"variant":v, "target":t, "mode":m, "runs":len(group),
             "detected":sum(r["detected"] for r in group),
             "wilson95":wilson(sum(r["detected"] for r in group),len(group)),
             "mean_capped_calls":sum(r["calls"] for r in group)/len(group),
             "bootstrap_detections":sum(r["detected"] and r["calls"] <= r["bootstrap_calls"]
                                         for r in group),
             "mean_observed_states":sum(r["observed_states"] for r in group)/len(group)}
            for (v,t,m),group in sorted(groups.items())]

def percentile(values, fraction):
    values = sorted(values)
    index = (len(values)-1)*fraction
    lo = int(index)
    hi = min(lo+1,len(values)-1)
    return values[lo]+(index-lo)*(values[hi]-values[lo])

def effects(rows, samples=5000):
    by = {(r["variant"],r["target"],r["mode"],r["seed"]):r for r in rows}
    output = []
    for variant,target in sorted({(r["variant"],r["target"]) for r in rows if r["variant"] != "fixed"}):
        seeds = sorted({r["seed"] for r in rows if (r["variant"],r["target"]) == (variant,target)})
        for left,right,purpose in CONTRASTS:
            pairs = [(by[variant,target,left,s],by[variant,target,right,s]) for s in seeds]
            calls = [b["calls"]-a["calls"] for a,b in pairs]
            detections = [int(b["detected"])-int(a["detected"]) for a,b in pairs]
            rng_seed = int(hashlib.sha256(f"{variant}:{target}:{left}:{right}:v06".encode()).hexdigest(),16)
            rng = random.Random(rng_seed)
            boot_calls,boot_hits = [],[]
            for _ in range(samples):
                indices = [rng.randrange(len(pairs)) for _ in pairs]
                boot_calls.append(sum(calls[i] for i in indices)/len(pairs))
                boot_hits.append(sum(detections[i] for i in indices)/len(pairs))
            output.append({"variant":variant,"target":target,"left":left,"right":right,
                "purpose":purpose,"seeds":seeds,"bootstrap_samples":samples,
                "mean_right_minus_left_capped_calls":sum(calls)/len(pairs),
                "paired_bootstrap95_capped_calls":[percentile(boot_calls,.025),percentile(boot_calls,.975)],
                "right_minus_left_detection_fraction":sum(detections)/len(pairs),
                "paired_bootstrap95_detection_difference":[percentile(boot_hits,.025),percentile(boot_hits,.975)],
                "left_only":sum(a["detected"] and not b["detected"] for a,b in pairs),
                "right_only":sum(b["detected"] and not a["detected"] for a,b in pairs),
                "both":sum(a["detected"] and b["detected"] for a,b in pairs),
                "neither":sum(not a["detected"] and not b["detected"] for a,b in pairs)})
    return output
