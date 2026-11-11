"""Evaluate a fixed saved Q; this layer alone consumes benchmark labels."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from experiments.subset_search.runner import round_embedding
from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY
from experiments.submission_refresh.selection import summarize
from experiments.submission_refresh.core import atomic_json,identity,digest
from .inputs import load_locked,datasets_lock_path


def evaluate(record,config,artifact_root):
    specification,lock,store=load_locked(config,artifact_root);entry=lock['datasets'][record['benchmark']];point_id=record['point_id'];target=store.root/'evaluations'/f'{point_id}.json'
    if record['source_fingerprint']!=lock['source_fingerprint'] or record['input_registration_sha256']!=digest(datasets_lock_path(store.root)) or record['candidate_id']!=entry['candidate_id']:raise ValueError('evaluation input/source registration mismatch')
    if target.exists():
        saved=json.loads(target.read_text())
        if saved['Q_object']!=record['objects']['Q'] or saved['protocol_sha256']!=lock['protocol_sha256']:raise ValueError('rounding identity changed')
        return saved
    start=time.process_time();Q=store.get(record['objects']['Q']);labels=store.get(entry['objects']['labels']);trials,predictions,centers=round_embedding(Q,labels,entry['K'],GREEDY,range(50))
    if [r['seed'] for r in trials]!=list(range(50)):raise ValueError('incomplete rounding cannot produce a complete endpoint')
    summary=summarize(trials,objective='inertia');native=min(trials,key=lambda row:(row['inertia'],row['seed']))
    result={'schema':'ssc-refinement-evaluation-v1','point_id':point_id,'benchmark':record['benchmark'],'candidate_id':entry['candidate_id'],'protocol_sha256':lock['protocol_sha256'],'source_fingerprint':lock['source_fingerprint'],'Q_object':record['objects']['Q'],'trials':trials,'summary':{k:v for k,v in summary.items() if k!='native_best'},'native_best':{'seed':native['seed'],'acc':native['acc'],'nmi':native['nmi'],'inertia':native['inertia'],'acc_sd':None,'nmi_sd':None},'predictions':store.put(predictions),'centers':store.put(centers),'CPU_seconds':time.process_time()-start,'scope':'50 conditional rounding seeds on one fixed saved Q; native assignment selected only by SSE then seed'}
    atomic_json(target,result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--record',required=True);p.add_argument('--config',required=True);p.add_argument('--artifact-root',required=True);args=p.parse_args();record=json.loads(Path(args.record).read_text());r=evaluate(record,args.config,args.artifact_root);print(json.dumps({'point_id':r['point_id'],'n':len(r['trials']),'ACC':r['summary']['acc_mean'],'NMI':r['summary']['nmi_mean']}),flush=True)

if __name__=='__main__':main()
