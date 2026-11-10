"""Generate submission evidence from authoritative records, without copying scores."""
from __future__ import annotations
import csv,json,time
from collections import Counter
from pathlib import Path
from experiments.subset_search.aggregate import write_csv
from .core import ROOT,ArtifactStore,ResourceLedger,atomic_json,digest
from .selection import summarize

def aggregate(artifact_root,output):
    start=time.process_time();out=Path(output);out.mkdir(parents=True,exist_ok=True);store=ArtifactStore(artifact_root)
    baseline=[];coverage=[];artifacts=[];graphrows=[];graphdiagnostics=[];cases=[]
    for folder in sorted((store.root/'baseline').glob('*')):
        if folder.name.startswith('profile-'):continue
        for path in sorted(folder.glob('*.json')):
            r=json.loads(path.read_text());artifacts.append({'record':str(path.relative_to(store.root)),'object':store.put(r)})
            if 'method' in r and 'trials' in r and 'config_id' in r:
                complete=r.get('status')=='COMPLETED' and len(r['trials'])==50
                row={'dataset':r.get('dataset'),'method':r['method'],'config_id':r['config_id'],'status':r.get('status'),'n_trials':len(r['trials']),'max_iter':r.get('max_iter'),'native_best_status':r.get('native_best_status'),'source_record':str(path.relative_to(store.root))}
                if complete:row.update({k:v for k,v in summarize(r['trials'],objective=None).items() if k!='native_best'})
                if r.get('diagnostics'):
                    diagnostics=r['diagnostics'];row['termination_counts']=dict(Counter(d.get('termination_reason',d.get('status','unknown')) for d in diagnostics));row['update_failures_total']=sum(d.get('lda_update_failures',0) for d in diagnostics);row['no_successful_lda_update_runs']=sum(d.get('lda_update_successes',0)==0 for d in diagnostics)
                baseline.append(row)
    for path in sorted((store.root/'task_status').glob('*.json')):
        r=json.loads(path.read_text());task=r.get('task',{});coverage.append({'run_id':path.stem,'status':r['status'],'dataset':task.get('dataset',r.get('candidate_id')),'kind':task.get('kind'),'phase':task.get('phase'),'cpu_seconds':r.get('cpu_seconds'),'error':r.get('error')})
    from .graph_repair import gate_dataset,DEVELOPMENT
    gates={}
    for ds in DEVELOPMENT:
        primary={}
        for path in sorted((store.root/'graph_records'/ds).glob('*/*.json')):
            r=json.loads(path.read_text())
            if not r.get('config_id'):continue
            row={k:r.get(k) for k in ['phase','dataset','anchor','graph','arm','addition_fraction','gamma','config_id','status']}
            row.update(r.get('summary',{}));solver=r.get('solver',{});row.update(solver_status=solver.get('status'),certified=solver.get('certified'),relative_gap=solver.get('gap'),normalized_L21_movement=solver.get('normalized_L21_movement'));graphrows.append(row)
            if 'graph_diagnostics'in r:graphdiagnostics.append({'dataset':ds,'config_id':r['config_id'],'schema_version':2,**r['graph_diagnostics']})
            if r.get('phase')=='G3' and r.get('addition_fraction')==.15 and r.get('gamma')==1000:primary[r['arm']]=r
            artifacts.append({'record':str(path.relative_to(store.root)),'object':store.put(r)})
        gates[ds]=gate_dataset(primary)
    for path in sorted((store.root/'graph_jobs').glob('*/*/casebook.json')):
        r=json.loads(path.read_text());cases.append({'record':str(path.relative_to(store.root)),**{k:v for k,v in r.items() if k!='objects'}})
        artifacts.append({'record':str(path.relative_to(store.root)),'object':store.put(r)})
    anypass=any(g['passed'] for g in gates.values());all_eval=all(g['decision'] in ['PASSED','FAILED'] for g in gates.values())
    gate={'version':1,'prior_campaign_gate':'0/4 unchanged','datasets':gates,'promotion_passed':anypass,'decision':'PASSED' if anypass else 'FAILED' if all_eval else 'INCOMPLETE_OR_NUMERICALLY_UNCERTIFIED','G4_G5_status':'TRIGGERED_IMPLEMENTATION_REQUIRED' if anypass else 'NOT_RUN_GATE_NOT_PASSED','four_benchmark_ACC_gain_pp':None,'four_benchmark_NMI_gain_pp':None,'scope':'Conditional rounding evidence on fixed development datasets; subset matching winners do not define inputs'}
    write_csv(out/'baseline_diagnostics.csv',baseline or [{'status':'NO_COMPLETED_BASELINE_RECORDS'}]);write_csv(out/'execution_coverage.csv',coverage)
    write_csv(out/'extension_results.csv',graphrows or [{'status':'NOT_RUN','reason':'Priority follows mandatory repairs and primary subset coverage'}]);write_csv(out/'graph_diagnostics.csv',graphdiagnostics or [{'schema_version':2,'status':'NO_NEW_GRAPH_RECORDS'}]);write_csv(out/'error_cases.csv',cases or [{'status':'NOT_RUN'}]);atomic_json(out/'extension_gate.json',gate)
    inventory=list(csv.DictReader((ROOT/'results/subset_search/source_inventory.csv').open()));write_csv(out/'dataset_inventory.csv',inventory)
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
    atomic_json(out/'artifact_manifest.json',{'store':'independent-data/scientific-artifacts/refresh-20261110 (outside Git)','records':artifacts,'definitions':{'objective_graph':'parent representation W for original SSC; graph_objects.fitted_W for interventions','IRLS_objects_fitted_W':'surrogate recomputed at returned G; not a claim to be the last linear-system weight matrix','dual_q':'only certified solver graph duals; IRLS weights are not dual variables'},'regenerate':'python -m experiments.submission_refresh run --config configs/submission_refresh/campaign.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume'})
    from .coverage import baseline_coverage
    baseline_coverage(artifact_root,out)
    state=ResourceLedger(artifact_root).state();state['charged_cpu_core_hours']=sum(e['charged_cpu_seconds'] for e in state['entries'])/3600;state['aggregation_this_invocation_cpu_seconds']=time.process_time()-start;atomic_json(out/'resource_usage.json',state)
    return {'baseline_configurations':len(baseline),'graph_configurations':len(graphrows),'promotion':gate['decision']}
