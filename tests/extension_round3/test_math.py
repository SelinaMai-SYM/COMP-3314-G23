"""Independent references for the round's algebra and convex subproblems."""
import numpy as np
import pytest
from scipy import sparse
from method_extension.extension_round3.evidence import edge_deletion_evidence
from method_extension.extension_round3.weighted_midrank import weighted_midrank
from method_extension.extension_round3.e7_cavity_graph import graph_weights
from method_extension.extension_round3.e1_v3_selective_tube import tube_distances
from method_extension.extension_round3.e5_v2_selective_guard import guard_coefficients
from method_extension.extension_round3.convex import FusionProblem,solve,eligible
from experiments.extension_round3.rounding import fit,anchor_indices


def graph(n,edges):
    i,j,w=zip(*edges);return sparse.csr_matrix((list(w)*2,(list(i)+list(j),list(j)+list(i))),shape=(n,n))

def test_deleted_edge_and_equivariance():
    rng=np.random.default_rng(9);H=rng.normal(size=(7,3));W=graph(7,[(0,1,2.),(1,2,.8),(2,3,.03),(3,4,1.),(4,5,1.),(5,6,.7),(0,2,.4)])
    E=edge_deletion_evidence(H,W);P=FusionProblem(H,W,1.);L=(P.B.T@sparse.diags(P.w)@P.B).toarray()
    for k,(i,j,w) in enumerate(zip(P.i,P.j,P.w)):
        b=P.B[k].toarray().ravel();Z=np.linalg.solve(np.eye(7)+E['tau']*(L-w*np.outer(b,b)),H)
        np.testing.assert_allclose(Z[i]-Z[j],(E['Z'][i]-E['Z'][j])/E['denominator'][k],atol=1e-11)
    rotation=np.linalg.qr(rng.normal(size=(3,3)))[0]
    for H2,W2 in [(H+3,W),(H@rotation,W),(H,W*7)]:
        F=edge_deletion_evidence(H2,W2);np.testing.assert_allclose(F['scores']['cavity'],E['scores']['cavity'],atol=1e-11)
    perm=rng.permutation(7);F=edge_deletion_evidence(H[perm],W[perm][:,perm]);mapping={tuple(sorted((perm[i],perm[j]))):s for i,j,s in zip(F['i'],F['j'],F['scores']['cavity'])}
    np.testing.assert_allclose([mapping[(i,j)] for i,j in zip(E['i'],E['j'])],E['scores']['cavity'],atol=1e-11)
    T=edge_deletion_evidence(np.array([[0.],[2.]]),graph(2,[(0,1,1.)]),tau_multiplier=5.)
    np.testing.assert_allclose(abs(T['Z'][0]-T['Z'][1]),2/11);np.testing.assert_allclose(T['scores']['cavity'],[4.]);assert np.all(T['denominator']>=T['denominator_bound']-1e-12)


def test_ranks_and_budgets():
    s=np.array([0.,2.,2.,5.]);w=np.array([1.,4.,2.,3.]);u,meta=weighted_midrank(s,w);assert abs(w@u-w.sum()/2)<1e-13;assert u[1]==u[2]
    np.testing.assert_allclose(u,[.05,.4,.4,.85],atol=1e-15)
    permutation=np.array([2,0,3,1]);v,_=weighted_midrank(s[permutation],w[permutation]);np.testing.assert_allclose(v,u[permutation])
    new,m=graph_weights(w,s);assert np.all(new>=.8*w);assert abs(new.sum()-.9*w.sum())<1e-12
    a0=np.array([0.,2.,3.,1.]);a,m=tube_distances(w,a0,s);assert abs(w@a-.25*(w@a0))<1e-12
    alpha,m=guard_coefficients(w,s);assert abs(w@alpha-w.sum())<1e-12
    np.testing.assert_allclose(graph_weights(w,np.ones(4))[0],.9*w)
    np.testing.assert_allclose(tube_distances(w,a0,np.ones(4))[0],.25*a0)
    np.testing.assert_allclose(guard_coefficients(w,np.ones(4))[0],1.)


