"""Versioned scientific projections; original evidence remains unchanged.

These functions read metadata only. Public payload hashes are deliberately
separate from the identities of the original records they describe.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import re

SCHEMA='public-scientific-record-projection-v2'
ARCHIVE_SCHEMA='public-scientific-archive-receipt-v1'
_HASH=re.compile(r'[0-9a-f]{64}\Z')
_OPERATIONS={'traceback','command','commands','argv','cwd','hostname','host_name','pid','ppid',
    'log_path','log_file','filepath','library_path','validation_run_id','source_queue','queue_path','queue_sha256',
    'active','pending','reservations','active_controller_run_ids','controller_evidence',
    'controller_identity','controller_run_ids','ledger_statuses','scheduler_pending',
    'shared_unreserved_budget_seconds_before_active_reservations','working_tree_dirty',
    'checkpoint_directory','outputs_directory','data_root','artifact_root','repo_root',
    'updated_unix','timestamp','timestamp_unix','timestamp_utc','launch_time','source_archive',
    'worker_id','session_id','thread_id','controller_index'}
_SOURCE_FIELDS={'source_commit','source_files','implementation_hash','cache_identity',
    'project_source_fingerprint','scientific_source_fingerprint',
    'scientific_behavior_files','effective_construction_constants','cache_fingerprint_scope'}
_BASELINE={'dataset','method','config_id','status','trials','max_iter','parameters','initialization',
    'native_best_status','seed_failures','implementation','source','qualification','seed_protocol',
    'historical_lda_sc_identity','row_normalization','paper_deviations','preparation_assumptions',
    'variant','record_path','input_metadata','input_objects','diagnostic_summary','source_native_values',
    'error','failure_reason','cpu_seconds','wall_seconds'}
_GRAPH={'dataset','method','phase','anchor','graph','arm','gamma','addition_fraction','config_id',
    'status','trials','summary','source','objects','graph_objects','solver','graph_diagnostics',
    'distance_diagnostics','mass_matching','edit_objects','oracle_edits','control_generation',
    'pool_hash','SC_graph_arm_alias','problem_id','record_path','error','qualification',
    'resume_context','family','cpu_seconds','wall_seconds','cpu_seconds_this_call','rounding','eigensolver',
    'problem','checkpoint','surrogate_note'}
_INPUT={'dataset','K','objects','source','input_metadata','input_preparation','input_membership',
    'historical_F_identity','spectral_info','A_info','W0_info','angular_zero_rows'}
_TASK={'dataset','gamma','max_iter','initialization','seeds','seed','profile'}
_USPS=_BASELINE|_GRAPH|_INPUT|{'schema','name','n_trials','n_samples','n_classes','native_best','stage',
    'gamma_nominal','gamma_effective','solver_status','relative_gap','gap','certified','primal','dual',
    'edge_violation','node_violation','historical_300_protocol_complete','complete_historical_execution',
    'iterations','iterations_completed_linear_steps','normalized_L21_movement','normalized_Frobenius_movement',
    'n_unique_G_rows','G_hash','G_hash_definition','input_arrays_file','input_arrays_sha256','metadata_source',
    'pair_identity','provenance','audit_metadata','statistical_scope','initialization','arrays_file','arrays_sha256',
    'target','labels_loaded_for_fitting','same_frozen_pair','records','source_fingerprint','source_commit',
    'environment','limits','historical_identity','linear_checks','protocol','checkpoint','history',
    'fixed_point_residual','initial_zero_residual_floor','objects','solver','F_shape','W_shape','K',
    'feature_hash','label_hash','fingerprint','input_metadata','complete_points','missing_G_points','unique_G_hashes','rounding_signature'}


def payload_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read_archive_receipt(path):
    """Require an explicit verified archive/recovery proof, without opening it."""
    value=json.loads(Path(path).read_text())
    if value.get('schema')=='public-source-lineage-receipt-v2':
        if value.get('verified') is not True or value.get('scope')!='HISTORICAL_RECOVERY_LINEAGE_ONLY':raise ValueError('invalid lineage scope')
        if not _HASH.fullmatch(value.get('archive_sha256','')) or not _HASH.fullmatch(value.get('recovery_proof_sha256','')):raise ValueError('invalid original lineage hash')
        return copy.deepcopy(value)
    required={'schema','verified','archive_id','archive_sha256','bytes','recovered_objects',
        'recovered_extra_files','recovery_proof_sha256','raw_release_inputs'}
    if not isinstance(value,dict) or set(value)!=required or value['schema']!=ARCHIVE_SCHEMA or value['verified'] is not True:
        raise ValueError('a strict verified scientific archive receipt is required')
    if not isinstance(value['archive_id'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',value['archive_id']):
        raise ValueError('archive ID must be an opaque token without a path')
    for key in ['archive_sha256','recovery_proof_sha256']:
        if not isinstance(value[key],str) or not _HASH.fullmatch(value[key]):raise ValueError('invalid archive proof hash')
    for key,minimum in [('bytes',1),('recovered_objects',1),('recovered_extra_files',0)]:
        if type(value[key]) is not int or value[key]<minimum:raise ValueError('invalid archive proof count')
    inputs=value['raw_release_inputs']
    specification={'source_records':{'sha256','uncompressed_sha256'},'current_release_manifest':{'sha256'},
        'evidence_manifest':{'sha256'},'artifact_manifests':{'refresh_sha256','subset_sha256'},
        'seed_inventory_proof':{'sha256'},'original_namespace':{'sha256'}}
    if not isinstance(inputs,dict) or set(inputs)!=set(specification):raise ValueError('incomplete raw release archive proof')
    for role,keys in specification.items():
        if not isinstance(inputs[role],dict) or set(inputs[role])!=keys or any(not isinstance(v,str) or not _HASH.fullmatch(v) for v in inputs[role].values()):
            raise ValueError('invalid raw release input proof: '+role)
    return copy.deepcopy(value)


def _relative(value):
    for prefix in ['graph_inputs/','graph_records/','graph_jobs/','graph_solutions/','usps_audit/','usps_continuations/',
        'usps_continuation_evaluation/','baseline/','confirmation/','subset/']:
        marker='/'+prefix
        if marker in value:return prefix+value.rsplit(marker,1)[1]
    return None


def failure_reason(value,status=None):
    if value in ['TIME_LIMIT','CG_NONCONVERGENCE','SINGULAR_LINEAR_SYSTEM','MEMORY_LIMIT',
        'INPUT_OR_SOURCE_IDENTITY_MISMATCH','INCOMPLETE_SEED_SET','BUDGET_LIMIT','NOT_RUN','NUMERICAL_OR_EXECUTION_FAILURE']:
        return value
    text=str(value or '').lower();state=str(status or '').upper()
    if 'timeout' in text or 'time limit' in text or 'cpu allocation' in text or state=='TIMEOUT':return 'TIME_LIMIT'
    if 'cg' in text and any(token in text for token in ['fail','converg','residual']):return 'CG_NONCONVERGENCE'
    if 'singular' in text or 'positive definite' in text:return 'SINGULAR_LINEAR_SYSTEM'
    if 'memory' in text:return 'MEMORY_LIMIT'
    if 'hash' in text or 'identity' in text:return 'INPUT_OR_SOURCE_IDENTITY_MISMATCH'
    if 'seed' in text and ('incomplete' in text or 'missing' in text):return 'INCOMPLETE_SEED_SET'
    if 'budget' in text or 'BUDGET' in state:return 'BUDGET_LIMIT'
    if not text and state.startswith('NOT_RUN'):return 'NOT_RUN'
    return 'NUMERICAL_OR_EXECUTION_FAILURE'


def _clean(value,key=''):
    if isinstance(value,dict):
        result={}
        for name,item in value.items():
            if name in _OPERATIONS or name.startswith('_debug'):continue
            if isinstance(name,str) and Path(name).is_absolute():
                name=_relative(name) or ('external-record-'+hashlib.sha256(name.encode()).hexdigest())
            if name=='source' and isinstance(item,dict):result[name]=public_source_payload(item);continue
            if name=='task' and isinstance(item,dict):result[name]=_clean({k:v for k,v in item.items() if k in _TASK});continue
            if name=='error' and isinstance(item,str):
                result[name]=failure_reason(item,value.get('status'))
                result['original_error_sha256']=value.get('original_error_sha256') or hashlib.sha256(item.encode()).hexdigest()
                # Retain named numerical diagnostics without treating dates,
                # account names or digits from filesystem paths as measurements.
                numeric=re.findall(r'\b(?:info|column|iterations?|relative[_ ]residual|residual|rcond)\s*[=:]\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)',item,re.I)
                if numeric:result['reported_failure_values']=numeric
                continue
            result[name]=_clean(item,name)
        return result
    if isinstance(value,(list,tuple)):return [_clean(item,key) for item in value]
    if isinstance(value,str):
        if value.startswith(('http://','https://')):return value
        if Path(value).is_absolute():return _relative(value)
        return re.sub(r'/(?:Users|tmp|private/var)/[^\s\"\'<>]+','<external-path>',value)
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('public scientific metadata must be finite')
    return value


def public_metadata_payload(raw):
    """Project nested non-metric metadata without mutating its original record."""
    return _clean(raw)


def public_source_payload(raw):
    """Project actual code/environment identity, never relabelling its raw hash."""
    if not isinstance(raw,dict):raise ValueError('source record must be a dictionary')
    result={key:_clean(value,key) for key,value in raw.items() if key in _SOURCE_FIELDS and key!='source_files'}
    if 'source_files'in raw:
        result['source_files']={name:sha for name,sha in raw['source_files'].items()
            if isinstance(name,str) and not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name}
    environment=raw.get('environment')
    if isinstance(environment,dict):
        safe={'python','python_version','python_implementation','platform','packages','machine','processor','dtype','precision','threads_per_worker'}
        result['environment']=_clean({key:value for key,value in environment.items() if key in safe})
    libraries=raw.get('thread_libraries')
    if isinstance(libraries,list):
        fields={'user_api','internal_api','num_threads','prefix','version','threading_layer','architecture'}
        result['thread_libraries']=[_clean({key:value for key,value in row.items() if key in fields}) for row in libraries if isinstance(row,dict)]
    return result


def project_record(raw,kind):
    """Return a public scientific record and a separate canonical-hash receipt."""
    fields={'baseline':_BASELINE,'graph':_GRAPH,'input':_INPUT,'usps':_USPS}
    if kind not in fields or not isinstance(raw,dict):raise ValueError('unknown public scientific record kind')
    allowed=fields[kind];selected={key:value for key,value in raw.items() if key in allowed or isinstance(value,(int,float,bool))}
    public=_clean(selected)
    if kind=='usps' and isinstance(raw.get('task'),dict) and raw['task'].get('run_id'):
        public.setdefault('task',{})['fit_id']=raw['task']['run_id']
    if isinstance(raw.get('source'),dict) and 'source'in public:
        public['original_source_record_sha256']=payload_hash(raw['source'])
        public['public_source_record_sha256']=payload_hash(public['source'])
    receipt={'schema':SCHEMA,'kind':kind,'original_record_sha256':payload_hash(raw),'public_record_sha256':payload_hash(public)}
    return public,receipt


def project_entry(entry,kind):
    public,receipt=project_record(entry['record'],kind)
    result={key:_clean(value,key) for key,value in entry.items() if key!='record'}
    result.update(record=public,public_record_sha256=receipt['public_record_sha256'],
        original_payload_sha256=receipt['original_record_sha256'])
    return result,receipt


def project_current(raw):
    public={'schema':'current-scalar-studies-v2','usps':copy.deepcopy(raw['usps']),'graph_inputs':[]};receipts=[]
    for key,entries in raw['usps'].items():
        if not isinstance(entries,list):continue
        values=[]
        for entry in entries:
            item,receipt=project_entry(entry,'usps');values.append(item);receipts.append(receipt)
        public['usps'][key]=values
    for entry in raw.get('graph_inputs',[]):
        item,receipt=project_entry(entry,'input');public['graph_inputs'].append(item);receipts.append(receipt)
    public['public_projection_schema']=SCHEMA
    return public,receipts


def public_coverage_rows(rows):
    """Retain scientific outcomes, exact seeds/certificates and static settings."""
    remove={'run_id','source_queue','supersedes_run_id','block_status','declaration_index',
        'controller_status','controller_identity','controller_run_ids','controller_evidence','ledger_statuses',
        'active_controller_run_ids','scheduler_pending','shared_unreserved_budget_seconds_before_active_reservations',
        'saved_problem_alias_run_ids','expected_point_filename','source_record','evidence_record'}
    result=[]
    for row in rows:
        def clean(value):
            if isinstance(value,str) and value[:1] in ['{','[']:
                try:return clean(json.loads(value))
                except (ValueError,TypeError):pass
            if isinstance(value,dict):return {key:clean(item) for key,item in value.items() if key not in remove}
            if isinstance(value,list):return [clean(item) for item in value]
            return _clean(value)
        item=_clean(clean(row))
        if 'controller_status'in row:item['execution_status']=row['controller_status']
        if row.get('unrun_reason'):item['unrun_reason']=failure_reason(row['unrun_reason'],row.get('status',row.get('coverage_state')))
        for name in ['source_record','evidence_record']:
            if row.get(name):item[name]=clean(row[name])
        result.append(item)
    return result


def final_resource_summary(raw):
    ledger=raw.get('ledger',raw)
    if ledger.get('active'):raise ValueError('public resource summary requires a finalized ledger snapshot')
    entries=ledger.get('entries',[]);phases=defaultdict(float)
    for entry in entries:phases[str(entry.get('phase','unspecified'))]+=float(entry.get('charged_cpu_seconds',0))
    total=sum(float(entry.get('charged_cpu_seconds',0)) for entry in entries)
    return {'schema':'public-scientific-resource-summary-v1','finalized':True,'total_cpu_seconds':total,
        'total_cpu_core_hours':total/3600,'cpu_limit_seconds':ledger.get('limit_seconds'),
        'max_workers':ledger.get('max_workers',2),'rss_target_bytes':ledger.get('rss_target_bytes'),
        'phase_cpu_seconds':dict(sorted(phases.items()))}
