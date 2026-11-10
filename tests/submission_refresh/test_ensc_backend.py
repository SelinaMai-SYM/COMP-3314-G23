"""Independent convex checks for the conditional EnSC backend; no benchmark labels."""
import inspect
import numpy as np
import pytest
from method_extension.submission_refresh.ensc import (
    elastic_net_code, elastic_net_objective, elastic_net_kkt,
    coefficients_to_affinity, ensc_affinity,
)


@pytest.mark.parametrize('tau',[.95,1.])
def test_true_elastic_net_objective_against_independent_cvxpy(tau):
    cp=pytest.importorskip('cvxpy')
    rng=np.random.RandomState(314);D=rng.normal(size=(11,5));target=rng.normal(size=5)
    alpha=.17
    c,diagnostics=elastic_net_code(D,target,alpha,tau,active_support=False)
    reference=cp.Variable(len(D))
    problem=cp.Problem(cp.Minimize(.5*cp.sum_squares(target-reference@D)+alpha*(tau*cp.norm1(reference)+(1-tau)*cp.sum_squares(reference)/2)))
    problem.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10)
    assert problem.status=='optimal'
    assert abs(elastic_net_objective(c,D,target,alpha,tau)-problem.value)<1e-7
    assert elastic_net_kkt(c,D,target,alpha,tau)<1e-7
    assert diagnostics['tau_used']==tau
    if tau<1:
        np.testing.assert_allclose(c,reference.value,atol=5e-5,rtol=5e-5)


def test_active_support_solves_same_target():
    rng=np.random.RandomState(519);D=rng.normal(size=(18,8));y=rng.normal(size=8)
    alpha=.13
    active,diag=elastic_net_code(D,y,alpha,.95,support_size=3,max_outer=40)
    full,_=elastic_net_code(D,y,alpha,.95,active_support=False)
    assert abs(elastic_net_objective(active,D,y,alpha,.95)-elastic_net_objective(full,D,y,alpha,.95))<1e-7
    assert diag['kkt_residual']<1e-7


def test_source_affinity_truncation_and_zero_row_convention():
    C=np.array([[0.,3.,4.],[2.,0.,0.],[0.,0.,0.]])
    result=coefficients_to_affinity(C,n_nonzero=1)
    np.testing.assert_array_equal(result['C_pre_truncation'].toarray(),C)
    np.testing.assert_allclose(result['Cn'].toarray(),[[0,0,1],[1,0,0],[0,0,0]])
    np.testing.assert_allclose(result['S'].toarray(),[[0,.5,.5],[.5,0,0],[.5,0,0]])
    assert result['zero_coefficient_rows']==[2]
    assert not result['degenerate_affinity']
    assert coefficients_to_affinity(np.zeros((3,3)))['degenerate_affinity']


def test_source_alpha_and_self_exclusion_are_label_free():
    result=ensc_affinity(np.eye(3),tau=.95)
    np.testing.assert_array_equal(result['alpha_i'],np.zeros(3))
    assert result['degenerate_affinity']
    assert not np.any(result['C'].diagonal())
    assert 'labels' not in inspect.signature(ensc_affinity).parameters
    with pytest.raises(ValueError):
        elastic_net_code(np.eye(2),np.ones(2),.1,tau=0.)
