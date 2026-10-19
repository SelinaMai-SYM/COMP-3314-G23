"""Tests for the SSC graph, embedding, objective, and Equation (13) solver."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from scipy import sparse
from scipy.linalg import eigh
from scipy.optimize import minimize

from SSC_method.graph_construction import (
    combinatorial_laplacian,
    knn_affinity,
    knn_neighbor_squared_distances,
    median_positive,
    symmetric_normalized_laplacian,
)
from SSC_method.objective import (
    equation8_objective,
    graph_l2_term,
    reweighted_affinity,
    row_l21_diagonal,
    shrinkage_laplacian,
    sqrt_smoothed_equation8_objective,
    trace_surrogate,
)
from SSC_method.optimizer import shrink_embedding, solve_spd_system
from SSC_method.spectral_embedding import smallest_eigenpairs, spectral_embedding
from SSC_method.ssc import SpectralShrunkClustering


def _chain_affinity(n_samples: int) -> np.ndarray:
    weights = np.zeros((n_samples, n_samples), dtype=np.float64)
    for index in range(n_samples - 1):
        weights[index, index + 1] = 1.0
        weights[index + 1, index] = 1.0
    return weights


def test_knn_bandwidth_is_median_of_positive_squared_distances():
    features = np.array([[0.0], [1.0], [3.0], [6.0]])
    dist2, _ = knn_neighbor_squared_distances(features, k=1)
    expected = float(np.median(dist2[dist2 > 0.0]))
    assert expected == pytest.approx(2.5)
    affinity, info = knn_affinity(features, k=1)
    assert info["delta2"] == pytest.approx(expected)
    assert info["delta2_source"] == "median_positive_knn_squared_distance"
    assert affinity.shape == (4, 4)
    assert np.all(affinity.data >= 0.0)
    assert np.allclose((affinity - affinity.T).toarray(), 0.0)
    assert np.allclose(affinity.diagonal(), 0.0)
    # Point 2's only 1-NN is point 1, at squared distance 4.
    assert affinity[2, 1] == pytest.approx(np.exp(-4.0 / 2.5))


def test_block_knn_matches_dense_on_distinct_distances():
    rng = np.random.default_rng(0)
    features = rng.normal(size=(40, 3))
    dense_dist, dense_idx = knn_neighbor_squared_distances(features, k=5, method="dense")
    block_dist, block_idx = knn_neighbor_squared_distances(features, k=5, method="block")
    assert np.array_equal(dense_idx, block_idx)
    assert np.allclose(dense_dist, block_dist)


def test_normalized_laplacian_symmetry_and_nonnegative_weights():
    rng = np.random.default_rng(1)
    features = rng.normal(size=(12, 4))
    affinity, _ = knn_affinity(features, k=5)
    assert np.all(affinity.data >= 0.0)
    laplacian = symmetric_normalized_laplacian(affinity)
    dense = laplacian.toarray()
    assert dense.shape == (12, 12)
    assert np.allclose(dense, dense.T, atol=1e-12)
    assert np.isfinite(dense).all()
    eigenvalues = eigh(dense, eigvals_only=True)
    assert np.all(np.diff(eigenvalues) >= -1e-10)
    assert eigenvalues[0] == pytest.approx(0.0, abs=1e-8)
    assert eigenvalues[-1] <= 2.0 + 1e-8


def test_two_node_normalized_laplacian_eigenpairs():
    affinity = sparse.csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]]))
    laplacian = symmetric_normalized_laplacian(affinity)
    assert np.allclose(laplacian.toarray(), np.array([[1.0, -1.0], [-1.0, 1.0]]))
    evals, evecs, _ = smallest_eigenpairs(laplacian, n_components=2, dense_threshold=0)
    assert evals == pytest.approx([0.0, 2.0])
    scale = 1.0 / np.sqrt(2.0)
    assert evecs[:, 0] == pytest.approx([scale, scale])
    assert evecs[:, 1] == pytest.approx([scale, -scale])


def test_embedding_shapes_ordering_and_orthonormality():
    rng = np.random.default_rng(2)
    features = rng.normal(size=(15, 5))
    embedding, info = spectral_embedding(features, n_components=3, k=5)
    assert embedding.shape == (15, 3)
    assert np.isfinite(embedding).all()
    eigenvalues = info["eigenvalues"]
    assert eigenvalues.shape == (3,)
    assert np.all(np.diff(eigenvalues) >= -1e-8)
    full = eigh(symmetric_normalized_laplacian(knn_affinity(features, k=5)[0]).toarray(), eigvals_only=True)
    assert eigenvalues == pytest.approx(full[:3])
    assert np.allclose(embedding.T @ embedding, np.eye(3), atol=1e-8)


def test_sparse_eigen_solver_matches_dense_ordering():
    rng = np.random.default_rng(3)
    features = rng.normal(size=(30, 4))
    affinity, _ = knn_affinity(features, k=5)
    laplacian = symmetric_normalized_laplacian(affinity)
    evals, _, solver = smallest_eigenpairs(laplacian, n_components=4, dense_threshold=0)
    assert solver == "scipy.sparse.linalg.eigsh"
    full = eigh(laplacian.toarray(), eigvals_only=True)
    assert np.all(np.diff(evals) >= -1e-8)
    assert evals == pytest.approx(full[:4], abs=1e-6)


def test_equation8_objective_matches_explicit_sum():
    patterns = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    embedding = np.zeros_like(patterns)
    affinity = np.array(
        [
            [0.0, 0.5, 0.0],
            [0.5, 0.0, 0.25],
            [0.0, 0.25, 0.0],
        ]
    )
    manual_data = 0.0 + 1.0 + np.sqrt(2.0)
    manual_graph = (
        0.5 * 1.0
        + 0.5 * 1.0
        + 0.25 * 1.0
        + 0.25 * 1.0
    )
    assert graph_l2_term(patterns, affinity) == pytest.approx(manual_graph)
    assert equation8_objective(patterns, embedding, affinity, gamma=2.0) == pytest.approx(
        manual_data + 2.0 * manual_graph
    )


def test_exact_and_sqrt_smoothed_objectives_differ():
    embedding = np.array([[0.0, 0.0], [1.0, 0.0]])
    affinity = np.array([[0.0, 1.0], [1.0, 0.0]])
    exact = equation8_objective(embedding, embedding, affinity, gamma=1.0)
    smoothed = sqrt_smoothed_equation8_objective(embedding, embedding, affinity, gamma=1.0, eps=1e-2)
    assert exact == pytest.approx(2.0)
    assert smoothed > exact


def test_row_wise_s_shape_and_hand_value():
    residual = np.array([[3.0, 4.0], [0.0, 0.0]])
    diagonal = row_l21_diagonal(residual, eps=1e-8)
    assert diagonal.shape == (2,)
    assert diagonal[0] == pytest.approx(1.0 / (2.0 * 5.0))
    assert diagonal[1] == pytest.approx(1.0 / (2.0 * 1e-8))


def test_laplacian_trace_identity_on_hand_example():
    # G rows 0.2 and 0.8, W fully connects the single unordered edge once
    # in each direction. See docs/ssc_mathematical_audit.md.
    patterns = np.array([[0.2], [0.8]])
    affinity = sparse.csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]]))
    distance = 0.6
    sum_w_sq = 2.0 * distance**2
    sum_w_dist = 2.0 * distance
    reweighted = reweighted_affinity(affinity, patterns, eps=1e-15)
    laplacian = combinatorial_laplacian(reweighted)
    quadratic = float(np.sum(patterns * (laplacian @ patterns)))
    sum_reweighted_sq = 2.0 * (1.0 / (2.0 * distance)) * distance**2
    assert sum_w_sq == pytest.approx(0.72)
    assert sum_reweighted_sq == pytest.approx(0.6)
    assert quadratic == pytest.approx(0.3)
    assert sum_reweighted_sq == pytest.approx(2.0 * quadratic)
    assert sum_reweighted_sq == pytest.approx(0.5 * sum_w_dist)


def test_lemma1_and_majorizer_coefficient():
    rng = np.random.default_rng(4)
    vector = rng.normal(size=5)
    reference = rng.normal(size=5)
    reference_norm = np.linalg.norm(reference)
    left = np.linalg.norm(vector) - np.dot(vector, vector) / (2.0 * reference_norm)
    right = reference_norm - np.dot(reference, reference) / (2.0 * reference_norm)
    assert left <= right + 1e-10

    n_samples, n_components = 5, 2
    embedding = rng.normal(size=(n_samples, n_components))
    current = embedding + rng.normal(size=(n_samples, n_components))
    affinity = _chain_affinity(n_samples)
    gamma = 0.8
    eps = 1e-12
    s_diagonal = row_l21_diagonal(current - embedding, eps=eps)
    reweighted, laplacian = shrinkage_laplacian(sparse.csr_matrix(affinity), current, eps=eps)

    def majorizer(patterns: np.ndarray) -> float:
        # Equation (15): f(G) + gamma * sum Wtilde_ij ||g_i - g_j||^2,
        # with S and Wtilde frozen at `current`.
        data = trace_surrogate(patterns, embedding, s_diagonal, np.zeros_like(affinity), gamma=0.0)
        coo = reweighted.tocoo()
        difference = patterns[coo.row] - patterns[coo.col]
        squared = np.sum(difference * difference, axis=1)
        return data + gamma * float(np.sum(coo.data * squared))

    rhs = s_diagonal[:, None] * embedding
    solved_eq13 = solve_spd_system(sparse.diags(s_diagonal) + gamma * laplacian, rhs)
    solved_eq8 = solve_spd_system(sparse.diags(s_diagonal) + (2.0 * gamma) * laplacian, rhs)
    assert majorizer(solved_eq8) <= majorizer(solved_eq13) + 1e-8
    assert majorizer(solved_eq8) <= majorizer(current) + 1e-7


def test_linear_solve_matches_dense_factorization_and_scipy_optimize():
    rng = np.random.default_rng(5)
    n_samples, n_components = 6, 2
    embedding = rng.normal(size=(n_samples, n_components))
    current = embedding + 0.2 * rng.normal(size=(n_samples, n_components))
    affinity = sparse.csr_matrix(_chain_affinity(n_samples))
    gamma = 0.7
    s_diagonal = row_l21_diagonal(current - embedding, eps=1e-8)
    _, laplacian = shrinkage_laplacian(affinity, current, eps=1e-8)
    coefficient = sparse.diags(s_diagonal) + gamma * laplacian
    rhs = s_diagonal[:, None] * embedding
    solved = solve_spd_system(coefficient, rhs)
    dense = np.linalg.solve(coefficient.toarray(), rhs)
    assert np.allclose(solved, dense, rtol=1e-8, atol=1e-8)
    residual = coefficient @ solved - rhs
    assert np.linalg.norm(residual) < 1e-8

    def quadratic(flat: np.ndarray) -> float:
        return trace_surrogate(flat.reshape(n_samples, n_components), embedding, s_diagonal, laplacian, gamma)

    start = rng.normal(size=n_samples * n_components)
    optimized = minimize(quadratic, start, method="L-BFGS-B", tol=1e-14)
    assert optimized.success
    assert quadratic(solved.ravel()) == pytest.approx(optimized.fun, rel=1e-6, abs=1e-8)
    assert np.allclose(optimized.x.reshape(n_samples, n_components), solved, rtol=1e-4, atol=1e-4)


def test_equation13_fixed_point_matches_cvxpy_halved_graph_term():
    cvxpy = pytest.importorskip("cvxpy")
    rng = np.random.default_rng(1)
    n_samples, n_components = 6, 2
    embedding = rng.normal(size=(n_samples, n_components))
    affinity = sparse.csr_matrix(_chain_affinity(n_samples))
    gamma = 0.8
    result = shrink_embedding(
        embedding,
        affinity,
        gamma=gamma,
        eps=1e-9,
        tol=1e-6,
        max_iter=300,
        zero_residual_floor="median_pairwise",
    )
    assert result.converged
    assert result.fixed_point_residual < 5e-5
    assert np.isfinite(result.patterns).all()
    for record in result.history:
        assert np.isfinite(record["equation8_objective"])
        assert np.isfinite(record["sqrt_smoothed_equation8_objective"])
        assert record["linear_residual"] < 1e-6

    def solve_exact(graph_coefficient: float) -> tuple[np.ndarray, float]:
        variable = cvxpy.Variable((n_samples, n_components))
        data_term = cvxpy.sum([cvxpy.norm(variable[i] - embedding[i], 2) for i in range(n_samples)])
        graph_terms = []
        dense = affinity.toarray()
        for i in range(n_samples):
            for j in range(n_samples):
                if dense[i, j] > 0.0:
                    graph_terms.append(dense[i, j] * cvxpy.norm(variable[i] - variable[j], 2))
        problem = cvxpy.Problem(cvxpy.Minimize(data_term + graph_coefficient * cvxpy.sum(graph_terms)))
        problem.solve(solver=cvxpy.CLARABEL, verbose=False)
        if problem.status not in {cvxpy.OPTIMAL, cvxpy.OPTIMAL_INACCURATE}:
            raise AssertionError(f"cvxpy status {problem.status}")
        return np.asarray(variable.value, dtype=np.float64), float(problem.value)

    # Equation (13) is the IRLS fixed point of Equation (8) with the graph
    # term halved. The literal Equation (8) uses the printed gamma.
    halved_reference, halved_value = solve_exact(gamma / 2.0)
    full_reference, full_value = solve_exact(gamma)
    halved_at_solution = equation8_objective(result.patterns, embedding, affinity, gamma / 2.0)
    full_at_solution = equation8_objective(result.patterns, embedding, affinity, gamma)
    full_at_reference = equation8_objective(full_reference, embedding, affinity, gamma)
    # A visible epsilon, not the solver floor, so the smoothed value cannot
    # collapse to the exact value by floating-point cancellation.
    smoothed_at_solution = sqrt_smoothed_equation8_objective(
        result.patterns, embedding, affinity, gamma / 2.0, eps=1e-2
    )
    assert smoothed_at_solution > halved_at_solution
    assert halved_at_solution == pytest.approx(halved_value, rel=1e-4, abs=1e-5)
    assert np.allclose(result.patterns, halved_reference, rtol=1e-3, atol=1e-3)
    # Printed Equation (13) is not the minimizer of literal Equation (8).
    # The independent solver of Equation (8) attains a strictly smaller value.
    assert full_value < full_at_solution - 1e-2
    assert full_at_reference <= full_at_solution - 1e-2
    assert full_value == pytest.approx(full_at_reference, rel=1e-4, abs=1e-5)


def test_literal_eps_floor_from_g_equals_f_does_not_leave_f():
    embedding = np.column_stack([np.linspace(0.0, 1.0, 6), np.linspace(1.0, 0.0, 6)])
    affinity = sparse.csr_matrix(_chain_affinity(6))
    result = shrink_embedding(
        embedding,
        affinity,
        gamma=1.0,
        eps=1e-8,
        tol=1e-14,
        max_iter=30,
        zero_residual_floor="eps",
    )
    assert np.linalg.norm(result.patterns - embedding) < 1e-5


def test_zero_gamma_returns_embedding():
    embedding = np.array([[0.0, 1.0], [1.0, 0.0], [0.2, 0.3], [0.7, 0.4]])
    affinity = sparse.csr_matrix(_chain_affinity(4))
    result = shrink_embedding(embedding, affinity, gamma=0.0, eps=1e-8, tol=1e-12, max_iter=5)
    assert np.allclose(result.patterns, embedding, atol=1e-8)
    assert equation8_objective(result.patterns, embedding, affinity, gamma=0.0) == pytest.approx(0.0)


def test_solver_source_does_not_invert():
    root = Path(__file__).resolve().parents[1] / "SSC_method"
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "linalg.inv" not in text
    assert "linalg.pinv" not in text
    assert "/Users/" not in text


def test_ssc_shapes_reproducibility_and_ignored_labels():
    rng = np.random.default_rng(6)
    first = rng.normal(loc=-2.0, scale=0.15, size=(8, 3))
    second = rng.normal(loc=2.0, scale=0.15, size=(8, 3))
    features = np.vstack([first, second])
    model = SpectralShrunkClustering(
        n_clusters=2,
        gamma=1.0,
        k=5,
        tol=1e-5,
        max_iter=100,
        kmeans_n_init=10,
        kmeans_random_state=0,
    )
    labels = model.fit_predict(features)
    assert model.embedding_.shape == (16, 2)
    assert model.shrunk_.shape == (16, 2)
    assert labels.shape == (16,)
    assert model.affinity_.shape == (16, 16)
    assert np.isfinite(model.shrunk_).all()
    assert np.isfinite(model.embedding_).all()
    assert np.all(np.diff(model.info_["embedding_eigenvalues"]) >= -1e-8)
    assert model.converged_
    assert model.objective_history_[-1]["linear_residual"] < 1e-6
    assert np.isfinite(model.fixed_point_residual_)
    assert model.info_["g0"] == "F"
    assert model.info_["linear_update"] == "equation_13"
    other = SpectralShrunkClustering(
        n_clusters=2, gamma=1.0, k=5, tol=1e-5, max_iter=100, kmeans_n_init=10, kmeans_random_state=0
    )
    other_labels = other.fit_predict(features, y=np.ones(16, dtype=int))
    assert np.array_equal(labels, other_labels)
    assert np.allclose(model.shrunk_, other.shrunk_)
    assert np.allclose(model.embedding_, other.embedding_)


def test_degenerate_inputs():
    with pytest.raises(ValueError):
        SpectralShrunkClustering(n_clusters=2, k=2).fit(np.ones((1, 3)))
    with pytest.raises(ValueError):
        SpectralShrunkClustering(n_clusters=5, k=1).fit(np.eye(3))
    with pytest.raises(ValueError):
        SpectralShrunkClustering(n_clusters=2, k=4).fit(np.eye(4))
    with pytest.raises(ValueError):
        SpectralShrunkClustering(n_clusters=2).fit(np.array([[0.0, np.nan], [1.0, 2.0]]))
    with pytest.raises(ValueError):
        shrink_embedding(np.eye(3), np.eye(3), gamma=-1.0)
    identical = np.ones((6, 2))
    model = SpectralShrunkClustering(n_clusters=2, k=2, max_iter=20, kmeans_random_state=0)
    labels = model.fit_predict(identical)
    assert labels.shape == (6,)
    assert np.isfinite(model.shrunk_).all()
    assert np.all(model.affinity_.data >= 0.0)
    assert median_positive(np.array([0.0, 0.0]), fallback=1.0) == 1.0
