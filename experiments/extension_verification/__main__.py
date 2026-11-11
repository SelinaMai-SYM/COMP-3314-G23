"""Registered independent refinement experiments and data-free release rebuilds."""
from __future__ import annotations
import argparse,json,os,sys,unittest
from pathlib import Path
from experiments.submission_refresh.core import ROOT,atomic_json,identity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['freeze','verify','run','diagnostics','report','rebuild'])
    parser.add_argument('--config',default=str(ROOT/'configs/extension_verification/protocol.yaml'))
    parser.add_argument('--data-root');parser.add_argument('--artifact-root');parser.add_argument('--output');parser.add_argument('--release-manifest');parser.add_argument('--resume',action='store_true')
    parser.add_argument('--phase',default='all',choices=['all','e1','e2_gate','e2','e3_gate','e3','controls'])
    parser.add_argument('--_execute',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.command=='rebuild':
        if not args.release_manifest or not args.output:parser.error('rebuild requires --release-manifest and --output')
        from .reporting import rebuild
        result=rebuild(args.release_manifest,args.output);print(json.dumps({'rebuilt':True,'trials':len(result['trials'])}));return
    if not args.artifact_root:parser.error('--artifact-root is required')
    # Heavy setup and release work use the same native CPU ledger as fitting.
    if args.command in ['freeze','verify','diagnostics','report'] and not args._execute:
        from .resources import run_command
        root=Path(args.artifact_root);folder=root/'command_jobs';ordinal=1
        while (folder/(args.command+'-'+str(ordinal))).exists():ordinal+=1
        limit={'freeze':3600,'verify':300,'diagnostics':1800,'report':1800}[args.command]
        record=run_command(root,args.command+'-'+str(ordinal),[sys.executable,'-m','experiments.extension_verification',*sys.argv[1:],'--_execute'],cpu_limit=limit,wall_limit=2*limit+120,phase='aggregation',cwd=ROOT)
        print(json.dumps(record));
        if record['status']!='COMPLETED':raise SystemExit(1)
        return
    if args.command=='freeze':
        if not args.data_root:parser.error('freeze requires --data-root')
        from .inputs import freeze
        lock=freeze(args.config,args.data_root,args.artifact_root);print(json.dumps({'input_count':len(lock['datasets']),'source_fingerprint':lock['source_fingerprint']}))
    elif args.command=='verify':
        from .inputs import source_files
        import pytest
        class Count:
            tests=0
            def pytest_collection_finish(self,session):self.tests=len(session.items)
        count=Count();code=pytest.main([str(ROOT/'tests/extension_verification'),'-q'],plugins=[count])
        atomic_json(Path(args.artifact_root)/'verification.json',{'passed':code==0,'tests':count.tests,'pytest_exit_code':int(code),'source_fingerprint':identity(source_files()),'independent_reference':'CVXPY / CLARABEL and analytic small graphs'})
        if code:raise SystemExit(code)
    elif args.command=='run':
        from .campaign import run
        result=run(args.config,args.artifact_root,args.phase);print(json.dumps(result))
    elif args.command=='diagnostics':
        from .diagnostics import compute
        result=compute(args.config,args.artifact_root);print(json.dumps({'saved_points':len(result['points'])}))
    elif args.command=='report':
        from .reporting import report
        result=report(args.config,args.artifact_root,args.output or ROOT/'results/extension_verification');print(json.dumps({'points':len(result['metrics'])//2,'trials':len(result['trials'])}))

if __name__=='__main__':main()
