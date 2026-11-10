import inspect
import numpy as np
import pytest
from scipy import sparse
from method_extension.next_round.certified_solver import solve,graph_arrays,certificate,threshold,component_dual_flow
from experiments.next_round.evaluate import graph_diagnostics


def test_class_induced_connectivity_includes_isolates():
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]])
    d=graph_diagnostics(np.arange(3.)[:,None],W,np.array([0,1,0]))
    assert d['diagnostic_schema']==2 and d['components']==1
    assert d['within_class_components']==[2,1]
    assert d['within_class_components_mean']==1.5
    assert d['within_class_excess_fragments']==1
    assert d['within_class_isolates']==[2,1]
    assert d['within_class_largest_component_fraction']==[.5,1.]
    assert d['whole_graph_components_covering_class']==[1,1]


def test_initial_feasible_dual_is_retained_without_updates():
    F=np.array([[0.],[2.],[4.]])
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]])
    B,_,_,w=graph_arrays(W);q=np.array([[-.5],[-.5]])
    cert=certificate(q,F,B,2*w)
    result=solve(F,W,1,q_init=q,max_iter=0,consensus_bound=False)
    assert result['initial_dual']==pytest.approx(cert['dual'])
    assert result['dual']==pytest.approx(cert['dual'])
    assert result['history'][0]['dual']>0


@pytest.mark.parametrize('fidelity,delta',[('radial',0),('radial',.3),('squared',.3)])
def test_diagonal_weighted_pdhg_against_independent_convex_reference(fidelity,delta):
    cp=pytest.importorskip('cvxpy');rng=np.random.default_rng(911)
    F=rng.normal(size=(6,2));weights=np.array([.01,.1,1.,10.,.03])
    W=sparse.diags([weights,weights],[-1,1]).tocsr();B,_,_,w=graph_arrays(W)
    G=cp.Variable(F.shape);r=cp.norm(G-F,axis=1)
    loss=cp.sum(r) if delta==0 else cp.sum_squares(G-F)/(2*delta) if fidelity=='squared' else cp.sum(cp.huber(r,delta))/(2*delta)
    prob=cp.Problem(cp.Minimize(loss+.8*cp.sum(cp.multiply(w,cp.norm(B@G,axis=1)))))
    prob.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10)
    result=solve(F,W,.4,fidelity=fidelity,delta=delta,preconditioned=True,max_iter=60000,return_checkpoint=True)
    assert result['certified'],result['gap']
    assert result['dual']<=prob.value+1e-7
    assert result['primal']>=prob.value-1e-7
    assert result['primal']-prob.value<=1e-5*max(1,abs(prob.value))+1e-7
    assert np.all(np.linalg.norm(result['q'],axis=1)<=.8*w+1e-8)
    check=certificate(result['q'],F,B,.8*w,delta=delta,fidelity=fidelity)
    assert check['edge_violation']<=1e-8 and check['node_violation']<=1e-8
    np.testing.assert_allclose(check['dual'],result['dual'],rtol=1e-9)
    # A warm restart retains its incoming feasible lower bound.
    continued=solve(F,W,.4,fidelity=fidelity,delta=delta,preconditioned=True,max_iter=0,G_init=result['G'],q_init=result['q'])
    assert continued['dual']>=result['dual']-1e-9
    assert continued['primal']<=result['primal']+1e-10


def test_eight_cycle_deletion_destroys_force_cancellation():
    angle=np.arange(8)*2*np.pi/8;F=np.column_stack([np.cos(angle),np.sin(angle)])
    W=sparse.csr_matrix((np.ones(16),(np.r_[np.arange(8),np.roll(np.arange(8),-1)],np.r_[np.roll(np.arange(8),-1),np.arange(8)])),shape=(8,8))
    edited=W.tolil();edited[0,1]=edited[1,0]=0;edited=edited.tocsr()
    assert threshold(F,W)['gamma0']==pytest.approx(.6532814824381882)
    assert threshold(F,edited)['gamma0']==pytest.approx(.5)
    original=solve(F,W,.6);deleted=solve(F,edited,.6,preconditioned=True)
    assert original['status']=='ANALYTIC_G_EQUALS_F'
    assert deleted['certified'] and np.linalg.norm(deleted['G']-F)>1e-3
    assert deleted['primal']<float(1.2*graph_arrays(edited)[3]@np.linalg.norm(graph_arrays(edited)[0]@F,axis=1))


def test_component_flow_is_independently_checked_and_label_free():
    F=np.array([[0.],[1.],[2.]])
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]])
    result=component_dual_flow(F,W,2,cpu_time_limit=1.)
    assert result['certified'] and result['gap']<=1e-5
    assert result['edge_violation']<=1e-8 and result['node_violation']<=1e-8
    assert 'y' not in inspect.signature(component_dual_flow).parameters


def test_audit_pair_preserves_recoverable_stages(tmp_path):
    import json
    from experiments.submission_refresh.usps_audit import audit_pair
    F=np.array([[0.],[1.],[2.]])
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]])
    result=audit_pair(F,W,output_dir=tmp_path,gammas=(1.,),attempt_cpu_limit=1.,flow_cpu_limit=1.,block_cpu_limit=5.,pdhg_max_iter=1000)
    assert len(result['records'])==5
    assert (tmp_path/'frozen_pair.npz').is_file()
    for stage in result['records']:
        assert (tmp_path/stage['arrays_file']).is_file()
        assert stage['same_frozen_pair']==result['same_frozen_pair']
        arrays=np.load(tmp_path/stage['arrays_file'])
        assert 'G' in arrays
    assert result['records'][0]['complete_historical_execution']
    assert 'checkpoint_G_last' in np.load(tmp_path/result['records'][1]['arrays_file'])
    assert json.loads((tmp_path/'audit_manifest.json').read_text())['same_frozen_pair']==result['same_frozen_pair']
