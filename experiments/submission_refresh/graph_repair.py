"""Preregistered fixed-F graph diagnostics, separate from subset calibration.

Only explicitly marked oracle/evaluation functions receive true labels. Graph
pools, angular transformations, masses and blind additions are label-free.
The calling campaign owns workers and the shared resource allowance.
"""
from __future__ import annotations
import csv,json,math,resource,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_embedding import spectral_embedding
from method_extension.next_round.certified_solver import solve,graph_arrays
from experiments.next_round.evaluate import graph_diagnostics,pair_errors
from experiments.subset_search.runner import source_record,round_embedding
from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY
from .core import ArtifactStore,atomic_json,identity,install_cpu_limit
from .selection import summarize

GAMMAS=(0.,.001,1.,10.,1000.,1000000.)
CONTROL_SEEDS=(400,401,402)
BUDGETS=(.15,.05)
DEVELOPMENT=('ORL_att92','YaleB_cropped2414')


def scientific_source_record(*, include_ensc=False):
    """Separate fitting/evaluation behavior from unrelated editorial modules.

    Exact project bytes and commit remain recorded. Cache reuse additionally
    requires the actual F/W object identities and all problem parameters.
    """
    import ast
    from .core import ROOT,digest
    source=source_record()
    paths=list((ROOT/'SSC_method').glob('*.py'))
    paths += [p for p in (ROOT/'method_extension/next_round/certified_solver').glob('*.py') if not p.name.startswith('test')]
    paths += [ROOT/'experiments/v2_kmeans_protocol/kmeans_trials.py',
              ROOT/'experiments/v2_kmeans_protocol/metrics.py',ROOT/'experiments/next_round/evaluate.py',
              ROOT/'experiments/submission_refresh/graph_repair.py']
    if include_ensc:paths.append(ROOT/'method_extension/submission_refresh/ensc.py')
    class WithoutDocstrings(ast.NodeTransformer):
        def _strip(self,node):
            self.generic_visit(node)
            if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str):
                node.body=node.body[1:] or [ast.Pass()]
            return node
        visit_Module=_strip
        visit_FunctionDef=_strip
        visit_AsyncFunctionDef=_strip
        visit_ClassDef=_strip
    behavior={str(path.relative_to(ROOT)):identity(ast.dump(WithoutDocstrings().visit(ast.parse(path.read_text())),include_attributes=False)) for path in sorted(paths)}
    source['project_source_fingerprint']=source['implementation_hash']
    source['implementation_hash']=identity({'schema':'graph-scientific-behavior-v1','files':behavior,'environment':source['environment']})
    source['scientific_source_fingerprint']=source['implementation_hash']
    source['scientific_behavior_files']=behavior
    source['cache_fingerprint_scope']='graph/embedding/PDHG/rounding/evaluator behavior; excludes comments,docstrings,reporting and unrelated campaign orchestration'
    for path in paths:source['source_files'][str(path.relative_to(ROOT))]=digest(path)
    return source

def row_unit(X):
    norms=np.linalg.norm(X,axis=1,keepdims=True)
    return np.divide(X,norms,out=np.zeros_like(X,dtype=float),where=norms>0)


def angular_graph(U,k=5):
    """Exactly zero vectors stay isolated; no label-derived norm threshold."""
    active=np.flatnonzero(np.linalg.norm(U,axis=1)>0)
    if len(active)<2:
        return sparse.csr_matrix((len(U),len(U)))
    inner,_=knn_affinity(U[active],k=min(k,len(active)-1))
    inner=inner.tocoo()
    return sparse.csr_matrix((inner.data,(active[inner.row],active[inner.col])),shape=(len(U),len(U)))


def mass_match(W,target):
    W=sparse.csr_matrix(W,dtype=float);W.eliminate_zeros()
    mass=float(sparse.triu(W,1).sum())
    if mass<=0 or target<=0:
        return W*0,{'status':'DEGENERATE_AFFINITY','raw_mass':mass,'target_mass':float(target),'scale':None}
    return W*(target/mass),{'status':'MASS_MATCHED','raw_mass':mass,'target_mass':float(target),'scale':float(target/mass)}


def stable_neighbors(X,k):
    """Top neighbors by distance then original zero-based row, including ties."""
    X=np.asarray(X,dtype=float);n=len(X);ids=np.arange(n)
    d=cdist(X,X,'sqeuclidean');np.fill_diagonal(d,np.inf)
    count=min(k,max(0,n-1))
    neighbors=np.empty((n,count),dtype=np.int64)
    for i in range(n):
        neighbors[i]=np.lexsort((ids,d[i]))[:count]
    return neighbors


