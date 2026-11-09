import json,hashlib
import numpy as np
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from experiments.v3_reproduction.runner import _write_job,_done

def test_perfect_imbalanced_entropy_roundoff():
    y=np.repeat(np.arange(3),[10,30,50]);r=evaluate_partition(y,y)
    assert r['acc']==1 and r['nmi']==1

def test_document_only_commit_reuses_source_identical_cache_and_detects_trial_tampering(tmp_path):
    p={'runs_dir':str(tmp_path),'dataset_id':'tiny','code_commit':'old','source_hash':'same','environment':{'python':'3'},'current_fingerprint':{'x':'data'},'protocols':{'seeds':[0]}}
    _write_job(p,'job',{'status':'COMPLETED'},[{'seed':0,'acc':1}]);q={**p,'code_commit':'docs-only-new'}
    assert _done(q,'job')
    assert not _done({**q,'source_hash':'changed'},'job')
    (tmp_path/'tiny/job.trials.jsonl').write_text('{}\n')
    assert not _done(q,'job')
