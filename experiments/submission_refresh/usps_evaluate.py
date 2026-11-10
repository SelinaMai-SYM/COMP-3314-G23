"""Rounding-only evaluation of the completed same-F/W USPS numerical audit.

No loader, graph construction, embedding fit or SSC solver is called here. True
labels are read only after every frozen/stage artifact passes integrity checks.
The shared scheduler owns the reservation and the six-hour USPS repair allowance.
"""
from __future__ import annotations
from contextlib import contextmanager
import csv,gzip,hashlib,io,json,os,resource,signal,tempfile,time,traceback
from pathlib import Path
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,GREEDY
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from .core import ArtifactStore,atomic_json,digest,identity,install_cpu_limit,ResourceLedger
from .selection import summarize

STAGES=('IRLS300','uniform_PDHG','diagonal_PDHG','component_dual_flow','diagonal_warm_restart')
GAMMAS=(1.,1000.)
TERMINAL={'COMPLETED','FAILED','TIMEOUT','KILLED_OR_CRASHED','CPU_LIMIT'}


def array_hash(array):
    array=np.ascontiguousarray(array)
    return hashlib.sha256(str(array.dtype).encode()+repr(array.shape).encode()+array.tobytes()).hexdigest()


def pair_identity(F,W):
    W=sparse.csr_matrix(W).copy();W.sort_indices()
    return {'F':array_hash(F),'W_data':array_hash(W.data),'W_indices':array_hash(W.indices),
            'W_indptr':array_hash(W.indptr),'shape':list(W.shape)}


def intended_names():
    return [(f'gamma_{gamma:.8g}_{stage}',gamma,stage) for gamma in GAMMAS for stage in STAGES]


def _load_npz(path):
    with np.load(path,allow_pickle=False) as arrays:
        return {key:arrays[key] for key in arrays.files}


def _safe_file(folder,name):
    if not isinstance(name,str) or Path(name).name!=name or not name.endswith('.npz'):
        raise ValueError('unsafe or unexpected audit arrays filename')
    path=(folder/name).resolve()
    if path.parent!=folder.resolve():raise ValueError('audit arrays escape the frozen directory')
    return path


