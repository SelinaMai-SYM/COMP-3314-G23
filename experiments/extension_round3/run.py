"""Finite round-robin scheduler with two single-thread guarded workers."""
from __future__ import annotations
import argparse,concurrent.futures,subprocess,sys,time
from .common import *
from experiments.extension_verification.resources import run_command


def remaining(root,phase='fitting'):
    s=ResourceLedger(root).state();return s['limit_seconds']-sum(x['charged_cpu_seconds'] for x in s['entries'])-sum(x['seconds'] for x in s['active'].values())-(0 if phase in ['validation','aggregation'] else s['reserve_seconds'])


def execute(root,config,input_root,*,phase='all',resume=False):
    spec,lock,store=locked(root,config);assert_fitting_open(root)
    for key,name in [('input_lock_sha256','cohort_lock.json'),('registry_sha256','method_registry.json'),('queue_sha256','experiment_queue.json')]:
        if lock[key]!=digest(ROOT/'configs/extension_round3'/name):raise ValueError('registered input, registry or queue changed')
    tasks=[]
    if phase in ['all','evidence']:
        tasks += [{'kind':'evidence','benchmark':b,'tau_multiplier':1.,'id':f'evidence-{b}-t1'} for b in ORDER if not (store.root/'evidence'/f'{b}__t1.json').exists()]
    def fitting(rows):
        return [dict(r,kind='fit') for r in rows if not profile_path(store,r['id']).exists()]
    q=queue()
    prerequisites=[r for r in q if r['stage']==3 or (phase in ['secondary','optional'] and r['stage']==4)]
    if phase in ['controls','secondary','optional'] and any(not profile_path(store,r['id']).exists() for r in prerequisites):raise RuntimeError('phase prerequisites have not all been attempted')
    stages=[]
    if tasks:stages.append(tasks)
    if phase in ['all','primary']:
        stages.append(fitting([r for r in q if r['stage']==2]));stages.append(fitting([r for r in q if r['stage']==3]))
    if phase in ['all','controls']:
        stages.append(fitting([r for r in q if r['stage']==4 and r['method']!='UNIFORM_GRAPH_ALIAS']));stages.append(fitting([r for r in q if r['method']=='UNIFORM_GRAPH_ALIAS']))
    if phase in ['all','secondary']:
        # Targets of one method/cohort share the same lambda path and caps.
        # Finish each target block before another can read/write that path.
        secondary=[r for r in q if r['stage']==5]
        for rho in dict.fromkeys(r['rho'] for r in secondary):
            stages.append(fitting([r for r in secondary if r['rho']==rho]))
    def launch(task):
        assert_fitting_open(root);is_evidence=task['kind']=='evidence';limit=3600. if is_evidence else 1800.
        if not is_evidence and task['method'] in ['SC','HISTORICAL_IRLS','SSC_REFERENCE','UNIFORM_GRAPH_ALIAS']:limit=180.
        if not is_evidence and task['method'] in registry():
            p=store.root/'paths'/f"{task['benchmark']}__{task['method']}__t{task['tau_multiplier']:g}"/'path.json'
            if p.exists():limit=min(limit,max(20.,1800-read(p)['CPU_seconds']))
        if is_evidence:
            used=sum(e['charged_cpu_seconds'] for e in ResourceLedger(root).state()['entries'] if e['run_id'].startswith('r3-evidence-'+task['benchmark']+'-t'))
            limit=min(limit,max(0.,3600.-used))
        if limit<20:return dict(id=task['id'],status='UNRUN_CUMULATIVE_CAP')
        if remaining(root)<limit:return dict(id=task['id'],status='UNRUN_RESOURCE_RESERVATION')
        runs=[p.name for p in (store.root/'command_jobs').glob('r3-'+task['id']+'-*')];run_id='r3-'+task['id']+'-'+str(len(runs))
        argv=[sys.executable,'-m','experiments.extension_round3.worker',task['kind'],'--artifact-root',str(store.root),'--config',str(config),'--input-artifact-root',str(input_root)]
        if is_evidence:argv+=['--benchmark',task['benchmark'],'--tau-multiplier',str(task['tau_multiplier'])]
        else:argv+=['--profile-id',task['id']]
        wall=min(limit*2+30,read(store.root/'clock.json')['fit_deadline_epoch']-time.time())
        try:
            if wall<15:return dict(id=task['id'],status='UNRUN_WALL_RESERVE')
            subprocess.run([sys.executable,'-m','experiments.extension_verification.resources','--artifact-root',str(store.root),'--run-id',run_id,'--cpu-limit',str(limit),'--wall-limit',str(wall),'--phase','fitting','--cwd',str(ROOT),'--',*argv],check=True,capture_output=True,text=True)
            return dict(id=task['id'],status='FINISHED')
        except Exception as e:
            status=read(store.root/'command_jobs'/run_id/'status.json') if (store.root/'command_jobs'/run_id/'status.json').exists() else {}
            if not is_evidence and not profile_path(store,task['id']).exists():
                record={k:v for k,v in task.items() if k!='kind'};record.update(status=status.get('status','WORKER_FAILURE'),qualified=False,certified=False,failure_type=type(e).__name__)
                # Retain a completed finite path point if a later fit was stopped.
                path=store.root/'paths'/f"{task['benchmark']}__{task['method']}__t{task['tau_multiplier']:g}"/'path.json'
                if path.exists() and read(path)['points']:
                    pts=read(path)['points'];p=min(pts,key=lambda p:abs(p['certificate']['movement']-task['rho']));record.update(result=p['result'],certificate=p['certificate'],lambda_value=p['lambda'],**{'lambda':p['lambda']})
                atomic_json(profile_path(store,task['id']),record)
            return dict(id=task['id'],status=status.get('status','WORKER_FAILURE'))
    for stage in stages:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for result in pool.map(launch,stage):
                with (store.root/'scheduler_log.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
                print(json.dumps(result),flush=True)
        if time.time()>=read(store.root/'clock.json')['fit_deadline_epoch'] or remaining(root)<2000:break
    if phase in ['all','optional']:
        required=[r for r in q if r['stage'] in [3,4]]
        gate=all(profile_path(store,r['id']).exists() and read(profile_path(store,r['id'])).get('qualified') for r in required)
        atomic_json(store.root/'optional_gate.json',{'passed':gate,'rule':spec['execution']['optional_stage6_gate'],'labels_loaded':False})
        if gate:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                for result in pool.map(launch,[{'kind':'evidence','benchmark':b,'tau_multiplier':t,'id':f'evidence-{b}-t{t:g}'} for t in [.25,4.] for b in ['ORL','YaleB']]):print(result,flush=True)
                for result in pool.map(launch,fitting([r for r in q if r['stage']==6])):print(result,flush=True)
    return store.root


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',default=str(CONFIG));p.add_argument('--data-root');p.add_argument('--artifact-root',required=True);p.add_argument('--input-artifact-root',required=True);p.add_argument('--phase',choices=['all','evidence','primary','controls','secondary','optional'],default='all');p.add_argument('--resume',action='store_true');a=p.parse_args();execute(a.artifact_root,a.config,a.input_artifact_root,phase=a.phase,resume=a.resume)
if __name__=='__main__':main()
