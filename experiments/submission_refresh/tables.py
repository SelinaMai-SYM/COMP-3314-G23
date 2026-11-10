"""Atomic English benchmark views from authoritative, qualified display rows."""
from pathlib import Path
import csv
import json
import shutil
import tempfile
import yaml
from .core import ROOT,atomic_json,digest
from .scalar_evidence import PAPER_METHOD

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


def build(root=ROOT):
    root=Path(root).resolve();out=root/'results/submission_refresh/per_benchmark'
    paper_path=root/'configs/v3/paper_reference.yaml';hashes={str(paper_path.relative_to(root)):digest(paper_path)};paper=yaml.safe_load(paper_path.read_text())
    paths=[];rows=[]
    for relative,endpoint in INPUTS:
        path=root/relative
        if not path.exists():continue
        paths.append(path);hashes[relative]=digest(path)
        with path.open(newline='') as stream:
            for record in csv.DictReader(stream):
                if endpoint and record.get('endpoint')!=endpoint:continue
                record['table_source']=relative;rows.append(record)
    if out.exists() and (not out.is_dir() or any(path.name not in {name+'.md' for name in NAMES}|{'table_inputs.json'} for path in out.iterdir())):
        raise ValueError('refusing to replace unknown benchmark-table files')
    out.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.benchmark-tables-',dir=out.parent))
    try:
        for name in NAMES:
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
