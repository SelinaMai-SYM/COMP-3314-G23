"""Hash-locked baseline/graph scalars for independent no-data rebuilds.

Fitted scientific objects stay outside Git. Complete metrics, source identities,
method qualifications, and native endpoints are rebuilt from committed records;
missing or failed seeds never become a successful-seed subset.
"""
from __future__ import annotations
from collections import Counter
import gzip
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import yaml
from .core import ROOT,atomic_json,digest
from .selection import summarize,distances,rank
from experiments.subset_search.aggregate import write_csv

PAPER_METHOD={'lda_existing':'lda_kmeans','lda_reference':'lda_kmeans','lda_adapted':'lda_kmeans','lda_adapted_sc':'lda_spectral','pca_p0_sc':'pca_spectral','pca_r_sc':'pca_spectral','raw_sc':'sc','pca_sc':'pca_spectral'}
BENCHMARK={'ORL_att92':'ORL','JAFFE':'JAFFE','YaleB_cropped2414':'YaleB','YaleB_dengcai32':'YaleB','USPS':'USPS','MSRA25_EBSA_16x16':'MSRA50'}
OPTIONAL_LIGHT=['baseline_execution_coverage.csv','baseline_seed_coverage.csv','baseline_coverage_manifest.json',
    'execution_coverage.csv','graph_execution_coverage.csv','graph_coverage_manifest.json','resource_usage.json','error_cases.csv','casebook_summary.csv',
    'source_version_audit.json','usps_numerical_reference_input_identity.json']
PUBLIC_SCHEMA='submission-scalar-evidence-public-v1'


def _read_csv_rows(path):
    """Read provenance-rich scalar rows without truncating large JSON fields."""
    previous=csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous,64*1024*1024))
        with Path(path).open(newline='') as stream:return list(csv.DictReader(stream))
    finally:csv.field_size_limit(previous)


def _safe_path(root,relative):
    if not isinstance(relative,str) or Path(relative).is_absolute():raise ValueError('evidence paths must be checkout-relative')
    path=(root/relative).resolve()
    if root not in path.parents:raise ValueError('evidence input escapes checkout')
    return path


def _gzip_bytes(rows):
    raw=(''.join(json.dumps(row,sort_keys=True,allow_nan=False)+'\n' for row in rows)).encode()
    return gzip.compress(raw,mtime=0),hashlib.sha256(raw).hexdigest()


def _validate_records(records,kind):
    identities=[]
    for row in records:
        if not isinstance(row,dict) or not row.get('config_id'):raise ValueError('missing evidence configuration identity')
        identities.append(row['config_id'])
        trials=row.get('trials',[])
        if not isinstance(trials,list):raise ValueError('evidence trials must be a list')
        seeds=[int(trial['seed']) for trial in trials]
        if len(seeds)!=len(set(seeds)):raise ValueError('duplicate trial primary key')
        if any(seed<0 or seed>=50 for seed in seeds):raise ValueError('evidence seed outside0..49')
        for trial in trials:
            if any(not math.isfinite(float(trial[m])) or not 0<=float(trial[m])<=1 for m in ['acc','nmi']):raise ValueError('invalid evidence metric units/value')
        if row.get('status')=='COMPLETED':
            summarize(trials,objective=None)
            if row.get('seed_failures'):raise ValueError('completed evidence contains failed seeds')
        if kind=='baseline' and row.get('dataset') not in BENCHMARK:raise ValueError('unknown baseline dataset identity')
    if len(identities)!=len(set(identities)):raise ValueError('duplicate '+kind+' configuration identity')


def _native_values(row):
    diagnostics=row.get('diagnostics',[]) or row.get('state_records',[])
    values=[]
    for entry in diagnostics:
        if not isinstance(entry,dict) or 'seed' not in entry:continue
        for field in ['source_error','error','inertia']:
            try:value=float(entry[field])
            except (KeyError,TypeError,ValueError):continue
            if math.isfinite(value) and value>=0:
                values.append({'seed':int(entry['seed']),'field':field,'value':value});break
    return values


def _diagnostic_summary(diagnostics):
    entries=[d for d in diagnostics if isinstance(d,dict)]
    return {'termination_counts':dict(Counter(d.get('termination_reason',d.get('status','unknown')) for d in entries)),
        'status_counts':dict(Counter(d.get('status','unspecified') for d in entries)),
        'update_failures':sum(d.get('lda_update_failures',0) for d in entries),
        'runs_with_no_successful_LDA_update':sum(d.get('lda_update_successes')==0 for d in entries),
        'returned_state_inconsistent_runs':sum(d.get('returned_state_consistent') is False for d in entries),
        'inner_kmeans_repetitions_values':sorted({d['inner_kmeans_repetitions'] for d in entries if 'inner_kmeans_repetitions'in d}),
        'outer_n_init_values':sorted({d['outer_n_init'] for d in entries if 'outer_n_init'in d})}


def diagnostic_view(summary):
    """Expose the same known diagnostic counts in live and frozen tables."""
    if not isinstance(summary,dict):return {}
    return {'diagnostic_summary':summary,'termination_counts':summary.get('termination_counts'),
        'update_failures_total':summary.get('update_failures'),
        'no_successful_lda_update_runs':summary.get('runs_with_no_successful_LDA_update'),
        'returned_state_inconsistent_runs':summary.get('returned_state_inconsistent_runs')}


