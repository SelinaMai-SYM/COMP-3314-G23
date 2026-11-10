"""Thin subset adapter; changed membership always reconstructs A, F, W and G."""
from __future__ import annotations
import json, os, resource, subprocess, time, traceback
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_embedding import spectral_embedding
from SSC_method.optimizer import shrink_embedding,iteration_diagnostics
from SSC_method.objective import shrinkage_laplacian
from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,RANDOM,VANILLA,GREEDY
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from experiments.v3_reproduction.provenance import fingerprint_matrix,environment_record
from experiments.submission_refresh.core import ArtifactStore,atomic_json,identity,install_cpu_limit,ROOT
from experiments.submission_refresh.selection import summarize

GAMMAS=[1e-6,1e-3,1.,1e3,1e6]
INITS=[RANDOM,VANILLA,GREEDY]

def source_record():
    files=[]
    for folder in ['SSC_method','baselines','method_extension','experiments/subset_search','experiments/submission_refresh','benchmarks']:
        files.extend(sorted((ROOT/folder).rglob('*.py')))
    from experiments.submission_refresh.core import digest
    hashes={str(f.relative_to(ROOT)):digest(f) for f in files}
    record={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_files':hashes,'implementation_hash':identity(hashes),'environment':environment_record(),'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())}
    from threadpoolctl import threadpool_info
    record['thread_libraries']=threadpool_info()
    artifact_root=os.environ.get('COMP3314_ARTIFACT_ROOT')
    if artifact_root:
        record['source_archive']=ArtifactStore(artifact_root).put({str(f.relative_to(ROOT)):f.read_text() for f in files})
    return record

def scientific_cache_identity(candidate, data_root=None, *, profile=False):
    """Match source behavior, environment, protocol and available input bytes.

    Comments and docstrings are excluded from the behavior fingerprint, so an
    editorial commit does not invalidate otherwise identical scientific runs.
    The exact source bytes and commit remain recorded separately in source.json.
    """
    import ast
    from .catalogue import _manifest
    from experiments.submission_refresh.core import digest
    manifest = _manifest(candidate)
    if data_root is not None:
        for source in manifest.get('source_files', []):
            path=Path(data_root)/source['path_relative_to_data_root']
            if not path.is_file() or digest(path)!=source['sha256']:
                raise ValueError(f'candidate source hash mismatch: {path}')
    files=list((ROOT/'SSC_method').glob('*.py'))+[f for f in (ROOT/'benchmarks').rglob('*.py') if not f.name.startswith('test')]
    files += [ROOT/'experiments/subset_search/catalogue.py', ROOT/'experiments/subset_search/runner.py',
              ROOT/'experiments/v2_kmeans_protocol/kmeans_trials.py', ROOT/'experiments/v2_kmeans_protocol/metrics.py',
              ROOT/'experiments/submission_refresh/selection.py']
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
    behavior={str(f.relative_to(ROOT)):identity(ast.dump(WithoutDocstrings().visit(ast.parse(f.read_text())),include_attributes=False)) for f in sorted(files)}
    return identity({'schema':'subset-scientific-cache-v1','candidate_id':candidate['candidate_id'],
                     'manifest_sha256':candidate['manifest_sha256'],'fingerprint':candidate['fingerprint'],
                     'source_files':manifest.get('source_files',[]),'behavior':behavior,'environment':environment_record(),
                     'protocol_sha256':digest(ROOT/'configs/subset_search/protocol.yaml'),'profile_only':bool(profile)})

def prepare(candidate,data_root,store):
    from .catalogue import materialize
    X,y,meta=materialize(candidate,Path(data_root));X=np.asarray(X,dtype=np.float64);y=np.asarray(y)
    prep=candidate.get('prep',candidate.get('preprocessing','Y0'))
    # Catalogue materialization is input preparation; embedding normalization is
    # a separate declared factor, never inferred from labels or score.
    F,info=spectral_embedding(X,len(np.unique(y)),k=5)
    if prep in ['Y2','Y3']:
        norms=np.linalg.norm(F,axis=1,keepdims=True);F=np.divide(F,norms,out=np.zeros_like(F),where=norms>0)
    A,Ainfo=knn_affinity(X,k=5);W,Winfo=knn_affinity(F,k=5)
    refs={name:store.put(value) for name,value in [('X',X),('y',y),('A',A),('F',F),('W',W)]}
    return X,y,F,A,W,{'candidate':candidate,'input_metadata':meta,'fingerprint':fingerprint_matrix(X,y),'spectral':info,'A_config':Ainfo,'W_config':Winfo,'objects':refs}

def round_embedding(G,y,K,initialization,seeds=range(50)):
    trials=[];pred=[];centers=[]
    for seed in seeds:
        try:
            fit=fit_lloyd(G,K,int(seed),initialization)
        except BaseException as exc:
            exc.partial_trials=trials
            exc.partial_predictions=np.asarray(pred)
            exc.failed_rounding_seed=int(seed)
            raise
        trials.append({'seed':int(seed),**evaluate_partition(y,fit['labels']),'inertia':fit['inertia'],'iterations':fit['kmeans_n_iter'],'warning':fit['kmeans_warning']})
        pred.append(fit['labels']);centers.append(fit['centers'])
    return trials,np.asarray(pred),np.asarray(centers)

