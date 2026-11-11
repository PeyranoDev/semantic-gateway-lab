"""Predicted detection probability versus call budget, with observed surrogate points.

The exact model gives P(detect within b) for every budget b; this plots the curve to
480 calls for the three main generators on each reviewed salon defect, and overlays the
1,000-seed surrogate detection fractions where they were measured.
"""
import gzip
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from integrations.salon.model import VARIANT_TARGET, legitimate_seeds
from integrations.salon_depth.model import (Table, detection_curve, extend_episode,
                                            mutation_episode, random_episode, run_program)

VARIANTS = ("read_scope", "slot_capacity", "confirm_unpaid", "refund_replay")
LABELS = {"read_scope": "Cross-scope read (depth 1)", "slot_capacity": "Overbooking (depth 2)",
          "confirm_unpaid": "Unpaid confirmation (depth 2)", "refund_replay": "Repeated refund (depth 5)"}
MODES = {"random": "#727C8E", "seed_extend": "#B04A00", "sequence_uniform": "#247BA0"}
NAMES = {"random": "Random", "seed_extend": "Valid prefix + random",
         "sequence_uniform": "Mutation of valid bank"}
MAX = 480

def load_table(variant):
    raw = json.loads(gzip.decompress((ROOT / "results/history-depth/tables" / (variant + ".json.gz")).read_bytes()))
    return Table(raw)

def episode(table, target, mode, seeds):
    if mode == "random":
        return random_episode(table, target), []
    prefix = [run_program(table, p, target) for p in seeds]
    if mode == "seed_extend":
        return extend_episode(table, target, seeds), prefix
    return mutation_episode(table, target, seeds), prefix

def observed():
    data = json.loads(gzip.decompress((ROOT / "results/history-depth/surrogate.json.gz").read_bytes()))
    return {(c["variant"], c["mode"], c["budget"]): c["detected"] / c["n"] for c in data["cells"]}

def main(destination="paper/figures"):
    seeds = legitimate_seeds()
    obs = observed()
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.9), sharey=True)
    for ax, variant in zip(axes, VARIANTS):
        table, target = load_table(variant), VARIANT_TARGET[variant]
        for mode, color in MODES.items():
            ep, prefix = episode(table, target, mode, seeds)
            first = detection_curve(ep, MAX, prefix)
            cumulative, running = [], 0.0
            for value in first:
                running += value
                cumulative.append(running)
            ax.plot(range(MAX + 1), cumulative, color=color, linewidth=1.6, label=NAMES[mode])
            for budget in (120, 480):
                if (variant, mode, budget) in obs:
                    ax.scatter([budget], [obs[(variant, mode, budget)]], color=color,
                               s=26, zorder=3, edgecolor="white", linewidth=.6)
        ax.axvline(120, color="#20252B", linewidth=.6, linestyle=":")
        ax.set_title(LABELS[variant], fontsize=10)
        ax.set_xlabel("Call budget")
        ax.set_xlim(0, MAX)
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=.25)
    axes[0].set_ylabel("Detection probability")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=9, frameon=False)
    fig.suptitle("Exact detection curves (lines) and 1,000-seed observed fractions (points)", fontsize=10)
    fig.tight_layout(rect=(0, .08, 1, .96))
    out = ROOT / destination
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("svg", "png", "pdf"):
        fig.savefig(out / f"reach-curves.{suffix}", dpi=160)
    print("wrote", out / "reach-curves.svg")

if __name__ == "__main__":
    main(*sys.argv[1:])
