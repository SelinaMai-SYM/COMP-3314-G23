from __future__ import annotations
import json,os,platform,subprocess,time,tempfile,shutil
from pathlib import Path
import importlib.metadata
import yaml
from experiments.submission_refresh.core import ROOT,ArtifactStore,atomic_json,digest,identity,ResourceLedger

ORDER=['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']
METHODS=['QSSC','E1_v2','E4','E5','E6']
DEFAULT_CONFIG=ROOT/'configs/extension_round2/protocol.yaml'

def environment():return {'python':platform.python_version(),'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn','osqp','cvxpy','clarabel','threadpoolctl']},'threads_per_worker':1}
def source_files():
    files=list((ROOT/'method_extension/extension_round2').glob('*.py'))+[ROOT/'experiments/extension_round2'/n for n in ['common.py','inputs.py','calibration.py','worker.py']]
    files+=list((ROOT/'SSC_method').glob('*.py'))+[ROOT/'experiments/subset_search/catalogue.py',ROOT/'experiments/subset_search/runner.py',ROOT/'experiments/submission_refresh/core.py',ROOT/'experiments/v2_kmeans_protocol/kmeans_trials.py',ROOT/'experiments/v2_kmeans_protocol/metrics.py',ROOT/'method_extension/next_round/certified_solver/solver.py',ROOT/'method_extension/extension_verification/convex.py',ROOT/'experiments/extension_verification/resources.py']
    return {str(f.relative_to(ROOT)):digest(f) for f in sorted(files)}
def config(path=DEFAULT_CONFIG):return yaml.safe_load(Path(path).read_text())
def locked(artifact_root,path=DEFAULT_CONFIG,check_source=True):
    spec=config(path);store=ArtifactStore(artifact_root);lock=json.loads((store.root/'cohort_lock.json').read_text())
    if lock['protocol_sha256']!=digest(path):raise ValueError('protocol hash changed')
    if check_source and (lock['source_files']!=source_files() or lock['environment']!=environment()):raise ValueError('source/environment changed; qualify an explicit amendment before resuming')
    return spec,lock,store
def initialize_ledger(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if not (root/'resource_ledger.json').exists():
        atomic_json(root/'resource_ledger.json',{'version':1,'limit_seconds':172800,'reserve_seconds':0,'max_workers':2,'rss_target_bytes':8*2**30,'entries':[],'active':{}})
    if not (root/'clock.json').exists():
        # Backdate by thirty minutes to conservatively include the opening
        # repository audit and protocol implementation, without extending time.
        started=time.time()-1800;atomic_json(root/'clock.json',{'start_epoch':started,'deadline_epoch':started+86400,'wall_hours':24,'initialization':'Conservatively includes thirty minutes of opening audit/setup'})
    return ResourceLedger(root)
def remaining_wall(root):return max(0.,json.loads((Path(root)/'clock.json').read_text())['deadline_epoch']-time.time())
def put_arrays(store,value):
    import numpy as np
    if isinstance(value,np.ndarray):return store.put(value)
    if isinstance(value,dict):return {k:put_arrays(store,v) for k,v in value.items()}
    if isinstance(value,list):return [put_arrays(store,v) for v in value]
    return value
def get_arrays(store,value):
    if isinstance(value,dict):
        if {'sha256','path','kind'}<=set(value):return store.get(value)
        return {k:get_arrays(store,v) for k,v in value.items()}
    if isinstance(value,list):return [get_arrays(store,v) for v in value]
    return value
def load_record(path):return json.loads(Path(path).read_text()) if Path(path).exists() else None

def save_continuation(folder,value):
    """Keep one recoverable generation, rather than accumulating large arrays."""
    import numpy as np
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);old=load_record(folder/'CURRENT.json');generation=Path(tempfile.mkdtemp(prefix='generation-',dir=folder));arrays={}
    def split(item):
        if isinstance(item,np.ndarray):
            name='array'+str(len(arrays));arrays[name]=item;return {'checkpoint_array':name}
        if isinstance(item,dict):return {k:split(v) for k,v in item.items()}
        if isinstance(item,list):return [split(v) for v in item]
        return item
    skeleton=split(value);np.savez_compressed(generation/'arrays.npz',**arrays);atomic_json(generation/'state.json',{'value':skeleton,'arrays_sha256':digest(generation/'arrays.npz')})
    atomic_json(folder/'CURRENT.json',{'directory':generation.name,'state_sha256':digest(generation/'state.json')})
    if old:
        previous=folder/old['directory']
        if previous.parent==folder and previous.exists():shutil.rmtree(previous)

def recover_continuation(folder):
    import numpy as np
    folder=Path(folder);pointer=load_record(folder/'CURRENT.json');generation=folder/pointer['directory']
    if generation.parent!=folder or digest(generation/'state.json')!=pointer['state_sha256']:raise ValueError('continuation metadata identity failed')
    state=load_record(generation/'state.json')
    if digest(generation/'arrays.npz')!=state['arrays_sha256']:raise ValueError('continuation array identity failed')
    with np.load(generation/'arrays.npz',allow_pickle=False) as archive:
        def join(v):
            if isinstance(v,dict):return archive[v['checkpoint_array']].copy() if set(v)=={'checkpoint_array'} else {k:join(x) for k,x in v.items()}
            if isinstance(v,list):return [join(x) for x in v]
            return v
        return join(state['value'])
