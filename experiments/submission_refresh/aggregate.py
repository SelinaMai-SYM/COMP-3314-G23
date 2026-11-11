"""Generate submission evidence from authoritative records, without copying scores."""
from __future__ import annotations
import csv,json,time
from collections import Counter
from pathlib import Path
from experiments.subset_search.aggregate import write_csv
from .core import ROOT,ArtifactStore,ResourceLedger,atomic_json,digest
from .selection import summarize

def _gate_input_identity(store,dataset,records):
    """Refuse to assemble a gate from distinct fixed inputs or source versions."""
    if not records:return None
    versions={path.parent.name for path,record in records}
    if len(versions)!=1:raise ValueError('multiple graph input versions require separately frozen source tracks: '+dataset)
    version=next(iter(versions));path=store.root/'graph_inputs'/dataset/version/'representation.json'
    if not path.is_file():raise ValueError('graph input provenance is unavailable: '+dataset)
    meta=json.loads(path.read_text());fingerprint=meta.get('source',{}).get('implementation_hash')
    if not fingerprint or meta.get('dataset')!=dataset:raise ValueError('invalid fixed graph input/source provenance')
    for _,record in records:
        if record.get('source',{}).get('implementation_hash')!=fingerprint:raise ValueError('graph records mix scientific source versions')
        anchor=meta['objects']['F0' if record.get('anchor','F0')=='F0' else 'U']
        if record.get('status')=='COMPLETED' and record.get('objects',{}).get('anchor')!=anchor:
            raise ValueError('graph records do not share their declared exact fixed anchor')
    for key in ['X','y','F0','U','A','W0']:store.get(meta['objects'][key])
    return {'dataset':dataset,'input_version':version,'input_record':str(path.relative_to(store.root)),
        'input_record_sha256':digest(path),'scientific_source_fingerprint':fingerprint,
        'fixed_input_objects':{key:meta['objects'][key] for key in ['X','y','F0','U','A','W0']}}


def _register_scientific_tree(store,artifacts):
    """Register graph, continuation and confirmation recovery evidence.

    Confirmation JSON includes the frozen seed namespace and nested prediction
    object references; raw companion files retain their exact bytes and hashes.
    """
    extra=[]
    for name in ['graph_inputs','graph_solutions','graph_jobs','graph_records',
                 'usps_continuations','usps_continuation_evaluation','confirmation']:
        for path in sorted((store.root/name).rglob('*')):
            if not path.is_file() or path.name.startswith('.'):continue
            relative=str(path.relative_to(store.root))
            if path.suffix=='.json':
                artifacts.append({'record':relative,'object':store.put(json.loads(path.read_text()))})
            else:
                extra.append({'relative_path':relative,'sha256':digest(path),'bytes':path.stat().st_size})
    unique={}
    for record in artifacts:
        key=record['record']
        if key in unique and unique[key]!=record:raise ValueError('conflicting scientific metadata recovery path: '+key)
        unique[key]=record
    return list(unique.values()),extra





def _casebook_summary(record_path,casebook,task_result):
    """Preserve matched G1 task scalars alongside the casebook evidence."""
    sc=task_result.get('sc_solution',{}) or {};ssc=task_result.get('ssc_solution',{}) or {}
    return {'record':record_path,'dataset':task_result.get('task',{}).get('dataset'),
        **{key:value for key,value in casebook.items() if key!='objects'},
        'upstream_A_diagnostics':task_result.get('upstream_A_diagnostics'),
        'shrinkage_W0_diagnostics':task_result.get('shrinkage_W0_diagnostics'),
        'sc_summary':sc.get('summary'),'ssc_summary':ssc.get('summary'),
        'sc_solver_status':sc.get('solver',{}).get('status'),'ssc_solver_status':ssc.get('solver',{}).get('status'),
        'sc_certified':sc.get('solver',{}).get('certified'),'ssc_certified':ssc.get('solver',{}).get('certified')}


