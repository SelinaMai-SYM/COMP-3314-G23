"""Bounded baseline blocks using existing library representations and shared objects."""
from __future__ import annotations
import json,os,resource,time,traceback,signal
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from SSC_method.spectral_embedding import spectral_embedding
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from experiments.v2_kmeans_protocol.kmeans_trials import RANDOM
from experiments.subset_search.runner import round_embedding,source_record
from experiments.submission_refresh.selection import summarize
from .core import ArtifactStore,atomic_json,install_cpu_limit

DATASETS={'ORL_att92':('ORL','orl','att92'),'JAFFE':('JAFFE','jaffe','zenodo'),'YaleB_cropped2414':('YaleB','yaleb','cropped2414'),'YaleB_dengcai32':('YaleB','yaleb','dengcai32'),'USPS':('USPS','usps','libsvm'),'MSRA25_EBSA_16x16':('MSRA50','msra50','ebsa16')}

def load(dataset,data_root):
    from benchmarks import load_dataset
    name,folder,version=DATASETS[dataset]
    return load_dataset(name,Path(data_root)/folder/'data',version=version)

def run_baseline(task,data_root,artifact_root):
    start=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root);folder=Path(artifact_root)/'baseline'/task['run_id'];folder.mkdir(parents=True,exist_ok=True)
    r={'task':task,'source':source_record(),'status':'RUNNING'};install_cpu_limit(task['cpu_limit'])
    try:
        with threadpool_limits(limits=1):
            X,y,meta=load(task['dataset'],data_root);K=len(np.unique(y));objects={'X':store.put(X),'y':store.put(y)};atomic_json(folder/'input.json',{'dataset':task['dataset'],'metadata':meta,'objects':objects,'source':r['source']})
            if task.get('profile') and task['block'] not in ['lda_existing','lda_reference','lda_adapted']:
                # Timing only: no evaluator is called and no performance labels
                # enter any scientific fitting function.
                if task['block']=='slps':
                    from baselines.spls.spls import oneshot_shrunk_patterns
                    S,_=oneshot_shrunk_patterns(X,.5,5);np.linalg.svd(S-S.mean(axis=0),full_matrices=False)
                else:
                    centered=X-X.mean(axis=0);np.linalg.svd(centered,full_matrices=False);spectral_embedding(X,K)
                    from baselines.llc import llc_normalized_embedding
                    np.random.seed(20261108);llc_normalized_embedding(X,K,5,1.,'gaussian',None)
                r['status']='PROFILE_ONLY_INELIGIBLE';return r
            seeds=range(1) if task.get('profile') else range(50)
            def endpoint(name,Z,extra=None):
                path=folder/(name+'.json')
                if path.exists():return
                trials,pred,centers=round_embedding(Z,y,K,RANDOM,seeds)
                record={'dataset':task['dataset'],'config_id':task['run_id']+'|'+name,'method':name.split('__')[0],'status':'PROFILE_ONLY_INELIGIBLE' if task.get('profile') else 'COMPLETED','trials':trials,'objects':{'G':store.put(Z),'predictions':store.put(pred),'centers':store.put(centers)},**(extra or {})}
                if len(trials)==50:record['summary']=summarize(trials)
                atomic_json(path,record)
            if task['block']=='slps':
                from baselines.spls.spls import oneshot_shrunk_patterns,pca_embedding
                pairs=[(k,a) for k in [5,7] for a in [.2,.5,.8]]
                if task.get('profile'):pairs=pairs[:1]
                for k,alpha in pairs:
                    t=time.process_time();S,info=oneshot_shrunk_patterns(X,alpha,k)
                    centered=S-S.mean(axis=0);u,s,vt=np.linalg.svd(centered,full_matrices=False)
                    dims=sorted(set(min(d,len(s),X.shape[0]-1) for d in [30,70,110]+task.get('extra_dimensions',[])))
                    for d in dims:
                        Z=centered@vt[:d].T
                        endpoint(f'spls__k{k}__alpha{alpha:g}__d{d}',Z,{'parameters':{'alpha':alpha,'n_neighbors':k,'dimension':d},'representation_info':info,'shrunk_patterns':store.put(S),'pca_mean':store.put(S.mean(axis=0)),'pca_projection':store.put(vt[:d].T),'preparation_cpu_seconds':time.process_time()-t})
            elif task['block'] in ['lda_existing','lda_reference','lda_adapted']:
                from .lda_audit import run_block
                run_block(task,X,y,K,store,folder,r['source'])
            elif task['block']=='msra_other':
                endpoint('kmeans',X)
                centered=X-X.mean(axis=0);u,s,vt=np.linalg.svd(centered,full_matrices=False)
                for d in task['dimensions']:
                    Z=centered@vt[:d].T;endpoint(f'pca_kmeans__d{d}',Z,{'projection':store.put(vt[:d].T),'mean':store.put(X.mean(axis=0))});F,_=spectral_embedding(Z,K);endpoint(f'pca_sc__d{d}',F)
                from baselines.llc import llc_normalized_embedding,yu_shi_discretize_state
                for reg in task['llc_ridge']:
                    for bw in task['llc_bandwidth']:
                        base=float(np.mean(np.linalg.norm(X,axis=1)))**2
                        # Isolate the source eigsh RNG modification explicitly.
                        np.random.seed(20261108)
                        F,info=llc_normalized_embedding(X,K,5,reg,'gaussian',base*bw)
                        trials=[];pred=[]
                        for seed in seeds:
                            state=yu_shi_discretize_state(F,seed,300,1e-7);p=state['labels'];trials.append({'seed':seed,**evaluate_partition(y,p),'native_objective':state.get('objective',state.get('procrustes_objective',0.))});pred.append(p)
                        atomic_json(folder/f'llc__{reg:g}__{bw:g}.json',{'dataset':task['dataset'],'method':'llc','config_id':task['run_id']+f'|{reg}|{bw}','status':'COMPLETED' if len(trials)==50 else 'PROFILE_ONLY_INELIGIBLE','trials':trials,'summary':summarize(trials,objective='native_objective') if len(trials)==50 else None,'info':info,'objects':{'F':store.put(F),'predictions':store.put(np.asarray(pred))},'determinism_modification':'seed global NumPy eigsh start at 20261108'})
            else:raise ValueError(task['block'])
            r['status']='PROFILE_ONLY_INELIGIBLE' if task.get('profile') else 'COMPLETED'
    except BaseException as exc:r.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);r.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);atomic_json(folder/'status.json',r)
    return r
