from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from scipy import sparse
from method_extension.next_round.certified_solver import solve


def synthetic_smoke():
    F=np.array([[-1.],[1.]]);W=sparse.csr_matrix([[0,.125],[.125,0]])
    results=[]
    for delta,expected in [(0.,.5),(.3,.48125)]:
        r=solve(F,W,1,delta=delta)
        if not r['certified'] or abs(r['primal']-expected)>1e-8 or r['gap']>1e-5:raise AssertionError(r)
        results.append({k:r[k] for k in ['delta','primal','dual','gap','status']})
    return {'ok':True,'data_required':False,'cases':results}


def data_smoke(config,data_root,datasets=None,output=None):
    from experiments.v3_reproduction.protocol_registry import load_campaign
    from experiments.v3_reproduction.dataset_registry import load_spec,resolve_data_root
    from experiments.v3_reproduction.provenance import json_ready,environment_record,source_fingerprint
    from SSC_method.spectral_embedding import spectral_embedding
    from SSC_method.graph_construction import knn_affinity
    from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,GREEDY
    from experiments.v2_kmeans_protocol.metrics import evaluate_partition
    import json
    campaign=load_campaign(config)
    if data_root:campaign['data_root']=data_root
    datasets=datasets or ['ORL_att92','JAFFE'];results=[]
    with threadpool_limits(limits=1):
        for dataset in datasets:
            spec=next(s for s in campaign['_datasets']['specs'] if s['dataset_id']==dataset)
            record=load_spec(resolve_data_root(campaign),spec)
            if not record['available']:raise FileNotFoundError(record['reason'])
            X,y=record['X'],record['y'];K=len(np.unique(y));F,info=spectral_embedding(X,K);W,_=knn_affinity(F,k=5)
            result=solve(F,W,1,time_limit=60,max_iter=3000)
            trials=[]
            for seed in range(3):
                for method,G in [('SC',F),('SSC',result['G'])]:
                    fit=fit_lloyd(G,K,seed,GREEDY);trials.append({'method':method,'seed':seed,**evaluate_partition(y,fit['labels'])})
            results.append({'dataset_id':dataset,'shape':list(X.shape),'data_fingerprint':record['fingerprint'],'solver':{k:v for k,v in result.items() if k not in ['G','q','history']},'trials':trials})
    summary=json_ready({'ok':True,'scope':'three-seed real-data smoke, not a reproduction result','source_hash':source_fingerprint(),'environment':environment_record(),'datasets':results})
    if output:
        p=Path(output);p.mkdir(parents=True,exist_ok=True);(p/'smoke.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary
