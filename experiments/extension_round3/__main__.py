import argparse,json,sys,time
from pathlib import Path
from .common import CONFIG,ROOT


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run','evaluate','report','rebuild']);p.add_argument('--config',default=str(CONFIG));p.add_argument('--data-root');p.add_argument('--artifact-root');p.add_argument('--input-artifact-root');p.add_argument('--phase',default='all');p.add_argument('--resume',action='store_true');p.add_argument('--output');p.add_argument('--release-manifest');p.add_argument('--figures',action='store_true',help='Regenerate figures during scalar rebuilding');p.add_argument('--inside-budget',action='store_true',help=argparse.SUPPRESS);a=p.parse_args()
    if a.command=='freeze':
        from experiments.submission_refresh.core import atomic_json
        root=Path(a.artifact_root);root.mkdir(parents=True,exist_ok=True)
        if not (root/'resource_ledger.json').exists():atomic_json(root/'resource_ledger.json',{'version':1,'limit_seconds':115200,'reserve_seconds':3600,'max_workers':2,'rss_target_bytes':8*2**30,'entries':[],'active':{}})
        if not (root/'clock.json').exists():
            start=time.time();atomic_json(root/'clock.json',{'start_epoch':start,'deadline_epoch':start+86400,'fit_deadline_epoch':start+82800,'wall_hours':24})
    if a.command in ['freeze','evaluate','report'] and not a.inside_budget:
        from experiments.extension_verification.resources import run_command
        from experiments.submission_refresh.core import ResourceLedger
        state=ResourceLedger(a.artifact_root).state();available=state['limit_seconds']-sum(x['charged_cpu_seconds'] for x in state['entries'])-sum(x['seconds'] for x in state['active'].values());limit=min({'freeze':600,'evaluate':3500,'report':1200}[a.command],available);wall=json.loads((Path(a.artifact_root)/'clock.json').read_text())['deadline_epoch']-time.time()
        if limit<20 or wall<20:raise RuntimeError('round budget exhausted before requested stage')
        run_command(a.artifact_root,'r3-'+a.command+'-'+str(time.time_ns()),[sys.executable,'-m','experiments.extension_round3',*sys.argv[1:],'--inside-budget'],cpu_limit=limit,wall_limit=wall,phase='preparation' if a.command=='freeze' else 'aggregation',cwd=Path.cwd());return
    if a.command=='freeze':
        from .freeze import freeze
        lock=freeze(a.config,a.data_root,a.artifact_root,a.input_artifact_root)
        from .common import digest
        for key,name in [('input_lock_sha256','cohort_lock.json'),('registry_sha256','method_registry.json'),('queue_sha256','experiment_queue.json')]:
            if lock[key]!=digest(ROOT/'configs/extension_round3'/name):raise ValueError('registered input, registry or queue changed')
    elif a.command=='run':
        from .run import execute
        execute(a.artifact_root,a.config,a.input_artifact_root,phase=a.phase,resume=a.resume)
    elif a.command=='evaluate':
        from .evaluate import evaluate
        evaluate(a.config,a.artifact_root)
    elif a.command=='report':
        from .report import build
        build(a.config,a.artifact_root,a.output)
    else:
        from .release import rebuild
        rebuild(a.release_manifest,a.output,plots=a.figures)
if __name__=='__main__':main()
