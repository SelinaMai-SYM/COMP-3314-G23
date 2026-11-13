"""Atomic English benchmark views from authoritative, qualified display rows."""
from pathlib import Path
import csv
import json
import shutil
import tempfile
import yaml
from .core import ROOT,atomic_json,digest
from .scalar_evidence import PAPER_METHOD
from .csv_transport import resolve_csv,open_csv
from .reporting import public_presentation_inputs

NAMES=['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']
INPUTS=[('results/submission_refresh/joint_metric_selection.csv',None),
        ('results/submission_refresh/endpoint_comparison.csv','native_best_of_50'),
        ('results/submission_refresh/expanded_baseline_selection.csv',None),
        ('results/submission_refresh/expanded_baseline_native_selection.csv',None),
        ('results/submission_refresh/baseline_source_native_diagnostics.csv',None),
        ('results/subset_search/closest_matches.csv',None)]


def first(row,*keys,default=None):
    return next((row[key] for key in keys if row.get(key) not in [None,'']),default)


def cell(value):
    """Keep stable IDs containing pipes inside one Markdown table cell."""
    return str(value).replace('\\','\\\\').replace('|','\\|').replace('\r',' ').replace('\n',' ')


def single(row):
    return first(row,'endpoint',default='') in ['native_best_of_50','source_native_selection_diagnostic']


def metric(row,name):
    value=first(row,name+'_mean','measured_'+name.upper())
    if value is None:return first(row,'status','execution_status',default='UNAVAILABLE')
    score=f'{float(value):.3f}'
    if single(row):return score+' (single assignment)'
    sd=first(row,name+'_sd','measured_'+name.upper()+'_SD')
    return score+(f' +/- {float(sd):.3f}' if sd is not None else ' (SD unavailable)')


def pair(row,prefix,suffix='',signed=False):
    values=[]
    for name in ['acc','nmi']:
        value=first(row,prefix+name+suffix)
        values.append(('--' if value is None else format(float(value),'+.3f' if signed else '.3f')))
    return ' / '.join(values)


METHOD_LABELS={'kmeans':'K-means','sc':'SC','pca_kmeans':'PCA–K-means','pca_spectral':'PCA–SC','pca_sc':'PCA–SC',
    'lda_kmeans':'LDA–K-means','lda_spectral':'LDA–SC','lda_sc':'LDA–SC','llc':'LLC','spls':'SLPS','ssc':'SSC',
    'lda_existing':'LDA–K-means (existing)','lda_reference':'LDA–K-means (pinned ClustPy)',
    'lda_adapted':'Ridge LDA–K-means','lda_adapted_sc':'Ridge LDA–SC','raw_sc':'Raw SC',
    'pca_p0_sc':'PCA-p0–SC','pca_r_sc':'PCA-r–SC'}


def public_setting(row):
    """Expose scientific settings without serializing internal record dictionaries."""
    source=first(row,'source_version','dataset_version','dataset',default='Source not identified')
    parts=[str(source)]
    for key,label in [('n_samples','n'),('n_features','features'),('source_kind','source kind'),('configuration_source_kind','source kind'),('native_resolution','native resolution'),
                      ('resolution','resolution'),('prep','normalization'),('variant','target'),
                      ('gamma_nominal','gamma'),('gamma_effective','effective gamma'),('initialization','initialization'),('max_iter','iteration limit')]:
        if row.get(key) not in [None,'']:parts.append(label+' '+str(row[key]))
    parameters=row.get('parameters')
    if isinstance(parameters,str):
        try:parameters=json.loads(parameters)
        except ValueError:parameters=None
    if isinstance(parameters,dict):
        for key in ['k','n_neighbors','alpha','dimension','n_components','dim','tau','ridge','inner_n_init']:
            if parameters.get(key) not in [None,'']:parts.append(key.replace('_',' ')+' '+str(parameters[key]))
    return '; '.join(parts)


