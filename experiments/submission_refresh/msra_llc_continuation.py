"""Numerical LLC repair using the existing library's dense eigensolver branch.

The original sparse ARPACK failure remains unchanged. This adapter keeps the
local regression operator, all fifteen parameter pairs, row normalization and
all fifty Yu-Shi seeds fixed. It neither rereuns completed PCA endpoints nor
chooses a backend or cohort using ACC/NMI.
"""
from __future__ import annotations
import json,resource,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from .core import ROOT,ArtifactStore,atomic_json,digest,identity,install_cpu_limit
from .selection import summarize

DATASET='MSRA25_EBSA_16x16'
RIDGE=(.1,1.,1.5)
BANDWIDTH=(.0625,.25,1.,4.,16.)
SEEDS=tuple(range(50))


def configurations(task):
    """The original fifteen pairs, with no additional model parameters."""
    if tuple(map(float,task.get('llc_ridge',RIDGE)))!=RIDGE or tuple(map(float,task.get('llc_bandwidth',BANDWIDTH)))!=BANDWIDTH:
        raise ValueError('LLC continuation must retain the complete frozen3-by5 grid')
    if task.get('dataset')!=DATASET or tuple(task.get('seeds',SEEDS))!=SEEDS:
        raise ValueError('LLC continuation dataset or full seed protocol changed')
    return [{'name':f'llc__{reg:g}__{bandwidth:g}','ridge':reg,'bandwidth_factor':bandwidth,
             'n_neighbors':5,'discretization_max_iter':300,'discretization_tol':1e-7,
             'kernel':'gaussian','initialization':'YU_SHI','seeds':list(SEEDS)}
            for reg in RIDGE for bandwidth in BANDWIDTH]


def _inputs(task,store,source):
    old_id=task.get('continue_from','msra-other-v1');prior=store.root/'baseline'/old_id
    old_status_path=prior/'status.json';old_input_path=prior/'input.json'
    if not old_status_path.is_file() or not old_input_path.is_file():raise ValueError('original MSRA failure/input provenance unavailable')
    status=json.loads(old_status_path.read_text());inp=json.loads(old_input_path.read_text());old_task=status.get('task',{})
    if status.get('status')!='FAILED' or 'ArpackNoConvergence' not in str(status.get('error')):
        raise ValueError('expected terminal sparse ARPACK failure is not recorded')
    if old_task.get('dataset')!=DATASET or old_task.get('block')!='msra_other':raise ValueError('original MSRA task identity differs')
    if tuple(map(float,old_task.get('llc_ridge',[])))!=RIDGE or tuple(map(float,old_task.get('llc_bandwidth',[])))!=BANDWIDTH:
        raise ValueError('original LLC grid differs from continuation declaration')
    refs=inp.get('objects',{});X=store.get(refs['X']);y=store.get(refs['y'])
    if X.shape!=(1799,256) or np.asarray(y).shape!=(1799,) or len(np.unique(y))!=12 or not np.isfinite(X).all():
        raise ValueError('continuation must use the full native16-by16 MSRA input')
    old_source=inp.get('source',status.get('source',{}))
    if old_source.get('environment')!=source.get('environment'):raise ValueError('LLC continuation environment changed')
    libraries=sorted(set(list((ROOT/'baselines/llc').glob('*.py'))+
                         list((ROOT/'baselines/spectral_clustering').glob('*.py'))+[ROOT/'baselines/common.py']))
    libraries=[p for p in libraries if not p.name.startswith('test')]
    source_archive=old_source.get('source_archive')
    if not source_archive:raise ValueError('original recoverable scientific source archive is missing')
    original_bodies=store.get(source_archive);verified=[]
    for path in libraries:
        relative=path.relative_to(ROOT).as_posix();current=digest(path)
        if old_source.get('source_files',{}).get(relative)!=current or source.get('source_files',{}).get(relative)!=current:
            raise ValueError('frozen LLC library bytes changed: '+relative)
        if relative not in original_bodies or __import__('hashlib').sha256(original_bodies[relative].encode()).hexdigest()!=current:
            raise ValueError('original LLC library body cannot be recovered: '+relative)
        verified.append({'path':relative,'sha256':current})
    completed=[]
    for path in sorted(prior.glob('*.json')):
        record=json.loads(path.read_text())
        if record.get('method') not in ['kmeans','pca_kmeans','pca_sc'] or 'trials' not in record:continue
        seeds=[int(row['seed']) for row in record['trials']]
        if record.get('status')!='COMPLETED' or sorted(seeds)!=list(SEEDS) or len(set(seeds))!=50:
            raise ValueError('original completed PCA/Kmeans inventory is incomplete')
        completed.append({'config_id':record['config_id'],'record_path':str(path.relative_to(store.root)),
                          'record_sha256':digest(path),'method':record['method'],'seed_count':50})
    if len(completed)!=31:raise ValueError('expected31 already-complete MSRA Kmeans/PCA endpoints')
    proof={'schema':'msra-llc-dense-numerical-repair-v1','original_run_id':old_id,
           'original_status_sha256':digest(old_status_path),'original_input_sha256':digest(old_input_path),
           'original_status_object':store.put(status),'original_input_object':store.put(inp),
           'original_source_archive':source_archive,'frozen_fit_libraries':verified,
           'original_sparse_failure':{'status':status['status'],'error':status['error'],'active_configuration':status.get('active_configuration')},
           'reused_input_objects':refs,'retained_Kmeans_PCA_endpoints':completed,
           'target':'smallest12 eigenvectors of (I-R).T@(I-R), then existing row normalization',
           'changed_numerical_choice':'existing llc_normalized_embedding dense_threshold=n; numpy.linalg.eigh',
           'unchanged_model_grid':configurations(task),'no_ACC_NMI_used_for_repair_or_cohort':True,
           'no_completed_PCA_or_Kmeans_reruns':True}
    return X,y,inp,proof