def frozen_pool(F0,X,U,W0,k=20):
    """Construct the addition pool without labels or clustering predictions."""
    _,i,j,_=graph_arrays(W0);existing=set(zip(i.tolist(),j.tolist()))
    membership={}
    for bit,Z in enumerate([F0,row_unit(X),U]):
        neighbors=stable_neighbors(Z,k)
        for a in range(len(Z)):
            for b in neighbors[a]:
                edge=(min(a,int(b)),max(a,int(b)))
                if edge not in existing and edge[0]!=edge[1]:
                    membership[edge]=membership.get(edge,0)|(1<<bit)
    edges=np.asarray(list(membership),dtype=np.int64).reshape(-1,2)
    lengths=np.linalg.norm(U[edges[:,0]]-U[edges[:,1]],axis=1) if len(edges) else np.empty(0)
    order=np.lexsort((edges[:,1],edges[:,0],lengths)) if len(edges) else np.array([],dtype=int)
    return {'edges':edges[order],'angular_distance':lengths[order],
            'source_space_mask':np.array([membership[tuple(e)] for e in edges[order]],dtype=np.int8),
            'neighbors_per_space':k,'index_convention':'zero_based_original_row_order',
            'construction':'label_blind_union_of_symmetrized_top20_rawF0_rowL2X_angularU_excluding_W0',
            'tie_break':'angular_distance_then_i_then_j'}


class _Union:
    def __init__(self,n):
        self.parent=np.arange(n);self.size=np.ones(n,dtype=int)
    def find(self,i):
        i=int(i)
        while self.parent[i]!=i:
            self.parent[i]=self.parent[self.parent[i]];i=int(self.parent[i])
        return i
    def join(self,i,j):
        a=self.find(i);b=self.find(j)
        if a==b:return False
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a;self.size[a]+=self.size[b]
        return True


def oracle_edits(W0,y,pool,fraction):
    """Label-assisted deletion/completion, using only an already frozen pool."""
    _,i,j,w=graph_arrays(W0);keep=np.asarray(y)[i]==np.asarray(y)[j]
    uf=_Union(len(y))
    for a,b in zip(i[keep],j[keep]):uf.join(a,b)
    cap=int(math.floor(fraction*len(w)));degree=np.zeros(len(y),dtype=int);chosen=[]
    for a,b in pool['edges']:
        if len(chosen)>=cap:break
        if y[a]!=y[b] or degree[a]>=2 or degree[b]>=2 or uf.find(a)==uf.find(b):continue
        chosen.append((int(a),int(b)));degree[a]+=1;degree[b]+=1;uf.join(a,b)
    return {'retained_mask':keep,'deleted_count':int((~keep).sum()),
            'additions':np.asarray(chosen,dtype=np.int64).reshape(-1,2),
            'requested_addition_cap':cap,'actual_additions':len(chosen),'new_degree':degree,
            'added_weight':float(np.median(w[w>0])) if np.any(w>0) else 0.}


def random_additions(edges,count,n,seed,*,attempts=100,eligible=None,rng=None):
    """Blind unless the caller explicitly supplies a same-class oracle mask."""
    edges=np.asarray(edges,dtype=np.int64).reshape(-1,2)
    if eligible is not None:edges=edges[np.asarray(eligible,dtype=bool)]
    rng=np.random.RandomState(seed) if rng is None else rng
    if count==0:return np.empty((0,2),dtype=np.int64),{'status':'MATCHED','attempts':0}
    if count>len(edges):return None,{'status':'INFEASIBLE_MATCHED_CONTROL','attempts':0}
    for attempt in range(attempts):
        degree=np.zeros(n,dtype=int);chosen=[]
        for index in rng.permutation(len(edges)):
            a,b=edges[index]
            if degree[a]>=2 or degree[b]>=2:continue
            chosen.append((int(a),int(b)));degree[a]+=1;degree[b]+=1
            if len(chosen)==count:
                return np.asarray(chosen,dtype=np.int64),{'status':'MATCHED','attempts':attempt+1}
    return None,{'status':'INFEASIBLE_MATCHED_CONTROL','attempts':attempts}


def edit_graph(W0,retained_mask,additions,added_weight):
    _,i,j,w=graph_arrays(W0);retained_mask=np.asarray(retained_mask,dtype=bool)
    additions=np.asarray(additions,dtype=np.int64).reshape(-1,2)
    a=np.r_[i[retained_mask],additions[:,0]];b=np.r_[j[retained_mask],additions[:,1]]
    weights=np.r_[w[retained_mask],np.full(len(additions),added_weight)]
    graph=sparse.csr_matrix((np.r_[weights,weights],(np.r_[a,b],np.r_[b,a])),shape=W0.shape)
    graph.eliminate_zeros()
    return graph


