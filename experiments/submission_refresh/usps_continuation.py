"""Two bounded same-objective USPS warm restarts, preserving the original audit.

Only frozen F/W and label-free primal/dual values select initialization. New
attempts are immutable objects in usps_continuations/, outside usps_audit/. True
labels are loaded only by the separate rounding adapter after fitting finishes.
"""
from __future__ import annotations
import json,resource,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from method_extension.next_round.certified_solver import solve,graph_arrays,objective,certificate
from .core import ArtifactStore,ResourceLedger,atomic_json,digest,identity,install_cpu_limit
from .usps_evaluate import array_hash,pair_identity,intended_names,TERMINAL,_is_usps_repair


def remaining_capacity(task,artifact_root,cap=1800.):
    root=Path(artifact_root)
    if not (root/'resource_ledger.json').is_file():raise ValueError('existing shared ledger is required')
    state=ResourceLedger(root).state();run_id=task['run_id'];audit_id=task.get('audit_run_id','usps-numerical-audit-v1')
    if run_id not in state['active']:raise ValueError('USPS continuation lacks a shared reservation')
    if audit_id in state['active']:raise ValueError('original USPS audit remains active')
    spent=sum(float(e['charged_cpu_seconds']) for e in state['entries'] if _is_usps_repair(e,audit_id))
    reserved=sum(float(e['seconds']) for key,e in state['active'].items()
                 if key!=run_id and _is_usps_repair({'run_id':key,**e},audit_id))
    return min(float(cap),float(task['cpu_limit']),float(state['active'][run_id]['seconds']),max(0.,21600-spent-reserved)),spent


def _npz(path):
    with np.load(path,allow_pickle=False) as arrays:return {key:arrays[key] for key in arrays.files}


def warm_initialization(F,W,gamma,candidates):
    """Choose actual primal and recovered feasible dual points without labels."""
    B,_,_,w=graph_arrays(W);c=2*gamma*w
    best_G=F.copy();best_P=objective(F,F,B,c);G_source={'record':'frozen_F','array':'F','value':best_P}
    best_q=np.zeros((len(w),F.shape[1]));best_D=0.;q_source={'record':'zero_feasible_dual','value':0.,'recovery_alpha':1.}
    observations=[]
    for item in candidates:
        for key in ['G','checkpoint_G_best','checkpoint_G_last']:
            if key not in item['arrays']:continue
            G=item['arrays'][key]
            if G.shape!=F.shape or not np.isfinite(G).all():raise ValueError('invalid same-objective primal checkpoint')
            P=objective(G,F,B,c);observations.append({'record':item['name'],'array':key,'primal':P,'array_hash':array_hash(G)})
            if P<best_P:
                best_G=G.copy();best_P=P;G_source={'record':item['name'],'array':key,'value':P,'array_hash':array_hash(G)}
        for key in ['q','checkpoint_q_best','checkpoint_q_last']:
            if key not in item['arrays']:continue
            q=item['arrays'][key]
            if q.shape!=best_q.shape or not np.isfinite(q).all():raise ValueError('invalid original-capacity dual checkpoint')
            feasible=certificate(q,F,B,c);D=feasible['dual']
            observations.append({'record':item['name'],'array':key,'dual_after_feasible_recovery':D,
                                 'recovery_alpha':feasible['alpha'],'array_hash':array_hash(q)})
            if D>best_D:
                best_q=feasible['q'];best_D=D;q_source={'record':item['name'],'array':key,'value':D,
                    'recovery_alpha':feasible['alpha'],'original_array_hash':array_hash(q),'feasible_array_hash':array_hash(best_q)}
    if best_P<best_D-1e-9*max(1.,abs(best_P),abs(best_D)):raise ArithmeticError('initial primal below feasible dual')
    return best_G,best_q,{'initial_primal':best_P,'initial_dual':best_D,
        'initial_relative_gap':(best_P-best_D)/max(1.,abs(best_P),abs(best_D)),
        'primal_source':G_source,'dual_source':q_source,'candidate_values':observations,
        'selection':'minimum exact E8 primal and maximum independently feasible E8 dual; no labels or clustering metrics'}


