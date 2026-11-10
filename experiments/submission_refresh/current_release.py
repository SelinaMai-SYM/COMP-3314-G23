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
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
import yaml

from experiments.submission_refresh.core import ROOT, atomic_json, digest, identity
from experiments.submission_refresh.selection import distances, rank, summarize
from experiments.submission_refresh.csv_transport import (
    DEFAULT_MIN_BYTES, copy_plain_csv, open_csv, pack_large_csvs, resolve_csv)

SCHEMA='subset-scalar-release-v1'
CSV_PACK_MIN_BYTES=DEFAULT_MIN_BYTES
SUMMARY_FIELDS={'acc_mean','acc_sd','nmi_mean','nmi_sd','n','seed','native_objective','native_best'}
DERIVED_FIELDS={'D_max','D_mean','d_acc','d_nmi','delta_acc_pp','delta_nmi_pp',
                'paper_acc','paper_nmi','paper_acc_sd','paper_nmi_sd','delta_acc_sd_pp','delta_nmi_sd_pp'}
FLOAT_FIELDS={'gamma_nominal','gamma_effective'}
INT_FIELDS={'n_samples','n_classes','paper_deviations','preparation_assumptions'}
SELECTED_FIELDS=['benchmark','pool','endpoint','config_id','candidate_id',
                 'acc_mean','acc_sd','nmi_mean','nmi_sd','D_max','D_mean',
                 'delta_acc_pp','delta_nmi_pp']
OPTIONAL_FILES={
    'coverage':'execution_coverage.csv','matched_sc_coverage':'matched_sc_coverage.csv',
    'completion_records':'completion_records.json.gz','source_inventory':'source_inventory.csv',
    'artifact_manifest':'artifact_manifest.json', 'confirmation':'rounding_confirmation.csv',
    'confirmation_seed_namespace':'confirmation_seed_namespace.json',
    'matched_sc':'matched_sc_summary.csv', 'matched_sc_contrasts':'matched_sc_contrasts.csv',
    'reference_contrasts':'reference_contrasts.csv', 'family_distributions':'fixed_protocol_family_distributions.csv', 'resource_usage':'resource_usage.json',
    'certified_search_status':'certified_search_status.csv',
}


def _csv_rows(path):
    with open_csv(path) as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f'empty CSV input: {path}')
        rows=list(reader)
    if not rows:
        raise ValueError(f'empty CSV input: {path}')
    return rows


def _available_file(path):
    path=Path(path)
    return resolve_csv(path) if path.name.endswith(('.csv','.csv.gz')) else path if path.is_file() else None


def _publish_inventory(output,metadata,manifest_path):
    """Stage the complete inventory and choose transport before hash locking."""
    logical=output/'configuration_inventory.csv';previous=resolve_csv(logical)
    if previous is not None and previous.name.endswith('.csv.gz'):
        # A later freeze may replace its own verified inventory, never an
        # unrelated compressed file that happens to use this filename.
        old=json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
        info=old.get('inputs',{}).get('configuration_inventory',{})
        if info.get('path')!=str(previous.relative_to(ROOT)) or info.get('sha256')!=digest(previous):
            raise ValueError('refusing to replace an unknown gzip configuration inventory')
    with tempfile.TemporaryDirectory(prefix='.inventory-transport-',dir=output) as work:
        staged=Path(work)/logical.name;_write_csv(staged,metadata)
        pack_large_csvs(Path(work),min_bytes=CSV_PACK_MIN_BYTES,names=[logical.name])
        actual=resolve_csv(staged,required=True);target=output/actual.name
        os.replace(actual,target)
        if previous is not None and previous!=target:previous.unlink()
    return target


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


def _reconstruct(trial_path,metadata,paper,reference_ids=None,candidate_pools=None,certified_pools=None):
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
        if row['prep']=='Y0' and row['variant']=='E8' and float(row['gamma_nominal'])==1 and row['initialization']=='RANDOM':fixed.append(mean)
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
    from experiments.subset_search.aggregate import fixed_distributions,family_distributions,reference_contrasts
    from experiments.subset_search.certified_status import certified_search_status
    return {'joint_search_summary.csv':mean_rows,'native_best_summary.csv':native_rows,
            'fixed_protocol_summary.csv':fixed,'closest_matches.csv':winners,
            'top_matches.csv':top,'fixed_protocol_distribution.csv':fixed_distributions(fixed),
            'fixed_protocol_family_distributions.csv':family_distributions(fixed),
            'certified_search_status.csv':certified_search_status(mean_rows,certified_pools if certified_pools is not None else candidate_pools),
            'reference_contrasts.csv':reference_contrasts(mean_rows,fixed,reference_ids or {},candidate_pools)},count


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


