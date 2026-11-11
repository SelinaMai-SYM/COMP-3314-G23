import numpy as np
import pytest
import cvxpy as cp
from scipy import sparse
from method_extension.extension_verification.convex import Problem,Hinges,solve,row_norm,rowunit
from method_extension.extension_verification.relative_neighbor import triplet_hinges,random_hinges
from method_extension.extension_verification.dispersion import geometric_median_bounds,dispersion_check


def independent(problem):
    H=problem.H;G=cp.Variable(H.shape);difference=G-H
    objective=cp.sum(cp.norm(difference,axis=1));constraints=[]
    if len(problem.w):
        edge=cp.norm(problem.B@G,axis=1)
        if problem.kind=='relative':edge=cp.pos(edge-problem.a)
        objective+=problem.c@edge
    if problem.kind in ['tangent','ball']:
        constraints.append(cp.norm(difference,axis=1)<=problem.radius)
        if problem.kind=='tangent':
            constraints.append(cp.sum(cp.multiply(H,difference),axis=1)==0)
            if np.any(~problem.active):constraints.append(difference[~problem.active]==0)
    if problem.kind=='relative_neighbor' and len(problem.hinges.anchors):
        t=problem.hinges
        objective+=problem.mu*cp.sum(cp.pos(cp.sum(cp.multiply(t.normals,G[t.anchors]),axis=1)+t.beta))
    reference=cp.Problem(cp.Minimize(objective),constraints)
    value=reference.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_feas=1e-10,tol_gap_rel=1e-10,max_iter=1000)
    assert reference.status in ['optimal','optimal_inaccurate']
    return value


@pytest.mark.parametrize('kind',['ssc','relative','tangent','ball','relative_neighbor'])
@pytest.mark.parametrize('seed',[1,3])
def test_independent_socp_and_saved_duals(kind,seed):
    rng=np.random.default_rng(seed);H=rowunit(rng.normal(size=(5,3)));H[0]=0
    W=np.zeros((5,5))
    for a,b,w in [(0,1,.8),(1,2,1.3),(2,3,.4),(3,4,.9)]:W[a,b]=W[b,a]=w
    hinges=Hinges(np.array([1,3]),rowunit(rng.normal(size=(2,3))),np.array([.3,-.1])) if kind=='relative_neighbor' else None
    problem=Problem(H,sparse.csr_matrix(W),.7,kind=kind,eta=.25,radius=np.tan(np.deg2rad(15)),hinges=hinges)
    result=solve(problem,max_iter=30000,cpu_limit=30)
    ref=independent(problem)
    assert result['certified'],(kind,result['relative_gap'],result['stopping_reason'])
    assert result['dual']<=ref+1e-7
    assert ref<=result['primal']+1e-7
    assert result['primal']-ref<1e-5*max(1,abs(ref))
    B=problem.B;q=result['q'];p=result['p'];s=B.T@q+problem.hinges.adjoint(p,H.shape)
    assert np.max(row_norm(q)-problem.c,initial=0)<=1e-8
    if kind in ['tangent','ball']:
        projected=s-H*np.sum(H*s,axis=1)[:,None] if kind=='tangent' else s
        excess=np.maximum(row_norm(projected)-1,0)
        if kind=='tangent':excess[~problem.active]=0
        dual=float(np.sum(H*(B.T@q)))-problem.radius*excess.sum()
    else:
        assert np.max(row_norm(s),initial=0)<=1+1e-8
        dual=float(np.sum(H*s))
        if kind=='relative':dual-=problem.a@row_norm(q)
        if kind=='relative_neighbor':dual+=problem.hinges.beta@p
    assert abs(dual-result['dual'])<1e-9
    assert max(problem.feasibility(result['G']).values(),default=0)<=1e-8
    if kind=='tangent':
        delta=result['G']-H
        assert np.allclose(np.sum(result['G'][problem.active]**2,axis=1),1+np.sum(delta[problem.active]**2,axis=1),atol=1e-9)
        assert np.array_equal(result['G'][~problem.active],H[~problem.active])


