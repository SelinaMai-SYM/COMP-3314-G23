"""Equation (8) checked against CVXPY. E8 and E13 stay separate."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from SSC_method.objective import equation8_objective
from SSC_method.optimizer import shrink_embedding
from experiments.v3_reproduction.solver_validation import admm_equation8, cvxpy_equation8


def _problem(seed: int = 1):
    rng = np.random.default_rng(seed)
    n_samples, n_components = 16, 3
    embedding = rng.normal(size=(n_samples, n_components))
    features = rng.normal(size=(n_samples, 4))
    distance = np.sum((features[:, None, :] - features[None, :, :]) ** 2, axis=-1)
    np.fill_diagonal(distance, np.inf)
    neighbors = np.argsort(distance, axis=1)[:, :3]
    weights = np.zeros((n_samples, n_samples))
    for i in range(n_samples):
        weights[i, neighbors[i]] = np.exp(-distance[i, neighbors[i]])
    weights = np.maximum(weights, weights.T)
    np.fill_diagonal(weights, 0.0)
    return embedding, sparse.csr_matrix(weights)


def test_admm_matches_cvxpy_objective_not_necessarily_unique_g() -> None:
    embedding, weights = _problem()
    gamma = 1.0
    reference = cvxpy_equation8(embedding, weights, gamma)
    assert reference["status"] == "OPTIMALITY_VERIFIED"
    solved = admm_equation8(embedding, weights, gamma, max_iter=400, tol=1e-5)
    gap = abs(solved["objective"] - reference["objective"])
    assert gap <= 1e-2
    # A nonunique optimum need not reproduce G.
    assert solved["patterns"].shape == embedding.shape


def test_e8_tracks_equation8_and_e13_is_not_the_same_system() -> None:
    embedding, weights = _problem(seed=2)
    gamma = 1.0
    reference = cvxpy_equation8(embedding, weights, gamma)
    e8 = shrink_embedding(
        embedding,
        weights,
        gamma=gamma,
        eps=1e-12,
        tol=1e-10,
        max_iter=300,
        variant="E8",
        zero_residual_floor="median_pairwise",
    )
    e13 = shrink_embedding(
        embedding,
        weights,
        gamma=gamma,
        eps=1e-12,
        tol=1e-10,
        max_iter=300,
        variant="E13",
        zero_residual_floor="median_pairwise",
    )
    e8_obj = equation8_objective(e8.patterns, embedding, weights, gamma)
    e13_obj = equation8_objective(e13.patterns, embedding, weights, gamma)
    assert abs(e8_obj - reference["objective"]) <= 1e-2
    assert e8.laplacian_coefficient == 2.0
    assert e13.laplacian_coefficient == 1.0
    # The printed update is allowed to miss the Equation (8) minimizer.
    assert e13_obj + 1e-6 >= reference["objective"] - 1e-3
