"""Authoritative trial aggregation, explicit coverage, and locked confirmation."""
from __future__ import annotations
import csv,gzip,json,time,os,shutil,tempfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import yaml
from experiments.submission_refresh.core import ROOT,ArtifactStore,ResourceLedger,atomic_json,digest,identity
from experiments.submission_refresh.selection import distances,rank,summarize
from .runner import GAMMAS,INITS,round_embedding
from .markdown import benchmark_markdown
from .certified_status import certified_search_status

def write_csv(path,rows,fields=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def compatibility_counts(candidate,policy):
    """Frozen policy values; this helper neither scores nor changes eligibility."""
    c=candidate;flags=policy['paper_deviation_flags'];assumptions=policy['additional_assumptions']
    input_norm=c['prep'] in ['Y1','Y3'];embedding_norm=c['prep'] in ['Y2','Y3']
    return {'paper_deviations':
        int(c['benchmark']=='MSRA50' and c['p']==256)*int(flags['native_MSRA16_instead_of32'])
        +int(c['family']=='BinAlpha_order_sensitivity')*int(flags['deterministic_BinAlpha_membership_instead_of_stated_random_sampling'])
        +int(input_norm)*int(flags['input_row_L2_changes_pixel_vectors'])
        +int(embedding_norm)*int(flags['embedding_row_L2_changes_raw_eigenvector_representation']),
        'preparation_assumptions':int(policy['family_preparation_assumptions'][c['family']])
        +int(c['benchmark']=='YaleB' and 'cropped2414' in c['candidate_id'])*int(assumptions['declared_resize_interpolation_for_cropped_yaleb'])
        +int(input_norm)*int(assumptions['input_row_L2'])+int(embedding_norm)*int(assumptions['embedding_row_L2']),
        'compatibility_policy_version':policy['version']}


def fixed_distributions(fixed):
    rows=[]
    for benchmark,pool in sorted({(r['benchmark'],r['pool']) for r in fixed}):
        unique={}
        for r in fixed:
            if r['benchmark']==benchmark and r['pool']==pool:unique.setdefault(r.get('alias_of') or r['candidate_id'],r)
        chosen=list(unique.values())
        if not chosen:continue
        for metric in ['acc_mean','nmi_mean']:
            values=[r[metric] for r in chosen]
            rows.append({'benchmark':benchmark,'pool':pool,'metric':metric,'unique_candidates':len(chosen),
                         'median':float(np.median(values)),'min':min(values),'max':max(values)})
    return rows


def family_distributions(fixed):
    rows=[]
    for benchmark,pool,family in sorted({(r['benchmark'],r['pool'],r['family']) for r in fixed}):
        allrows=[r for r in fixed if (r['benchmark'],r['pool'],r['family'])==(benchmark,pool,family)]
        for weighting in ['declared_candidates_with_aliases','unique_physical_inputs']:
            chosen=allrows
            if weighting=='unique_physical_inputs':
                unique={}
                for r in allrows:unique.setdefault(r.get('alias_of') or r['candidate_id'],r)
                chosen=list(unique.values())
            for metric in ['acc_mean','nmi_mean']:
                values=[r[metric] for r in chosen]
                rows.append({'family':family,'benchmark':benchmark,'pool':pool,'weighting':weighting,
                             'declared_candidates':len(allrows),'observations':len(chosen),'metric':metric,
                             'median':float(np.median(values)),'min':min(values),'max':max(values)})
    return rows


def reference_contrasts(summaries,fixed,reference_ids,candidate_pools=None):
    rows=[]
    for benchmark,reference in reference_ids.items():
        baseline=next((r for r in fixed if r['candidate_id']==reference),None)
        reference_grid=[r for r in summaries if r['candidate_id']==reference]
        intended_pools=(candidate_pools or {}).get(benchmark,{r['pool'] for r in summaries if r['benchmark']==benchmark and r['pool']!='diagnostic'})
        for pool in sorted(intended_pools):
            pools=[('reference_candidate_reference_settings',[baseline] if baseline else []),
                   ('candidate_cohort_reference_settings',[r for r in fixed if r['benchmark']==benchmark and r['pool']==pool]),
                   ('reference_candidate_frozen_grid',reference_grid),
                   ('candidate_cohort_frozen_grid',[r for r in summaries if r['benchmark']==benchmark and r['pool']==pool])]
            for contrast,items in pools:
                if items:
                    chosen=rank(items)[0]
                    rows.append({**chosen,'contrast':contrast,'target_pool':pool,'reference_candidate':reference,
                                 'reference_pool':baseline['pool'] if baseline else None,
                                 'eligible_configurations_in_contrast':len(items),
                                 'selection':'same joint minimax; descriptive retrospective comparison'})
                else:rows.append({'benchmark':benchmark,'target_pool':pool,'reference_candidate':reference,
                                  'contrast':contrast,'status':'UNAVAILABLE_INCOMPLETE_REFERENCE'})
    return rows

def matched_sc_contrasts(winners,sc_rows):
    contrasts=[]
    for r in winners:
        sc=next((v for v in sc_rows if v['candidate_id']==r['candidate_id'] and v['initialization']==r['initialization']),None)
        if sc is None:
            contrasts.append({'config_id':r['config_id'],'candidate_id':r['candidate_id'],'benchmark':r['benchmark'],'pool':r['pool'],'endpoint':r['endpoint'],
                'status':'UNAVAILABLE_MATCHED_SC','matched_sc_status':r.get('matched_sc_status','NOT_RUN'),
                'qualification':'The matching SC initialization failed or was unrun; no paired SC contrast is claimed.'})
            continue
        if r.get('F_sha256') and sc.get('F_sha256')!=r['F_sha256']:raise ValueError('SC/SSC contrast does not share F')
        endpoint=sc if r['endpoint']=='mean_sample_sd_50' else sc['native_best']
        contrasts.append({'config_id':r['config_id'],'candidate_id':r['candidate_id'],'benchmark':r['benchmark'],
            'pool':r['pool'],'endpoint':r['endpoint'],'F_sha256':r.get('F_sha256'),
            'ssc_acc':r['acc_mean'],'ssc_nmi':r['nmi_mean'],'sc_acc':endpoint['acc_mean'],'sc_nmi':endpoint['nmi_mean'],
            'ssc_acc_sd':r['acc_sd'],'ssc_nmi_sd':r['nmi_sd'],'sc_acc_sd':endpoint['acc_sd'],'sc_nmi_sd':endpoint['nmi_sd'],
            'ssc_selected_seed':r.get('seed') if r['endpoint']=='native_best_of_50' else None,
            'sc_selected_seed':endpoint.get('seed') if r['endpoint']=='native_best_of_50' else None,
            'n':50 if r['endpoint']=='mean_sample_sd_50' else 1,
            'delta_acc_pp':r['acc_mean']-endpoint['acc_mean'],'delta_nmi_pp':r['nmi_mean']-endpoint['nmi_mean'],
            'qualification':'Same selected samples/F/protocol. Native endpoints independently select the within-method best of 50; the two single selected seeds are not a paired seed contrast.'})
    return contrasts


def _execution_details(folder,store):
    """Read original and supplemental outcomes without rewriting their history."""
    state=json.loads((folder/'status.json').read_text()) if (folder/'status.json').is_file() else {}
    failures=[];attempts=[]
    for path in sorted((folder/'completion_failures').glob('*.json')):
        failures.append({'path':str(path.relative_to(store.root)),'sha256':digest(path),'record':json.loads(path.read_text())})
    for path in sorted((folder/'completion_attempts').glob('*.json')):
        attempts.append({'path':str(path.relative_to(store.root)),'sha256':digest(path),'record':json.loads(path.read_text())})
    index=json.loads((folder/'completion_status.json').read_text()) if (folder/'completion_status.json').is_file() else {}
    return {'original_status':state,'completion_failures':failures,'completion_attempts':attempts,'completion_index':index}


def _active_matches(active,method,variant,gamma,init):
    return active.get('method')==method and (method=='sc' or (active.get('variant')==variant and active.get('gamma_nominal')==gamma)) and (active.get('stage')=='solver' or active.get('initialization')==init)


def _point_outcome(details,method,variant,gamma,init,record=None):
    """Keep failed/unrun points separate from later independent completions."""
    original=details['original_status'];active=original.get('active_configuration',{})
    original_active=_active_matches(active,method,variant,gamma,init)
    key='SC__'+init if method=='sc' else f'{variant}__{gamma:g}__{init}'
    result={'original_candidate_status':original.get('status'),
        'original_point_status':original.get('status') if original_active else None,
        'completion_candidate_status':details['completion_index'].get('latest_status'),
        'original_failure_preserved':original_active and original.get('status') in ['FAILED','TIMEOUT']}
    if record is not None:
        if result['original_failure_preserved']:raise ValueError('a completed record replaced an original failed point')
        result.update(status='COMPLETED',execution_origin='independent_completion' if record.get('completion_provenance') else 'original_candidate')
        return result
    relevant=[]
    for failure in details['completion_failures']:
        if key in failure['record'].get('blocked_points',[]):relevant.append(failure)
    if relevant:
        if len(relevant)>1:raise ValueError('one frozen point has multiple permanent completion failure markers')
        marker=relevant[0];failure=marker['record'];result.update(status='FAILED_ORIGINAL_PRESERVED' if failure.get('original_failure') else 'FAILED_COMPLETION_PRESERVED',
            failure_record=marker['path'],failure_record_sha256=marker['sha256'],failure_error=failure.get('error'))
        if not failure.get('original_failure'):
            for attempt in details['completion_attempts']:
                if attempt['record'].get('status')=='TIMEOUT' and _active_matches(attempt['record'].get('active_configuration',{}),method,variant,gamma,init):result['status']='TIMEOUT_COMPLETION_PRESERVED'
        interruption=failure.get('interrupted_rounding',{})
    elif original_active and original.get('status') in ['FAILED','TIMEOUT']:
        result.update(status=original['status'],failure_error=original.get('error'));interruption=original.get('interrupted_rounding',{})
    else:
        interruption={};latest=result['completion_candidate_status']
        if latest:result['status']='MISSING_AFTER_COMPLETION' if latest=='COMPLETED_WITH_PRESERVED_FAILURES' else 'NOT_RUN_AFTER_COMPLETION_'+latest
        else:
            status=original.get('status')
            result['status']='MISSING_RESULT' if status=='COMPLETED' else 'NOT_RUN_AFTER_CANDIDATE_'+status if status in ['FAILED','TIMEOUT'] else 'NOT_RUN_CANDIDATE_'+status if status else 'NOT_RUN'
    if interruption:
        result.update(failed_rounding_seed=interruption.get('failed_rounding_seed'),
            partial_completed_rounding_seeds=[trial['seed'] for trial in interruption.get('completed_trials',[])],
            partial_rounding_status='INCOMPLETE_INELIGIBLE; never included in complete-50 endpoints')
    return result


def _configuration_provenance(folder,path,record,store):
    primary=json.loads((folder/'source.json').read_text()) if (folder/'source.json').is_file() else {}
    supplemental=record.get('completion_provenance',{})
    source=record.get('source') if supplemental else primary
    if supplemental:
        if not isinstance(source,dict) or store.get(supplemental['source'])!=source:raise ValueError('completion configuration source object mismatch')
        if supplemental.get('implementation_hash')!=source.get('implementation_hash'):raise ValueError('completion controller/source implementation mismatch')
        controller=supplemental.get('controller');sha=supplemental.get('controller_sha256')
        if source.get('source_files',{}).get(controller)!=sha:raise ValueError('completion controller bytes are not in its actual source record')
    else:controller='experiments/subset_search/runner.py';sha=source.get('source_files',{}).get(controller)
    return {'source_record_id':identity(source) if source else None,'original_source_record_id':identity(primary) if primary else None,
        'scientific_source_commit':source.get('source_commit'),'scientific_source_fingerprint':source.get('implementation_hash'),
        'cache_identity':source.get('cache_identity'),'configuration_source_kind':'per_configuration_completion' if supplemental else 'original_candidate_source',
        'controller_path':controller,'controller_sha256':sha,'configuration_record_sha256':digest(path),
        'completion_provenance':supplemental or None}


def _aggregate(artifact_root,output):
    start=time.process_time();store=ArtifactStore(artifact_root);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    tie=yaml.safe_load((ROOT/'configs/subset_search/compatibility.yaml').read_text());cat=json.loads((ROOT/'results/subset_search/candidate_catalogue.json').read_text());paper=yaml.safe_load((ROOT/'configs/v3/paper_reference.yaml').read_text());summaries=[];fixed=[];coverage=[];native=[];refs=[];sc_rows=[];sc_coverage=[];completion_audit={}
    trialfields=['candidate_id','config_id','method','initialization','variant','gamma_nominal','seed','acc','nmi','inertia','iterations','warning'];counts=Counter()
    with gzip.open(out/'trials.csv.gz','wt',newline='') as tf:
        writer=csv.DictWriter(tf,fieldnames=trialfields,extrasaction='ignore');writer.writeheader()
        for c in cat['candidates']:
            cid=c['candidate_id'];alias=c.get('alias_of');folder=store.root/'subset'/(alias or cid)
            records={};representation=None;sc_records={}
            details=_execution_details(folder,store)
            if details['completion_attempts'] or details['completion_failures']:
                completion_audit[str(folder.relative_to(store.root))]=details
            if (folder/'representation.json').exists():
                representation=json.loads((folder/'representation.json').read_text())
                if representation.get('fingerprint')!=c['fingerprint']:raise ValueError('candidate alias/representation fingerprint mismatch')
            for scfile in sorted(folder.glob('SC__*.json')):
                sr=json.loads(scfile.read_text())
                if sr.get('status')!='COMPLETED':continue
                if representation is None or sr.get('objects',{}).get('G',{}).get('sha256')!=representation['objects']['F']['sha256']:
                    raise ValueError('matched SC did not use the exact saved candidate F')
                sc_records[sr['initialization']]=sr
                stats=summarize(sr['trials']);stats['native_best']={**stats['native_best'],'n':1}
                sc_rows.append({'candidate_id':cid,'benchmark':c['benchmark'],'pool':c['pool'],'initialization':sr['initialization'],'alias_of':alias,'n_samples':c['n'],'trials':sr['trials'],**stats,'same_embedding':'representation.json exact F; no independently regenerated SC','F_sha256':representation['objects']['F']['sha256'],'input_fingerprint':representation['fingerprint'],'sample_manifest_sha256':c['manifest_sha256'],'canonical_candidate_id':alias or cid,'source_record':str(scfile.relative_to(store.root)),**_configuration_provenance(folder,scfile,sr,store)})
            for init in INITS:
                sc_coverage.append({'candidate_id':cid,'canonical_candidate_id':alias or cid,'initialization':init,'alias_of':alias,**_point_outcome(details,'sc',None,None,init,sc_records.get(init))})
            for f in sorted(folder.rglob('*.json')):
                if f.name=='profile.json':continue
                obj=json.loads(f.read_text());refs.append({'candidate_id':cid,'record':str(f.relative_to(store.root)),'object':store.put(obj)})
                if obj.get('method')=='ssc' and obj.get('status')=='COMPLETED':records[(obj['variant'],obj['gamma_nominal'],obj['initialization'])]=obj
            for variant in ['E8','E13']:
                for gamma in GAMMAS:
                    for init in INITS:
                        record=records.get((variant,gamma,init));outcome=_point_outcome(details,'ssc',variant,gamma,init,record)
                        if record and alias:outcome['status']='COMPLETED_ALIAS'
                        coverage.append({'candidate_id':cid,'family':c['family'],'pool':c['pool'],'variant':variant,'gamma_nominal':gamma,'initialization':init,'alias_of':alias,**outcome});counts[outcome['status']]+=1
                        if not record:continue
                        if representation is None:raise ValueError('SSC scalar record has no recoverable candidate representation metadata')
                        # Recompute from all50 rows; stored summaries cannot mask a
                        # missing, duplicated or invalid seed in authoritative data.
                        s=summarize(record['trials']);benchmark=c['benchmark'];target={m:paper[m]['ssc'][benchmark]['mean'] for m in ['acc','nmi']}
                        row={'candidate_id':cid,'config_id':cid+'|'+variant+'|'+str(gamma)+'|'+init,'benchmark':benchmark,'family':c['family'],'pool':c['pool'],'n_samples':c['n'],'n_classes':c['classes'],'prep':c['prep'],'variant':variant,'gamma_nominal':gamma,'gamma_effective':record['gamma_effective'],'initialization':init,'solver_status':record['solver']['status'],'endpoint':'mean_sample_sd_50',**compatibility_counts(c,tie),'alias_of':alias,'record_directory':str(Path('subset')/(alias or cid)),'record_file':f'{variant}__{gamma:g}__{init}.json','F_sha256':representation['objects']['F']['sha256'],'G_sha256':record['objects']['G']['sha256'],'input_fingerprint':representation['fingerprint'],'sample_manifest_sha256':c['manifest_sha256'],**{k:v for k,v in s.items() if k!='native_best'}}
                        row.update(parent_id=c.get('parent_id'),source_version=c.get('parent_id'),original_parent_id=c.get('original_parent_id'),n_features=c.get('p'),source_url=c.get('source_url'),membership_rule=c.get('construction_rule'),source_specification_deviations=c.get('specification_deviations',[]))
                        row.update(**_configuration_provenance(folder,folder/row['record_file'],record,store),matched_sc_status=_point_outcome(details,'sc',None,None,init,sc_records.get(init))['status'])
                        row=distances(row,target);row.update(paper_acc=target['acc'],paper_nmi=target['nmi'],paper_acc_sd=paper['acc']['ssc'][benchmark]['sd'],paper_nmi_sd=paper['nmi']['ssc'][benchmark]['sd'],historical_identity='UNVERIFIED' if benchmark in ['AR','UMIST','BinAlpha','MSRA50'] else 'documented source; no pixel identity proof')
                        row['delta_acc_sd_pp']=row['acc_sd']-row['paper_acc_sd'];row['delta_nmi_sd_pp']=row['nmi_sd']-row['paper_nmi_sd']
                        summaries.append(row)
                        if c['prep']=='Y0' and variant=='E8' and gamma==1 and init=='RANDOM':fixed.append(row)
                        native.append(distances({**row,**s['native_best'],'n':1,'endpoint':'native_best_of_50','delta_acc_sd_pp':None,'delta_nmi_sd_pp':None},target))
                        # Aliases remain visible in coverage; avoid multiplying
                        # scientific trial observations for byte-identical inputs.
                        if not alias:
                            for trial in record['trials']:writer.writerow({**row,**trial,'method':'ssc'})
    winners=[];top=[]
    for endpoint,rows in [('mean_sample_sd_50',summaries),('native_best_of_50',native)]:
        groups=defaultdict(list)
        for r in rows:
            if r['pool']!='diagnostic':groups[(r['benchmark'],r['pool'])].append(r)
        for (b,pool),group in sorted(groups.items()):
            ordered=rank(group);winner={**ordered[0],'eligible_configurations':len(group),'unique_candidates':len({r['alias_of'] or r['candidate_id'] for r in group}),'candidate_aliases':len({r['candidate_id'] for r in group}),'qualification':'Retrospective numerical match; historical sample identity unverified; conditional rounding endpoint'}
            winners.append(winner);top.extend({**r,'rank':i+1} for i,r in enumerate(ordered[:10]))
    write_csv(out/'matched_sc_summary.csv',sc_rows);write_csv(out/'matched_sc_coverage.csv',sc_coverage);write_csv(out/'execution_coverage.csv',coverage);write_csv(out/'joint_search_summary.csv',summaries);write_csv(out/'fixed_protocol_summary.csv',fixed);write_csv(out/'closest_matches.csv',winners);write_csv(out/'top_matches.csv',top)
    write_csv(out/'native_best_summary.csv',native)
    write_csv(out/'matched_sc_contrasts.csv',matched_sc_contrasts(winners,sc_rows))
    write_csv(out/'fixed_protocol_distribution.csv',fixed_distributions(fixed))
    write_csv(out/'fixed_protocol_family_distributions.csv',family_distributions(fixed))
    reference_ids=yaml.safe_load((ROOT/'configs/subset_search/protocol.yaml').read_text())['reference_candidates']
    candidate_pools={b:{c['pool'] for c in cat['candidates'] if c['benchmark']==b and c['pool']!='diagnostic'} for b in reference_ids}
    write_csv(out/'reference_contrasts.csv',reference_contrasts(summaries,fixed,reference_ids,candidate_pools))
    certified_pools={b:{c['pool'] for c in cat['candidates'] if c['benchmark']==b and c['pool']!='diagnostic'} for b in {c['benchmark'] for c in cat['candidates']}}
    certified_status=certified_search_status(summaries,certified_pools)
    write_csv(out/'certified_search_status.csv',certified_status)
    atomic_json(out/'winner_lock.json',{'version':1,'catalogue_sha256':digest(ROOT/'results/subset_search/candidate_catalogue.json'),'selection_rule_sha256':digest(ROOT/'configs/submission_refresh/selection.yaml'),'winners':winners,'no_reselection_after_confirmation':True})
    atomic_json(out/'artifact_manifest.json',{'store':'external independent-data/scientific-artifacts/refresh-20261110','object_format':'verified content-addressed npz/npy/json','records':refs,'regeneration':'python -m experiments.subset_search run --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume','source_catalogue_sha256':digest(ROOT/'results/subset_search/candidate_catalogue.json')})
    with (out/'completion_records.json.gz').open('wb') as handle:handle.write(gzip.compress((json.dumps({'schema':'subset-completion-evidence-v1','records':completion_audit},sort_keys=True)+'\n').encode(),mtime=0))
    ssc_counts=Counter(r['candidate_id'] for r in summaries if not r['alias_of'])
    sc_counts=Counter(r['candidate_id'] for r in sc_rows if not r['alias_of'])
    atomic_json(out/'coverage_summary.json',{'intended_candidates':len(cat['candidates']),'unique_catalogue_inputs':len({r.get('alias_of') or r['candidate_id'] for r in cat['candidates']}),'status_counts':dict(counts),'complete_unique_configurations':sum(r['alias_of'] is None for r in summaries),'complete_unique_candidates':len(ssc_counts),
        'inputs_with_complete_30point_ssc_grid':sum(count==30 for count in ssc_counts.values()),
        'inputs_with_complete_30point_ssc_and_3matched_sc_grid':sum(count==30 and sc_counts[cid]==3 for cid,count in ssc_counts.items()),
        'candidate_completion_definition':'complete_unique_candidates counts inputs with any complete SSC configuration; full-grid counts are separate; aliases never multiply independent inputs',
        'cpu_aggregation_seconds':time.process_time()-start})
    for b in paper['datasets']:
        (out/(b+'.md')).write_text(benchmark_markdown(b,winners,paper,certified_status))
    return winners

def aggregate(artifact_root,output):
    """Stage all generated scalars; a failed audit preserves previous outputs."""
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.aggregate-subset-',dir=output.parent))
    try:
        winners=_aggregate(artifact_root,staged)
        old_lock=output/'winner_lock.json'
        confirmed=any((Path(artifact_root)/'confirmation').glob('confirm-*.json')) or (output/'confirmation_seed_namespace.json').exists() or (Path(artifact_root)/'confirmation/seed_namespace.json').exists()
        if old_lock.exists() and confirmed:
            previous=json.loads(old_lock.read_text())['winners']
            view=lambda rows:sorted((r['benchmark'],r['pool'],r['endpoint'],r['config_id']) for r in rows)
            if view(previous)!=view(winners):raise ValueError('winner reselection is prohibited after rounding confirmation')
        output.mkdir(parents=True,exist_ok=True)
        for path in staged.iterdir():
            if confirmed and old_lock.exists() and path.name=='winner_lock.json':continue
            os.replace(path,output/path.name)
        return winners
    finally:shutil.rmtree(staged)

_SEED_COLUMNS={'seed','rounding_seed','kmeans_seed','k_means_seed','selected_seed'}
_METRIC_COLUMNS={'acc','nmi','accuracy','mean_acc','mean_nmi','acc_mean','nmi_mean','selected_acc','selected_nmi'}


def _own_confirmation_path(relative):
    parts=Path(relative).parts
    return len(parts)>1 and parts[:2]==('results','subset_search') and 'confirmation' in Path(relative).name.lower()


def _historical_seed_paths(root,paths=None):
    """Current tracked records only; never archive code, tests or old Git objects."""
    root=Path(root).resolve()
    if paths is None:
        import subprocess
        names=subprocess.check_output(['git','ls-files','-z','--','results','runs'],cwd=root).decode().split('\0')
    else:names=[str(Path(path).relative_to(root)) if Path(path).is_absolute() else str(path) for path in paths]
    result=[]
    for name in sorted(set(filter(None,names))):
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] not in ['results','runs']:
            continue
        if _own_confirmation_path(relative) or 'sample_manifests' in relative.parts or relative.name=='candidate_catalogue.json':continue
        if not name.endswith(('.csv','.csv.gz','.jsonl','.jsonl.gz','.json','.json.gz')):continue
        path=root/relative
        if not path.is_file():raise ValueError(f'tracked historical seed source is missing: {name}')
        result.append(path)
    if paths is None:
        required={'results/v2_kmeans_protocol/all_trial_results.csv','results/v3_reproduction/all_trials.csv.gz',
                  'results/next_round/raw_trials.csv','results/v3_theory/all_trials.csv'}
        actual={str(path.relative_to(root)) for path in result}
        if not required.issubset(actual):raise ValueError('required historical v2/v3/next_round/theory trial sources are missing from the tracked checkout')
    return result