def verify_artifacts(artifact_root,*,audit_run_id='usps-numerical-audit-v1',expected_n=9298,expected_K=10):
    """Validate all inputs before any metric or K-means call.

    Missing G in a verified array archive is an explicit unavailable point.
    Missing/corrupt archives promised by metadata are integrity failures, not
    permission to evaluate only the remaining successful stages.
    """
    store=ArtifactStore(artifact_root);folder=store.root/'usps_audit'
    status_path=store.root/'task_status'/(audit_run_id+'.json')
    if not status_path.is_file():raise ValueError('USPS audit task has no terminal status record')
    status=json.loads(status_path.read_text())
    if status.get('status') not in TERMINAL:raise ValueError('USPS audit task is not terminal')
    frozen_path=folder/'frozen_pair.json';manifest_path=folder/'audit_manifest.json'
    if not frozen_path.is_file() or not manifest_path.is_file():raise ValueError('frozen pair or audit manifest is missing')
    frozen=json.loads(frozen_path.read_text());manifest=json.loads(manifest_path.read_text())
    if status.get('manifest') is not None and status['manifest']!=manifest:
        raise ValueError('audit task manifest differs from the final audit manifest')
    loaded={name:store.get(ref) for name,ref in frozen['objects'].items()}
    if not {'F','W','y'}<=loaded.keys():raise ValueError('frozen pair lacks required F/W/y objects')
    F=np.asarray(loaded['F']);W=sparse.csr_matrix(loaded['W']);y=np.asarray(loaded['y'])
    if F.ndim!=2 or y.shape!=(len(F),) or len(F)!=expected_n or len(np.unique(y))!=expected_K:
        raise ValueError('frozen input does not meet the declared evaluation shape/classes')
    if np.issubdtype(y.dtype,np.number) and not np.isfinite(y).all():raise ValueError('nonfinite frozen evaluation labels')
    if not np.isfinite(F).all() or W.shape!=(len(F),len(F)) or not np.isfinite(W.data).all():
        raise ValueError('nonfinite or incompatible frozen arrays')
    pair=pair_identity(F,W)
    if manifest.get('same_frozen_pair')!=pair:raise ValueError('audit F/W identity mismatch')
    if manifest.get('graph',{}).get('E8_capacities')!='2*gamma*w':raise ValueError('audit does not declare the E8 undirected target')
    saved_pair_path=folder/'frozen_pair.npz'
    if not saved_pair_path.is_file():raise ValueError('solver frozen-pair archive is missing')
    saved=_load_npz(saved_pair_path)
    required={'F','W_data','W_indices','W_indptr','W_shape'}
    if not required<=saved.keys():raise ValueError('solver frozen-pair archive is incomplete')
    saved_W=sparse.csr_matrix((saved['W_data'],saved['W_indices'],saved['W_indptr']),shape=tuple(saved['W_shape']))
    if pair_identity(saved['F'],saved_W)!=pair:raise ValueError('solver archive differs from the object-store F/W pair')
    names={name for name,_,_ in intended_names()};listed={}
    for record in manifest.get('records',[]):
        name=record.get('name')
        if name not in names or name in listed:raise ValueError('unregistered or duplicated USPS audit stage')
        listed[name]=record
    verified=[]
    for name,gamma,stage in intended_names():
        record=listed.get(name);stage_path=folder/(name+'.json')
        source='audit_manifest'
        if stage_path.exists():
            stage_record=json.loads(stage_path.read_text())
            if record is not None and {k:v for k,v in record.items() if k!='name'}!=stage_record:
                raise ValueError('stage metadata differs from its audit-manifest row: '+name)
            if record is None:source='terminal_stage_json_not_listed_in_manifest'
            record=stage_record
        if record is None:
            verified.append({'name':name,'gamma':gamma,'stage':stage,'metadata':{'status':'NOT_RUN_AUDIT_INTERRUPTED'},
                             'availability':'NOT_EVALUATED_MISSING_G','metadata_source':'no_record'})
            continue
        if record.get('same_frozen_pair') is not None and record['same_frozen_pair']!=pair:
            raise ValueError('stage F/W identity mismatch: '+name)
        for key in ['gamma','gamma_effective']:
            if record.get(key) is not None and float(record[key])!=gamma:raise ValueError('stage gamma mapping mismatch: '+name)
        if record.get('variant','E8')!='E8' or record.get('fidelity','radial')!='radial' or float(record.get('delta',0))!=0:
            raise ValueError('non-E8 stage in the locked USPS audit')
        if record.get('objective_target') not in [None,'undirected_E8_c=2*gamma*w','E8']:
            raise ValueError('stage objective target differs from E8')
        arrays_file=record.get('arrays_file');point={'name':name,'gamma':gamma,'stage':stage,'metadata':record,'metadata_source':source}
        if not arrays_file:
            if record.get('arrays_sha256'):raise ValueError('array hash without a recoverable filename')
            point['availability']='NOT_EVALUATED_MISSING_G';verified.append(point);continue
        path=_safe_file(folder,arrays_file)
        if arrays_file!=name+'.npz' or not path.is_file() or not record.get('arrays_sha256'):
            raise ValueError('missing/unregistered stage archive or hash: '+name)
        actual=digest(path)
        if actual!=record['arrays_sha256']:raise ValueError('stage archive hash mismatch: '+name)
        arrays=_load_npz(path)
        point.update(arrays_file=arrays_file,arrays_sha256=actual)
        if 'G' not in arrays:
            point['availability']='NOT_EVALUATED_MISSING_G'
        else:
            G=arrays['G']
            if G.shape!=F.shape or not np.isfinite(G).all():raise ValueError('invalid stage G: '+name)
            point.update(availability='VERIFIED_G',G=G,G_hash=array_hash(G))
        verified.append(point)
    return {'F':F,'W':W,'y':y,'K':expected_K,'points':verified,'pair':pair,
            'frozen':frozen,'audit_manifest':manifest,'audit_run_id':audit_run_id,'audit_task_status':status['status'],
            'provenance':{'frozen_pair_json_sha256':digest(frozen_path),'audit_manifest_sha256':digest(manifest_path),
                          'solver_frozen_npz_sha256':digest(saved_pair_path),'audit_task_status_sha256':digest(status_path),
                          'frozen_objects':frozen['objects'],'all_stages_preverified_before_evaluation':True}}


def _is_usps_repair(entry,audit_run_id):
    run_id=entry.get('run_id','');phase=entry.get('phase','')
    return run_id==audit_run_id or phase in {'mandatory_usps','mandatory_usps_evaluation','usps_evaluation'} or run_id.startswith(('usps-numerical-audit','usps-solver-evaluation','usps-evaluation'))


