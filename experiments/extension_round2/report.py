"""Authoritative round-two scalar tables, mechanism figures and recovery inventory."""
from __future__ import annotations
import argparse,csv,gzip,json,time,sys,io
from collections import Counter
import numpy as np
from .common import *
from .diagnostics import mechanism,certificate_audit


def write_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)

def planned():
    rows=[]
    for b in ORDER:
        for method in ['SC','historical','SSC_reference','old_E1_reference']:rows.append({'benchmark':b,'method':method,'variant':'default','rho':None,'phase':'reference'})
        for method in METHODS:
            for rho in [.05,.02,.1,.2]:rows.append({'benchmark':b,'method':method,'variant':'default','rho':rho,'phase':'primary' if rho==.05 else 'secondary'})
        for seed in [400,401,402]:rows.append({'benchmark':b,'method':'E4','variant':f'perm{seed}','rho':.05,'phase':'alignment_control'})
        if b in ['ORL','YaleB']:
            for method,name,values in [('E1_v2','eta',[.1,.5]),('E4','beta',[.25,4.]),('E5','alpha',[.25,4.]),('E6','eta_dir',[.25,.75])]:
                for value in values:rows.append({'benchmark':b,'method':method,'variant':f'{name}{value}','rho':.05,'phase':'sensitivity'})
    return rows

def point_key(row):return (row['benchmark'],row['method'],row['variant'],row['rho'])
def paired(target,control):
    a=np.array([[r['acc'],r['nmi']] for r in target['trials']]);b=np.array([[r['acc'],r['nmi']] for r in control['trials']]);difference=100*(a-b);rng=np.random.default_rng(424242);draws=difference[rng.integers(0,50,(10000,50))].mean(axis=1);lo,hi=np.quantile(draws,[.025,.975],axis=0)
    return {'ACC_delta_pp':float(difference[:,0].mean()),'NMI_delta_pp':float(difference[:,1].mean()),'ACC_lower_pp':float(lo[0]),'ACC_upper_pp':float(hi[0]),'NMI_lower_pp':float(lo[1]),'NMI_upper_pp':float(hi[1]),'bootstrap_seed':424242,'bootstrap_resamples':10000,'interval_scope':'Conditional rounding variability, not independent datasets or unseen-data inference'}

def qualified(row):return bool(row and row['certified'] and row['matched'] and row.get('graph_eligible',True) and row['trial_count']==50)

def receipt_task(store,value):
    argv=value.get('command',[])
    if '--task' in argv:
        task=load_record(Path(argv[argv.index('--task')+1]))
        if task:return task
    return load_record(store.root/'tasks'/(value['run_id'].rsplit('-',1)[0]+'.json'))

