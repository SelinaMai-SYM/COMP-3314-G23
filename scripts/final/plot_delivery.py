"""Publication figures from measured jobs; no hand-copied numerical values."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.final.analyze_next_round import load
from experiments.next_round.evaluate import paired
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/next_round';DEST=OUT/'figures';DATASETS=['ORL_att92','JAFFE','YaleB_cropped2414','USPS'];NAMES=['ORL','JAFFE','YaleB cropped','USPS']
def main():
    jobs=[j for j in load() if j.get('status')=='COMPLETED'];DEST.mkdir(exist_ok=True)
    fig,axes=plt.subplots(2,2,figsize=(9,6),sharex=True,sharey=True,constrained_layout=True)
    for ax,dataset,name in zip(axes.flat,DATASETS,NAMES):
        a=sorted([j for j in jobs if j['task']['phase']=='A' and j['task']['dataset']==dataset],key=lambda j:j['task']['gamma']);sc=json.loads((OUT/'sc'/(dataset+'__Y0.json')).read_text())
        for metric,color in [('acc','#27699b'),('nmi','#bb6120')]:
            ax.plot([j['task']['gamma'] for j in a],[j['scores'][metric+'_mean'] for j in a],color=color,lw=1.2,label='SSC '+metric.upper())
            ax.axhline(sc['scores'][metric+'_mean'],color=color,ls='--',lw=.8,label='SC '+metric.upper())
            for j in a:ax.plot(j['task']['gamma'],j['scores'][metric+'_mean'],'o',ms=5,mec=color,mfc=color if j.get('qualified_for_method_contrast') else 'white')
        ax.set_xscale('log');ax.set_xticks([1e-6,1e-3,1,1e3,1e6]);ax.set_ylim(0,102);ax.set_title(name);ax.grid(alpha=.2);ax.set_xlabel('gamma');ax.set_ylabel('ACC / NMI (%)')
    axes[0,0].legend(fontsize=8,ncol=2,loc='lower left');fig.suptitle('Our new seeded audit: open markers are uncertified returned points',fontsize=11)
    for ext in ['png','pdf']:fig.savefig(DEST/('gamma_curves.'+ext),dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,4.8),sharey=True,constrained_layout=True)
    kinds=[('oracle_delete','Oracle W correction'),('uniform_mass','Uniform mass weakening'),('random_delete','Mean random deletion')];colors=['#28667b','#ae6b36','#768347']
    for ax,metric in zip(axes,['acc','nmi']):
        for q,(kind,label) in enumerate(kinds):
            for index,(dataset,name) in enumerate(zip(DATASETS,NAMES)):
                base=next(j for j in jobs if j['task']['phase']=='A' and j['task']['dataset']==dataset and j['task']['gamma']==1);matches=[j for j in jobs if j['task']['phase']=='B' and j['task']['dataset']==dataset and j['task']['gamma']==1 and j['task']['kind']==kind]
                if not matches:continue
                values=[{metric:float(np.mean([j['trials'][s][metric] for j in matches]))} for s in range(50)];contrast=paired(values,base['trials'],metric);value=contrast['delta_pp'];qualified=base.get('qualified_for_method_contrast') and all(j.get('qualified_for_method_contrast') for j in matches);y=index+(q-1)*.23
                ax.errorbar(value,y,xerr=np.maximum(0.,np.array([[value-contrast['ci_lower_pp']],[contrast['ci_upper_pp']-value]])),fmt='o',color=colors[q],mfc=colors[q] if qualified else 'white',ms=5,capsize=2,label=label if index==0 else None)
        ax.axvline(0,color='black',lw=.8);ax.set_yticks(range(4),NAMES);ax.set_xlabel(metric.upper()+' change vs SSC gamma=1 (pp)');ax.grid(axis='x',alpha=.2)
    axes[0].legend(loc='best',fontsize=8);fig.suptitle('Our label-assisted edge diagnosis: conditional seed-bootstrap intervals; open = uncertified',fontsize=10)
    for ext in ['png','pdf']:fig.savefig(DEST/('edge_diagnosis.'+ext),dpi=180)
    plt.close(fig)
if __name__=='__main__':main()