def aggregate(artifact_root,output):
    start=time.process_time();out=Path(output);out.mkdir(parents=True,exist_ok=True);store=ArtifactStore(artifact_root)
    baseline=[];coverage=[];artifacts=[];graphrows=[];graphdiagnostics=[];cases=[];case_summaries=[]
    for folder in sorted((store.root/'baseline').glob('*')):
        if folder.name.startswith('profile-'):continue
        for path in sorted(folder.glob('*.json')):
            r=json.loads(path.read_text());artifacts.append({'record':str(path.relative_to(store.root)),'object':store.put(r)})
            if 'method' in r and 'trials' in r and 'config_id' in r:
                complete=r.get('status')=='COMPLETED' and len(r['trials'])==50
                row={'dataset':r.get('dataset'),'method':r['method'],'config_id':r['config_id'],'status':r.get('status'),'n_trials':len(r['trials']),'max_iter':r.get('max_iter'),'native_best_status':r.get('native_best_status'),'source_record':str(path.relative_to(store.root))}
                if complete:row.update({k:v for k,v in summarize(r['trials'],objective=None).items() if k!='native_best'})
                if r.get('diagnostics'):
                    from .scalar_evidence import _diagnostic_summary,diagnostic_view
                    row.update(diagnostic_view(_diagnostic_summary(r['diagnostics'])))
                baseline.append(row)
    for path in sorted((store.root/'task_status').glob('*.json')):
        r=json.loads(path.read_text());task=r.get('task',{});coverage.append({'run_id':path.stem,'status':r['status'],'dataset':task.get('dataset',r.get('candidate_id')),'kind':task.get('kind'),'phase':task.get('phase'),'cpu_seconds':r.get('cpu_seconds'),'error':r.get('error')})
    from .graph_repair import gate_dataset,DEVELOPMENT
    gates={}
    for ds in DEVELOPMENT:
        primary={};scientific_records=[]
        for path in sorted((store.root/'graph_records'/ds).glob('*/*.json')):
            r=json.loads(path.read_text())
            if not r.get('config_id'):continue
            scientific_records.append((path,r))
            row={k:r.get(k) for k in ['phase','dataset','anchor','graph','arm','addition_fraction','gamma','config_id','status']}
            row.update(r.get('summary',{}));solver=r.get('solver',{});row.update(solver_status=solver.get('status'),certified=solver.get('certified'),relative_gap=solver.get('gap'),normalized_L21_movement=solver.get('normalized_L21_movement'));graphrows.append(row)
            if 'graph_diagnostics'in r:graphdiagnostics.append({'dataset':ds,'config_id':r['config_id'],'schema_version':2,**r['graph_diagnostics']})
            if r.get('phase')=='G3' and r.get('addition_fraction')==.15 and r.get('gamma')==1000:primary[r['arm']]=r
            artifacts.append({'record':str(path.relative_to(store.root)),'object':store.put(r)})
        provenance=_gate_input_identity(store,ds,scientific_records)
        gates[ds]={**gate_dataset(primary),'input_provenance':provenance}
    for path in sorted((store.root/'graph_jobs').glob('*/*/casebook.json')):
        r=json.loads(path.read_text())
        case_path=path.parent/'error_cases.csv'
        if not case_path.is_file():raise ValueError('full scientific casebook table is unavailable')
        task_path=store.root/'task_status'/(path.parents[1].name+'.json')
        local_task_path=path.parent/'status.json'
        # Prefer the status beside this exact source-version casebook. A later
        # controller attempt may have replaced the shared task-status record.
        task_record=json.loads(local_task_path.read_text()) if local_task_path.is_file() else json.loads(task_path.read_text()) if task_path.is_file() else {}
        case_summaries.append(_casebook_summary(str(path.relative_to(store.root)),r,task_record))
        case_hash=digest(case_path)
        with case_path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                cases.append({'dataset':task_record.get('task',{}).get('dataset'),
                    'casebook_record':str(path.relative_to(store.root)),
                    'case_table_sha256':case_hash,**row})
        artifacts.append({'record':str(path.relative_to(store.root)),'object':store.put(r)})
    anypass=any(g['passed'] for g in gates.values());all_eval=all(g['decision'] in ['PASSED','FAILED'] for g in gates.values())
    gate={'version':1,'prior_campaign_gate':'0/4 unchanged','datasets':gates,'promotion_passed':anypass,'decision':'PASSED' if anypass else 'FAILED' if all_eval else 'INCOMPLETE_OR_NUMERICALLY_UNCERTIFIED','scope':'Conditional rounding evidence on fixed development datasets; subset matching winners do not define inputs'}
    write_csv(out/'baseline_diagnostics.csv',baseline or [{'status':'NO_COMPLETED_BASELINE_RECORDS'}]);write_csv(out/'execution_coverage.csv',coverage)
    write_csv(out/'extension_results.csv',graphrows or [{'status':'NOT_RUN','reason':'Priority follows mandatory repairs and primary subset coverage'}]);write_csv(out/'graph_diagnostics.csv',graphdiagnostics or [{'schema_version':2,'status':'NO_NEW_GRAPH_RECORDS'}]);write_csv(out/'error_cases.csv',cases or [{'status':'NOT_RUN'}]);write_csv(out/'casebook_summary.csv',case_summaries or [{'status':'NOT_RUN'}]);atomic_json(out/'extension_gate.json',gate)
    from .inventory import build_inventory
    build_inventory(out)
    # Include solver arrays/metadata and a recoverable object for every small
    # scientific record. Full archives remain outside Git, linked by hash.
    for path in sorted((store.root/'usps_audit').rglob('*')):
        if path.is_file():
            relative=str(path.relative_to(store.root))
            artifacts.append({'record':relative,'sha256':digest(path),'bytes':path.stat().st_size,'availability':'byte-exact extra file in local scientific export; audit_jobs.py regeneration'})
            if path.suffix=='.json':artifacts.append({'record':'recovery_metadata/'+relative,'original_record_path':relative,'object':store.put(json.loads(path.read_text()))})
    if (store.root/'usps_audit/evaluation').exists():
        from .usps_evaluate import export_evaluation
        export_evaluation(artifact_root,out)
    if (store.root/'usps_continuations').exists():
        from .usps_continuation import export_results
        export_results(artifact_root,out)
    artifacts,raw_scientific_files=_register_scientific_tree(store,artifacts)
    atomic_json(out/'artifact_manifest.json',{'store':'independent-data/scientific-artifacts/refresh-20261110 (outside Git)','records':artifacts,'extra_files':raw_scientific_files,'definitions':{'objective_graph':'parent representation W for original SSC; graph_objects.fitted_W for interventions','IRLS_objects_fitted_W':'surrogate recomputed at returned G; not a claim to be the last linear-system weight matrix','dual_q':'only certified solver graph duals; IRLS weights are not dual variables'},'regenerate':'python -m experiments.submission_refresh run --config configs/submission_refresh/campaign.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume'})
    from .coverage import baseline_coverage
    baseline_coverage(artifact_root,out)
    from .graph_coverage import build_graph_coverage
    build_graph_coverage(artifact_root,out,root=ROOT)
    state=ResourceLedger(artifact_root).state();state['charged_cpu_core_hours']=sum(e['charged_cpu_seconds'] for e in state['entries'])/3600;state['aggregation_this_invocation_cpu_seconds']=time.process_time()-start;atomic_json(out/'resource_usage.json',state)
    return {'baseline_configurations':len(baseline),'graph_configurations':len(graphrows),'promotion':gate['decision']}
