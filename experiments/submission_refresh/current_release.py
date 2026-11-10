"""Freeze and rebuild current SSC scalar results without data, artifacts or Git.

Scientific arrays remain in the recoverable external store. This release reads
only committed scalar trials and lightweight source/configuration metadata. It
never regenerates or substitutes an embedding during a statistical rebuild.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import tempfile

import numpy as np
import yaml

from experiments.submission_refresh.core import ROOT, atomic_json, digest, identity
from experiments.submission_refresh.selection import distances, rank, summarize

SCHEMA='subset-scalar-release-v1'
SUMMARY_FIELDS={'acc_mean','acc_sd','nmi_mean','nmi_sd','n','seed','native_objective','native_best'}
DERIVED_FIELDS={'D_max','D_mean','d_acc','d_nmi','delta_acc_pp','delta_nmi_pp',
                'paper_acc','paper_nmi','paper_acc_sd','paper_nmi_sd','delta_acc_sd_pp','delta_nmi_sd_pp'}
FLOAT_FIELDS={'gamma_nominal','gamma_effective'}
INT_FIELDS={'n_samples','n_classes','paper_deviations','preparation_assumptions'}
SELECTED_FIELDS=['benchmark','pool','endpoint','config_id','candidate_id',
                 'acc_mean','acc_sd','nmi_mean','nmi_sd','D_max','D_mean',
                 'delta_acc_pp','delta_nmi_pp']
OPTIONAL_FILES={
    'coverage':'execution_coverage.csv', 'source_inventory':'source_inventory.csv',
    'artifact_manifest':'artifact_manifest.json', 'confirmation':'rounding_confirmation.csv',
    'confirmation_seed_namespace':'confirmation_seed_namespace.json',
    'matched_sc':'matched_sc_summary.csv', 'matched_sc_contrasts':'matched_sc_contrasts.csv',
    'reference_contrasts':'reference_contrasts.csv', 'resource_usage':'resource_usage.json',
}


def _csv_rows(path):
    with Path(path).open(newline='') as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f'empty CSV input: {path}')
        rows=list(reader)
    if not rows:
        raise ValueError(f'empty CSV input: {path}')
    return rows


def _write_csv(path,rows):
    rows=list(rows)
    if not rows:
        Path(path).write_text('status\nNO_COMPLETE_ELIGIBLE_RECORDS\n')
        return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(list,dict)) else v for k,v in row.items()})


def _typed(row):
    result={k:(None if v=='' else v) for k,v in row.items()}
    for key in FLOAT_FIELDS:
        if result.get(key) is not None:result[key]=float(result[key])
    for key in INT_FIELDS:
        if result.get(key) is not None:result[key]=int(result[key])
    return result


def _decompressed_hash(path):
    h=hashlib.sha256()
    with gzip.open(path,'rb') as handle:
        while True:
            block=handle.read(1024*1024)
            if not block:break
            h.update(block)
    return h.hexdigest()


def _safe_path(root,relative):
    if Path(relative).is_absolute():raise ValueError('release inputs must use checkout-relative paths')
    root=Path(root).resolve();p=(root/relative).resolve()
    if p==root or root not in p.parents:
        raise ValueError('release input escapes the checkout')
    return p


def _canonicalize(rows):
    by_id={r['config_id']:r for r in rows}
    if len(by_id)!=len(rows):raise ValueError('duplicate configuration primary key')
    lookup={(r['candidate_id'],r['variant'],float(r['gamma_nominal']),r['initialization']):r['config_id'] for r in rows}
    if len(lookup)!=len(rows):raise ValueError('duplicate candidate/setting primary key')
    for row in rows:
        candidate=row['candidate_id'];alias=row.get('alias_of');seen=set()
        while alias:
            if alias in seen:raise ValueError('candidate alias cycle')
            seen.add(alias)
            key=(alias,row['variant'],float(row['gamma_nominal']),row['initialization'])
            if key not in lookup:raise ValueError('alias has no complete canonical configuration')
            canonical=by_id[lookup[key]];candidate=canonical['candidate_id'];alias=canonical.get('alias_of')
        row['canonical_config_id']=lookup[(candidate,row['variant'],float(row['gamma_nominal']),row['initialization'])]
    return rows


def _read_trials(path,metadata):
    canonical={r['config_id']:r for r in metadata if r['config_id']==r['canonical_config_id']}
    if not canonical:raise ValueError('no complete canonical configurations')
    names=sorted(canonical);index={name:i for i,name in enumerate(names)}
    values=np.full((len(names),50,3),np.nan);seen=np.zeros((len(names),50),dtype=bool);count=0
    with gzip.open(path,'rt',newline='') as handle:
        reader=csv.DictReader(handle)
        required={'config_id','candidate_id','seed','acc','nmi','inertia','variant','gamma_nominal','initialization'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):raise ValueError('trial columns missing')
        for row in reader:
            name=row['config_id']
            if name not in index:raise ValueError(f'trial configuration has no canonical metadata: {name}')
            seed=int(row['seed'])
            if seed<0 or seed>=50:raise ValueError('selection trial seed outside 0..49')
            i=index[name]
            if seen[i,seed]:raise ValueError('duplicate trial primary key (config_id,seed)')
            original=canonical[name]
            for field in ['candidate_id','variant','initialization']:
                if row[field]!=original[field]:raise ValueError('trial/configuration source mapping mismatch')
            if float(row['gamma_nominal'])!=float(original['gamma_nominal']):raise ValueError('trial gamma mapping mismatch')
            sample=np.array([float(row[k]) for k in ['acc','nmi','inertia']])
            if not np.isfinite(sample).all() or np.any(sample[:2]<0) or np.any(sample[:2]>1) or sample[2]<0:
                raise ValueError('invalid trial metric/native objective')
            values[i,seed]=sample;seen[i,seed]=True;count+=1
    if count==0:raise ValueError('empty trial input')
    if not seen.all():raise ValueError('missing trials: every complete configuration needs exact seeds 0..49')
    summaries={}
    for name,i in index.items():
        trials=[{'seed':seed,'acc':float(v[0]),'nmi':float(v[1]),'inertia':float(v[2])} for seed,v in enumerate(values[i])]
        summaries[name]=summarize(trials)
    return summaries,count


def _reconstruct(trial_path,metadata,paper):
    summaries,count=_read_trials(trial_path,metadata)
    mean_rows=[];native_rows=[];fixed=[]
    for raw in metadata:
        row={k:v for k,v in raw.items() if k not in SUMMARY_FIELDS|DERIVED_FIELDS}
        summary=summaries[row['canonical_config_id']]
        benchmark=row['benchmark']
        target={m:paper[m]['ssc'][benchmark]['mean'] for m in ['acc','nmi']}
        row.update(paper_acc=target['acc'],paper_nmi=target['nmi'],
                   paper_acc_sd=paper['acc']['ssc'][benchmark]['sd'],paper_nmi_sd=paper['nmi']['ssc'][benchmark]['sd'])
        mean=distances({**row,**{k:v for k,v in summary.items() if k!='native_best'},'endpoint':'mean_sample_sd_50'},target)
        native=distances({**row,**summary['native_best'],'n':1,'endpoint':'native_best_of_50'},target)
        mean.update(delta_acc_sd_pp=mean['acc_sd']-mean['paper_acc_sd'],delta_nmi_sd_pp=mean['nmi_sd']-mean['paper_nmi_sd'])
        native.update(delta_acc_sd_pp=None,delta_nmi_sd_pp=None)
        if native['acc_sd'] is not None or native['nmi_sd'] is not None:raise ValueError('single-result SD must be unavailable')
        mean_rows.append(mean);native_rows.append(native)
        if row['variant']=='E8' and float(row['gamma_nominal'])==1 and row['initialization']=='RANDOM':fixed.append(mean)
    winners=[];top=[]
    for rows in [mean_rows,native_rows]:
        groups=defaultdict(list)
        for row in rows:
            if row['pool']!='diagnostic':groups[(row['benchmark'],row['pool'])].append(row)
        for (benchmark,pool),group in sorted(groups.items()):
            ordered=rank(group)
            winner={**ordered[0],'eligible_configurations':len(group),
                    'unique_candidates':len({r.get('alias_of') or r['candidate_id'] for r in group}),
                    'candidate_aliases':len({r['candidate_id'] for r in group}),
                    'qualification':'Retrospective numerical match; historical sample identity unverified; conditional rounding endpoint'}
            winners.append(winner)
            top.extend({**r,'rank':i+1} for i,r in enumerate(ordered[:10]))
    distribution=[]
    for benchmark in sorted({r['benchmark'] for r in fixed}):
        rows=[r for r in fixed if r['benchmark']==benchmark and not r.get('alias_of')]
        if not rows:continue
        for metric in ['acc_mean','nmi_mean']:
            numbers=[r[metric] for r in rows]
            distribution.append({'benchmark':benchmark,'metric':metric,'unique_candidates':len(rows),
                                 'median':float(np.median(numbers)),'min':min(numbers),'max':max(numbers)})
    return {'joint_search_summary.csv':mean_rows,'native_best_summary.csv':native_rows,
            'fixed_protocol_summary.csv':fixed,'closest_matches.csv':winners,
            'top_matches.csv':top,'fixed_protocol_distribution.csv':distribution},count


def _selection_view(rows):
    result=[]
    for row in rows:
        view={key:row.get(key) for key in SELECTED_FIELDS}
        for key in SELECTED_FIELDS[5:]:
            if view[key] in [None,'']:view[key]=None
            else:view[key]=float(view[key])
        result.append(view)
    return sorted(result,key=lambda r:(r['benchmark'],r['pool'],r['endpoint']))


def _check_selected(actual,expected):
    actual=_selection_view(actual);expected=_selection_view(expected)
    if len(actual)!=len(expected):raise ValueError('selected-result count changed')
    for left,right in zip(actual,expected):
        for key in SELECTED_FIELDS:
            if isinstance(left[key],(int,float)) and isinstance(right[key],(int,float)):
                if not math.isclose(left[key],right[key],rel_tol=0,abs_tol=1e-10):
                    raise ValueError(f'selected scalar mismatch: {key}')
            elif left[key]!=right[key]:raise ValueError(f'selected identity/endpoint mismatch: {key}')


def _validate_light_csv(role,path):
    if role!='matched_sc':return
    for row in _csv_rows(path):
        if 'trials' not in row:raise ValueError('matched SC lightweight record lacks full trials')
        trials=json.loads(row['trials']);summary=summarize(trials)
        stored=json.loads(row['summary']) if row.get('summary') else row
        for field in ['acc_mean','acc_sd','nmi_mean','nmi_sd']:
            if field in stored and stored[field] not in [None,''] and not math.isclose(float(stored[field]),summary[field],abs_tol=1e-10,rel_tol=0):
                raise ValueError('matched SC summary differs from its complete 50 trials')


def freeze(output=Path('results/subset_search'),manifest_path=None,artifact_root=None):
    """Export lightweight identities and hash-lock complete current scalars."""
    output=Path(output).resolve();manifest_path=Path(manifest_path or ROOT/'configs/subset_search/release_manifest.json').resolve()
    original=_csv_rows(output/'joint_search_summary.csv')
    metadata=_canonicalize([_typed({k:v for k,v in row.items() if k not in SUMMARY_FIELDS|DERIVED_FIELDS}) for row in original])
    paper=yaml.safe_load((ROOT/'configs/v3/paper_reference.yaml').read_text())
    rebuilt,trial_count=_reconstruct(output/'trials.csv.gz',metadata,paper)
    recomputed={r['config_id']:r for r in rebuilt['joint_search_summary.csv']}
    for row in original:
        for key in ['acc_mean','acc_sd','nmi_mean','nmi_sd']:
            if not math.isclose(float(row[key]),recomputed[row['config_id']][key],abs_tol=1e-10,rel_tol=0):raise ValueError('original summary differs from authoritative trials')
    selected=_csv_rows(output/'closest_matches.csv');_check_selected(rebuilt['closest_matches.csv'],selected)
    source_records={};source_status='SOURCE_OBJECT_REFERENCES_ONLY'
    if artifact_root is not None:
        source_status='INLINE_COMMITTED_SOURCE_RECORDS'
        for row in metadata:
            path=Path(artifact_root)/row['record_directory']/'source.json'
            source=json.loads(path.read_text());key=identity(source);source_records[key]=source
            row.update(source_record_id=key,scientific_source_commit=source['source_commit'],
                       scientific_source_fingerprint=source['implementation_hash'],cache_identity=source.get('cache_identity'))
    # Validate optional light records before any release files are authored.
    for role,name in OPTIONAL_FILES.items():
        path=output/name
        if path.is_file():_validate_light_csv(role,path)
    output.relative_to(ROOT);manifest_path.relative_to(ROOT)
    inventory=output/'configuration_inventory.csv';_write_csv(inventory,metadata)
    sources=output/'source_records.json.gz'
    payload=(json.dumps({'schema':'deduplicated-scientific-source-records-v1','status':source_status,'records':source_records},sort_keys=True,indent=2)+'\n').encode()
    with sources.open('wb') as handle:handle.write(gzip.compress(payload,mtime=0))
    required={'trials':output/'trials.csv.gz','configuration_inventory':inventory,'source_records':sources,
              'catalogue':ROOT/'results/subset_search/candidate_catalogue.json',
              'protocol':ROOT/'configs/subset_search/protocol.yaml','selection':ROOT/'configs/submission_refresh/selection.yaml',
              'paper':ROOT/'configs/v3/paper_reference.yaml'}
    for role,name in OPTIONAL_FILES.items():
        if (output/name).is_file():required[role]=output/name
    inputs={role:{'path':str(path.relative_to(ROOT)),'sha256':digest(path),'bytes':path.stat().st_size} for role,path in required.items()}
    inputs['trials']['uncompressed_sha256']=_decompressed_hash(output/'trials.csv.gz')
    manifest={'schema':SCHEMA,'checkout_root_relative':'../..','inputs':inputs,
              'trial_primary_key':['config_id','seed'],'selection_seed_set':list(range(50)),
              'metric_input_units':'unit interval; published summaries are percentage points',
              'counts':{'trials':trial_count,'complete_configurations_including_aliases':len(metadata),
                        'canonical_configurations':len({r['canonical_config_id'] for r in metadata})},
              'expected_selections':_selection_view(selected),'source_identity_status':source_status,
              'scope':'Current SSC subset mean/sample-SD and native-best endpoints; historical release remains separate',
              'no_external_objects_required_for_rebuild':True,'no_git_history_required_for_rebuild':True}
    atomic_json(manifest_path,manifest)
    return manifest


def load(manifest_path):
    manifest_path=Path(manifest_path).resolve();manifest=json.loads(manifest_path.read_text())
    if manifest.get('schema')!=SCHEMA:raise ValueError('unsupported current release schema')
    root=(manifest_path.parent/manifest['checkout_root_relative']).resolve()
    roles={'trials','configuration_inventory','source_records','catalogue','protocol','selection','paper'}
    if not roles.issubset(manifest.get('inputs',{})):raise ValueError('release inputs missing')
    paths={}
    for role,record in manifest['inputs'].items():
        path=_safe_path(root,record['path'])
        if not path.is_file() or path.stat().st_size==0 or digest(path)!=record['sha256'] or path.stat().st_size!=record['bytes']:
            raise ValueError(f'release input missing, empty or hash mismatch: {role}')
        paths[role]=path
    if _decompressed_hash(paths['trials'])!=manifest['inputs']['trials']['uncompressed_sha256']:
        raise ValueError('uncompressed trial CSV hash mismatch')
    metadata=[_typed(row) for row in _csv_rows(paths['configuration_inventory'])]
    _canonicalize(metadata)
    catalogue=json.loads(paths['catalogue'].read_text());candidates={c['candidate_id']:c for c in catalogue['candidates']}
    for row in metadata:
        c=candidates.get(row['candidate_id'])
        if c is None or c['benchmark']!=row['benchmark'] or c['pool']!=row['pool'] or int(c['n'])!=row['n_samples']:
            raise ValueError('configuration/catalogue identity mismatch')
        p=_safe_path(root,c['manifest_path'])
        if not p.is_file() or digest(p)!=c['manifest_sha256']:raise ValueError('sample manifest missing/hash mismatch')
    with gzip.open(paths['source_records'],'rt') as handle:sources=json.load(handle)
    for key,record in sources['records'].items():
        if identity(record)!=key:raise ValueError('source record identity mismatch')
    for row in metadata:
        if row.get('source_record_id') and row['source_record_id'] not in sources['records']:raise ValueError('configuration source record missing')
    for role,path in paths.items():_validate_light_csv(role,path)
    paper=yaml.safe_load(paths['paper'].read_text());tables,count=_reconstruct(paths['trials'],metadata,paper)
    if count!=manifest['counts']['trials'] or len(metadata)!=manifest['counts']['complete_configurations_including_aliases']:
        raise ValueError('release counts disagree')
    if len({r['canonical_config_id'] for r in metadata})!=manifest['counts']['canonical_configurations']:
        raise ValueError('canonical configuration count disagrees')
    _check_selected(tables['closest_matches.csv'],manifest['expected_selections'])
    return root,manifest,paths,tables


def rebuild(manifest_path,output):
    """Validate every input and endpoint before atomically replacing known output."""
    root,manifest,paths,tables=load(manifest_path)
    output=Path(output).resolve()
    if output==root or root in output.parents and output in [root/'results',root/'report']:
        raise ValueError('unsafe output directory')
    if any(path==output or output in path.parents for path in paths.values()):raise ValueError('output would replace release inputs')
    if output.exists() and any(output.iterdir()):
        marker=output/'validation.json'
        if not marker.is_file():raise ValueError('refusing to replace unknown nonempty output directory')
        previous=json.loads(marker.read_text())
        if previous.get('schema')!=SCHEMA or previous.get('ok') is not True:raise ValueError('refusing to replace unknown nonempty output directory')
    output.parent.mkdir(parents=True,exist_ok=True);temporary=Path(tempfile.mkdtemp(prefix='.rebuild-current-',dir=output.parent))
    try:
        for name,rows in tables.items():_write_csv(temporary/name,rows)
        for role,name in OPTIONAL_FILES.items():
            if role in paths:shutil.copy2(paths[role],temporary/name)
        for benchmark in sorted({r['benchmark'] for r in tables['joint_search_summary.csv']}):
            text=[f'# {benchmark}: scalar release rebuild','','Retrospective joint ACC/NMI matching. Historical sample identity remains unverified. Mean/sample-SD and single native-best endpoints are separate.','','| Pool / endpoint | Candidate | ACC (%) | NMI (%) | Dmax / Dmean | Solver |','|---|---|---:|---:|---:|---|']
            for row in tables['closest_matches.csv']:
                if row['benchmark']!=benchmark:continue
                fmt=lambda m:f"{row[m+'_mean']:.3f}"+(f" +/- {row[m+'_sd']:.3f}" if row[m+'_sd'] is not None else ' (single run)')
                text.append(f"| {row['pool']} / {row['endpoint']} | {row['candidate_id']} | {fmt('acc')} | {fmt('nmi')} | {row['D_max']:.3f} / {row['D_mean']:.3f} | {row['solver_status']} |")
            (temporary/(benchmark+'.md')).write_text('\n'.join(text)+'\n')
        validation={'schema':SCHEMA,'ok':True,**manifest['counts'],'source_identity_status':manifest['source_identity_status'],
                    'compressed_trials_sha256':manifest['inputs']['trials']['sha256'],
                    'uncompressed_trials_sha256':manifest['inputs']['trials']['uncompressed_sha256'],
                    'selection_recomputed_and_matches':True,'external_data_read':False,'external_artifact_read':False,'git_history_read':False}
        atomic_json(temporary/'validation.json',validation)
        atomic_json(temporary/'output_hashes.json',{p.name:digest(p) for p in sorted(temporary.iterdir()) if p.is_file()})
        if output.exists():
            old=output.with_name(output.name+'.previous')
            if old.exists():raise ValueError('previous rebuild backup exists; refusing replacement')
            output.rename(old)
            try:temporary.rename(output)
            except BaseException:old.rename(output);raise
            shutil.rmtree(old)
        else:temporary.rename(output)
        return validation
    finally:
        if temporary.exists():shutil.rmtree(temporary)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['freeze','rebuild'])
    parser.add_argument('--release-manifest',default='configs/subset_search/release_manifest.json')
    parser.add_argument('--output',required=True)
    parser.add_argument('--artifact-root')
    args=parser.parse_args()
    result=freeze(args.output,args.release_manifest,args.artifact_root) if args.phase=='freeze' else rebuild(args.release_manifest,args.output)
    print(json.dumps(result.get('counts',result),indent=2))

if __name__=='__main__':main()
