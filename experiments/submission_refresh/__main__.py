from __future__ import annotations
import argparse,json
from pathlib import Path
from .core import atomic_json

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['rebuild','run','aggregate','validate','freeze-evidence','rebuild-evidence']);p.add_argument('--config',default='configs/submission_refresh/campaign.yaml');p.add_argument('--data-root');p.add_argument('--artifact-root');p.add_argument('--resume',action='store_true');p.add_argument('--output',default='results/submission_refresh');p.add_argument('--queue',default='configs/submission_refresh/execution_queue.json');p.add_argument('--release-manifest',default='configs/submission_refresh/evidence_manifest.json');args=p.parse_args()
    import yaml
    protocol=yaml.safe_load(Path(args.config).read_text())
    if protocol.get('max_cpu_core_hours')!=36 or protocol.get('workers')!=2:raise ValueError('resource configuration differs from approved shared allowance')
    if args.phase=='rebuild':
        from .historical import rebuild_joint
        rebuild_joint(args.output)
    elif args.phase=='run':
        if not args.artifact_root or not args.data_root:raise ValueError('explicit data/artifact roots required')
        from .scheduler import run
        tasks=json.loads(Path(args.queue).read_text())['tasks'];atomic_json(Path(args.output)/'resource_usage.json',run(tasks,args.data_root,args.artifact_root))
    elif args.phase=='freeze-evidence':
        from .scalar_evidence import freeze
        freeze(args.artifact_root,args.output)
    elif args.phase=='rebuild-evidence':
        from .scalar_evidence import rebuild
        rebuild(args.release_manifest,args.output)
    elif args.phase=='aggregate':
        from .aggregate import aggregate
        aggregate(args.artifact_root,args.output)
    else:
        from .validation import validate
        validate(args.artifact_root,args.output)
if __name__=='__main__':main()