def _publish_files(files,stage):
    """Replace only fully staged files, rolling back earlier replacements on error."""
    backups={};published=[]
    for index,(source,target) in enumerate(files):
        if target.exists() and not target.is_file():raise ValueError('release target is not a regular file')
        if target.exists():
            backup=stage/('backup-'+str(index));shutil.copy2(target,backup);backups[target]=backup
        else:backups[target]=None
    try:
        for source,target in files:
            target.parent.mkdir(parents=True,exist_ok=True);os.replace(source,target);published.append(target)
    except BaseException:
        for target in reversed(published):
            if backups[target] is None:target.unlink(missing_ok=True)
            else:os.replace(backups[target],target)
        raise


def _inventory_inputs(root):
    from .inventory import INITIAL,AUDIT
    initial=root/INITIAL;audit=root/AUDIT
    if not initial.exists() and not audit.exists():return []
    if not initial.is_file() or not audit.is_file():raise ValueError('incomplete committed source-inventory audit inputs')
    paths=[initial,audit]
    for parent in json.loads(audit.read_text())['parents']:
        path=(audit.parent/parent['duplicate_map']['path']).resolve()
        if root not in path.parents or not path.is_file():raise ValueError('source inventory duplicate map escapes checkout or is unavailable')
        paths.append(path)
    return paths


def _collect_current(store):
    from .ensc_campaign import collect_ensc_metadata
    from .scalar_views import collect_usps_metadata
    inputs=[]
    for path in sorted((store/'graph_inputs').glob('*/*/representation.json')):
        inputs.append({'record_path':str(path.relative_to(store)),'record_sha256':digest(path),'record':json.loads(path.read_text())})
    return {'schema':'current-scalar-extension-v1','ensc':collect_ensc_metadata(store),
        'usps':collect_usps_metadata(store),'graph_inputs':inputs}


def _current_counts(current):
    return {'ensc_jobs':len(current['ensc']['jobs']),'ensc_configurations':len(current['ensc']['records']),
        **{'usps_'+key:len(current['usps'].get(key,[])) for key in ['original_audit','original_evaluations','continuation_fits','continuation_evaluations','evaluation_jobs']}}


def _derive_current(current):
    from .ensc_campaign import derive_ensc_metadata
    from .scalar_views import derive_usps_views
    if current.get('schema')!='current-scalar-extension-v1':raise ValueError('unsupported current scalar extension schema')
    return derive_ensc_metadata(current['ensc']),derive_usps_views(current['usps'])


def _graph_gates(graphs,inputs=None):
    from .graph_repair import DEVELOPMENT,gate_dataset
    lookup={entry['record_path']:entry for entry in inputs or []}
    if len(lookup)!=len(inputs or []):raise ValueError('duplicate fixed graph input metadata')
    gates={}
    for dataset in DEVELOPMENT:
        rows=[record for record in graphs if record.get('dataset')==dataset]
        primary_rows=[record for record in rows if record.get('phase')=='G3' and record.get('gamma')==1000 and record.get('addition_fraction')==.15]
        primary={record['arm']:record for record in primary_rows}
        if len(primary)!=len(primary_rows):raise ValueError('duplicate frozen primary G3 arm')
        gate=gate_dataset(primary)
        if rows and inputs is not None:
            versions={Path(row['record_path']).parent.name for row in rows}
            if len(versions)!=1:raise ValueError('frozen graph scalars mix fixed input/source versions')
            version=next(iter(versions));path=f'graph_inputs/{dataset}/{version}/representation.json'
            if path not in lookup:raise ValueError('frozen graph scalar input provenance unavailable')
            item=lookup[path];meta=item['record'];source=meta.get('source',{}).get('implementation_hash')
            if not source or meta.get('dataset')!=dataset:raise ValueError('invalid frozen graph input/source provenance')
            for row in rows:
                if row.get('source',{}).get('implementation_hash')!=source:raise ValueError('frozen graph scalar source identity mismatch')
                anchor=meta['objects']['F0' if row.get('anchor','F0')=='F0' else 'U']
                if row.get('status')=='COMPLETED' and row.get('objects',{}).get('anchor')!=anchor:raise ValueError('frozen graph scalar actual anchor mismatch')
            gate['input_provenance']={'dataset':dataset,'input_version':version,'input_record':path,
                'input_record_sha256':item['record_sha256'],'scientific_source_fingerprint':source,
                'fixed_input_objects':{key:meta['objects'][key] for key in ['X','y','F0','U','A','W0']}}
        elif inputs is not None:gate['input_provenance']=None
        gates[dataset]=gate
    passed=any(value['passed'] for value in gates.values());evaluated=all(value['decision'] in ['PASSED','FAILED'] for value in gates.values())
    return {'version':1,'prior_campaign_gate':'0/4 unchanged','datasets':gates,'promotion_passed':passed,
        'decision':'PASSED' if passed else 'FAILED' if evaluated else 'INCOMPLETE_OR_NUMERICALLY_UNCERTIFIED',
        'G4_G5_status':'TRIGGERED_NOT_RUN' if passed else 'NOT_RUN_GATE_NOT_PASSED',
        'four_benchmark_ACC_gain_pp':None,'four_benchmark_NMI_gain_pp':None,
        'scope':'Conditional rounding evidence on fixed development datasets; subset matching winners do not define inputs'}


