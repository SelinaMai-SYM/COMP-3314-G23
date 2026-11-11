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


def point_status(record,evaluation):
    if evaluation is None:return 'PENDING'
    solver=record['solver']
    if solver.get('certified') is None:return 'COMPLETED_REFERENCE'
    if not solver['certified']:return 'COMPLETED_UNCERTIFIED'
    return 'COMPLETED_CERTIFIED' if solver['numerically_active'] else 'NUMERICALLY_INACTIVE'


def views(spec,lock,records,gates,diagnostics,run_state):
    metrics=[];trials=[];contrasts=[];status=[];by_id={r['point']['point_id']:r for r in records};primary={}
    for packet in records:
        row=packet['point'];evaluation=packet.get('evaluation');solver=row['solver'];common={'benchmark':row['benchmark'],'candidate_id':row['candidate_id'],'role':row['role'],'historical_identity':'UNVERIFIED','adaptation_flags':row['qualification'],'method':row['method'],'panel':row['panel'],'point_id':row['point_id'],'primary':bool(row.get('primary')),'purposes':row.get('purposes',[]),'parameters':row['parameters'],'actual_gamma':row['gamma'],'output_normalization':row['output_normalization'],'n_samples':row['n'],'K':row['K'],'trial_count':len(evaluation['trials']) if evaluation else 0,'status':point_status(row,evaluation),'certified':solver.get('certified'),'relative_gap':solver.get('relative_gap'),'absolute_gap':solver.get('absolute_gap'),'normalized_L21_movement':solver.get('normalized_L21_movement'),'fit_CPU_seconds':row.get('cumulative_charged_fit_CPU_seconds'),'rounding_CPU_seconds':evaluation.get('CPU_seconds') if evaluation else None,'G_sha256':row['objects']['G']['sha256'],'Q_sha256':row['objects']['Q']['sha256'],'source_fingerprint':row['source_fingerprint'],'protocol_sha256':row['protocol_sha256']}
        if row.get('primary'):primary[(row['benchmark'],row['panel'],row['method'])]=packet
        if evaluation is None:continue
        metrics.append({**common,'endpoint':'mean_sample_sd_50',**{k:evaluation['summary'][k] for k in ['acc_mean','acc_sd','nmi_mean','nmi_sd']},'selected_seed':None})
        native=evaluation['native_best'];metrics.append({**common,'endpoint':'native_best_of_50','acc_mean':100*native['acc'],'nmi_mean':100*native['nmi'],'acc_sd':None,'nmi_sd':None,'selected_seed':native['seed']})
        for trial in evaluation['trials']:trials.append({'point_id':row['point_id'],'benchmark':row['benchmark'],'method':row['method'],'panel':row['panel'],**trial})
    def contrast(target,base,comparison):
        if target is None or base is None or not target.get('evaluation') or not base.get('evaluation'):return
        a=target['point'];b=base['point'];qualified=all(r['solver'].get('certified') is not False for r in [a,b])
        acc=paired(target['evaluation']['trials'],base['evaluation']['trials'],'acc');nmi=paired(target['evaluation']['trials'],base['evaluation']['trials'],'nmi')
        contrasts.append({'benchmark':a['benchmark'],'panel':a['panel'],'method':a['method'],'comparison':comparison,'target_point_id':a['point_id'],'control_point_id':b['point_id'],'target_gamma':a['gamma'],'control_gamma':b['gamma'],'qualified':qualified,'ACC_delta_pp':acc['delta_pp'],'ACC_lower_pp':acc['lower_pp'],'ACC_upper_pp':acc['upper_pp'],'NMI_delta_pp':nmi['delta_pp'],'NMI_lower_pp':nmi['lower_pp'],'NMI_upper_pp':nmi['upper_pp'],'bootstrap_resamples':10000,'bootstrap_seed':424242,'interval_scope':'Conditional paired rounding seeds; no new-dataset inference'})
    for benchmark in spec['inputs']['dataset_order']:
        entry=lock['datasets'][benchmark]
        for method,panels in [('E1',['original','angular']),('E2',['angular']),('E3',['angular'])]:
            for panel in panels:
                packet=primary.get((benchmark,panel,method));gate=gates.get(method)
                result=point_status(packet['point'],packet.get('evaluation')) if packet else 'GATE_FAILED' if gate is not None and not gate['promoted'] else 'NOT_RUN_BUDGET' if run_state.get('run_status')=='STOPPED_SHARED_BUDGET' else 'FAILED_OR_NOT_RUN' if run_state.get('run_status')=='FAILED_REQUIRES_INVESTIGATION' else 'PENDING'
                reason='Development mechanism gate did not permit benchmark optimization' if result=='GATE_FAILED' else run_state.get('stop_reason') if packet is None else packet['point']['solver'].get('stopping_reason')
                status.append({'benchmark':benchmark,'candidate_id':entry['candidate_id'],'role':entry['role'],'method':method,'panel':panel,'status':result,'reason':reason,'point_id':packet['point']['point_id'] if packet else None,'historical_identity':'UNVERIFIED','adaptation_flags':entry['qualification'],'force_reference_status':entry['gamma_references'][panel]['reference_status'],'actual_primary_gamma':entry['gamma_references'][panel]['primary_gamma']})
                if packet is None:continue
                controls=['SC','SSC']+(['interpolation'] if method=='E1' else ['isotropic'] if method=='E2' else ['triplet_only','random_hinge_400','random_hinge_401','random_hinge_402'])
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
          for comparator in ['SC','SSC']:
            rows=[r for r in contrasts if r['method']==method and r['panel']==panel and r['comparison']==method+'_minus_'+comparator and r['qualified']]
            complete=len({r['benchmark'] for r in rows})==8
            macros.append({'method':method,'panel':panel,'comparison':'matched '+comparator,'qualified_datasets':len(rows),'denominator':8,'status':'COMPLETE_QUALIFIED_EIGHT' if complete else 'UNAVAILABLE_INCOMPLETE_QUALIFIED_COVERAGE','ACC_delta_pp':float(np.mean([r['ACC_delta_pp'] for r in rows])) if complete else None,'NMI_delta_pp':float(np.mean([r['NMI_delta_pp'] for r in rows])) if complete else None,'partial_ACC_delta_pp':float(np.mean([r['ACC_delta_pp'] for r in rows])) if rows and not complete else None,'partial_NMI_delta_pp':float(np.mean([r['NMI_delta_pp'] for r in rows])) if rows and not complete else None})
    return {'metrics':metrics,'trials':trials,'contrasts':contrasts,'status':status,'macros':macros}