def build(config_path,artifact_root,output):
    spec,lock,store=locked(artifact_root,config_path);out=Path(output);out.mkdir(parents=True,exist_ok=True);endpoints={};evaluations={};results={};points=[];contrasts=[];diagnostics={};resources=[];audits={}
    task_outcomes=[load_record(p) for p in sorted((store.root/'task_outcomes').glob('*.json'))]
    native=[]
    for file in sorted((store.root/'command_jobs').glob('*/status.json')):
        value=load_record(file);task=receipt_task(store,value)
        if task and value['status']!='RUNNING':native.append({'task':task,'result':value})
    task_outcomes=native+[v for v in task_outcomes if not v['result'].get('run_id')]
    for path in sorted((store.root/'endpoints').glob('*.json')):
        endpoint=load_record(path)
        if endpoint['source_fingerprint']!=lock['source_fingerprint']:continue
        key=point_key(endpoint);endpoints[key]=endpoint
        if endpoint.get('result'):
            payload=store.get(endpoint['result']);payload={k:v for k,v in payload.items() if k not in ['checkpoint','history']};value=get_arrays(store,payload);audits[key]=certificate_audit(endpoint,value,lock['cohorts'][endpoint['benchmark']],store);results[key]={k:v for k,v in value.items() if k not in ['q','p']}
        ev=load_record(store.root/'evaluations'/path.name)
        if ev:
            if [t['seed'] for t in ev['trials']]!=list(range(50)):raise ValueError('incomplete or reordered trial set')
            evaluations[key]=ev
    for design in planned():
        key=point_key(design);endpoint=endpoints.get(key);result=results.get(key);evaluation=evaluations.get(key);entry=lock['cohorts'][design['benchmark']];outcome=endpoint['outcome'] if endpoint else {}
        row={**design,'candidate_id':entry['candidate_id'],'prep':entry['prep'],'initializer':entry['initialization'],'n':entry['n'],'K':entry['K'],'status':outcome.get('status','UNRUN_DEADLINE' if remaining_wall(store.root)<=0 else 'UNRUN'),'certified':outcome.get('certified'),'matched':outcome.get('matched'),'graph_eligible':outcome.get('graph_eligible',True),'trial_count':len(evaluation['trials']) if evaluation else 0,'point_id':endpoint['point_id'] if endpoint else None,'lambda':result.get('lam') if result else None,'actual_movement':result.get('movement') if result else None,'movement_error':result.get('movement_error') if result else None,'relative_gap':result.get('relative_gap') if result else None,'stable_gap':result.get('stable_gap') if result else None,'primal':result.get('primal') if result else None,'dual':result.get('dual') if result else None,'historical_identity':entry['historical_identity'],'historical_H_identity_matches':entry['historical_H_identity_matches']}
        row['historical_variant']=entry['variant'];row['historical_gamma_nominal']=entry['gamma_nominal'];row['historical_gamma_effective']=entry['gamma_effective'];row['parameters']=json.dumps(endpoint['parameters'] if endpoint else {})
        defaults={'E1_v2':{'eta':.25},'E5':{'alpha':1.},'E6':{'eta_dir':.5},'E4':{'beta':1.,'mix':.25,'a_budget':1.05}}
        resolved={**defaults.get(row['method'],{}),**(endpoint['parameters'] if endpoint else {})}
        if row['method']=='E4':
            graph=load_record(store.root/'graphs'/f"{row['benchmark']}--{row['variant']}.json")
            if graph and 'beta' in graph['diagnostics']:resolved['beta']=graph['diagnostics']['beta']
        row['resolved_method_parameters']=json.dumps(resolved)
        row.update({'stored_historical_'+k:float(entry['historical_selection'][k]) for k in ['acc_mean','acc_sd','nmi_mean','nmi_sd']});row['stored_historical_G_sha256']=entry['historical_selection']['G_sha256']
        attempts=[v['result'] for v in task_outcomes if v['task']['benchmark']==row['benchmark'] and v['task'].get('method',v['task']['kind'])==row['method'] and v['task'].get('variant','default')==row['variant'] and (row['rho'] in v['task'].get('targets',[]) if row['rho'] is not None else v['task']['kind'] in ['SC','historical','SSC_reference','old_E1_reference'])]
        row['native_attempt_statuses']=';'.join(v['status'] for v in attempts);row['native_failed_attempt_count']=sum(v['status']!='COMPLETED' for v in attempts);row['finite_output_retained_after_native_failure']=bool(result and row['native_failed_attempt_count'])
        if endpoint is None and attempts and row['native_failed_attempt_count']:row['status']='FAILED_NO_FINITE_OUTPUT'
        rounding=[v['result']['status'] for v in native if v['task']['kind']=='evaluate' and Path(v['task']['endpoint']).stem==row['point_id']]
        row['rounding_status']='COMPLETE_50' if evaluation else 'FAILED' if any(s!='COMPLETED' for s in rounding) else 'UNRUN';row['rounding_native_statuses']=';'.join(rounding)
        if row['method'] in ['historical','SSC_reference','old_E1_reference']:row['lambda']=2*entry['gamma_effective']
        if row['method']=='SC':row['lambda']=0.
        if evaluation:row.update({k:evaluation['summary'][k] for k in ['acc_mean','acc_sd','nmi_mean','nmi_sd']});row['native_best']=json.dumps(evaluation['summary'].get('native_best'))
        else:row.update({k:None for k in ['acc_mean','acc_sd','nmi_mean','nmi_sd']})
        if result:
            for name in ['q','p','S','Zf','G']:
                value=store.get(endpoint['result']).get(name)
                if isinstance(value,dict) and 'sha256'in value:row[name+'_sha256']=value['sha256']
            if row['method']=='historical':row['replay_G_object_matches_stored']=row.get('G_sha256')==row['stored_historical_G_sha256']
        if key in audits and row['method']!='SC':
            row['saved_certified']=row['certified'];row['certified']=audits[key]['qualified']
            if row['method'] in METHODS:row['matched']=bool(row['matched'] and audits[key]['matched']);row['certificate_audit']='PASSED' if audits[key]['qualified'] else 'NOT_QUALIFIED'
            if row['method']=='E4':row['graph_eligible']=bool(row['graph_eligible'] and audits[key]['graph_certificate']['eligible'])
            row['frozen_search_status']=row['status']
            if row['method'] in METHODS and row['saved_certified'] and not row['certified']:row['status']='UNCERTIFIED_SAVED_ARRAY_AUDIT'
        row['qualified_matched_pair_candidate']=qualified(row);points.append(row)
    lookup={point_key(r):r for r in points}
    for row in points:
        key=point_key(row);endpoint=endpoints.get(key);result=results.get(key);evaluation=evaluations.get(key);b=row['benchmark'];qkey=(b,'QSSC','default',row['rho']);qssc=results.get(qkey)
        if result:
            diagnostics[row['point_id']]=mechanism(endpoint,result,lock['cohorts'][b],store,qssc=qssc,sc_evaluation=evaluations.get((b,'SC','default',None)),evaluation=evaluation,qssc_evaluation=evaluations.get(qkey))
            diagnostics[row['point_id']]['independent_saved_array_certificate']=audits[key]
            diagnostics[row['point_id']]['QSSC_comparison_qualified_and_matched']=qualified(row) and qualified(lookup.get(qkey))
        if not evaluation:continue
        for comparison,controlkey in [('QSSC',qkey),('SSC_reference',(b,'SSC_reference','default',None)),('historical',(b,'historical','default',None)),('SC',(b,'SC','default',None))]:
            if controlkey==key or controlkey not in evaluations:continue
            control=lookup[controlkey];eligible=qualified(row) and qualified(control) if comparison=='QSSC' else row['trial_count']==50 and control['trial_count']==50 and bool(row['certified']) and (bool(control['certified']) if comparison=='SSC_reference' else True)
            contrast={**{k:row[k] for k in ['benchmark','method','variant','rho']},'comparison':comparison,'target_point_id':row['point_id'],'control_point_id':control['point_id'],'qualified':bool(eligible),**paired(evaluation,evaluations[controlkey])};contrasts.append(contrast)
    write_csv(out/'all_points.csv',points);write_csv(out/'primary_metrics.csv',[r for r in points if r['phase'] in ['primary','reference']]);write_csv(out/'secondary_metrics.csv',[r for r in points if r['phase']=='secondary']);write_csv(out/'control_metrics.csv',[r for r in points if r['phase'] in ['alignment_control','sensitivity']]);write_csv(out/'paired_differences.csv',contrasts);write_csv(out/'coverage.csv',[{k:r.get(k) for k in ['benchmark','candidate_id','method','variant','rho','phase','status','frozen_search_status','native_attempt_statuses','native_failed_attempt_count','finite_output_retained_after_native_failure','certified','matched','graph_eligible','rounding_status','rounding_native_statuses','trial_count','point_id']} for r in points]);atomic_json(out/'diagnostics.json',diagnostics)
    macros=[]
    for method in METHODS[1:]:
        values=[v for v in contrasts if v['method']==method and v['variant']=='default' and v['rho']==.05 and v['comparison']=='QSSC' and v['qualified']];seen={v['benchmark'] for v in values};complete=len(seen)==8
        macros.append({'method':method,'comparison':'fresh movement-matched QSSC','qualified_denominator':len(values),'eight_dataset_macro_ACC_pp':float(np.mean([v['ACC_delta_pp'] for v in values])) if complete else None,'eight_dataset_macro_NMI_pp':float(np.mean([v['NMI_delta_pp'] for v in values])) if complete else None,'available_case_ACC_pp':float(np.mean([v['ACC_delta_pp'] for v in values])) if values else None,'available_case_NMI_pp':float(np.mean([v['NMI_delta_pp'] for v in values])) if values else None,'missing_datasets':';'.join(b for b in ORDER if b not in seen),'ACC_wins':sum(v['ACC_delta_pp']>1e-12 for v in values),'ACC_ties':sum(abs(v['ACC_delta_pp'])<=1e-12 for v in values),'ACC_losses':sum(v['ACC_delta_pp']<-1e-12 for v in values),'NMI_wins':sum(v['NMI_delta_pp']>1e-12 for v in values),'NMI_ties':sum(abs(v['NMI_delta_pp'])<=1e-12 for v in values),'NMI_losses':sum(v['NMI_delta_pp']<-1e-12 for v in values)})
    write_csv(out/'macro_summary.csv',macros)
    alignment=[]
    for b in ORDER:
        real=evaluations.get((b,'E4','default',.05));controls=[evaluations.get((b,'E4',f'perm{s}',.05)) for s in [400,401,402]];rows=[lookup[(b,'E4',f'perm{s}',.05)] for s in [400,401,402]]
        def exchange(row):
            data=diagnostics.get(row['point_id'],{}).get('graph',{});value=data.get('exchange_mass');return .25*value if value is not None else None
        actual=lookup[(b,'E4','default',.05)]
        for seed,control,row in zip([400,401,402],controls,rows):
            if real and control:alignment.append({'benchmark':b,'comparison':f'real omitted band minus row permutation {seed}','qualified':qualified(actual) and qualified(row),'permutation_seeds':str(seed),'real_applied_exchange_fraction':exchange(actual),'control_applied_exchange_fraction':exchange(row),**paired(real,control)})
        if real and all(controls):
            mean={**controls[0],'trials':[{**t,'acc':float(np.mean([c['trials'][i]['acc'] for c in controls])),'nmi':float(np.mean([c['trials'][i]['nmi'] for c in controls]))} for i,t in enumerate(controls[0]['trials'])]}
            masses=[exchange(r) for r in rows]
            alignment.append({'benchmark':b,'comparison':'real omitted band minus mean of all three row-permuted controls','qualified':qualified(actual) and all(qualified(r) for r in rows),'permutation_seeds':'400;401;402','real_applied_exchange_fraction':exchange(actual),'control_applied_exchange_fraction':float(np.mean(masses)) if all(m is not None for m in masses) else None,**paired(real,mean)})
    write_csv(out/'E4_alignment_controls.csv',alignment)
    for b,entry in lock['cohorts'].items():resources.append({'category':'preparation_detail','benchmark':b,'CPU_seconds':entry['preparation_CPU_seconds'],'additive_to_native_total':False})
    for file in sorted((store.root/'fits').glob('*/definition.json')):
        definition=load_record(file);saved=load_record(file.with_name('result.json')) or load_record(file.with_name('recovered_result.json'));value=store.get(saved['object']) if saved else {}
        resources.append({'category':'refinement_detail','benchmark':definition['benchmark'],'method':definition['method'],'variant':definition['variant'],'fit_id':file.parent.name,'lambda':definition['lambda'],'attempt':definition['attempt'],'status':value.get('stopping_reason','INCOMPLETE_CHECKPOINT_ONLY'),'iterations':value.get('iterations'),'CPU_seconds':value.get('fit_total_CPU_seconds'),'additive_to_native_total':False})
    for file in sorted((store.root/'command_jobs').glob('*/status.json')):
        value=load_record(file);task=receipt_task(store,value)
        if value['status']=='RUNNING':continue
        resources.append({'category':value['phase'],'benchmark':task.get('benchmark') if task else None,'method':task.get('method',task.get('kind')) if task else None,'variant':task.get('variant','default') if task else None,'run_id':value['run_id'],'status':value['status'],'CPU_seconds':value.get('charged_CPU_seconds'),'wall_seconds':value.get('wall_seconds'),'peak_sampled_RSS_bytes':value.get('max_sampled_RSS_bytes'),'additive_to_native_total':True})
    write_csv(out/'resource_usage.csv',resources)
    with io.StringIO(newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['point_id','benchmark','method','variant','rho','seed','acc','nmi','inertia','iterations','warning']);writer.writeheader()
        for key,ev in evaluations.items():
            endpoint=endpoints[key]
            for t in ev['trials']:writer.writerow({**{k:endpoint[k] for k in ['point_id','benchmark','method','variant','rho']},**{k:t.get(k) for k in ['seed','acc','nmi','inertia','iterations','warning']}})
        (out/'trials.csv.gz').write_bytes(gzip.compress(f.getvalue().encode(),mtime=0))
    _markdown(out,points,macros,contrasts,diagnostics,lock)
    from .interpretation import write_evidence
    write_evidence(out,points,macros,diagnostics,alignment)
    from .figures import figures
    figures(out,points,contrasts,diagnostics)
    from experiments.submission_refresh.export_artifacts import references
    record={'protocol':spec,'cohort_lock':lock,'endpoints':list(endpoints.values()),'evaluations':list(evaluations.values()),'diagnostics':diagnostics}
    shared=[ROOT/'benchmarks/metrics/accuracy.py',ROOT/'benchmarks/metrics/nmi.py',ROOT/'benchmarks/metrics/__init__.py',ROOT/'experiments/submission_refresh/selection.py'];derivation={str(p.relative_to(ROOT)):digest(p) for p in [*(ROOT/'experiments/extension_round2').glob('*.py'),*shared]};record['derivation_source_files']=derivation;record['derivation_source_snapshot']=store.put({n:(ROOT/n).read_text() for n in derivation})
    refs={ref['sha256']:ref for ref in references(record)};logical=[]
    for name in ['cohort_lock.json','clock.json','resource_ledger.json','verification.json','primary_attempts_complete.json']:
        path=store.root/name
        if path.exists():
            value=load_record(path)
            if name=='resource_ledger.json':
                for run_id,reservation in value['active'].items():value['entries'].append({'run_id':run_id,'phase':reservation['phase'],'charged_cpu_seconds':reservation['seconds'],'status':'CONSERVATIVE_RECOVERY_RESERVATION'})
                value['active']={};value['recovery_accounting_is_conservative']=True
            logical.append({'record':name,'object':store.put(value)})
    for directory in ['inputs','auxiliary','graphs','graph_inputs','paths','endpoints','evaluations','tasks','task_outcomes','recovery_records']:
        for path in sorted((store.root/directory).glob('*.json')):
            value=load_record(path)
            if directory=='task_outcomes' and isinstance(value.get('result'),dict):
                value={**value,'result':{k:v for k,v in value['result'].items() if k in ['run_id','phase','status','charged_CPU_seconds','wall_seconds','max_sampled_RSS_bytes','exit_code','stop_reason','cpu_limit','wall_limit','terminal_accounting_complete']},'projection':'Scientific status and resource fields; local command text excluded'}
            logical.append({'record':str(path.relative_to(store.root)),'object':store.put(value)})
    for pattern in ['fits/*/result.json','fits/*/recovered_result.json','fits/*/definition.json','reference_checkpoints/*.json']:
        for file in sorted(store.root.glob(pattern)):logical.append({'record':str(file.relative_to(store.root)),'object':store.put(load_record(file))})
    # Restored receipts prevent a failed one-attempt reference from obtaining
    # another allowance. Native logs and machine-specific argv are excluded.
    for file in sorted((store.root/'command_jobs').glob('*/status.json')):
        value=load_record(file)
        if value['status']=='RUNNING':continue
        clean={k:v for k,v in value.items() if k in ['run_id','phase','status','charged_CPU_seconds','wall_seconds','max_sampled_RSS_bytes','exit_code','stop_reason','cpu_limit','wall_limit','terminal_accounting_complete']}
        logical.append({'record':str(file.relative_to(store.root)),'object':store.put(clean)})
    extra=[]
    for pointer in sorted(store.root.glob('**/continuation/CURRENT.json'))+sorted(store.root.glob('reference_checkpoints/*/CURRENT.json')):
        value=load_record(pointer);generation=pointer.parent/value['directory']
        for file in [pointer,generation/'state.json',generation/'arrays.npz']:
            extra.append({'relative_path':str(file.relative_to(store.root)),'sha256':digest(file),'bytes':file.stat().st_size})
    amendments=[load_record(p) for p in sorted((ROOT/'configs/extension_round2/amendments').glob('*.json'))]
    logical.append({'record':'amendments.json','object':store.put(amendments)})
    for ref in references(logical):refs[ref['sha256']]=ref
    pending=list(refs.values());visited=set()
    while pending:
        ref=pending.pop()
        if ref['sha256'] in visited:continue
        visited.add(ref['sha256'])
        if ref['kind']=='json':
            for child in references(store.get(ref)):
                refs[child['sha256']]=child;pending.append(child)
    atomic_json(out/'artifact_manifest.json',{'schema':'ssc-round2-artifacts-v1','records':logical,'numerical_objects':list(refs.values()),'extra_files':extra,'derivation_source_snapshot':record['derivation_source_snapshot'],'scope':'Exact eight-cohort states, scientific records, models and per-seed predictions; arrays stay outside Git','restriction':'Provider data rights remain independent from project MIT code'})
    files={str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in out.rglob('*') if p.is_file() and p.name!='release_manifest.json'}
    atomic_json(out/'release_manifest.json',{'schema':'ssc-round2-scalar-release-v1','files':files,'source_fingerprint':lock['source_fingerprint'],'protocol_sha256':lock['protocol_sha256'],'derivation_source_files':derivation,'trials_uncompressed_sha256':__import__('hashlib').sha256(gzip.decompress((out/'trials.csv.gz').read_bytes())).hexdigest(),'counts':{'planned_endpoints':len(points),'frozen_endpoints':len(endpoints),'complete_50_seed_endpoints':len(evaluations),'certified_and_matched':sum(qualified(p) for p in points),'primary_qualified_and_matched':sum(qualified(p) for p in points if p['phase']=='primary'),'primary_planned':40,'certified_unsquared_references':sum(bool(p['certified']) for p in points if p['method'] in ['SSC_reference','old_E1_reference']),'quadratic_fit_attempts':sum(r['category']=='refinement_detail' for r in resources)}})
    return points

