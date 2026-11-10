"""Predeclared joint numerical matching, separate from capability selection."""
from __future__ import annotations
import numpy as np
TOL=1e-12

def summarize(trials,seeds=range(50),objective='inertia'):
    expected=sorted(map(int,seeds));actual=[int(r['seed']) for r in trials]
    if sorted(actual)!=expected or len(set(actual))!=len(actual):raise ValueError('incomplete or duplicate seed set')
    for metric in ['acc','nmi']:
        a=np.asarray([r[metric] for r in trials],float)
        if not np.isfinite(a).all() or np.any((a<0)|(a>1)):raise ValueError('invalid metric')
    out={m+'_mean':float(np.mean([r[m] for r in trials])*100) for m in ['acc','nmi']}
    out.update({m+'_sd':float(np.std([r[m] for r in trials],ddof=1)*100) for m in ['acc','nmi']});out['n']=len(trials)
    if objective and all(np.isfinite(float(r.get(objective,float('nan')))) for r in trials):
        best=min(trials,key=lambda r:(float(r[objective]),int(r['seed'])))
        out['native_best']={'acc_mean':best['acc']*100,'nmi_mean':best['nmi']*100,'seed':best['seed'],'acc_sd':None,'nmi_sd':None,'native_objective':best[objective]}
    return out

def distances(row,paper):
    out=dict(row)
    for m in ['acc','nmi']:
        out['delta_'+m+'_pp']=out[m+'_mean']-paper[m]
        out['d_'+m]=abs(out['delta_'+m+'_pp'])
    out['D_max']=max(out['d_acc'],out['d_nmi']);out['D_mean']=(out['d_acc']+out['d_nmi'])/2
    return out

def compatibility(row):
    # The five published gamma values do not count as deviations.
    return (int(row.get('paper_deviations',0)),int(row.get('preparation_assumptions',0)),int(row.get('variant','E8')!='E8'),str(row.get('config_id',row.get('candidate_id',''))))

def rank(rows):
    # Anchor each tolerance bucket at its minimum. A pairwise epsilon
    # comparator can be nontransitive and make selection depend on input order.
    primary=sorted(rows,key=lambda r:(r['D_max'],r['D_mean'],compatibility(r)))
    ordered=[];left=0
    while left<len(primary):
        right=left+1
        while right<len(primary) and primary[right]['D_max']-primary[left]['D_max']<=TOL:right+=1
        secondary=sorted(primary[left:right],key=lambda r:(r['D_mean'],compatibility(r)))
        first=0
        while first<len(secondary):
            last=first+1
            while last<len(secondary) and secondary[last]['D_mean']-secondary[first]['D_mean']<=TOL:last+=1
            ordered.extend(sorted(secondary[first:last],key=compatibility));first=last
        left=right
    return ordered

def capability(rows):
    return min(rows,key=lambda r:(-r['acc_mean'],-r['nmi_mean'],str(r['config_id'])))