def graph_family(W0,y,pool,fraction):
    edits=oracle_edits(W0,y,pool,fraction);_,i,j,w=graph_arrays(W0)
    all_edges=np.ones(len(w),dtype=bool);no_add=np.empty((0,2),dtype=np.int64)
    graphs={}
    for arm,mask,add in [('none',all_edges,no_add),('delete',edits['retained_mask'],no_add),
                         ('add',all_edges,edits['additions']),('both',edits['retained_mask'],edits['additions'])]:
        graphs[arm]={'raw_graph':edit_graph(W0,mask,add,edits['added_weight']),
                     'retained_mask':mask,'additions':add,'status':'MATCHED','label_assisted':arm!='none'}
    for kind in ['blind','same_class_random','fully_random']:
        for seed in CONTROL_SEEDS:
            rng=np.random.RandomState(seed)
            mask=edits['retained_mask'].copy()
            eligible=None
            if kind=='same_class_random':
                edges=pool['edges'];eligible=np.asarray(y)[edges[:,0]]==np.asarray(y)[edges[:,1]]
            if kind=='fully_random':
                mask=np.ones(len(w),dtype=bool)
                mask[rng.choice(len(w),edits['deleted_count'],replace=False)]=False
            additions,info=random_additions(pool['edges'],edits['actual_additions'],len(y),seed,
                                            eligible=eligible,rng=rng)
            name=f'{kind}_{seed}'
            graphs[name]={**info,'label_assisted':kind!='fully_random',
                          'control_role':'fixed_oracle_deletion_plus_blind_additions' if kind=='blind' else kind,
                          'retained_mask':mask,'additions':additions}
            if additions is not None:
                graphs[name]['raw_graph']=edit_graph(W0,mask,additions,edits['added_weight'])
    return graphs,edits


def paired_interval(left,right):
    a=np.asarray(left,dtype=float);b=np.asarray(right,dtype=float)
    if a.shape!=(50,) or b.shape!=(50,) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('The gate requires exactly50 paired finite rounding outcomes')
    difference=(a-b)*100
    indices=np.random.default_rng(424242).integers(0,50,(10000,50))
    means=difference[indices].mean(axis=1)
    return {'delta_pp':float(difference.mean()),'ci_lower_pp':float(np.quantile(means,.025)),
            'ci_upper_pp':float(np.quantile(means,.975)),
            'unit':'rounding_seed_conditional_on_fixed_data_and_representation',
            'resamples':10000,'bootstrap_seed':424242}


def _metric_vector(record,metric):
    rows=sorted(record['trials'],key=lambda row:int(row['seed']))
    if [int(r['seed']) for r in rows]!=list(range(50)):raise ValueError('Incomplete gate seed set')
    return np.array([r[metric] for r in rows])


