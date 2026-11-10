"""Complete independent frozen points after a candidate's non-timeout failure.

This controller is for a dedicated shared-scheduler child after the primary
cohort pass. It preserves the original failed point, source and status, and
uses only the unused portion of that candidate's original CPU allocation.
It never retries an interrupted fit or changes a grid, seed set or solver.
"""
from __future__ import annotations
import base64
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import time
import traceback

import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from SSC_method.optimizer import shrink_embedding,iteration_diagnostics
from SSC_method.objective import shrinkage_laplacian,row_l21_diagonal
from experiments.submission_refresh.core import (ROOT,ArtifactStore,THREAD_ENV,
    atomic_json,digest,identity,install_cpu_limit)
from experiments.submission_refresh.selection import summarize
from experiments.v3_reproduction.provenance import fingerprint_matrix
from .runner import GAMMAS,INITS,round_embedding,scientific_cache_identity,source_record


VARIANTS=('E8','E13')


def _raw_record(path,store):
    body=path.read_bytes()
    return {'path':str(path.relative_to(store.root)),'sha256':digest(path),
            'body':store.put({'encoding':'base64','bytes_base64':base64.b64encode(body).decode('ascii')})}


def _objects(value,store,seen):
    if isinstance(value,dict):
        if {'sha256','path','kind'}<=value.keys():
            key=(value['sha256'],value['path'])
            if key not in seen:
                item=store.get(value);seen.add(key)
                if isinstance(item,(dict,list)):_objects(item,store,seen)
        else:
            for item in value.values():_objects(item,store,seen)
    elif isinstance(value,list):
        for item in value:_objects(item,store,seen)


def _configuration(active,cid):
    if active.get('method')=='sc' and active.get('stage')=='rounding' and active.get('initialization') in INITS:
        return ['SC__'+active['initialization']]
    if active.get('method')=='ssc' and active.get('variant') in VARIANTS and active.get('gamma_nominal') in GAMMAS:
        key=f"{active['variant']}__{active['gamma_nominal']:g}"
        if active.get('stage')=='solver':return [key+'__'+init for init in INITS]
        if active.get('stage')=='rounding' and active.get('initialization') in INITS:return [key+'__'+active['initialization']]
    raise ValueError('original failure lacks an exact frozen configuration identity: '+cid)


def _cpu_used(store,candidate,status):
    original_id='subset-'+identity(candidate)[:20]
    values=[float(status['cpu_seconds'])]
    prior=store.root/'task_status'/(original_id+'.json')
    if prior.exists():
        task_status=json.loads(prior.read_text())
        if task_status.get('candidate_id')!=candidate['candidate_id'] or task_status.get('cache_identity')!=status['cache_identity']:
            raise ValueError('original scheduler status identity mismatch')
        values.append(float(task_status.get('process_cpu_seconds',task_status['cpu_seconds'])))
    ledger=store.root/'resource_ledger.json'
    if ledger.exists():
        record=json.loads(ledger.read_text())
        if original_id in record.get('active',{}):raise ValueError('original candidate is still active')
        charged=[float(entry['charged_cpu_seconds']) for entry in record.get('entries',[]) if entry['run_id']==original_id]
        if len(charged)>1:raise ValueError('duplicate original candidate CPU charges')
        values+=charged
    if any(not math.isfinite(value) or value<0 for value in values):raise ValueError('invalid original CPU accounting')
    return max(values)


