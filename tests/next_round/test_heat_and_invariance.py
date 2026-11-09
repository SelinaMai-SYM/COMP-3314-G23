import numpy as np
from scipy import sparse
from scipy.linalg import expm
from SSC_method.graph_construction import symmetric_normalized_laplacian
from method_extension.next_round.heat_geometry import project_heat
from method_extension.next_round.certified_solver import graph_arrays,objective,threshold


def test_exact_heat_action_distance_and_duhamel_bound():
    A=sparse.diags([np.ones(5),np.ones(5)],[-1,1],shape=(6,6)).tocsr();changed=A.copy();changed.data*=np.random.default_rng(200).uniform(.95,1.05,A.nnz);changed=(changed+changed.T)/2
    L=symmetric_normalized_laplacian(A);Lp=symmetric_normalized_laplacian(changed);t=4.;H,_=project_heat(L,t,r=6,R=np.eye(6));K=expm(-t*L.toarray());Kp=expm(-t*Lp.toarray())
    np.testing.assert_allclose(H@H.T,K,atol=1e-12)
    for i,j in [(0,1),(1,5)]:
        d=np.sum((H[i]-H[j])**2)
        np.testing.assert_allclose(d,K[i,i]+K[j,j]-2*K[i,j],atol=1e-12)
    assert np.linalg.norm(K-Kp,2)<=t*np.linalg.norm((L-Lp).toarray(),2)+1e-12


def test_radial_rotation_invariance_and_finite_sufficient_threshold():
    F=np.array([[0.,0],[.4,.1],[1.,.7]]);G=F+np.array([[.2,.4],[-.2,.1],[.5,-.1]]);W=sparse.csr_matrix([[0,1,0],[1,0,1],[0,1,0]]);B,_,_,w=graph_arrays(W)
    Q=np.array([[1.,-1.],[1.,1.]])/np.sqrt(2)
    for delta in [0,.3]:np.testing.assert_allclose(objective(G,F,B,w,delta=delta),objective(G@Q,F@Q,B,w,delta=delta),atol=1e-12)
    tinyF=np.array([[0.],[1e-20]]);tinyW=sparse.csr_matrix([[0,1],[1,0]])
    assert np.isfinite(threshold(tinyF,tinyW)['gamma0'])
