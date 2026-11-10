"""Correctness tests for the nine extensions. Labels are not used to fit."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from SSC_method.graph_construction import knn_affinity
from SSC_method.optimizer import shrink_embedding
from method_extension.common.clustering import (
    consensus_labels,
    disagreement_fraction,
    inertia_best_labels,
    kmeans_once,
)
from method_extension.common.fitting import ExtensionConfig, fit_named_method
from method_extension.common.graphs import (
    clear_graph_cache,
    degree_normalize,
    recurrence_probability,
    total_edge_normalize,
)
from method_extension.common.irls import MATCH_ATOL, MATCH_RTOL, shrink_embedding_alpha


def _blobs(seed: int = 0, n_per: int = 8) -> np.ndarray:
    rng = np.random.default_rng(seed)
    first = rng.normal(loc=-2.0, scale=0.2, size=(n_per, 3))
    second = rng.normal(loc=2.0, scale=0.2, size=(n_per, 3))
    return np.vstack([first, second])


def _finite_symmetric(affinity: sparse.spmatrix) -> None:
    weights = sparse.csr_matrix(affinity)
    assert weights.shape[0] == weights.shape[1]
    assert np.isfinite(weights.data).all()
    if weights.nnz:
        assert np.all(weights.data >= -1e-15)
    assert np.allclose((weights - weights.T).toarray(), 0.0, atol=1e-10)
    assert np.allclose(weights.diagonal(), 0.0)


def test_alpha_one_matches_original_e8_solver():
    features = _blobs()
    state = fit_named_method("ssc", features, 2, gamma=0.7, config=ExtensionConfig(max_iter=40, tol=1e-8, solver="original"))
    reference = shrink_embedding(
        state.embedding,
        state.affinity,
        gamma=0.7,
        variant="E8",
        max_iter=40,
        tol=1e-8,
        G_init=state.embedding,
        zero_residual_floor="median_pairwise",
        eps=1e-8,
    )
    assert reference.laplacian_coefficient == 2.0
    assert np.allclose(state.patterns, reference.patterns, rtol=MATCH_RTOL, atol=MATCH_ATOL)


def test_direct_alpha_vector_of_ones_matches_shrink_embedding():
    rng = np.random.default_rng(4)
    embedding = rng.normal(size=(10, 2))
    affinity, _info = knn_affinity(embedding, k=3)
    reference = shrink_embedding(
        embedding, affinity, gamma=0.5, variant="E8", max_iter=25, tol=1e-8, G_init=embedding
    )
    result = shrink_embedding_alpha(
        embedding,
        affinity,
        alpha=np.ones(10),
        gamma=0.5,
        variant="E8",
        max_iter=25,
        tol=1e-8,
        solver="original",
    )
    assert np.allclose(result.patterns, reference.patterns, rtol=MATCH_RTOL, atol=MATCH_ATOL)


def test_zero_noise_recurrence_matches_original_weights_and_g():
    features = _blobs(1)
    config = ExtensionConfig(noise_rel=0.0, max_iter=30, tol=1e-8, solver="original")
    control = fit_named_method("ssc", features, 2, gamma=1.0, config=config)
    recurrence = fit_named_method("e01", features, 2, gamma=1.0, config=config, embedding=control.embedding)
    assert np.allclose(recurrence.affinity.toarray(), control.affinity.toarray(), atol=1e-10)
    assert np.allclose(recurrence.patterns, control.patterns, rtol=MATCH_RTOL, atol=MATCH_ATOL)


def test_total_edge_normalization_is_only_a_gamma_scale():
    features = _blobs(2)
    config = ExtensionConfig(max_iter=20, tol=1e-8, solver="original")
    control = fit_named_method("ssc", features, 2, gamma=1.0, config=config)
    scaled, info = total_edge_normalize(control.affinity)
    assert info["equivalent_to_global_gamma_scale"] is True
    left = shrink_embedding_alpha(
        control.embedding, scaled, gamma=1.0, max_iter=20, tol=1e-8, variant="E8", solver="original"
    )
    right = shrink_embedding_alpha(
        control.embedding,
        control.affinity,
        gamma=info["applied_scale"],
        max_iter=20,
        tol=1e-8,
        variant="E8",
        solver="original",
    )
    assert np.allclose(left.patterns, right.patterns, rtol=1e-5, atol=1e-5)


def test_degree_normalization_is_not_a_global_scale():
    weights = sparse.csr_matrix(
        np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 0.4],
                [0.0, 0.4, 0.0],
            ]
        )
    )
    normalized = degree_normalize(weights, eps=1e-12)
    ratio = []
    dense_w = weights.toarray()
    dense_n = normalized.toarray()
    for i, j in ((0, 1), (1, 2)):
        ratio.append(dense_n[i, j] / dense_w[i, j])
    assert abs(ratio[0] - ratio[1]) > 1e-6


def test_extensions_are_nonnegative_symmetric_and_ignore_labels():
    features = _blobs(3)
    labels_a = np.zeros(features.shape[0], dtype=int)
    labels_b = np.arange(features.shape[0]) % 2
    config = ExtensionConfig(max_iter=12, tol=1e-6, n_outer=2, solver="original")
    calls = [
        ("e01", "default"),
        ("e02", "default"),
        ("e03", "W"),
        ("e04", "degree"),
        ("e04", "total"),
        ("e05", "fuse"),
        ("e05", "bilateral"),
        ("e06", "default"),
        ("e08", "default"),
        ("e09", "default"),
    ]
    for method, variant in calls:
        left = fit_named_method(method, features, 2, gamma=1.0, variant=variant, config=config, y=labels_a)
        right = fit_named_method(method, features, 2, gamma=1.0, variant=variant, config=config, y=labels_b)
        _finite_symmetric(left.affinity)
        assert left.patterns.shape == features.shape[0:1] + (2,)
        assert np.isfinite(left.patterns).all()
        assert np.allclose(left.patterns, right.patterns)


def test_duplicate_rows_stay_finite():
    features = _blobs(5, n_per=4)
    features = np.vstack([features, features[:1]])
    state = fit_named_method(
        "e01", features, 2, config=ExtensionConfig(max_iter=8, solver="original")
    )
    assert np.isfinite(state.patterns).all()
    assert np.isfinite(state.affinity.data).all()


def test_recurrence_cache_and_determinism():
    clear_graph_cache()
    embedding = _blobs(6)
    import method_extension.common.graphs as graphs

    calls = {"n": 0}
    original = graphs.knn_neighbor_squared_distances

    def wrapped(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    graphs.knn_neighbor_squared_distances = wrapped
    try:
        first = recurrence_probability(embedding, k=3, n_perturbations=4, noise_rel=0.02, seed=3)
        used = calls["n"]
        second = recurrence_probability(embedding, k=3, n_perturbations=4, noise_rel=0.02, seed=3)
        assert calls["n"] == used
        assert np.allclose(first.toarray(), second.toarray())
    finally:
        graphs.knn_neighbor_squared_distances = original
        clear_graph_cache()


def test_e07_selects_by_inertia_not_labels():
    rng = np.random.default_rng(7)
    features = rng.normal(size=(20, 2))
    labels, inertia, _seed = inertia_best_labels(features, 2, [0, 1, 2, 3])
    inertias = [kmeans_once(features, 2, seed, init="random")[1] for seed in range(4)]
    assert inertia == min(inertias)
    agreed = consensus_labels(features, 2, [0])
    only, _inertia = kmeans_once(features, 2, 0, init="random")
    assert disagreement_fraction(only, agreed) == 0.0


def test_e02_matches_cvxpy_on_a_chain():
    cvxpy = pytest.importorskip("cvxpy")
    rng = np.random.default_rng(1)
    embedding = rng.normal(size=(6, 2))
    chain = np.zeros((6, 6))
    for index in range(5):
        chain[index, index + 1] = chain[index + 1, index] = 1.0
    affinity = sparse.csr_matrix(chain)
    alpha = np.array([0.5, 0.8, 1.0, 1.2, 1.7, 2.0])
    result = shrink_embedding_alpha(
        embedding,
        affinity,
        alpha=alpha,
        gamma=0.6,
        eps=1e-9,
        tol=1e-8,
        max_iter=200,
        variant="E8",
        solver="original",
    )
    variable = cvxpy.Variable((6, 2))
    data_term = cvxpy.sum([alpha[i] * cvxpy.norm(variable[i] - embedding[i], 2) for i in range(6)])
    graph_terms = []
    for i in range(6):
        for j in range(6):
            if chain[i, j] > 0.0:
                graph_terms.append(chain[i, j] * cvxpy.norm(variable[i] - variable[j], 2))
    problem = cvxpy.Problem(cvxpy.Minimize(data_term + 0.6 * cvxpy.sum(graph_terms)))
    problem.solve(solver=cvxpy.CLARABEL, verbose=False)
    assert problem.status in {cvxpy.OPTIMAL, cvxpy.OPTIMAL_INACCURATE}
    assert np.allclose(result.patterns, np.asarray(variable.value), rtol=1e-3, atol=1e-3)


def test_e03_placements_are_separate():
    features = _blobs(8)
    config = ExtensionConfig(max_iter=8, solver="original")
    on_w = fit_named_method("e03", features, 2, variant="W", config=config)
    on_a = fit_named_method("e03", features, 2, variant="A", config=config)
    assert on_w.variant == "W" and on_a.variant == "A"
    assert on_w.f_source == "control_eq4"
    assert on_a.f_source == "local_scale_on_A"
