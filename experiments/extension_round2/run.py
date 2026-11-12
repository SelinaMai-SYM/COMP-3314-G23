"""Frozen, resumable and wall-bounded SSC extension study."""
from __future__ import annotations
import argparse,json,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from .common import *


def invoke(task,args,cpu_limit,phase):
    from experiments.extension_verification.resources import run_command
    root=Path(args.artifact_root);initialize_ledger(root);task={**task,'cpu_allowance':cpu_limit};key=identity(task);taskfile=root/'tasks'/f'{key}.json';atomic_json(taskfile,task)
    ordinal=1
    while (root/'command_jobs'/f'{key}-{ordinal}').exists():
        old=load_record(root/'command_jobs'/f'{key}-{ordinal}'/'status.json')
        if old and old['status']=='COMPLETED':return old
        ordinal+=1
    if remaining_wall(root)<15:return {'status':'UNRUN_DEADLINE','task':task}
    command=[sys.executable,'-m','experiments.extension_round2.worker','--task',str(taskfile),'--config',str(args.config),'--artifact-root',str(root)]
    # A distinct controller process owns native accounting for each worker.
    argv=[sys.executable,'-m','experiments.extension_verification.resources','--artifact-root',str(root),'--run-id',f'{key}-{ordinal}','--cpu-limit',str(cpu_limit),'--wall-limit',str(min(2*cpu_limit+120,remaining_wall(root))),'--phase',phase,'--cwd',str(ROOT),'--',*command]
    while True:
        value=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);receipt=root/'command_jobs'/f'{key}-{ordinal}'/'status.json'
        if receipt.exists():return load_record(receipt)
        if remaining_wall(root)<15:return {'status':'UNRUN_DEADLINE','task':task}
        ledger=ResourceLedger(root).state()
        if not ledger['active']:return {'status':'UNRUN_RESOURCE_LIMIT','task':task,'detail':value.stdout[-1200:]}
        time.sleep(.5)


def batch(tasks,args):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(invoke,t,args,cpu,phase):(t,phase) for t,cpu,phase in tasks}
        for future in as_completed(futures):
            task,phase=futures[future]
            try:result=future.result()
            except Exception as error:result={'status':'FAILED_CONTROLLER','error':repr(error)}
            atomic_json(Path(args.artifact_root)/'task_outcomes'/f'{identity(task)}.json',{'task':task,'phase':phase,'result':result});print('TASK',task['benchmark'],task['kind'],task.get('method',''),task.get('variant','default'),result['status'],flush=True)


def path_phase(task):return 'path|'+task['benchmark']+'|'+task['method']+'|'+task.get('variant','default')
def path_budget(task,root,control=False):
    phase=path_phase(task);used=sum(e['charged_cpu_seconds'] for e in ResourceLedger(root).state()['entries'] if e['phase']==phase)
    return max(0.,(600 if control else 1800)-used)

def evaluate(args):
    root=Path(args.artifact_root);tasks=[]
    for path in sorted((root/'endpoints').glob('*.json')):
        row=load_record(path)
        if row.get('result') and not (root/'evaluations'/path.name).exists():tasks.append(({'kind':'evaluate','benchmark':row['benchmark'],'endpoint':str(path)},600,'rounding'))
    batch(tasks,args)

