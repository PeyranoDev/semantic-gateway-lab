"""Publication figures from verified v0.6 JSON; requires matplotlib only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parents[1]
MODES = ("random","random_bootstrap","seed_replay","seed_extend","mutation_unseeded",
         "sequence_uniform","sequence_enabled","sequence_enriched")
LABELS = ("Random","Warmup + random","Replay workflows","Extend workflows",
          "Mutate random bank","Mutate valid workflows","Coarse feedback","Rich feedback")
TARGETS = ("BOOKING_SCOPE","SLOT_CAPACITY","CONFIRM_PAYMENT","REFUND_REPLAY")
TITLES = ("Cross-scope reading","Slot overbooking","Unpaid confirmation","Repeated refund")
COLORS = ("#6b7280","#a1a1aa","#d1d5db","#8cb8c3","#a8a1ba","#276c89","#66874f","#b17436")

def save(fig,name,out):
    fig.savefig(out/(name+".svg"),bbox_inches="tight",pad_inches=.22,metadata={"Date":None})
    fig.savefig(out/(name+".png"),bbox_inches="tight",pad_inches=.22,dpi=180)
    plt.close(fig)

def main():
    from scripts.analyze_salon_ablation import analyze
    analyze()
    out = ROOT/"paper/figures"
    out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,
                         "svg.fonttype":"none","svg.hashsalt":"salon-ablation-v06",
                         "axes.spines.top":False,"axes.spines.right":False})
    summary = json.loads((ROOT/"results/salon-v06/summary.json").read_text())
    fig,axes = plt.subplots(2,2,figsize=(11.5,8),layout="constrained")
    for ax,target,title in zip(axes.flat,TARGETS,TITLES):
        entries = [next(r for r in summary if r["variant"]!="fixed" and r["target"]==target
                        and r["mode"]==mode) for mode in MODES]
        values = [r["detected"]/r["runs"] for r in entries]
        low = [max(0,v-r["wilson95"][0]) for v,r in zip(values,entries)]
        high = [max(0,r["wilson95"][1]-v) for v,r in zip(values,entries)]
        ax.barh(range(len(MODES)),values,color=COLORS,xerr=[low,high],
                error_kw={"linewidth":.8,"capsize":2})
        ax.set_yticks(range(len(MODES)),LABELS)
        ax.invert_yaxis()
        ax.set_xlim(0,1.12)
        ax.set_xticks((0,.25,.5,.75,1),labels=("0%","25%","50%","75%","100%"))
        ax.set_title(title,loc="left",fontweight="bold")
        ax.grid(axis="x",alpha=.18)
        ax.set_axisbelow(True)
        for index,r in enumerate(entries):
            ax.text(1.04,index,f"{r['detected']}/{r['runs']}",va="center",ha="left",fontsize=8)
    fig.suptitle("Detection within 120 calls · 30 fresh search seeds per treatment",fontsize=12)
    fig.supxlabel("Error bars: descriptive Wilson 95% intervals within the authored backend",fontsize=9)
    save(fig,"v06-detection",out)

    effects = json.loads((ROOT/"results/salon-v06/effects.json").read_text())
    contrasts = [("mutation_unseeded","sequence_uniform","Valid-bank mutation − random-bank mutation"),
                 ("seed_extend","sequence_uniform","Full mutation − append-only extension"),
                 ("seed_replay","sequence_uniform","Full mutation − workflow replay"),
                 ("random","random_bootstrap","Warmup + random − random"),
                 ("random_bootstrap","sequence_uniform","Workflow mutation − warmup + random"),
                 ("sequence_enabled","sequence_enriched","Rich − coarse feedback")]
    fig,axes = plt.subplots(3,2,figsize=(11.5,8),layout="constrained",sharex=True)
    for ax,(left,right,title) in zip(axes.flat,contrasts):
        entries = [next(r for r in effects if r["target"]==target and r["left"]==left
                        and r["right"]==right) for target in TARGETS]
        values = [r["mean_right_minus_left_capped_calls"] for r in entries]
        low = [v-r["paired_bootstrap95_capped_calls"][0] for v,r in zip(values,entries)]
        high = [r["paired_bootstrap95_capped_calls"][1]-v for v,r in zip(values,entries)]
        ax.errorbar(values,range(4),xerr=[low,high],fmt="o",color="#276c89",capsize=3)
        ax.set_yticks(range(4),TITLES)
        ax.invert_yaxis()
        ax.axvline(0,color="#666666",linewidth=.8)
        ax.set_title(title,loc="left",fontsize=10,fontweight="bold")
        ax.grid(axis="x",alpha=.18)
        ax.set_xlim(-120,120)
    fig.suptitle("Prespecified paired effects · misses retain the 120-call limit",fontsize=12)
    fig.supxlabel("Difference in mean capped calls: first treatment minus second\n"
                  "Negative: first uses fewer · Bars: paired bootstrap 95%, descriptive seed variation",fontsize=9)
    save(fig,"v06-paired-effort",out)
    print("Saved two SVG and PNG scientific figures")

if __name__ == "__main__":
    main()