def publish_views(out,derived,gates,diagnostics,run_state):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    csv_write(out/'status.csv',derived['status']);csv_write(out/'metrics.csv',derived['metrics'],None if derived['metrics'] else ['benchmark','method','panel','status','acc_mean','acc_sd','nmi_mean','nmi_sd'])
    csv_write(out/'contrasts.csv',derived['contrasts'],None if derived['contrasts'] else ['benchmark','method','panel','comparison','qualified','ACC_delta_pp','NMI_delta_pp'])
    csv_write(out/'macro_summary.csv',derived['macros']);temporary=out/'trials.csv';csv_write(temporary,derived['trials'],None if derived['trials'] else ['point_id','benchmark','method','panel','seed','acc','nmi','inertia']);raw=temporary.read_bytes();(out/'trials.csv.gz').write_bytes(gzip.compress(raw,mtime=0));temporary.unlink()
    atomic_json(out/'diagnostics/gates.json',gates);atomic_json(out/'diagnostics/saved_points.json',diagnostics);atomic_json(out/'coverage.json',{'status_counts':dict(__import__('collections').Counter(r['status'] for r in derived['status'])),'extension_benchmark_pairs':24,'primary_panel_rows':32,'stage_completion':run_state.get('stages',{}),'run_status':run_state.get('run_status','PENDING'),'stop_reason':run_state.get('stop_reason')})