def _matched_sc_rows(path):
    rows=[];keys=set()
    for raw in _csv_rows(path):
        if 'trials' not in raw:raise ValueError('matched SC lightweight record lacks full trials')
        key=(raw['candidate_id'],raw['initialization'])
        if key in keys:raise ValueError('duplicate matched SC candidate/initialization record')
        keys.add(key)
        trials=json.loads(raw['trials']);summary=summarize(trials)
        stored=json.loads(raw['summary']) if raw.get('summary') else raw
        for field in ['acc_mean','acc_sd','nmi_mean','nmi_sd']:
            if field in stored and stored[field] not in [None,''] and not math.isclose(float(stored[field]),summary[field],abs_tol=1e-10,rel_tol=0):
                raise ValueError('matched SC summary differs from its complete 50 trials')
        native=json.loads(raw['native_best']) if raw.get('native_best') else stored.get('native_best')
        if native is None:raise ValueError('matched SC native endpoint missing')
        expected=summary['native_best']
        for field in ['acc_mean','nmi_mean','seed','native_objective','acc_sd','nmi_sd']:
            value=native.get(field);wanted=expected[field]
            if wanted is None:
                if value is not None:raise ValueError('matched SC single-result SD must be unavailable')
            elif value is None or not math.isclose(float(value),float(wanted),rel_tol=0,abs_tol=1e-10):
                raise ValueError('matched SC native endpoint differs from its native-best trial')
        if native.get('n',1)!=1:raise ValueError('matched SC native endpoint must have n=1')
        rows.append({**_typed(raw),**summary,'native_best':{**expected,'n':1}})
    return rows


def _validate_light_csv(role,path):
    if role=='matched_sc':_matched_sc_rows(path)
    elif role=='completion_records':
        with gzip.open(path,'rt') as stream:record=json.load(stream)
        if record.get('schema')!='subset-completion-evidence-v1' or not isinstance(record.get('records'),dict):raise ValueError('invalid completion evidence schema')
        for directory,details in record['records'].items():
            if Path(directory).is_absolute() or '..' in Path(directory).parts:raise ValueError('unsafe completion evidence path')
            if details.get('original_status',{}).get('status')!='FAILED':raise ValueError('completion evidence does not retain its original failed status')
            for item in details.get('completion_failures',[])+details.get('completion_attempts',[]):
                if not isinstance(item.get('record'),dict) or not item.get('sha256'):raise ValueError('incomplete completion record identity')
    elif role in ['coverage','matched_sc_coverage']:
        rows=_csv_rows(path)
        keys=['candidate_id','variant','gamma_nominal','initialization'] if role=='coverage' else ['candidate_id','initialization']
        identities=[tuple(row.get(key) for key in keys) for row in rows]
        if len(identities)!=len(set(identities)):raise ValueError('duplicate execution coverage key')



def _verify_matched_sources(metadata,rows):
    by_key={(r['candidate_id'],r['initialization']):r for r in rows}
    for configuration in metadata:
        key=(configuration['candidate_id'],configuration['initialization'])
        if key not in by_key:
            status=configuration.get('matched_sc_status')
            if status and status!='COMPLETED':continue
            raise ValueError('complete SSC configuration lacks its complete matched SC control or explicit unavailable status')
        control=by_key[key]
        if not configuration.get('F_sha256') or control.get('F_sha256')!=configuration['F_sha256']:
            raise ValueError('matched SC/SSC exact F object identity mismatch')
        for field in ['benchmark','pool','n_samples']:
            if control.get(field)!=configuration.get(field):raise ValueError('matched SC/SSC source metadata mismatch')
        for field in ['input_fingerprint','sample_manifest_sha256']:
            if control.get(field)!=configuration.get(field):raise ValueError('matched SC/SSC sample fingerprint mismatch')


