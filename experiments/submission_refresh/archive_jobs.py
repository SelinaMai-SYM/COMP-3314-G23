"""Charge final scientific export and recovery to the existing shared ledger.

This controller calls the existing atomic archive implementation unchanged. It
does not start a subprocess pool, fit models, or create another scientific store.
"""
from __future__ import annotations
import fcntl
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import resource
import signal
import subprocess
import sys
import time
import traceback
from . import export_artifacts
from .core import ROOT,ResourceLedger,atomic_json,digest,identity,install_cpu_limit

MANIFESTS=('results/submission_refresh/artifact_manifest.json',
           'results/subset_search/artifact_manifest.json')
CPU_MAX={'export':3600.,'recover':1800.}
CLEANUP_MARGIN=10.


def _filename(value,kind):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',value):
        raise ValueError(kind+' must be one safe relative filename')
    if kind=='archive_name' and not value.endswith('.tar.gz'):
        raise ValueError('archive_name must end in .tar.gz')
    return value


def _beside(root,name):
    target=root.parent/name
    if target.is_symlink() or target.resolve().parent!=root.parent or target.resolve()==root:
        raise ValueError('archive outputs must be distinct siblings of the artifact root')
    return target


def _child_cpu(start):
    current=resource.getrusage(resource.RUSAGE_CHILDREN)
    return max(0.,current.ru_utime+current.ru_stime-start.ru_utime-start.ru_stime)


class _Budget:
    """Bound worker CPU plus reaped Git children within one reservation."""
    def __init__(self,cpu_limit,wall_limit,start,children_start):
        self.cpu_limit=cpu_limit;self.wall_limit=wall_limit;self.start=start;self.children_start=children_start

    def remaining_cpu(self):
        return self.cpu_limit-time.process_time()-_child_cpu(self.children_start)-CLEANUP_MARGIN

    def remaining_wall(self):return self.wall_limit-(time.perf_counter()-self.start)

    def arm(self):
        remaining=self.remaining_cpu()
        if remaining<=0:raise TimeoutError('archive CPU allocation exhausted during preflight')
        install_cpu_limit(remaining)
        return remaining


def _git(*arguments,budget):
    remaining=budget.arm();wall=budget.remaining_wall()-2
    if remaining<2 or wall<=0:raise TimeoutError('archive Git check has no remaining bounded allocation')
    # These local read-only commands do not need hooks, filesystem monitors or
    # submodule helpers. The hard child CPU limit fits the remaining allocation.
    allocation=int(math.floor(remaining-1))
    def child_limits():
        _,inherited_hard=resource.getrlimit(resource.RLIMIT_CPU)
        hard=allocation+1 if inherited_hard==resource.RLIM_INFINITY else min(allocation+1,inherited_hard)
        resource.setrlimit(resource.RLIMIT_CPU,(min(allocation,hard),hard))
    try:
        completed=subprocess.run(['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null',*arguments],
            cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            timeout=wall,preexec_fn=child_limits,check=False)
        if completed.returncode in [-signal.SIGXCPU,-signal.SIGKILL]:
            raise TimeoutError('archive Git check exhausted its child CPU allocation')
        if completed.returncode:raise ValueError('archive Git check failed: '+completed.stdout.strip())
        return completed.stdout.strip()
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError('archive Git check exhausted its wall allocation') from exc
    finally:
        # Reap/charge each child before granting the worker another interval.
        budget.arm()


def _committed_manifests(budget):
    """Require the exact two manifests used by export to exist in HEAD."""
    commit=_git('rev-parse','HEAD',budget=budget);records=[]
    for name in MANIFESTS:
        path=ROOT/name
        if not path.is_file():raise ValueError('final committed artifact manifest is missing: '+name)
        committed=_git('rev-parse','--verify','HEAD:'+name,budget=budget)
        actual=_git('hash-object',str(path),budget=budget)
        if committed!=actual:raise ValueError('artifact manifest differs from its committed bytes: '+name)
        records.append({'path':name,'sha256':digest(path),'bytes':path.stat().st_size,'git_blob':committed})
    return commit,records


