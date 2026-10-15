"""Recreate both prespecified budget panels from the archived summary."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def plot(source='results/salon-v08', destination='paper/figures'):
    rows=json.loads((Path(source)/'summary.json').read_text())
    variants=['read_scope','slot_capacity','confirm_unpaid','refund_replay']
    labels=['Cross-scope\nread','Slot\ncapacity','Unpaid\nconfirmation','Repeated\nrefund']
    modes=['random','sequence_uniform','portfolio_balanced']
    titles=['Random','Workflow mutation','Balanced portfolio']
    colors=['#727C8E','#247BA0','#B04A00']
    fig,axes=plt.subplots(1,2,figsize=(11,4.7),sharey=True)
    for ax,budget in zip(axes,[120,480]):
        for index,(mode,title,color) in enumerate(zip(modes,titles,colors)):
            group=[next(r for r in rows if (r['budget'],r['variant'],r['mode'])==(budget,v,mode)) for v in variants]
            xs=[x+(index-1)*.25 for x in range(4)]
            hits=[r['detected'] for r in group]
            ax.bar(xs,hits,width=.24,label=title,color=color)
            errors=[[max(0,r['detected']-30*r['wilson95'][0]) for r in group],
                    [max(0,30*r['wilson95'][1]-r['detected']) for r in group]]
            ax.errorbar(xs,hits,yerr=errors,fmt='none',ecolor='#20252B',capsize=2,elinewidth=.7)
            for x,h in zip(xs,hits):
                ax.text(x,h-1 if h else .7,str(h),ha='center',va='top' if h else 'bottom',fontsize=8,color='white' if h else color,fontweight='bold')
        ax.set_xticks(range(4),labels,fontsize=9)
        ax.set_title(f'{budget} calls per campaign')
        ax.set_ylim(0,34)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_axisbelow(True)
        ax.grid(axis='y',alpha=.18)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Detected campaigns / 30 search seeds')
    fig.suptitle('Fixed portfolio: detection tradeoffs at two shared budgets',fontsize=14)
    handles,legend=axes[0].get_legend_handles_labels()
    fig.legend(handles,legend,loc='lower center',bbox_to_anchor=(.5,.055),ncol=3,frameon=False)
    fig.text(.5,.012,'Wilson 95% intervals; same four authored defects; budget panels reuse seeds and are dependent.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.14,1,.94))
    target=Path(destination);target.mkdir(parents=True,exist_ok=True)
    matplotlib.rcParams['svg.hashsalt']='salon-portfolio-v08'
    fig.savefig(target/'salon-portfolio.svg',metadata={'Date':None})
    fig.savefig(target/'salon-portfolio.png',dpi=180)
    plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='results/salon-v08')
    parser.add_argument('--destination',default='paper/figures')
    args=parser.parse_args();plot(args.source,args.destination)
