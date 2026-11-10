"""Authoritative trial aggregation, explicit coverage, and locked confirmation."""
from __future__ import annotations
import csv,gzip,json,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import yaml
from experiments.submission_refresh.core import ROOT,ArtifactStore,ResourceLedger,atomic_json,digest,identity
from experiments.submission_refresh.selection import distances,rank,summarize
from .runner import GAMMAS,INITS,round_embedding

def write_csv(path,rows,fields=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def aggregate(artifact_root,output):
    start=time.process_time();store=ArtifactStore(artifact_root);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    cat=json.loads((ROOT/'results/subset_search/candidate_catalogue.json').read_text());paper=yaml.safe_load((ROOT/'configs/v3/paper_reference.yaml').read_text());summaries=[];fixed=[];coverage=[];native=[];refs=[];sc_rows=[]
    trialfields=['candidate_id','config_id','method','initialization','variant','gamma_nominal','seed','acc','nmi','inertia','iterations','warning'];counts=Counter()
    with gzip.open(out/'trials.csv.gz','wt',newline='') as tf:
        writer=csv.DictWriter(tf,fieldnames=trialfields,extrasaction='ignore');writer.writeheader()
        for c in cat['candidates']:
            cid=c['candidate_id'];alias=c.get('alias_of');folder=Path(artifact_root)/'subset'/(alias or cid)
            records={}
            for scfile in sorted(folder.glob('SC__*.json')):
                sr=json.loads(scfile.read_text())
                if sr.get('status')!='COMPLETED':continue
                stats=summarize(sr['trials'])
                sc_rows.append({'candidate_id':cid,'benchmark':c['benchmark'],'pool':c['pool'],'initialization':sr['initialization'],'alias_of':alias,'n_samples':c['n'],'trials':sr['trials'],**stats,'same_embedding':'representation.json exact F; no independently regenerated SC'})
            for f in sorted(folder.glob('*.json')):
                if f.name in ['status.json','profile.json']:continue
                obj=json.loads(f.read_text());refs.append({'candidate_id':cid,'record':f.name,'object':store.put(obj)})
                if obj.get('method')=='ssc' and obj.get('status')=='COMPLETED':records[(obj['variant'],obj['gamma_nominal'],obj['initialization'])]=obj
            for variant in ['E8','E13']:
                for gamma in GAMMAS:
                    for init in INITS:
                        record=records.get((variant,gamma,init));status='COMPLETED_ALIAS' if record and alias else 'COMPLETED' if record else 'NOT_RUN'
                        if not record and (folder/'status.json').exists():
                            candidate_status=json.loads((folder/'status.json').read_text())['status']
                            state=json.loads((folder/'status.json').read_text())
                            active=state.get('active_configuration',{})
                            is_active=active.get('method')=='ssc' and active.get('variant')==variant and active.get('gamma_nominal')==gamma and (active.get('stage')=='solver' or active.get('initialization')==init)
                            if candidate_status=='COMPLETED':status='MISSING_RESULT'
                            elif candidate_status in ['TIMEOUT','FAILED']:
                                status=candidate_status if is_active else 'NOT_RUN_AFTER_CANDIDATE_'+candidate_status
                            else:status='NOT_RUN_CANDIDATE_'+candidate_status
                        coverage.append({'candidate_id':cid,'family':c['family'],'pool':c['pool'],'variant':variant,'gamma_nominal':gamma,'initialization':init,'status':status,'alias_of':alias});counts[status]+=1
                        if not record:continue
                        # Recompute from all50 rows; stored summaries cannot mask a
                        # missing, duplicated or invalid seed in authoritative data.
                        s=summarize(record['trials']);benchmark=c['benchmark'];target={m:paper[m]['ssc'][benchmark]['mean'] for m in ['acc','nmi']}
                        row={'candidate_id':cid,'config_id':cid+'|'+variant+'|'+str(gamma)+'|'+init,'benchmark':benchmark,'family':c['family'],'pool':c['pool'],'n_samples':c['n'],'n_classes':c['classes'],'prep':c['prep'],'variant':variant,'gamma_nominal':gamma,'gamma_effective':record['gamma_effective'],'initialization':init,'solver_status':record['solver']['status'],'endpoint':'mean_sample_sd_50','paper_deviations':int(c['pool']=='adapted')+int(c['prep'] in ['Y1','Y2'])+2*int(c['prep']=='Y3'),'preparation_assumptions':1,'alias_of':alias,'record_directory':str(Path('subset')/(alias or cid)),'record_file':f'{variant}__{gamma:g}__{init}.json',**{k:v for k,v in s.items() if k!='native_best'}}
                        row=distances(row,target);row.update(paper_acc=target['acc'],paper_nmi=target['nmi'],paper_acc_sd=paper['acc']['ssc'][benchmark]['sd'],paper_nmi_sd=paper['nmi']['ssc'][benchmark]['sd'],historical_identity='UNVERIFIED' if benchmark in ['AR','UMIST','BinAlpha','MSRA50'] else 'documented source; no pixel identity proof')
                        row['delta_acc_sd_pp']=row['acc_sd']-row['paper_acc_sd'];row['delta_nmi_sd_pp']=row['nmi_sd']-row['paper_nmi_sd']
                        summaries.append(row)
                        if variant=='E8' and gamma==1 and init=='RANDOM':fixed.append(row)
                        native.append(distances({**row,**s['native_best'],'n':1,'endpoint':'native_best_of_50'},target))
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
    write_csv(out/'matched_sc_summary.csv',sc_rows);write_csv(out/'execution_coverage.csv',coverage);write_csv(out/'joint_search_summary.csv',summaries);write_csv(out/'fixed_protocol_summary.csv',fixed);write_csv(out/'closest_matches.csv',winners);write_csv(out/'top_matches.csv',top)
    write_csv(out/'native_best_summary.csv',native)
    contrasts=[]
    for r in winners:
        sc=next((v for v in sc_rows if v['candidate_id']==r['candidate_id'] and v['initialization']==r['initialization']),None)
        if sc is None:continue
        endpoint=sc if r['endpoint']=='mean_sample_sd_50' else sc['native_best']
        contrasts.append({'config_id':r['config_id'],'candidate_id':r['candidate_id'],'benchmark':r['benchmark'],'pool':r['pool'],'endpoint':r['endpoint'],'ssc_acc':r['acc_mean'],'ssc_nmi':r['nmi_mean'],'sc_acc':endpoint['acc_mean'],'sc_nmi':endpoint['nmi_mean'],'delta_acc_pp':r['acc_mean']-endpoint['acc_mean'],'delta_nmi_pp':r['nmi_mean']-endpoint['nmi_mean'],'qualification':'Same selectedsamples/F/protocol. For nativeendpoint eachmethod independentlyselectsnativebestof50; no acrossmethodpairedsinglebestseed interpretation.'})
    write_csv(out/'matched_sc_contrasts.csv',contrasts)
    distributions=[]
    for b in sorted({r['benchmark'] for r in fixed}):
        rows=[r for r in fixed if r['benchmark']==b and not r['alias_of']]
        for metric in ['acc_mean','nmi_mean']:distributions.append({'benchmark':b,'metric':metric,'unique_candidates':len(rows),'median':float(np.median([r[metric] for r in rows])),'min':min(r[metric] for r in rows),'max':max(r[metric] for r in rows)})
    write_csv(out/'fixed_protocol_distribution.csv',distributions)
    family_distributions=[]
    for family in sorted({r['family'] for r in fixed}):
        allrows=[r for r in fixed if r['family']==family]
        for weighting in ['declared_candidates_with_aliases','unique_physical_inputs']:
            chosen=allrows
            if weighting=='unique_physical_inputs':
                unique={}
                for r in allrows:unique.setdefault(r['alias_of'] or r['candidate_id'],r)
                chosen=list(unique.values())
            for metric in ['acc_mean','nmi_mean']:
                family_distributions.append({'family':family,'benchmark':chosen[0]['benchmark'],'weighting':weighting,'declared_candidates':len(allrows),'observations':len(chosen),'metric':metric,'median':float(np.median([r[metric] for r in chosen])),'min':min(r[metric] for r in chosen),'max':max(r[metric] for r in chosen)})
    write_csv(out/'fixed_protocol_family_distributions.csv',family_distributions)
    reference_ids=yaml.safe_load((ROOT/'configs/subset_search/protocol.yaml').read_text())['reference_candidates']
    reference_contrasts=[]
    for benchmark,reference in reference_ids.items():
        baseline=next((r for r in fixed if r['candidate_id']==reference),None)
        reference_grid=[r for r in summaries if r['candidate_id']==reference]
        for pool in sorted({r['pool'] for r in summaries if r['benchmark']==benchmark and r['pool']!='diagnostic'}):
            pools=[('reference_candidate_reference_settings',[baseline] if baseline else []),
                   ('candidate_cohort_reference_settings',[r for r in fixed if r['benchmark']==benchmark and r['pool']==pool]),
                   ('reference_candidate_frozen_grid',reference_grid),
                   ('candidate_cohort_frozen_grid',[r for r in summaries if r['benchmark']==benchmark and r['pool']==pool])]
            for contrast,items in pools:
                if items:
                    chosen=rank(items)[0]
                    reference_contrasts.append({**chosen,'contrast':contrast,'target_pool':pool,'reference_candidate':reference,'reference_pool':baseline['pool'] if baseline else None,'eligible_configurations_in_contrast':len(items),'selection':'same joint minimax; descriptive retrospective comparison'})
                else:reference_contrasts.append({'benchmark':benchmark,'target_pool':pool,'reference_candidate':reference,'contrast':contrast,'status':'UNAVAILABLE_INCOMPLETE_REFERENCE'})
    write_csv(out/'reference_contrasts.csv',reference_contrasts)
    atomic_json(out/'winner_lock.json',{'version':1,'catalogue_sha256':digest(ROOT/'results/subset_search/candidate_catalogue.json'),'selection_rule_sha256':digest(ROOT/'configs/submission_refresh/selection.yaml'),'winners':winners,'no_reselection_after_confirmation':True})
    atomic_json(out/'artifact_manifest.json',{'store':'external independent-data/scientific-artifacts/refresh-20261110','object_format':'verified content-addressed npz/npy/json','records':refs,'regeneration':'python -m experiments.subset_search run --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume','source_catalogue_sha256':digest(ROOT/'results/subset_search/candidate_catalogue.json')})
    atomic_json(out/'coverage_summary.json',{'intended_candidates':len(cat['candidates']),'unique_catalogue_inputs':len({r.get('alias_of') or r['candidate_id'] for r in cat['candidates']}),'status_counts':dict(counts),'complete_unique_configurations':sum(r['alias_of'] is None for r in summaries),'complete_unique_candidates':len({r['candidate_id'] for r in summaries if not r['alias_of']}),'cpu_aggregation_seconds':time.process_time()-start})
    for b in paper['datasets']:
        rows=[r for r in winners if r['benchmark']==b]
        text=[f'# {b}: closest evaluated reconstructions','','Retrospective joint ACC/NMI matching within each endpoint and eligibility pool. Sample identity remains unverified. A single native-best result has no across-run SD.','','| Pool / endpoint | Candidate | ACC / paper | NMI / paper | Dmax / Dmean | Solver |','|---|---|---:|---:|---:|---|']
        for r in rows:
            text.append(f"| {r['pool']} / {r['endpoint']} | {r['candidate_id']} | {r['acc_mean']:.3f} / {r['paper_acc']:.1f} | {r['nmi_mean']:.3f} / {r['paper_nmi']:.1f} | {r['D_max']:.3f} / {r['D_mean']:.3f} | {r['solver_status']} |")
        (out/(b+'.md')).write_text('\n'.join(text)+'\n')
    return winners

def confirm(artifact_root,output):
    from threadpoolctl import threadpool_limits
    out=Path(output);lock=json.loads((out/'winner_lock.json').read_text());store=ArtifactStore(artifact_root);ledger=ResourceLedger(artifact_root);rows=[]
    # Verify namespace against committed historical raw seeds, not an assumption.
    import pandas as pd
    old=pd.read_csv(ROOT/'results/v3_reproduction/all_trials.csv.gz',usecols=['seed']);used=set(map(int,old.seed))
    first=1000000
    while any(i in used for i in range(first,first+50)):first+=50
    confirmation=Path(artifact_root)/'confirmation';confirmation.mkdir(exist_ok=True)
    for winner in lock['winners']:
        rid='confirm-'+identity(winner)[:20];path=confirmation/(rid+'.json')
        if path.exists():rows.append(json.loads(path.read_text()));continue
        if not ledger.reserve(rid,120,'confirmation'):rows.append({'config_id':winner['config_id'],'status':'NOT_RUN_BUDGET'});continue
        t=time.process_time()
        try:
            folder=Path(artifact_root)/winner['record_directory'];record=json.loads((folder/winner['record_file']).read_text());rep=json.loads((folder/'representation.json').read_text());G=store.get(record['objects']['G']);F=store.get(rep['objects']['F']);y=store.get(rep['objects']['y']);K=len(np.unique(y))
            with threadpool_limits(limits=1):
                trials,pred,centers=round_embedding(G,y,K,winner['initialization'],range(first,first+50));sc,scp,_=round_embedding(F,y,K,winner['initialization'],range(first,first+50))
            s=summarize(trials,range(first,first+50));endpoint=s if winner['endpoint']=='mean_sample_sd_50' else s['native_best'];target={'acc':winner['paper_acc'],'nmi':winner['paper_nmi']}
            row={'config_id':winner['config_id'],'candidate_id':winner['candidate_id'],'benchmark':winner['benchmark'],'pool':winner['pool'],'endpoint':winner['endpoint'],'status':'COMPLETED','first_seed':first,'selection_acc':winner['acc_mean'],'selection_nmi':winner['nmi_mean'],'confirmation':distances(endpoint,target),'confirmation_all50':{k:v for k,v in s.items() if k!='native_best'},'matched_sc':summarize(sc,range(first,first+50)),'trials':trials,'objects':{'predictions':store.put(pred),'matched_sc_predictions':store.put(scp)},'cpu_seconds':time.process_time()-t,'qualification':'New rounding seeds on the same fixed samples/G; no historical identity, generalization or label-free selection guarantee'}
            atomic_json(path,row);rows.append(row);ledger.finish(rid,time.process_time()-t,'COMPLETED')
        except BaseException:
            ledger.finish(rid,time.process_time()-t,'FAILED');raise
    write_csv(out/'rounding_confirmation.csv',rows);atomic_json(out/'confirmation_seed_namespace.json',{'first':first,'count':50,'historical_trial_file_sha256':digest(ROOT/'results/v3_reproduction/all_trials.csv.gz'),'overlap':False,'no_reselection':True})
