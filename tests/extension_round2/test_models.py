"""Small convex references and analytic counterexamples; no benchmark tuning."""
import numpy as np
import pytest
import cvxpy as cp
from scipy import sparse,linalg
from method_extension.extension_round2.models import QuadraticProblem,solve,center,sym
from method_extension.extension_round2.graph_repair import GraphRepair
from SSC_method.objective import equation8_objective
from experiments.submission_refresh.core import ArtifactStore


def graph(n,edges):
    i,j=np.array(edges).T
    return sparse.csr_matrix((np.ones(2*len(i)),(np.r_[i,j],np.r_[j,i])),shape=(n,n))

def reference(P):
    Z=cp.Variable(P.anchor.shape);d=P.B@Z;objective=.5*cp.sum_squares(Z-P.anchor);constraints=[]
    if P.method=='E1_v2':objective+=cp.sum(cp.multiply(P.r1,cp.pos(cp.norm(d,axis=1)-P.a)))
    elif P.method=='E5':objective+=cp.sum(cp.multiply(P.r1,cp.norm(d,axis=1)))+cp.sum(cp.multiply(P.r2,cp.norm(d-P.edge_H,axis=1)))-P.lam*P.alpha*P.tv_H
    else:objective+=cp.sum(cp.multiply(P.r1,cp.norm(d,axis=1)))
    if P.method=='E6':constraints=[cp.sum(Z,axis=0)==0,(P.Y.T@Z+Z.T@P.Y)/2-P.eta_dir*P.sigma2>>0]
    problem=cp.Problem(cp.Minimize(objective),constraints);problem.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10)
    assert problem.status in ['optimal','optimal_inaccurate'];return problem.value,Z.value

@pytest.mark.parametrize('method',['QSSC','E1_v2','E5','E6'])
def test_independent_convex_objective_and_dual(method):
    H=np.array([[0.,0.],[2.,.2],[.4,1.]]);P=QuadraticProblem(H,graph(3,[(0,1),(1,2),(0,2)]),.15,method)
    value,Z=reference(P);answer=solve(P,rho=.001,cpu_limit=20)
    assert answer['certified'];assert answer['dual']<=value+2e-7;assert answer['primal']>=value-2e-7
    assert abs(answer['primal']-value)<2e-5
    assert abs(answer['stable_gap']-answer['signed_subtracted_gap'])<1e-9
    assert answer['capacity_residual']<=1e-8

@pytest.mark.parametrize('lam',[.1,.9,2.])
def test_E1_two_node_edge_stopping_and_single_edge_factor(lam):
    H=np.array([[-1.],[1.]]);W=graph(2,[(0,1)]);eta=.25;P=QuadraticProblem(H,W,lam,'E1_v2',eta=eta);a=solve(P,rho=.001,cpu_limit=10)
    length=max(2*eta,2-2*lam);assert a['certified'];assert abs(float(a['G'][1,0]-a['G'][0,0])-length)<2e-4
    assert np.isclose(equation8_objective(H,H,W,lam/2),lam*P.tv_H)
    bound=P.scale-np.sqrt((1-eta)**2*P.scale**2+2*max(0.,a['stable_gap']))
    assert linalg.norm(center(a['G']))>=bound-1e-9

def test_exact_baseline_parameter_reductions(tmp_path):
    H=np.array([[0.,0.],[2.,.2],[.4,1.]]);W=graph(3,[(0,1),(1,2),(0,2)]);base=solve(QuadraticProblem(H,W,.1),rho=.001,cpu_limit=10)
    for method,params in [('E1_v2',{'eta':0.}),('E5',{'alpha':0.})]:
        answer=solve(QuadraticProblem(H,W,.1,method,**params),rho=.001,cpu_limit=10);assert np.array_equal(base['G'],answer['G'])
    repaired,info,_=GraphRepair(H,W,H).fit(beta=0);store=ArtifactStore(tmp_path);assert store.put(repaired)==store.put(W)

