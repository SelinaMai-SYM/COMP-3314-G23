"""Bounded commands with one shared CPU ledger and native process accounting."""
from __future__ import annotations
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from experiments.submission_refresh.core import ResourceLedger, atomic_json, THREAD_ENV


def native_usage(pid):
    """Return own CPU, reaped-child CPU and resident bytes, or None."""
    try:
        if sys.platform == 'darwin':
            class Usage(ctypes.Structure):
                _fields_=[('uuid',ctypes.c_uint8*16)]+[(name,ctypes.c_uint64) for name in
                    ['user','system','idle','interrupt','pageins','wired','resident','footprint',
                     'start','exit','child_user','child_system','child_idle','child_interrupt',
                     'child_pageins','child_elapsed','read','written']]
            class Timebase(ctypes.Structure):
                _fields_=[('numer',ctypes.c_uint32),('denom',ctypes.c_uint32)]
            value=Usage();library=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
            if library.proc_pid_rusage(int(pid),2,ctypes.byref(value))!=0:return None
            scale=Timebase();ctypes.CDLL('/usr/lib/libSystem.B.dylib').mach_timebase_info(ctypes.byref(scale))
            unit=scale.numer/scale.denom/1e9
            return ((value.user+value.system)*unit,(value.child_user+value.child_system)*unit,int(value.resident))
        if sys.platform.startswith('linux'):
            raw=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
            hz=os.sysconf('SC_CLK_TCK');page=os.sysconf('SC_PAGE_SIZE')
            return ((int(raw[11])+int(raw[12]))/hz,(int(raw[13])+int(raw[14]))/hz,int(raw[21])*page)
    except (OSError,ValueError,AttributeError):return None
    return None


def _group_usage(group):
    raw=subprocess.check_output(['/bin/ps','-axo','pid=,pgid='],text=True)
    total=0.;rss=0;complete=True
    for line in raw.splitlines():
        pid,pgid=map(int,line.split())
        if pgid!=group:continue
        value=native_usage(pid)
        if value is None:
            try:os.kill(pid,0)
            except ProcessLookupError:continue
            complete=False
        else:total+=value[0]+value[1];rss+=value[2]
    return total,rss,complete


def stop_group(process):
    if process.poll() is not None:return
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait()


def run_command(artifact_root,run_id,argv,*,cpu_limit,wall_limit,phase='validation',cwd=None):
    """Charge startup, monitoring and descendants; unavailable accounting is conservative.

    The ledger reservation is held until all children have been reaped. Linux
    procfs and Darwin rusage use cumulative reaped-child counters, so short-lived
    children are included even when no live sample observed them.
    """
    root=Path(artifact_root).resolve();folder=root/'command_jobs'/run_id
    if folder.exists():raise ValueError('Command identity already exists')
    ledger=ResourceLedger(root);state=ledger.state()
    if any(e['run_id']==run_id for e in state['entries']):raise ValueError('Command already charged')
    if not ledger.reserve(run_id,float(cpu_limit),phase):raise RuntimeError('No shared resource allocation')
    folder.mkdir(parents=True);start=time.perf_counter();initial=native_usage(os.getpid())
    record={'run_id':run_id,'command':argv,'status':'RUNNING','cpu_limit':cpu_limit,
            'wall_limit':wall_limit,'phase':phase,'samples':[],'accounting':'native own/reaped-child CPU; conservative reservation on unavailable terminal counter'}
    process=None;max_rss=0;code=None;reason=None;complete=True;measured=0.
    atomic_json(folder/'status.json',record)
    environment=os.environ.copy();environment.update(THREAD_ENV);environment['PYTHONDONTWRITEBYTECODE']='1';environment['MPLBACKEND']='Agg'
    try:
        with (folder/'command.log').open('w') as output:
            process=subprocess.Popen(argv,cwd=cwd,env=environment,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            while process.poll() is None:
                live,rss,available=_group_usage(process.pid);own=native_usage(os.getpid())
                reaped=0. if own is None or initial is None else max(0.,own[1]-initial[1])
                measured=time.process_time()+reaped+live
                enforcement=measured if available and own is not None else max(measured,(time.perf_counter()-start)*os.cpu_count())
                max_rss=max(max_rss,rss);complete=complete and available
                if len(record['samples'])<3 or time.perf_counter()-start-record['samples'][-1]['wall_seconds']>15:
                    record['samples'].append({'wall_seconds':time.perf_counter()-start,'CPU_seconds':measured,'RSS_bytes':rss,'native_available':available})
                if enforcement>=max(1,float(cpu_limit)-10):reason='CPU_LIMIT'
                if rss>4*2**30:reason='MEMORY_LIMIT'
                if time.perf_counter()-start>=wall_limit:reason='WALL_LIMIT'
                if reason:stop_group(process);break
                time.sleep(.5)
            code=process.wait()
        record['status']='COMPLETED' if code==0 and reason is None else 'FAILED'
    except BaseException as exc:
        if process is not None:stop_group(process)
        record.update(status='FAILED',error=repr(exc))
    finally:
        terminal=native_usage(os.getpid())
        reliable=initial is not None and terminal is not None
        actual=time.process_time()+max(0.,terminal[1]-initial[1]) if reliable else measured
        charged=actual if reliable else max(float(cpu_limit),actual)
        record.update(exit_code=code,stop_reason=reason,CPU_seconds=actual,charged_CPU_seconds=charged,
                      terminal_accounting_complete=reliable,live_samples_complete=complete,
                      max_sampled_RSS_bytes=max_rss,wall_seconds=time.perf_counter()-start)
        atomic_json(folder/'status.json',record);ledger.finish(run_id,charged,record['status'])
    if record['status']!='COMPLETED':raise RuntimeError(f'{run_id}: see {folder / "command.log"}')
    return record


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-root',required=True);parser.add_argument('--run-id',required=True)
    parser.add_argument('--cpu-limit',type=float,required=True);parser.add_argument('--wall-limit',type=float,required=True)
    parser.add_argument('--phase',default='experiment');parser.add_argument('--cwd');parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command:parser.error('an explicit command is required')
    result=run_command(args.artifact_root,args.run_id,command,cpu_limit=args.cpu_limit,wall_limit=args.wall_limit,phase=args.phase,cwd=args.cwd)
    print(json.dumps({key:result[key] for key in ['run_id','status','CPU_seconds','charged_CPU_seconds']}),flush=True)

if __name__=='__main__':main()