def _validate_graph_coverage(csv_path,manifest_path,root,locked=None):
    """Verify the full frozen design before copying a coverage snapshot."""
    from .graph_coverage import _validate_tasks,EXPECTED_PHASES,SCHEMA
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('schema')=='public-scientific-graph-coverage-v1':
        from .public_records import payload_hash
        if manifest.get('intended_tasks')!=362 or manifest.get('phase_counts')!=EXPECTED_PHASES or digest(csv_path)!=manifest.get('coverage_sha256'):
            raise ValueError('public graph coverage must retain the complete verified 362-point design')
        relative=manifest.get('design_path');path=_safe_path(root,relative)
        if locked is not None and relative not in locked:raise ValueError('public graph design is not hash-locked')
        if digest(path)!=manifest.get('design_sha256'):raise ValueError('public graph design hash mismatch')
        definitions=json.loads(path.read_text()).get('configurations',[])
        rows=_read_csv_rows(csv_path)
        if len(definitions)!=362 or len(rows)!=362 or dict(Counter(row.get('phase') for row in rows))!=EXPECTED_PHASES:
            raise ValueError('public graph coverage must retain all 362 tasks')
        from .graph_coverage import SELECTORS
        expected={row.get('configuration_id'):row for row in definitions};actual={row.get('configuration_id'):row for row in rows}
        if len(expected)!=362 or len(actual)!=362 or expected.keys()!=actual.keys():raise ValueError('public graph design identities differ')
        for key,row in expected.items():
            if payload_hash({name:row[name] for name in SELECTORS[row['phase']]})!=key:raise ValueError('public scientific graph configuration identity mismatch')
        return [path]
    if manifest.get('schema')!=SCHEMA or manifest.get('intended_tasks')!=362 or manifest.get('phase_counts')!=EXPECTED_PHASES:
        raise ValueError('graph coverage must describe the full 362-task design')
    if any(manifest.get(key) is not False for key in ['array_objects_read','fits_run','labels_evaluated','score_based_scope_selection']):
        raise ValueError('graph coverage has invalid metadata-only qualifications')
    if digest(csv_path)!=manifest.get('coverage_sha256'):raise ValueError('graph coverage CSV/manifest hash mismatch')
    queue_relative=manifest.get('queue_path');queue_path=_safe_path(root,queue_relative)
    if locked is not None and queue_relative not in locked:raise ValueError('graph coverage queue is not hash-locked')
    if digest(queue_path)!=manifest.get('queue_sha256'):raise ValueError('graph coverage frozen queue hash mismatch')
    tasks=_validate_tasks(json.loads(queue_path.read_text()))
    rows=_read_csv_rows(csv_path)
    if len(rows)!=362 or dict(Counter(row.get('phase') for row in rows))!=EXPECTED_PHASES:raise ValueError('graph coverage CSV must retain all 362 tasks')
    expected={task['run_id']:task for task in tasks};actual={row.get('run_id'):row for row in rows}
    if len(actual)!=len(rows) or actual.keys()!=expected.keys():raise ValueError('graph coverage run IDs do not match the frozen design')
    if any(row.get('configuration_id')!=expected[run_id]['configuration_id'] for run_id,row in actual.items()):raise ValueError('graph coverage configuration identity mismatch')
    membership=manifest.get('frozen_membership_inventory',{});relative=membership.get('path')
    if membership.get('sha256') is not None:
        if locked is not None and relative not in locked:raise ValueError('graph coverage membership inventory is not hash-locked')
        path=_safe_path(root,relative)
        if digest(path)!=membership['sha256']:raise ValueError('graph coverage frozen membership hash mismatch')
    return [queue_path]+([_safe_path(root,relative)] if membership.get('sha256') is not None else [])


def _validate_light(path):
    if path.name=='usps_numerical_reference_input_identity.json':
        record=json.loads(path.read_text())
        if record.get('schema')!='usps-numerical-reference-input-identity-v1' or any(record.get(key) is not False for key in ['arrays_loaded_for_this_view','historical_missing_F_G_identity_established','certificate_transferred_to_locked_IRLS_G']):
            raise ValueError('invalid USPS reference-input identity qualification')