def public_qualification(row,pool,endpoint):
    qualifications=[]
    if row.get('candidate_id') or pool in ['specification_compatible','adapted']:
        qualifications.append('Retrospective joint ACC/NMI match; historical membership unverified')
    elif pool=='historical_scalar':qualifications.append('Retrospective joint historical selection')
    if pool=='adapted':qualifications.append('Adapted source or method; not an equivalent historical reconstruction')
    if endpoint=='source_native_selection_diagnostic':qualifications.append('Source-native diagnostic; cross-subspace objectives are not comparable')
    elif endpoint=='native_best_of_50':qualifications.append('One native-objective-selected assignment; no across-run SD')
    elif first(row,'acc_mean','measured_ACC') is not None and first(row,'nmi_mean','measured_NMI') is not None:
        qualifications.append('Mean and sample SD from one complete seed set')
    else:qualifications.append('No complete measured endpoint')
    status=str(first(row,'status','execution_status',default=''))
    if status and status!='COMPLETED':qualifications.append(status.replace('_',' ').capitalize())
    solver=str(first(row,'solver_status','solver_status_current_audit',default=''))
    if solver and solver!='NOT_APPLICABLE':qualifications.append('Solver: '+solver.replace('_',' ').lower())
    identity=str(row.get('historical_identity') or '')
    if identity:qualifications.append('Identity: '+identity.replace('_',' ').lower())
    if pool=='historical_scalar' and row.get('method')=='ssc':
        qualifications.append('Historical G unavailable; separate current certificates do not certify this output')
    if str(first(row,'method',default='')).startswith('lda_adapted'):
        qualifications.append('PCA-preconditioned ridge adaptation; historical LDA-SC identity unresolved')
    if 'MSRA25_EBSA' in public_setting(row) or 'EBSA_16' in public_setting(row):
        qualifications.append('Native 16×16 source; paper 32×32 source unresolved')
    if 'dense' in str(row.get('qualification','')).lower():
        qualifications.append('Dense eigensolver; original sparse ARPACK attempt unsuccessful')
    diagnostics=row.get('diagnostic_summary')
    if isinstance(diagnostics,str):
        try:diagnostics=json.loads(diagnostics)
        except ValueError:diagnostics=None
    if isinstance(diagnostics,dict):
        for key,label in [('update_failures','failed LDA updates'),('runs_with_no_successful_LDA_update','fits with no successful LDA update'),('returned_state_inconsistent_runs','inconsistent returned states')]:
            if diagnostics.get(key) is not None:qualifications.append(str(diagnostics[key])+' '+label)
    return '; '.join(qualifications)


def public_view(name,rows,paper):
    text=[f'# {name}: clustering results','',
        'ACC/NMI and sample SD are percentages; signed differences and joint discrepancies are percentage points. Each pair of metrics uses one configuration and seed set. Joint matches are retrospective, using labels and paper targets; numerical closeness does not establish historical source or sample identity. Native-best endpoints contain one assignment and have no across-run SD. Compatible, adapted and diagnostic results remain separate.','',
        '| Method / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |',
        '|---|---|---:|---:|---:|---:|---|']
    for record in rows:
        if record.get('benchmark')!=name:continue
        row=dict(record);endpoint=first(row,'endpoint',default='mean_sample_sd_50')
        status=first(row,'status','execution_status',default='')
        if single(row) and str(status).startswith('UNAVAILABLE'):
            for key in ['acc_mean','nmi_mean','measured_ACC','measured_NMI','D_max','D_mean','delta_acc_pp','delta_nmi_pp','delta_acc_sd_pp','delta_nmi_sd_pp']:row.pop(key,None)
        pool=first(row,'pool',default='historical_scalar' if 'joint_metric_selection' in row['table_source'] or row['table_source'].endswith('/endpoint_comparison.csv') else 'implementation_audit')
        method='ssc' if row.get('candidate_id') else PAPER_METHOD.get(row.get('method'),row.get('method'))
        method={'pca_sc':'pca_spectral','lda_sc':'lda_spectral'}.get(method,method)
        reported=[]
        for m in ['acc','nmi']:
            mean=first(row,'paper_'+m,'paper_'+m.upper());sd=first(row,'paper_'+m+'_sd','paper_'+m.upper()+'_SD')
            if mean is None and method in paper['acc']:
                mean=paper[m][method][name]['mean'];sd=paper[m][method][name]['sd']
            reported.append('--' if mean is None else f'{float(mean):.3f}'+(f' ± {float(sd):.3f}' if sd is not None else ' (SD unavailable)'))
        maximum=first(row,'D_max');average=first(row,'D_mean')
        distance='--' if maximum is None or average is None else f'{float(maximum):.3f} / {float(average):.3f}'
        sd_delta='-- / --' if single(row) else pair(row,'delta_','_sd_pp',True)
        endpoint_label={'mean_sample_sd_50':'mean ± sample SD (50 seeds)','native_best_of_50':'native best of 50','source_native_selection_diagnostic':'source-native diagnostic'}.get(endpoint,endpoint.replace('_',' '))
        values=[METHOD_LABELS.get(row.get('method'),METHOD_LABELS.get(method,str(method)))+' / '+endpoint_label,
                public_setting(row),' / '.join(reported),metric(row,'acc').replace('+/-','±')+' / '+metric(row,'nmi').replace('+/-','±'),
                pair(row,'delta_','_pp',True)+'; '+sd_delta,distance,public_qualification(row,pool,endpoint)]
        text.append('| '+' | '.join(map(cell,values))+' |')
    text+=['','Configuration identities, exact source/sample hashes and complete trial records are retained in the public registry and CSV releases. Coverage distinguishes complete, unsuccessful and unevaluated configurations. `table_inputs.json` records the exact source-file hashes.']
    return '\n'.join(text)+'\n'


def build(root=ROOT):
    root=Path(root).resolve();out=root/'results/submission_refresh/per_benchmark'
    paper_path=root/'configs/v3/paper_reference.yaml';hashes={str(paper_path.relative_to(root)):digest(paper_path)};paper=yaml.safe_load(paper_path.read_text())
    presentation_inputs=public_presentation_inputs(root)
    public=bool(presentation_inputs)
    for path in presentation_inputs.values():hashes[str(path.relative_to(root))]=digest(path)
    paths=[];rows=[]
    for relative,endpoint in INPUTS:
        path=resolve_csv(root/relative)
        if path is None:continue
        paths.append(path);hashes[str(path.relative_to(root))]=digest(path)
        with open_csv(path,newline='') as stream:
            for record in csv.DictReader(stream):
                if endpoint and record.get('endpoint')!=endpoint:continue
                record['table_source']=relative;rows.append(record)
    if out.exists() and (not out.is_dir() or any(path.name not in {name+'.md' for name in NAMES}|{'table_inputs.json'} for path in out.iterdir())):
        raise ValueError('refusing to replace unknown benchmark-table files')
    out.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.benchmark-tables-',dir=out.parent))
    try:
        for name in NAMES:
            if public:
                (stage/(name+'.md')).write_text(public_view(name,rows,paper))
                continue
            text=[f'# {name}: authoritative reproduction and audit views','',
                'All scores and SDs are percentages; differences are percentage points. Joint matching is retrospective and label/paper-assisted. A count-compatible candidate does not establish historical identity. Single native-best assignments have no across-run SD. Source-native learned-subspace selection is diagnostic only and excluded from primary selection. Different implementation/source pools stay separate.','',
                '| Track / endpoint | Method or candidate | Paper ACC / NMI (mean +/- SD) | Our ACC | Our NMI | Dmax / Dmean (pp) | Delta ACC / NMI (pp) | Delta SD ACC / NMI (pp) | Source, settings and status |',
                '|---|---|---:|---:|---:|---:|---:|---:|---|']
            for record in rows:
                if record.get('benchmark')!=name:continue
                row=dict(record);endpoint=first(row,'endpoint',default='mean_sample_sd_50')
                # Unavailable native endpoints must not inherit their mean row's scores.
                status=first(row,'status','execution_status',default='')
                if single(row) and str(status).startswith('UNAVAILABLE'):
                    for key in ['acc_mean','nmi_mean','measured_ACC','measured_NMI','D_max','D_mean','delta_acc_pp','delta_nmi_pp','delta_acc_sd_pp','delta_nmi_sd_pp']:row.pop(key,None)
                pool=first(row,'pool',default='historical_scalar' if 'joint_metric_selection' in row['table_source'] or row['table_source'].endswith('/endpoint_comparison.csv') else 'implementation_audit')
                label=first(row,'candidate_id','method',default='--')
                method='ssc' if row.get('candidate_id') else PAPER_METHOD.get(row.get('method'),row.get('method'))
                method={'pca_sc':'pca_spectral','lda_sc':'lda_spectral'}.get(method,method)
                reported=[]
                for m in ['acc','nmi']:
                    mean=first(row,'paper_'+m,'paper_'+m.upper());sd=first(row,'paper_'+m+'_sd','paper_'+m.upper()+'_SD')
                    if mean is None and method in paper['acc']:
                        mean=paper[m][method][name]['mean'];sd=paper[m][method][name]['sd']
                    reported.append('--' if mean is None else f'{float(mean):.3f}'+(f' +/- {float(sd):.3f}' if sd is not None else ' (SD unavailable)'))
                maximum=first(row,'D_max');average=first(row,'D_mean')
                distance='--' if maximum is None or average is None else f'{float(maximum):.3f} / {float(average):.3f}'
                solver=first(row,'solver_status','solver_status_current_audit',default='')
                keys=['dataset','dataset_version','n_samples','prep','variant','gamma_nominal','gamma_effective','initialization','max_iter','parameters','config_id','historical_identity','qualification','diagnostic_summary','variability_scope','setting_deviations','native_best_status','objective_comparability','native_objective_field','native_objective','selected_seed']
                setting='; '.join(key+'='+str(row[key]) for key in keys if row.get(key) not in [None,''])
                qualification='; '.join(part for part in [setting,'status='+str(status) if status else '', 'solver='+str(solver) if solver else '',row['table_source']] if part)
                sd_delta='-- / --' if single(row) else pair(row,'delta_','_sd_pp',True)
                values=[str(pool)+' / '+str(endpoint),label,' / '.join(reported),metric(row,'acc'),metric(row,'nmi'),distance,pair(row,'delta_','_pp',True),sd_delta,qualification]
                text.append('| '+' | '.join(map(cell,values))+' |')
            text+=['','Complete per-configuration and per-seed failed and unrun work is recorded in the coverage tables. Input paths and hashes are in table_inputs.json; no scores in this table are hand copied.']
            (stage/(name+'.md')).write_text('\n'.join(text)+'\n')
        if any(digest(root/relative)!=sha for relative,sha in hashes.items()):raise ValueError('benchmark table inputs changed during generation')
        atomic_json(stage/'table_inputs.json',hashes)
        if out.exists():
            previous=out.with_name(out.name+'.previous')
            if previous.exists():raise ValueError('benchmark table backup already exists')
            out.rename(previous)
            try:stage.rename(out)
            except BaseException:previous.rename(out);raise
            shutil.rmtree(previous)
        else:stage.rename(out)
    finally:
        if stage.exists():shutil.rmtree(stage)
if __name__=='__main__':build()
