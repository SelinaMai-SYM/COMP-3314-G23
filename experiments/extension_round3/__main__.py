import argparse
from .common import CONFIG


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run','evaluate','report','rebuild']);p.add_argument('--config',default=str(CONFIG));p.add_argument('--data-root');p.add_argument('--artifact-root');p.add_argument('--input-artifact-root');p.add_argument('--phase',default='all');p.add_argument('--resume',action='store_true');p.add_argument('--output');p.add_argument('--release-manifest');a=p.parse_args()
    if a.command=='freeze':
        from .freeze import freeze
        freeze(a.config,a.data_root,a.artifact_root,a.input_artifact_root)
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
        rebuild(a.release_manifest,a.output)
if __name__=='__main__':main()