def freeze(artifact_root,output):
    root=ROOT.resolve();store=Path(artifact_root).resolve();out=Path(output).resolve()
    out.relative_to(root)  # Reject invalid destinations before writing files.
    baseline=[];graphs=[]
    for folder in sorted((store/'baseline').glob('*')):
        if folder.name.startswith('profile-'):continue
        inp=json.loads((folder/'input.json').read_text()) if (folder/'input.json').exists() else {}
        for path in sorted(folder.glob('*.json')):
            record=json.loads(path.read_text())
            if not ('config_id'in record and 'trials'in record):continue
            keep=['dataset','method','config_id','status','trials','max_iter','parameters','initialization','native_best_status','seed_failures','implementation','source','cpu_charged_in','qualification','seed_protocol','historical_lda_sc_identity','row_normalization','paper_deviations','preparation_assumptions','variant']
            row={key:record[key] for key in keep if key in record}
            row.update(record_path=str(path.relative_to(store)),input_metadata=inp.get('metadata'),input_objects=inp.get('objects'))
            if record.get('diagnostics'):row['diagnostic_summary']=_diagnostic_summary(record['diagnostics'])
            if record.get('method','').startswith('lda_'):row['source_native_values']=_native_values(record)
            baseline.append(row)
    for path in sorted((store/'graph_records').glob('*/*/*.json')):
        record=json.loads(path.read_text())
        if 'config_id'in record:graphs.append({**record,'record_path':str(path.relative_to(store))})
    if not baseline:raise ValueError('empty current baseline evidence')
    _validate_records(baseline,'baseline');_validate_records(graphs,'graph')
    current=_collect_current(store);_derive_current(current);_graph_gates(graphs,current['graph_inputs'])
    current_bytes,current_hash=_gzip_bytes([current])
    baseline_bytes,baseline_hash=_gzip_bytes(baseline);graph_bytes,graph_hash=_gzip_bytes(graphs)
    # The paper and selection rule are inputs, not mutable output placeholders.
    fixed=[root/'configs/v3/paper_reference.yaml',root/'configs/submission_refresh/selection.yaml']
    inventory_inputs=_inventory_inputs(root)
    fixed+=inventory_inputs
    for path in fixed:
        if not path.is_file():raise ValueError('missing scalar release input '+str(path))
    yaml.safe_load(fixed[0].read_text());yaml.safe_load(fixed[1].read_text())
    if (root/'configs/submission_refresh/campaign.yaml').is_file():
        for name in ['baseline_execution_coverage.csv','baseline_seed_coverage.csv','baseline_coverage_manifest.json','execution_coverage.csv','graph_execution_coverage.csv','graph_coverage_manifest.json','resource_usage.json']:
            if not (out/name).is_file():raise ValueError('required campaign coverage input unavailable: '+name)
    graph_csv=out/'graph_execution_coverage.csv';graph_manifest=out/'graph_coverage_manifest.json'
    if graph_csv.exists()!=graph_manifest.exists():raise ValueError('graph coverage CSV/manifest pair is incomplete')
    if graph_csv.is_file():fixed+=_validate_graph_coverage(graph_csv,graph_manifest,root)
    light=[out/name for name in OPTIONAL_LIGHT if (out/name).is_file()]
    light+=sorted((out/'source_duplicate_maps').glob('*.json'))
    for path in light:_validate_light(path)
    out.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.scalar-freeze-',dir=out.parent))
    try:
        if inventory_inputs:
            from .inventory import build_inventory
            build_inventory(stage/'inventory-validation',root=root)
        destinations=[];files={}
        for name,payload,uncompressed in [('baseline_records.jsonl.gz',baseline_bytes,baseline_hash),('graph_records.jsonl.gz',graph_bytes,graph_hash),('current_scalar_records.jsonl.gz',current_bytes,current_hash)]:
            staged=stage/name;staged.write_bytes(payload);target=out/name
            files[str(target.relative_to(root))]={'sha256':digest(staged),'bytes':len(payload),'uncompressed_sha256':uncompressed}
            destinations.append((staged,target))
        for path in fixed+light:
            info={'sha256':digest(path),'bytes':path.stat().st_size}
            if path.suffix=='.gz':
                with gzip.open(path,'rb') as stream:info['uncompressed_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            files[str(path.relative_to(root))]=info
        supplementary=[str(path.relative_to(root)) for path in light]
        manifest={'schema':'submission-scalar-evidence-v1','checkout_root_relative':'../..','files':files,
            'baseline_file':str((out/'baseline_records.jsonl.gz').relative_to(root)),
            'graph_file':str((out/'graph_records.jsonl.gz').relative_to(root)),
            'current_scalar_file':str((out/'current_scalar_records.jsonl.gz').relative_to(root)),
            'current_scalar_counts':_current_counts(current),'inventory_inputs':[str(path.relative_to(root)) for path in inventory_inputs],
            'full_campaign_coverage_required':(root/'configs/submission_refresh/campaign.yaml').is_file(),
            'baseline_records':len(baseline),'graph_records':len(graphs),'paper_file':'configs/v3/paper_reference.yaml',
            'selection_file':'configs/submission_refresh/selection.yaml','supplementary_files':supplementary,
            'input_metric_units':'unit interval','display_units':'percent; differences in percentage points'}
        staged_manifest=stage/'evidence_manifest.json';atomic_json(staged_manifest,manifest)
        destinations.append((staged_manifest,root/'configs/submission_refresh/evidence_manifest.json'))
        _publish_files(destinations,stage)
        return manifest
    finally:shutil.rmtree(stage)


def _paper_fields(row,paper):
    row=dict(row);benchmark=BENCHMARK[row['dataset']];row['benchmark']=benchmark
    method=PAPER_METHOD.get(row['method'],row['method'].split('__')[0]);method=PAPER_METHOD.get(method,method)
    if method in paper['acc']:
        target={metric:paper[metric][method][benchmark]['mean'] for metric in ['acc','nmi']}
        row=distances(row,target)
        for metric in ['acc','nmi']:
            row['paper_'+metric]=target[metric];row['paper_'+metric+'_sd']=paper[metric][method][benchmark]['sd']
            row['delta_'+metric+'_sd_pp']=None if row.get(metric+'_sd') is None else row[metric+'_sd']-row['paper_'+metric+'_sd']
    return row


def _diagnostic_native(row,base,paper):
    values=row.get('source_native_values',[]);by_seed={entry['seed']:entry for entry in values}
    clean={k:v for k,v in base.items() if k not in ['acc_mean','nmi_mean','D_max','D_mean','d_acc','d_nmi','delta_acc_pp','delta_nmi_pp','delta_acc_sd_pp','delta_nmi_sd_pp']}
    result={**clean,'endpoint':'source_native_selection_diagnostic','pool':'diagnostic_only',
        'objective_comparability':'NOT_COMMON_OBJECTIVE','acc_sd':None,'nmi_sd':None,'n':1,
        'excluded_from_primary_selection':True}
    expected=set(range(50));trials={int(t['seed']):t for t in row['trials']}
    if len(values)!=50 or set(by_seed)!=expected or set(trials)!=expected or len({entry['field'] for entry in values})!=1:
        return {**result,'status':'UNAVAILABLE_INCOMPLETE_NATIVE_VALUES','finite_native_values':len(values)}
    winner=min(values,key=lambda entry:(entry['value'],entry['seed']));trial=trials[winner['seed']]
    result.update(status='DIAGNOSTIC_ONLY_NOT_COMMON_OBJECTIVE',selected_seed=winner['seed'],
        native_objective=winner['value'],native_objective_field=winner['field'],acc_mean=trial['acc']*100,nmi_mean=trial['nmi']*100,
        qualification='Source-native selection behavior retained as a diagnostic; raw SSE across learned subspaces is not a common primary objective.')
    return _paper_fields(result,paper)


def rebuild(manifest_path,output):
    manifest_path=Path(manifest_path).resolve();initial_manifest_hash=digest(manifest_path);manifest=json.loads(manifest_path.read_text())
    if manifest.get('schema') not in ['submission-scalar-evidence-v1',PUBLIC_SCHEMA]:raise ValueError('unknown scalar evidence schema')
    root=(manifest_path.parent/manifest.get('checkout_root_relative','../..')).resolve()
    required=['baseline_file','graph_file','paper_file']
    if manifest.get('selection_file'):required.append('selection_file')
    if manifest.get('current_scalar_file'):required.append('current_scalar_file')
    for role in required:
        if manifest.get(role) not in manifest.get('files',{}):raise ValueError('required evidence input is not hash-locked: '+role)
    paths={relative:_safe_path(root,relative) for relative in manifest['files']}
    for relative,info in manifest['files'].items():
        path=paths[relative]
        if not path.is_file() or digest(path)!=info['sha256']:raise ValueError('evidence hash mismatch')
        if info.get('bytes') is not None and path.stat().st_size!=info['bytes']:raise ValueError('evidence size mismatch')
        if 'uncompressed_sha256'in info:
            with gzip.open(path,'rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=info['uncompressed_sha256']:raise ValueError('uncompressed evidence hash mismatch')
    def read(role):
        with gzip.open(paths[manifest[role]],'rt') as stream:return [json.loads(line) for line in stream if line.strip()]
    baseline=read('baseline_file');graphs=read('graph_file')
    if not baseline:raise ValueError('empty current baseline evidence')
    if len(baseline)!=manifest['baseline_records'] or len(graphs)!=manifest['graph_records']:raise ValueError('scalar evidence record count mismatch')
    _validate_records(baseline,'baseline');_validate_records(graphs,'graph')
    current=None;ensc_derived=None;usps_derived=None
    if manifest.get('current_scalar_file'):
        records=read('current_scalar_file')
        if len(records)!=1:raise ValueError('current scalar extension requires one complete metadata record')
        current=records[0]
        if _current_counts(current)!=manifest.get('current_scalar_counts'):raise ValueError('current scalar extension count mismatch')
        ensc_derived,usps_derived=_derive_current(current)
    if manifest.get('schema')==PUBLIC_SCHEMA:
        _validate_public_projection(manifest,paths,baseline,graphs,current)
    for relative in manifest.get('inventory_inputs',[]):
        if relative not in paths:raise ValueError('source inventory audit input is not hash-locked')
    if manifest.get('inventory_inputs'):
        from .inventory import INITIAL,AUDIT
        if any(relative not in paths for relative in [INITIAL,AUDIT]):raise ValueError('required source inventory root records are not hash-locked')
        expected_inventory={str(path.relative_to(root)) for path in _inventory_inputs(root)}
        if expected_inventory!=set(manifest['inventory_inputs']) or not expected_inventory<=paths.keys():raise ValueError('incomplete hash-locked source inventory input mapping')
    if manifest.get('full_campaign_coverage_required'):
        parent=Path(manifest['baseline_file']).parent
        for name in ['baseline_execution_coverage.csv','baseline_seed_coverage.csv','baseline_coverage_manifest.json','execution_coverage.csv','graph_execution_coverage.csv','graph_coverage_manifest.json','resource_usage.json']:
            if str(parent/name) not in paths:raise ValueError('required campaign coverage input is not hash-locked')

    for relative in manifest.get('supplementary_files',[]):
        if relative not in paths:raise ValueError('supplementary file is not hash-locked')
        _validate_light(paths[relative])
    parent=Path(manifest['baseline_file']).parent
    graph_csv_relative=str(parent/'graph_execution_coverage.csv');graph_manifest_relative=str(parent/'graph_coverage_manifest.json')
    if (graph_csv_relative in paths)!=(graph_manifest_relative in paths):raise ValueError('hash-locked graph coverage pair is incomplete')
    if graph_csv_relative in paths:_validate_graph_coverage(paths[graph_csv_relative],paths[graph_manifest_relative],root,locked=paths)
    paper=yaml.safe_load(paths[manifest['paper_file']].read_text());rows=[];native_rows=[];source_diagnostics=[]
    for record in baseline:
        base={key:record.get(key) for key in ['dataset','method','config_id','status','max_iter','parameters','initialization','native_best_status','diagnostic_summary','record_path','paper_deviations','preparation_assumptions','variant','qualification','seed_protocol','historical_lda_sc_identity','row_normalization']}
        # Frozen scalar records can omit these optional compatibility counts.
        # The selector expects integer counts, so normalize absent/null values
        # here without changing the shared selection or fitting implementation.
        base.update(diagnostic_view(record.get('diagnostic_summary')))
        for count in ['paper_deviations','preparation_assumptions']:
            base[count]=int(record.get(count) or 0)
        base.update(source_implementation_hash=(record.get('source') or {}).get('implementation_hash'),source_commit=(record.get('source') or {}).get('source_commit'))
        base.update(n_trials=len(record['trials']),endpoint='mean_sample_sd_50',
            pool='adapted_resolution_16x16' if record['dataset']=='MSRA25_EBSA_16x16' else 'implementation_audit')
        if record.get('status')=='COMPLETED':
            base.update(summarize(record['trials'],objective=None));base=_paper_fields(base,paper)
            base['qualification']='; '.join(filter(None,[base.get('qualification'),'Complete 50 execution; source failures/degeneration remain qualified; adapted methods do not resolve historical LDA-SC.']))
            base['variability_scope']='50 separately fitted representations/trajectories and paired external indices' if record['method'].startswith('lda_') else '50 rounding/discretization seeds conditional on fixed representation'
            if record['method']=='llc':base['variability_scope']='50 Yu-Shi rotations conditional on fixed LLC eigenspace'
            if record['method'].startswith('lda_'):
                native_rows.append({**{k:v for k,v in base.items() if k not in ['acc_mean','nmi_mean','acc_sd','nmi_sd','D_max','D_mean','d_acc','d_nmi','delta_acc_pp','delta_nmi_pp','delta_acc_sd_pp','delta_nmi_sd_pp']},
                    'endpoint':'native_best_of_50','status':'UNAVAILABLE_CROSS_SUBSPACE_OBJECTIVE','n':None,'n_trials':50})
                source_diagnostics.append(_diagnostic_native(record,base,paper))
            else:
                objective='native_objective' if record['method']=='llc' else 'inertia'
                summary=summarize(record['trials'],objective=objective)
                if 'native_best'in summary:
                    native=_paper_fields({**base,**summary['native_best'],'endpoint':'native_best_of_50','n':1,'n_trials':1,'selected_seed':summary['native_best']['seed']},paper)
                    native['native_objective_field']=objective
                    native['variability_scope']='Single native-objective-selected assignment within one fixed representation; no across-run SD'
                    native_rows.append(native)
                else:native_rows.append({**{k:v for k,v in base.items() if k not in ['acc_mean','nmi_mean','D_max','D_mean','d_acc','d_nmi','delta_acc_pp','delta_nmi_pp','delta_acc_sd_pp','delta_nmi_sd_pp']},'endpoint':'native_best_of_50','status':'UNAVAILABLE_NATIVE_OBJECTIVE','acc_sd':None,'nmi_sd':None})
        rows.append(base)
    graphrows=[];diagnostics=[]
    from .graph_repair import DEVELOPMENT,gate_dataset
    for record in graphs:
        row={key:record.get(key) for key in ['dataset','phase','anchor','graph','arm','gamma','addition_fraction','config_id','status']}
        if record.get('status')=='COMPLETED':row.update(summarize(record['trials'],objective=None))
        row.update(solver_status=record.get('solver',{}).get('status'),certified=record.get('solver',{}).get('certified'),relative_gap=record.get('solver',{}).get('gap'),normalized_L21_movement=record.get('solver',{}).get('normalized_L21_movement'));graphrows.append(row)
        if 'graph_diagnostics'in record:diagnostics.append({'dataset':record['dataset'],'config_id':record['config_id'],**record['graph_diagnostics']})
    gate=_graph_gates(graphs,current['graph_inputs'] if current is not None else None)
    if ensc_derived is not None:
        from .ensc_campaign import apply_ensc_gate
        gate=apply_ensc_gate(gate,ensc_derived)
    if manifest.get('schema')==PUBLIC_SCHEMA:
        gate.pop('G4_G5_implementation_status',None)
    out=Path(output).resolve()
    if any(path==out or out in path.parents for path in [manifest_path,*paths.values()]):raise ValueError('rebuild output would replace its own release inputs')
    if out.exists() and (not out.is_dir() or (any(out.iterdir()) and not (out/'evidence_validation.json').exists())):raise ValueError('refusing unknown nonempty evidence output')
    out.parent.mkdir(parents=True,exist_ok=True);tmp=Path(tempfile.mkdtemp(prefix='.evidence-rebuild-',dir=out.parent))
    try:
        if ensc_derived is not None:
            from .ensc_campaign import write_ensc_views
            from .scalar_views import write_usps_views
            write_ensc_views(ensc_derived,tmp);write_usps_views(usps_derived,tmp)
        if manifest.get('inventory_inputs'):
            from .inventory import build_inventory
            build_inventory(tmp,root=root)
        write_csv(tmp/'baseline_diagnostics.csv',rows)
        write_csv(tmp/'baseline_endpoint_comparison.csv',rows+native_rows)
        write_csv(tmp/'baseline_source_native_diagnostics.csv',source_diagnostics or [{'status':'NO_LEARNED_SUBSPACE_NATIVE_DIAGNOSTICS'}])
        write_csv(tmp/'extension_results.csv',graphrows or [{'status':'NOT_RUN'}]);write_csv(tmp/'graph_diagnostics.csv',diagnostics or [{'status':'NOT_RUN'}]);atomic_json(tmp/'extension_gate.json',gate)
        for endpoint,endpoint_rows,name in [('mean_sample_sd_50',rows,'expanded_baseline_selection.csv'),('native_best_of_50',native_rows,'expanded_baseline_native_selection.csv')]:
            groups={}
            for row in endpoint_rows:
                if row.get('status')=='COMPLETED' and row.get('D_max') is not None:groups.setdefault((row['dataset'],row['method'],row['pool'],endpoint),[]).append(row)
            selected=[rank(group)[0] for group in groups.values()]
            write_csv(tmp/name,selected or [{'status':'NO_COMPLETE_ELIGIBLE_RECORDS','endpoint':endpoint}])
        for relative in manifest.get('supplementary_files',[]):
            if relative not in paths:raise ValueError('supplementary file is not hash-locked')
            destination=tmp/Path(relative).relative_to(paths[manifest['baseline_file']].parent.relative_to(root))
            destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(paths[relative],destination)
        # Detect concurrent input changes before publishing any derived file.
        if digest(manifest_path)!=initial_manifest_hash:raise ValueError('evidence manifest changed during rebuild')
        if any(digest(paths[relative])!=info['sha256'] for relative,info in manifest['files'].items()):raise ValueError('evidence inputs changed during rebuild')
        atomic_json(tmp/'evidence_validation.json',{'ok':True,'baseline_records':len(baseline),'graph_records':len(graphs),'source_manifest_sha256':digest(manifest_path),'scope':'scalar evidence rebuild, not a fresh solver certificate','input_metric_units':'unit interval','output_units':'percent','source_native_diagnostics_excluded_from_primary_selection':True,
            'current_scalar_counts':_current_counts(current) if current is not None else None,
            'external_data_read':False,'external_artifact_read':False,'git_history_read':False})
        if out.exists():
            previous=out.with_name(out.name+'.previous')
            if previous.exists():raise ValueError('previous evidence backup already exists')
            out.rename(previous)
            try:tmp.rename(out)
            except BaseException:previous.rename(out);raise
            shutil.rmtree(previous)
        else:tmp.rename(out)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return gate


def _public_packet_records(baseline,graphs,current):
    yield from baseline;yield from graphs
    if current is not None:
        for key in ['jobs','records']:
            for entry in current['ensc'].get(key,[]):yield entry['record']
        for entries in current['usps'].values():
            if isinstance(entries,list):
                for entry in entries:yield entry['record']
        for entry in current.get('graph_inputs',[]):yield entry['record']


def _validate_public_projection(manifest,paths,baseline,graphs,current):
    from .public_records import read_archive_receipt,payload_hash,SCHEMA
    projection_path=manifest.get('projection_file');receipt_path=manifest.get('archive_receipt_file')
    if projection_path not in paths or receipt_path not in paths:raise ValueError('public projection/archive proof is not hash-locked')
    receipt=read_archive_receipt(paths[receipt_path]);projection=json.loads(paths[projection_path].read_text())
    if projection.get('schema')!=SCHEMA or projection.get('archive_id')!=receipt['archive_id'] or projection.get('original_evidence_manifest_sha256')!=receipt['raw_release_inputs']['evidence_manifest']['sha256']:
        raise ValueError('public projection does not match its verified raw archive')
    records=projection.get('records',[])
    if Counter(row.get('public_record_sha256') for row in records)!=Counter(payload_hash(row) for row in _public_packet_records(baseline,graphs,current)):
        raise ValueError('public payload hashes do not match projection mapping')
    for row in records:
        if row.get('schema')!=SCHEMA or not isinstance(row.get('original_record_sha256'),str) or len(row['original_record_sha256'])!=64:
            raise ValueError('original record identities are unavailable in public projection')
    for row in _public_packet_records(baseline,graphs,current):
        if 'public_source_record_sha256'in row and payload_hash(row.get('source'))!=row['public_source_record_sha256']:
            raise ValueError('public source payload hash mismatch')
    if current is not None:
        seen={}
        for entry in current['ensc'].get('records',[]):
            record=entry['record'];key=record.get('config_id');source=record.get('original_source_record_sha256')
            if key in seen and seen[key]!=source:raise ValueError('public projection cannot merge distinct original scientific source IDs')
            seen[key]=source


def project_existing_release(manifest_path,public_root,*,archive_receipt):
    """Project a frozen release into a separate package after verified recovery.

    This explicit publication step never opens the scientific store, data root
    or Git history, and never changes raw release files. Default freeze remains
    the original raw mode. The returned package is independently rebuildable.
    """
    from .public_records import (read_archive_receipt,project_record,project_current,
        public_coverage_rows,final_resource_summary,payload_hash,_clean,SCHEMA)
    import copy
    source_manifest=Path(manifest_path).resolve();original_hash=digest(source_manifest)
    original=json.loads(source_manifest.read_text())
    if original.get('schema')!='submission-scalar-evidence-v1':raise ValueError('public projection requires an original raw scalar release')
    root=(source_manifest.parent/original.get('checkout_root_relative','../..')).resolve()
    destination=Path(public_root).resolve()
    if destination==root or destination in root.parents:raise ValueError('public projection cannot replace the raw checkout')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):raise ValueError('public package destination must be new or empty')
    receipt_hash=digest(archive_receipt);receipt=read_archive_receipt(archive_receipt)
    if receipt['raw_release_inputs']['evidence_manifest']['sha256']!=original_hash:raise ValueError('archive receipt does not cover this raw evidence manifest')
    if any(Path(relative).is_absolute() or '..' in Path(relative).parts or str(Path(relative))!=relative for relative in original['files']):
        raise ValueError('public release inputs require canonical checkout-relative paths')
    paths={relative:_safe_path(root,relative) for relative in original['files']}
    for relative,info in original['files'].items():
        path=paths[relative]
        if not path.is_file() or digest(path)!=info['sha256'] or path.stat().st_size!=info['bytes']:raise ValueError('raw evidence hash/size mismatch before public projection')
        if info.get('uncompressed_sha256'):
            with gzip.open(path,'rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=info['uncompressed_sha256']:raise ValueError('raw uncompressed evidence hash mismatch')
    def read(role):
        if not original.get(role):return []
        with gzip.open(paths[original[role]],'rt') as stream:return [json.loads(line) for line in stream if line.strip()]
    baseline=read('baseline_file');graphs=read('graph_file');current_records=read('current_scalar_file')
    _validate_records(baseline,'baseline');_validate_records(graphs,'graph')
    if not baseline or len(baseline)!=original['baseline_records'] or len(graphs)!=original['graph_records']:raise ValueError('invalid original scalar counts')
    if original.get('current_scalar_file') and len(current_records)!=1:raise ValueError('invalid current scalar record count')
    receipts=[]
    def project(rows,kind):
        values=[]
        for row in rows:
            value,proof=project_record(row,kind);values.append(value);receipts.append(proof)
        return values
    baseline=project(baseline,'baseline');graphs=project(graphs,'graph');current=None
    if current_records:
        current,proofs=project_current(current_records[0]);receipts+=proofs
    _validate_records(baseline,'baseline');_validate_records(graphs,'graph')
    if current is not None:_derive_current(current)
    parent=Path(original['baseline_file']).parent
    graph_csv=str(parent/'graph_execution_coverage.csv');graph_meta=str(parent/'graph_coverage_manifest.json')
    graph_design=None;raw_queue=None;graph_info=None
    if graph_csv in paths or graph_meta in paths:
        if graph_csv not in paths or graph_meta not in paths:raise ValueError('raw graph coverage pair is incomplete')
        _validate_graph_coverage(paths[graph_csv],paths[graph_meta],root,locked=paths)
        graph_info=json.loads(paths[graph_meta].read_text());raw_queue=graph_info['queue_path']
        from .graph_coverage import SELECTORS
        graph_design={'schema':'public-scientific-graph-design-v1','configurations':[
            {key:task[key] for key in [*SELECTORS[task['phase']],'configuration_id']}
            for task in json.loads(paths[raw_queue].read_text())['tasks']]}
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.public-scientific-package-',dir=destination.parent))
    try:
        files={};supplementary=[];source_files=[]
        packet_roles={original['baseline_file']:(baseline,'baseline_records'),original['graph_file']:(graphs,'graph_records')}
        if current is not None:packet_roles[original['current_scalar_file']]=([current],'current_scalar_records')
        for relative,path in paths.items():
            if relative==raw_queue or relative==graph_meta:continue
            target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True)
            if relative in packet_roles:
                payload,_=_gzip_bytes(packet_roles[relative][0]);target.write_bytes(payload)
            elif relative in original.get('inventory_inputs',[]):shutil.copy2(path,target)
            elif path.suffix=='.csv':
                rows=_read_csv_rows(path)
                rows=public_coverage_rows(rows)
                write_csv(target,rows or [{'status':'NO_RECORDED_SCIENTIFIC_ROWS'}])
            elif path.name=='resource_usage.json':atomic_json(target,final_resource_summary(json.loads(path.read_text())))
            elif path.name=='baseline_coverage_manifest.json':
                raw=json.loads(path.read_text());atomic_json(target,{'schema':'public-scientific-baseline-coverage-v1',
                    'original_manifest_sha256':digest(path),'expected_seeds':list(range(50)),
                    'scientific_status_summary':_clean({k:v for k,v in raw.items() if k in ['configuration_count','seed_rows','status_counts','configuration_status_counts']})})
            elif path.suffix=='.json':atomic_json(target,_clean(json.loads(path.read_text())))
            elif path.suffix in ['.yaml','.yml']:shutil.copy2(path,target)
            else:raise ValueError('unsupported public scalar input transport: '+relative)
            if relative in original.get('supplementary_files',[]):supplementary.append(relative)
            source_files.append({'original_path':relative,'original_sha256':digest(path),'public_path':relative,'public_sha256':digest(target)})
        if graph_design is not None:
            design_relative='configs/submission_refresh/graph_design.public.v1.json';design_path=stage/design_relative;atomic_json(design_path,graph_design)
            atomic_json(stage/graph_meta,{'schema':'public-scientific-graph-coverage-v1','intended_tasks':362,
                'phase_counts':graph_info['phase_counts'],'coverage_sha256':digest(stage/graph_csv),
                'design_path':design_relative,'design_sha256':digest(design_path),
                'original_coverage_manifest_sha256':digest(paths[graph_meta])})
            supplementary.append(graph_meta)
            source_files += [{'original_path':raw_queue,'original_sha256':digest(paths[raw_queue]),'public_path':design_relative,'public_sha256':digest(design_path)},
                {'original_path':graph_meta,'original_sha256':digest(paths[graph_meta]),'public_path':graph_meta,'public_sha256':digest(stage/graph_meta)}]
        proof_relative=str(parent/'public_archive_receipt.v1.json');atomic_json(stage/proof_relative,receipt)
        projection_relative=str(parent/'public_projection.v1.json')
        atomic_json(stage/projection_relative,{'schema':SCHEMA,'archive_id':receipt['archive_id'],
            'original_evidence_manifest_sha256':original_hash,'records':receipts,'files':source_files,
            'record_hash_semantics':'Original record and record_sha256 references identify raw archived evidence; public payloads have separate canonical public_record_sha256 hashes.'})
        supplementary += [proof_relative,projection_relative]
        for path in stage.rglob('*'):
            if not path.is_file():continue
            relative=str(path.relative_to(stage));info={'sha256':digest(path),'bytes':path.stat().st_size}
            if path.suffix=='.gz':
                with gzip.open(path,'rb') as stream:info['uncompressed_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            files[relative]=info
        public=copy.deepcopy(original);public.update(schema=PUBLIC_SCHEMA,files=files,supplementary_files=sorted(set(supplementary)),
            projection_file=projection_relative,archive_receipt_file=proof_relative,original_evidence_manifest_sha256=original_hash)
        manifest_relative=source_manifest.relative_to(root);target_manifest=stage/manifest_relative;atomic_json(target_manifest,public)
        _validate_public_projection(public,{key:stage/key for key in files},baseline,graphs,current)
        if graph_design is not None:_validate_graph_coverage(stage/graph_csv,stage/graph_meta,stage,locked=files)
        if digest(archive_receipt)!=receipt_hash or digest(source_manifest)!=original_hash or any(digest(path)!=original['files'][relative]['sha256'] for relative,path in paths.items()):
            raise ValueError('raw release changed during public projection')
        if destination.exists():destination.rmdir()
        stage.rename(destination)
        return {'manifest_path':str(destination/manifest_relative),'schema':PUBLIC_SCHEMA,'archive_id':receipt['archive_id'],
            'records':len(receipts),'raw_inputs_modified':False}
    finally:
        if stage.exists():shutil.rmtree(stage)
