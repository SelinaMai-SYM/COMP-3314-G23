"""Separate descriptive batch repeatability from single-assignment endpoints."""
from collections import defaultdict
import csv,json,math
from pathlib import Path
from .core import atomic_json,digest
from experiments.v3_reproduction.release import _write_csv


def build(source,output):
    source=Path(source);output=Path(output)
    with source.open(newline='') as stream:rows=list(csv.DictReader(stream))
    if not rows:raise ValueError('empty historical batch inventory')
    groups=defaultdict(list);keys=set()
    for row in rows:
        key=(row['config_id'],int(row['batch']))
        if key in keys:raise ValueError('duplicate historical configuration/batch')
        keys.add(key);seeds=json.loads(row['seed_list'])
        if int(row['n_trials'])!=50 or len(seeds)!=50 or len(set(seeds))!=50:
            raise ValueError('incomplete historical batch')
        native_fields=['selected_seed','selected_ACC','selected_NMI']
        present=[row.get(name) not in [None,''] for name in native_fields]
        if any(present) and not all(present):raise ValueError('partially missing native batch endpoint')
        if all(present) and int(row['selected_seed']) not in seeds:raise ValueError('native seed is outside its batch')
        for name in ['ACC','ACC_SD','NMI','NMI_SD']+(['selected_ACC','selected_NMI'] if all(present) else []):
            if not math.isfinite(float(row[name])):raise ValueError('nonfinite historical batch metric')
        groups[row['config_id']].append(row)
    selected=[];summary=[]
    for config,group in sorted(groups.items()):
        if len(group)<2:continue
        group.sort(key=lambda row:int(row['batch']));seen=set()
        for row in group:
            seeds=set(json.loads(row['seed_list']))
            if seeds&seen:raise ValueError('rounding seeds overlap between repeatability batches')
            seen.update(seeds)
        method=config.split('|')[1];native_available=sum(row.get('selected_seed') not in [None,''] for row in group)
        native_status=('UNAVAILABLE_NATIVE_ENDPOINT' if native_available<len(group) else 'SOURCE_NATIVE_DIAGNOSTIC_ONLY_CROSS_SUBSPACE_INERTIA' if method=='lda_kmeans' else 'SINGLE_ASSIGNMENT_PER_BATCH_NO_WITHIN_BATCH_SD')
        selected.extend({**row,'native_endpoint_status':native_status} for row in group)
        result={'config_id':config,'dataset':config.split('|')[0],'method':method,'batches':len(group),
                'seeds_per_batch':50,'rounding_seed_count':len(seen),'native_endpoint_status':native_status,'native_batches_available':native_available}
        for field in ['ACC','NMI','selected_ACC','selected_NMI']:
            values=[float(row[field]) for row in group] if not field.startswith('selected_') or native_available==len(group) else []
            result[field+'_min']=min(values) if values else None;result[field+'_max']=max(values) if values else None
        summary.append(result)
    output.mkdir(parents=True,exist_ok=True)
    _write_csv(output/'historical_repeatability_batches.csv',selected)
    _write_csv(output/'historical_repeatability_summary.csv',summary)
    atomic_json(output/'historical_repeatability_manifest.json',{
        'schema':'historical-repeatability-v1','source':'validated frozen release/batch_repeatability.csv',
        'source_sha256':digest(source),'source_rows':len(rows),'multi_batch_configurations':len(summary),
        'multi_batch_rows':len(selected),'selection':'all configurations with at least two complete disjoint50-seed batches; no ACC/NMI ranking',
        'scope':'Historical conditional rounding batches, not new experiments or independent dataset replicates. Ranges describe batch variation. Each native assignment has no within-batch SD.',
        'outputs':{name:digest(output/name) for name in ['historical_repeatability_batches.csv','historical_repeatability_summary.csv']}})
    return summary
