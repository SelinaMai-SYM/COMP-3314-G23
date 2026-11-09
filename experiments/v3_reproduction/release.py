"""Deterministic no-data reconstruction from the immutable scalar release.

Validates every input and complete seed set before touching an output directory.
The resulting tables distinguish retrospective display from controlled evidence.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import csv, gzip, hashlib, json, math, os, shutil, tempfile
import numpy as np
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[2]
GROUP=['dataset_id','method','prep','config_name','variant','initialization','report_role']
METHODS=['kmeans','sc','pca_kmeans','pca_sc','lda_kmeans','lda_sc','llc','spls','ssc']
BENCHMARKS=['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']
PAPER_METHOD={'pca_sc':'pca_spectral','lda_sc':'lda_spectral'}
PRIMARY={'ORL':'ORL_att92','JAFFE':'JAFFE','YaleB':'YaleB_cropped2414','USPS':'USPS'}


def sha(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(1<<20):d.update(b)
    return d.hexdigest()


def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def _key(row):return tuple(str(row[k]) for k in GROUP)
def _id(key):return '|'.join(key)
def _clean(value):
    if isinstance(value,dict):return {str(k):_clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_clean(v) for v in value]
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,np.floating):value=float(value)
    if isinstance(value,float) and not math.isfinite(value):return None
    return value


def _write_csv(path,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:(_json(_clean(v)) if isinstance(v,(dict,list,tuple)) else _clean(v)) for k,v in r.items()})


def _format(row,metric='ACC'):
    if row.get('measured_'+metric) is None:return row['execution_status']
    return f"{row['measured_'+metric]:.3f} ± {row['measured_'+metric+'_SD']:.3f}"


def _table(title,rows):
    text=[f'# {title}','','All scores are percent. Reported in Chang et al. (2015) and Our reproduction/adapted setting are distinct. Closest means post-hoc display selection, not unsupervised tuning.','','| Benchmark | Method | Dataset | Paper ACC | Our ACC mean ± sample SD | NMI | Status / setting / solver |','|---|---|---|---:|---|---|---|']
    for r in rows:
        paper='' if r.get('paper_ACC') is None else f"{r['paper_ACC']:.1f}"
        note='; '.join([r['execution_status'],*r.get('setting_deviations',[]),r.get('solver_status_current_audit','')]).replace('|','/')
        text.append(f"| {r['benchmark']} | {r['method']} | {r.get('dataset_version','')} | {paper} | {_format(r)} | {_format(r,'NMI')} | {note} |")
    return '\n'.join(text)+'\n'


def _deviations(row,params):
    deviations=[];dataset=row['dataset_id'];method=row['method'];prep=row['prep']
    if dataset=='YaleB_dengcai32':deviations.append('alternate_dataset_version')
    if prep in ['Y1','Y3']:deviations.append('input_l2_normalization')
    if prep in ['Y2','Y3']:deviations.append('embedding_row_normalization')
    if row['variant']=='E13':deviations.append('printed_E13_gamma_half')
    if method=='ssc' and float(params.get('ssc_gamma',1))!=1:deviations.append('gamma_not_fixed_one')
    refinit={'lda_kmeans':'FULL_REFIT','llc':'YU_SHI'}.get(method,'RANDOM')
    if row['initialization']!=refinit:deviations.append('initialization_not_fixed_reference')
    if params.get('n_init',1)!=1:deviations.append('n_init_not_one')
    if method=='ssc' and params.get('max_iter',300)!=300:deviations.append('iteration_budget_not_300')
    return deviations


def _solver(meta,method):
    if method!='ssc':return 'NOT_APPLICABLE'
    original=meta.get('solver_status','UNKNOWN')
    return {'CONVERGED_BY_ITERATE_CRITERION':'ITERATE_CONVERGED_UNCERTIFIED','OPTIMALITY_VERIFIED':'LEGACY_VERIFIED_NOT_DUAL_CERTIFIED'}.get(original,original)


def load_release(manifest_path):
    path=Path(manifest_path).resolve();manifest=json.loads(path.read_text())
    # Paths belong to the release checkout, independent of CWD and Git history.
    root=path.parents[2]
    required=['trial_file','metadata_file','configuration_file','coverage_file','paper_file','selection_file','counts','files']
    if any(k not in manifest for k in required):raise ValueError('release manifest missing fields')
    for field in required[:6]:
        if manifest[field] not in manifest['files']:raise ValueError('required release input not covered by hashes: '+field)
    for name,info in manifest['files'].items():
        p=(root/name).resolve()
        if root not in p.parents or not p.is_file() or sha(p)!=info['sha256']:raise ValueError(f'release hash mismatch: {name}')
    trial=root/manifest['trial_file'];d=hashlib.sha256()
    with gzip.open(trial,'rb') as f:
        while b:=f.read(1<<20):d.update(b)
    if d.hexdigest()!=manifest['trial_sha256_uncompressed']:raise ValueError('uncompressed trial hash mismatch')
    df=pd.read_csv(trial,dtype=str,keep_default_na=False)
    needed=GROUP+['batch','seed','acc','nmi','code_commit','labels_sha256','counts_as_historical','historical_benchmark']
    if any(k not in df for k in needed) or df.empty:raise ValueError('empty/missing trial fields')
    for k in ['batch','seed']:
        raw=pd.to_numeric(df[k],errors='raise')
        if (raw<0).any() or (raw!=raw.astype(int)).any():raise ValueError(f'invalid {k}')
        df[k]=raw.astype(int)
    for k in ['acc','nmi']:
        df[k]=pd.to_numeric(df[k],errors='raise')
        if not np.isfinite(df[k]).all() or ((df[k]<0)|(df[k]>1)).any():raise ValueError(f'invalid {k}')
    if df.duplicated(GROUP+['batch','seed']).any():raise ValueError('duplicate trial primary key')
    if len(df)!=manifest['counts']['trials']:raise ValueError('trial count mismatch')
    with gzip.open(root/manifest['metadata_file'],'rt') as f:jobs=[json.loads(s) for s in f if s.strip()]
    if len(jobs)!=manifest['counts']['jobs'] or len({j['metadata_id'] for j in jobs})!=len(jobs):raise ValueError('metadata job count/identity mismatch')
    owner={};expected={}
    for job in jobs:
        for group in job['groups']:
            key=tuple(group['key']);b=int(group['batch']);seeds=group['seeds']
            if len(seeds)!=len(set(seeds)):raise ValueError('duplicate expected seeds')
            if (key,b) in expected:raise ValueError('duplicate metadata group')
            expected[(key,b)]=seeds;owner[key]=job
    actual={}
    for key,block in df.groupby(GROUP+['batch'],sort=True):actual[(tuple(key[:-1]),int(key[-1]))]=sorted(block.seed.tolist())
    if actual!=expected:raise ValueError('missing/unexpected trial groups or seeds')
    # The historical package's planned endpoint is 50 contiguous seeds per batch.
    for (key,b),seeds in actual.items():
        if seeds!=list(range(50*b,50*b+50)):raise ValueError(f'incomplete planned seed set: {key}, batch {b}')
    if len(owner)!=manifest['counts']['configurations']:raise ValueError('configuration count mismatch')
    historical=pd.read_csv(root/manifest['configuration_file'],dtype=str,keep_default_na=False)
    if len(historical)!=len(owner) or set(map(tuple,historical[GROUP].values))!=set(owner):raise ValueError('configuration source mapping mismatch')
    return root,manifest,df,jobs,owner


def rebuild(manifest_path,output):
    root,manifest,df,jobs,owner=load_release(manifest_path)
    paper=yaml.safe_load((root/manifest['paper_file']).read_text());rule=yaml.safe_load((root/manifest['selection_file']).read_text())
    coverage=list(csv.DictReader((root/manifest['coverage_file']).open()))
    if len(coverage)!=72 or len({(r['benchmark'],r['method']) for r in coverage})!=72:raise ValueError('invalid 72-cell registry')
    configs=[];batches=[];exclusions=[]
    for key,block in df.groupby(GROUP,sort=True):
        job=owner[key];meta=job['metadata'];params=meta.get('effective_config',{});row=dict(zip(GROUP,key));row['historical_benchmark']=block.iloc[0]['historical_benchmark'];method=row['method'];benchmark=row['historical_benchmark']
        bybatch=[]
        for b,group in block.groupby('batch',sort=True):
            summary={'config_id':_id(key),'batch':int(b),'n_trials':len(group),'ACC':float(group.acc.mean()*100),'ACC_SD':float(group.acc.std(ddof=1)*100),'NMI':float(group.nmi.mean()*100),'NMI_SD':float(group.nmi.std(ddof=1)*100),'seed_list':group.seed.tolist()}
            selected=group[group.selection_value!=''] if 'selection_value' in group else group.iloc[0:0]
            if len(selected) and group.iloc[0]['selection_rule'] in ['min_inertia','min_procrustes']:
                selected=selected.assign(_value=pd.to_numeric(selected.selection_value)).sort_values(['_value','seed']).iloc[0]
                summary.update(selected_ACC=float(selected.acc*100),selected_NMI=float(selected.nmi*100),selected_seed=int(selected.seed))
            bybatch.append(summary);batches.append(summary)
        first=next((b for b in bybatch if b['batch']==0),None)
        if first is None:exclusions.append({'config_id':_id(key),'reason':'INCOMPLETE_BATCH0'});continue
        declared=params.get('max_iter');checkpoint=meta.get('checkpoint_300') or {};continuation=meta.get('continuation') or {};history=meta.get('history_summary') or {}
        total_budget=declared;executed=history.get('count')
        if meta.get('continued_after_checkpoint') or continuation or meta.get('continuation_extra_iter'):
            extra=meta.get('continuation_extra_iter',continuation.get('extra_iter',700))
            total_budget=(declared or 300)+extra;executed=(checkpoint.get('n_iterations') or 0)+(history.get('count') or 0)
        effective_params={**params,'max_iter':total_budget}
        dev=_deviations(row,effective_params);gamma=params.get('ssc_gamma');solver=_solver(meta,method)
        source=meta.get('code_commit','');snapshot=root/'archive/source'/source/'SOURCE_MANIFEST.json'
        records=block[block.batch==0].sort_values('seed').to_dict('records');trial_hash=hashlib.sha256(_json(records).encode()).hexdigest()
        status='TRUNCATED_EXECUTION' if method=='ssc' and meta.get('solver_status')=='MAX_ITER_REACHED' else meta.get('status','LEGACY_METADATA_INCOMPLETE')
        base={**row,'benchmark':benchmark,'dataset_version':row['dataset_id'],'subset_status':'historical_reconstruction' if block.iloc[0]['counts_as_historical']=='True' else 'SUBSET_UNVERIFIED_SUPPLEMENTAL','config_id':_id(key),'all_effective_parameters':({**effective_params,'declared_max_iter':declared} if method=='ssc' else params),'initialization_exact_name':row['initialization'],'n_init':None if method=='llc' else params.get('n_init',1),'kmeans_seed_list':first['seed_list'],'batch_count':len(bybatch),'n_trials':first['n_trials'],'paper_ACC':paper.get('acc',{}).get(PAPER_METHOD.get(method,method),{}).get(benchmark,{}).get('mean'),'paper_ACC_SD':paper.get('acc',{}).get(PAPER_METHOD.get(method,method),{}).get(benchmark,{}).get('sd'),'paper_NMI':paper.get('nmi',{}).get(PAPER_METHOD.get(method,method),{}).get(benchmark,{}).get('mean'),'paper_NMI_SD':paper.get('nmi',{}).get(PAPER_METHOD.get(method,method),{}).get(benchmark,{}).get('sd'),'measured_ACC':first['ACC'],'measured_ACC_SD':first['ACC_SD'],'measured_NMI':first['NMI'],'measured_NMI_SD':first['NMI_SD'],'execution_status':status,'solver_status_original':meta.get('solver_status','NOT_APPLICABLE'),'solver_status_current_audit':solver,'max_iter':total_budget,'iterations':executed,'declared_max_iter':declared,'continuation_metadata':continuation,'continued_from_checkpoint':bool(meta.get('continued_after_checkpoint')),'objective_target':'E8(gamma_effective)' if method=='ssc' else method,'gamma_nominal':gamma,'gamma_effective':float(gamma)/(2 if row['variant']=='E13' else 1) if gamma is not None else None,'setting_deviations':dev,'selection_rule_version':rule['version'],'source_commit':source,'source_file_hashes':{'scientific_snapshot_manifest':sha(snapshot)} if snapshot.exists() else {'status':'LEGACY_METADATA_INCOMPLETE'},'dataset_hash':hashlib.sha256(_json(meta.get('fingerprint',{})).encode()).hexdigest(),'feature_hash':meta.get('fingerprint',{}).get('x_sha256'),'label_hash':meta.get('fingerprint',{}).get('y_sha256'),'embedding_hash':'LEGACY_EMBEDDING_NOT_SAVED','trial_file':manifest['trial_file'],'trial_hash':trial_hash,'trial_hash_definition':'sha256(canonical sorted batch0 CSV records as JSON)','metadata_record':job['metadata_id'],'metadata_record_hash':job['original_metadata_sha256'],'reproducible_command':'python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output results/rebuilt','batch0_selected_statistic':{k:v for k,v in first.items() if k.startswith('selected_')},'repeatability_selected_ACC_mean':float(np.mean([b['selected_ACC'] for b in bybatch if 'selected_ACC' in b])) if any('selected_ACC'in b for b in bybatch) else None,'repeatability_selected_ACC_SD':float(np.std([b['selected_ACC'] for b in bybatch if 'selected_ACC'in b],ddof=1)) if sum('selected_ACC'in b for b in bybatch)>1 else None}
        base['delta_pp']=base['measured_ACC']-base['paper_ACC'] if base['paper_ACC'] is not None else None
        base['selection_distance']=abs(base['delta_pp']) if base['delta_pp'] is not None else None
        if meta.get('status')!='COMPLETED' or method not in METHODS or any(meta.get(field) in ['PRE_FIX_LEGACY','INVALID_CACHE','SAMPLE_MISMATCH','UNTRACEABLE'] for field in ['status','validity_status','source_status']):
            exclusions.append({'config_id':base['config_id'],'reason':'INVALID_OR_LEGACY_OR_NONBASELINE'});continue
        configs.append(base)
    selected=[];supplemental=[]
    ranks=rule['solver_evidence_rank']
    def choose(pool):
        best=min(r['selection_distance'] for r in pool)
        tied=[r for r in pool if r['selection_distance']-best<=float(rule['tie_absolute_tolerance'])]
        return min(tied,key=lambda r:(ranks.get(r['solver_status_current_audit'],4),len(r['setting_deviations']),r['config_id']))
    reconstructed=[]
    for cell in coverage:
        benchmark,method=cell['benchmark'],cell['method'];pool=[r for r in configs if r['benchmark']==benchmark and r['method']==method and r['subset_status']=='historical_reconstruction']
        status=cell['execution_status']
        if status=='COMPLETED' and not pool:raise ValueError(f'completed cell has no configurations: {benchmark}/{method}')
        reconstructed.append({'benchmark':benchmark,'method':method,'execution_status':status,'reason':cell['reason'],'n_completed_configurations':len(pool)})
        for track in ['closest_to_paper','fixed_protocol_reference']:
            usable=pool
            if track=='fixed_protocol_reference':
                usable=[r for r in pool if r['dataset_id']==PRIMARY.get(benchmark) and r['prep']=='Y0' and r['report_role']=='reference']
                init={'lda_kmeans':'FULL_REFIT','llc':'YU_SHI'}.get(method,'RANDOM');usable=[r for r in usable if r['initialization']==init]
                if method=='ssc':usable=[r for r in usable if r['variant']=='E8' and r['gamma_nominal']==1]
                if method=='llc':usable=[r for r in usable if r['all_effective_parameters'].get('llc_ridge')==1 and r['all_effective_parameters'].get('bandwidth_multiplier')==1]
                if method in rule['fixed_reference']['no_unique_reference']:usable=[]
                if len(usable)>1:raise ValueError('ambiguous locked reference; do not silently choose')
            if usable and status=='COMPLETED':
                r=dict(choose(usable) if track=='closest_to_paper' else usable[0]);r['track']=track
            else:
                pmethod=PAPER_METHOD.get(method,method)
                r={'benchmark':benchmark,'method':method,'dataset_version':PRIMARY.get(benchmark,''),'track':track,'config_id':None,'execution_status':status if status!='COMPLETED' else 'GRID_NOT_COLLAPSED','paper_ACC':paper['acc'][pmethod][benchmark]['mean'],'paper_NMI':paper['nmi'][pmethod][benchmark]['mean'],'measured_ACC':None,'measured_NMI':None,'setting_deviations':[],'reason':cell['reason'] if status!='COMPLETED' else 'No unique locked configuration; full measured grid is in configuration_table.csv','selection_rule_version':rule['version']}
            r['result_hash']=hashlib.sha256(_json(_clean(r)).encode()).hexdigest();selected.append(r)
    for dataset in rule['supplemental_only']+['YaleB_dengcai32']:
        for method in METHODS:
            pool=[r for r in configs if r['dataset_id']==dataset and r['method']==method]
            if pool:r=dict(choose(pool));r['track']='supplemental_closest_display';supplemental.append(r)
    counts=dict(Counter(r['execution_status'] for r in reconstructed))
    if counts!=manifest['coverage_counts']:raise ValueError('reconstructed coverage counts disagree')
    output=Path(output).resolve()
    if output==root or root in output.parents and output in [root/'results',root/'report']:raise ValueError('unsafe output directory')
    if output.exists() and any(output.iterdir()):
        marker=output/'validation.json'
        try: previous_validation=json.loads(marker.read_text())
        except (OSError,ValueError):raise ValueError('refusing to replace unknown nonempty output directory')
        if previous_validation.get('ok') is not True or previous_validation.get('metadata_scope')!='scalar trials and effective configurations; historical representation arrays not published':raise ValueError('refusing to replace unknown nonempty output directory')
    output.parent.mkdir(parents=True,exist_ok=True);temporary=Path(tempfile.mkdtemp(prefix='.rebuild-',dir=output.parent))
    try:
        _write_csv(temporary/'selection_manifest.csv',selected)
        with (temporary/'selection_manifest.jsonl').open('w') as f:
            for r in selected:f.write(_json(_clean(r))+'\n')
        _write_csv(temporary/'configuration_table.csv',configs);_write_csv(temporary/'batch_repeatability.csv',batches);_write_csv(temporary/'coverage_72_cells.csv',reconstructed);_write_csv(temporary/'supplemental.csv',supplemental);_write_csv(temporary/'invalid_or_legacy.csv',exclusions or [{'config_id':'','reason':'No invalid baseline rows beyond explicitly excluded matched-F diagnostics'}])
        for track in ['closest_to_paper','fixed_protocol_reference']:
            rows=[r for r in selected if r['track']==track];_write_csv(temporary/(track+'.csv'),rows);(temporary/(track+'.md')).write_text(_table(track,rows))
        folder=temporary/'per_benchmark';folder.mkdir()
        for benchmark in BENCHMARKS:(folder/(benchmark+'.md')).write_text(_table(benchmark,[r for r in selected if r['benchmark']==benchmark]))
        (temporary/'supplemental.md').write_text(_table('Supplemental versions - not historical subset reproduction',supplemental))
        latex=['% Generated from selection_manifest.jsonl; values are percentages.','\\begin{table}[t]','\\centering\\small','\\caption{Reported in Chang et al. (2015) versus our reproduction/adapted setting. Closest rows use post-hoc ACC matching; fixed rows use Y0/E8/gamma=1/random.}','\\label{tab:main}','\\begin{tabular}{llrrl}','\\toprule Dataset & Method & Paper & Closest observed & Setting \\\\','\\midrule']
        for benchmark in ['ORL','JAFFE','YaleB','USPS']:
            for method in ['sc','ssc']:
                r=next(x for x in selected if x['benchmark']==benchmark and x['method']==method and x['track']=='closest_to_paper')
                val=f"{r['measured_ACC']:.2f} $\\pm$ {r['measured_ACC_SD']:.2f}"
                mark='T' if r['execution_status']=='TRUNCATED_EXECUTION' else 'I' if method=='ssc' else '--'
                latex.append(f"{benchmark} & {method.upper()} & {r['paper_ACC']:.1f} & {val} & {r['prep']}/{r['variant'] or 'SC'}/{mark} \\\\")
        latex+=['\\bottomrule','\\end{tabular}','\\end{table}'];(temporary/'report_main.tex').write_text('\n'.join(latex)+'\n')
        validation={'ok':True,**manifest['counts'],'coverage':counts,'metadata_scope':'scalar trials and effective configurations; historical representation arrays not published','selection_rule':rule['version'],'uncompressed_trials_sha256':manifest['trial_sha256_uncompressed']}
        (temporary/'validation.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
        (temporary/'output_hashes.json').write_text(json.dumps({str(p.relative_to(temporary)):sha(p) for p in sorted(temporary.rglob('*')) if p.is_file()},indent=2,sort_keys=True)+'\n')
        if output.exists():
            previous=output.with_name(output.name+'.previous')
            if previous.exists():raise ValueError('previous output backup exists; refusing replacement')
            output.rename(previous)
            try:temporary.rename(output)
            except BaseException:previous.rename(output);raise
            shutil.rmtree(previous)
        else:temporary.rename(output)
        return validation
    finally:
        if temporary.exists():shutil.rmtree(temporary)