def gate_dataset(records):
    """Fixed 15%/gamma1000 gate; no best-gamma or best-budget replacement."""
    needed=['delete','both']+[f'blind_{s}' for s in CONTROL_SEEDS]
    missing=[name for name in needed if name not in records or records[name].get('status')!='COMPLETED']
    if missing:return {'decision':'NOT_EVALUABLE_INCOMPLETE','passed':False,'missing':missing}
    delete=records['delete'];both=records['both']
    comparisons={}
    for metric in ['acc','nmi']:
        comparisons['both_minus_delete_'+metric]=paired_interval(_metric_vector(both,metric),_metric_vector(delete,metric))
        blind=np.mean([_metric_vector(records[f'blind_{s}'],metric) for s in CONTROL_SEEDS],axis=0)
        comparisons['both_minus_blind_mean_'+metric]=paired_interval(_metric_vector(both,metric),blind)
        for control in ['same_class_random','fully_random']:
            if all(f'{control}_{s}' in records and records[f'{control}_{s}']['status']=='COMPLETED' for s in CONTROL_SEEDS):
                mean=np.mean([_metric_vector(records[f'{control}_{s}'],metric) for s in CONTROL_SEEDS],axis=0)
                comparisons['both_minus_'+control+'_mean_'+metric]=paired_interval(_metric_vector(both,metric),mean)
    certified=all(records[name]['solver'].get('certified',False)
                  and records[name]['solver'].get('gap',float('inf'))<=1e-5
                  and records[name]['solver'].get('edge_violation',float('inf'))<=1e-8
                  and records[name]['solver'].get('node_violation',float('inf'))<=1e-8
                  for name in ['delete','both'])
    active=all(records[name]['solver'].get('normalized_L21_movement',0)>1e-6 for name in ['delete','both'])
    dfrag=delete['graph_diagnostics']['within_class_excess_fragments']
    bfrag=both['graph_diagnostics']['within_class_excess_fragments']
    reduction=(dfrag-bfrag)/dfrag if dfrag>0 else None
    conditions={'certified_involved_solutions':certified,'active_delete_and_both':active,
                'ACC_gain_at_least_1pp':comparisons['both_minus_delete_acc']['delta_pp']>=1-1e-12,
                'NMI_not_decreased':comparisons['both_minus_delete_nmi']['delta_pp']>=-1e-12,
                'excess_fragments_reduced_at_least_20pct':reduction is not None and reduction>=.2-1e-12,
                'ACC_CI_positive_vs_delete':comparisons['both_minus_delete_acc']['ci_lower_pp']>0,
                'ACC_CI_positive_vs_mean_blind':comparisons['both_minus_blind_mean_acc']['ci_lower_pp']>0}
    passed=all(conditions.values())
    return {'passed':passed,'decision':'PASSED' if passed else ('NOT_EVALUABLE_UNCERTIFIED' if not certified else 'FAILED'),
            'conditions':conditions,'contrasts':comparisons,'excess_fragment_reduction_fraction':reduction,
            'blind_control_solver_statuses':{name:records[name]['solver'].get('status',records[name]['solver'].get('certified')) for name in needed if name.startswith('blind_')},
            'blind_control_certification':{name:records[name]['solver'].get('certified',False) for name in needed if name.startswith('blind_')},
            'fixed_gamma':1000,'fixed_addition_fraction':.15,
            'gate_comparator':'fixed_oracle_deletion_plus_mean_blind_random_additions',
            'not_an_unseen_test':'development benchmarks already observed during design'}


def intended_tasks():
    """Complete finite catalogue; the caller can reserve individual configurations."""
    tasks=[]
    for dataset in DEVELOPMENT:
        tasks.append({'phase':'G1','dataset':dataset,'gamma':1.})
        for anchor in ['F0','U']:
            for graph in ['W0','Wa']:
                for gamma in GAMMAS:
                    tasks.append({'phase':'G2','dataset':dataset,'anchor':anchor,'graph':graph,'gamma':gamma})
        arms=['none','delete','add','both']+[f'{name}_{seed}' for name in ['blind','same_class_random','fully_random'] for seed in CONTROL_SEEDS]
        for fraction in BUDGETS:
            for arm in arms:
                for gamma in GAMMAS:
                    tasks.append({'phase':'G3','dataset':dataset,'addition_fraction':fraction,'arm':arm,'gamma':gamma})
    for task in tasks:task['configuration_id']=identity(task)
    return tasks


def _fixed_inputs(dataset,data_root,store,source):
    if dataset not in DEVELOPMENT:raise ValueError('Graph development inputs are fixed ORL/full cropped YaleB, not subset-search winners')
    from .baselines import load
    X,y,data_meta=load(dataset,data_root);X=np.asarray(X,dtype=float);y=np.asarray(y)
    input_refs={'X':store.put(X),'y':store.put(y)}
    input_identity=identity({'dataset':dataset,'implementation':source['implementation_hash'],
                             'X':input_refs['X']['sha256'],'y':input_refs['y']['sha256']})
    folder=store.root/'graph_inputs'/dataset/input_identity
    path=folder/'representation.json'
    if path.exists():
        meta=json.loads(path.read_text())
        arrays={name:store.get(ref) for name,ref in meta['objects'].items()}
        return folder,meta,arrays
    K={'ORL_att92':40,'YaleB_cropped2414':38}[dataset]
    F0,info=spectral_embedding(X,K,k=5)
    A,Ainfo=knn_affinity(X,k=5);W0,Winfo=knn_affinity(F0,k=5)
    U=row_unit(F0);Wa=angular_graph(U)
    arrays={'X':X,'y':y,'F0':F0,'U':U,'A':A,'W0':W0,'Wa_raw':Wa}
    refs={name:store.put(value) for name,value in arrays.items()}
    meta={'dataset':dataset,'input_preparation':'Y0','input_membership':'full_preregistered_development_benchmark',
          'historical_F_identity':'new_recoverable_current_F0; not claimed identical to missing historical arrays',
          'K':K,'objects':refs,'source':source,'input_metadata':data_meta,
          'spectral_info':info,'A_info':Ainfo,'W0_info':Winfo,
          'angular_zero_rows':np.flatnonzero(np.linalg.norm(F0,axis=1)==0).tolist()}
    atomic_json(path,meta)
    return folder,meta,arrays


