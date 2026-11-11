"""Authoritative scalar release and human-readable fixed-design comparisons."""
from __future__ import annotations
import csv,gzip,hashlib,json,os,shutil,tempfile
from pathlib import Path
import numpy as np
import yaml
from experiments.submission_refresh.core import ROOT,atomic_json,digest,identity,ResourceLedger
from .statistics import paired


def csv_write(path,rows,fields=None):
    rows=list(rows);fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fields,lineterminator='\n');writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def controls_for(method):
    return ['SC','SSC']+(['interpolation','uniform_scaling'] if method=='E1' else ['isotropic'] if method=='E2' else ['triplet_only','random_hinge_400','random_hinge_401','random_hinge_402'])


def point_status(record,evaluation):
    if evaluation is None:return 'PENDING'
    solver=record['solver']
    if solver.get('certified') is None:return 'COMPLETED_REFERENCE'
    if not solver['certified']:return 'COMPLETED_UNCERTIFIED'
    return 'COMPLETED_CERTIFIED' if solver['numerically_active'] else 'NUMERICALLY_INACTIVE'


def views(spec,lock,records,gates,diagnostics,run_state):
    metrics=[];trials=[];contrasts=[];status=[];by_id={r['point']['point_id']:r for r in records};primary={}
    display_order={name:i for i,name in enumerate(['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS'])};method_order={name:i for i,name in enumerate(['SC','SSC','E1','interpolation','uniform_scaling','radial_neutralization','E2','isotropic','E3','triplet_only','random_hinge_400','random_hinge_401','random_hinge_402'])}
    records=sorted(records,key=lambda packet:(display_order.get(packet['point']['benchmark'],99),packet['point']['panel']!='original',not packet['point'].get('primary',False),method_order.get(packet['point']['method'],99),packet['point']['gamma'],json.dumps(packet['point']['parameters'],sort_keys=True),packet['point']['point_id']))
    for packet in records:
        row=packet['point'];evaluation=packet.get('evaluation');solver=row['solver'];common={'benchmark':row['benchmark'],'candidate_id':row['candidate_id'],'role':row['role'],'historical_identity':'UNVERIFIED','adaptation_flags':row['qualification'],'method':row['method'],'panel':row['panel'],'point_id':row['point_id'],'primary':bool(row.get('primary')),'purposes':row.get('purposes',[]),'parameters':row['parameters'],'actual_gamma':row['gamma'],'output_normalization':row['output_normalization'],'n_samples':row['n'],'K':row['K'],'trial_count':len(evaluation['trials']) if evaluation else 0,'status':point_status(row,evaluation),'certified':solver.get('certified'),'relative_gap':solver.get('relative_gap'),'absolute_gap':solver.get('absolute_gap'),'normalized_L21_movement':solver.get('normalized_L21_movement'),'fit_CPU_seconds':row.get('cumulative_charged_fit_CPU_seconds'),'rounding_CPU_seconds':evaluation.get('CPU_seconds') if evaluation else None,'fit_peak_sampled_RSS_bytes':row.get('fit_peak_sampled_RSS_bytes'),'fit_attempt_count':len(row.get('numerical_attempts',[])),'iterations_completed':solver.get('iterations_total'),'G_sha256':row['objects']['G']['sha256'],'Q_sha256':row['objects']['Q']['sha256'],'source_fingerprint':row['source_fingerprint'],'protocol_sha256':row['protocol_sha256']}
        if row.get('primary'):primary[(row['benchmark'],row['panel'],row['method'])]=packet
        if evaluation is None:continue
        metrics.append({**common,'endpoint':'mean_sample_sd_50',**{k:evaluation['summary'][k] for k in ['acc_mean','acc_sd','nmi_mean','nmi_sd']},'selected_seed':None})
        native=evaluation['native_best'];metrics.append({**common,'endpoint':'native_best_of_50','acc_mean':100*native['acc'],'nmi_mean':100*native['nmi'],'acc_sd':None,'nmi_sd':None,'selected_seed':native['seed']})
        for trial in evaluation['trials']:trials.append({'point_id':row['point_id'],'benchmark':row['benchmark'],'method':row['method'],'panel':row['panel'],**trial})
    def contrast(target,base,comparison):
        if target is None or base is None or not target.get('evaluation') or not base.get('evaluation'):return
        a=target['point'];b=base['point'];qualified=all(r['solver'].get('certified') is not False for r in [a,b])
        for r in [a,b]:
            source=by_id.get(r.get('source_point'))
            if source and source['point']['solver'].get('certified') is False:qualified=False
        acc=paired(target['evaluation']['trials'],base['evaluation']['trials'],'acc');nmi=paired(target['evaluation']['trials'],base['evaluation']['trials'],'nmi')
        contrasts.append({'benchmark':a['benchmark'],'panel':a['panel'],'method':a['method'],'comparison':comparison,'target_point_id':a['point_id'],'control_point_id':b['point_id'],'target_gamma':a['gamma'],'control_gamma':b['gamma'],'qualified':qualified,'ACC_delta_pp':acc['delta_pp'],'ACC_lower_pp':acc['lower_pp'],'ACC_upper_pp':acc['upper_pp'],'NMI_delta_pp':nmi['delta_pp'],'NMI_lower_pp':nmi['lower_pp'],'NMI_upper_pp':nmi['upper_pp'],'bootstrap_resamples':10000,'bootstrap_seed':424242,'interval_scope':'Conditional paired rounding seeds; no new-dataset inference'})
    for benchmark in spec['inputs']['dataset_order']:
        entry=lock['datasets'][benchmark]
        for method,panels in [('E1',['original','angular']),('E2',['angular']),('E3',['angular'])]:
            for panel in panels:
                packet=primary.get((benchmark,panel,method));gate=gates.get(method)
                result=point_status(packet['point'],packet.get('evaluation')) if packet else 'GATE_FAILED' if gate is not None and not gate['promoted'] else 'NOT_RUN_BUDGET' if run_state.get('run_status')=='STOPPED_SHARED_BUDGET' else 'FAILED_OR_NOT_RUN' if run_state.get('run_status')=='FAILED_REQUIRES_INVESTIGATION' else 'PENDING'
                reason='Development mechanism gate did not permit benchmark optimization' if result=='GATE_FAILED' else run_state.get('stop_reason') if packet is None else packet['point']['solver'].get('stopping_reason')
                control_ids={}
                for name in controls_for(method):
                    control=primary.get((benchmark,panel,name)) or next((r for r in records if r['point']['benchmark']==benchmark and r['point']['panel']==panel and r['point']['method']==name and 'primary_control' in r['point'].get('purposes',[])),None)
                    control_ids[name]=control['point']['point_id'] if control else None
                status.append({'control_point_ids':control_ids,'development_gate_reference_point_id':gate.get('development_outcomes',{}).get(benchmark,{}).get('selected_reference') if gate else None,'benchmark':benchmark,'candidate_id':entry['candidate_id'],'role':entry['role'],'method':method,'panel':panel,'status':result,'reason':reason,'point_id':packet['point']['point_id'] if packet else None,'historical_identity':'UNVERIFIED','adaptation_flags':entry['qualification'],'force_reference_status':entry['gamma_references'][panel]['reference_status'],'actual_primary_gamma':entry['gamma_references'][panel]['primary_gamma']})
                if packet is None:continue
                controls=controls_for(method)
                for control in controls:
                    base=primary.get((benchmark,panel,control))
                    if base is None:
                        options=[r for r in records if r['point']['benchmark']==benchmark and r['point']['panel']==panel and r['point']['method']==control and 'primary_control' in r['point'].get('purposes',[])];base=options[0] if len(options)==1 else None
                    contrast(packet,base,method+'_minus_'+control)
    for match in diagnostics.get('movement_matches',[]):
        if match.get('control_point_id'):contrast(by_id.get(match['target_point_id']),by_id.get(match['control_point_id']),'declared_movement_match_'+match['status'])
    macros=[]
    for method in ['E1','E2','E3']:
        for panel in ['original','angular'] if method=='E1' else ['angular']:
          for comparator in (['SC','SSC','interpolation','uniform_scaling'] if method=='E1' else ['SC','SSC','isotropic'] if method=='E2' else ['SC','SSC','triplet_only','random_hinge_400','random_hinge_401','random_hinge_402']):
            rows=[r for r in contrasts if r['method']==method and r['panel']==panel and r['comparison']==method+'_minus_'+comparator and r['qualified']]
            complete=len({r['benchmark'] for r in rows})==8
            macros.append({'method':method,'panel':panel,'comparison':'matched '+comparator,'qualified_datasets':len(rows),'denominator':8,'status':'COMPLETE_QUALIFIED_EIGHT' if complete else 'UNAVAILABLE_INCOMPLETE_QUALIFIED_COVERAGE','ACC_delta_pp':float(np.mean([r['ACC_delta_pp'] for r in rows])) if complete else None,'NMI_delta_pp':float(np.mean([r['NMI_delta_pp'] for r in rows])) if complete else None,'partial_ACC_delta_pp':float(np.mean([r['ACC_delta_pp'] for r in rows])) if rows and not complete else None,'partial_NMI_delta_pp':float(np.mean([r['NMI_delta_pp'] for r in rows])) if rows and not complete else None})
    design=[]
    def planned(b,p,m,gamma,parameters,phase,condition,allowed=True):
        matches=[r for r in records if r['point']['benchmark']==b and r['point']['panel']==p and r['point']['method']==m and r['point']['gamma']==gamma and r['point']['parameters']==parameters]
        packet=matches[0] if len(matches)==1 else None
        status_value='PENDING' if allowed is None else 'GATE_FAILED' if not allowed and condition=='development_promotion' else 'NOT_TRIGGERED' if not allowed else point_status(packet['point'],packet.get('evaluation')) if packet else 'NOT_RUN_BUDGET' if run_state.get('run_status')=='STOPPED_SHARED_BUDGET' else 'PENDING'
        design.append({'benchmark':b,'candidate_id':lock['datasets'][b]['candidate_id'],'panel':p,'method':m,'phase':phase,'actual_gamma':gamma,'parameters':parameters,'condition':condition,'condition_satisfied':allowed,'configuration_status':point_status(packet['point'],packet.get('evaluation')) if packet else 'UNMEASURED','status':status_value,'point_id':packet['point']['point_id'] if packet else None})
    for b in spec['inputs']['dataset_order']:
        entry=lock['datasets'][b]
        for panel in ['original','angular']:
            gamma=entry['gamma_references'][panel]['primary_gamma'];ref=entry['gamma_references'][panel].get('gamma_ref')
            for m,param,g in [('SC',{},0.),('SSC',{},gamma),('E1',{'eta':.25},gamma),('interpolation',{'eta':.25},gamma),('uniform_scaling',{'eta':.25},0.)]:planned(b,panel,m,g,param,'E1_primary_and_controls','unconditional')
            a=primary.get((b,panel,'SSC'));z=primary.get((b,panel,'E1'));inactive=bool(ref is not None and a and z and a['point']['solver'].get('certified') and z['point']['solver'].get('certified') and not a['point']['solver']['numerically_active'] and not z['point']['solver']['numerically_active'])
            if ref is not None:
                for factor in [8,32]:
                    for m,param in [('SSC',{}),('E1',{'eta':.25})]:planned(b,panel,m,factor*ref,param,'E1_activity_probe','both_primary_outputs_certified_inactive',inactive)
            if b in ['ORL','YaleB']:
                for g in ([factor*ref for factor in [0,.5,1,2,8]] if ref is not None else [])+[1.]:
                    for m,param in [('SSC',{}),('E1',{'eta':.25})]:planned(b,panel,m,g,param,'development_path','unconditional')
                for m in ['E1','interpolation']:planned(b,panel,m,gamma,{'eta':.5},'development_eta_sensitivity','unconditional')
        gamma=entry['gamma_references']['angular']['primary_gamma']
        for m in ['E2','isotropic']:planned(b,'angular',m,gamma,{'angle_degrees':15.},'E2_formal_and_control','development_promotion',gates.get('E2',{}).get('promoted'))
        if b in ['ORL','YaleB']:
            for m in ['E2','isotropic']:planned(b,'angular',m,gamma,{'angle_degrees':30.},'E2_angle_sensitivity','development_promotion',gates.get('E2',{}).get('promoted'))
        tangent_ref=entry['gamma_references']['angular'].get('gamma_tan_ref')
        if tangent_ref is not None:
            for factor in [2,8]:
                promoted=gates.get('E2',{}).get('promoted');allowed=promoted
                if factor==8 and promoted:
                    first=[r for r in records if r['point']['benchmark']==b and r['point']['panel']=='angular' and r['point']['method']=='E2' and r['point']['gamma']==2*tangent_ref and r['point']['parameters']=={'angle_degrees':15.}]
                    allowed=bool(first and first[0]['point']['solver'].get('certified') and not first[0]['point']['solver']['numerically_active'])
                condition='development_promotion' if not promoted else 'first_projected_point_certified_inactive' if factor==8 else 'development_promotion'
                for method in ['SSC','E2','isotropic']:planned(b,'angular',method,factor*tangent_ref,{} if method=='SSC' else {'angle_degrees':15.},'E2_projected_force_secondary',condition,allowed)
        for m,g,param in [('E3',gamma,{'mu':2.}),('triplet_only',0.,{'mu':2.})]+[('random_hinge_'+str(seed),gamma,{'mu':2.,'random_seed':seed}) for seed in [400,401,402]]:planned(b,'angular',m,g,param,'E3_formal_and_controls','development_promotion',gates.get('E3',{}).get('promoted'))
        if b in ['ORL','YaleB']:planned(b,'angular','E3',gamma,{'mu':.5},'E3_mu_sensitivity','development_promotion',gates.get('E3',{}).get('promoted'))
    return {'metrics':metrics,'trials':trials,'contrasts':contrasts,'status':status,'macros':macros,'design_coverage':design}