@pytest.mark.parametrize('method',['QSSC','E1_v2','E5','E6'])
def test_orientation_and_right_rotation_invariance(method):
    H=np.array([[0.,0.],[2.,.2],[.4,1.]]);W=graph(3,[(0,1),(1,2),(0,2)]);rotation=np.array([[.6,-.8],[.8,.6]])
    P=QuadraticProblem(H,W,.15,method);R=QuadraticProblem(H@rotation,W,.15,method);reverse=QuadraticProblem(H,W,.15,method);reverse.B=-reverse.B;reverse.edge_H=-reverse.edge_H
    answers=[solve(p,rho=.001,cpu_limit=10) for p in [P,R,reverse]]
    assert all(a['certified'] for a in answers)
    assert linalg.norm(answers[0]['G']@rotation-answers[1]['G'])<2e-4
    assert linalg.norm(answers[0]['G']-answers[2]['G'])<2e-4

@pytest.mark.parametrize('beta',[.25,1.,4.])
def test_E4_four_cycle_dual_constant_and_degrees(beta):
    H=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]);Z=np.array([[0.],[1.],[1.],[0.]]);edges=np.array([[0,1],[1,2],[2,3],[0,3]]);W=graph(4,[(0,1),(2,3)])
    model=GraphRepair(H,W,Z,edges=edges);new,info,state=model.fit(beta=beta);x=min(beta/4,1.)
    assert info['eligible'];assert np.allclose(state['t'],np.array([1.,0.,1.,0.])+x*np.array([-1,1,-1,1]),atol=1e-7)
    assert info['relative_gap']<=1e-6 and info['degree_residual']<=1e-8 and info['budget_residual']<=1e-8
    assert np.allclose(new.sum(axis=1),W.sum(axis=1),atol=1e-8);assert info['old_edge_floor_min']>=.75-1e-9
    assert np.isclose(info['primal'],info['solver_objective_without_constant']+info['QP_constant'],atol=1e-7)

@pytest.mark.parametrize('lam',[.1,1.2])
def test_E6_two_node_analytic_and_feasible_repair(lam):
    H=np.array([[-1.],[1.]]);P=QuadraticProblem(H,graph(2,[(0,1)]),lam,'E6');a=solve(P,rho=.001,cpu_limit=10);expected=max(.5,1-lam)*H
    assert a['certified'];assert linalg.norm(a['G']-expected)<2e-4;assert a['repair']['whitened_min_eigenvalue']>=.5-1e-8
    fixed,info=P.repair(.1*P.Y);assert info['fraction']>0;assert linalg.eigvalsh(P.whitened(fixed))[0]>=.5-1e-8

def test_E6_rank_deficiency_and_weak_direction_whitened_check():
    H=np.array([[1.,0.,0.],[-1.,0.,0.],[0.,1e-7,0.],[0.,-1e-7,0.]])
    P=QuadraticProblem(H,graph(4,[(0,1),(1,2),(2,3)]),.1,'E6');assert len(P.s)==2
    violated=P.Y@np.diag([1.,.1]);assert np.min(linalg.eigvalsh(sym(P.Y.T@violated)-.5*P.sigma2))>-1e-12
    assert np.min(linalg.eigvalsh(P.whitened(violated)))<.5
    fixed,info=P.repair(violated);assert info['fraction']>0;assert info['whitened_min_eigenvalue']>=.5-1e-8

def test_E5_triangle_slack_and_nonuniform_shape():
    h=np.array([2.,0.])
    for t in [0.,.3,1.]:assert abs(linalg.norm(t*h)+linalg.norm(t*h-h)-linalg.norm(h))<1e-12
    for d in [np.array([-1.,0.]),np.array([3.,0.]),np.array([1.,1.])]:assert linalg.norm(d)+linalg.norm(d-h)>linalg.norm(h)
    H=np.array([[0.,0.],[2.,.2],[.4,1.]]);W=graph(3,[(0,1),(1,2),(0,2)]);P=QuadraticProblem(H,W,.15,'E5');value,Z=reference(P);movement=linalg.norm(Z-H)
    lo,hi=0.,1.
    for _ in range(14):
        lam=(lo+hi)/2;_,Q=reference(QuadraticProblem(H,W,lam));
        if linalg.norm(Q-H)<movement:lo=lam
        else:hi=lam
    assert linalg.norm(Z-Q)>1e-4
    _,large=reference(QuadraticProblem(H,W,.15,'E5',alpha=10000));hc=center(H);gc=center(large);scale=max(0.,np.sum(hc*gc)/np.sum(hc*hc));assert linalg.norm(gc-scale*hc)<1e-3