def _solution(anchor,W,meta,store,source,*,gamma,fit_cpu_limit=1800):
    """Cache a mathematical problem once; graph-arm aliases reuse the same G."""
    from SSC_method.objective import shrinkage_laplacian
    if float(gamma)==0:
        # SC predictions depend only on the anchor. Graph-arm rows are aliases,
        # not independent reruns or certificates for a different edge indexing.
        W=sparse.csr_matrix((len(anchor),len(anchor)))
    Fref=store.put(anchor);Wref=store.put(W)
    problem={'F':Fref['sha256'],'W':Wref['sha256'],'gamma':float(gamma),
             'objective':'E8_c=2gammaw','preconditioned':True,'max_iter':30000,
             'gap_tol':1e-5,'fit_cpu_limit':min(1800,float(fit_cpu_limit)),
             'source':source['implementation_hash']}
    folder=store.root/'graph_solutions'/identity(problem);path=folder/'solution.json'
    if path.exists():return json.loads(path.read_text())
    start=time.process_time()
    fitpath=folder/'fitted_state.json'
    if fitpath.exists():
        state=json.loads(fitpath.read_text())
        if state['problem']!=problem:raise ValueError('Stored graph problem identity mismatch')
        G=store.get(state['objects']['G'])
    else:
        fit=solve(anchor,W,gamma,max_iter=30000,time_limit=max(3600,fit_cpu_limit*3),
                  cpu_time_limit=min(1800,float(fit_cpu_limit)),preconditioned=True,
                  gap_tol=1e-5,check_every=50,return_checkpoint=True,warm_start_irls=False)
        G=fit.pop('G');q=fit.pop('q');checkpoint=fit.pop('checkpoint',{})
        checkpoint_refs={name:store.put(value) for name,value in checkpoint.items() if isinstance(value,np.ndarray)}
        checkpoint_meta={name:value for name,value in checkpoint.items() if not isinstance(value,np.ndarray)}
        surrogate,_=shrinkage_laplacian(W,G,eps=1e-8)
        state={'problem':problem,'solver':fit,'objects':{'anchor':Fref,'fitted_W':Wref,'G':store.put(G),
               'q':store.put(q),'surrogate_IRLS_W':store.put(surrogate),'checkpoint_arrays':checkpoint_refs},
               'checkpoint':checkpoint_meta,'source':source}
        # Keep the expensive convex fit even if a later rounding is interrupted.
        atomic_json(fitpath,state)
    from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd
    from experiments.v2_kmeans_protocol.metrics import evaluate_partition
    y=store.get(meta['objects']['y']);trials=[];pred=[];centers=[]
    for seed in range(50):
        path=folder/'rounding'/f'{seed}.json'
        if path.exists():
            row=json.loads(path.read_text())
        else:
            fitted=fit_lloyd(G,meta['K'],seed,GREEDY)
            partition=fitted['labels']
            row={'trial':{'seed':seed,**evaluate_partition(y,partition),**pair_errors(y,partition),
                          'inertia':fitted['inertia'],'iterations':fitted['kmeans_n_iter'],'warning':fitted['kmeans_warning']},
                 'prediction':store.put(partition),'centers':store.put(fitted['centers'])}
            atomic_json(path,row)
        trials.append(row['trial']);pred.append(store.get(row['prediction']));centers.append(store.get(row['centers']))
    record={**state,'status':'COMPLETED','trials':trials,'summary':summarize(trials),
            'objects':{**state['objects'],'predictions':store.put(np.asarray(pred)),
                       'centers':store.put(np.asarray(centers))},
            'cpu_seconds_this_call':time.process_time()-start,
            'surrogate_note':'IRLS surrogate is diagnostic; fixed W remains the PDHG objective graph'}
    atomic_json(folder/'solution.json',record)
    return record


def _matched_correctness(y,pred):
    classes,truth=np.unique(y,return_inverse=True);clusters,labels=np.unique(pred,return_inverse=True)
    contingency=np.zeros((len(classes),len(clusters)),dtype=np.int64)
    np.add.at(contingency,(truth,labels),1)
    rows,cols=linear_sum_assignment(-contingency)
    mapping={int(b):int(a) for a,b in zip(rows,cols)}
    matched=np.array([mapping.get(int(c),-1) for c in labels])
    return matched==truth,matched,contingency


