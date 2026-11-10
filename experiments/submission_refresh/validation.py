"""Check authoritative records and content addresses without raw benchmark data."""
from pathlib import Path
import csv,json
from .core import ArtifactStore,ROOT,atomic_json,digest

def validate(artifact_root,output):
    out=Path(output);checks={}
    paper=json.loads((out/'paper_reference_verification.json').read_text());checks['paper72']=paper['cells_verified']==72
    selected=list(csv.DictReader((out/'joint_metric_selection.csv').open()));checks['historical72']=len(selected)==72
    checks['joint_metric_rows']=all(abs(max(float(r['d_acc']),float(r['d_nmi']))-float(r['D_max']))<1e-10 for r in selected if r.get('D_max'))
    if artifact_root:
        store=ArtifactStore(artifact_root)
        for manifest in [out/'artifact_manifest.json',ROOT/'results/subset_search/artifact_manifest.json']:
            if not manifest.exists():continue
            for r in json.loads(manifest.read_text()).get('records',[]):
                if 'object'in r:store.get(r['object'])
        checks['record_objects_available_and_verified']=True
    checks['ok']=all(checks.values());atomic_json(out/'validation.json',checks)
    if not checks['ok']:raise ValueError(checks)
    return checks
