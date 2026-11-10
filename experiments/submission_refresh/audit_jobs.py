from pathlib import Path
import time,json
from experiments.submission_refresh.core import ArtifactStore,atomic_json

def run_usps(task,data_root,artifact_root):
    from .usps_audit import audit_pair
    from .baselines import load
    from SSC_method.spectral_embedding import spectral_embedding
    from SSC_method.graph_construction import knn_affinity
    from threadpoolctl import threadpool_limits
    start=time.process_time();store=ArtifactStore(artifact_root)
    with threadpool_limits(limits=1):
        X,y,meta=load('USPS',data_root);F,info=spectral_embedding(X,10);A,_=knn_affinity(X,5);W,_=knn_affinity(F,5)
        refs={k:store.put(v) for k,v in [('X',X),('y',y),('A',A),('F',F),('W',W)]}
        folder=Path(artifact_root)/'usps_audit';atomic_json(folder/'frozen_pair.json',{'objects':refs,'spectral':info,'dataset':meta,'identity':'new independently generated pair; not historical missing arrays'})
        manifest=audit_pair(F,W,output_dir=folder,gammas=(1.,1000.),attempt_cpu_limit=task.get('attempt_cpu_limit',1800),flow_cpu_limit=300,block_cpu_limit=task['cpu_limit'],pdhg_max_iter=30000)
    return {'status':'COMPLETED','cpu_seconds':time.process_time()-start,'manifest':manifest}