def run_candidate(candidate,data_root,artifact_root,cpu_limit=3600,profile=False):
    os.environ.update({k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']})
    start=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root);cid=candidate['candidate_id'];folder=Path(artifact_root)/'subset'/cid;folder.mkdir(parents=True,exist_ok=True)
    result={'candidate_id':cid,'status':'RUNNING','candidate':candidate,'source':source_record(),'profile_only':profile}
    result['source']['protocol_sha256']=__import__('experiments.submission_refresh.core',fromlist=['digest']).digest(ROOT/'configs/subset_search/protocol.yaml')
    install_cpu_limit(cpu_limit)
    try:
        result['cache_identity']=scientific_cache_identity(candidate,data_root,profile=profile)
        previous_source=folder/'source.json'
        if not profile and previous_source.exists():
            old_source=json.loads(previous_source.read_text())
            if old_source.get('cache_identity')!=result['cache_identity']:
                raise ValueError('scientific cache identity mismatch; preserve old run and use a new artifact root')
            result['original_source']=old_source
        result['source']['cache_identity']=result['cache_identity']
        with threadpool_limits(limits=1):
            prep_path=folder/'representation.json'
            if prep_path.exists() and not profile:
                meta=json.loads(prep_path.read_text())
                if meta['candidate']!=candidate or meta.get('cache_identity')!=result['cache_identity']:raise ValueError('candidate or scientific cache identity changed')
                X,y,F,A,W=[store.get(meta['objects'][name]) for name in ['X','y','F','A','W']]
                if fingerprint_matrix(X,y)!=candidate['fingerprint']:raise ValueError('cached processed-data fingerprint mismatch')
            else:
                X,y,F,A,W,meta=prepare(candidate,data_root,store)
                meta['cache_identity']=result['cache_identity']
                if not profile:atomic_json(prep_path,meta)
            result['preparation_cpu_seconds']=time.process_time()-cpu
            if profile:
                timings=[];result['solver_timings']=timings
                for variant in ['E8','E13']:
                    for gamma in GAMMAS:
                        t=time.process_time();out=shrink_embedding(F,W,gamma,variant=variant,max_iter=300,tol=1e-6,eps=1e-8)
                        timings.append({'variant':variant,'gamma':gamma,'cpu_seconds':time.process_time()-t,'iterations':out.n_iterations})
                t=time.process_time()
                for seed in range(3):fit_lloyd(F,len(np.unique(y)),seed,RANDOM)
                result.update(status='PROFILE_ONLY_INELIGIBLE',solver_timings=timings,rounding_cpu_per_seed=(time.process_time()-t)/3)
            else:
                if not (folder/'source.json').exists():atomic_json(folder/'source.json',result['source'])
                K=len(np.unique(y))
                # A matched SC is retained on the exact candidate embedding.
                for init in INITS:
                    path=folder/('SC__'+init+'.json')
                    if not path.exists():
                        result['active_configuration']={'method':'sc','initialization':init,'stage':'rounding'}
                        trials,pred,centers=round_embedding(F,y,K,init)
                        atomic_json(path,{'candidate_id':cid,'method':'sc','config_id':cid+'|SC|'+init,'initialization':init,'status':'COMPLETED','trials':trials,'summary':summarize(trials),'objects':{'predictions':store.put(pred),'native_best_centers':store.put(centers[min(range(len(trials)),key=lambda i:(trials[i]['inertia'],trials[i]['seed']))]),'G':meta['objects']['F']},'solver':{'status':'NOT_APPLICABLE'}})
                for variant in ['E8','E13']:
                    for gamma in GAMMAS:
                        key=f'{variant}__{gamma:g}';solvepath=folder/(key+'__solver.json')
                        if solvepath.exists():
                            sm=json.loads(solvepath.read_text());G=store.get(sm['objects']['G'])
                        else:
                            result['active_configuration']={'method':'ssc','variant':variant,'gamma_nominal':gamma,'stage':'solver'}
                            t=time.process_time();fit=shrink_embedding(F,W,gamma,variant=variant,max_iter=300,tol=1e-6,eps=1e-8)
                            G=fit.patterns;Wfit,_=shrinkage_laplacian(W,G,eps=1e-8)
                            sm={'solver':{**iteration_diagnostics(fit),'status':'ITERATE_CONVERGED_UNCERTIFIED' if fit.converged else 'MAX_ITER_REACHED','certified':False,'gamma_nominal':gamma,'gamma_effective':gamma/(2 if variant=='E13' else 1),'variant':variant,'history':fit.history,'cpu_seconds':time.process_time()-t},'objects':{'G':store.put(G),'fitted_W':store.put(Wfit),'checkpoint':store.put({'G':store.put(G),'history':fit.history,'continuation_validity':'final primal only; fresh IRLS call is a disclosed new trajectory, not exact internal-state continuation'})}}
                            atomic_json(solvepath,sm)
                        for init in INITS:
                            path=folder/(key+'__'+init+'.json')
                            if path.exists():continue
                            result['active_configuration']={'method':'ssc','variant':variant,'gamma_nominal':gamma,'initialization':init,'stage':'rounding'}
                            trials,pred,centers=round_embedding(G,y,K,init)
                            atomic_json(path,{'candidate_id':cid,'config_id':cid+'|'+key+'|'+init,'method':'ssc','initialization':init,'variant':variant,'gamma_nominal':gamma,'gamma_effective':gamma/(2 if variant=='E13' else 1),'status':'COMPLETED','trials':trials,'summary':summarize(trials),'solver':sm['solver'],'objects':{**sm['objects'],'predictions':store.put(pred),'native_best_centers':store.put(centers[min(range(len(trials)),key=lambda i:(trials[i]['inertia'],trials[i]['seed']))])}})
                result['status']='COMPLETED'
                result.pop('active_configuration',None)
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
        if hasattr(exc,'partial_trials'):
            result['interrupted_rounding']={'completed_trials':exc.partial_trials,'failed_rounding_seed':exc.failed_rounding_seed,
                'predictions':store.put(exc.partial_predictions),'status':'INCOMPLETE_INELIGIBLE'}
    finally:
        import signal
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(folder/('profile.json' if profile else 'status.json'),result)
    return result