def publish_views(out,derived,gates,diagnostics,run_state):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    csv_write(out/'design_coverage.csv',derived.get('design_coverage',[]));csv_write(out/'status.csv',derived['status']);csv_write(out/'metrics.csv',derived['metrics'],None if derived['metrics'] else ['benchmark','method','panel','status','acc_mean','acc_sd','nmi_mean','nmi_sd'])
    csv_write(out/'contrasts.csv',derived['contrasts'],None if derived['contrasts'] else ['benchmark','method','panel','comparison','qualified','ACC_delta_pp','NMI_delta_pp'])
    csv_write(out/'macro_summary.csv',derived['macros']);temporary=out/'trials.csv';csv_write(temporary,derived['trials'],None if derived['trials'] else ['point_id','benchmark','method','panel','seed','acc','nmi','inertia']);raw=temporary.read_bytes();(out/'trials.csv.gz').write_bytes(gzip.compress(raw,mtime=0));temporary.unlink()
    atomic_json(out/'diagnostics/gates.json',gates);atomic_json(out/'diagnostics/saved_points.json',diagnostics);atomic_json(out/'coverage.json',{'status_counts':dict(__import__('collections').Counter(r['status'] for r in derived['status'])),'extension_benchmark_pairs':24,'primary_panel_rows':32,'stage_completion':run_state.get('stages',{}),'run_status':run_state.get('run_status','PENDING'),'stop_reason':run_state.get('stop_reason')})