def eigen_diagnostics(regression,raw,eigenvalues):
    """Independent operator action checks, without another eigenproblem solve."""
    residual=raw-regression@raw
    applied=residual-regression.T@residual
    absolute=float(np.linalg.norm(applied-raw*np.asarray(eigenvalues)[None,:]))
    relative=absolute/max(1.,float(np.linalg.norm(applied)),float(np.linalg.norm(raw*np.asarray(eigenvalues)[None,:])))
    orthogonal=float(np.linalg.norm(raw.T@raw-np.eye(raw.shape[1])))
    out={'absolute_eigen_residual_Frobenius':absolute,'normalized_eigen_residual':relative,
         'raw_eigenvector_orthogonality_Frobenius':orthogonal,
         'minimum_returned_eigenvalue':float(np.min(eigenvalues)),
         'acceptance_tolerance':1e-8,'operator':'(I-R).T@(I-R)'}
    out['qualified']=bool(relative<=1e-8 and orthogonal<=1e-8 and out['minimum_returned_eigenvalue']>=-1e-10)
    return out


def _fit(X,config,store):
    from baselines.llc import llc_normalized_embedding
    before=time.process_time();base=float(np.mean(np.linalg.norm(X,axis=1)))**2
    # The exact existing dense branch is selected uniformly for all fifteen
    # configurations before performance evaluation, rather than changing R.
    F,info=llc_normalized_embedding(X,12,5,config['ridge'],'gaussian',base*config['bandwidth_factor'],
                                  dense_threshold=len(X),return_state=True)
    state=info.pop('fit_state');diagnostic=eigen_diagnostics(state['regression_matrix'],state['raw_embedding'],info['eigenvalues'])
    residual=sparse.eye(len(X),format='csr')-state['regression_matrix']
    gram=(residual.T@residual).toarray();gram=.5*(gram+gram.T)
    objects={'F':store.put(F),'G':store.put(F),'dense_Gram':store.put(gram),
             **{name:store.put(value) for name,value in state.items()}}
    return F,{'info':info,'objects':objects,'eigen_diagnostics':diagnostic,
              'parameters':{**config,'bandwidth':base*config['bandwidth_factor'],'dense_threshold':len(X)},
              'fit_cpu_seconds':time.process_time()-before,'numerical_solver':'numpy.linalg.eigh existing dense branch',
              'target_unchanged':True,'original_sparse_run_succeeded':False}


