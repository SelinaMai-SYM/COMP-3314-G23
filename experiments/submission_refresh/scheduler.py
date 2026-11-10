"""Two-worker orchestration shared by refresh and subset campaigns."""
from __future__ import annotations
import multiprocessing as mp,os,time,json
from pathlib import Path
from .core import ResourceLedger,atomic_json,THREAD_ENV

def _execute(task,data_root,artifact_root):
    os.environ.update(THREAD_ENV)
    if task['kind']=='subset':
        from experiments.subset_search.runner import run_candidate
        r=run_candidate(task['candidate'],data_root,artifact_root,task['cpu_limit'],task.get('profile',False))
    elif task['kind']=='baseline':
        from .baselines import run_baseline
        r=run_baseline(task,data_root,artifact_root)
    elif task['kind']=='usps':
        from .audit_jobs import run_usps
        r=run_usps(task,data_root,artifact_root)
    elif task['kind']=='graph':
        from .graph_repair import run_graph
        r=run_graph(task,data_root,artifact_root)
    else:raise ValueError(task['kind'])
    r['process_cpu_seconds']=__import__('time').process_time()
    atomic_json(Path(artifact_root)/'task_status'/(task['run_id']+'.json'),r)

def run(tasks,data_root,artifact_root):
    os.environ.update(THREAD_ENV);ledger=ResourceLedger(artifact_root);ctx=mp.get_context('spawn');pending=list(tasks);active=[]
    while pending or active:
        for p,t,start in active[:]:
            if not p.is_alive() or time.monotonic()-start>t['cpu_limit']*2+60:
                if p.is_alive():p.terminate();p.join(3)
                p.join();path=Path(artifact_root)/'task_status'/(t['run_id']+'.json')
                r=json.loads(path.read_text()) if path.exists() else {'status':'KILLED_OR_CRASHED','cpu_seconds':None}
                ledger.finish(t['run_id'],r.get('process_cpu_seconds',r.get('cpu_seconds')),r['status']);active.remove((p,t,start));print('FINISHED',t['run_id'],r['status'],flush=True)
        while pending and len(active)<2:
            t=pending[0];path=Path(artifact_root)/'task_status'/(t['run_id']+'.json')
            if path.exists():
                previous=json.loads(path.read_text())
                if t['kind']=='subset':
                    from experiments.subset_search.runner import scientific_cache_identity
                    expected=scientific_cache_identity(t['candidate'],data_root,profile=t.get('profile',False))
                    if previous.get('cache_identity')!=expected:
                        raise ValueError('existing subset execution identity differs; preserve it and use a new run ID/artifact root')
                pending.pop(0);continue
            if not ledger.reserve(t['run_id'],t['cpu_limit'],t.get('phase','experiment')):break
            pending.pop(0);p=ctx.Process(target=_execute,args=(t,str(data_root),str(artifact_root)));p.start();active.append((p,t,time.monotonic()));print('START',t['run_id'],flush=True)
        if pending and not active:break
        atomic_json(Path(artifact_root)/'queues'/(__import__('hashlib').sha256(str([t['run_id'] for t in tasks]).encode()).hexdigest()[:20]+'.json'),{'pending':[t['run_id'] for t in pending],'active':[{'run_id':t['run_id'],'pid':p.pid} for p,t,_ in active],'updated_unix':time.time()})
        if active:time.sleep(.5)
    return {'not_launched':[t['run_id'] for t in pending],'ledger':ledger.state()}