@pytest.mark.parametrize('kind',['quadratic','tube','guard','graph'])
def test_convex_reference(kind):
    import cvxpy as cp
    rng=np.random.default_rng(12);H=rng.normal(size=(6,2));H[1]=H[0];W=graph(6,[(0,1,1.),(1,2,.7),(2,3,1.3),(3,4,.5)])
    s=np.array([1.,3.,2.,4.]);base=FusionProblem(H,W,.17);kw={}
    if kind=='tube':kw['tubes']=tube_distances(base.w,np.linalg.norm(base.h,axis=1),s)[0]
    if kind=='guard':kw['alpha']=guard_coefficients(base.w,s)[0]
    if kind=='graph':kw['weights']=graph_weights(base.w,s)[0]
    P=FusionProblem(H,W,.17,**kw);G=cp.Variable(H.shape);e=P.B@G;obj=.5*cp.sum_squares(G-H)
    if kind=='guard':
        alpha=kw['alpha'];anchor=np.linalg.norm(base.B@H,axis=1)
        obj+=.17*cp.sum(cp.multiply(base.w,cp.norm(e,axis=1)+cp.multiply(alpha,cp.norm(e,axis=1)+cp.norm(e-base.B@H,axis=1)-anchor)))
    else:
        weights=kw.get('weights',base.w);tubes=kw.get('tubes',np.zeros(len(base.w)))
        obj+=.17*cp.sum(cp.multiply(weights,cp.pos(cp.norm(e,axis=1)-tubes)))
    reference=cp.Problem(cp.Minimize(obj));reference.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_feas=1e-10,tol_gap_rel=1e-10)
    out=solve(P,rho=.05,cpu_limit=30.)
    assert eligible(out,.05);assert out['dual']<=reference.value+1e-8;assert abs(out['primal']-reference.value)<1e-6
    np.testing.assert_allclose(out['G'],G.value,atol=8e-4)
    assert np.linalg.norm(out['G'][-1]-H[-1])<1e-12


def test_requested_target_and_rounding():
    c={'valid_bound':True,'relative_gap':1e-8,'capacity_residual':0.,'movement_error':.0004}
    assert eligible(c,.1);assert not eligible(c,.05)
    from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,GREEDY
    rng=np.random.default_rng(3);H=rng.normal(size=(30,3));indices=anchor_indices(H,4)
    for seed in [0,1,7]:
        own=fit(H,4,seed);old=fit_lloyd(H,4,seed,GREEDY);np.testing.assert_array_equal(own['labels'],old['labels']);np.testing.assert_array_equal(own['initial_indices'],indices[seed])
        fixed=fit(H+.1,4,seed,indices=indices[seed]);np.testing.assert_array_equal(fixed['initial_indices'],indices[seed])


def test_quadratic_dispatch_is_score_free():
    from experiments.extension_round3.calibration import parameters
    H=np.array([[0.],[1.]]);W=graph(2,[(0,1,1.)])
    kw,meta=parameters(H,W,{'scores':{}},{'family':'quadratic','score':'none'})
    assert kw=={} and meta=={}


def test_control_parameters_and_degenerate_solutions():
    from experiments.extension_round3.calibration import parameters
    H=np.array([[0.],[1.],[2.]]);W=graph(3,[(0,1,1.),(1,2,2.)]);scores={'cavity':np.array([1.,2.]),'pilot':np.array([2.,1.])}
    for family,key in [('graph','weights'),('tube','tubes'),('guard','alpha')]:
        a,_=parameters(H,W,{'scores':scores},{'family':family,'score':'cavity'})
        b,_=parameters(H,W,{'scores':scores},{'family':family,'score':'pilot'})
        assert set(a)=={key} and set(b)=={key}
        assert not np.array_equal(a[key],b[key])
    P=FusionProblem(H,W,.1,alpha=np.zeros(2));Q=FusionProblem(H,W,.1)
    a=solve(P,rho=.1,cpu_limit=10.);b=solve(Q,rho=.1,cpu_limit=10.);np.testing.assert_allclose(a['G'],b['G'],atol=1e-3)
    zero=np.zeros((3,1));out=solve(FusionProblem(zero,W,1.),rho=.1,cpu_limit=10.);assert out['certified'];np.testing.assert_array_equal(out['G'],zero)


