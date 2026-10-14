"""Descriptive pilot summaries; no discovery rate is a universal guarantee."""
import csv
import math
import statistics
from collections import defaultdict

def wilson(successes, total):
    z = 1.959963984540054
    p = successes / total
    scale = 1 + z*z / total
    center = (p + z*z / (2*total)) / scale
    margin = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / scale
    return max(0, center-margin), min(1, center+margin)

def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["mutant"], row["strategy"]].append(row)
    summaries = []
    for (mutant, strategy), runs in sorted(groups.items()):
        hits = sum(r["detected"] for r in runs)
        low, high = wilson(hits, len(runs))
        found = [r["first_failure_call"] for r in runs if r["detected"]]
        # Runs without a hit cost the full budget. This is a capped descriptive
        # effort metric, not an estimate of uncensored time-to-discovery.
        efforts = [r["first_failure_call"] if r["detected"] else r["budget"] for r in runs]
        summaries.append({"mutant": mutant, "strategy": strategy, "runs": len(runs),
            "detected": hits, "rate": hits/len(runs), "wilson_low": low, "wilson_high": high,
            "median_calls_detected_only": statistics.median(found) if found else None,
            "mean_capped_calls": statistics.mean(efforts),
            "mean_concrete_states": statistics.mean(r["concrete_states"] for r in runs),
            "mean_abstract_states": statistics.mean(r["abstract_states"] for r in runs),
            "mean_elapsed_s": statistics.mean(r["elapsed_s"] for r in runs)})
    return summaries

def write_report(rows, out):
    summaries = summarize(rows)
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    lines = ["# Descriptive campaign results", "",
        "Synthetic implementation mutants; finite fixture; first violation per run.",
        "Misses are right-censored at the call budget. Replays count toward that budget.",
        "Wilson intervals describe variation over seeds in this benchmark, not real-world breach probability.",
        "Conditional medians omit misses; use capped effort and detection rate together.", "",
        "| Variant | Strategy | Hits / seeds | 95% Wilson interval | Mean capped calls | Mean concrete states |",
        "|---|---|---:|---:|---:|---:|"]
    for s in summaries:
        lines.append(f"| {s['mutant']} | {s['strategy']} | {s['detected']}/{s['runs']} | "
                     f"{s['wilson_low']:.2f}-{s['wilson_high']:.2f} | {s['mean_capped_calls']:.1f} | "
                     f"{s['mean_concrete_states']:.1f} |")
    lines.extend(["", "Abstraction sizes are diagnostics, not comparable coverage percentages.",
                  "Fixed-control hits would indicate a defect in the implementation or specification.", ""])
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return summaries
