"""Recoverable content-addressed objects and the shared resource ledger.

Records point to available objects, not merely checksums. Every object is verified
on read; archives can be moved independently of the checkout.
"""
from __future__ import annotations
import contextlib, hashlib, io, json, os, resource, tarfile, tempfile, time
from pathlib import Path
import numpy as np
from scipy import sparse
from experiments.v3_reproduction.provenance import json_ready

ROOT=Path(__file__).resolve().parents[2]
THREAD_ENV={k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']}

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(json_ready(value),sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(name,path)

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def identity(value):return hashlib.sha256(json.dumps(json_ready(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()

class ArtifactStore:
    def __init__(self,root):
        self.root=Path(root).resolve();(self.root/'objects').mkdir(parents=True,exist_ok=True)
    def put(self,value,kind='array'):
        stream=io.BytesIO()
        if sparse.issparse(value):sparse.save_npz(stream,value.tocsr());suffix='npz';kind='sparse'
        elif isinstance(value,np.ndarray):np.savez_compressed(stream,data=value);suffix='npz';kind='compressed_array'
        else:stream.write((json.dumps(json_ready(value),sort_keys=True,allow_nan=False)+'\n').encode());suffix='json';kind='json'
        content=stream.getvalue();sha=hashlib.sha256(content).hexdigest();rel=Path('objects')/sha[:2]/(sha+'.'+suffix);p=self.root/rel;p.parent.mkdir(exist_ok=True)
        if not p.exists():
            fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.object-')
            with os.fdopen(fd,'wb') as f:f.write(content)
            os.replace(tmp,p)
        if digest(p)!=sha:raise ValueError('object hash mismatch')
        return {'sha256':sha,'bytes':len(content),'path':str(rel),'kind':kind}
    def get(self,ref):
        p=(self.root/ref['path']).resolve()
        if self.root not in p.parents or digest(p)!=ref['sha256']:raise ValueError('missing/corrupt artifact')
        if ref['kind']=='sparse':return sparse.load_npz(p)
        if ref['kind']=='array':return np.load(p,allow_pickle=False)
        if ref['kind']=='compressed_array':
            with np.load(p,allow_pickle=False) as f:return f['data']
        return json.loads(p.read_text())
    def archive(self,refs,output):
        refs={r['path']:r for r in refs}.values();output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        with tarfile.open(output,'w:gz') as f:
            for ref in refs:self.get(ref);f.add(self.root/ref['path'],arcname=ref['path'])
        with tarfile.open(output) as f:
            for ref in refs:
                member=f.extractfile(ref['path'])
                if member is None or hashlib.sha256(member.read()).hexdigest()!=ref['sha256']:raise ValueError('archive failed verification')
        return {'path':str(output),'sha256':digest(output),'objects':len(refs)}

class ResourceLedger:
    """One append-only ledger for both campaigns, protected by a file lock.

    Reservations prevent two schedulers from oversubscribing the allowance.
    CPU limits use process CPU, and killed jobs are conservatively charged their
    reservation. Scheduler wall limits are a second, separate safeguard.
    """
    def __init__(self,root):self.path=Path(root)/'resource_ledger.json';self.path.parent.mkdir(parents=True,exist_ok=True)
    @contextlib.contextmanager
    def locked(self):
        import fcntl
        with self.path.with_suffix('.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state=json.loads(self.path.read_text()) if self.path.exists() else {'version':1,'limit_seconds':129600,'reserve_seconds':7200,'max_workers':2,'rss_target_bytes':8*2**30,'entries':[],'active':{}}
            yield state;atomic_json(self.path,state)
    def reserve(self,run_id,seconds,phase):
        with self.locked() as s:
            used=sum(e['charged_cpu_seconds'] for e in s['entries']);reserved=sum(v['seconds'] for v in s['active'].values())
            limit=s['limit_seconds']-(0 if phase in ['confirmation','validation','aggregation'] else s['reserve_seconds'])
            if run_id in s['active'] or len(s['active'])>=2 or used+reserved+seconds>limit:return False
            s['active'][run_id]={'seconds':seconds,'phase':phase,'timestamp':time.time()};return True
    def finish(self,run_id,cpu_seconds,status,**extra):
        with self.locked() as s:
            reservation=s['active'].pop(run_id,None)
            if reservation is None:raise ValueError('unreserved or duplicate job')
            charged=reservation['seconds'] if cpu_seconds is None else max(0,float(cpu_seconds))
            s['entries'].append({'run_id':run_id,'phase':reservation['phase'],'charged_cpu_seconds':charged,'status':status,**extra})
    def state(self):
        with self.locked() as s:return s.copy()

def install_cpu_limit(seconds):
    import signal
    started=time.process_time();allocation=float(seconds)
    def exceeded(_s,_f):
        remaining=allocation-(time.process_time()-started)
        # Some platforms deliver profiling signals before measured process CPU
        # reaches the requested interval. Only measured CPU exhausts the budget.
        if remaining>0.01:signal.setitimer(signal.ITIMER_PROF,remaining)
        else:raise TimeoutError('process CPU allocation exhausted')
    signal.signal(signal.SIGPROF,exceeded);signal.setitimer(signal.ITIMER_PROF,allocation)