def test_fixed_lambda_continuation_preserves_prior_segment(tmp_path):
    from experiments.extension_round3.calibration import calibrate
    from experiments.extension_round3.common import ArtifactStore,put_arrays,scalar,atomic_json,read
    H=np.array([[0.],[1.],[3.]]);W=graph(3,[(0,1,1.),(1,2,.7)])
    store=ArtifactStore(tmp_path);folder=tmp_path/'paths'/'continuation';folder.mkdir(parents=True)
    old=solve(FusionProblem(H,W,.2),rho=.1,max_iter=1,cpu_limit=10.)
    point={'lambda':.2,'rho_requested':.1,'certificate':scalar(old),'result':put_arrays(store,old),'history_file':'prior.jsonl'}
    atomic_json(folder/'path.json',{'points':[point],'CPU_seconds':old['CPU_seconds'],'targets':{}})
    result,outcome=calibrate(H,W,{},.1,folder,cpu_limit=20.,max_iter=2000000)
    path=read(folder/'path.json');assert path['points'][0]['segments'][0]['result']==point['result']
    assert path['points'][0]['fit_CPU_seconds']>=old['CPU_seconds']
    assert len({p['lambda'] for p in path['points']})==len(path['points'])


def test_bad_bridge_and_genuine_sparse_bridge_have_the_same_algebra():
    # Identical geometry can receive two class interpretations. Edge deletion
    # is exact in each, and by itself cannot distinguish those interpretations.
    edges=[(0,1,1.),(0,2,1.),(1,2,1.),(3,4,1.),(3,5,1.),(4,5,1.),(2,3,.2)]
    W=graph(6,edges);H=np.array([[-1.],[-.9],[-1.1],[1.],[.9],[1.1]])
    E=edge_deletion_evidence(H,W);P=FusionProblem(H,W,1.);k=int(np.flatnonzero((P.i==2)&(P.j==3))[0]);b=P.B[k].toarray().ravel();L=(P.B.T@sparse.diags(P.w)@P.B).toarray()
    deleted=np.linalg.solve(np.eye(6)+E['tau']*(L-P.w[k]*np.outer(b,b)),H)
    np.testing.assert_allclose(deleted[2]-deleted[3],(E['Z'][2]-E['Z'][3])/E['denominator'][k],atol=1e-11)
    assert E['scores']['cavity'][k]>E['scores']['pilot'][k]
    bad_bridge_classes=np.array([0,0,0,1,1,1]);genuine_bridge_classes=np.zeros(6,dtype=int)
    assert bad_bridge_classes[2]!=bad_bridge_classes[3]
    assert genuine_bridge_classes[2]==genuine_bridge_classes[3]


def test_reported_leverage_minimum_is_not_clamped_to_zero(tmp_path):
    from experiments.extension_round3.common import ArtifactStore,put_arrays,atomic_json
    from experiments.extension_round3.evaluate import mechanisms
    H=np.array([[0.],[2.]]);W=graph(2,[(0,1,1.)]);store=ArtifactStore(tmp_path)
    lock={'cohorts':{'toy':{'objects':{'H':store.put(H),'W0':store.put(W)}}}}
    E=edge_deletion_evidence(H,W,tau_multiplier=5.)
    atomic_json(tmp_path/'evidence/toy__t5.json',{'result':put_arrays(store,E)})
    record={'id':'toy','benchmark':'toy','method':'SC','rho':0.,'tau_multiplier':5.}
    diagnostic=mechanisms(store,lock,record,H,np.array([0,1]))
    assert diagnostic['leverage_min']==pytest.approx(10/11)
    assert diagnostic['leverage_max']==pytest.approx(10/11)
    assert diagnostic['pilot_cross_class_auroc'] is None
