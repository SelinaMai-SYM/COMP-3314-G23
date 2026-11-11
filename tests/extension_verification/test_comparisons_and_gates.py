import numpy as np
from scipy import sparse
from method_extension.extension_verification.comparisons import construct,_neighbors
from method_extension.extension_verification.convex import rowunit,row_norm
from method_extension.extension_verification.relative_neighbor import triplet_hinges
from experiments.extension_verification.gates import radial_geometry,semantic_gate,radial_gate


def fixture():
    rng=np.random.default_rng(6);base=np.array([1.,-1.,2.,-2.,3.,-3.,4.,-4.]);X=base+.01*rng.normal(size=(65,8));X[1]=X[0];X[64]=-base
    U=rowunit(rng.normal(size=(65,2)));U[0]=[1.,0.];U[1]=[np.cos(.2),np.sin(.2)];U[64]=[np.cos(.1),np.sin(.1)]
    ids=np.arange(65)+100;ids[0]=20;ids[1]=10;ids[64]=30;W=np.zeros((65,65));W[0,64]=W[64,0]=1
    return X,U,sparse.csr_matrix(W),ids


def test_triplet_construction_respects_frozen_geometry_and_all_valid_roles():
    X,U,W,ids=fixture();result=construct(X,U,W,ids,spatial_shape=[2,4]);assert result['triplets'].tolist()==[[0,1,64]]
    hinges=triplet_hinges(U,result['triplets']);initial=hinges.apply(U)+hinges.beta
    assert 0<initial[0]<=np.sin(np.deg2rad(15))
    for kind in ['invalid_view','zero_anchor']:
        x=X.copy();u=U.copy()
        if kind=='invalid_view':x[64]=1
        else:u[64]=0
        filtered=construct(x,u,W,ids,spatial_shape=[2,4]);assert len(filtered['triplets'])==0
        assert len(filtered['view_norms'])==65
    repeat=construct(X,U,W,ids,spatial_shape=[2,4]);assert np.array_equal(repeat['triplets'],result['triplets'])


def test_neighbor_boundary_ties_use_original_ids_and_split_is_deterministic():
    X=np.zeros((6,2));ids=np.array([50,10,40,20,30,60]);actual=_neighbors(X,ids,3)
    for i in range(6):assert actual[i].tolist()==sorted([j for j in range(6) if j!=i],key=lambda j:ids[j])[:3]
    X,U,W,ids=fixture();a=construct(X,U,W,ids);b=construct(X,U,W,ids)
    assert all(np.array_equal(x,y) for x,y in zip(a['feature_columns'],b['feature_columns']))
    assert set(a['feature_columns'][0]).isdisjoint(a['feature_columns'][1])


def test_radial_zero_and_angle_masks_never_drop_metric_membership():
    U=np.array([[1.,0.],[0.,1.],[0.,0.]]);G=np.array([[0.,0.],[.2,.9],[.1,.2]])
    R,geometry,arrays=radial_geometry(U,G)
    assert np.array_equal(R[2],G[2]);assert arrays['angle_mask'].tolist()==[False,True,False]
    assert geometry['angle_excluded_count']==2 and len(R)==3
    assert np.isfinite(arrays['angle_degrees']).all()
    _,empty,_=radial_geometry(U,U);assert not empty['evaluable']
    gate=radial_gate({'certified':True,'numerically_active':False},empty,None,None);assert not gate['passed']


def test_semantic_gate_counts_ambiguity_and_never_promotes_low_coverage():
    labels=np.array([0,0,1]);gate=semantic_gate(np.array([[0,1,2]]),labels)
    assert gate['correct_fraction']==1 and gate['triplets']==1 and not gate['passed']
    empty=semantic_gate(np.empty((0,3),int),labels);assert empty['correct_fraction'] is None and not empty['passed']