def report(config,artifact_root,output):
    from .inputs import load_locked
    spec,lock,store=load_locked(config,artifact_root);packets=[]
    for path in sorted((store.root/'points').glob('*.json')):
        point=json.loads(path.read_text())
        if point['source_fingerprint']!=lock['source_fingerprint']:continue
        evaluation=store.root/'evaluations'/f"{point['point_id']}.json"
        public={k:v for k,v in point.items() if k not in ['attempt_id','cpu_allowance','prior_charged_CPU_seconds']}
        attempts=[]
        if point.get('fit_id'):
            for result in sorted((store.root/'fits'/point['fit_id']/'attempts').glob('*/result.json')):
                fit=json.loads(result.read_text());receipt=store.root/'command_jobs'/result.parent.name/'status.json';cost=json.loads(receipt.read_text()) if receipt.exists() else {}
                attempts.append({'iteration_ceiling':fit.get('iteration_ceiling'),'iterations_completed':fit['solver']['iterations_total'],'certified':fit['solver']['certified'],'relative_gap':fit['solver']['relative_gap'],'accounted_CPU_seconds':cost.get('charged_CPU_seconds'),'wall_seconds':cost.get('wall_seconds'),'peak_sampled_RSS_bytes':cost.get('max_sampled_RSS_bytes'),'stopping_reason':fit['solver']['stopping_reason']})
        public['numerical_attempts']=attempts;public['fit_peak_sampled_RSS_bytes']=max((a['peak_sampled_RSS_bytes'] or 0 for a in attempts),default=0) if attempts else None
        packets.append({'point':public,'evaluation':json.loads(evaluation.read_text()) if evaluation.exists() else None,'original_point_payload_sha256':identity(point),'public_point_payload_sha256':identity(public)})
    gates={method:json.loads((store.root/'gates'/f'{method}.json').read_text()) for method in ['E2','E3'] if (store.root/'gates'/f'{method}.json').exists()};diagnostics=json.loads((store.root/'diagnostics.json').read_text()) if (store.root/'diagnostics.json').exists() else {};state=json.loads((store.root/'campaign_state.json').read_text()) if (store.root/'campaign_state.json').exists() else {}
    derived=views(spec,lock,packets,gates,diagnostics,state);out=Path(output).resolve();publish_views(out,derived,gates,diagnostics,state)
    evidence={'schema':'ssc-refinement-scalar-packet-v1','protocol':spec,'datasets_lock':lock,'records':packets,'gates':gates,'diagnostics':diagnostics,'confirmation':json.loads((ROOT/'results/extension_verification/context_confirmation.json').read_text()) if (ROOT/'results/extension_verification/context_confirmation.json').exists() else None,'run_state':{k:state.get(k) for k in ['run_status','stages','stop_reason']}}
    payload=(json.dumps(evidence,sort_keys=True,allow_nan=False)+'\n').encode();packet=out/'scalar_records.v1.json.gz';packet.write_bytes(gzip.compress(payload,mtime=0));manifest={'schema':'ssc-refinement-release-v1','checkout_root_relative':os.path.relpath(out,ROOT/'configs/extension_verification'),'packet_file':packet.name,'files':{packet.name:{'sha256':digest(packet),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'bytes':packet.stat().st_size}},'protocol_sha256':lock['protocol_sha256'],'source_fingerprint':lock['source_fingerprint'],'derivation_source_files':{str(Path(__file__).relative_to(ROOT)):digest(Path(__file__)), 'experiments/extension_verification/diagnostics.py':digest(ROOT/'experiments/extension_verification/diagnostics.py')},'counts':{'points':len(packets),'trials':len(derived['trials']),'primary_panel_rows':32},'scope':'Fixed reference inputs; no subset or performance-based parameter selection'}
    portable={**manifest,'checkout_root_relative':'.'};atomic_json(out/'release_manifest.json',portable)
    if out==(ROOT/'results/extension_verification').resolve():atomic_json(ROOT/'configs/extension_verification/release_manifest.json',manifest)
    # Only scientific objects in these packets are advertised. Command logs,
    # private instructions and operational queues are outside the closure.
    from experiments.submission_refresh.export_artifacts import references
    refs={ref['sha256']:ref for ref in references(evidence)}
    logical=[{'record':'refinement/scalar_records.json','object':store.put(evidence)}]
    history=store.root/'source_versions/retained_source_contexts.json'
    if history.exists():logical.extend(json.loads(history.read_text())['records'])
    for name,value in [('registration/datasets.lock.json',lock),('freeze.json',json.loads((store.root/'freeze.json').read_text())),('verification.json',json.loads((store.root/'verification.json').read_text())),('campaign_state.json',{'source_fingerprint':lock['source_fingerprint'],'stages':state.get('stages',{}),'gates':gates,'point_ids':[],'run_status':state.get('run_status','PENDING')})]:
        logical.append({'record':name,'object':store.put(value)})
    for method,gate in gates.items():
        logical.append({'record':f'gates/{method}.json','object':store.put(gate)})
    if diagnostics:
        logical.append({'record':'diagnostics.json','object':store.put(diagnostics)})
    if history.exists():
        logical.append({'record':str(history.relative_to(store.root)),'object':store.put(json.loads(history.read_text()))})
    for packet in packets:
        row=packet['point'];point_id=row['point_id'];logical.append({'record':'points/'+point_id+'.json','object':store.put(row)})
        if packet.get('evaluation'):logical.append({'record':'evaluations/'+point_id+'.json','object':store.put(packet['evaluation'])})
        if row.get('fit_id'):
            folder=store.root/'fits'/row['fit_id']/'attempts'
            for result in sorted(folder.glob('*/result.json')):
                metadata=json.loads(result.read_text());logical.append({'record':str(result.relative_to(store.root)),'object':store.put(metadata)})
                run_id=result.parent.name;receipt=store.root/'command_jobs'/run_id/'status.json';task=store.root/'fit_tasks'/f'{run_id}.json'
                if task.exists():logical.append({'record':str(task.relative_to(store.root)),'object':store.put(json.loads(task.read_text()))})
                if receipt.exists():
                    raw=json.loads(receipt.read_text());typed={k:raw.get(k) for k in ['run_id','status','charged_CPU_seconds','stop_reason','CPU_seconds','max_sampled_RSS_bytes','wall_seconds','terminal_accounting_complete']}
                    logical.append({'record':str(receipt.relative_to(store.root)),'object':store.put(typed)})
    ledger=ResourceLedger(store.root).state();prior=sum(r['charged_cpu_seconds'] for r in ledger['entries'])
    # Recovered states keep an upper bound on the same allowance. The final
    # packaging reserve is counted conservatively, rather than granting a new
    # campaign budget when the destination directory changes.
    upper=min(ledger['limit_seconds'],prior+sum(r['seconds'] for r in ledger['active'].values())+ledger['reserve_seconds'])
    preserved={k:ledger[k] for k in ['version','limit_seconds','reserve_seconds','max_workers','rss_target_bytes']};preserved.update(active={},entries=[{'run_id':'prior-scientific-work','phase':'preserved_scientific_accounting','charged_cpu_seconds':max(0.,upper-600),'status':'CONSERVATIVE_PRESERVED_ACCOUNTING'},{'run_id':'controller-bookkeeping-0001','phase':'aggregation','charged_cpu_seconds':600.,'status':'CONSERVATIVE_PRESERVED_ACCOUNTING'}],recovery_accounting_is_conservative=True)
    logical.append({'record':'resource_ledger.json','object':store.put(preserved)})
    counter=store.root/'controller_accounting.json'
    if counter.exists():logical.append({'record':'controller_accounting.json','object':store.put(json.loads(counter.read_text()))})
    unique={row['record']:row for row in logical}
    atomic_json(out/'artifact_manifest.json',{'schema':'ssc-refinement-artifacts-v2','records':list(unique.values()),'numerical_objects':list(refs.values()),'restriction':'Provider-restricted arrays remain outside Git; exact public regeneration is documented','scope':'Numerical states, typed continuation metadata and clean source; execution commands, logs and original mixed source-body packages are excluded'})
    if out==(ROOT/'results/extension_verification').resolve():_markdown(derived,gates,state,diagnostics)
    return derived


