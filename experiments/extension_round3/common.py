from __future__ import annotations
import json,os,shutil,subprocess,time
from pathlib import Path
import numpy as np
from experiments.submission_refresh.core import ROOT,ArtifactStore,atomic_json,digest,identity,ResourceLedger
from experiments.extension_round2.common import environment,put_arrays,get_arrays,save_continuation,recover_continuation

ORDER=['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']
CONFIG=ROOT/'configs/extension_round3/protocol.yaml'

def read(path):return json.loads(Path(path).read_text())
def registry():return {r['id']:r for r in read(ROOT/'configs/extension_round3/method_registry.json')}
def queue():return read(ROOT/'configs/extension_round3/experiment_queue.json')
def numerical_files():
    paths=list((ROOT/'method_extension/extension_round3').glob('*.py'))+[ROOT/'experiments/extension_round3'/x for x in ['common.py','rounding.py','freeze.py','calibration.py','worker.py']]
    paths+=[ROOT/'experiments/submission_refresh/core.py',ROOT/'experiments/extension_verification/resources.py',ROOT/'experiments/extension_round2/common.py',ROOT/'method_extension/next_round/certified_solver/solver.py',ROOT/'method_extension/extension_verification/convex.py']
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}
def locked(root,config=CONFIG):
    store=ArtifactStore(root);lock=read(store.root/'cohort_lock.json')
    if lock['protocol_sha256']!=digest(config) or lock['source_files']!=numerical_files() or lock['environment']!=environment():raise ValueError('frozen protocol, numerical source or environment differs')
    spec=read(config)
    for amendment in lock.get('amendments',[]):
        for dotted,value in amendment.get('effective_overrides',{}).items():
            target=spec;parts=dotted.split('.')
            for key in parts[:-1]:target=target[key]
            target[parts[-1]]=value
    return spec,lock,store

def assert_fitting_open(root):
    root=Path(root)
    if (root/'numerical_freeze.json').exists():raise RuntimeError('numeric outputs frozen; terminal scoring forbids further fitting')
    clock=read(root/'clock.json')
    if time.time()>=clock['fit_deadline_epoch']:raise TimeoutError('reserved final wall hour reached')

def link_ref(source,store,ref):
    src=source.root/ref['path'];dest=store.root/ref['path']
    if digest(src)!=ref['sha256']:raise ValueError('source object hash mismatch')
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        try:os.link(src,dest)
        except OSError:shutil.copy2(src,dest)
    if digest(dest)!=ref['sha256']:raise ValueError('linked object hash mismatch')
    return ref

def collect_refs(value):
    if isinstance(value,dict):
        if {'path','sha256','kind'}<=set(value):yield value
        else:
            for v in value.values():yield from collect_refs(v)
    elif isinstance(value,list):
        for v in value:yield from collect_refs(v)

def scalar(cert):return {k:v for k,v in cert.items() if not isinstance(v,np.ndarray) and k!='checkpoint'}
def profile_path(store,id):return store.root/'profiles'/(id+'.json')
