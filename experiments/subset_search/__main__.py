from __future__ import annotations
import argparse,json
from pathlib import Path
from experiments.submission_refresh.core import atomic_json,identity
from experiments.submission_refresh.config_contract import require_frozen_config,require_cohort,require_profile_ids

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['catalogue','profile','freeze','run','aggregate','confirm','complete-failed']);p.add_argument('--config',default='configs/subset_search/protocol.yaml');p.add_argument('--data-root');p.add_argument('--artifact-root',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--output',default='results/subset_search');p.add_argument('--candidates',nargs='*');p.add_argument('--cohort',default='configs/subset_search/executable_cohort.json');args=p.parse_args()
    require_frozen_config(args.config,'subset')
    if args.phase=='catalogue':
        from .catalogue import build_catalogue
        build_catalogue(Path(args.data_root),Path(args.output));return
    cat=json.loads(Path(args.output,'candidate_catalogue.json').read_text());candidates=cat['candidates']
    if args.phase=='freeze':
        cohort=json.loads(Path(args.cohort).read_text())
        require_cohort(cohort,cat,Path(args.output)/'candidate_catalogue.json',allow_empty=True)
        print(json.dumps({'frozen_candidate_count':len(cohort['candidate_ids']),'cohort':args.cohort,'score_based_changes_allowed':False}));return
    if args.phase=='profile':
        if not args.candidates:raise ValueError('explicit candidate IDs required for blind profile')
        require_profile_ids(args.candidates,cat)
        chosen=[c for c in candidates if c['candidate_id'] in args.candidates]
        tasks=[{'run_id':'profile-'+identity(c)[:20],'kind':'subset','candidate':c,'profile':True,'cpu_limit':1800,'phase':'profile'} for c in chosen]
    elif args.phase=='run':
        cohort=json.loads(Path(args.cohort).read_text());require_cohort(cohort,cat,Path(args.output)/'candidate_catalogue.json')
        chosen=[c for c in candidates if c['candidate_id'] in cohort['candidate_ids']]
        order_path=Path(args.cohort).with_name(Path(args.cohort).stem+'_order.json')
        if order_path.exists():
            order=json.loads(order_path.read_text())['candidate_ids']
            if set(order)!=set(cohort['candidate_ids']) or len(order)!=len(set(order)):raise ValueError('execution order does not match frozen cohort')
            positions={cid:i for i,cid in enumerate(order)};chosen.sort(key=lambda c:positions[c['candidate_id']])
        tasks=[{'run_id':'subset-'+identity(c)[:20],'kind':'subset','candidate':c,'cpu_limit':cohort.get('per_candidate_limits',{}).get(c['candidate_id'],cohort['cpu_limit_per_candidate']),'phase':'subset'} for c in chosen]
    elif args.phase=='complete-failed':
        cohort=json.loads(Path(args.cohort).read_text());require_cohort(cohort,cat,Path(args.output)/'candidate_catalogue.json')
        from experiments.submission_refresh.core import ArtifactStore
        from .complete_failed import _cpu_used
        store=ArtifactStore(args.artifact_root);tasks=[]
        for c in candidates:
            if c['candidate_id'] not in cohort['candidate_ids']:continue
            folder=store.root/'subset'/c['candidate_id'];statuspath=folder/'status.json'
            if not statuspath.exists():continue
            status=json.loads(statuspath.read_text())
            if status.get('status')!='FAILED' or not (folder/'representation.json').exists():continue
            cap=cohort.get('per_candidate_limits',{}).get(c['candidate_id'],cohort['cpu_limit_per_candidate'])
            used=_cpu_used(store,c,status)
            for previous in (folder/'completion_attempts').glob('*.json'):
                prior=json.loads(previous.read_text());used+=prior.get('process_cpu_seconds',prior.get('cpu_seconds',0))
            remaining=cap-used
            if remaining<=2:continue
            rid='complete-'+identity({'candidate':c,'original_status':status,'controller_version':1})[:20]
            tasks.append({'run_id':rid,'kind':'subset_completion','phase':'subset','post_primary':True,'candidate':c,'cpu_limit':remaining})
        atomic_json(Path(args.output)/'completion_queue.json',{'reason':'Same predeclared grid, independent missing points after non-timeout failures; no failed point retry, no score-driven additions','tasks':tasks})
    elif args.phase=='aggregate':
        from .aggregate import aggregate
        aggregate(args.artifact_root,args.output);return
    elif args.phase=='confirm':
        from .aggregate import confirm
        confirm(args.artifact_root,args.output);return
    else:raise ValueError('freeze writes a concrete preregistered cohort using blinded profile records; see campaign README')
    from experiments.submission_refresh.scheduler import run
    out=run(tasks,args.data_root,args.artifact_root);atomic_json(Path(args.output)/('profile_usage.json' if args.phase=='profile' else 'resource_usage.json'),out)
if __name__=='__main__':main()