def _profile(task,X,store,folder,proof):
    from baselines.llc import yu_shi_discretize_state
    config=configurations(task)[0];F,fit=_fit(X,config,store)
    if not fit['eigen_diagnostics']['qualified']:raise ArithmeticError('dense profile eigenpair residual check failed')
    started=time.process_time();pred=[];rotations=[]
    for seed in range(3):
        state=yu_shi_discretize_state(F,seed,300,1e-7);pred.append(state['labels']);rotations.append(state['rotation'])
    per_seed=(time.process_time()-started)/3
    record={'status':'PROFILE_ONLY_INELIGIBLE','task':task,'fit':fit,'compatibility_proof':store.put(proof),
            'rounding_cpu_per_seed':per_seed,'profile_rounding_seeds':[0,1,2],
            'profile_objects':{'predictions':store.put(np.asarray(pred)),'rotations':store.put(np.asarray(rotations))},
            'projected15_configuration_CPU_seconds':15*fit['fit_cpu_seconds']+15*50*per_seed+30.,
            'no_evaluation_labels_or_ACC_NMI_used':True,'formal_fit_must_be_rerun':True}
    atomic_json(folder/'profile.json',record)
    return record


def run_continuation(task,data_root,artifact_root):
    """One shared-scheduler job; no worker pool or independent compute ledger."""
    del data_root  # Exact original input objects, never a replacement source.
    start=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root)
    folder=store.root/'baseline'/task['run_id'];folder.mkdir(parents=True,exist_ok=True)
    result={'task':task,'status':'RUNNING'};install_cpu_limit(task['cpu_limit'])
    try:
        with threadpool_limits(limits=1):
            from experiments.subset_search.runner import source_record
            source=source_record();result['source']=source
            configs=configurations(task);X,y,old_input,proof=_inputs(task,store,source)
            atomic_json(folder/'input.json',{'dataset':DATASET,'metadata':old_input.get('metadata'),
                'objects':old_input['objects'],'source':source,'numerical_repair_proof':store.put(proof)})
            if task.get('profile'):
                result.update(_profile(task,X,store,folder,proof));return result
            profile_id=task.get('required_profile_run_id')
            profile_path=store.root/'task_status'/(str(profile_id)+'.json')
            if not profile_id or not profile_path.is_file():raise ValueError('required label-blind dense profile has not completed')
            profile=json.loads(profile_path.read_text())
            if profile.get('status')!='PROFILE_ONLY_INELIGIBLE' or not profile.get('no_evaluation_labels_or_ACC_NMI_used'):
                raise ValueError('required dense profile is not label-blind/ineligible')
            proof_ref=store.put(proof);atomic_json(folder/'numerical_repair_proof.json',proof)
            failures=[]
            from baselines.llc import yu_shi_discretize_state
            from experiments.v2_kmeans_protocol.metrics import evaluate_partition
            for config in configs:
                name=config['name'];path=folder/(name+'.json');result['active_configuration']=name
                if path.exists():
                    previous=json.loads(path.read_text())
                    if previous.get('status')=='COMPLETED' and sorted(row['seed'] for row in previous['trials'])==list(SEEDS):continue
                    raise ValueError('incomplete terminal result already exists; retain it under its original run ID')
                config_id=task['run_id']+f"|{config['ridge']}|{config['bandwidth_factor']}"
                signature=identity({'parameters':config,'input_objects':old_input['objects'],
                                    'libraries':proof['frozen_fit_libraries'],'environment':source['environment'],
                                    'backend':'existing_dense_branch','shape':list(X.shape)})
                fitpath=folder/(name+'__fit.json')
                try:
                    if fitpath.exists():
                        fitted=json.loads(fitpath.read_text())
                        if fitted.get('fit_signature')!=signature:raise ValueError('dense LLC checkpoint identity changed')
                        F=store.get(fitted['objects']['F'])
                    else:
                        F,fitted=_fit(X,config,store);fitted.update(dataset=DATASET,config_id=config_id,fit_signature=signature,
                            compatibility_proof=proof_ref,source=source)
                        atomic_json(fitpath,fitted)
                    if not fitted['eigen_diagnostics']['qualified']:raise ArithmeticError('dense eigenpair residual/orthogonality check failed')
                    trials=[];pred=[];rotations=[];diagnostics=[];seed_failures=[]
                    for seed in SEEDS:
                        checkpoint=folder/'rounding'/name/(str(seed)+'.json')
                        if checkpoint.exists():
                            state=json.loads(checkpoint.read_text())
                            if state.get('fit_signature')!=signature or state.get('seed')!=seed:raise ValueError('LLC rounding checkpoint identity mismatch')
                        else:
                            try:
                                fitted_state=yu_shi_discretize_state(F,seed,300,1e-7)
                                labels=fitted_state.pop('labels');rotation=fitted_state.pop('rotation')
                                native=float(fitted_state['objective'])
                                if not np.isfinite(native):raise ArithmeticError('nonfinite Yu-Shi Procrustes objective')
                                state={'status':'COMPLETED','seed':seed,'fit_signature':signature,
                                    'trial':{'seed':seed,**evaluate_partition(y,labels),'native_objective':native},
                                    'objects':{'predictions':store.put(labels),'rotation':store.put(rotation)},'diagnostics':fitted_state}
                            except Exception as exc:
                                state={'status':'TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED','seed':seed,
                                    'fit_signature':signature,'error':repr(exc)}
                                atomic_json(checkpoint,state)
                                if isinstance(exc,TimeoutError):raise
                            atomic_json(checkpoint,state)
                        if state['status']!='COMPLETED':
                            seed_failures.append({'seed':seed,'status':state['status'],'error':state.get('error')});continue
                        trials.append(state['trial']);pred.append(store.get(state['objects']['predictions']));rotations.append(store.get(state['objects']['rotation']))
                        diagnostics.append({'seed':seed,**state['diagnostics']})
                    complete=len(trials)==50 and not seed_failures
                    record={'dataset':DATASET,'method':'llc','initialization':'YU_SHI','config_id':config_id,
                        'status':'COMPLETED' if complete else 'INCOMPLETE_FAILED_SEEDS','parameters':fitted['parameters'],
                        'trials':trials,'summary':summarize(trials,objective='native_objective') if complete else None,
                        'objects':{**fitted['objects'],'predictions':store.put(np.asarray(pred)),'rotations':store.put(np.asarray(rotations))},
                        'discretization_diagnostics':diagnostics,'seed_failures':seed_failures,'source':source,
                        'info':fitted['info'],'eigen_diagnostics':fitted['eigen_diagnostics'],
                        'numerical_repair':{'backend':fitted['numerical_solver'],'original_run_id':task.get('continue_from'),
                            'original_sparse_status':'FAILED_ARPACK_NONCONVERGENCE','proof':proof_ref,'target_and15_pair_grid_unchanged':True},
                        'native_objective_definition':'sum ||one_hot(labels)-F@rotation||^2, within one fixed F only',
                        'qualification':'Explicit dense numerical LLC repair; the original sparse ARPACK run did not complete.'}
                    atomic_json(path,record)
                    if not complete:failures.append(name)
                except TimeoutError:raise
                except Exception as exc:
                    failures.append(name);atomic_json(path,{'dataset':DATASET,'method':'llc','config_id':config_id,
                        'status':'FAILED','parameters':config,'trials':[],'error':repr(exc),'source':source,'compatibility_proof':proof_ref})
            result.pop('active_configuration',None)
            result.update(status='FAILED' if failures else 'COMPLETED',failed_configurations=failures,
                          intended_configurations=15,completed_existing_PCA_Kmeans=31,compatibility_proof=proof_ref)
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(folder/'status.json',result)
    return result