def _validate(task,data_root,store):
    if task.get('post_primary') is not True:raise ValueError('completion requires explicit post_primary=true')
    if task.get('profile'):raise ValueError('profile runs cannot complete scientific candidates')
    candidate=task['candidate'];cid=candidate['candidate_id']
    if not re.fullmatch('[A-Za-z0-9_.-]+',cid) or not re.fullmatch('[A-Za-z0-9_.-]+',task['run_id']):raise ValueError('unsafe completion identifier')
    folder=store.root/'subset'/cid;status_path=folder/'status.json';source_path=folder/'source.json';prep_path=folder/'representation.json'
    for path in [status_path,source_path,prep_path]:
        if not path.is_file():raise ValueError('completion requires saved original status, source and representation')
    status=json.loads(status_path.read_text());old_source=json.loads(source_path.read_text());meta=json.loads(prep_path.read_text())
    if status.get('status')!='FAILED' or status.get('profile_only') or status.get('candidate')!=candidate:
        raise ValueError('only original non-timeout FAILED candidate executions are eligible')
    if any((store.root/'confirmation').glob('confirm-*.json')):raise ValueError('completion is prohibited after winner confirmation begins')
    cohort_path=ROOT/'configs/subset_search/executable_cohort.json';cohort=json.loads(cohort_path.read_text())
    catalogue_path=ROOT/'results/subset_search/candidate_catalogue.json'
    if digest(catalogue_path)!=cohort['catalogue_sha256'] or cid not in cohort['candidate_ids']:raise ValueError('candidate is not in the original frozen executable cohort')
    catalogue=json.loads(catalogue_path.read_text())['candidates']
    if next((entry for entry in catalogue if entry['candidate_id']==cid),None)!=candidate:raise ValueError('candidate differs from frozen catalogue')
    cap=float(cohort.get('per_candidate_limits',{}).get(cid,cohort['cpu_limit_per_candidate']))
    cache=scientific_cache_identity(candidate,data_root,profile=False)
    if any(record.get('cache_identity')!=cache for record in [status,old_source,meta]) or meta.get('candidate')!=candidate:
        raise ValueError('saved scientific cache/source/representation identity mismatch')
    X,y,F,A,W=[store.get(meta['objects'][name]) for name in ['X','y','F','A','W']]
    if fingerprint_matrix(X,y)!=candidate['fingerprint'] or meta.get('fingerprint')!=candidate['fingerprint']:
        raise ValueError('saved exact data fingerprint mismatch')
    if X.ndim!=2 or y.ndim!=1 or len(y)!=len(X) or F.ndim!=2 or len(F)!=len(X) or not np.isfinite(X).all() or not np.isfinite(F).all():
        raise ValueError('invalid saved exact data or spectral representation')
    for graph in [A,W]:
        matrix=sparse.csr_matrix(graph)
        if matrix.shape!=(len(X),len(X)) or not np.isfinite(matrix.data).all() or np.any(matrix.data<0):raise ValueError('invalid saved graph')
    blocked=set(_configuration(status.get('active_configuration',{}),cid))
    interruption=status.get('interrupted_rounding')
    if status['active_configuration']['stage']=='rounding':
        if not isinstance(interruption,dict) or not isinstance(interruption.get('failed_rounding_seed'),int) or not 0<=interruption['failed_rounding_seed']<50:
            raise ValueError('original failed rounding seed is unavailable')
    seen=set();completed={};solvers={}
    expected=['SC__'+init for init in INITS]+[f'{variant}__{gamma:g}__{init}' for variant in VARIANTS for gamma in GAMMAS for init in INITS]
    for key in expected:
        path=folder/(key+'.json')
        if not path.exists():continue
        record=json.loads(path.read_text())
        if record.get('candidate_id')!=cid or record.get('status')!='COMPLETED':raise ValueError('existing result is not a valid completed frozen point')
        if key in blocked:raise ValueError('original failed point conflicts with an existing complete result')
        if key.startswith('SC__'):
            if record.get('method')!='sc' or record.get('initialization')!=key[4:] or record.get('objects',{}).get('G')!=meta['objects']['F']:
                raise ValueError('existing SC record does not use the exact saved F/protocol')
        else:
            expected_variant,expected_gamma,expected_init=key.split('__',2)
            if record.get('method')!='ssc' or record.get('variant')!=expected_variant or record.get('gamma_nominal')!=float(expected_gamma) or record.get('initialization')!=expected_init:
                raise ValueError('existing SSC record configuration identity mismatch')
        summarize(record['trials']);_objects(record.get('objects',{}),store,seen);completed[key]=record
    for variant in VARIANTS:
        for gamma in GAMMAS:
            key=f'{variant}__{gamma:g}';path=folder/(key+'__solver.json')
            if not path.exists():continue
            record=json.loads(path.read_text());_objects(record.get('objects',{}),store,seen)
            G=store.get(record['objects']['G'])
            solver=record['solver']
            if G.shape!=F.shape or not np.isfinite(G).all() or solver.get('variant')!=variant or solver.get('gamma_nominal')!=gamma:
                raise ValueError('existing saved solver identity/shape mismatch')
            solvers[key]=record
    for key,record in completed.items():
        if key.startswith('SC__'):continue
        solver_key='__'.join(key.split('__')[:2])
        if solver_key not in solvers or record['objects'].get('G')!=solvers[solver_key]['objects']['G']:
            raise ValueError('existing completed SSC result lacks its exact saved solver')
    failures={};previous_cpu=0.
    for path in sorted((folder/'completion_failures').glob('*.json')):
        record=json.loads(path.read_text())
        if record.get('cache_identity')!=cache or record.get('candidate_id')!=cid:raise ValueError('completion failure identity mismatch')
        for key in record.get('blocked_points',[]):
            if key not in expected:raise ValueError('failure marker outside frozen grid')
            blocked.add(key);failures[key]=record
        _objects(record.get('interrupted_rounding'),store,seen)
    for path in sorted((folder/'completion_attempts').glob('*.json')):
        record=json.loads(path.read_text())
        if record.get('cache_identity')!=cache:raise ValueError('prior completion accounting identity mismatch')
        if record.get('status')=='RUNNING':raise ValueError('an unfinished completion attempt must be resolved before another attempt')
        if record.get('status')=='TIMEOUT':raise ValueError('a prior CPU timeout terminates this candidate completion campaign')
        value=float(record.get('process_cpu_seconds',record['cpu_seconds']))
        if not math.isfinite(value) or value<0:raise ValueError('invalid prior completion CPU accounting')
        previous_cpu+=value
    original_cpu=_cpu_used(store,candidate,status);remaining=cap-original_cpu-previous_cpu
    if remaining<=0:raise ValueError('original candidate CPU allocation is exhausted')
    allocation=float(task['cpu_limit'])
    if not math.isfinite(allocation) or allocation<=0 or allocation>remaining+1e-8:raise ValueError('completion reservation exceeds remaining original candidate allocation')
    return folder,status,old_source,meta,X,y,F,A,W,completed,solvers,blocked,cache,cap,original_cpu,previous_cpu