def error_casebook(X,F0,U,W0,y,sc,ssc,store,folder):
    """Evaluation-only casebook with all samples/seeds and fixed illustrations."""
    scpred=store.get(sc['objects']['predictions']);sscpred=store.get(ssc['objects']['predictions'])
    if scpred.shape!=sscpred.shape or scpred.shape!=(50,len(y)):raise ValueError('Casebook requires paired50 predictions')
    sc_correct=[];ssc_correct=[];confusions=[];per_class=[]
    classes=np.unique(y)
    for seed in range(50):
        a,_,ca=_matched_correctness(y,scpred[seed]);b,_,cb=_matched_correctness(y,sscpred[seed])
        sc_correct.append(a);ssc_correct.append(b);confusions.append({'seed':seed,'sc':ca,'ssc':cb})
        for label in classes:
            mask=y==label
            per_class.append({'seed':seed,'class':label.item() if isinstance(label,np.generic) else label,
                              'n':int(mask.sum()),'sc_acc':float(a[mask].mean()),'ssc_acc':float(b[mask].mean())})
    sc_correct=np.asarray(sc_correct);ssc_correct=np.asarray(ssc_correct)
    norm=np.linalg.norm(F0,axis=1);degree=np.asarray(W0.sum(axis=1)).ravel();count_degree=np.diff(W0.indptr)
    _,i,j,w=graph_arrays(W0);cross=np.asarray(y)[i]!=np.asarray(y)[j]
    wrong_count=np.bincount(np.r_[i[cross],j[cross]],minlength=len(y))
    wrong_mass=np.bincount(np.r_[i[cross],j[cross]],weights=np.r_[w[cross],w[cross]],minlength=len(y))
    norm_cut=np.quantile(norm,[.2,.4,.6,.8]);degree_cut=np.quantile(degree,[.2,.4,.6,.8])
    norm_bin=np.searchsorted(norm_cut,norm,side='right');degree_bin=np.searchsorted(degree_cut,degree,side='right')
    raw_neighbors=stable_neighbors(F0,5);angular_neighbors=stable_neighbors(U,5)
    rows=[]
    for index in range(len(y)):
        rows.append({'sample_id':index,'true_class':y[index].item() if isinstance(y[index],np.generic) else y[index],
                     'F_row_norm':float(norm[index]),'weighted_degree':float(degree[index]),'edge_count_degree':int(count_degree[index]),
                     'row_norm_quintile':int(norm_bin[index]),'weighted_degree_quintile':int(degree_bin[index]),
                     'wrong_incident_edge_count':int(wrong_count[index]),'wrong_incident_edge_mass':float(wrong_mass[index]),
                     'sc_correct_rounds':int(sc_correct[:,index].sum()),'ssc_correct_rounds':int(ssc_correct[:,index].sum()),
                     'sc_correct_ssc_wrong_rounds':int((sc_correct[:,index]&~ssc_correct[:,index]).sum()),
                     'sc_wrong_ssc_correct_rounds':int((~sc_correct[:,index]&ssc_correct[:,index]).sum()),
                     'raw_F0_neighbors':raw_neighbors[index].tolist(),'angular_U_neighbors':angular_neighbors[index].tolist()})
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'error_cases.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    examples={}
    for name,mask in [('sc_correct_ssc_wrong',sc_correct[0]&~ssc_correct[0]),
                      ('sc_wrong_ssc_correct',~sc_correct[0]&ssc_correct[0]),
                      ('both_correct',sc_correct[0]&ssc_correct[0]),('both_wrong',~sc_correct[0]&~ssc_correct[0])]:
        ids=np.flatnonzero(mask);examples[name]=int(ids[0]) if len(ids) else None
    strata=[]
    for variable,bins in [('row_norm',norm_bin),('weighted_degree',degree_bin)]:
        for quintile in range(5):
            ids=np.flatnonzero(bins==quintile)
            strata.append({'variable':variable,'quintile':quintile,'samples':len(ids),
                           'mean_wrong_edge_count':float(wrong_count[ids].mean()) if len(ids) else None,
                           'mean_wrong_edge_mass':float(wrong_mass[ids].mean()) if len(ids) else None,
                           'sc_correct_ssc_wrong_fraction':float((sc_correct[:,ids]&~ssc_correct[:,ids]).mean()) if len(ids) else None,
                           'sc_wrong_ssc_correct_fraction':float((~sc_correct[:,ids]&ssc_correct[:,ids]).mean()) if len(ids) else None})
    record={'status':'COMPLETED','objects':{'sc_correct':store.put(sc_correct),'ssc_correct':store.put(ssc_correct),
                                          'raw_neighbors':store.put(raw_neighbors),'angular_neighbors':store.put(angular_neighbors),
                                          'confusions':store.put(confusions)},
            'samples':len(y),'seed_count':50,'per_class':per_class,'strata':strata,
            'quintile_thresholds':{'row_norm':norm_cut.tolist(),'weighted_degree':degree_cut.tolist()},
            'illustrations_seed':0,'illustrations_rule':'first_original_row_of_each_seed0_correctness_category',
            'illustration_sample_ids':examples,'graph_diagnostics':graph_diagnostics(F0,W0,y),
            'sc_pair_errors':[pair_errors(y,p) for p in scpred],
            'ssc_pair_errors':[pair_errors(y,p) for p in sscpred],
            'evaluation_scope':'Label-assisted full casebook; not a label-free graph rule'}
    atomic_json(folder/'casebook.json',record)
    return record