def _verify_derived(role,actual,path):
    if not actual:
        try:empty_rows=_csv_rows(path)
        except ValueError as exc:
            if 'empty CSV input' in str(exc):return
            raise
        if all(row.get('status')=='NO_COMPLETE_ELIGIBLE_RECORDS' for row in empty_rows):return
        raise ValueError(f'{role} has stored rows but no recomputable eligible observations')
    expected=_csv_rows(path)
    if role=='family_distributions':
        key_fields=['benchmark','pool','family','weighting','metric'];numeric=['declared_candidates','observations','median','min','max']
    elif role=='reference_contrasts':
        key_fields=['benchmark','target_pool','reference_candidate','contrast'];numeric=['acc_mean','nmi_mean','D_max','D_mean','eligible_configurations_in_contrast']
    elif role=='matched_sc_contrasts':
        key_fields=['config_id','endpoint'];numeric=['ssc_acc','ssc_nmi','sc_acc','sc_nmi','delta_acc_pp','delta_nmi_pp']
    elif role=='certified_search_status':
        key_fields=['benchmark','pool','endpoint'];numeric=['historical_complete_configurations','historical_complete_canonical_configurations','historical_complete_unique_inputs','rounding_starts_per_complete_configuration','comparable_certified_search_configurations']
    else:return
    def normalize(value):return '' if value is None else str(value)
    def mapping(rows):
        result={tuple(normalize(row.get(k)) for k in key_fields):row for row in rows}
        if len(result)!=len(rows):raise ValueError('duplicate derived-table primary key')
        return result
    left=mapping(actual);right=mapping(expected)
    if left.keys()!=right.keys():raise ValueError(f'{role} derived identities/coverage mismatch')
    for key,row in left.items():
        old=right[key]
        if role=='reference_contrasts' and normalize(row.get('config_id'))!=normalize(old.get('config_id')):
            raise ValueError('reference contrast selected a different configuration')
        if role=='certified_search_status':
            for field in ['search_track','certified_closest_config_id','status','certificate_transfer_allowed','scope']:
                if normalize(row.get(field))!=normalize(old.get(field)):
                    raise ValueError('certified-search availability scope/status mismatch: '+field)
        for field in numeric:
            a=row.get(field);b=old.get(field)
            if a in [None,''] and b in [None,'']:continue
            if a in [None,''] or b in [None,''] or not math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-10):
                raise ValueError(f'{role} derived scalar mismatch: {field}')


def _verify_compatibility(metadata,candidates,policy):
    from experiments.subset_search.aggregate import compatibility_counts
    for row in metadata:
        counts=compatibility_counts(candidates[row['candidate_id']],policy)
        for field in ['paper_deviations','preparation_assumptions','compatibility_policy_version']:
            if row.get(field)!=counts[field]:raise ValueError('configuration differs from the frozen compatibility policy')


