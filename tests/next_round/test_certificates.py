import inspect
import itertools
import numpy as np
import pytest
from scipy import sparse
from method_extension.next_round.certified_solver import solve,graph_arrays,certificate,threshold
from method_extension.next_round.capped_fusion import fit,capped_objective


def test_analytic_one_edge_and_huber():
    F=np.array([[-1.],[1.]]);W=sparse.csr_matrix([[0,.125],[.125,0]])
    for delta,value,target in [(0,.5,[-1,1]),(.3,.48125,[-.925,.925])]:
        r=solve(F,W,1,delta=delta)
        assert r['certified'] and r['gap']<=1e-5
        assert r['primal']==pytest.approx(value,abs=1e-9)
        np.testing.assert_allclose(r['G'].ravel(),target,atol=1e-7)


@pytest.mark.parametrize('fidelity,delta',[('radial',0),('radial',.3),('squared',.3)])
def test_independent_cvxpy_chain_and_random(fidelity,delta):
    cp=pytest.importorskip('cvxpy');rng=np.random.default_rng(92)
    for n in [3,7]:
        F=rng.normal(size=(n,2));W=sparse.diags([np.ones(n-1),np.ones(n-1)],[-1,1]).tocsr();B,_,_,w=graph_arrays(W)
        G=cp.Variable(F.shape);norm=cp.norm(G-F,axis=1)
        data=cp.sum(norm) if delta==0 else cp.sum_squares(G-F)/(2*delta) if fidelity=='squared' else cp.sum(cp.huber(norm,delta))/(2*delta)
        problem=cp.Problem(cp.Minimize(data+0.8*cp.sum(cp.multiply(w,cp.norm(B@G,axis=1)))))
        problem.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_feas=1e-10,tol_gap_rel=1e-10)
        r=solve(F,W,.4,delta=delta,fidelity=fidelity)
        assert r['certified'],r['gap']
        assert r['dual']<=problem.value+1e-6
        assert r['primal']>=problem.value-1e-6
        assert r['primal']-problem.value<=1e-5*max(1,r['primal'])+1e-7


def test_no_edges_zero_gamma_coincident_and_label_free():
    F=np.array([[0.,0],[0,0],[1,0]])
    for W,gamma in [(sparse.csr_matrix((3,3)),1),(sparse.csr_matrix(np.ones((3,3))-np.eye(3)),0)]:
        r=solve(F,W,gamma);np.testing.assert_array_equal(r['G'],F);assert r['certified']
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]])
    t=threshold(F,W);assert t['sufficient_only'] and np.isfinite(t['gamma0'])
    for function in [solve,threshold,fit]:assert 'y' not in inspect.signature(function).parameters


def test_squared_dual_does_not_project_node_balls():
    F=np.array([[-1.],[1.]]);B,_,_,w=graph_arrays(sparse.csr_matrix([[0,1],[1,0]]));q=np.array([[10.]])
    radial=certificate(q,F,B,100*w,delta=.2)
    square=certificate(q,F,B,100*w,delta=.2,fidelity='squared')
    assert np.linalg.norm(B.T@radial['q'],axis=1).max()<=1+1e-8
    assert np.linalg.norm(B.T@square['q'],axis=1).max()>9


def test_capped_local_output_and_global_small_mask_enumeration():
    cp=pytest.importorskip('cvxpy');F=np.array([[0.],[.2],[4.]])
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]]);B,_,_,w=graph_arrays(W);gamma=.8;tau=1.
    exact=[]
    for mask in itertools.product([0,1],repeat=2):
        G=cp.Variable(F.shape);mask=np.array(mask)
        p=cp.Problem(cp.Minimize(cp.sum(cp.norm(G-F,axis=1))+2*gamma*cp.sum(cp.multiply(w*mask,cp.norm(B@G,axis=1)))+2*gamma*np.sum(w*(1-mask))*tau));p.solve(solver='CLARABEL');exact.append(p.value)
    r=fit(F,W,gamma,tau)
    assert r['objective']>=min(exact)-1e-6
    assert all(b['objective']<=a['objective']+1e-8 for a,b in zip(r['history'],r['history'][1:]))
    assert not r['globally_certified']
    assert r['objective']==pytest.approx(capped_objective(r['G'],F,W,gamma,tau))


def test_primal_initializer_keeps_independent_certificate():
    F=np.array([[0.],[.3],[2.]])
    W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]])
    r=solve(F,W,.8,warm_start_irls=True)
    assert r['certified'] and r['gap']<=1e-5
    assert r['primal']>=r['dual']-1e-9
    assert r['warm_start']['requested']
