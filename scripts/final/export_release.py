"""One-time export of ignored historical metadata; no data or papers are copied."""
from pathlib import Path
import argparse, collections, csv, gzip, hashlib, io, json

ROOT = Path(__file__).resolve().parents[2]
GROUP = ('dataset_id','method','prep','config_name','variant','initialization','report_role')
def key(row): return tuple(str(row.get(k) or '') for k in GROUP)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--legacy-runs',type=Path,required=True);args=ap.parse_args()
    output=ROOT/'results/final/release';output.mkdir(parents=True,exist_ok=True)
    records=[];owners={};allkeys=set()
    for path in sorted(args.legacy_runs.glob('*/*.json')):
        blob=path.read_bytes();meta=json.loads(blob);h=meta.pop('history',[])
        if h:meta['history_summary']={'count':len(h),'first':h[0],'last':h[-1], 'min_equation8_objective':min(r.get('equation8_objective',float('inf')) for r in h)}
        group_seeds=collections.defaultdict(list);trialpath=path.with_suffix('.trials.jsonl')
        if trialpath.exists():
            for line in trialpath.read_text().splitlines():
                r=json.loads(line);g=key(r);b=int(r['batch']);s=int(r['seed']);pk=(g,b,s)
                if pk in allkeys:raise ValueError(f'duplicate legacy trial {pk}')
                allkeys.add(pk);group_seeds[(g,b)].append(s)
                if g in owners and owners[g]!=str(path.relative_to(args.legacy_runs)):raise ValueError(f'multiple jobs for configuration {g}')
                owners[g]=str(path.relative_to(args.legacy_runs))
        groups=[{'key':list(g),'batch':b,'seeds':sorted(v)} for (g,b),v in sorted(group_seeds.items())]
        records.append({'metadata_id':str(path.relative_to(args.legacy_runs)), 'original_metadata_sha256':hashlib.sha256(blob).hexdigest(), 'original_trials_sha256':sha(trialpath) if trialpath.exists() else None,'groups':groups,'metadata':meta})
    target=output/'job_metadata.jsonl.gz'
    with target.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
            for r in records:gz.write((json.dumps(r,sort_keys=True,allow_nan=False)+'\n').encode())
    trials=ROOT/'results/v3_reproduction/all_trials.csv.gz';digest=hashlib.sha256();count=0;csvkeys=set()
    with gzip.open(trials,'rt',newline='') as f:
        for r in csv.DictReader(f):
            pk=(key(r),int(r['batch']),int(r['seed']));assert pk not in csvkeys,pk;csvkeys.add(pk);count+=1
    assert csvkeys==allkeys,(len(csvkeys-allkeys),len(allkeys-csvkeys))
    with gzip.open(trials,'rb') as f:
        while chunk:=f.read(1<<20):digest.update(chunk)
    inputs=[trials,target,ROOT/'results/v3_reproduction/all_configurations.csv',ROOT/'results/v3_reproduction/coverage_72_cells.csv',ROOT/'results/v3_reproduction/solver_audit.csv',ROOT/'configs/v3/paper_reference.yaml',ROOT/'configs/v3/protocols.yaml',ROOT/'configs/v3/datasets.yaml',ROOT/'configs/final/report_selection.yaml']
    release={'schema_version':1,'release_id':'historical-v3-20261109','frozen_source_commit':'95d599918627379b21f665b9b2754dd3852dc6dc','trial_file':str(trials.relative_to(ROOT)),'trial_sha256_uncompressed':digest.hexdigest(),'metadata_file':str(target.relative_to(ROOT)),'configuration_file':'results/v3_reproduction/all_configurations.csv','coverage_file':'results/v3_reproduction/coverage_72_cells.csv','paper_file':'configs/v3/paper_reference.yaml','selection_file':'configs/final/report_selection.yaml','counts':{'trials':count,'jobs':len(records),'configurations':len(owners),'cells':72},'coverage_counts':dict(collections.Counter(r['execution_status'] for r in csv.DictReader((ROOT/'results/v3_reproduction/coverage_72_cells.csv').open()))),'files':{str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs}}
    (ROOT/'configs/final/release_manifest.json').write_text(json.dumps(release,indent=2,sort_keys=True)+'\n');print(json.dumps(release['counts']))
if __name__=='__main__':main()