def freeze(output=Path('results/subset_search'),manifest_path=None,artifact_root=None):
    """Export lightweight identities and hash-lock complete current scalars."""
    output=Path(output).resolve();manifest_path=Path(manifest_path or ROOT/'configs/subset_search/release_manifest.json').resolve()
    original=_csv_rows(output/'joint_search_summary.csv')
    metadata=_canonicalize([_typed({k:v for k,v in row.items() if k not in SUMMARY_FIELDS|DERIVED_FIELDS}) for row in original])
    paper=yaml.safe_load((ROOT/'configs/v3/paper_reference.yaml').read_text())
    catalogue=json.loads((ROOT/'results/subset_search/candidate_catalogue.json').read_text())
    protocol=yaml.safe_load((ROOT/'configs/subset_search/protocol.yaml').read_text())
    compatibility_path=ROOT/'configs/subset_search/compatibility.yaml'
    if compatibility_path.exists():_verify_compatibility(metadata,{c['candidate_id']:c for c in catalogue['candidates']},yaml.safe_load(compatibility_path.read_text()))
    candidate_pools={b:{c['pool'] for c in catalogue['candidates'] if c['benchmark']==b and c['pool']!='diagnostic'} for b in protocol.get('reference_candidates',{})}
    certified_pools={b:{c['pool'] for c in catalogue['candidates'] if c['benchmark']==b and c['pool']!='diagnostic'} for b in {c['benchmark'] for c in catalogue['candidates']}}
    rebuilt,trial_count=_reconstruct(output/'trials.csv.gz',metadata,paper,protocol.get('reference_candidates',{}),candidate_pools,certified_pools)
    recomputed={r['config_id']:r for r in rebuilt['joint_search_summary.csv']}
    for row in original:
        for key in ['acc_mean','acc_sd','nmi_mean','nmi_sd']:
            if not math.isclose(float(row[key]),recomputed[row['config_id']][key],abs_tol=1e-10,rel_tol=0):raise ValueError('original summary differs from authoritative trials')
    selected=_csv_rows(output/'closest_matches.csv');_check_selected(rebuilt['closest_matches.csv'],selected)
    if _available_file(output/'matched_sc_summary.csv') is not None:
        from experiments.subset_search.aggregate import matched_sc_contrasts
        sc=_matched_sc_rows(output/'matched_sc_summary.csv');_verify_matched_sources(metadata,sc)
        rebuilt['matched_sc_contrasts.csv']=matched_sc_contrasts(rebuilt['closest_matches.csv'],sc)
    for role in ['family_distributions','reference_contrasts','matched_sc_contrasts','certified_search_status']:
        path=_available_file(output/OPTIONAL_FILES[role])
        if path is not None:_verify_derived(role,rebuilt[OPTIONAL_FILES[role]],path)
    source_records={};source_status='SOURCE_OBJECT_REFERENCES_ONLY'
    if artifact_root is not None:
        source_status='INLINE_COMMITTED_SOURCE_RECORDS'
        from .core import ArtifactStore
        store=ArtifactStore(artifact_root)
        def register(row,is_sc=False):
            if is_sc:
                relative=Path(row['source_record']);folder=store.root/relative.parent;record_path=store.root/relative
            else:
                folder=store.root/row['record_directory'];record_path=folder/row['record_file']
            if store.root not in folder.resolve().parents or store.root not in record_path.resolve().parents:raise ValueError('configuration source path escapes artifact root')
            original=json.loads((folder/'source.json').read_text())
            record=json.loads(record_path.read_text()) if record_path.is_file() else {}
            supplemental=record.get('completion_provenance',{})
            if row.get('configuration_source_kind')=='per_configuration_completion' and not supplemental:raise ValueError('completed configuration controller record is unavailable')
            source=record.get('source') if supplemental else original
            if supplemental:
                if not isinstance(source,dict) or store.get(supplemental['source'])!=source:raise ValueError('per-configuration actual source object mismatch')
                if source.get('source_files',{}).get(supplemental.get('controller'))!=supplemental.get('controller_sha256'):raise ValueError('completion controller source hash mismatch')
                if row.get('configuration_record_sha256') and digest(record_path)!=row['configuration_record_sha256']:raise ValueError('configuration record changed after aggregation')
            key=identity(source);original_key=identity(original);source_records[key]=source;source_records[original_key]=original
            for field,wanted in [('source_record_id',key),('original_source_record_id',original_key),('scientific_source_fingerprint',source.get('implementation_hash'))]:
                if row.get(field) not in [None,'',wanted]:raise ValueError('configuration actual source mapping mismatch: '+field)
            row.update(source_record_id=key,original_source_record_id=original_key,
                       scientific_source_commit=source.get('source_commit'),scientific_source_fingerprint=source.get('implementation_hash'),cache_identity=source.get('cache_identity'))
        for row in metadata:register(row)
        if _available_file(output/'matched_sc_summary.csv') is not None:
            for row in _matched_sc_rows(output/'matched_sc_summary.csv'):register(row,True)
        completion_path=output/'completion_records.json.gz'
        if completion_path.is_file():
            with gzip.open(completion_path,'rt') as stream:completion_records=json.load(stream)
            for details in completion_records.get('records',{}).values():
                original=details.get('original_status',{}).get('source')
                if isinstance(original,dict):source_records[identity(original)]=original
                for entry in details.get('completion_attempts',[]):
                    source=entry.get('record',{}).get('source')
                    if isinstance(source,dict):source_records[identity(source)]=source
    elif any(row.get('source_record_id') for row in metadata):
        # A source-aware aggregation cannot be downgraded to hash-only records.
        existing=output/'source_records.json.gz'
        if not existing.is_file():raise ValueError('actual source records require --artifact-root for first freeze')
        with gzip.open(existing,'rt') as stream:source_records=json.load(stream)['records']
        if any(row['source_record_id'] not in source_records for row in metadata):raise ValueError('inline source record unavailable')
        source_status='INLINE_COMMITTED_SOURCE_RECORDS'
    # Validate optional light records before any release files are authored.
    for role,name in OPTIONAL_FILES.items():
        path=_available_file(output/name)
        if path is not None:_validate_light_csv(role,path)
    output.relative_to(ROOT);manifest_path.relative_to(ROOT)
    if _available_file(output/'certified_search_status.csv') is None:
        _write_csv(output/'certified_search_status.csv',rebuilt['certified_search_status.csv'])
    inventory=_publish_inventory(output,metadata,manifest_path)
    sources=output/'source_records.json.gz'
    payload=(json.dumps({'schema':'deduplicated-scientific-source-records-v1','status':source_status,'records':source_records},sort_keys=True,indent=2)+'\n').encode()
    with sources.open('wb') as handle:handle.write(gzip.compress(payload,mtime=0))
    required={'trials':output/'trials.csv.gz','configuration_inventory':inventory,'source_records':sources,
              'catalogue':ROOT/'results/subset_search/candidate_catalogue.json',
              'protocol':ROOT/'configs/subset_search/protocol.yaml','selection':ROOT/'configs/submission_refresh/selection.yaml',
              'paper':ROOT/'configs/v3/paper_reference.yaml'}
    if (ROOT/'configs/subset_search/compatibility.yaml').exists():required['compatibility']=ROOT/'configs/subset_search/compatibility.yaml'
    for role,name in OPTIONAL_FILES.items():
        path=_available_file(output/name)
        if path is not None:required[role]=path
    inputs={role:{'path':str(path.relative_to(ROOT)),'sha256':digest(path),'bytes':path.stat().st_size} for role,path in required.items()}
    for role,path in required.items():
        if path.suffix=='.gz':inputs[role]['uncompressed_sha256']=_decompressed_hash(path)
    manifest={'schema':SCHEMA,'checkout_root_relative':'../..','inputs':inputs,
              'trial_primary_key':['config_id','seed'],'selection_seed_set':list(range(50)),
              'metric_input_units':'unit interval; published summaries are percentage points',
              'counts':{'trials':trial_count,'complete_configurations_including_aliases':len(metadata),
                        'canonical_configurations':len({r['canonical_config_id'] for r in metadata})},
              'expected_selections':_selection_view(selected),'source_identity_status':source_status,
              'scope':'Current SSC subset historical-style mean/sample-SD and native-best endpoints plus separate certified-search availability; no certified closest winner inferred; historical release remains separate',
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
        if path.name.endswith(('.csv','.csv.gz')):
            # A manifest pins the physical transport; do not silently switch
            # to a different representation even if its logical CSV matches.
            actual=resolve_csv(path,required=True)
            if actual!=path:raise ValueError('release CSV transport differs from hash-locked path: '+role)
        if not path.is_file() or path.stat().st_size==0 or digest(path)!=record['sha256'] or path.stat().st_size!=record['bytes']:
            raise ValueError(f'release input missing, empty or hash mismatch: {role}')
        paths[role]=path
    for role,path in paths.items():
        expected=manifest['inputs'][role].get('uncompressed_sha256')
        if expected is not None and _decompressed_hash(path)!=expected:raise ValueError('uncompressed release input hash mismatch: '+role)
    metadata=[_typed(row) for row in _csv_rows(paths['configuration_inventory'])]
    _canonicalize(metadata)
    catalogue=json.loads(paths['catalogue'].read_text());candidates={c['candidate_id']:c for c in catalogue['candidates']}
    if 'compatibility' in paths:_verify_compatibility(metadata,candidates,yaml.safe_load(paths['compatibility'].read_text()))
    for row in metadata:
        c=candidates.get(row['candidate_id'])
        if c is None or c['benchmark']!=row['benchmark'] or c['pool']!=row['pool'] or int(c['n'])!=row['n_samples']:
            raise ValueError('configuration/catalogue identity mismatch')
        p=_safe_path(root,c['manifest_path'])
        if not p.is_file() or digest(p)!=c['manifest_sha256']:raise ValueError('sample manifest missing/hash mismatch')
    with gzip.open(paths['source_records'],'rt') as handle:sources=json.load(handle)
    for key,record in sources['records'].items():
        if identity(record)!=key:raise ValueError('source record identity mismatch')
    def verify_source(row):
        key=row.get('source_record_id')
        if not key:return
        if key not in sources['records']:raise ValueError('configuration source record missing')
        record=sources['records'][key]
        if row.get('scientific_source_fingerprint') not in [None,'',record.get('implementation_hash')]:raise ValueError('configuration scientific source fingerprint mismatch')
        if row.get('scientific_source_commit') not in [None,'',record.get('source_commit')]:raise ValueError('configuration scientific source commit mismatch')
        if row.get('cache_identity') not in [None,'',record.get('cache_identity')]:raise ValueError('configuration scientific cache identity mismatch')
        original=row.get('original_source_record_id')
        if original and original not in sources['records']:raise ValueError('configuration original source record missing')
        if row.get('configuration_source_kind')=='per_configuration_completion':
            if record.get('source_files',{}).get(row.get('controller_path'))!=row.get('controller_sha256') or not row.get('controller_sha256'):
                raise ValueError('configuration actual controller source mismatch')
    for row in metadata:verify_source(row)
    if 'matched_sc'in paths:
        for row in _matched_sc_rows(paths['matched_sc']):verify_source(row)

    for role,path in paths.items():_validate_light_csv(role,path)
    paper=yaml.safe_load(paths['paper'].read_text());protocol=yaml.safe_load(paths['protocol'].read_text())
    candidate_pools={b:{c['pool'] for c in catalogue['candidates'] if c['benchmark']==b and c['pool']!='diagnostic'} for b in protocol.get('reference_candidates',{})}
    certified_pools={b:{c['pool'] for c in catalogue['candidates'] if c['benchmark']==b and c['pool']!='diagnostic'} for b in {c['benchmark'] for c in catalogue['candidates']}}
    tables,count=_reconstruct(paths['trials'],metadata,paper,protocol.get('reference_candidates',{}),candidate_pools,certified_pools)
    if count!=manifest['counts']['trials'] or len(metadata)!=manifest['counts']['complete_configurations_including_aliases']:
        raise ValueError('release counts disagree')
    if len({r['canonical_config_id'] for r in metadata})!=manifest['counts']['canonical_configurations']:
        raise ValueError('canonical configuration count disagrees')
    _check_selected(tables['closest_matches.csv'],manifest['expected_selections'])
    if 'matched_sc' in paths:
        from experiments.subset_search.aggregate import matched_sc_contrasts
        sc=_matched_sc_rows(paths['matched_sc']);_verify_matched_sources(metadata,sc)
        tables['matched_sc_contrasts.csv']=matched_sc_contrasts(tables['closest_matches.csv'],sc)
    for role in ['family_distributions','reference_contrasts','matched_sc_contrasts','certified_search_status']:
        if role in paths:_verify_derived(role,tables[OPTIONAL_FILES[role]],paths[role])
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
        shutil.copy2(paths['source_records'],temporary/'source_records.json.gz')
        copy_plain_csv(paths['configuration_inventory'],temporary/'configuration_inventory.csv')
        for role,name in OPTIONAL_FILES.items():
            if role in paths and name not in tables:
                if name.endswith('.csv'):copy_plain_csv(paths[role],temporary/name)
                else:shutil.copy2(paths[role],temporary/name)
        from experiments.subset_search.markdown import benchmark_markdown
        paper=yaml.safe_load(paths['paper'].read_text())
        for benchmark in paper.get('datasets',sorted({r['benchmark'] for r in tables['joint_search_summary.csv']})):
            (temporary/(benchmark+'.md')).write_text(benchmark_markdown(benchmark,tables['closest_matches.csv'],paper,tables['certified_search_status.csv']))
        validation={'schema':SCHEMA,'ok':True,**manifest['counts'],'source_identity_status':manifest['source_identity_status'],
                    'compressed_trials_sha256':manifest['inputs']['trials']['sha256'],
                    'uncompressed_trials_sha256':manifest['inputs']['trials']['uncompressed_sha256'],
                    'selection_recomputed_and_matches':True,'external_data_read':False,'external_artifact_read':False,'git_history_read':False}
        validation['certified_search_availability_recomputed']=True
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