def remaining_allowance(task,artifact_root):
    root=Path(artifact_root);path=root/'resource_ledger.json'
    if not path.is_file():raise ValueError('evaluation requires the existing shared resource ledger')
    state=ResourceLedger(root).state();run_id=task['run_id'];audit_run_id=task.get('audit_run_id','usps-numerical-audit-v1')
    if run_id not in state['active']:raise ValueError('evaluation has no shared-ledger reservation')
    if audit_run_id in state['active']:raise ValueError('USPS audit reservation remains active')
    spent=sum(float(e['charged_cpu_seconds']) for e in state['entries'] if _is_usps_repair(e,audit_run_id))
    other_reserved=sum(float(entry['seconds']) for key,entry in state['active'].items()
                       if key!=run_id and _is_usps_repair({'run_id':key,**entry},audit_run_id))
    return min(900.,float(task.get('cpu_limit',900)),float(state['active'][run_id]['seconds']),max(0.,21600.-spent-other_reserved)),spent


@contextmanager
def _limit(seconds):
    previous=signal.getsignal(signal.SIGPROF);timer=signal.getitimer(signal.ITIMER_PROF);started=time.process_time()
    install_cpu_limit(seconds)
    try:yield
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,previous)
        if timer[0]>0:signal.setitimer(signal.ITIMER_PROF,max(0.,timer[0]-(time.process_time()-started)),timer[1])


def _point_metadata(point,F):
    meta=point.get('metadata',{});G=point['G'];stage=point['stage']
    historical=stage=='IRLS300' and bool(meta.get('complete_historical_execution',False)) and int(meta.get('protocol',{}).get('max_iter',0))==300
    certified=bool(meta.get('certified',False))
    if certified:
        certified=(-1e-9<=float(meta.get('gap',float('inf')))<=1e-5 and float(meta.get('edge_violation',float('inf')))<=1e-8
                   and float(meta.get('node_violation',float('inf')))<=1e-8)
    return {'stage':stage,'gamma_nominal':point.get('gamma'),'gamma_effective':point.get('gamma'),
            'variant':'SC' if stage=='SC_F' else 'E8','solver_status':meta.get('status','NOT_APPLICABLE'),
            'certified':certified,'relative_gap':meta.get('gap'),'primal':meta.get('primal'),'dual':meta.get('dual'),
            'edge_violation':meta.get('edge_violation'),'node_violation':meta.get('node_violation'),
            'historical_300_protocol_complete':historical,'complete_historical_execution':meta.get('complete_historical_execution',False),
            'iterations':meta.get('iterations',meta.get('iterations_completed_linear_steps')),
            'normalized_L21_movement':float(np.linalg.norm(G-F,axis=1).sum()/max(np.linalg.norm(F,axis=1).sum(),np.finfo(float).tiny)),
            'normalized_Frobenius_movement':float(np.linalg.norm(G-F)/max(np.linalg.norm(F),np.finfo(float).tiny)),
            'n_unique_G_rows':int(len(np.unique(G,axis=0))),'G_hash':array_hash(G),
            'G_hash_definition':'sha256(dtype + repr(shape) + contiguous_bytes)',
            'input_arrays_file':point.get('arrays_file'),'input_arrays_sha256':point.get('arrays_sha256'),
            'metadata_source':point.get('metadata_source','frozen_SC_anchor')}


