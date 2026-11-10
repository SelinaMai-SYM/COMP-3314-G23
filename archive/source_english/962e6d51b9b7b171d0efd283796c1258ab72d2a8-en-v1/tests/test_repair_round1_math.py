"""Small convex checks for the E13 and E8 linear systems.

E13 is the printed Equation (13). E8 is the ordered-pair stationary system
of the printed Equation (8), with Laplacian coefficient 2. The nonsmooth
Equation (8), the square-root smoothing, the frozen IRLS quadratic, and the
fixed-point residual are compared as different quantities.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse
from scipy.optimize import minimize

from SSC_method.objective import (
    equation8_objective,
    graph_l2_term,
    row_l21_diagonal,
    row_l2_norms,
    shrinkage_laplacian,
    sqrt_smoothed_equation8_objective,
    trace_surrogate,
)
from SSC_method.optimizer import (
    iteration_diagnostics,
    shrink_embedding,
    solve_spd_system,
    variant_laplacian_coefficient,
)
from SSC_method.ssc import SpectralShrunkClustering

CLARABEL_SETTINGS = {
    "tol_gap_abs": 1e-10,
    "tol_gap_rel": 1e-10,
    "tol_feas": 1e-10,
    "max_iter": 500,
}
SCIPY_SETTINGS = {
    "ftol": 1e-14,
    "gtol": 1e-8,
    "maxiter": 4000,
}


def _chain_affinity(n_samples: int) -> np.ndarray:
    weights = np.zeros((n_samples, n_samples), dtype=np.float64)
    for index in range(n_samples - 1):
        weights[index, index + 1] = 1.0
        weights[index + 1, index] = 1.0
    return weights


def _block_affinity() -> np.ndarray:
    """Two cliques of three nodes plus one weak bridge."""
    weights = np.zeros((6, 6), dtype=np.float64)
    for block in (range(0, 3), range(3, 6)):
        for i in block:
            for j in block:
                if i != j:
                    weights[i, j] = 1.0
    weights[2, 3] = 0.15
    weights[3, 2] = 0.15
    return weights


def _example(graph_name: str) -> tuple[np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(1)
    embedding = rng.normal(size=(6, 2))
    if graph_name == "chain":
        affinity = _chain_affinity(6)
    elif graph_name == "block":
        affinity = _block_affinity()
    else:
        raise ValueError(graph_name)
    return embedding, affinity, 0.8


def _equation8_gradient(patterns: np.ndarray, embedding: np.ndarray, affinity: np.ndarray, gamma: float) -> np.ndarray:
    """Gradient of the printed ordered-pair Equation (8), away from kinks.

    Data contribution is 2 S (G - F). Graph contribution is 4 gamma Ltilde G
    when Wtilde uses the Equation (11) factor 1/2 and both ordered directions
    are stored.
    """
    s_diagonal = row_l21_diagonal(patterns - embedding, eps=1e-15)
    _, laplacian = shrinkage_laplacian(sparse.csr_matrix(affinity), patterns, eps=1e-15)
    data = 2.0 * s_diagonal[:, None] * (patterns - embedding)
    graph = 4.0 * gamma * (laplacian @ patterns)
    return data + graph


def _numeric_equation8_gradient(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: np.ndarray,
    gamma: float,
    step: float = 1e-6,
) -> np.ndarray:
    gradient = np.zeros_like(patterns)
    for row in range(patterns.shape[0]):
        for col in range(patterns.shape[1]):
            plus = patterns.copy()
            minus = patterns.copy()
            plus[row, col] += step
            minus[row, col] -= step
            gradient[row, col] = (
                equation8_objective(plus, embedding, affinity, gamma)
                - equation8_objective(minus, embedding, affinity, gamma)
            ) / (2.0 * step)
    return gradient


def _system_residual(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: np.ndarray,
    gamma: float,
    laplacian_coefficient: float,
    eps: float,
) -> float:
    s_diagonal = row_l21_diagonal(patterns - embedding, eps=eps)
    _, laplacian = shrinkage_laplacian(sparse.csr_matrix(affinity), patterns, eps=eps)
    coefficient = sparse.diags(s_diagonal) + (laplacian_coefficient * gamma) * laplacian
    rhs = s_diagonal[:, None] * embedding
    return float(np.linalg.norm(coefficient @ patterns - rhs))


def _solve_printed_objective(embedding: np.ndarray, affinity: np.ndarray, graph_coefficient: float) -> dict:
    """Minimize sum_i ||g_i - f_i||_2 + graph_coefficient * sum_ij W_ij ||g_i - g_j||_2."""
    try:
        import cvxpy
    except ImportError:
        cvxpy = None
    if cvxpy is not None:
        return _solve_with_cvxpy(cvxpy, embedding, affinity, graph_coefficient)
    return _solve_with_scipy(embedding, affinity, graph_coefficient)


def _solve_with_cvxpy(cvxpy, embedding: np.ndarray, affinity: np.ndarray, graph_coefficient: float) -> dict:
    n_samples, n_components = embedding.shape
    variable = cvxpy.Variable((n_samples, n_components))
    data_term = cvxpy.sum([cvxpy.norm(variable[i] - embedding[i], 2) for i in range(n_samples)])
    graph_terms = []
    for i in range(n_samples):
        for j in range(n_samples):
            if affinity[i, j] > 0.0:
                graph_terms.append(affinity[i, j] * cvxpy.norm(variable[i] - variable[j], 2))
    problem = cvxpy.Problem(cvxpy.Minimize(data_term + float(graph_coefficient) * cvxpy.sum(graph_terms)))
    problem.solve(solver=cvxpy.CLARABEL, verbose=False, **CLARABEL_SETTINGS)
    stats = problem.solver_stats
    return {
        "solver": "CLARABEL",
        "status": problem.status,
        "value": float(problem.value),
        "solution": np.asarray(variable.value, dtype=np.float64),
        "tolerances": dict(CLARABEL_SETTINGS),
        "num_iters": None if stats is None else getattr(stats, "num_iters", None),
        "solve_time": None if stats is None else getattr(stats, "solve_time", None),
    }


def _solve_with_scipy(embedding: np.ndarray, affinity: np.ndarray, graph_coefficient: float) -> dict:
    n_samples, n_components = embedding.shape

    def objective(flat: np.ndarray) -> float:
        patterns = flat.reshape(n_samples, n_components)
        data_term = float(np.sum(row_l2_norms(patterns - embedding)))
        return data_term + float(graph_coefficient) * graph_l2_term(patterns, affinity)

    starts = [embedding.ravel(), np.zeros(n_samples * n_components)]
    rng = np.random.default_rng(0)
    starts.append(rng.normal(size=n_samples * n_components))
    best = None
    for start in starts:
        optimized = minimize(
            objective,
            start,
            method="L-BFGS-B",
            tol=1e-14,
            options=dict(SCIPY_SETTINGS),
        )
        if best is None or float(optimized.fun) < float(best.fun):
            best = optimized
    assert best is not None
    return {
        "solver": "scipy.optimize.L-BFGS-B",
        "status": "success" if best.success else f"failure:{best.status}",
        "value": float(best.fun),
        "solution": best.x.reshape(n_samples, n_components),
        "tolerances": dict(SCIPY_SETTINGS),
        "message": str(best.message),
    }


def _run_variant(embedding: np.ndarray, affinity: np.ndarray, gamma: float, variant: str):
    # tol is tight on purpose. On the block graph, Equation (13) can report a
    # tiny step while the rebuilt fixed-point residual is still large, so the
    # caller checks that residual rather than the converged flag alone.
    return shrink_embedding(
        embedding,
        sparse.csr_matrix(affinity),
        gamma=gamma,
        eps=1e-10,
        tol=1e-12,
        max_iter=1000,
        zero_residual_floor="median_pairwise",
        variant=variant,
    )


@pytest.mark.parametrize("graph_name", ["chain", "block"])
def test_e8_matches_printed_equation8_and_e13_matches_halved_graph(graph_name: str):
    embedding, affinity, gamma = _example(graph_name)
    e13 = _run_variant(embedding, affinity, gamma, "E13")
    e8 = _run_variant(embedding, affinity, gamma, "E8")
    assert e13.variant == "E13" and e13.laplacian_coefficient == 1.0
    assert e8.variant == "E8" and e8.laplacian_coefficient == 2.0
    assert e13.patterns.shape == embedding.shape
    assert e8.patterns.shape == embedding.shape
    assert row_l21_diagonal(e8.patterns - embedding, eps=1e-10).shape == (embedding.shape[0],)
    assert not np.allclose(e13.patterns, e8.patterns, rtol=1e-3, atol=1e-3)

    e13_residual = _system_residual(e13.patterns, embedding, affinity, gamma, 1.0, eps=1e-10)
    e8_residual = _system_residual(e8.patterns, embedding, affinity, gamma, 2.0, eps=1e-10)
    crossed_e13 = _system_residual(e13.patterns, embedding, affinity, gamma, 2.0, eps=1e-10)
    crossed_e8 = _system_residual(e8.patterns, embedding, affinity, gamma, 1.0, eps=1e-10)
    assert e13.fixed_point_residual == pytest.approx(e13_residual, rel=1e-6, abs=1e-12)
    assert e8.fixed_point_residual == pytest.approx(e8_residual, rel=1e-6, abs=1e-12)
    assert e13_residual < 1e-5
    assert e8_residual < 1e-5
    assert crossed_e13 > 1e-2
    assert crossed_e8 > 1e-2
    assert e13.history[-1]["linear_residual"] < 1e-5
    assert e8.history[-1]["linear_residual"] < 1e-5

    printed = _solve_printed_objective(embedding, affinity, gamma)
    halved = _solve_printed_objective(embedding, affinity, gamma / 2.0)
    assert printed["status"] in {"optimal", "optimal_inaccurate", "success"}
    assert halved["status"] in {"optimal", "optimal_inaccurate", "success"}
    assert printed["solver"] in {"CLARABEL", "scipy.optimize.L-BFGS-B"}
    if printed["solver"] == "CLARABEL":
        assert printed["status"] == "optimal"
        assert halved["status"] == "optimal"
        matrix_rtol, matrix_atol = 1e-4, 1e-5
        value_rtol, value_atol = 1e-7, 1e-8
        assert printed["tolerances"] == CLARABEL_SETTINGS
    else:
        matrix_rtol, matrix_atol = 5e-2, 5e-2
        value_rtol, value_atol = 1e-3, 1e-3

    e8_objective = equation8_objective(e8.patterns, embedding, affinity, gamma)
    e13_objective = equation8_objective(e13.patterns, embedding, affinity, gamma)
    e13_halved_objective = equation8_objective(e13.patterns, embedding, affinity, gamma / 2.0)
    printed_at_reference = equation8_objective(printed["solution"], embedding, affinity, gamma)
    halved_at_reference = equation8_objective(halved["solution"], embedding, affinity, gamma / 2.0)

    assert e8_objective == pytest.approx(printed["value"], rel=value_rtol, abs=value_atol)
    assert printed_at_reference == pytest.approx(printed["value"], rel=value_rtol, abs=value_atol)
    assert np.allclose(e8.patterns, printed["solution"], rtol=matrix_rtol, atol=matrix_atol)
    assert e13_halved_objective == pytest.approx(halved["value"], rel=value_rtol, abs=value_atol)
    assert halved_at_reference == pytest.approx(halved["value"], rel=value_rtol, abs=value_atol)
    assert np.allclose(e13.patterns, halved["solution"], rtol=matrix_rtol, atol=matrix_atol)
    # Block optima are closer than chain optima; the gap is still far above
    # the solver tolerance, so Equation (13) is not the Equation (8) minimizer.
    assert e13_objective - printed["value"] > 1e-3

    visible_smoothed = sqrt_smoothed_equation8_objective(
        e8.patterns, embedding, affinity, gamma, eps=1e-2
    )
    surrogate = e8.history[-1]["irls_quadratic_surrogate"]
    solver_smoothed = e8.history[-1]["sqrt_smoothed_equation8_objective"]
    assert visible_smoothed > e8_objective + 1e-3
    assert abs(surrogate - e8_objective) > 1e-2
    assert abs(solver_smoothed - surrogate) > 1e-3
    assert e8.fixed_point_residual < 1e-5
    assert e8_objective > 0.1
    diagnostics = iteration_diagnostics(e8)
    assert diagnostics["equation8_objective"] == pytest.approx(e8_objective)
    assert diagnostics["irls_quadratic_surrogate"] == pytest.approx(surrogate)
    assert diagnostics["fixed_point_residual"] == pytest.approx(e8.fixed_point_residual)
    assert diagnostics["sqrt_smoothed_equation8_objective"] == pytest.approx(solver_smoothed)


def test_equation8_gradient_is_twice_the_e8_residual():
    rng = np.random.default_rng(7)
    embedding = rng.normal(size=(5, 2))
    patterns = embedding + rng.normal(size=(5, 2))
    affinity = _chain_affinity(5)
    gamma = 0.8
    analytic = _equation8_gradient(patterns, embedding, affinity, gamma)
    numeric = _numeric_equation8_gradient(patterns, embedding, affinity, gamma)
    assert np.allclose(analytic, numeric, rtol=1e-5, atol=1e-6)

    s_diagonal = row_l21_diagonal(patterns - embedding, eps=1e-15)
    _, laplacian = shrinkage_laplacian(sparse.csr_matrix(affinity), patterns, eps=1e-15)
    e8_matrix_residual = (sparse.diags(s_diagonal) + (2.0 * gamma) * laplacian) @ patterns - s_diagonal[:, None] * embedding
    e13_matrix_residual = (sparse.diags(s_diagonal) + gamma * laplacian) @ patterns - s_diagonal[:, None] * embedding
    assert np.allclose(2.0 * e8_matrix_residual, analytic, rtol=1e-8, atol=1e-8)
    assert np.linalg.norm(e13_matrix_residual - e8_matrix_residual) > 1e-2


def test_default_variant_matches_explicit_e13_and_keeps_eps_floor():
    embedding, affinity, gamma = _example("chain")
    omitted = shrink_embedding(
        embedding,
        affinity,
        gamma=gamma,
        eps=1e-8,
        tol=1e-8,
        max_iter=50,
        zero_residual_floor="median_pairwise",
    )
    explicit = shrink_embedding(
        embedding,
        affinity,
        gamma=gamma,
        eps=1e-8,
        tol=1e-8,
        max_iter=50,
        zero_residual_floor="median_pairwise",
        variant="E13",
    )
    assert omitted.variant == "E13"
    assert omitted.laplacian_coefficient == 1.0
    assert variant_laplacian_coefficient("E8") == 2.0
    assert np.array_equal(omitted.patterns, explicit.patterns)
    assert omitted.history == explicit.history
    with pytest.raises(ValueError, match="E13"):
        variant_laplacian_coefficient("equation13")

    smooth = np.column_stack([np.linspace(0.0, 1.0, 6), np.linspace(1.0, 0.0, 6)])
    stayed = shrink_embedding(
        smooth,
        affinity,
        gamma=1.0,
        eps=1e-8,
        tol=1e-14,
        max_iter=30,
        zero_residual_floor="eps",
        variant="E13",
    )
    assert np.linalg.norm(stayed.patterns - smooth) < 1e-5
    assert stayed.initial_zero_residual_floor == pytest.approx(1e-8)
    # The same eps floor is accepted by E8. Its first step is O(eps). On this
    # chain the later factor-2 updates are not contracted back to F, so this
    # test does not claim that E8 remains at F.
    e8_floor = shrink_embedding(
        smooth,
        affinity,
        gamma=1.0,
        eps=1e-8,
        tol=1e-14,
        max_iter=1,
        zero_residual_floor="eps",
        variant="E8",
    )
    assert e8_floor.initial_zero_residual_floor == pytest.approx(1e-8)
    assert e8_floor.history[0]["step_frobenius"] < 1e-6


def test_frozen_quadratic_matches_scipy_for_both_coefficients():
    rng = np.random.default_rng(5)
    embedding = rng.normal(size=(6, 2))
    current = embedding + 0.2 * rng.normal(size=(6, 2))
    affinity = sparse.csr_matrix(_chain_affinity(6))
    gamma = 0.7
    eps = 1e-8
    s_diagonal = row_l21_diagonal(current - embedding, eps=eps)
    _, laplacian = shrinkage_laplacian(affinity, current, eps=eps)
    for coefficient in (1.0, 2.0):
        rhs = s_diagonal[:, None] * embedding
        solved = solve_spd_system(sparse.diags(s_diagonal) + (coefficient * gamma) * laplacian, rhs)

        def quadratic(flat: np.ndarray, coefficient: float = coefficient) -> float:
            return trace_surrogate(
                flat.reshape(6, 2),
                embedding,
                s_diagonal,
                laplacian,
                coefficient * gamma,
            )

        optimized = minimize(quadratic, rng.normal(size=12), method="L-BFGS-B", tol=1e-14)
        assert optimized.success
        assert quadratic(solved.ravel()) == pytest.approx(float(optimized.fun), rel=1e-6, abs=1e-8)
        assert np.allclose(optimized.x.reshape(6, 2), solved, rtol=1e-4, atol=1e-4)


def test_block_e13_small_step_is_not_a_small_fixed_point_residual():
    embedding, affinity, gamma = _example("block")
    result = shrink_embedding(
        embedding,
        sparse.csr_matrix(affinity),
        gamma=gamma,
        eps=1e-10,
        tol=1e-8,
        max_iter=80,
        zero_residual_floor="median_pairwise",
        variant="E13",
    )
    assert result.converged
    assert result.history[-1]["step_frobenius"] < 1e-6
    assert result.history[-1]["linear_residual"] < 1e-4
    assert result.fixed_point_residual > 1e-1


def test_ssc_variant_is_explicit_and_defaults_to_equation_13():
    rng = np.random.default_rng(6)
    features = np.vstack(
        [
            rng.normal(loc=-2.0, scale=0.15, size=(8, 3)),
            rng.normal(loc=2.0, scale=0.15, size=(8, 3)),
        ]
    )
    common = dict(n_clusters=2, gamma=1.0, k=3, tol=1e-5, max_iter=80, kmeans_n_init=1, kmeans_random_state=0)
    default = SpectralShrunkClustering(**common)
    e13 = SpectralShrunkClustering(**common, variant="E13")
    e8 = SpectralShrunkClustering(**common, variant="E8")
    default.fit(features)
    e13.fit(features)
    e8.fit(features)
    assert default.info_["variant"] == "E13"
    assert default.info_["linear_update"] == "equation_13"
    assert default.info_["laplacian_coefficient"] == 1.0
    assert np.allclose(default.shrunk_, e13.shrunk_)
    assert e8.info_["variant"] == "E8"
    assert e8.info_["linear_update"] == "equation_8_stationary"
    assert e8.info_["laplacian_coefficient"] == 2.0
    assert e8.shrunk_.shape == (16, 2)
    assert not np.allclose(e8.shrunk_, e13.shrunk_, rtol=1e-3, atol=1e-3)
    with pytest.raises(ValueError):
        SpectralShrunkClustering(n_clusters=2, variant="E12")