def report(config,artifact_root,output):
    from .inputs import load_locked
    spec,lock,store=load_locked(config,artifact_root);packets=[]
    for path in sorted((store.root/'points').glob('*.json')):
        point=json.loads(path.read_text())
        if point['source_fingerprint']!=lock['source_fingerprint']:continue
        evaluation=store.root/'evaluations'/f"{point['point_id']}.json";packets.append({'point':point,'evaluation':json.loads(evaluation.read_text()) if evaluation.exists() else None})
    gates={method:json.loads((store.root/'gates'/f'{method}.json').read_text()) for method in ['E2','E3'] if (store.root/'gates'/f'{method}.json').exists()};diagnostics=json.loads((store.root/'diagnostics.json').read_text()) if (store.root/'diagnostics.json').exists() else {};state=json.loads((store.root/'campaign_state.json').read_text()) if (store.root/'campaign_state.json').exists() else {}
    derived=views(spec,lock,packets,gates,diagnostics,state);out=Path(output).resolve();publish_views(out,derived,gates,diagnostics,state)
    evidence={'schema':'ssc-refinement-scalar-packet-v1','protocol':spec,'datasets_lock':lock,'records':packets,'gates':gates,'diagnostics':diagnostics,'run_state':{k:state.get(k) for k in ['run_status','stages','stop_reason']}}
    payload=(json.dumps(evidence,sort_keys=True,allow_nan=False)+'\n').encode();packet=out/'scalar_records.v1.json.gz';packet.write_bytes(gzip.compress(payload,mtime=0));manifest={'schema':'ssc-refinement-release-v1','checkout_root_relative':os.path.relpath(out,ROOT/'configs/extension_verification'),'packet_file':packet.name,'files':{packet.name:{'sha256':digest(packet),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'bytes':packet.stat().st_size}},'protocol_sha256':lock['protocol_sha256'],'source_fingerprint':lock['source_fingerprint'],'counts':{'points':len(packets),'trials':len(derived['trials']),'primary_panel_rows':32},'scope':'Fixed reference inputs; no subset or performance-based parameter selection'}
    atomic_json(ROOT/'configs/extension_verification/release_manifest.json',manifest)
    # Only scientific objects in these packets are advertised. Command logs,
    # private instructions and operational queues are outside the closure.
    from experiments.submission_refresh.export_artifacts import references
    refs={ref['sha256']:ref for ref in references(evidence)};atomic_json(out/'artifact_manifest.json',{'schema':'ssc-refinement-artifacts-v1','records':[{'record':'refinement/scalar_records.json','object':store.put(evidence)}],'numerical_objects':list(refs.values()),'restriction':'Provider-restricted arrays remain outside Git; exact public regeneration is documented'})
    _markdown(derived,gates,state);return derived


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
        publish_views(stage,derived,packet['gates'],packet['diagnostics'],packet['run_state']);atomic_json(stage/'validation.json',{'ok':True,'data_read':False,'external_artifact_read':False,'Git_history_read':False,'trials':len(derived['trials'])})
        if out.exists():shutil.rmtree(out)
        os.replace(stage,out)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return derived


def _markdown(derived,gates,state):
    lines=['# Independent refinement results','','The inputs, objectives and operating points are registered before new benchmark scoring. ORL and YaleB are previously studied development datasets. All other inputs confirm the locked specification; they are not claimed to be unseen data.','',f"Current scientific status: **{state.get('run_status','PENDING')}**. A failed gate is a mechanism decision, not an optimized benchmark result.",'','| Benchmark | E1 original / angular | E2 angular | E3 angular |','|---|---|---|---|']
    for b in ['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']:
        statuses={(r['method'],r['panel']):r['status'] for r in derived['status'] if r['benchmark']==b};lines.append(f"| {b} | {statuses.get(('E1','original'))} / {statuses.get(('E1','angular'))} | {statuses.get(('E2','angular'))} | {statuses.get(('E3','angular'))} |")
    lines += ['','## Fixed primary paired effects','','Each entry uses the same configuration and complete seeds 0–49 for ACC/NMI. Differences are percentage points relative to matched ordinary SSC. Intervals are conditional rounding-seed intervals, not new-dataset uncertainty. Uncertified rows are exploratory.','','| Benchmark | Method / panel | ACC delta [95% interval] | NMI delta [95% interval] | Qualified |','|---|---|---:|---:|---|']
    for r in derived['contrasts']:
        if r['comparison']==r['method']+'_minus_SSC':lines.append(f"| {r['benchmark']} | {r['method']} / {r['panel']} | {r['ACC_delta_pp']:.3f} [{r['ACC_lower_pp']:.3f}, {r['ACC_upper_pp']:.3f}] | {r['NMI_delta_pp']:.3f} [{r['NMI_lower_pp']:.3f}, {r['NMI_upper_pp']:.3f}] | {r['qualified']} |")
    lines += ['','## Mechanisms and attribution','', 'E1 tests protection of global dispersion, separately from any gain beyond interpolation. E2 uses the two fixed radial-neutralization development contrasts and the declared isotropic control. E3 uses frozen comparison coverage/semantics, triplet-only correction and three matched random-force controls. The complete objective, certificate, movement, runtime, mean/SD, native and contrast rows are retained in the result files.']
    for method,gate in gates.items():
        lines += ['',f"{method} promotion: **{'PASSED' if gate['promoted'] else 'NOT PROMOTED'}**."]
        for b,outcome in gate['development_outcomes'].items():lines.append(f"- {b}: {outcome['decision']}.")
    lines += ['','## Coverage and limitations','', 'An eight-benchmark macro requires all eight qualified paired rows of that named panel. Partial summaries keep their denominator and do not substitute for a full macro. Inactive certified outputs have valid metrics. All inputs retain unverified historical identity; native-16 MSRA is an adapted proxy, AR is a source-order hypothesis and UMIST retains 10,304 features. Mathematical bounds concern G; rounding and hinge satisfaction after row normalization concern Q. The scalar release rebuilds without data arrays, private artifact stores or old Git objects.']
    (ROOT/'docs/extension_verification_results.md').write_text('\n'.join(lines)+'\n')
