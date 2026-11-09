"""Label-assisted diagnostics live here, outside all method/parameter functions."""
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import roc_auc_score
from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,GREEDY
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from method_extension.next_round.certified_solver import graph_arrays


def pair_errors(y,pred):
    _,a=np.unique(y,return_inverse=True);_,b=np.unique(pred,return_inverse=True)
    cont=np.zeros((a.max()+1,b.max()+1),dtype=np.int64);np.add.at(cont,(a,b),1)
    choose=lambda x:np.sum(x*(x-1)//2)
    same_y=choose(cont.sum(axis=1));same_p=choose(cont.sum(axis=0));same_both=choose(cont)
    cross=len(y)*(len(y)-1)//2-same_y
    return {'false_merge_rate':float((same_p-same_both)/max(1,cross)),'false_split_rate':float((same_y-same_both)/max(1,same_y)),'predicted_classes':len(np.unique(pred))}


def graph_diagnostics(F,W,y):
    B,i,j,w=graph_arrays(W);length=np.linalg.norm(B@F,axis=1);cross=y[i]!=y[j]
    components,labels=connected_components(W,directed=False)
    fragments=[len(np.unique(labels[y==k])) for k in np.unique(y)]
    return {'edges':len(w),'edge_mass_undirected':float(w.sum()),'components':components,'cross_class_edge_fraction':float(cross.mean()) if len(w) else None,'cross_class_mass_fraction':float(w[cross].sum()/w.sum()) if w.sum()>0 else None,'cross_edge_length_AUROC':float(roc_auc_score(cross,length)) if len(np.unique(cross))==2 else None,'within_class_components_mean':float(np.mean(fragments)),'length_positive_median':float(np.median(length[length>0])) if np.any(length>0) else 0.}


def distance_diagnostics(F,G,y):
    rng=np.random.default_rng(20261108);out={}
    for same in [True,False]:
        left=[];right=[]
        # Rejection sampling is bounded and samples the same fixed pairs for F/G.
        while len(left)<10000:
            i=rng.integers(0,len(F),20000);j=rng.integers(0,len(F),20000);keep=(i!=j)&((y[i]==y[j])==same)
            left.extend(i[keep].tolist());right.extend(j[keep].tolist())
        i=np.array(left[:10000]);j=np.array(right[:10000]);df=np.linalg.norm(F[i]-F[j],axis=1);dg=np.linalg.norm(G[i]-G[j],axis=1)
        name='within' if same else 'between';out[name+'_distance_before']=float(df.mean());out[name+'_distance_after']=float(dg.mean());out[name+'_contraction_ratio']=float(dg.mean()/df.mean()) if df.mean()>0 else None
    return out


def evaluate(F,G,y,K,seeds=range(50)):
    rows=[];predictions=[]
    for seed in seeds:
        fit=fit_lloyd(G,K,seed,GREEDY);pred=fit['labels'];predictions.append(pred)
        rows.append({'seed':seed,**evaluate_partition(y,pred),**pair_errors(y,pred),'inertia':fit['inertia'],'warning':fit['kmeans_warning'],'initialization_exact_name':GREEDY,'n_init':1})
    return rows,np.array(predictions),distance_diagnostics(F,G,y)


def paired(left,right,metric='acc'):
    a=np.asarray([r[metric] for r in left]);b=np.asarray([r[metric] for r in right])
    if len(a)!=50 or len(b)!=50:raise ValueError('paired endpoint needs all 50 seeds')
    d=(a-b)*100;rng=np.random.default_rng(20261108);indices=rng.integers(0,50,(2000,50));means=d[indices].mean(axis=1)
    return {'delta_pp':float(d.mean()),'ci_lower_pp':float(np.quantile(means,.025)),'ci_upper_pp':float(np.quantile(means,.975))}