def _save_result(path,base,solution,W,anchor,y,mass,store):
    result={**base,**solution,'mass_matching':mass,'SC_graph_arm_alias':base['gamma']==0,
            'graph_diagnostics':graph_diagnostics(anchor,W,y),
            'graph_objects':{'fitted_W':store.put(W)}}
    if mass['status']=='DEGENERATE_AFFINITY' and base['gamma']!=0:
        result['status']='DEGENERATE_AFFINITY'
    atomic_json(path,result)
    return result


def run_graph(task,data_root,artifact_root):
    """Execute one task or an explicitly selected phase using the caller's ledger.

    Fields: dataset, phase=G1/G2/G3, cpu_limit, optional anchor/graph/gamma,
    addition_fraction/arm. Omitted selectors enumerate the corresponding frozen
    phase. ``intended_tasks`` gives individual schedulable configuration records.
    A label-blind profile never invokes an evaluator or oracle edit function.
    """
    start=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root)
    run_id=task.get('run_id',identity(task));outfolder=store.root/'graph_jobs'/run_id
    outfolder.mkdir(parents=True,exist_ok=True)
    source=scientific_source_record();result={'task':task,'source':source,'status':'RUNNING'}
    if task.get('cpu_limit') is not None:install_cpu_limit(task['cpu_limit'])
    try:
        with threadpool_limits(limits=1):
            folder,meta,a=_fixed_inputs(task['dataset'],data_root,store,source)
            X,y,F0,U,A,W0=[a[key] for key in ['X','y','F0','U','A','W0']]
            outfolder=store.root/'graph_jobs'/run_id/folder.name
            outfolder.mkdir(parents=True,exist_ok=True)
            record_folder=store.root/'graph_records'/task['dataset']/folder.name
            if (outfolder/'status.json').exists():
                saved=json.loads((outfolder/'status.json').read_text())
                if saved.get('task')==task and saved.get('status')=='COMPLETED':
                    result={**saved,'cache_reused':True,'original_execution_cpu_seconds':saved.get('cpu_seconds')}
                    return result
            mass0=float(sparse.triu(W0,1).sum());Wa,wa_mass=mass_match(a['Wa_raw'],mass0)
            phase=task.get('phase',task.get('block','G2'))
            if phase not in ['G1','G2','G3']:raise ValueError('phase must be G1,G2 orG3')
            result.update(input_record=str(folder/'representation.json'),phase=phase)
            fit_limit=min(1800,float(task.get('fit_cpu_limit',1800)))
            if task.get('profile'):
                pool=frozen_pool(F0,X,U,W0)
                t=time.process_time();fit=solve(F0,W0,1000,preconditioned=True,max_iter=30000,
                    cpu_time_limit=fit_limit,time_limit=max(3600,fit_limit*3),return_checkpoint=True)
                result.update(status='PROFILE_ONLY_INELIGIBLE',fit_cpu_seconds=time.process_time()-t,
                    fit_status=fit['status'],pool_edges=len(pool['edges']),evaluation='NOT_COMPUTED',
                    profile_state=store.put({k:store.put(v) if isinstance(v,np.ndarray) else v for k,v in fit.items() if k!='checkpoint'}))
            elif phase=='G1':
                sc=_solution(F0,W0,meta,store,source,gamma=0,fit_cpu_limit=fit_limit)
                ssc=_solution(F0,W0,meta,store,source,gamma=1,fit_cpu_limit=fit_limit)
                result['casebook']=error_casebook(X,F0,U,W0,y,sc,ssc,store,outfolder)
                result.update(status='COMPLETED',sc_solution=sc,ssc_solution=ssc,
                              upstream_A_diagnostics=graph_diagnostics(X,A,y),
                              shrinkage_W0_diagnostics=graph_diagnostics(F0,W0,y))
            elif phase=='G2':
                records=[]
                for anchor_name in ([task['anchor']] if 'anchor' in task else ['F0','U']):
                    anchor={'F0':F0,'U':U}[anchor_name]
                    for graph_name in ([task['graph']] if 'graph' in task else ['W0','Wa']):
                        W,mass=mass_match(W0 if graph_name=='W0' else a['Wa_raw'],mass0)
                        for gamma in ([float(task['gamma'])] if 'gamma' in task else GAMMAS):
                            if gamma not in GAMMAS:raise ValueError('gamma outside preregistered diagnostic path')
                            base={'phase':'G2','dataset':task['dataset'],'anchor':anchor_name,'graph':graph_name,'gamma':gamma,
                                  'method':'sc' if gamma==0 else 'ssc_graph_diagnostic','config_id':f'{task["dataset"]}|G2|{anchor_name}|{graph_name}|{gamma:g}'}
                            solution=_solution(anchor,W,meta,store,source,gamma=gamma,fit_cpu_limit=fit_limit)
                            path=record_folder/('G2__'+anchor_name+'__'+graph_name+f'__{gamma:g}.json')
                            records.append(_save_result(path,base,solution,W,anchor,y,mass,store))
                result.update(status='COMPLETED',records=records)
            else:
                pool_path=folder/'frozen_label_blind_pool.json'
                if pool_path.exists():
                    poolmeta=json.loads(pool_path.read_text());pool={**poolmeta['metadata'],**{k:store.get(v) for k,v in poolmeta['objects'].items()}}
                else:
                    pool=frozen_pool(F0,X,U,W0)
                    poolmeta={'metadata':{k:v for k,v in pool.items() if not isinstance(v,np.ndarray)},
                              'objects':{k:store.put(v) for k,v in pool.items() if isinstance(v,np.ndarray)},
                              'source':source,'label_access':'NONE; frozen before oracle_edits call'}
                    poolmeta['pool_hash']=identity(poolmeta['objects']);atomic_json(pool_path,poolmeta)
                records=[]
                for fraction in ([float(task['addition_fraction'])] if 'addition_fraction' in task else BUDGETS):
                    if fraction not in BUDGETS:raise ValueError('addition budget outside frozen fractions')
                    graphs,edits=graph_family(W0,y,pool,fraction)
                    editmeta={k:store.put(v) if isinstance(v,np.ndarray) else v for k,v in edits.items()}
                    atomic_json(folder/f'oracle_edits__{fraction:g}.json',{'edits':editmeta,'pool_hash':poolmeta['pool_hash']})
                    for arm in ([task['arm']] if 'arm' in task else list(graphs)):
                        specification=graphs[arm]
                        for gamma in ([float(task['gamma'])] if 'gamma' in task else GAMMAS):
                            if gamma not in GAMMAS:raise ValueError('gamma outside preregistered diagnostic path')
                            base={'phase':'G3','dataset':task['dataset'],'anchor':'F0','arm':arm,'addition_fraction':fraction,'gamma':gamma,
                                  'method':'oracle_graph_diagnostic','config_id':f'{task["dataset"]}|G3|{fraction:g}|{arm}|{gamma:g}',
                                  'pool_hash':poolmeta['pool_hash'],'oracle_edits':editmeta}
                            path=record_folder/(f'G3__{fraction:g}__{arm}__{gamma:g}.json')
                            if specification['status']!='MATCHED':
                                record={**base,'status':specification['status'],'control_generation':{k:v for k,v in specification.items() if not isinstance(v,np.ndarray)}}
                                atomic_json(path,record);records.append(record);continue
                            Wraw=specification['raw_graph'];W,mass=mass_match(Wraw,mass0)
                            base['edit_objects']={k:store.put(v) for k,v in specification.items() if isinstance(v,np.ndarray) or sparse.issparse(v)}
                            base['control_generation']={k:v for k,v in specification.items() if not isinstance(v,np.ndarray) and not sparse.issparse(v)}
                            solution=_solution(F0,W,meta,store,source,gamma=gamma,fit_cpu_limit=fit_limit)
                            records.append(_save_result(path,base,solution,W,F0,y,mass,store))
                # Gate reads only the fixed primary arm records; other gamma and
                # budget results cannot replace the preregistered comparison.
                primary={}
                for path in record_folder.glob('G3__0.15__*__1000.json'):
                    record=json.loads(path.read_text());primary[record['arm']]=record
                result.update(status='COMPLETED',records=records,gate=gate_dataset(primary))
                atomic_json(record_folder/'gate.json',result['gate'])
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(outfolder/'status.json',result)
    return result
