"""Pure USPS scalar views and deterministic writers for frozen evidence."""
from __future__ import annotations
import csv
import gzip
import io
import json
import math
from pathlib import Path
from .core import digest
from .selection import summarize

SCHEMA='usps-scalar-metadata-v1'


def collect_usps_metadata(artifact_root):
    root=Path(artifact_root)
    def entries(paths,eligible=lambda record:True):
        result=[]
        for path in sorted(paths):
            record=json.loads(path.read_text())
            if eligible(record):result.append({'record_path':str(path.relative_to(root)),'record_sha256':digest(path),'record':record})
        return result
    original=entries((root/'usps_audit/evaluation').glob('*/*/*.json'),lambda r:r.get('dataset')=='USPS' and bool(r.get('config_id')))
    continuation=entries((root/'usps_continuation_evaluation').glob('*/*/*.json'),lambda r:bool(r.get('config_id')))
    jobs=entries(list((root/'usps_audit/evaluation').glob('**/evaluation_manifest.json'))+list((root/'usps_continuation_evaluation').glob('**/evaluation_manifest.json')))
    for item in jobs:item['record']={key:value for key,value in item['record'].items() if key!='records'}
    return {'schema':SCHEMA,'original_audit':entries((root/'usps_audit').glob('*.json')),
        'original_evaluations':original,'continuation_fits':entries((root/'usps_continuations').glob('*/result.json')),
        'continuation_evaluations':continuation,'evaluation_jobs':jobs,
        'conditional_status':'RECORDS_AVAILABLE' if original or continuation else 'NOT_EVALUATED'}


def _validated_summary(record):
    trials=record.get('trials',[])
    if not isinstance(trials,list):raise ValueError('USPS trials must be a list')
    seeds=[int(row['seed']) for row in trials]
    if len(seeds)!=len(set(seeds)) or any(seed not in range(50) for seed in seeds):raise ValueError('duplicate/out-of-range USPS trial seed')
    for trial in trials:
        if any(not math.isfinite(float(trial[metric])) or not 0<=float(trial[metric])<=1 for metric in ['acc','nmi']):raise ValueError('invalid USPS metric units/value')
    if record.get('status')=='COMPLETED':
        if record.get('n_trials',50)!=50:raise ValueError('completed USPS record declares an incomplete seed count')
        return summarize(trials)
    return {}


def derive_usps_views(evidence):
    """Derive views from records only; no arrays or external paths are read."""
    if evidence.get('schema')!=SCHEMA:raise ValueError('unsupported USPS scalar metadata schema')
    fits=[];original_rows=[];continuation_rows=[];original_trials=[];continuation_trials=[];audit_rows=[];jobs=[]
    for key,rows,trials in [('original_evaluations',original_rows,original_trials),('continuation_evaluations',continuation_rows,continuation_trials)]:
        seen=set()
        for item in evidence.get(key,[]):
            record=item['record'];config=record.get('config_id')
            if not config or config in seen:raise ValueError('missing/duplicate USPS evaluation configuration')
            seen.add(config)
            if record.get('dataset')!='USPS' or record.get('n_samples')!=9298 or record.get('n_classes')!=10:raise ValueError('non-full-USPS evaluation cannot be published')
            summary=_validated_summary(record)
            row={name:record[name] for name in sorted(record) if name not in ['trials','summary','objects','audit_metadata','native_best']}
            if key=='original_evaluations':
                audit=record.get('audit_metadata',{});linear=audit.get('linear_checks',{})
                row.update(fit_cpu_seconds=audit.get('cpu_seconds'),fit_wall_seconds=audit.get('wall_seconds'),
                    cg_calls=linear.get('cg_calls'),cg_failures=linear.get('cg_failures'),cg_max_relative_residual=linear.get('cg_max_relative_residual'),
                    final_linear_relative_residual=linear.get('relative_linear_residual'))
            row.update({name:value for name,value in summary.items() if name!='native_best'})
            row.update(native_best=summary.get('native_best'),source_record=item['record_path'])
            rows.append(row)
            trials.extend({'config_id':config,'name':record['name'],**trial} for trial in record.get('trials',[]))
    seen=set()
    for item in evidence.get('continuation_fits',[]):
        record=item['record'];task=record.get('task',{});solver=record.get('solver',{});run_id=task.get('run_id')
        if not run_id or run_id in seen:raise ValueError('missing/duplicate USPS continuation fit identity')
        seen.add(run_id)
        fits.append({'run_id':run_id,'gamma_effective':task.get('gamma'),'status':record.get('status'),
            'solver_status':solver.get('status'),'certified':solver.get('certified'),'primal':solver.get('primal'),
            'dual':solver.get('dual'),'relative_gap':solver.get('gap'),'iterations':solver.get('iterations'),
            'max_iter':record.get('max_iter',task.get('max_iter')),'cpu_seconds':record.get('cpu_seconds'),
            'initialization':record.get('initialization'),'provenance':record.get('provenance'),
            'arrays_sha256':record.get('arrays_sha256'),'source_record':item['record_path'],
            'qualification':record.get('qualification'),'error':record.get('error')})
    for item in evidence.get('original_audit',[]):
        record=item['record']
        if 'records'in record and 'same_frozen_pair'in record:
            for stage in record['records']:
                audit_rows.append({'source_record':item['record_path'],**{key:stage[key] for key in sorted(stage) if key not in ['history','objects']}})
    for item in evidence.get('evaluation_jobs',[]):
        record=item['record'];task=record.get('task',{})
        jobs.append({'source_record':item['record_path'],'run_id':task.get('run_id'),'status':record.get('status'),
            'cpu_seconds':record.get('cpu_seconds'),'wall_seconds':record.get('wall_seconds'),'error':record.get('error'),
            'provenance':record.get('provenance'),'qualification':record.get('qualification')})
    return {'tables':{'usps_solver_evaluation.csv':original_rows or [{'status':'NOT_EVALUATED_NO_RECORDS'}],
        'usps_continuation_audit.csv':fits or [{'status':'NOT_RUN'}],
        'usps_continuation_evaluation.csv':continuation_rows or [{'status':'NOT_EVALUATED'}],
        'usps_original_solver_audit.csv':audit_rows or [{'status':'NOT_RUN'}],
        'usps_evaluation_job_status.csv':jobs or [{'status':'NOT_RUN'}]},
        'trial_tables':{'usps_solver_evaluation_trials.csv.gz':original_trials,'usps_continuation_trials.csv.gz':continuation_trials}}


def write_usps_views(derived,output):
    from experiments.subset_search.aggregate import write_csv
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name,rows in derived['tables'].items():write_csv(output/name,rows)
    for name,rows in derived['trial_tables'].items():
        buffer=io.StringIO();fields=['config_id','name','seed','acc','nmi','inertia','iterations','warning']
        writer=csv.DictWriter(buffer,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        (output/name).write_bytes(gzip.compress(buffer.getvalue().encode(),mtime=0))
