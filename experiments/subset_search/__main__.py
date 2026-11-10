from __future__ import annotations
import argparse,json
from pathlib import Path
from experiments.submission_refresh.core import atomic_json,identity

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['catalogue','profile','freeze','run','aggregate','confirm']);p.add_argument('--config',default='configs/subset_search/protocol.yaml');p.add_argument('--data-root');p.add_argument('--artifact-root',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--output',default='results/subset_search');p.add_argument('--candidates',nargs='*');p.add_argument('--cohort',default='configs/subset_search/executable_cohort.json');args=p.parse_args()
    import yaml
    protocol=yaml.safe_load(Path(args.config).read_text())
    if protocol.get('version')!='subset-search-20261110-v1' or list(map(float,protocol.get('gamma_nominal',[])))!=[1e-6,1e-3,1.,1e3,1e6] or protocol.get('solver',{}).get('max_iter')!=300:
        raise ValueError('config does not match the preregistered historical-style protocol')
    if args.phase=='catalogue':
        from .catalogue import build_catalogue
        build_catalogue(Path(args.data_root),Path(args.output));return
    cat=json.loads(Path(args.output,'candidate_catalogue.json').read_text());candidates=cat['candidates']
    if args.phase=='freeze':
        cohort=json.loads(Path(args.cohort).read_text())
        from experiments.submission_refresh.core import digest
        if cohort['catalogue_sha256']!=digest(Path(args.output)/'candidate_catalogue.json'):raise ValueError('frozen cohort catalogue mismatch')
        print(json.dumps({'frozen_candidate_count':len(cohort['candidate_ids']),'cohort':args.cohort,'score_based_changes_allowed':False}));return
    if args.phase=='profile':
        if not args.candidates:raise ValueError('explicit candidate IDs required for blind profile')
        chosen=[c for c in candidates if c['candidate_id'] in args.candidates]
        tasks=[{'run_id':'profile-'+identity(c)[:20],'kind':'subset','candidate':c,'profile':True,'cpu_limit':1800,'phase':'profile'} for c in chosen]
    elif args.phase=='run':
        cohort=json.loads(Path(args.cohort).read_text());chosen=[c for c in candidates if c['candidate_id'] in cohort['candidate_ids']]
        tasks=[{'run_id':'subset-'+identity(c)[:20],'kind':'subset','candidate':c,'cpu_limit':cohort.get('per_candidate_limits',{}).get(c['candidate_id'],cohort['cpu_limit_per_candidate']),'phase':'subset'} for c in chosen]
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
