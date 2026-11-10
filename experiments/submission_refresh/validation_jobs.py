"""Run isolated validation commands through the shared two-worker scheduler.

The scheduler reserves resources. This handler never starts another worker pool
and writes logs, command output, and rebuild products outside the checkout.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
from .core import ROOT, THREAD_ENV, atomic_json, digest
from experiments.subset_search.runner import source_record


def _scientific_inventory():
    """Detect source/configuration changes while a command is being checked."""
    prefixes=['SSC_method','baselines','benchmarks','method_extension','experiments','configs']
    inventory={}
    for prefix in prefixes:
        for path in sorted((ROOT/prefix).rglob('*')):
            if path.is_file() and path.suffix in {'.py','.yaml','.yml','.json','.toml'}:
                if 'data' not in path.parts and '__pycache__' not in path.parts:
                    inventory[str(path.relative_to(ROOT))]=digest(path)
    for name in ['pyproject.toml','requirements.txt','environment/requirements.lock.txt']:
        path=ROOT/name
        if path.is_file():inventory[name]=digest(path)
    return inventory


def _cpu_time(text):
    # POSIX ps formats CPU time as [[dd-]hh:]mm:ss[.fraction].
    value=text.strip();days=0
    if '-' in value:
        day,value=value.split('-',1);days=int(day)
    fields=list(map(float,value.split(':')))
    return days*86400+sum(part*60**i for i,part in enumerate(reversed(fields)))


def _group_usage(group):
    """Sample the whole command process group, including live descendants."""
    try:
        raw=subprocess.check_output(['ps','-axo','pid=,pgid=,time=,rss='],text=True)
        rows=[line.split() for line in raw.splitlines()]
        selected=[row for row in rows if len(row)==4 and int(row[1])==group]
        return sum(_cpu_time(row[2]) for row in selected),sum(int(row[3])*1024 for row in selected)
    except (OSError,ValueError,subprocess.SubprocessError):return None,None


def _stop_group(process):
    if process.poll() is not None:return
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait()


def run_validation(task,data_root,artifact_root):
    """Execute one argv-list command and return measured CPU including children.

    Supported placeholders are {python}, {repo_root}, {data_root},
    {artifact_root}, and {validation_dir}. No shell expansion is performed.
    A source/configuration change during validation invalidates the check; it
    is reported as an observed concurrent change, not attributed to the child.
    """
    start=time.perf_counter();cpu_start=time.process_time()
    children_start=resource.getrusage(resource.RUSAGE_CHILDREN)
    run_id=task['run_id']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',run_id):raise ValueError('invalid validation run ID')
    artifact_root=Path(artifact_root).resolve()
    if artifact_root==ROOT or ROOT in artifact_root.parents:
        raise ValueError('validation artifacts must be outside the checkout')
    cpu_limit=float(task.get('cpu_limit',900));wall_limit=float(task.get('wall_limit',1800))
    if not 0<cpu_limit<=900 or not 0<wall_limit<=1800:
        raise ValueError('validation limits exceed the frozen per-check maximum')
    command=task.get('command')
    if not isinstance(command,list) or not command or any(not isinstance(part,str) for part in command):
        raise ValueError('validation command must be a nonempty string argv list')
    folder=artifact_root/'validation';folder.mkdir(parents=True,exist_ok=True)
    validation_dir=folder/run_id;validation_dir.mkdir(parents=True,exist_ok=True)
    substitutions={'python':sys.executable,'repo_root':str(ROOT),'data_root':str(data_root),
                   'artifact_root':str(artifact_root),'validation_dir':str(validation_dir)}
    argv=[part.format_map(substitutions) for part in command]
    log_path=folder/(run_id+'.log');record_path=folder/(run_id+'.json')
    environment=os.environ.copy();environment.update(THREAD_ENV)
    # The no-data checks must not inherit an old checkout or data-root override.
    environment.pop('PYTHONPATH',None);environment.pop('COMP3314_DATA_ROOT',None)
    environment['PYTHONDONTWRITEBYTECODE']='1'
    environment['PYTEST_ADDOPTS']='-p no:cacheprovider'
    environment['MPLBACKEND']='Agg'
    result={'task':task,'run_id':run_id,'status':'RUNNING','command':argv,'cwd':str(ROOT),
            'log_path':str(log_path),'outputs_directory':str(validation_dir),
            'environment_overrides':{**THREAD_ENV,'PYTHONDONTWRITEBYTECODE':'1','PYTEST_ADDOPTS':'-p no:cacheprovider','MPLBACKEND':'Agg'},
            'cleared_environment_keys':['PYTHONPATH','COMP3314_DATA_ROOT'],
            'cpu_limit':cpu_limit,'wall_limit':wall_limit,'exit_code':None}
    process=None;max_rss=0;sampled_cpu=0.;stop_reason=None
    before=_scientific_inventory();result['source']=source_record()
    result['source_inventory_sha256']=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
    def child_limits():
        # Leave headroom for this handler, sampling, and command startup.
        allocation=max(1,int(math.floor(cpu_limit-10)))
        resource.setrlimit(resource.RLIMIT_CPU,(allocation,allocation+1))
    try:
        with log_path.open('w') as log:
            log.write(json.dumps({'command':argv,'cwd':str(ROOT),'task':task},sort_keys=True)+'\n')
            log.flush()
            process=subprocess.Popen(argv,cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT,
                                     start_new_session=True,preexec_fn=child_limits)
            while process.poll() is None:
                group_cpu,rss=_group_usage(process.pid)
                if group_cpu is not None:sampled_cpu=max(sampled_cpu,group_cpu)
                if rss is not None:max_rss=max(max_rss,rss)
                if time.perf_counter()-start>=wall_limit:stop_reason='WALL_LIMIT';_stop_group(process);break
                if sampled_cpu+time.process_time()-cpu_start>=max(1.,cpu_limit-5):
                    stop_reason='CPU_LIMIT';_stop_group(process);break
                time.sleep(.25)
            result['exit_code']=process.wait()
            if result['exit_code'] in [-signal.SIGXCPU,-signal.SIGKILL] and stop_reason is None:
                stop_reason='CPU_LIMIT_OR_EXTERNAL_SIGNAL'
            result['stop_reason']=stop_reason
            result['status']='TIMEOUT' if stop_reason else 'COMPLETED' if result['exit_code']==0 else 'FAILED'
    except BaseException as exc:
        if process is not None:_stop_group(process)
        result.update(status='FAILED',error=repr(exc))
        if process is not None:result['exit_code']=process.returncode
    finally:
        after=_scientific_inventory()
        changed=sorted(key for key in before.keys()|after.keys() if before.get(key)!=after.get(key))
        result['scientific_source_unchanged']=not changed
        result['source_or_config_paths_changed_during_check']=changed
        if changed and result['status']=='COMPLETED':result['status']='SOURCE_CHANGED_DURING_VALIDATION'
        children_end=resource.getrusage(resource.RUSAGE_CHILDREN)
        child_cpu=(children_end.ru_utime+children_end.ru_stime-children_start.ru_utime-children_start.ru_stime)
        own_elapsed=time.process_time()-cpu_start
        result.update(own_handler_cpu_seconds=own_elapsed,child_cpu_seconds=child_cpu,
            cpu_seconds=own_elapsed+child_cpu,
            process_cpu_seconds=time.process_time()+child_cpu,
            cpu_charge_definition='whole scheduler worker process CPU plus measured RUSAGE_CHILDREN delta; includes command and sampling children',
            wall_seconds=time.perf_counter()-start,max_sampled_command_group_rss_bytes=max_rss,
            max_sampled_command_group_cpu_seconds=sampled_cpu,
            peak_worker_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            validation_passed=bool(result['status']=='COMPLETED' and result['exit_code']==0 and not changed))
        if log_path.exists():result['log_sha256']=digest(log_path)
        atomic_json(record_path,result)
    return result
