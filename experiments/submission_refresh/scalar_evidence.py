"""Hash-locked baseline/graph scalars for independent no-data rebuilds.

Fitted scientific objects stay outside Git. Complete metrics, source identities,
method qualifications, and native endpoints are rebuilt from committed records;
missing or failed seeds never become a successful-seed subset.
"""
from __future__ import annotations
from collections import Counter
import gzip
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
OPTIONAL_LIGHT=['baseline_execution_coverage.csv','baseline_seed_coverage.csv','baseline_coverage_manifest.json','source_version_audit.json']


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
    return {'termination_counts':dict(Counter(d.get('termination_reason','unknown') for d in entries)),
        'status_counts':dict(Counter(d.get('status','unspecified') for d in entries)),
        'update_failures':sum(d.get('lda_update_failures',0) for d in entries),
        'runs_with_no_successful_LDA_update':sum(d.get('lda_update_successes')==0 for d in entries),
        'returned_state_inconsistent_runs':sum(d.get('returned_state_consistent') is False for d in entries),
        'inner_kmeans_repetitions_values':sorted({d['inner_kmeans_repetitions'] for d in entries if 'inner_kmeans_repetitions'in d}),
        'outer_n_init_values':sorted({d['outer_n_init'] for d in entries if 'outer_n_init'in d})}


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
        if 'config_id'in record:graphs.append(record)
    if not baseline:raise ValueError('empty current baseline evidence')
    _validate_records(baseline,'baseline');_validate_records(graphs,'graph')
    baseline_bytes,baseline_hash=_gzip_bytes(baseline);graph_bytes,graph_hash=_gzip_bytes(graphs)
    # The paper and selection rule are inputs, not mutable output placeholders.
    fixed=[root/'configs/v3/paper_reference.yaml',root/'configs/submission_refresh/selection.yaml']
    for path in fixed:
        if not path.is_file():raise ValueError('missing scalar release input '+str(path))
    yaml.safe_load(fixed[0].read_text());yaml.safe_load(fixed[1].read_text())
    light=[out/name for name in OPTIONAL_LIGHT if (out/name).is_file()]
    light+=sorted((out/'source_duplicate_maps').glob('*.json'))
    out.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.scalar-freeze-',dir=out.parent))
    try:
        destinations=[];files={}
        for name,payload,uncompressed in [('baseline_records.jsonl.gz',baseline_bytes,baseline_hash),('graph_records.jsonl.gz',graph_bytes,graph_hash)]:
            staged=stage/name;staged.write_bytes(payload);target=out/name
            files[str(target.relative_to(root))]={'sha256':digest(staged),'bytes':len(payload),'uncompressed_sha256':uncompressed}
            destinations.append((staged,target))
        for path in fixed+light:files[str(path.relative_to(root))]={'sha256':digest(path),'bytes':path.stat().st_size}
        supplementary=[str(path.relative_to(root)) for path in light]
        manifest={'schema':'submission-scalar-evidence-v1','checkout_root_relative':'../..','files':files,
            'baseline_file':str((out/'baseline_records.jsonl.gz').relative_to(root)),
            'graph_file':str((out/'graph_records.jsonl.gz').relative_to(root)),
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
    if manifest.get('schema')!='submission-scalar-evidence-v1':raise ValueError('unknown scalar evidence schema')
    root=(manifest_path.parent/manifest.get('checkout_root_relative','../..')).resolve()
    required=['baseline_file','graph_file','paper_file']
    if manifest.get('selection_file'):required.append('selection_file')
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
    paper=yaml.safe_load(paths[manifest['paper_file']].read_text());rows=[];native_rows=[];source_diagnostics=[]
    for record in baseline:
        base={key:record.get(key) for key in ['dataset','method','config_id','status','max_iter','parameters','initialization','native_best_status','diagnostic_summary','record_path','paper_deviations','preparation_assumptions','variant','qualification','seed_protocol','historical_lda_sc_identity','row_normalization']}
        # Frozen scalar records can omit these optional compatibility counts.
        # The selector expects integer counts, so normalize absent/null values
        # here without changing the shared selection or fitting implementation.
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
        row.update(solver_status=record.get('solver',{}).get('status'),certified=record.get('solver',{}).get('certified'),relative_gap=record.get('solver',{}).get('gap'));graphrows.append(row)
        if 'graph_diagnostics'in record:diagnostics.append({'dataset':record['dataset'],'config_id':record['config_id'],**record['graph_diagnostics']})
    gates={dataset:gate_dataset({record['arm']:record for record in graphs if record.get('dataset')==dataset and record.get('phase')=='G3' and record.get('gamma')==1000 and record.get('addition_fraction')==.15}) for dataset in DEVELOPMENT}
    passed=any(gate['passed'] for gate in gates.values());evaluated=all(gate['decision'] in ['PASSED','FAILED'] for gate in gates.values())
    gate={'version':1,'prior_campaign_gate':'0/4 unchanged','datasets':gates,'promotion_passed':passed,
        'decision':'PASSED' if passed else 'FAILED' if evaluated else 'INCOMPLETE_OR_NUMERICALLY_UNCERTIFIED',
        'G4_G5_status':'TRIGGERED_IMPLEMENTATION_REQUIRED' if passed else 'NOT_RUN_GATE_NOT_PASSED',
        'four_benchmark_ACC_gain_pp':None,'four_benchmark_NMI_gain_pp':None}
    out=Path(output).resolve()
    if any(path==out or out in path.parents for path in [manifest_path,*paths.values()]):raise ValueError('rebuild output would replace its own release inputs')
    if out.exists() and (not out.is_dir() or (any(out.iterdir()) and not (out/'evidence_validation.json').exists())):raise ValueError('refusing unknown nonempty evidence output')
    out.parent.mkdir(parents=True,exist_ok=True);tmp=Path(tempfile.mkdtemp(prefix='.evidence-rebuild-',dir=out.parent))
    try:
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
        atomic_json(tmp/'evidence_validation.json',{'ok':True,'baseline_records':len(baseline),'graph_records':len(graphs),'source_manifest_sha256':digest(manifest_path),'scope':'scalar evidence rebuild, not a fresh solver certificate','input_metric_units':'unit interval','output_units':'percent','source_native_diagnostics_excluded_from_primary_selection':True})
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