def load_problem(task,store):
    gamma=float(task['gamma'])
    if gamma not in [1.,1000.]:raise ValueError('only the two locked E8 gamma targets are permitted')
    folder=store.root/'usps_audit';audit_id=task.get('audit_run_id','usps-numerical-audit-v1')
    status_path=store.root/'task_status'/(audit_id+'.json')
    status=json.loads(status_path.read_text()) if status_path.is_file() else {}
    if status.get('status') not in TERMINAL:raise ValueError('original audit must have a terminal task status')
    frozen_path=folder/'frozen_pair.json';manifest_path=folder/'audit_manifest.json'
    frozen=json.loads(frozen_path.read_text());manifest=json.loads(manifest_path.read_text())
    if status.get('manifest') is not None and status['manifest']!=manifest:raise ValueError('original terminal audit manifest differs')
    # Labels are deliberately not dereferenced anywhere in this fitting adapter.
    F=store.get(frozen['objects']['F']);W=store.get(frozen['objects']['W'])
    if F.shape!=(9298,10) or W.shape!=(9298,9298) or not np.isfinite(F).all():raise ValueError('the full frozen USPS F/W protocol is required')
    pair=pair_identity(F,W)
    if pair!=manifest.get('same_frozen_pair') or manifest.get('graph',{}).get('E8_capacities')!='2*gamma*w':
        raise ValueError('frozen pair or E8 target identity mismatch')
    original_files={str(p.relative_to(store.root)):digest(p) for p in [frozen_path,manifest_path,folder/'frozen_pair.npz',status_path]}
    saved=_npz(folder/'frozen_pair.npz')
    saved_W=sparse.csr_matrix((saved['W_data'],saved['W_indices'],saved['W_indptr']),shape=tuple(saved['W_shape']))
    if pair_identity(saved['F'],saved_W)!=pair:raise ValueError('solver frozen NPZ differs from the anchor objects')
    allowed={name:(g,stage) for name,g,stage in intended_names()};seen=set();candidates=[]
    for record in manifest.get('records',[]):
        name=record.get('name')
        if name not in allowed or name in seen:raise ValueError('unknown/duplicate original audit stage')
        seen.add(name);g,stage=allowed[name]
        if record.get('same_frozen_pair') not in [None,pair]:raise ValueError('stage pair identity differs')
        if record.get('variant','E8')!='E8' or record.get('fidelity','radial')!='radial' or float(record.get('delta',0))!=0:
            raise ValueError('stage does not target unsquared E8')
        if record.get('objective_target') not in [None,'E8','undirected_E8_c=2*gamma*w']:raise ValueError('wrong stage objective target')
        for field in ['gamma','gamma_effective']:
            if record.get(field) is not None and float(record[field])!=g:raise ValueError('original stage gamma mismatch')
        metadata_path=folder/(name+'.json')
        if metadata_path.exists():
            metadata=json.loads(metadata_path.read_text())
            if metadata!={k:v for k,v in record.items() if k!='name'}:raise ValueError('stage JSON differs from its immutable manifest row')
            original_files[str(metadata_path.relative_to(store.root))]=digest(metadata_path)
        if not record.get('arrays_file'):continue
        if record['arrays_file']!=name+'.npz':raise ValueError('unexpected original stage array path')
        path=folder/record['arrays_file']
        if not path.is_file() or digest(path)!=record.get('arrays_sha256'):raise ValueError('original stage array missing/corrupt')
        original_files[str(path.relative_to(store.root))]=digest(path)
        if g==gamma:candidates.append({'name':name,'arrays':_npz(path),'metadata':record})
    G,q,initial=warm_initialization(F,W,gamma,candidates)
    provenance={'original_files_sha256':original_files,'pair_identity':pair,'gamma':gamma,
                'frozen_objects':frozen['objects'],'labels_loaded_for_fitting':False,
                'original_solver_source_commit':manifest.get('source_commit'),'original_solver_source_fingerprint':manifest.get('source_fingerprint')}
    return F,W,G,q,initial,provenance


def assert_originals_unchanged(store,provenance):
    for relative,sha in provenance['original_files_sha256'].items():
        if digest(store.root/relative)!=sha:raise ValueError('original audit changed during continuation: '+relative)


def new_attempt_folder(store,run_id):
    if not isinstance(run_id,str) or Path(run_id).name!=run_id or run_id in ['','.','..']:raise ValueError('invalid continuation run ID')
    base=store.root/'usps_continuations';base.mkdir(exist_ok=True)
    if base.resolve().is_relative_to((store.root/'usps_audit').resolve()):raise ValueError('continuations cannot overwrite the original audit')
    folder=base/run_id
    if folder.exists():raise ValueError('immutable continuation directory exists; retain it and use a new run ID')
    folder.mkdir()
    return folder


