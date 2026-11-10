"""USPS evaluation verifies saved points and never reruns an optimizer."""
from pathlib import Path
import json
import numpy as np
import pytest
from scipy import sparse
import experiments.submission_refresh.usps_evaluate as evaluation
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest,ResourceLedger


def fixture(tmp_path,*,with_G=True):
    store=ArtifactStore(tmp_path);folder=tmp_path/'usps_audit';folder.mkdir()
    F=np.array([[0.,0.],[.1,0.],[0.,.1],[4.,4.],[4.1,4.],[4.,4.1]])
    y=np.repeat([0,1],3);W=sparse.csr_matrix(np.ones((6,6))-np.eye(6))
    refs={key:store.put(value) for key,value in [('F',F),('W',W),('y',y)]}
    atomic_json(folder/'frozen_pair.json',{'objects':refs})
    np.savez_compressed(folder/'frozen_pair.npz',F=F,W_data=W.data,W_indices=W.indices,W_indptr=W.indptr,W_shape=np.array(W.shape))
    pair=evaluation.pair_identity(F,W);name='gamma_1_IRLS300';array_path=folder/(name+'.npz')
    np.savez_compressed(array_path,**({'G':F+.01} if with_G else {'q':np.zeros((1,2))}))
    metadata={'stage':'IRLS300','status':'MAX_ITER_REACHED','variant':'E8','gamma':1.,'gamma_effective':1.,
              'certified':False,'complete_historical_execution':True,'protocol':{'max_iter':300},
              'same_frozen_pair':pair,'arrays_file':array_path.name,'arrays_sha256':digest(array_path)}
    atomic_json(folder/(name+'.json'),metadata)
    manifest={'same_frozen_pair':pair,'graph':{'E8_capacities':'2*gamma*w'},'records':[{'name':name,**metadata}]}
    atomic_json(folder/'audit_manifest.json',manifest)
    atomic_json(tmp_path/'task_status/usps-numerical-audit-v1.json',{'status':'COMPLETED','manifest':manifest})
    return store,folder,F,y,W


def test_verified_tiny_points_round_all50_without_solver_calls(tmp_path,monkeypatch):
    store,folder,F,y,W=fixture(tmp_path)
    import method_extension.next_round.certified_solver as solver
    def forbidden(*args,**kwargs):raise AssertionError('No optimizer may be called by evaluation')
    monkeypatch.setattr(solver,'solve',forbidden)
    monkeypatch.setattr(solver,'component_dual_flow',forbidden)
    calls=[]
    def rounder(G,K,seed,initialization):
        calls.append((G.copy(),K,seed,initialization))
        labels=np.repeat([0,1],3);centers=np.array([G[labels==k].mean(axis=0) for k in range(K)])
        return {'labels':labels,'centers':centers,'inertia':float(seed+1),'kmeans_n_iter':1,'kmeans_warning':''}
    monkeypatch.setattr(evaluation,'fit_lloyd',rounder)
    verified=evaluation.verify_artifacts(tmp_path,expected_n=6,expected_K=2)
    records=evaluation.evaluate_verified(verified,store,folder/'evaluation/fixture/version',dataset='TEST_FIXTURE')
    complete=[r for r in records if r['status']=='COMPLETED']
    assert len(calls)==100 and len(complete)==2
    for row in complete:
        assert [r['seed'] for r in row['trials']]==list(range(50))
        assert row['summary']['n']==50 and row['summary']['acc_mean']==100
        assert row['summary']['acc_sd']==0
        assert row['native_best']['seed']==0 and row['native_best']['acc_sd'] is None
        assert store.get(row['objects']['predictions']).shape==(50,6)
    assert complete[1]['historical_300_protocol_complete']
    assert sum(r['status']=='NOT_EVALUATED_MISSING_G' for r in records)==9
    assert {c[3] for c in calls}=={'SKLEARN_GREEDY_KMEANSPP'}
    # Toy validation cannot enter a published USPS row.
    with pytest.raises(ValueError,match='full9298'):
        evaluation.evaluate_verified(verified,store,folder/'evaluation/wrong/version')


@pytest.mark.parametrize('failure',['missing','corrupt','bad_shape','wrong_gamma'])
def test_integrity_failures_happen_before_any_evaluation(tmp_path,monkeypatch,failure):
    store,folder,F,y,W=fixture(tmp_path)
    called=[];monkeypatch.setattr(evaluation,'fit_lloyd',lambda *a,**k:called.append(True))
    path=folder/'gamma_1_IRLS300.npz'
    if failure=='missing':path.unlink()
    elif failure=='corrupt':path.write_bytes(path.read_bytes()+b'changed')
    else:
        stage=json.loads((folder/'gamma_1_IRLS300.json').read_text())
        manifest=json.loads((folder/'audit_manifest.json').read_text())
        if failure=='bad_shape':
            np.savez_compressed(path,G=F[:-1]);stage['arrays_sha256']=digest(path)
        else:stage['gamma_effective']=.5
        atomic_json(folder/'gamma_1_IRLS300.json',stage)
        manifest['records']=[{'name':'gamma_1_IRLS300',**stage}]
        atomic_json(folder/'audit_manifest.json',manifest)
        atomic_json(tmp_path/'task_status/usps-numerical-audit-v1.json',{'status':'COMPLETED','manifest':manifest})
    with pytest.raises(ValueError):evaluation.verify_artifacts(tmp_path,expected_n=6,expected_K=2)
    assert not called


def test_verified_npz_without_G_is_explicitly_not_evaluated(tmp_path):
    store,folder,F,y,W=fixture(tmp_path,with_G=False)
    verified=evaluation.verify_artifacts(tmp_path,expected_n=6,expected_K=2)
    point=next(p for p in verified['points'] if p['name']=='gamma_1_IRLS300')
    assert point['availability']=='NOT_EVALUATED_MISSING_G' and 'G' not in point


def test_shared_USPS_remaining_allowance_and_active_audit_guard(tmp_path):
    ledger=ResourceLedger(tmp_path)
    with ledger.locked() as state:
        state['entries']=[{'run_id':'usps-numerical-audit-v1','phase':'mandatory_usps','charged_cpu_seconds':21450,'status':'COMPLETED'}]
    assert ledger.reserve('usps-evaluation-fixture',900,'mandatory_usps')
    allowed,spent=evaluation.remaining_allowance({'run_id':'usps-evaluation-fixture','cpu_limit':900},tmp_path)
    assert allowed==150 and spent==21450
    with ledger.locked() as state:state['active']['usps-numerical-audit-v1']={'seconds':1,'phase':'mandatory_usps'}
    with pytest.raises(ValueError,match='remains active'):
        evaluation.remaining_allowance({'run_id':'usps-evaluation-fixture','cpu_limit':900},tmp_path)
