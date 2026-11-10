"""Scientific state and pinned-reference checks for the submission refresh."""
import ast
from pathlib import Path
import hashlib
import numpy as np
from scipy.linalg import eigh
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import normalized_mutual_info_score
from sklearn.utils import check_random_state
import pytest
from baselines.lda_kmeans import (fit_state, fit_predict,fit_reference_state,fit_adapted_state,
                                  prepare_pca,partitions_equal,trajectory_prefix_matches)
from baselines.lda_kmeans.reference import _source_scatter


def blobs():
    rng=np.random.default_rng(143)
    return np.vstack([rng.normal(size=(20,5))+np.eye(5)[k]*3 for k in range(3)])


def assert_state(X,state):
    Z=(X-state['training_mean']) @ state['projection_used']
    np.testing.assert_allclose(Z,state['representation'],rtol=1e-11,atol=1e-11)
    objective=np.sum((Z-state['centers'][state['labels']])**2)
    np.testing.assert_allclose(objective,state['inertia'],rtol=1e-10,atol=1e-10)


def test_fit_state_preserves_labels_and_trajectory_prefix():
    X=blobs();short=fit_state(X,3,4,n_components=2,max_iter=1)
    long=fit_state(X,3,4,n_components=2,max_iter=3)
    assert trajectory_prefix_matches(short,long)
    np.testing.assert_array_equal(short['labels'],fit_predict(X,3,4,n_components=2,max_iter=1))
    assert_state(X,short);assert_state(X,long)


def test_partition_convergence_uses_bijection():
    assert partitions_equal(np.array([0,0,1,2]),np.array([8,8,3,4]))
    assert not partitions_equal(np.array([0,0,1,2]),np.array([8,3,3,4]))
    assert not partitions_equal(np.array([0,1,2]),np.array([7,7,8]))


def test_adapted_rank_ridge_and_state_at_iteration_cap():
    X=blobs();X=np.column_stack([X,X[:,0],np.ones(len(X))])
    p=prepare_pca(X,3)
    assert p['numerical_rank']==5 and p['p0']==5
    expected=np.finfo(np.float64).eps*max(X.shape)*p['singular_values'][0]
    assert p['rank_tolerance']==expected
    assert p['eta']==1e-6*np.trace(p['St'])/p['p0']
    fit=fit_adapted_state(X,3,7,max_iter=1,prepared=p)
    assert fit['termination_reason']=='MAX_ITER'
    assert fit['lda_update_attempts']==0
    assert fit['inner_kmeans_repetitions']==10
    assert_state(X,fit)
    np.testing.assert_allclose(fit['projection'],fit['pca_projection']@fit['lda_projection'])


def test_adapted_degenerate_and_no_label_interface():
    assert fit_adapted_state(np.ones((12,4)),3,0)['termination_reason']=='DEGENERATE_INPUT'
    with pytest.raises(TypeError):fit_adapted_state(blobs(),3,0,y=np.zeros(60))
    with pytest.raises(TypeError):fit_reference_state(blobs(),3,0,y=np.zeros(60))


def test_reference_failure_is_visible_and_state_stays_consistent():
    X=np.column_stack([blobs(),np.zeros(len(blobs()))])
    state=fit_reference_state(X,3,0,max_iter=2)
    assert state['lda_update_attempts']>=1
    assert state['lda_update_failures']>=1
    assert state['status']=='DEGENERATED_TO_PCA_KMEANS'
    assert any('exception' in row for row in state['history'])
    assert_state(X,state)


def test_reference_at_cap_retains_source_inconsistency():
    X=blobs()
    state=fit_reference_state(X,3,5,max_iter=1)
    assert state['lda_update_successes']==1
    assert not state['returned_state_consistent']
    assert_state(X,state)
    assert not np.allclose(state['representation'],state['source_returned_representation'])


def test_pinned_source_blob_and_exact_core_agreement():
    path=Path(__file__).resolve().parents[2]/'baselines/lda_kmeans/vendor/clustpy/clustpy/centroid/ldakmeans.py'
    source=path.read_bytes()
    assert hashlib.sha1(f'blob {len(source)}\0'.encode()+source).hexdigest()=='e2d952694a20ccabe0d38bd54ba9e5b5c5d4b846'
    tree=ast.parse(source)
    core=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_lda_kmeans')
    namespace={'np':np,'KMeans':KMeans,'PCA':PCA,'nmi':normalized_mutual_info_score,'eigh':eigh,
               '_update_centers_and_scatter_matrix':_source_scatter}
    exec(compile(ast.Module(body=[core],type_ignores=[]),str(path),'exec'),namespace)
    X=blobs();seed=5;local=int(check_random_state(seed).choice(10000,1,replace=False)[0])
    saved=np.random.get_state();np.random.seed(seed)
    try:labels,R,centers,inertia,iters=namespace['_lda_kmeans'](X,3,2,3,10,check_random_state(local))
    finally:np.random.set_state(saved)
    state=fit_reference_state(X,3,seed,max_iter=3)
    np.testing.assert_array_equal(state['labels'],labels)
    np.testing.assert_allclose(state['projection_returned'],R,rtol=0,atol=0)
    np.testing.assert_allclose(state['centers'],centers,rtol=0,atol=0)
    assert state['inertia']==inertia and state['outer_iterations']==iters


def test_generalized_eigenvector_scaling_matches_reference_covariance():
    from baselines.lda_kmeans.lda_kmeans import lda_basis
    X=blobs();state=fit_reference_state(X,3,5,max_iter=1)
    reference=state['projection_returned']
    project=lda_basis(X-X.mean(axis=0),state['labels'],2,0.)
    for j in range(2):
        if np.dot(project[:,j],reference[:,j])<0:
            project[:,j]*=-1
    np.testing.assert_allclose(reference,np.sqrt(len(X)-1)*project,rtol=1e-10,atol=1e-10)


def test_blind_profile_never_calls_evaluator(tmp_path,monkeypatch):
    from experiments.submission_refresh.lda_audit import run_block
    from experiments.submission_refresh.core import ArtifactStore
    import experiments.v2_kmeans_protocol.metrics as metrics
    def forbidden(*args,**kwargs):
        raise AssertionError('Profiling must not evaluate ground-truth labels')
    monkeypatch.setattr(metrics,'evaluate_partition',forbidden)
    X=blobs();store=ArtifactStore(tmp_path/'artifacts')
    for block in ['lda_existing','lda_reference','lda_adapted']:
        run_block({'block':block,'dataset':'synthetic','run_id':block,'profile':True},X,None,3,
                  store,tmp_path/block,{'implementation_hash':'synthetic-test'})
        import json
        record=json.loads((tmp_path/block/(block+'__profile.json')).read_text())
        assert record['status']=='PROFILE_ONLY_INELIGIBLE'
        assert 'NOT_COMPUTED' in record['evaluation']
        assert 'summary' not in record