def evaluate_verified(verified,store,folder,*,dataset='USPS'):
    """Evaluate verified points; this function never constructs a new point."""
    F=verified['F'];y=verified['y'];K=verified['K'];pair_id=identity(verified['pair'])
    if dataset=='USPS' and (len(F)!=9298 or K!=10):raise ValueError('USPS publication requires the full9298-row/10-class protocol')
    points=[{'name':'SC_F','stage':'SC_F','gamma':None,'G':F,'availability':'VERIFIED_G','metadata':{'status':'NOT_APPLICABLE'}}]+verified['points']
    records=[]
    for point in points:
        config_id=dataset+'|frozen_'+pair_id[:16]+'|'+point['name']+'|'+GREEDY
        path=folder/(point['name']+'.json')
        if point['availability']!='VERIFIED_G':
            record={'dataset':dataset,'config_id':config_id,'name':point['name'],'stage':point['stage'],
                    'gamma_nominal':point.get('gamma'),'gamma_effective':point.get('gamma'),'variant':'E8',
                    'status':'NOT_EVALUATED_MISSING_G','solver_status':point['metadata'].get('status'),
                    'certified':bool(point['metadata'].get('certified',False)),
                    'historical_300_protocol_complete':False,'n_trials':0,'trials':[],
                    'n_samples':len(F),'n_classes':K,'audit_metadata':point['metadata'],'pair_identity':verified['pair'],'provenance':verified['provenance']}
            atomic_json(path,record);records.append(record);continue
        G=point['G'];metadata=_point_metadata(point,F);Gref=store.put(G)
        signature=identity({'config_id':config_id,'G':Gref,'label_object':verified['frozen']['objects']['y'],
                            'pair_identity':verified['pair'],'protocol':{'init':GREEDY,'seeds':list(range(50)),'n_init':1,'algorithm':'lloyd','max_iter':300,'tol':1e-4}})
        seed_folder=folder/'rounding'/point['name'];trials=[];predictions=[];centers=[]
        for seed in range(50):
            checkpoint=seed_folder/(str(seed)+'.json')
            if checkpoint.exists():
                saved=json.loads(checkpoint.read_text())
                if saved.get('evaluation_signature')!=signature:raise ValueError('USPS rounding checkpoint identity changed')
            else:
                fitted=fit_lloyd(G,K,seed,GREEDY)
                saved={'evaluation_signature':signature,'trial':{'seed':seed,**evaluate_partition(y,fitted['labels']),
                       'inertia':fitted['inertia'],'iterations':fitted['kmeans_n_iter'],'warning':fitted['kmeans_warning']},
                       'prediction':store.put(fitted['labels']),'centers':store.put(fitted['centers'])}
                atomic_json(checkpoint,saved)
            trials.append(saved['trial']);predictions.append(store.get(saved['prediction']));centers.append(store.get(saved['centers']))
        summary=summarize(trials)
        record={'dataset':dataset,'config_id':config_id,'name':point['name'],'status':'COMPLETED','n_trials':50,'n_samples':len(F),'n_classes':K,
                **metadata,'trials':trials,'summary':summary,'rounding_signature':signature,
                'objects':{'G':Gref,'predictions':store.put(np.asarray(predictions)),'centers':store.put(np.asarray(centers))},
                'pair_identity':verified['pair'],'provenance':verified['provenance'],
                'audit_metadata':point.get('metadata',{}),'native_best':summary.get('native_best'),
                'statistical_scope':'50 conditional greedy++ Lloyd roundings on the exact saved point; native-best assignment has no across-run SD'}
        atomic_json(path,record);records.append(record)
    return records


def run_evaluation(task,data_root,artifact_root):
    """Public USPS-only adapter; caller reserves <=900CPU seconds in its ledger."""
    del data_root  # No data reload or fitting is allowed to replace frozen artifacts.
    started=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root)
    result={'task':task,'status':'RUNNING'};folder=store.root/'usps_audit/evaluation'/task['run_id']
    try:
        allowance,spent=remaining_allowance(task,artifact_root)
        result.update(cpu_allowance_seconds=allowance,prior_USPS_repair_charged_seconds=spent)
        if allowance<=.01:
            result['status']='NOT_RUN_USPS_BLOCK_CPU_LIMIT'
        else:
            with _limit(allowance),threadpool_limits(limits=1):
                verified=verify_artifacts(artifact_root,audit_run_id=task.get('audit_run_id','usps-numerical-audit-v1'))
                folder=folder/identity(verified['provenance'])
                records=evaluate_verified(verified,store,folder)
                result.update(status='COMPLETED',records=records,provenance=verified['provenance'],
                              complete_points=sum(r['status']=='COMPLETED' for r in records),
                              missing_G_points=sum(r['status']=='NOT_EVALUATED_MISSING_G' for r in records),
                              unique_G_hashes=len({r['G_hash'] for r in records if r.get('G_hash')}))
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(folder/'evaluation_manifest.json',result)
    return result


def export_evaluation(artifact_root,output):
    """Export verified small evaluation records; no arrays, fits or re-selection."""
    from .scalar_views import collect_usps_metadata,derive_usps_views,write_usps_views
    root=Path(artifact_root);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    metadata=collect_usps_metadata(root);derived=derive_usps_views(metadata)
    names=['usps_solver_evaluation.csv','usps_solver_evaluation_trials.csv.gz']
    selected={'tables':{name:rows for name,rows in derived['tables'].items() if name in names},
              'trial_tables':{name:rows for name,rows in derived['trial_tables'].items() if name in names}}
    # Stage both public files, then replace their final paths.
    with tempfile.TemporaryDirectory(prefix='.usps-evaluation-',dir=out) as tmp:
        tmp=Path(tmp);write_usps_views(selected,tmp)
        for name in names:os.replace(tmp/name,out/name)
    return {'configurations':len(metadata['original_evaluations']),
            'trials':len(derived['trial_tables']['usps_solver_evaluation_trials.csv.gz']),
            'source_records_recoverable':True}