def rebuild(manifest_path,output):
    path=Path(manifest_path).resolve();manifest=json.loads(path.read_text());root=(path.parent/manifest['checkout_root_relative']).resolve()
    if manifest['schema']!='ssc-refinement-release-v1':raise ValueError('unknown refinement release schema')
    if not manifest.get('files'):raise ValueError('empty refinement release')
    for name,info in manifest['files'].items():
        target=(root/name).resolve()
        if root not in target.parents or digest(target)!=info['sha256'] or target.stat().st_size!=info['bytes']:raise ValueError('refinement input hash/size mismatch')
        raw=gzip.decompress(target.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=info['uncompressed_sha256']:raise ValueError('refinement decompressed hash mismatch')
    packet=json.loads(gzip.decompress((root/manifest['packet_file']).read_bytes()))
    if packet['datasets_lock']['protocol_sha256']!=manifest['protocol_sha256']:raise ValueError('refinement protocol mismatch')
    keys=[r['point']['point_id'] for r in packet['records']]
    if len(keys)!=len(set(keys)):raise ValueError('duplicate refinement point identity')
    if manifest.get('counts',{}).get('points',len(keys))!=len(keys):raise ValueError('refinement point count mismatch')
    if not keys and packet['run_state'].get('run_status')=='COMPLETED':raise ValueError('empty completed refinement release')
    for row in packet['records']:
        if row.get('evaluation'):
            from experiments.submission_refresh.selection import summarize
            evaluation=row['evaluation'];trials=evaluation['trials']
            if [t['seed'] for t in trials]!=list(range(50)):raise ValueError('incomplete refinement trials')
            if evaluation['point_id']!=row['point']['point_id'] or evaluation['Q_object']!=row['point']['objects']['Q']:raise ValueError('rounding point identity mismatch')
            recalculated=summarize(trials,objective='inertia')
            for metric in ['acc_mean','nmi_mean','acc_sd','nmi_sd']:
                if not np.isclose(recalculated[metric],evaluation['summary'][metric],rtol=0,atol=1e-12):raise ValueError('trial/summary mismatch')
            native=min(trials,key=lambda t:(t['inertia'],t['seed']))
            if any(evaluation['native_best'][k]!=native[k] for k in ['seed','acc','nmi','inertia']):raise ValueError('native endpoint mismatch')
    derived=views(packet['protocol'],packet['datasets_lock'],packet['records'],packet['gates'],packet['diagnostics'],packet['run_state'])
    if len(derived['trials'])!=manifest['counts']['trials']:raise ValueError('refinement count mismatch')
    out=Path(output).resolve()
    if out==root or any(out==root/f or out in (root/f).parents for f in manifest['files']):raise ValueError('rebuild overlaps release inputs')
    if out.exists() and any(out.iterdir()) and not (out/'validation.json').is_file():raise ValueError('refusing unknown output directory')
    out.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.refinement-rebuild-',dir=out.parent))
    try:
        publish_views(stage,derived,packet['gates'],packet['diagnostics'],packet['run_state'])
        if packet.get('confirmation') is not None:atomic_json(stage/'context_confirmation.json',packet['confirmation'])
        atomic_json(stage/'validation.json',{'ok':True,'data_read':False,'external_artifact_read':False,'Git_history_read':False,'trials':len(derived['trials'])})
        if out.exists():
            backup=out.with_name(out.name+'.previous')
            if backup.exists():raise ValueError('previous rebuild recovery directory already exists')
            out.rename(backup)
            try:os.replace(stage,out)
            except BaseException:backup.rename(out);raise
            shutil.rmtree(backup)
        else:os.replace(stage,out)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return derived


def _markdown(derived,gates,state,diagnostics=None):
    lines=['# Independent refinement results','','The inputs, objectives and operating points are registered before new benchmark scoring. ORL and YaleB are previously studied development datasets. All other inputs confirm the locked specification; they are not claimed to be unseen data.','',f"Current scientific status: **{state.get('run_status','PENDING')}**. A failed gate is a mechanism decision, not an optimized benchmark result.",'','| Benchmark | E1 original / angular | E2 angular | E3 angular |','|---|---|---|---|']
    for b in ['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']:
        statuses={(r['method'],r['panel']):r['status'] for r in derived['status'] if r['benchmark']==b};lines.append(f"| {b} | {statuses.get(('E1','original'))} / {statuses.get(('E1','angular'))} | {statuses.get(('E2','angular'))} | {statuses.get(('E3','angular'))} |")
    lines += ['','## Fixed primary paired effects','','Each entry uses the same configuration and complete seeds 0–49 for ACC/NMI. Differences are percentage points relative to matched ordinary SSC. Intervals are conditional rounding-seed intervals, not new-dataset uncertainty. Uncertified rows are exploratory.','','| Benchmark | Method / panel | ACC delta [95% interval] | NMI delta [95% interval] | Qualified |','|---|---|---:|---:|---|']
    for r in derived['contrasts']:
        if r['comparison']==r['method']+'_minus_SSC':lines.append(f"| {r['benchmark']} | {r['method']} / {r['panel']} | {r['ACC_delta_pp']:.3f} [{r['ACC_lower_pp']:.3f}, {r['ACC_upper_pp']:.3f}] | {r['NMI_delta_pp']:.3f} [{r['NMI_lower_pp']:.3f}, {r['NMI_upper_pp']:.3f}] | {r['qualified']} |")
    lines += ['','## Mechanisms and attribution','', 'E1 tests protection of global dispersion, separately from any gain beyond interpolation. E2 uses the two fixed radial-neutralization development contrasts and the declared isotropic control. E3 uses frozen comparison coverage/semantics, triplet-only correction and three matched random-force controls. The complete objective, certificate, movement, runtime, mean/SD, native and contrast rows are retained in the result files.']
    for row in derived['macros']:
        if row['method']=='E1' and row['comparison'] in ['matched SC','matched SSC','matched interpolation']:
            complete=row['status']=='COMPLETE_QUALIFIED_EIGHT'
            lines += ['',f"E1 {row['panel']} against {row['comparison']}: "+(f"ACC {row['ACC_delta_pp']:+.3f} pp, NMI {row['NMI_delta_pp']:+.3f} pp (8/8 qualified)." if complete else f"eight-benchmark macro unavailable ({row['qualified_datasets']}/8 qualified); explicitly partial ACC {row['partial_ACC_delta_pp']:+.3f} pp / NMI {row['partial_NMI_delta_pp']:+.3f} pp." if row['qualified_datasets'] else 'unavailable (0/8 qualified).')]
    if diagnostics:
        tubes=[p for p in diagnostics.get('points',{}).values() if 'stopping_tubes' in p]
        if tubes:
            lower=min(p['dispersion']['output']['lower']/p['dispersion']['anchor']['upper'] for p in tubes);fraction=max(p['stopping_tubes']['strictly_inside_stopping_tube_fraction'] for p in tubes)
            lines += ['',f"The saved primary E1 outputs retain at least {100*lower:.3f}% of anchor dispersion under the median bounds, far above the 25% guaranteed floor. At most {100*fraction:.3f}% of edges lie strictly inside the stopping tubes. These supplementary geometric diagnostics do not identify correct class relations or establish a clustering benefit."]
        affine=diagnostics.get('affine_checks',[])
        if affine:lines += ['',f"All {len(affine)} uniform-origin-scaling checks preserve the SC partitions for all 50 seeds; this is a geometry check and supplies no additional method benefit."]
    for method,gate in gates.items():
        lines += ['',f"{method} promotion: **{'PASSED' if gate['promoted'] else 'NOT PROMOTED'}**."]
        for b,outcome in gate['development_outcomes'].items():
            detail=''
            if method=='E2' and outcome.get('geometry'):
                g=outcome['geometry'];detail=f" Inward energy {100*g['inward_radial_energy_share']:.4f}%; RMS neutralization angle {g['RMS_angle_degrees']:.6f} degrees; ACC change {outcome['ACC']['delta_pp']:+.3f} pp (adjusted lower {outcome['ACC']['lower_pp']:+.3f}); NMI change {outcome['NMI']['delta_pp']:+.3f} pp."
            elif method=='E3':detail=f" {outcome['triplets']} comparisons (minimum {outcome['minimum_triplets']}); correct {100*outcome['correct_fraction']:.2f}% and reversed {100*outcome['reversed_fraction']:.2f}%." if outcome['correct_fraction'] is not None else ' No usable comparisons.'
            lines.append(f"- {b}: {outcome['decision']}."+detail)
    lines += ['','## Coverage and limitations','', 'An eight-benchmark macro requires all eight qualified paired rows of that named panel. Partial summaries keep their denominator and do not substitute for a full macro. Inactive certified outputs have valid metrics. All inputs retain unverified historical identity; native-16 MSRA is an adapted proxy, AR is a source-order hypothesis and UMIST retains 10,304 features. Mathematical bounds concern G; rounding and hinge satisfaction after row normalization concern Q. The scalar release rebuilds without data arrays, private artifact stores or old Git objects.']
    (ROOT/'docs/extension_verification_results.md').write_text('\n'.join(lines)+'\n')


def latex_tables(derived,gates,diagnostics):
    """Produce report inputs from the same validated release as the CSV tables."""
    from experiments.submission_refresh.reporting import escape
    def f(value,places=3):return '--' if value is None else f'{value:.{places}f}'
    names={'radial_neutralization':'radial R','uniform_scaling':'scale','interpolation':'mix','random_hinge_400':'random 400','random_hinge_401':'random 401','random_hinge_402':'random 402'}
    labels={'COMPLETED_CERTIFIED':'certified','NUMERICALLY_INACTIVE':'inactive (certified)','COMPLETED_UNCERTIFIED':'uncertified','GATE_FAILED':'not promoted','PENDING':'pending','NOT_RUN_BUDGET':'budget-unrun','FAILED_OR_NOT_RUN':'failed / unrun'}
    main=[r'\noindent\textbf{Fixed primary effects.} Differences are percentage points against matched ordinary SSC; C means both saved outputs are certified. A gated method has no formal benchmark score. All historical identities remain unverified; MSRA denotes the adapted native-16 proxy.',r'\begin{center}\small\begin{tabular}{lrrrr}\toprule',r'Data & E1 orig. $\Delta$ACC & $\Delta$NMI & E1 angular $\Delta$ACC & $\Delta$NMI\\\midrule']
    for b in ['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']:
        values=[]
        for panel in ['original','angular']:
            match=[r for r in derived['contrasts'] if r['benchmark']==b and r['panel']==panel and r['comparison']=='E1_minus_SSC']
            row=match[0] if match else {};mark=' C' if row.get('qualified') else ' U' if row else ''
            values.extend([f(row.get('ACC_delta_pp'))+mark,f(row.get('NMI_delta_pp'))])
        main.append(escape(b)+' & '+' & '.join(values)+r'\\')
    main += [r'\bottomrule\end{tabular}\end{center}']
    for method in ['E2','E3']:
        gate=gates.get(method);main.append(r'\noindent '+method+': '+('development gate '+('passed' if gate['promoted'] else 'not passed') if gate else 'development gate pending')+r'.\par')
    macros=[r for r in derived['macros'] if r['comparison']=='matched SSC']
    main.append(r'\noindent Eight-input qualified paired macro: '+('; '.join(r['method']+' '+r['panel']+': '+(f(r['ACC_delta_pp'])+' ACC / '+f(r['NMI_delta_pp'])+' NMI' if r['ACC_delta_pp'] is not None else 'unavailable ('+str(r['qualified_datasets'])+'/8)') for r in macros))+r'.\par')
    appendix=[r'\subsection{Registered endpoint status}',r'\begin{longtable}{llp{.28\linewidth}p{.30\linewidth}}\toprule Data & Study & Panel & Status\\\midrule\endhead']
    for row in derived['status']:appendix.append(' & '.join(escape(str(x)) for x in [row['benchmark'],row['method'],row['panel'],labels.get(row['status'],row['status'])])+r'\\')
    appendix += [r'\bottomrule\end{longtable}',r'\subsection{Complete fixed-point means and numerical qualification}',r'Bold study names denote primary operating points. Means and sample SD use the same complete fifty seeds. Native single-assignment endpoints and all seeds are retained in the CSV/gzip release. Gated or unrun points are absent from this measured table, rather than filled with zeros.',r'\begingroup\scriptsize\setlength{\tabcolsep}{3pt}',r'\begin{longtable}{lllp{.14\linewidth}rrrrr}\toprule Data & Study & Panel & Parameters & ACC & NMI & Gap & Move & CPU (s)\\\midrule\endhead']
    for row in derived['metrics']:
        if row['endpoint']!='mean_sample_sd_50':continue
        parameters='gamma='+format(row['actual_gamma'],'.4g')+(' '+','.join(k+'='+str(v) for k,v in row['parameters'].items()) if row['parameters'] else '')
        vals=[escape(row['benchmark']),(r'\textbf{'+escape(names.get(row['method'],row['method']))+'}' if row['primary'] else escape(names.get(row['method'],row['method']))),escape(row['panel']),escape(parameters),f(row['acc_mean'])+r'$\pm$'+f(row['acc_sd']),f(row['nmi_mean'])+r'$\pm$'+f(row['nmi_sd']),'--' if row['relative_gap'] is None else format(row['relative_gap'],'.3g')+(' C' if row['certified'] else ' U'),f(row['normalized_L21_movement'],4),f(row['fit_CPU_seconds'],1)]
        appendix.append(' & '.join(vals)+r'\\')
    appendix += [r'\bottomrule\end{longtable}\endgroup',r'\subsection{All declared paired contrasts}',r'Intervals use 10,000 paired resamples of rounding seeds, conditional on the fixed input and saved representation. Qualification requires both applicable convex certificates. Interpolation, radial neutralization and SC are deterministic references, not certified optimizers of another target.',r'\begingroup\scriptsize\setlength{\tabcolsep}{3pt}',r'\begin{longtable}{llp{.28\linewidth}rrl}\toprule Data & Panel & Contrast & $\Delta$ACC [interval] & $\Delta$NMI & Qualified\\\midrule\endhead']
    for row in derived['contrasts']:
        appendix.append(' & '.join([escape(row['benchmark']),escape(row['panel']),escape(row['comparison']),f(row['ACC_delta_pp'])+' ['+f(row['ACC_lower_pp'])+', '+f(row['ACC_upper_pp'])+']',f(row['NMI_delta_pp']),str(row['qualified'])])+r'\\')
    appendix += [r'\bottomrule\end{longtable}\endgroup',r'\subsection{Development mechanism decisions}']
    for method,gate in gates.items():
        appendix.append(r'\paragraph{'+method+': '+('promoted' if gate['promoted'] else 'not promoted')+r'.} Both predefined development outcomes follow.')
        for b,row in gate['development_outcomes'].items():
            text=b+': '+row['decision']+'. '
            if method=='E2':
                geom=row.get('geometry',{});text+='Inward energy share '+f(geom.get('inward_radial_energy_share'))+', RMS angle '+f(geom.get('RMS_angle_degrees'))+' degrees. '
                if row.get('ACC'):text+='ACC change '+f(row['ACC']['delta_pp'])+' pp, adjusted lower '+f(row['ACC']['lower_pp'])+' pp; NMI change '+f(row['NMI']['delta_pp'])+' pp. '
            else:text+='Comparisons '+str(row['triplets'])+' / required '+str(row['minimum_triplets'])+'; correct fraction '+f(row['correct_fraction'])+', reversed fraction '+f(row['reversed_fraction'])+'. '
            appendix.append(escape(text)+r'\par')
    appendix += [r'\paragraph{Interpretation.} Dispersion and hinge diagnostics concern the saved optimized G. Output normalization may alter hinge satisfaction and angular movement. Numerical activity, retained dispersion and passing a development gate do not by themselves establish ACC/NMI gains beyond the named controls. Full saved-array diagnostics, conditions, masks, failures and object identities accompany the scalar release.']
    (ROOT/'report/tables/refinement_main.tex').write_text('\n'.join(main)+'\n');(ROOT/'report/tables/refinement_appendix.tex').write_text('\n'.join(appendix)+'\n')


def tables_from_release(manifest_path):
    with tempfile.TemporaryDirectory(prefix='refinement-report-') as temporary:
        derived=rebuild(manifest_path,Path(temporary)/'rebuilt')
    path=Path(manifest_path).resolve();manifest=json.loads(path.read_text());root=(path.parent/manifest['checkout_root_relative']).resolve();packet=json.loads(gzip.decompress((root/manifest['packet_file']).read_bytes()))
    latex_tables(derived,packet['gates'],packet['diagnostics'])


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Generate report tables from the validated scalar release.');parser.add_argument('--release-manifest',default='configs/extension_verification/release_manifest.json');args=parser.parse_args();tables_from_release(args.release_manifest)