def execute(args):
    root=Path(args.artifact_root);initialize_ledger(root)
    if args.phase=='freeze':
        from experiments.extension_verification.resources import run_command
        command=[sys.executable,'-m','experiments.extension_round2.run','--phase','freeze-execute','--config',str(args.config),'--data-root',str(args.data_root),'--artifact-root',str(root)]
        run_command(root,'freeze-inputs',command,cpu_limit=3600,wall_limit=min(7300,remaining_wall(root)),phase='aggregation',cwd=ROOT);return
    if args.phase=='freeze-execute':
        from .inputs import freeze
        freeze(args.config,args.data_root,root);return
    if args.phase=='verify':
        from experiments.extension_verification.resources import run_command
        ordinal=1
        while (root/'command_jobs'/f'verify-{ordinal}').exists():ordinal+=1
        program='import os,sys,pytest;os.environ["COMP3314_ROUND2_ARTIFACT_ROOT"]=sys.argv[1];raise SystemExit(pytest.main(["-q","tests/extension_round2","--junitxml",sys.argv[2]]))'
        try:run_command(root,f'verify-{ordinal}',[sys.executable,'-c',program,str(root),str(root/f'verification-{ordinal}.xml')],cpu_limit=600,wall_limit=min(1320,remaining_wall(root)),phase='validation',cwd=ROOT)
        except RuntimeError:atomic_json(root/'verification.json',{'passed':False,'source_files':source_files()});raise
        atomic_json(root/'verification.json',{'passed':True,'source_files':source_files(),'environment':environment()});return
    spec,lock,store=locked(root,args.config);verified=load_record(root/'verification.json')
    if not verified or not verified['passed'] or verified['source_files']!=source_files():raise ValueError('Verify exact numerical source before benchmark tasks')
    if args.phase=='primary':
        batch([({'kind':'aux','benchmark':b},600,'auxiliary') for b in ORDER if not (root/'auxiliary'/f'{b}.json').exists()],args)
        batch([({'kind':'graph','benchmark':b,'variant':'default'},600,'graph_QP') for b in ORDER if not (root/'graphs'/f'{b}--default.json').exists()],args)
        tasks=[]
        for method in ['SC','historical','SSC_reference','old_E1_reference',*METHODS]:
            for b in ORDER:
                if method in METHODS:
                    task={'kind':'path','benchmark':b,'method':method,'targets':[.05]};budget=path_budget(task,root)
                    if budget>=30:tasks.append((task,budget,path_phase(task)))
                else:tasks.append(({'kind':method,'benchmark':b,'method':method},600,'reference'))
        batch(tasks,args);atomic_json(root/'primary_attempts_complete.json',{'source_fingerprint':lock['source_fingerprint'],'completed_before_secondary':True});evaluate(args)
    elif args.phase=='secondary':
        if not (root/'primary_attempts_complete.json').exists():raise ValueError('Attempt all-eight primary and references first')
        tasks=[]
        for method in METHODS:
            for b in ORDER:
                task={'kind':'path','benchmark':b,'method':method,'targets':[.02,.10,.20]};budget=path_budget(task,root)
                if budget>=30:tasks.append((task,budget,path_phase(task)))
        batch(tasks,args);evaluate(args)
    elif args.phase=='controls':
        if not (root/'primary_attempts_complete.json').exists():raise ValueError('Attempt primary study first')
        graphs=[({'kind':'graph_controls','benchmark':b},600*(5 if b in ['ORL','YaleB'] else 3),'graph_QP_controls') for b in ORDER];batch(graphs,args)
        tasks=[]
        for b in ORDER:
            for seed in [400,401,402]:tasks.append({'kind':'path','benchmark':b,'method':'E4','variant':f'perm{seed}','targets':[.05]})
        for b in ['ORL','YaleB']:
            for method,name,values in [('E1_v2','eta',[.10,.50]),('E4','beta',[.25,4.]),('E5','alpha',[.25,4.]),('E6','eta_dir',[.25,.75])]:
                for value in values:tasks.append({'kind':'path','benchmark':b,'method':method,'variant':f'{name}{value}','parameters':{} if method=='E4' else {name:value},'targets':[.05]})
        batch([(t,path_budget(t,root,True),path_phase(t)) for t in tasks if path_budget(t,root,True)>=30],args);evaluate(args)
    elif args.phase=='evaluate':evaluate(args)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',required=True,choices=['freeze','freeze-execute','verify','primary','secondary','controls','evaluate']);p.add_argument('--config',type=Path,default=DEFAULT_CONFIG);p.add_argument('--data-root');p.add_argument('--artifact-root',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--all-benchmarks',action='store_true');args=p.parse_args();execute(args)
if __name__=='__main__':main()