@pytest.mark.parametrize('lam,expected',[(1.6,[6.4,4.8,3.2]),(2.4,[8.,6.,4.])])
def test_symmetric_two_group_reference(lam,expected):
    H=np.array([[0.],[0.],[4.],[4.],[4.]])
    W=np.zeros((5,5));W[:2,2:]=lam/12;W[2:,:2]=lam/12
    # This is the explicit complete bipartite symmetric graph. Group
    # averaging preserves feasibility and cannot increase its convex objective.
    for eta,optimum in zip([0,.25,.5],expected):
        problem=Problem(H,sparse.csr_matrix(W),1,kind='relative',eta=eta)
        result=solve(problem,max_iter=30000,cpu_limit=20)
        assert result['certified']
        assert abs(independent(problem)-optimum)<1e-7
        assert result['primal']-optimum<1e-4
        target=4 if lam<2 else 4*eta
        separation=float(abs(result['G'][:2].mean()-result['G'][2:].mean()))
        assert abs(separation-target)<1e-3
        proof=dispersion_check(H,result['G'],eta,result['absolute_gap'])
        assert proof['status']!='INCONSISTENT_BOUND'


def test_equality_nonuniqueness_and_limiting_cases():
    H=np.array([[0.],[0.],[4.],[4.],[4.]])
    W=np.zeros((5,5));W[:2,2:]=2/12;W[2:,:2]=2/12
    for eta in [0,.25,.5]:
        problem=Problem(H,sparse.csr_matrix(W),1,kind='relative',eta=eta)
        assert abs(independent(problem)-8*(1-eta))<1e-7
        for location in [0,2*(1-eta),4*(1-eta)]:
            G=H.copy();G[:2]=location;assert abs(problem.primal(G)-8*(1-eta))<1e-12
    for eta in [0,.25,1.]:
        for graph,gamma in [(sparse.csr_matrix(W),0),(sparse.csr_matrix((5,5)),12)]:
            result=solve(Problem(H,graph,gamma,kind='relative',eta=eta),cpu_limit=5)
            assert result['certified'] and np.array_equal(result['G'],H)
    result=solve(Problem(H,sparse.csr_matrix(W),3,kind='relative',eta=1),cpu_limit=5)
    assert result['certified'] and result['primal']==0 and np.array_equal(result['G'],H)


def test_hinge_zero_gamma_and_random_force_matching():
    U=rowunit(np.array([[1.,0.],[0.,1.],[-1.,0.],[0.,0.]]))
    hinges=Hinges(np.array([0,1]),rowunit(np.array([[1.,2.],[-1.,1.]])),np.array([.1,.2]))
    W=sparse.csr_matrix((4,4));initial=np.maximum(hinges.apply(U)+hinges.beta,0)
    for mu in [.5,1.,2.]:
        problem=Problem(U,W,0,kind='relative_neighbor',hinges=hinges,mu=mu)
        result=solve(problem,cpu_limit=5);target=U.copy()
        if mu>1:target[hinges.anchors]-=initial[:,None]*hinges.normals
        assert result['certified'] and np.allclose(result['G'],target)
        assert abs(independent(problem)-result['primal'])<1e-7
    for seed in [400,401,402]:
        random,redraws=random_hinges(U,hinges,seed,[30,10,20,40])
        assert not redraws and np.allclose(row_norm(random.normals),1)
        assert np.array_equal(random.anchors,hinges.anchors)
        assert np.allclose(random.apply(U)+random.beta,initial)


def test_median_bounds_duplicates_and_checkpoint_continuation():
    X=np.array([[0.,0.],[0.,0.],[4.,0.],[4.,0.],[4.,0.]])
    bounds=geometric_median_bounds(X);assert bounds['certified_interval'];assert bounds['lower']<=8<=bounds['upper']+1e-12
    H=rowunit(np.random.default_rng(4).normal(size=(6,3)));W=sparse.diags([np.ones(5),np.ones(5)],[-1,1],shape=(6,6)).tocsr();problem=Problem(H,W,1,kind='relative',eta=.25)
    first=solve(problem,max_iter=50,cpu_limit=10);continued=solve(problem,max_iter=30000,cpu_limit=30,checkpoint=first['checkpoint']);full=solve(problem,max_iter=30000,cpu_limit=30)
    assert continued['certified'] and full['certified']
    assert np.allclose(continued['G'],full['G'],atol=1e-10)
    assert abs(continued['primal']-full['primal'])<1e-10