def run_continuation(task,data_root,artifact_root):
    """A bounded numerical warm restart, not an uninterrupted trajectory claim."""
    del data_root
    started=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root);folder=None
    result={'task':task,'status':'RUNNING'}
    try:
        allowed,spent=remaining_capacity(task,artifact_root,1800.)
        result.update(cpu_allowance_seconds=allowed,prior_USPS_repair_charged_seconds=spent)
        if allowed<=15:
            result['status']='NOT_RUN_USPS_BLOCK_CPU_LIMIT';return result
        install_cpu_limit(allowed)
        with threadpool_limits(limits=1):
            F,W,G0,q0,initial,provenance=load_problem(task,store)
            folder=new_attempt_folder(store,task['run_id'])
            from experiments.subset_search.runner import source_record
            source=source_record();result.update(source=source,initialization=initial,provenance=provenance)
            atomic_json(folder/'input.json',{'task':task,'provenance':provenance,'initialization':initial,
                'source':source,'objects':{'G_init':store.put(G0),'q_init':store.put(q0)}})
            max_iter=int(task.get('max_iter',300000))
            if not 0<max_iter<=300000:raise ValueError('continuation iteration budget exceeds300000')
            solver_cpu=max(.01,allowed-(time.process_time()-cpu)-10.)
            fitted=solve(F,W,float(task['gamma']),G_init=G0,q_init=q0,preconditioned=True,
                max_iter=max_iter,cpu_time_limit=solver_cpu,time_limit=max(60.,solver_cpu*3),gap_tol=1e-5,
                check_every=50,return_checkpoint=True,warm_start_irls=False)
            arrays={};metadata={}
            for key,value in fitted.items():
                if isinstance(value,np.ndarray):arrays[key]=value
                elif key=='checkpoint':
                    metadata['checkpoint']={}
                    for name,item in value.items():
                        if isinstance(item,np.ndarray):arrays['checkpoint_'+name]=item
                        else:metadata['checkpoint'][name]=item
                else:metadata[key]=value
            np.savez_compressed(folder/'fit_arrays.npz',**arrays)
            assert_originals_unchanged(store,provenance)
            result.update(status='COMPLETED',solver=metadata,arrays_file='fit_arrays.npz',arrays_sha256=digest(folder/'fit_arrays.npz'),
                objects={key:store.put(value) for key,value in arrays.items()},
                gamma_effective=float(task['gamma']),variant='E8',max_iter=max_iter,
                target='undirected_E8_c=2*gamma*w',labels_loaded_for_fitting=False,
                qualification='Separate numerical same-objective warm restart; original ten attempts and historical selections are unchanged.')
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        # Existing attempts are never rewritten, including on a rejected rerun.
        if folder is not None and not (folder/'result.json').exists():atomic_json(folder/'result.json',result)
    return result


def run_rounding(task,data_root,artifact_root):
    """Round additional saved outputs separately, only after their fits finish."""
    del data_root
    from .usps_evaluate import verify_artifacts,evaluate_verified,remaining_allowance
    started=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root);folder=None
    result={'task':task,'status':'RUNNING'}
    try:
        allowed,spent=remaining_allowance(task,artifact_root)
        result.update(cpu_allowance_seconds=allowed,prior_USPS_repair_charged_seconds=spent)
        if allowed<=.01:result['status']='NOT_RUN_USPS_BLOCK_CPU_LIMIT';return result
        install_cpu_limit(allowed)
        with threadpool_limits(limits=1):
            verified=verify_artifacts(artifact_root,audit_run_id=task.get('audit_run_id','usps-numerical-audit-v1'))
            points=[];additional=[]
            ledger=ResourceLedger(artifact_root).state()
            for run_id in task['continuation_run_ids']:
                if run_id in ledger['active']:raise ValueError('a continuation fit remains active')
                status_path=store.root/'task_status'/(run_id+'.json')
                status=json.loads(status_path.read_text()) if status_path.is_file() else {}
                if status.get('status') not in TERMINAL:raise ValueError('continuation task is not terminal')
                path=store.root/'usps_continuations'/run_id/'result.json'
                if not path.is_file():
                    points.append({'name':run_id,'stage':'diagonal_continuation','gamma':None,'metadata':{'status':status['status']},'availability':'NOT_EVALUATED_MISSING_G'});continue
                record=json.loads(path.read_text())
                if record.get('provenance',{}).get('pair_identity')!=verified['pair']:raise ValueError('continuation F/W differs from the original evaluated pair')
                gamma=record.get('gamma_effective',record.get('task',{}).get('gamma'))
                if gamma not in [1.,1000.]:raise ValueError('continuation target is not one of the locked E8 points')
                if record.get('status')!='COMPLETED' or not record.get('arrays_file'):
                    points.append({'name':run_id,'stage':'diagonal_continuation','gamma':gamma,'metadata':{'status':record['status']},'availability':'NOT_EVALUATED_MISSING_G'});continue
                arrays_path=path.parent/record['arrays_file']
                if record['arrays_file']!='fit_arrays.npz' or digest(arrays_path)!=record['arrays_sha256']:raise ValueError('continuation array archive changed')
                arrays=_npz(arrays_path);G=arrays.get('G')
                if G is None:availability='NOT_EVALUATED_MISSING_G'
                else:
                    if G.shape!=verified['F'].shape or not np.isfinite(G).all():raise ValueError('invalid continuation G')
                    stored=store.get(record['objects']['G'])
                    if array_hash(stored)!=array_hash(G):raise ValueError('continuation G object/NPZ identity differs')
                    availability='VERIFIED_G'
                points.append({'name':run_id,'stage':'diagonal_continuation','gamma':gamma,'metadata':record['solver'],
                               'arrays_file':str(arrays_path.relative_to(store.root)),'arrays_sha256':record['arrays_sha256'],
                               'availability':availability,**({'G':G} if G is not None else {})})
                additional.append({'record_path':str(path.relative_to(store.root)),'record_sha256':digest(path),'arrays_sha256':record['arrays_sha256']})
            verified['points']=points;verified['provenance']={**verified['provenance'],'additional_continuations':additional}
            folder=store.root/'usps_continuation_evaluation'/task['run_id']/identity(verified['provenance'])
            records=evaluate_verified(verified,store,folder)
            result.update(status='COMPLETED',records=records,provenance=verified['provenance'],
                qualification='Separate same-pair conditional rounding; original audit evaluation and historical winners are unchanged.')
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if folder is not None:atomic_json(folder/'evaluation_manifest.json',result)
    return result