def _markdown(out,points,macros,contrasts,diagnostics,lock):
    def number(v):return 'NA' if v is None else f'{v:.3f}'
    lines=['# Conditional SSC extension evaluation on locked report cohorts','','These cohorts were selected retrospectively against published targets. This is a conditional study, not unseen or unbiased test data. All methods use the same frozen H per cohort and feed optimized G directly to the locked rounding protocol. MSRA50 denotes the adapted native-16 EBSA source (1,799 samples, 12 classes); identity with the paper dataset is unverified.','','The primary mechanism comparison is against quadratic QSSC at the prescribed 5% movement target. A fidelity change, nonzero movement, a smaller objective, or a geometric guarantee alone does not establish improved clustering.','','| Cohort | SC ACC / NMI | Historical replay | Certified SSC reference | Original E1 reference | QSSC | E1_v2 | E4 | E5 | E6 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for b in ORDER:
        values=[]
        for method in ['SC','historical','SSC_reference','old_E1_reference',*METHODS]:
            row=next(r for r in points if r['benchmark']==b and r['method']==method and r['variant']=='default' and (r['rho']==.05 if method in METHODS else r['rho'] is None));text=number(row['acc_mean'])+' / '+number(row['nmi_mean'])
            if method in METHODS and not qualified(row):text+=' †'
            if method in ['SSC_reference','old_E1_reference'] and not row['certified']:text+=' U'
            values.append(text)
        lines.append('| '+b+' | '+' | '.join(values)+' |')
    lines += ['','Scores are percent means; complete same-configuration sample SDs are in primary_metrics.csv. ACC uses Hungarian matching and NMI uses geometric-mean entropy normalization. †: unqualified or unmatched intervention; U: uncertified unsquared reference. Missing entries remain NA. Native minimum-inertia assignments are diagnostic only and have no across-run SD.','','## Stored historical reference','', 'These frozen report measurements are not substituted for fresh outputs. Object identity checks are strict and include array storage representation; a mismatch alone does not quantify numerical value differences.','','| Cohort | Stored ACC ± sample SD | Stored NMI ± sample SD | Replay G object matches stored |','|---|---:|---:|---|']
    for b in ORDER:
        row=next(r for r in points if r['benchmark']==b and r['method']=='historical')
        lines.append(f"| {b} | {number(row['stored_historical_acc_mean'])} ± {number(row['stored_historical_acc_sd'])} | {number(row['stored_historical_nmi_mean'])} ± {number(row['stored_historical_nmi_sd'])} | {row.get('replay_G_object_matches_stored','NA')} |")
    lines += ['','## Primary changes relative to fresh QSSC','']
    for row in macros:
        complete=row['qualified_denominator']==8
        lines.append(f"- {row['method']}: {'eight-cohort macro' if complete else 'available-case mean'} ΔACC / ΔNMI = {number(row['available_case_ACC_pp'])} / {number(row['available_case_NMI_pp'])} percentage points; n={row['qualified_denominator']}/8. Missing: {row['missing_datasets'] or 'none'}. ACC wins/ties/losses {row['ACC_wins']}/{row['ACC_ties']}/{row['ACC_losses']}; NMI {row['NMI_wins']}/{row['NMI_ties']}/{row['NMI_losses']}.")
    lines += ['','The fixed .02/.10/.20 path, all three alignment controls and ORL/YaleB sensitivities remain separate. No best-performing path point replaces the .05 primary configuration. Intervals use 10,000 paired rounding-seed bootstrap draws (424242); fifty starts are not fifty independent datasets. They condition on the saved numerical embeddings and do not integrate solver approximation or historical-selection uncertainty.','','## Mechanism evidence and limits','', 'E1_v2 must move beyond the old fidelity and activate its relative stopping tubes before its mechanism is empirically tested. Coincident and uncertain edges are reported separately; the bound protects total dispersion rather than every edge or class.', '', 'E4 must change the graph under the recorded degree, mass and a-cost checks. Its real omitted band is compared with every row-permuted control; changed exchange mass is part of that comparison. An inactive certified graph is distinct from a failed QP fallback. Changed within/between-label masses are strictly post-fit diagnostics.', '', 'E5 must reduce triangle slack with nonuniform shape or permutation-invariant partition changes. An almost uniform scale/translation is not evidence of improved clustering.', '', 'E6 must confront a threatened direction: sufficient inactivity, actual LMI slack, PSD dual norm and the QSSC directional scale are reported. A singular-value floor is not a class-separation guarantee, and may preserve unhelpful directions.', '', 'Detailed per-point values and certificate-aware geometric diagnostics are in diagnostics.json; all failures and unmatched points are retained in coverage.csv.','','## Provenance and prior art','', 'Seven Y0 raw bases were reused from verified historical objects; YaleB raw U0 was freshly replayed and Y3 applied explicitly. All eight final H object identities match their locked report counterparts. Historical scalar measurements are preserved as reference metadata, not silently reused as fresh baselines. Pre-evaluation storage-layout amendments preserve their original registrations.', '', '[Quadratic convex clustering](https://www.ericchi.com/ec_papers/1304.0499v1.pdf), [TV-TV](https://jmota.eps.hw.ac.uk/documents/Vella21-RobustSingleImageSuperResolutionViaCNNsAndTVTVMinimization.pdf) / [PICCS](https://pmc.ncbi.nlm.nih.gov/articles/PMC3257752/) and [singular-value LMIs](https://shaharkov.github.io/ContSingVal.html) are established prior art. These are specific SSC extension candidates designed and tested in this project; E5 and E6 explicitly adapt tools from other fields. The scoped review cannot prove absolute novelty. No external image FFT or graphics optimizer was copied into these graph-vector solvers.','']
    (out/'summary.md').write_text('\n'.join(lines))
    recommendations=['# Report / presentation integration note','','The existing report and presentation are intentionally unchanged. Evaluate primary matched-QSSC effects and activation together before choosing main-text material. At most one or two candidates should receive main-text space; retain inactive, unqualified and null outcomes in the appendix or a compact limitations paragraph. No retrospective path winner should replace the registered primary point.','']
    complete=[r for r in macros if r['qualified_denominator']==8]
    supported=[r['method'] for r in complete if r['available_case_ACC_pp']>0 and r['available_case_NMI_pp']>=0]
    recommendations.append('Candidates with a positive complete primary ACC mean and nondecreasing NMI: '+(', '.join(supported) if supported else 'none established')+'. This descriptive screen is not a novelty or generalization claim; mechanism diagnostics and dataset regressions remain necessary.')
    recommendations+=['','Suggested nine-minute structure: motivation and common quadratic control (1.5 min); frozen cohorts and movement/certificate protocol (1.5 min); up to two evidence-supported mechanisms (3 min); failures, controls and tradeoffs (2 min); scope and reproducibility (1 min).','']
    (out/'integration_note.md').write_text('\n'.join(recommendations))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=DEFAULT_CONFIG);p.add_argument('--artifact-root',required=True);p.add_argument('--output',default=str(ROOT/'results/extension_round2'));args=p.parse_args()
    from experiments.extension_verification.resources import run_command
    folder=Path(args.artifact_root)/'command_jobs';ordinal=1
    while (folder/f'report-{ordinal}').exists():ordinal+=1
    command=[sys.executable,'-c','from experiments.extension_round2.report import build;import sys;build(*sys.argv[1:])',str(args.config),args.artifact_root,args.output]
    run_command(args.artifact_root,f'report-{ordinal}',command,cpu_limit=1800,wall_limit=min(3720,remaining_wall(args.artifact_root)),phase='aggregation',cwd=ROOT)
if __name__=='__main__':main()