def _seed_integer(value):
    if isinstance(value,bool):raise ValueError('boolean is not a rounding seed')
    if isinstance(value,float) and (not np.isfinite(value) or not value.is_integer()):raise ValueError('nonintegral historical rounding seed')
    if isinstance(value,int):seed=value
    else:
        try:seed=int(value)
        except (TypeError,ValueError):
            number=float(value)
            if not np.isfinite(number) or not number.is_integer():raise ValueError('nonintegral historical rounding seed')
            seed=int(number)
    if seed<0:raise ValueError('negative historical rounding seed')
    return seed


def scan_historical_rounding_seeds(root=ROOT,paths=None):
    """Inventory actual result rows with scalar seed and ACC/NMI fields."""
    root=Path(root).resolve();sources=[];used=set();scanned=0
    for path in _historical_seed_paths(root,paths):
        scanned+=1;columns=set();seeds=set();counts=Counter();missing=Counter();rows_with_seeds=0
        opener=gzip.open if path.suffix=='.gz' else open
        def accept(record):
            nonlocal rows_with_seeds
            if not isinstance(record,dict):return
            normalized={str(k).strip().lower():k for k in record}
            if not (_METRIC_COLUMNS & normalized.keys()):return
            found=False
            for normalized_name in _SEED_COLUMNS & normalized.keys():
                original=normalized[normalized_name];value=record[original];columns.add(original)
                if value in [None,''] or isinstance(value,(dict,list)) or (isinstance(value,str) and value.strip().lower() in ['none','nan','na','n/a','-','unavailable']):
                    missing[original]+=1;continue
                if isinstance(value,float) and not np.isfinite(value):missing[original]+=1;continue
                seed=_seed_integer(value);columns.add(original);counts[original]+=1;seeds.add(seed);found=True
            if found:rows_with_seeds+=1
        with opener(path,'rt',newline='') as handle:
            name=path.name[:-3] if path.suffix=='.gz' else path.name
            if name.endswith('.csv'):
                reader=csv.DictReader(handle)
                if reader.fieldnames:
                    normalized={str(k).strip().lower() for k in reader.fieldnames}
                    if _SEED_COLUMNS & normalized and _METRIC_COLUMNS & normalized:
                        for record in reader:accept(record)
            else:
                def walk(node):
                    if isinstance(node,dict):
                        accept(node)
                        for value in node.values():
                            if isinstance(value,(dict,list)):walk(value)
                    elif isinstance(node,list):
                        for value in node:
                            if isinstance(value,(dict,list)):walk(value)
                if name.endswith('.jsonl'):
                    for line in handle:
                        if line.strip():walk(json.loads(line))
                else:walk(json.load(handle))
        if columns:
            used.update(seeds)
            sources.append({'path':str(path.relative_to(root)),'sha256':digest(path),'bytes':path.stat().st_size,
                'seed_columns':sorted(columns),'seed_observations_by_column':dict(counts),'missing_seed_observations_by_column':dict(missing),
                'rows_with_seeds':rows_with_seeds,'unique_seed_count':len(seeds),
                'minimum_seed':min(seeds) if seeds else None,'maximum_seed':max(seeds) if seeds else None})
    if not used:raise ValueError('no historical rounding seeds could be verified')
    return used,{'sources':sources,'scanned_record_files':scanned,'sources_with_rounding_seeds':len(sources),
                 'unique_used_seed_count':len(used),'minimum_used_seed':min(used),'maximum_used_seed':max(used),
                 'source_inventory_method':'current git ls-files index plus current working-file bytes; no Git history/object reads',
                 'scope':'tracked results/runs CSV, gzip CSV, JSONL and JSON result rows with scalar rounding-seed columns and ACC/NMI fields; own subset confirmations excluded'}