def numerical_reference_input_identity(artifact_root):
    """Compare recorded current F/W content addresses without loading arrays.

    This is an input-reference identity view, not a new solver certificate or
    an assertion that historical missing arrays have been recovered.
    """
    root=Path(artifact_root);sources={}
    paths={'numerical_audit':'usps_audit/frozen_pair.json',
           'subset_search':'subset/USPS/representation.json'}
    for name,relative in paths.items():
        path=root/relative
        if not path.is_file():
            sources[name]={'path':relative,'available':False,'sha256':None,'objects':None}
            continue
        record=json.loads(path.read_text());objects={}
        for field in ['F','W']:
            ref=record.get('objects',{}).get(field)
            if not isinstance(ref,dict):raise ValueError('USPS input-reference metadata missing '+field)
            sha=ref.get('sha256');objpath=Path(str(ref.get('path','')))
            if (not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha)
                    or not ref.get('kind') or objpath.is_absolute() or '..' in objpath.parts
                    or not objpath.parts or objpath.parts[0]!='objects' or objpath.stem!=sha):
                raise ValueError('invalid USPS F/W content-addressed reference')
            objects[field]=dict(ref)
        sources[name]={'path':relative,'available':True,'sha256':digest(path),'objects':objects}
    available=all(source['available'] for source in sources.values())
    same=(sources['numerical_audit']['objects']==sources['subset_search']['objects']) if available else None
    return {'schema':'usps-numerical-reference-input-identity-v1','benchmark':'USPS',
        'subset_candidate_id':'USPS','sources':sources,
        'status':('MATCHING_RECORDED_CURRENT_F_W_OBJECTS' if same else 'DIFFERENT_RECORDED_CURRENT_F_W_OBJECTS') if available else 'UNAVAILABLE_CURRENT_INPUT_REFERENCE_COMPARISON',
        'same_current_F_W_content_addresses':same,'arrays_loaded_for_this_view':False,
        'historical_missing_F_G_identity_established':False,
        'certificate_transferred_to_locked_IRLS_G':False,
        'numerical_reference_exports':['usps_continuation_audit.csv','usps_continuation_evaluation.csv'],
        'scope':'Exact recorded current F/W object references only; no historical-array identity or closest-search claim. Each numerical certificate applies only to its own saved continuation G. Matching F/W does not certify a different historical-style IRLS G.'}


def export_results(artifact_root,output):
    """Read-only scalar export of separate continuation fits and roundings."""
    import os,tempfile
    from .scalar_views import collect_usps_metadata,derive_usps_views,write_usps_views
    root=Path(artifact_root);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    input_identity=numerical_reference_input_identity(root)
    metadata=collect_usps_metadata(root);derived=derive_usps_views(metadata)
    names=['usps_continuation_audit.csv','usps_continuation_evaluation.csv','usps_continuation_trials.csv.gz']
    selected={'tables':{name:rows for name,rows in derived['tables'].items() if name in names},
              'trial_tables':{name:rows for name,rows in derived['trial_tables'].items() if name in names}}
    with tempfile.TemporaryDirectory(prefix='.usps-continuations-',dir=out) as temporary:
        temporary=Path(temporary)
        write_usps_views(selected,temporary)
        atomic_json(temporary/'usps_numerical_reference_input_identity.json',input_identity)
        for name in names+['usps_numerical_reference_input_identity.json']:
            os.replace(temporary/name,out/name)
    return {'fit_records':len(metadata['continuation_fits']),
            'rounding_records':len(metadata['continuation_evaluations']),
            'rounding_trials':len(derived['trial_tables']['usps_continuation_trials.csv.gz']),
            'current_input_identity_status':input_identity['status']}