def _run_completion(task,data_root,artifact_root):
    """Finish other missing points without retrying any failed configuration.

    Caller reserves task.cpu_limit in the existing shared ledger and must use a
    fresh dedicated child process. task.post_primary must be true. Source/data
    validation occurs before fitting or writing scientific result records.
    """
    os.environ.update(THREAD_ENV);os.environ['COMP3314_ARTIFACT_ROOT']=str(artifact_root)
    wall=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root)
    (folder,original,old_source,meta,X,y,F,A,W,completed,solvers,blocked,cache,cap,
        original_cpu,previous_cpu)=_validate(task,data_root,store)
    attempt=folder/'completion_attempts'/(task['run_id']+'.json')
    if attempt.exists():raise ValueError('completion run ID already exists; preserve its original accounting')
    # Process CPU already spent on imports/preflight also belongs to this
    # candidate's remaining original allocation and the scheduler reservation.
    allocation=min(float(task['cpu_limit']),cap-original_cpu-previous_cpu)
    remaining=allocation-time.process_time()-.25
    if remaining<=0:raise ValueError('completion preflight consumed the remaining candidate allocation')
    source=source_record();source['cache_identity']=cache
    provenance={'controller':'experiments/subset_search/complete_failed.py','controller_sha256':digest(Path(__file__)),
        'source':store.put(source),'implementation_hash':source['implementation_hash'],
        'original_source':_raw_record(folder/'source.json',store),'original_status':_raw_record(folder/'status.json',store),
        'representation':_raw_record(folder/'representation.json',store),'scientific_cache_identity':cache,
        'no_failed_point_retries':True,'no_score_based_scope':True}
    K=len(np.unique(y))
    result={'schema':'subset-independent-completion-v1','task':task,'candidate_id':candidate_id(meta),
        'cache_identity':cache,'source':source,'provenance':provenance,'status':'RUNNING',
        'original_candidate_status':'FAILED','frozen_candidate_cpu_cap':cap,'original_cpu_seconds':original_cpu,
        'prior_completion_cpu_seconds':previous_cpu,'blocked_original_and_prior_failed_points':sorted(blocked),
        'completed_before_attempt':len(completed),'new_completed_points':[],'new_failed_points':[],
        'dual_status':'NOT_COMPUTED_IRLS'}
    atomic_json(attempt,result)
    def failure(keys,active,exc,original_failure=False):
        record={'candidate_id':candidate_id(meta),'cache_identity':cache,'status':'FAILED_PRESERVED',
            'blocked_points':keys,'active_configuration':active,'error':original.get('error') if original_failure else repr(exc),
            'original_failure':original_failure,'provenance':provenance}
        interrupted=original.get('interrupted_rounding') if original_failure else None
        if not original_failure and hasattr(exc,'partial_trials'):
            interrupted={'completed_trials':exc.partial_trials,'failed_rounding_seed':exc.failed_rounding_seed,
                'predictions':store.put(exc.partial_predictions),'status':'INCOMPLETE_INELIGIBLE'}
        if interrupted is not None:record['interrupted_rounding']=interrupted
        path=folder/'completion_failures'/((identity({'keys':keys,'original':original_failure})[:24])+'.json')
        if not path.exists():atomic_json(path,record)
        blocked.update(keys);result['new_failed_points'].extend(keys if not original_failure else [])
    failure(_configuration(original['active_configuration'],candidate_id(meta)),original['active_configuration'],None,True)
    def rounding(key,G,sm,variant=None,gamma=None,init=None):
        if key in completed or key in blocked:return
        active={'method':'sc' if variant is None else 'ssc','stage':'rounding','initialization':init}
        if variant is not None:active.update(variant=variant,gamma_nominal=gamma)
        result['active_configuration']=active
        try:
            trials,pred,centers=round_embedding(G,y,K,init)
            objects={'G':meta['objects']['F']} if sm is None else dict(sm['objects'])
            objects.update(predictions=store.put(pred),native_best_centers=store.put(centers[min(range(len(trials)),key=lambda i:(trials[i]['inertia'],trials[i]['seed']))]))
            record={'candidate_id':candidate_id(meta),'config_id':candidate_id(meta)+('|SC|'+init if variant is None else f'|{variant}__{gamma:g}|{init}'),
                'method':active['method'],'status':'COMPLETED','initialization':init,'trials':trials,'summary':summarize(trials),
                'solver':{'status':'NOT_APPLICABLE'} if sm is None else sm['solver'],'objects':objects,
                'source':source,'completion_provenance':provenance,'dual_status':'NOT_COMPUTED_IRLS'}
            if variant is not None:record.update(variant=variant,gamma_nominal=gamma,gamma_effective=gamma/(2 if variant=='E13' else 1))
            target=folder/(key+'.json')
            if target.exists():raise ValueError('refusing to replace an existing completed configuration')
            atomic_json(target,record);completed[key]=record;result['new_completed_points'].append(key)
        except RuntimeError as exc:failure([key],active,exc)
    remaining=allocation-time.process_time()-.25
    if remaining<=0:raise ValueError('completion provenance accounting consumed the remaining allocation')
    install_cpu_limit(remaining)
    try:
        with threadpool_limits(limits=1):
            for init in INITS:rounding('SC__'+init,F,None,init=init)
            for variant in VARIANTS:
                for gamma in GAMMAS:
                    key=f'{variant}__{gamma:g}';keys=[key+'__'+init for init in INITS]
                    if all(point in completed or point in blocked for point in keys):continue
                    if key not in solvers:
                        active={'method':'ssc','variant':variant,'gamma_nominal':gamma,'stage':'solver'};result['active_configuration']=active
                        try:
                            begin=time.process_time();fit=shrink_embedding(F,W,gamma,variant=variant,max_iter=300,tol=1e-6,eps=1e-8)
                            G=fit.patterns;fitted_W,_=shrinkage_laplacian(W,G,eps=1e-8)
                            refs={'G':store.put(G),'fitted_W':store.put(fitted_W),'fidelity_weights_S_diagonal':store.put(row_l21_diagonal(G-F,1e-8))}
                            refs['checkpoint']=store.put({'G':refs['G'],'history':fit.history,'fidelity_weights_S_diagonal':refs['fidelity_weights_S_diagonal'],
                                'continuation_validity':'Final primal only; an interrupted IRLS fit is never resumed or retried by this controller.'})
                            sm={'solver':{**iteration_diagnostics(fit),'status':'ITERATE_CONVERGED_UNCERTIFIED' if fit.converged else 'MAX_ITER_REACHED',
                                'certified':False,'gamma_nominal':gamma,'gamma_effective':gamma/(2 if variant=='E13' else 1),'variant':variant,'history':fit.history,'cpu_seconds':time.process_time()-begin,
                                'dual_status':'NOT_COMPUTED_IRLS','fidelity_weights_definition':'S_ii=1/(2 max(||G_i-F_i||_2,1e-8)); diagnostic reconstructed at final G, not the previous frozen linear solve.'},
                                'objects':refs,'source':source,'completion_provenance':provenance}
                            target=folder/(key+'__solver.json')
                            if target.exists():raise ValueError('refusing to replace an existing solver record')
                            atomic_json(target,sm);solvers[key]=sm
                        except RuntimeError as exc:failure(keys,active,exc);continue
                    sm=solvers[key];G=store.get(sm['objects']['G'])
                    for init in INITS:rounding(key+'__'+init,G,sm,variant,gamma,init)
        result['status']='COMPLETED_WITH_PRESERVED_FAILURES';result.pop('active_configuration',None)
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
        if 'active_configuration'in result:
            failure(_configuration(result['active_configuration'],candidate_id(meta)),result['active_configuration'],exc)
    finally:
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,process_cpu_seconds=time.process_time(),wall_seconds=time.perf_counter()-wall,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,completed_after_attempt=len(completed),
            original_plus_completion_cpu_seconds=original_cpu+previous_cpu+time.process_time())
        atomic_json(attempt,result)
        # The original candidate status and source remain byte-for-byte intact.
        records=sorted(str(path.relative_to(store.root)) for path in (folder/'completion_attempts').glob('*.json'))
        atomic_json(folder/'completion_status.json',{'schema':'subset-completion-index-v1','original_status':'FAILED','latest_status':result['status'],
            'attempt_records':records,'cache_identity':cache,'original_source_untouched':True,'original_status_untouched':True})
    return result


def candidate_id(meta):
    return meta['candidate']['candidate_id']


def run_completion(task,data_root,artifact_root):
    """Run one post-primary completion under an exclusive candidate lock.

    The caller owns the shared ledger reservation. A fresh dedicated child is
    required because full worker CPU, including imports, is charged to the cap.
    """
    import fcntl
    cid=task.get('candidate',{}).get('candidate_id','')
    if not re.fullmatch('[A-Za-z0-9_.-]+',cid):raise ValueError('unsafe completion candidate ID')
    folder=Path(artifact_root)/'subset'/cid
    if not folder.is_dir():raise ValueError('original candidate folder is unavailable')
    with (folder/'.completion.lock').open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('another completion controller owns this candidate') from exc
        try:return _run_completion(task,data_root,artifact_root)
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