def _source(record,budget):
    names=['archive_jobs.py','export_artifacts.py','core.py','scheduler.py']
    files={'experiments/submission_refresh/'+name:digest(Path(__file__).with_name(name)) for name in names}
    versions={}
    for package in ['numpy','scipy']:
        try:versions[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:versions[package]=None
    record.update(files=files,implementation_hash=identity(files),
        environment={'python':sys.version,'platform':platform.platform(),'packages':versions})
    record['source_commit']=_git('rev-parse','HEAD',budget=budget)
    record['working_tree_dirty']=bool(_git('status','--porcelain','--ignore-submodules=all',budget=budget))
    record['inspection_status']='COMPLETE'


def _reservation(root,task,cpu_limit):
    state=ResourceLedger(root).state();own=state['active'].get(task['run_id'])
    if own is None or own.get('phase')!='aggregation' or float(own['seconds'])!=cpu_limit:
        raise ValueError('archive jobs require their exact shared aggregation-phase reservation')
    others=sorted(set(state['active'])-{task['run_id']})
    if others:raise ValueError('finish all other shared jobs before final archiving: '+','.join(others))


def _dependency(task,root,archive,manifests):
    dependency=_filename(task.get('depends_on'),'depends_on')
    path=root/'archive_jobs'/(dependency+'.json')
    if not path.is_file() or path.is_symlink():raise ValueError('completed export dependency is unavailable')
    record=json.loads(path.read_text());result=record.get('archive',{})
    if record.get('schema')!='shared-archive-job-v1' or record.get('run_id')!=dependency or record.get('operation')!='export' or record.get('status')!='COMPLETED' or result.get('verified') is not True:
        raise ValueError('export dependency is not a completed verified export')
    if record.get('archive_name')!=archive.name or record.get('input_manifests')!=manifests:
        raise ValueError('export dependency does not match archive or committed manifests')
    sidecar=archive.with_suffix(archive.suffix+'.json')
    if not archive.is_file() or not sidecar.is_file():raise ValueError('export archive or sidecar is missing')
    if sidecar.is_symlink() or archive.is_symlink():raise ValueError('archive dependency must not use symlinks')
    if archive.stat().st_size!=result.get('bytes') or digest(archive)!=result.get('sha256'):
        raise ValueError('export archive hash or size differs from completed dependency')
    if digest(sidecar)!=record.get('export_sidecar_sha256'):
        raise ValueError('export sidecar differs from completed dependency')
    metadata=json.loads(sidecar.read_text())
    if any(metadata.get(key)!=result.get(key) for key in ['sha256','bytes','verified','object_count','extra_files','export_manifest_object']):
        raise ValueError('export sidecar metadata conflicts with completed dependency')
    return {'run_id':dependency,'record':'archive_jobs/'+path.name,'record_sha256':digest(path),
        'archive_sha256':result['sha256'],'export_sidecar_sha256':digest(sidecar)}


def run_archive(task,data_root,artifact_root):
    """Run one export or dependent recovery; the caller owns its reservation.

    Output names are basenames beside artifact_root. Recovery is a separate
    queue and requires a completed export record with unchanged archive bytes.
    Both operations reject existing outputs. A retry needs a new run ID and,
    whenever an output was published, a new destination name.
    """
    del data_root  # Archive operations do not inspect or load the private data.
    start=time.perf_counter();cpu_start=time.process_time()
    children_start=resource.getrusage(resource.RUSAGE_CHILDREN)
    run_id=_filename(task.get('run_id'),'run_id');root=Path(artifact_root).resolve()
    if root==ROOT or ROOT in root.parents:raise ValueError('scientific archives must stay outside the checkout')
    folder=root/'archive_jobs'
    if folder.is_symlink():raise ValueError('archive job records must remain inside the artifact root')
    folder.mkdir(parents=True,exist_ok=True)
    record_path=folder/(run_id+'.json');claim=folder/(run_id+'.claim')
    if record_path.exists() or record_path.is_symlink():raise ValueError('archive job record already exists; use a new run ID')
    descriptor=os.open(claim,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as stream:stream.write(run_id+'\n')
    result={'schema':'shared-archive-job-v1','task':task,'run_id':run_id,'status':'RUNNING',
        'operation':task.get('operation'),'archive_name':task.get('archive_name'),
        'recovery_name':task.get('recovery_name'),'uses_shared_ledger':True,
        'no_scientific_fit_or_data_load':True,'source':{'inspection_status':'PENDING_GUARDED_PREFLIGHT'}}
    atomic_json(record_path,result)
    previous_alarm=signal.getsignal(signal.SIGALRM);previous_prof=signal.getsignal(signal.SIGPROF)
    destination_lock=None;archive=None;export_started=False
    try:
        operation=task.get('operation')
        if task.get('kind')!='archive' or operation not in CPU_MAX:raise ValueError('archive task kind and export/recover operation are required')
        cpu_limit=float(task.get('cpu_limit',CPU_MAX[operation]));wall_limit=float(task.get('wall_limit',2*cpu_limit+15))
        if not math.isfinite(cpu_limit) or not 0<cpu_limit<=CPU_MAX[operation] or task.get('phase')!='aggregation':
            raise ValueError('archive task must use aggregation phase and its bounded CPU allocation')
        if not math.isfinite(wall_limit) or not 0<wall_limit<=2*cpu_limit+30:
            raise ValueError('archive wall limit exceeds the scheduler cleanup headroom')
        # Account for imports and controller startup already charged to this
        # worker, rather than granting a fresh full allocation to compression.
        budget=_Budget(cpu_limit,wall_limit,start,children_start);remaining=budget.arm()
        def wall_exceeded(_signal,_frame):raise TimeoutError('archive wall allocation exhausted')
        remaining_wall=wall_limit-(time.perf_counter()-start)
        if remaining_wall<=0:raise TimeoutError('archive wall allocation exhausted before preflight')
        signal.signal(signal.SIGALRM,wall_exceeded);signal.setitimer(signal.ITIMER_REAL,remaining_wall)
        result.update(cpu_limit=cpu_limit,wall_limit=wall_limit,
            guarded_remaining_cpu_seconds=remaining,guarded_remaining_wall_seconds=remaining_wall,
            cleanup_margin_seconds=CLEANUP_MARGIN)
        _source(result['source'],budget)
        _reservation(root,task,cpu_limit)
        archive=_beside(root,_filename(task.get('archive_name'),'archive_name'))
        # A nonblocking lock prevents concurrent export/recovery controllers
        # from racing even if a second scheduler launches the same destination.
        lock_path=root.parent/('.'+archive.name+'.finalization.lock')
        if lock_path.is_symlink():raise ValueError('archive destination lock must not use a symlink')
        destination_lock=lock_path.open('a+')
        fcntl.flock(destination_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        commit,manifests=_committed_manifests(budget);result.update(tested_commit=commit,input_manifests=manifests)
        if operation=='export':
            sidecar=archive.with_suffix(archive.suffix+'.json')
            if archive.exists() or sidecar.exists() or sidecar.is_symlink():
                raise ValueError('archive or sidecar output already exists; preserve it and use a new filename')
            export_started=True;value=export_artifacts.export(root,archive)
            result['archive']={**value,'path':'../'+archive.name}
            result['export_sidecar_sha256']=digest(archive.with_suffix(archive.suffix+'.json'))
        else:
            recovered=_beside(root,_filename(task.get('recovery_name'),'recovery_name'))
            if recovered==archive or recovered.exists():raise ValueError('recovery output already exists or conflicts with archive')
            result['export_dependency']=_dependency(task,root,archive,manifests)
            export_artifacts.recover(archive,recovered)
            proof=recovered/'RECOVERED_EXPORT.json';summary=json.loads(proof.read_text())
            if summary.get('archive_sha256')!=result['export_dependency']['archive_sha256']:
                raise ValueError('recovered archive identity differs from verified dependency')
            result['recovery']={'path':'../'+recovered.name,'summary':summary,'proof_sha256':digest(proof)}
        _,after=_committed_manifests(budget)
        if after!=manifests:raise ValueError('committed artifact manifest bytes changed during archive operation')
        _reservation(root,task,cpu_limit)
        result['status']='COMPLETED'
    except BaseException as exc:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        # export() publishes the archive before its sidecar. If interrupted in
        # that tiny interval, remove only this attempt's newly created outputs;
        # preflight already established that neither destination existed.
        if export_started and 'archive' not in result:
            try:
                archive.unlink(missing_ok=True)
                archive.with_suffix(archive.suffix+'.json').unlink(missing_ok=True)
            except OSError as cleanup_error:result['cleanup_error']=repr(cleanup_error)
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'FAILED',
            error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGPROF,previous_prof);signal.signal(signal.SIGALRM,previous_alarm)
        if destination_lock is not None:destination_lock.close()
        child_cpu=_child_cpu(children_start)
        own=time.process_time()-cpu_start
        result.update(own_handler_cpu_seconds=own,child_cpu_seconds=child_cpu,cpu_seconds=own+child_cpu,
            process_cpu_seconds=time.process_time()+child_cpu,wall_seconds=time.perf_counter()-start,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
            cpu_charge_definition='whole scheduler worker process CPU plus measured RUSAGE_CHILDREN delta; startup and preflight included',
            output_publication='Existing export/recover implementation validates then publishes atomically; failed jobs do not qualify as recovery dependencies')
        atomic_json(record_path,result)
    return result
