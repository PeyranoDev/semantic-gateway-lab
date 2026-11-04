"""Two prespecified contrasts, separately at each budget and defect."""
from collections import defaultdict
import hashlib
import random
from integrations.salon_ablation.analysis import percentile, summarize as base_summary

CONTRASTS = (("random", "portfolio_balanced"), ("sequence_uniform", "portfolio_balanced"))

def summarize(rows):
    output = []
    for budget in sorted({r["budget"] for r in rows}):
        group = [r for r in rows if r["budget"] == budget]
        output.extend(dict(r, budget=budget) for r in base_summary(group))
    return output

def effects(rows, samples=5000):
    by = {(r["budget"],r["variant"],r["mode"],r["seed"]):r for r in rows}
    result = []
    for budget,variant in sorted({(r["budget"],r["variant"]) for r in rows if r["variant"] != "fixed"}):
        seeds = sorted({r["seed"] for r in rows if (r["budget"],r["variant"]) == (budget,variant)})
        for left,right in CONTRASTS:
            pairs = [(by[budget,variant,left,s],by[budget,variant,right,s]) for s in seeds]
            hits = [int(b["detected"])-int(a["detected"]) for a,b in pairs]
            calls = [b["calls"]-a["calls"] for a,b in pairs]
            rng = random.Random(int(hashlib.sha256(f"v08:{budget}:{variant}:{left}:{right}".encode()).hexdigest(),16))
            boot_h,boot_c = [],[]
            for _ in range(samples):
                indices = [rng.randrange(len(pairs)) for _ in pairs]
                boot_h.append(sum(hits[i] for i in indices)/len(pairs))
                boot_c.append(sum(calls[i] for i in indices)/len(pairs))
            result.append({"budget":budget,"variant":variant,"left":left,"right":right,
                "seeds":seeds,"bootstrap_samples":samples,
                "detection_difference":sum(hits)/len(pairs),
                "descriptive95_detection":[percentile(boot_h,.025),percentile(boot_h,.975)],
                "mean_capped_calls_difference":sum(calls)/len(pairs),
                "descriptive95_capped_calls":[percentile(boot_c,.025),percentile(boot_c,.975)],
                "left_only":sum(a["detected"] and not b["detected"] for a,b in pairs),
                "right_only":sum(b["detected"] and not a["detected"] for a,b in pairs),
                "both":sum(a["detected"] and b["detected"] for a,b in pairs),
                "neither":sum(not a["detected"] and not b["detected"] for a,b in pairs)})
    return result
