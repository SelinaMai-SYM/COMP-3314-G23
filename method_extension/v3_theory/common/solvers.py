"""IRLS and an independent ADMM solver for one fixed convex objective.

The IRLS linear system uses S_ii = a_i / (2 max(||g_i-f_i||, floor)) and
A = S + c * gamma * Ltilde. c = 2 is the ordered-pair stationary system
(SSC variant E8). c = 1 is the printed Equation (13) and is not the default
here. ADMM splits the same nonsmooth objective; it is the convex-clustering
algorithm of Chi and Lange and is not claimed as a new method.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from SSC_method.objective import shrinkage_laplacian
from SSC_method.optimizer import shrink_embedding, solve_spd_system
from method_extension.v3_theory.common.objectives import (
    as_csr,
    fidelity_vector,
    relative_change,
    weighted_objective,
)


def shrink_weighted(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    fidelity: np.ndarray | None = None,
    *,
    eps: float = 1e-8,
    tol: float = 1e-6,
    max_iter: int = 300,
    variant: str = "E8",
    zero_residual_floor: str | float = "median_pairwise",
    G_init: np.ndarray | None = None,
) -> dict[str, Any]:
    """Majorize the weighted ordered-pair objective and solve the SPD step.

    a_i = 1 and variant E8 call the frozen SSC solver so the extension control
    cannot drift from that implementation.
    """
    features = np.asarray(embedding, dtype=np.float64)
    weights = fidelity_vector(fidelity, features.shape[0])
    started = time.perf_counter()
    if np.allclose(weights, 1.0):
        solved = shrink_embedding(
            features,
            affinity,
            gamma=float(gamma),
            eps=eps,
            tol=tol,
            max_iter=max_iter,
            variant=variant,
            zero_residual_floor=zero_residual_floor,
            G_init=G_init,
        )
        patterns = np.asarray(solved.patterns, dtype=np.float64)
        objective = weighted_objective(patterns, features, affinity, gamma, weights)
        return {
            "patterns": patterns,
            "objective": objective,
            "n_iterations": int(solved.n_iterations),
            "converged": bool(solved.converged),
            "fixed_point_residual": float(solved.fixed_point_residual),
            "wall_seconds": time.perf_counter() - started,
            "solver": f"frozen_ssc_irls_{variant}",
            "variant": variant,
        }
    if variant not in {"E8", "E13"}:
        raise ValueError("variant must be E8 or E13")
    coefficient_scale = 2.0 if variant == "E8" else 1.0
    affinity_matrix = as_csr(affinity)
    if G_init is None:
        patterns = np.array(features, copy=True)
    else:
        patterns = np.array(G_init, dtype=np.float64, copy=True)
    from SSC_method.optimizer import _initial_denominator_floor

    initial_floor = None
    converged = False
    iterations = 0
    fixed_point_residual = np.nan
    for iteration in range(int(max_iter)):
        iterations = iteration + 1
        residual_norms = np.linalg.norm(patterns - features, axis=1)
        if initial_floor is None and np.all(residual_norms <= eps):
            floor = _initial_denominator_floor(patterns, eps, zero_residual_floor)
            initial_floor = floor
        else:
            floor = eps
        s_diagonal = weights / (2.0 * np.maximum(residual_norms, floor))
        _, laplacian = shrinkage_laplacian(affinity_matrix, patterns, eps=eps)
        coefficient = sparse.diags(s_diagonal) + (coefficient_scale * float(gamma)) * laplacian
        rhs = s_diagonal[:, None] * features
        updated = solve_spd_system(coefficient, rhs)
        step = float(np.linalg.norm(updated - patterns))
        patterns = updated
        scale = 1.0 + float(np.linalg.norm(features))
        if step <= tol * scale:
            converged = True
            break
    final_norms = np.linalg.norm(patterns - features, axis=1)
    s_final = weights / (2.0 * np.maximum(final_norms, eps))
    _, laplacian_final = shrinkage_laplacian(affinity_matrix, patterns, eps=eps)
    coefficient_final = sparse.diags(s_final) + (coefficient_scale * float(gamma)) * laplacian_final
    fixed_point_residual = float(np.linalg.norm(coefficient_final @ patterns - s_final[:, None] * features))
    return {
        "patterns": patterns,
        "objective": weighted_objective(patterns, features, affinity_matrix, gamma, weights),
        "n_iterations": iterations,
        "converged": converged,
        "fixed_point_residual": fixed_point_residual,
        "wall_seconds": time.perf_counter() - started,
        "solver": f"weighted_irls_{variant}",
        "variant": variant,
    }


def _prox_rows(matrix: np.ndarray, threshold: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1)
    scale = np.zeros_like(norms)
    positive = norms > 0.0
    scale[positive] = np.maximum(1.0 - threshold[positive] / norms[positive], 0.0)
    return matrix * scale[:, None]


def admm_weighted(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    fidelity: np.ndarray | None = None,
    *,
    rho: float = 1.0,
    max_iter: int = 200,
    tol: float = 1e-4,
    G_init: np.ndarray | None = None,
    adapt_rho: bool = False,
) -> dict[str, Any]:
    """ADMM on the same weighted ordered-pair objective. Independent of IRLS."""
    features = np.asarray(embedding, dtype=np.float64)
    n_samples, _dimension = features.shape
    weights = fidelity_vector(fidelity, n_samples)
    gamma = float(gamma)
    rho = float(rho)
    matrix = as_csr(affinity).tocoo()
    keep = (matrix.data > 0.0) & (matrix.row != matrix.col)
    src = np.asarray(matrix.row[keep], dtype=np.int64)
    dst = np.asarray(matrix.col[keep], dtype=np.int64)
    edge_weight = np.asarray(matrix.data[keep], dtype=np.float64)
    n_edges = int(src.size)
    diagonal = np.zeros(n_samples, dtype=np.float64)
    if n_edges:
        np.add.at(diagonal, src, 1.0)
        np.add.at(diagonal, dst, 1.0)
    laplacian = sparse.diags(diagonal).tocsc()
    if n_edges:
        off = sparse.coo_matrix(
            (
                np.concatenate([-np.ones(n_edges), -np.ones(n_edges)]),
                (np.concatenate([src, dst]), np.concatenate([dst, src])),
            ),
            shape=(n_samples, n_samples),
        ).tocsc()
        laplacian = (laplacian + off).tocsc()
    started = time.perf_counter()
    patterns = np.array(features if G_init is None else G_init, dtype=np.float64, copy=True)
    data_aux = patterns - features
    data_dual = np.zeros_like(patterns)
    edge_aux = patterns[src] - patterns[dst] if n_edges else np.zeros((0, features.shape[1]))
    edge_dual = np.zeros_like(edge_aux)
    converged = False
    primal = np.nan
    dual = np.nan
    history_tail = []
    iterations = 0
    factor_rho = None
    factor = None

    def refactor(current_rho: float):
        system = (current_rho * sparse.eye(n_samples, format="csc") + current_rho * laplacian).tocsc()
        system = ((system + system.T) * 0.5).tocsc()
        return splu(system)

    factor = refactor(rho)
    factor_rho = rho
    for iteration in range(int(max_iter)):
        iterations = iteration + 1
        data_aux = _prox_rows(patterns - features + data_dual, weights / rho)
        if n_edges:
            edge_aux = _prox_rows(patterns[src] - patterns[dst] + edge_dual, (gamma * edge_weight) / rho)
        rhs = rho * (features + data_aux - data_dual)
        if n_edges:
            extra = np.zeros_like(patterns)
            target = edge_aux - edge_dual
            np.add.at(extra, src, rho * target)
            np.add.at(extra, dst, -rho * target)
            rhs = rhs + extra
        previous = patterns
        if factor_rho != rho:
            factor = refactor(rho)
            factor_rho = rho
        patterns = np.asarray(factor.solve(rhs), dtype=np.float64)
        if patterns.ndim == 1:
            patterns = patterns.reshape(n_samples, -1)
        data_gap = patterns - features - data_aux
        data_dual = data_dual + data_gap
        dual_vector = rho * (patterns - previous)
        if n_edges:
            edge_gap = patterns[src] - patterns[dst] - edge_aux
            edge_dual = edge_dual + edge_gap
            primal = float(np.linalg.norm(data_gap) + np.linalg.norm(edge_gap))
        else:
            primal = float(np.linalg.norm(data_gap))
        dual = float(np.linalg.norm(dual_vector))
        objective = weighted_objective(patterns, features, affinity, gamma, weights)
        if iteration % 25 == 0 or iteration + 1 == max_iter:
            history_tail.append({"iteration": iteration, "objective": objective, "primal": primal, "dual": dual, "rho": rho})
        scale = 1.0 + float(np.linalg.norm(patterns))
        if primal <= tol * scale and dual <= tol * scale:
            converged = True
            break
        if adapt_rho and n_edges and primal > 8.0 * max(dual, 1e-12) and rho < 1e6:
            rho *= 2.0
            data_dual *= 0.5
            edge_dual *= 0.5
        elif adapt_rho and dual > 8.0 * max(primal, 1e-12) and rho > 1e-4:
            rho *= 0.5
            data_dual *= 2.0
            edge_dual *= 2.0
    objective = weighted_objective(patterns, features, affinity, gamma, weights)
    return {
        "patterns": patterns,
        "objective": float(objective),
        "n_iterations": iterations,
        "converged": converged,
        "primal_residual": float(primal),
        "dual_residual": float(dual),
        "rho_final": float(rho),
        "wall_seconds": time.perf_counter() - started,
        "solver": "admm_weighted_ordered_pair",
        "history_tail": history_tail,
    }


def compare_solvers(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    fidelity: np.ndarray | None = None,
    *,
    irls_max_iter: int = 300,
    admm_max_iter: int = 200,
    objective_gap_tol: float = 1e-3,
    variant: str = "E8",
) -> dict[str, Any]:
    """Compare IRLS with ADMM on the exact nonsmooth objective.

    A small step of G is not enough. Agreement here measures the relative
    objective gap to be within tolerance and the independent primal residual
    to be small. Neither condition is a feasible-dual optimality certificate.
    """
    irls = shrink_weighted(
        embedding, affinity, gamma, fidelity, max_iter=irls_max_iter, variant=variant
    )
    admm = admm_weighted(
        embedding, affinity, gamma, fidelity, max_iter=admm_max_iter, G_init=irls["patterns"]
    )
    # A second start from F stops a warm start from hiding a bad basin. The
    # better exact objective is the independent value that is compared.
    admm_cold = admm_weighted(embedding, affinity, gamma, fidelity, max_iter=admm_max_iter)
    if admm_cold["objective"] + 1e-8 < admm["objective"]:
        admm = admm_cold
    gap = float(irls["objective"] - admm["objective"])
    relative_gap = abs(relative_change(gap, admm["objective"]))
    primal_ok = bool(admm["converged"]) or (
        np.isfinite(admm["primal_residual"]) and admm["primal_residual"] <= 1e-3 * (1.0 + np.linalg.norm(admm["patterns"]))
    )
    if relative_gap <= objective_gap_tol and primal_ok and irls["objective"] <= admm["objective"] * (1.0 + objective_gap_tol):
        status = "SOLVER_AGREEMENT_UNCERTIFIED"
    else:
        status = "NUMERICALLY_UNCERTIFIED"
    features = np.asarray(embedding, dtype=np.float64)
    movement = float(np.linalg.norm(irls["patterns"] - features) / max(np.linalg.norm(features), 1e-12))
    return {
        "status": status,
        "irls_objective": irls["objective"],
        "independent_objective": admm["objective"],
        "objective_gap_irls_minus_independent": gap,
        "relative_objective_gap": relative_gap,
        "irls_iterations": irls["n_iterations"],
        "independent_iterations": admm["n_iterations"],
        "irls_converged": irls["converged"],
        "independent_converged": admm["converged"],
        "primal_residual": admm["primal_residual"],
        "dual_residual": admm["dual_residual"],
        "irls_fixed_point_residual": irls["fixed_point_residual"],
        "irls_wall_seconds": irls["wall_seconds"],
        "independent_wall_seconds": admm["wall_seconds"],
        "relative_g_minus_f": movement,
        "irls_patterns": irls["patterns"],
        "independent_patterns": admm["patterns"],
    }


def cvxpy_weighted(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    fidelity: np.ndarray | None = None,
    *,
    eps: float = 1e-6,
) -> dict[str, Any]:
    """Exact nonsmooth objective with CVXPY. Small problems only."""
    import cvxpy as cp

    features = np.asarray(embedding, dtype=np.float64)
    n_samples, dimension = features.shape
    weights = fidelity_vector(fidelity, n_samples)
    patterns = cp.Variable((n_samples, dimension))
    data_term = cp.sum(cp.multiply(weights, cp.norm(patterns - features, axis=1)))
    matrix = as_csr(affinity).tocoo()
    terms = []
    for left, right, value in zip(matrix.row, matrix.col, matrix.data, strict=True):
        if left == right or value == 0.0:
            continue
        terms.append(float(value) * cp.norm(patterns[int(left)] - patterns[int(right)]))
    objective = data_term if not terms else data_term + float(gamma) * cp.sum(cp.hstack(terms))
    problem = cp.Problem(cp.Minimize(objective))
    problem.solve(solver=cp.SCS, eps=float(eps), max_iters=8000, verbose=False)
    solved = None if patterns.value is None else np.asarray(patterns.value, dtype=np.float64)
    value = None if problem.value is None else float(problem.value)
    verified = solved is not None and value is not None and str(problem.status) in {"optimal", "optimal_inaccurate"}
    return {
        "patterns": solved,
        "objective": value,
        "solver_status": str(problem.status),
        "status": "NUMERICAL_REFERENCE_UNCERTIFIED" if verified else "NUMERICALLY_UNCERTIFIED",
    }
