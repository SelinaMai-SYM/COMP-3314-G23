"""Independent completion never retries failed points or selects on scores."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest
from experiments.v3_reproduction.provenance import fingerprint_matrix
from experiments.subset_search import complete_failed as completion


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'checkout';store=ArtifactStore(tmp_path/'durable');folder=store.root/'subset/unit';folder.mkdir(parents=True)
    X=np.arange(12.).reshape(4,3);y=np.array([0,0,1,1]);F=np.array([[0.,0.],[.1,0.],[1.,1.],[1.1,1.]])
    W=sparse.csr_matrix(np.ones((4,4))-np.eye(4));refs={name:store.put(value) for name,value in [('X',X),('y',y),('F',F),('A',W),('W',W)]}
    candidate={'candidate_id':'unit','fingerprint':fingerprint_matrix(X,y)};cache='unchanged-scientific-functions'
    atomic_json(folder/'representation.json',{'candidate':candidate,'fingerprint':candidate['fingerprint'],'objects':refs,'cache_identity':cache})
    atomic_json(folder/'source.json',{'cache_identity':cache,'implementation_hash':'original-byte-map'})
    status={'candidate_id':'unit','candidate':candidate,'cache_identity':cache,'status':'FAILED','profile_only':False,'cpu_seconds':5.,
        'active_configuration':{'method':'ssc','variant':'E8','gamma_nominal':1.,'stage':'solver'},'error':'original numerical failure'}
    atomic_json(folder/'status.json',status)
    catalogue=root/'results/subset_search/candidate_catalogue.json';atomic_json(catalogue,{'candidates':[candidate]})
    atomic_json(root/'configs/subset_search/executable_cohort.json',{'catalogue_sha256':digest(catalogue),'candidate_ids':['unit'],'cpu_limit_per_candidate':10000})
    monkeypatch.setattr(completion,'ROOT',root);monkeypatch.setattr(completion,'scientific_cache_identity',lambda *args,**kwargs:cache)
    monkeypatch.setattr(completion,'source_record',lambda:{'implementation_hash':'actual-completion-source','source_files':{}})
    monkeypatch.setattr(completion,'install_cpu_limit',lambda *args:None)
    monkeypatch.setattr(completion.signal,'setitimer',lambda *args:None)
    monkeypatch.setattr(completion,'iteration_diagnostics',lambda fit:{'n_iterations':1,'converged':True})
    monkeypatch.setattr(completion,'shrinkage_laplacian',lambda W,G,eps:(W,W))
    def rounding(G,y,K,init):
        trials=[{'seed':i,'acc':.5,'nmi':.4,'inertia':float(50-i),'iterations':1,'warning':''} for i in range(50)]
        return trials,np.tile(y,(50,1)),np.tile(G[:K],(50,1,1))
    monkeypatch.setattr(completion,'round_embedding',rounding)
    task={'run_id':'complete-unit','candidate':candidate,'cpu_limit':1000.,'post_primary':True}
    return store,folder,task,F


def test_one_solver_failure_does_not_skip_other_points_or_retry_original(tmp_path,monkeypatch):
    store,folder,task,F=fixture(tmp_path,monkeypatch);calls=[];original=(folder/'status.json').read_bytes();source=(folder/'source.json').read_bytes()
    def fit(F,W,gamma,**kwargs):
        calls.append((kwargs['variant'],gamma,kwargs))
        assert kwargs['max_iter']==300 and kwargs['tol']==1e-6 and kwargs['eps']==1e-8
        if kwargs['variant']=='E8' and gamma==1e-3:raise RuntimeError('independent numerical failure')
        return SimpleNamespace(patterns=F+.01,history=[],converged=True)
    monkeypatch.setattr(completion,'shrink_embedding',fit)
    result=completion.run_completion(task,tmp_path/'data',store.root)
    assert ('E8',1.) not in [(v,g) for v,g,_ in calls]
    assert ('E13',1e6) in [(v,g) for v,g,_ in calls]
    assert result['status']=='COMPLETED_WITH_PRESERVED_FAILURES'
    assert len(result['new_completed_points'])==27
    assert len(result['new_failed_points'])==3
    assert not (folder/'E8__1__RANDOM.json').exists()
    assert not (folder/'E8__0.001__RANDOM.json').exists()
    assert (folder/'E13__1e+06__RANDOM.json').exists()
    assert original==(folder/'status.json').read_bytes() and source==(folder/'source.json').read_bytes()
    record=json.loads((folder/'E13__1e+06__RANDOM.json').read_text())
    assert record['source']['implementation_hash']=='actual-completion-source'
    assert record['dual_status']=='NOT_COMPUTED_IRLS' and 'q' not in record['objects']
    assert 'fidelity_weights_S_diagonal'in record['objects']


def test_corrupt_saved_object_fails_before_any_fit_or_scientific_write(tmp_path,monkeypatch):
    store,folder,task,F=fixture(tmp_path,monkeypatch);meta=json.loads((folder/'representation.json').read_text())
    (store.root/meta['objects']['F']['path']).write_bytes(b'corrupt')
    calls=[];monkeypatch.setattr(completion,'shrink_embedding',lambda *args,**kwargs:calls.append('fit'))
    with pytest.raises(ValueError,match='corrupt'):completion.run_completion(task,tmp_path/'data',store.root)
    assert not calls and not (folder/'completion_attempts').exists()


def test_timeout_stops_candidate_and_is_not_retried_in_later_attempt(tmp_path,monkeypatch):
    store,folder,task,F=fixture(tmp_path,monkeypatch);calls=[]
    def fit(*args,**kwargs):calls.append('fit');raise TimeoutError('process CPU allocation exhausted')
    monkeypatch.setattr(completion,'shrink_embedding',fit)
    result=completion.run_completion(task,tmp_path/'data',store.root)
    assert result['status']=='TIMEOUT' and len(calls)==1
    with pytest.raises(ValueError,match='prior CPU timeout'):
        completion.run_completion({**task,'run_id':'second'},tmp_path/'data',store.root)
    assert len(calls)==1