def confirmation_namespace(artifact_root,output,*,historical_paths=None):
    """Freeze once for the exact winner lock and reuse it on every resume."""
    out=Path(output);lock_path=out/'winner_lock.json';lock_hash=digest(lock_path)
    persistent=Path(artifact_root)/'confirmation'/'seed_namespace.json';published=out/'confirmation_seed_namespace.json'
    existing=[json.loads(path.read_text()) for path in [persistent,published] if path.exists()]
    if existing:
        namespace=existing[0]
        if any(record!=namespace for record in existing):raise ValueError('confirmation namespace copies disagree')
        if namespace.get('version')==3:
            from .confirmation_public import validate_public_namespace
            validate_public_namespace(namespace,out,root=ROOT)
            if not persistent.exists():atomic_json(persistent,namespace)
            if not published.exists():atomic_json(published,namespace)
            return namespace
        if namespace.get('version')!=2 or namespace.get('winner_lock_sha256')!=lock_hash:
            raise ValueError('winner lock changed or old confirmation namespace is not fully verified; never advance/reselect on resume')
        first=namespace['first']
        if first<1000000 or (first-1000000)%50 or namespace.get('count')!=50 or namespace.get('seeds')!=list(range(first,first+50)) or namespace.get('overlap') is not False:
            raise ValueError('invalid persisted confirmation namespace')
        for source in namespace['historical_inventory']['sources']:
            path=ROOT/source['path']
            if not path.is_file() or digest(path)!=source['sha256']:raise ValueError('historical seed source changed after namespace freeze')
        if not persistent.exists():atomic_json(persistent,namespace)
        if not published.exists():atomic_json(published,namespace)
        return namespace
    used,inventory=scan_historical_rounding_seeds(ROOT,historical_paths)
    first=1000000
    while any(seed in used for seed in range(first,first+50)):first+=50
    namespace={'version':2,'first':first,'count':50,'seeds':list(range(first,first+50)),
               'winner_lock_sha256':lock_hash,'historical_inventory':inventory,
               'historical_inventory_sha256':identity(inventory),'overlap':False,'no_reselection':True,
               'historical_inventory_frozen_at_namespace_lock':True,
               'resume_rule':'reuse this exact block; own confirmation files never influence a new choice'}
    atomic_json(persistent,namespace);atomic_json(published,namespace)
    return namespace

