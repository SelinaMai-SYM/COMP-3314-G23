"""Synthetic certificates for the five prespecified objectives."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from SSC_method.objective import equation8_objective
from SSC_method.optimizer import shrink_embedding
from method_extension.v3_theory.common.graphs import apply_stability, normalize_each_and_average, total_mass
from method_extension.v3_theory.common.objectives import weighted_objective
from method_extension.v3_theory.common.solvers import admm_weighted, cvxpy_weighted, shrink_weighted
from method_extension.v3_theory.x1_certified_path.threshold import g_equals_f_is_optimal, ordered_pair_threshold
from method_extension.v3_theory.x3_graph_calibration.calibrate import equivalent_gamma
from method_extension.v3_theory.x5_adaptive_fidelity.weights import adaptive_fidelity


def _path_problem():
    features = np.array([[0.0, 0.0], [1.0, 0.0], [2.2, 0.4], [3.4, -0.2]], dtype=np.float64)
    rows = np.array([0, 1, 1, 2, 2, 3])
    cols = np.array([1, 0, 2, 1, 3, 2])
    data = np.array([0.8, 0.8, 0.5, 0.5, 0.4, 0.4])
    affinity = sparse.csr_matrix((data, (rows, cols)), shape=(4, 4))
    return features, affinity


def test_alpha_zero_matches_frozen_e8():
    features, affinity = _path_problem()
    fidelity = adaptive_fidelity(features, affinity, alpha=0.0)
    assert np.allclose(fidelity, 1.0)
    frozen = shrink_embedding(features, affinity, gamma=0.3, variant="E8", max_iter=40)
    weighted = shrink_weighted(features, affinity, 0.3, fidelity, variant="E8", max_iter=40)
    assert np.allclose(weighted["patterns"], frozen.patterns)
    assert np.isclose(
        weighted["objective"],
        equation8_objective(frozen.patterns, features, affinity, 0.3),
    )


def test_threshold_against_cvxpy():
    features, affinity = _path_problem()
    threshold = ordered_pair_threshold(features, affinity)
    gamma_0 = threshold["gamma_0"]
    assert np.isfinite(gamma_0) and gamma_0 > 0.0
    assert threshold["n_coincident_edges"] == 0
    below = cvxpy_weighted(features, affinity, gamma_0 * 0.5)
    at_boundary = cvxpy_weighted(features, affinity, gamma_0)
    above = cvxpy_weighted(features, affinity, gamma_0 * 4.0)
    assert below["status"] == "NUMERICAL_REFERENCE_UNCERTIFIED"
    assert at_boundary["status"] == "NUMERICAL_REFERENCE_UNCERTIFIED"
    base_below = equation8_objective(features, features, affinity, gamma_0 * 0.5)
    base_at = equation8_objective(features, features, affinity, gamma_0)
    base_above = equation8_objective(features, features, affinity, gamma_0 * 4.0)
    assert abs(below["objective"] - base_below) <= 1e-2 * max(1.0, abs(base_below))
    assert abs(at_boundary["objective"] - base_at) <= 2e-2 * max(1.0, abs(base_at))
    assert above["objective"] < base_above - 1e-3
    assert g_equals_f_is_optimal(threshold, gamma_0 * 0.5)
    assert not g_equals_f_is_optimal(threshold, gamma_0 * 4.0)


def test_coincident_edge_does_not_divide_by_zero():
    features = np.array([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0]], dtype=np.float64)
    affinity = sparse.csr_matrix(
        [
            [0.0, 1.0, 0.7],
            [1.0, 0.0, 0.0],
            [0.7, 0.0, 0.0],
        ]
    )
    threshold = ordered_pair_threshold(features, affinity)
    assert threshold["n_coincident_edges"] == 1
    assert np.isfinite(threshold["gamma_0"])
    assert threshold["threshold_source"].startswith("coincident_subgradient")


def test_admm_matches_cvxpy_on_weighted_objective():
    features, affinity = _path_problem()
    fidelity = np.array([0.5, 1.0, 1.5, 0.8])
    reference = cvxpy_weighted(features, affinity, 0.4, fidelity)
    solved = admm_weighted(features, affinity, 0.4, fidelity, max_iter=400, tol=1e-5)
    assert reference["status"] == "NUMERICAL_REFERENCE_UNCERTIFIED"
    assert abs(solved["objective"] - reference["objective"]) <= 1e-2 * max(1.0, abs(reference["objective"]))
    irls = shrink_weighted(features, affinity, 0.4, fidelity, variant="E8", max_iter=80)
    assert abs(irls["objective"] - reference["objective"]) <= 1e-2 * max(1.0, abs(reference["objective"]))


def test_beta_zero_restores_original_mass_and_weights():
    _features, affinity = _path_problem()
    fraction = sparse.csr_matrix(
        [
            [0, 0.2, 0, 0],
            [0.2, 0, 0.8, 0],
            [0, 0.8, 0, 0.1],
            [0, 0, 0.1, 0],
        ]
    )
    stable = apply_stability(affinity, fraction, beta=0.0)
    assert np.isclose(total_mass(stable), total_mass(affinity))
    assert np.allclose(stable.toarray(), affinity.toarray())


def test_mass_normalization_is_exact_gamma_rescaling():
    features, affinity = _path_problem()
    mass = float(affinity.sum() / affinity.shape[0])
    tau = 0.7
    gamma = equivalent_gamma(tau, mass)
    left = shrink_weighted(features, affinity / max(mass, 1e-12), tau, variant="E8", max_iter=50)
    right = shrink_weighted(features, affinity, gamma, variant="E8", max_iter=50)
    assert np.allclose(left["patterns"], right["patterns"], atol=1e-6)
    assert np.isclose(left["objective"], weighted_objective(right["patterns"], features, affinity / max(mass, 1e-12), tau))


def test_multiscale_alphas_are_fixed():
    graphs = []
    for scale in (0.2, 0.5, 0.9, 1.3):
        weight = np.array(
            [
                [0, scale, 0, 0],
                [scale, 0, scale, 0],
                [0, scale, 0, scale],
                [0, 0, scale, 0],
            ]
        )
        graphs.append(sparse.csr_matrix(weight))
    combined = normalize_each_and_average(graphs)
    masses = [total_mass(graph) for graph in graphs]
    assert np.isclose(total_mass(combined), float(np.mean(masses)))


def test_solver_functions_do_not_accept_labels():
    import inspect

    for function in (shrink_weighted, admm_weighted, cvxpy_weighted, ordered_pair_threshold):
        assert "labels" not in inspect.signature(function).parameters
        assert "y" not in inspect.signature(function).parameters


def test_conjugate_gradient_matches_direct_spd_solve():
    from scipy.sparse.linalg import spsolve

    from SSC_method.optimizer import _conjugate_gradient_solve

    rng = np.random.default_rng(0)
    size = 60
    basis = sparse.random(size, size, density=0.08, random_state=0, format="csr")
    coefficient = (basis.T @ basis + sparse.eye(size, format="csc")).tocsc()
    rhs = rng.normal(size=(size, 3))
    direct = np.asarray(spsolve(coefficient, rhs))
    iterative = _conjugate_gradient_solve(coefficient, rhs)
    assert np.allclose(iterative, direct, atol=1e-7, rtol=1e-7)
