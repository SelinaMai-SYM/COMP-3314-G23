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
    import yaml
    from .core import ROOT
    from experiments.v3_reproduction.dataset_registry import load_spec
    from benchmarks import DatasetUnavailable
    specs=yaml.safe_load((ROOT/'configs/submission_refresh/datasets.yaml').read_text())['specs']
    spec=next(s for s in specs if s['dataset_id']==dataset)
    record=load_spec(Path(data_root),spec)
    if not record['available']:raise DatasetUnavailable(record['reason'])
    return record['X'],record['y'],record['metadata']

def slps_configurations(task):
    """Frozen paired grid plus historical reported-setting controls, before scoring."""
    configs=[{'n_neighbors':k,'alpha':a,'dimension':d,'initialization':RANDOM,'role':'primary_paired_grid'}
             for k in [5,7] for a in [.2,.5,.8] for d in [30,70,110]]
    for config in task.get('extra_configs',[]):
        item=dict(config)
        if item['n_neighbors'] not in [5,7] or not 0<float(item['alpha'])<=1 or int(item['dimension'])<1:
            raise ValueError('invalid frozen SLPS extra configuration')
        item.setdefault('initialization',RANDOM);configs.append(item)
    return configs

def run_baseline(task,data_root,artifact_root):
    if task.get('block')=='slps':
        # The paired source-native additions were frozen before this block,
        # while the shared scheduler already held the earlier mandatory queue.
        # Reload only these declared additions; scientific limits stay fixed.
        from .core import ROOT
        declared=json.loads((ROOT/'configs/submission_refresh/execution_queue.json').read_text())['tasks']
        frozen=next((t for t in declared if t['run_id']==task['run_id']),None)
        if frozen is not None:
            if any(frozen.get(k)!=task.get(k) for k in ['dataset','block','cpu_limit']):raise ValueError('queued block differs from frozen definition')
            task={**task,'extra_configs':frozen.get('extra_configs',[])}
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
            if task['dataset']=='MSRA25_EBSA_16x16' and not task.get('profile'):
                primary=Path(artifact_root)/'baseline'/'msra-primary-v1'
                first=primary/'kmeans.json'
                if not first.exists():
                    primary.mkdir(parents=True,exist_ok=True)
                    trials,pred,centers=round_embedding(X,y,K,RANDOM)
                    atomic_json(first,{'dataset':task['dataset'],'method':'kmeans','config_id':'msra-primary-v1|kmeans','status':'COMPLETED','trials':trials,'summary':summarize(trials),'objects':{'G':objects['X'],'predictions':store.put(pred),'native_best_centers':store.put(centers[min(range(50),key=lambda i:(trials[i]['inertia'],i))])},'source':r['source'],'cpu_charged_in':task['run_id']})
                catalogue=json.loads((__import__('experiments.submission_refresh.core',fromlist=['ROOT']).ROOT/'results/subset_search/candidate_catalogue.json').read_text())['candidates']
                candidate=next(c for c in catalogue if c['candidate_id']=='MSRA25_EBSA_16x16')
                from experiments.subset_search.runner import run_candidate,scientific_cache_identity
                from .core import identity
                primary_status=Path(artifact_root)/'task_status'/('subset-'+identity(candidate)[:20]+'.json')
                if not primary_status.exists():
                    nested=run_candidate(candidate,data_root,artifact_root,cpu_limit=min(300,max(1,task['cpu_limit']-(time.process_time()-cpu))))
                    nested['cpu_charged_in']=task['run_id'];nested['execution_role']='preregistered MSRA Kmeans/SC/SSC first, reused by subset queue'
                    atomic_json(primary_status,nested)
                install_cpu_limit(max(.001,task['cpu_limit']-(time.process_time()-cpu)))
            seeds=range(1) if task.get('profile') else range(50)
            def endpoint(name,Z,extra=None,initialization=RANDOM):
                path=folder/(name+'.json')
                if path.exists():return
                extra=dict(extra or {});representation_objects={'G':store.put(Z),**extra.pop('objects',{})}
                atomic_json(folder/(name+'__fit.json'),{'dataset':task['dataset'],'config_id':task['run_id']+'|'+name,'objects':representation_objects,'initialization':initialization,**extra})
                r['active_configuration']=name
                trials,pred,centers=round_embedding(Z,y,K,initialization,seeds)
                record={'dataset':task['dataset'],'config_id':task['run_id']+'|'+name,'method':name.split('__')[0],'initialization':initialization,'status':'PROFILE_ONLY_INELIGIBLE' if task.get('profile') else 'COMPLETED','trials':trials,'objects':{**representation_objects,'predictions':store.put(pred),'centers':store.put(centers)},**extra}
                if len(trials)==50:record['summary']=summarize(trials)
                atomic_json(path,record)
            if task['block']=='slps':
                from baselines.spls.spls import oneshot_shrunk_patterns
                configs=slps_configurations(task)
                pairs=sorted(set((c['n_neighbors'],c['alpha']) for c in configs))
                if task.get('profile'):pairs=pairs[:1]
                for k,alpha in pairs:
                    t=time.process_time();S,info=oneshot_shrunk_patterns(X,alpha,k,return_state=True)
                    state=info.pop('fit_state');mean=S.mean(axis=0);centered=S-mean
                    u,singular,vt=np.linalg.svd(centered,full_matrices=False)
                    # Preserve the existing SLPS library's numerical-rank rule.
                    rank=int(np.sum(singular>singular[0]*1e-10)) if len(singular) else 0
                    valid_max=min(rank,X.shape[0]-1,X.shape[1])
                    if valid_max<1:raise ValueError('DEGENERATE_SLPS_ZERO_RANK')
                    common={'shrunk_patterns':store.put(S),'pca_mean':store.put(mean),
                            'singular_values':store.put(singular),**{key:store.put(value) for key,value in state.items()}}
                    unique={}
                    for config in configs:
                        if (config['n_neighbors'],config['alpha'])!=(k,alpha):continue
                        d=min(config['dimension'],valid_max)
                        key=(d,config['initialization'])
                        if key not in unique:unique[key]=[]
                        unique[key].append(config)
                    for (d,initialization),aliases in sorted(unique.items()):
                        Z=centered@vt[:d].T
                        name=f'spls__k{k}__alpha{alpha:g}__d{d}'
                        if initialization!=RANDOM:name+='__'+initialization
                        endpoint(name,Z,{'parameters':{'alpha':alpha,'n_neighbors':k,'dimension':d,'initialization':initialization,'n_init':1,'seeds':list(seeds)},
                            'representation_info':{**info,'numerical_rank':rank,'rank_tolerance':'singular[0]*1e-10 (existing SLPS library)',
                                'explained_variance_ratio':float(np.sum(singular[:d]**2)/np.sum(singular**2)),'whitening':False},
                            'declared_configuration_aliases':aliases,'objects':{**common,'pca_projection':store.put(vt[:d].T)},
                            'preparation_cpu_seconds':time.process_time()-t},initialization=initialization)
            elif task['block'] in ['lda_existing','lda_reference','lda_adapted']:
                from .lda_audit import run_block
                run_block(task,X,y,K,store,folder,r['source'])
            elif task['block']=='msra_other':
                endpoint('kmeans',X)
                mean=X.mean(axis=0);centered=X-mean;u,singular,vt=np.linalg.svd(centered,full_matrices=False)
                pca_common={'mean':store.put(mean),'singular_values':store.put(singular)}
                from SSC_method.graph_construction import knn_affinity
                for d in task['dimensions']:
                    projection=store.put(vt[:d].T);Z=centered@vt[:d].T
                    prep_objects={**pca_common,'projection':projection,'PCA_scores':store.put(Z)}
                    endpoint(f'pca_kmeans__d{d}',Z,{'objects':prep_objects,'parameters':{'dimension':d,'centering':True,'whitening':False}})
                    F,spectral_info=spectral_embedding(Z,K);A,Ainfo=knn_affinity(Z,k=5)
                    endpoint(f'pca_sc__d{d}',F,{'objects':{**prep_objects,'A':store.put(A),'F':store.put(F)},
                        'spectral_info':spectral_info,'A_config':Ainfo,'parameters':{'dimension':d,'centering':True,'whitening':False,'n_neighbors':5}})
                from baselines.llc import llc_normalized_embedding,yu_shi_discretize_state
                for reg in task['llc_ridge']:
                    for bw in task['llc_bandwidth']:
                        name=f'llc__{reg:g}__{bw:g}';r['active_configuration']=name
                        path=folder/(name+'.json')
                        if path.exists():continue
                        base=float(np.mean(np.linalg.norm(X,axis=1)))**2
                        # Isolate the source eigsh RNG modification explicitly.
                        np.random.seed(20261108)
                        F,info=llc_normalized_embedding(X,K,5,reg,'gaussian',base*bw,return_state=True)
                        state_arrays=info.pop('fit_state');representation_objects={'F':store.put(F),
                            **{key:store.put(value) for key,value in state_arrays.items()}}
                        parameters={'n_neighbors':5,'ridge':reg,'bandwidth_factor':bw,'bandwidth':base*bw,'kernel':'gaussian','discretization_max_iter':300,'discretization_tol':1e-7,'seeds':list(seeds)}
                        atomic_json(folder/(name+'__fit.json'),{'dataset':task['dataset'],'parameters':parameters,'info':info,'objects':representation_objects})
                        trials=[];pred=[];rotations=[];diagnostics=[]
                        for seed in seeds:
                            state=yu_shi_discretize_state(F,seed,300,1e-7);predicted=state['labels']
                            native=float(state['objective'])
                            if not np.isfinite(native):raise ValueError('nonfinite native LLC Procrustes objective')
                            trials.append({'seed':seed,**evaluate_partition(y,predicted),'native_objective':native});pred.append(predicted);rotations.append(state['rotation'])
                            diagnostics.append({key:value for key,value in state.items() if key not in ['labels','rotation']})
                            atomic_json(folder/(name+'__checkpoint.json'),{'completed_trials':trials,'diagnostics':diagnostics,
                                'objects':{'predictions':store.put(np.asarray(pred)),'rotations':store.put(np.asarray(rotations))}})
                        atomic_json(path,{'dataset':task['dataset'],'method':'llc','config_id':task['run_id']+f'|{reg}|{bw}',
                            'status':'COMPLETED' if len(trials)==50 else 'PROFILE_ONLY_INELIGIBLE','trials':trials,
                            'summary':summarize(trials,objective='native_objective') if len(trials)==50 else None,
                            'info':info,'parameters':parameters,'discretization_diagnostics':diagnostics,
                            'objects':{**representation_objects,'predictions':store.put(np.asarray(pred)),'rotations':store.put(np.asarray(rotations))},
                            'native_objective_definition':'sum ||one_hot(labels)-F@rotation||^2, within one fixed F only',
                            'determinism_modification':'seed global NumPy eigsh start at 20261108'})
            else:raise ValueError(task['block'])
            r.pop('active_configuration',None)
            r['status']='PROFILE_ONLY_INELIGIBLE' if task.get('profile') else 'COMPLETED'
    except BaseException as exc:
        r.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
        if hasattr(exc,'partial_trials'):
            r['interrupted_rounding']={'completed_trials':exc.partial_trials,'failed_rounding_seed':exc.failed_rounding_seed,
                'predictions':store.put(exc.partial_predictions),'status':'INCOMPLETE_INELIGIBLE'}
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);r.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);atomic_json(folder/'status.json',r)
    return r