def confirm(artifact_root,output):
    from threadpoolctl import threadpool_limits
    out=Path(output);lock=json.loads((out/'winner_lock.json').read_text());store=ArtifactStore(artifact_root);ledger=ResourceLedger(artifact_root);rows=[]
    # Source scanning is one separately charged final-phase utility. The block
    # is persisted before any rounding, so interruption cannot change its seeds.
    namespace_job='confirmation-seed-audit-'+str(time.time_ns())
    if not ledger.reserve(namespace_job,120,'confirmation'):raise RuntimeError('No shared confirmation resource slot is available; resume after active workers finish')
    audit_cpu=time.process_time()
    from experiments.submission_refresh.core import install_cpu_limit
    import signal
    install_cpu_limit(120)
    try:
        namespace=confirmation_namespace(artifact_root,out)
        ledger.finish(namespace_job,time.process_time()-audit_cpu,'COMPLETED')
    except BaseException:
        ledger.finish(namespace_job,time.process_time()-audit_cpu,'FAILED');raise
    finally:signal.setitimer(signal.ITIMER_PROF,0)
    first=namespace['first']
    confirmation=store.root/'confirmation';confirmation.mkdir(exist_ok=True)
    for winner in lock['winners']:
        rid='confirm-'+identity(winner)[:20];path=confirmation/(rid+'.json')
        if path.exists():
            cached=json.loads(path.read_text())
            if cached.get('first_seed')!=first or cached.get('config_id')!=winner['config_id'] or cached.get('endpoint')!=winner['endpoint']:
                raise ValueError('cached confirmation differs from the locked namespace/endpoint')
            summarize(cached['trials'],range(first,first+50))
            rows.append(cached);continue
        if not ledger.reserve(rid,120,'confirmation'):rows.append({'config_id':winner['config_id'],'status':'NOT_RUN_BUDGET'});continue
        t=time.process_time();status='FAILED';stage='input_verification';trials=None;pred=None;sc=None;scp=None
        try:
            install_cpu_limit(120)
            folder=store.root/winner['record_directory'];record=json.loads((folder/winner['record_file']).read_text());rep=json.loads((folder/'representation.json').read_text())
            if winner.get('G_sha256') and winner['G_sha256']!=record['objects']['G']['sha256']:raise ValueError('locked winner G object changed before confirmation')
            if winner.get('F_sha256') and winner['F_sha256']!=rep['objects']['F']['sha256']:raise ValueError('locked winner F object changed before confirmation')
            G=store.get(record['objects']['G']);F=store.get(rep['objects']['F']);y=store.get(rep['objects']['y']);K=len(np.unique(y))
            with threadpool_limits(limits=1):
                stage='locked_candidate_rounding'
                trials,pred,centers=round_embedding(G,y,K,winner['initialization'],range(first,first+50))
                stage='matched_sc_rounding'
                sc,scp,_=round_embedding(F,y,K,winner['initialization'],range(first,first+50))
            stage='summary_and_publication'
            s=summarize(trials,range(first,first+50));endpoint=s if winner['endpoint']=='mean_sample_sd_50' else s['native_best'];target={'acc':winner['paper_acc'],'nmi':winner['paper_nmi']}
            row={'config_id':winner['config_id'],'candidate_id':winner['candidate_id'],'benchmark':winner['benchmark'],'pool':winner['pool'],'endpoint':winner['endpoint'],'status':'COMPLETED','first_seed':first,'namespace_sha256':identity(namespace),'winner_lock_sha256':namespace['winner_lock_sha256'],'locked_F_sha256':winner.get('F_sha256'),'locked_G_sha256':winner.get('G_sha256'),'selection_acc':winner['acc_mean'],'selection_nmi':winner['nmi_mean'],'confirmation':distances(endpoint,target),'confirmation_all50':{k:v for k,v in s.items() if k!='native_best'},'matched_sc':summarize(sc,range(first,first+50)),'trials':trials,'objects':{'predictions':store.put(pred),'matched_sc_predictions':store.put(scp)},'cpu_seconds':time.process_time()-t,'qualification':'New rounding seeds on the same fixed samples/G; no historical identity, generalization or label-free selection guarantee'}
            atomic_json(path,row);rows.append(row);status='COMPLETED'
        except BaseException as exc:
            # Failure provenance is cleanup, not another rounding attempt. It
            # must survive the timer that interrupted the fixed seed sequence.
            signal.setitimer(signal.ITIMER_PROF,0)
            status='TIMEOUT' if isinstance(exc,TimeoutError) else 'INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'FAILED'
            failure={'config_id':winner['config_id'],'candidate_id':winner['candidate_id'],
                'endpoint':winner['endpoint'],'status':status,'first_seed':first,'seeds':list(range(first,first+50)),
                'namespace_sha256':identity(namespace),'winner_lock_sha256':namespace['winner_lock_sha256'],
                'stage':stage,'exception_type':type(exc).__name__,'error':repr(exc),
                'failed_rounding_seed':getattr(exc,'failed_rounding_seed',None),
                'partial_trials':getattr(exc,'partial_trials',[]),'objects':{},
                'cpu_limit':120,'no_winner_or_seed_reselection':True,
                'qualification':'Failed fixed-winner confirmation attempt; partial outcomes are not a completed endpoint'}
            # A timeout can arrive just after atomic publication. This attempt
            # started without a completed path, so it owns any such new file.
            path.unlink(missing_ok=True)
            for name,values in [('completed_candidate_predictions',pred),('completed_matched_sc_predictions',scp),
                ('partial_predictions',getattr(exc,'partial_predictions',None))]:
                if values is not None:
                    try:failure['objects'][name]=store.put(values)
                    except Exception as artifact_error:failure.setdefault('partial_artifact_errors',{})[name]=repr(artifact_error)
            if trials is not None:failure['completed_candidate_trials']=trials
            if sc is not None:failure['completed_matched_sc_trials']=sc
            failure['cpu_seconds']=time.process_time()-t
            atomic_json(confirmation/'failures'/rid/('attempt-'+str(time.time_ns())+'.json'),failure)
            raise
        finally:
            signal.setitimer(signal.ITIMER_PROF,0)
            ledger.finish(rid,time.process_time()-t,status)
    write_csv(out/'rounding_confirmation.csv',rows)
