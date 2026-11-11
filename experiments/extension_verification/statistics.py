"""Conditional paired rounding statistics; no parameter or subset selection."""
import numpy as np
from scipy.optimize import linear_sum_assignment


def paired(new,baseline,metric):
    if [int(x['seed']) for x in new]!=list(range(50)) or [int(x['seed']) for x in baseline]!=list(range(50)):raise ValueError('paired statistics require complete aligned seeds 0..49')
    difference=100*(np.array([x[metric] for x in new])-np.array([x[metric] for x in baseline]))
    if not np.isfinite(difference).all():raise ValueError('nonfinite paired metric')
    index=np.random.Generator(np.random.PCG64(424242)).integers(0,50,size=(10000,50));distribution=difference[index].mean(axis=1)
    lower,upper=np.quantile(distribution,[.025,.975],method='linear')
    return {'delta_pp':float(difference.mean()),'lower_pp':float(lower),'upper_pp':float(upper),'bootstrap_resamples':10000,'bootstrap_seed':424242,'lower_quantile':.025,'scope':'Conditional on fixed samples and representations; paired rounding seeds only'}


def correctness(labels,prediction):
    _,truth=np.unique(labels,return_inverse=True);_,cluster=np.unique(prediction,return_inverse=True)
    table=np.zeros((int(truth.max())+1,int(cluster.max())+1),dtype=np.int64);np.add.at(table,(truth,cluster),1)
    rows,cols=linear_sum_assignment(-table);mapping=np.full(table.shape[1],-1);mapping[cols]=rows
    return mapping[cluster]==truth


def transitions(labels,baseline,new,original_ids):
    rows=[]
    for seed,(before,after) in enumerate(zip(baseline,new)):
        a=correctness(labels,before);b=correctness(labels,after)
        for kind,mask in [('correct_to_wrong',a&~b),('wrong_to_correct',~a&b)]:
            rows.append({'seed':seed,'transition':kind,'count':int(mask.sum()),'original_row_ids':np.asarray(original_ids)[mask].tolist()})
    return rows
