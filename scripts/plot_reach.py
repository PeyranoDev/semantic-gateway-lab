"""Predicted detection probability versus observed fraction (historical and prospective cells)."""
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from fuzzlab.report import wilson

COLORS = {"random": "#727C8E", "random_bootstrap": "#9AA3B2", "seed_replay": "#C9CED6",
          "seed_extend": "#B04A00", "mutation_unseeded": "#7A9E3B", "sequence_uniform": "#247BA0"}
LABELS = {"random": "Random", "random_bootstrap": "Random after warmup", "seed_replay": "Valid replay",
          "seed_extend": "Valid prefix + random", "mutation_unseeded": "Mutation of random bank",
          "sequence_uniform": "Mutation of valid bank"}

def panel(ax, points, title):
    ax.plot([0, 1], [0, 1], color="#20252B", linewidth=.7, linestyle="--")
    seen = set()
    for predicted, k, n, mode in points:
        lo, hi = wilson(k, n)
        ax.errorbar(predicted, k / n, yerr=[[max(0.0, k / n - lo)], [max(0.0, hi - k / n)]], fmt="o", markersize=4,
                    color=COLORS[mode], elinewidth=.6, capsize=1.5,
                    label=None if mode in seen else LABELS[mode])
        seen.add(mode)
    ax.set_xlim(-.03, 1.03)
    ax.set_ylim(-.03, 1.03)
    ax.set_xlabel("Exact predicted P(detect within budget)")
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=.25)

def main(destination="paper/figures"):
    summary = json.loads((ROOT / "results/history-depth/summary.json").read_text())
    historical = [(c["predicted_probability"], c["observed"], c["n"], c["mode"]) for c in summary["cells"]]
    frozen = json.loads((ROOT / "results/prospective/predictions.json").read_text())
    comparison = json.loads((ROOT / "results/prospective/comparison.json").read_text())
    prob = {(p["site"], m): v["p_detect"] for p in frozen["predictions"] for m, v in p["modes"].items()}
    prospective = [(prob[c["site"], c["mode"]], c["observed"], c["n"], c["mode"]) for c in comparison["cells"]]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), sharey=True)
    panel(axes[0], historical, "Recorded campaigns, 4 reviewed defects (pipeline validation)")
    panel(axes[1], prospective, "Frozen prediction, 14 systematic mutants (prospective)")
    axes[0].set_ylabel("Observed detection fraction (Wilson 95%)")
    handles, labels = [], []
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in labels:
                handles.append(h)
                labels.append(l)
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, .1, 1, 1))
    out = ROOT / destination
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("svg", "png", "pdf"):
        fig.savefig(out / f"reach-calibration.{suffix}", dpi=160, metadata={"Date": None} if suffix == "svg" else None)
    print("wrote", out / "reach-calibration.svg")

if __name__ == "__main__":
    main(*sys.argv[1:])
