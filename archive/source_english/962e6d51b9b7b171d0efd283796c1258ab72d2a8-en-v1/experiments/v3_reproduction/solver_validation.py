"""Independent check of the printed Equation (8) objective.

The IRLS variants stay separate. This module does not replace their G.
``E8`` is the ordered-pair stationary system. ``E13`` is the printed
Equation (13) update. Only Equation (8) is passed to CVXPY and to ADMM.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from SSC_method.objective import equation8_objective


def _prox_l2_rows(matrix: np.ndarray, threshold: np.ndarray | float) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1)
    thresh = np.asarray(threshold, dtype=np.float64)
    if thresh.ndim == 0:
        thresh = np.full(norms.shape, float(thresh))
    scale = np.zeros_like(norms)
    positive = norms > 0.0
    scale[positive] = np.maximum(1.0 - thresh[positive] / norms[positive], 0.0)
    return matrix * scale[:, None]


def _edges(affinity: sparse.spmatrix | np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    weights = sparse.csr_matrix(affinity, dtype=np.float64).tocoo()
    keep = (weights.data > 0.0) & (weights.row != weights.col)
    return (
        np.asarray(weights.row[keep], dtype=np.int64),
        np.asarray(weights.col[keep], dtype=np.int64),
        np.asarray(weights.data[keep], dtype=np.float64),
    )


def admm_equation8(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    *,
    rho: float = 1.0,
    max_iter: int = 200,
    tol: float = 1e-4,
    G_init: np.ndarray | None = None,
) -> dict[str, Any]:
    """ADMM on ``sum_i ||g_i-f_i|| + gamma * sum_{i,j} W_ij ||g_i-g_j||``.

    Stored ordered pairs are used as written in Equation (8). A symmetric
    ``W`` with both triangles therefore contributes both directions. The
    factorization does not depend on ``gamma``.
    """
    features = np.asarray(embedding, dtype=np.float64)
    n_samples, _n_components = features.shape
    gamma = float(gamma)
    rho = float(rho)
    if rho <= 0.0:
        raise ValueError("rho must be positive")
    src, dst, weight = _edges(affinity)
    n_edges = int(src.size)
    diagonal = np.zeros(n_samples, dtype=np.float64)
    if n_edges:
        np.add.at(diagonal, src, 1.0)
        np.add.at(diagonal, dst, 1.0)
        rows = np.concatenate([np.arange(n_samples), src, dst])
        cols = np.concatenate([np.arange(n_samples), dst, src])
        data = np.concatenate([diagonal, -np.ones(n_edges), -np.ones(n_edges)])
    else:
        rows = np.arange(n_samples)
        cols = np.arange(n_samples)
        data = np.zeros(n_samples)
    laplacian = sparse.coo_matrix((data, (rows, cols)), shape=(n_samples, n_samples)).tocsc()
    system = (rho * sparse.eye(n_samples, format="csc") + rho * laplacian).tocsc()
    system = ((system + system.T) * 0.5).tocsc()
    factor = splu(system)

    patterns = np.array(features if G_init is None else G_init, dtype=np.float64, copy=True)
    residual = patterns - features
    dual_residual = np.zeros_like(patterns)
    edge_value = patterns[src] - patterns[dst] if n_edges else np.zeros((0, features.shape[1]))
    edge_dual = np.zeros_like(edge_value)
    history: list[dict[str, float]] = []
    converged = False
    for iteration in range(int(max_iter)):
        residual = _prox_l2_rows(patterns - features + dual_residual, 1.0 / rho)
        if n_edges:
            edge_value = _prox_l2_rows(
                patterns[src] - patterns[dst] + edge_dual,
                (gamma * weight) / rho,
            )
        edge_target = edge_value - edge_dual
        rhs = rho * (features + residual - dual_residual)
        if n_edges:
            extra = np.zeros_like(patterns)
            np.add.at(extra, src, rho * edge_target)
            np.add.at(extra, dst, -rho * edge_target)
            rhs = rhs + extra
        patterns = np.asarray(factor.solve(rhs), dtype=np.float64)
        if patterns.ndim == 1:
            patterns = patterns.reshape(n_samples, -1)
        gap_data = patterns - features - residual
        dual_residual = dual_residual + gap_data
        if n_edges:
            gap_edge = patterns[src] - patterns[dst] - edge_value
            edge_dual = edge_dual + gap_edge
            primal = float(np.linalg.norm(gap_data) + np.linalg.norm(gap_edge))
        else:
            primal = float(np.linalg.norm(gap_data))
        objective = equation8_objective(patterns, features, affinity, gamma)
        history.append(
            {
                "iteration": float(iteration),
                "equation8_objective": objective,
                "primal_residual": primal,
            }
        )
        scale = 1.0 + float(np.linalg.norm(patterns))
        if primal <= tol * scale:
            converged = True
            break
    objective = equation8_objective(patterns, features, affinity, gamma)
    status = "CONVERGED_BY_ITERATE_CRITERION" if converged else "MAX_ITER_REACHED"
    return {
        "patterns": patterns,
        "objective": objective,
        "converged": converged,
        "status": status,
        "n_iterations": len(history),
        "history": history,
        "solver": "admm_equation8",
        "gamma": gamma,
        "rho": rho,
    }


def cvxpy_equation8(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    *,
    eps: float = 1e-6,
) -> dict[str, Any]:
    """Solve Equation (8) with CVXPY. Intended for small verification problems."""
    import cvxpy as cp

    features = np.asarray(embedding, dtype=np.float64)
    n_samples, n_components = features.shape
    patterns = cp.Variable((n_samples, n_components))
    data_term = cp.sum(cp.norm(patterns - features, axis=1))
    src, dst, weight = _edges(affinity)
    if src.size:
        graph_terms = [
            float(weight[index]) * cp.norm(patterns[int(src[index])] - patterns[int(dst[index])])
            for index in range(src.size)
        ]
        objective = data_term + float(gamma) * cp.sum(cp.hstack(graph_terms))
    else:
        objective = data_term
    problem = cp.Problem(cp.Minimize(objective))
    problem.solve(solver=cp.SCS, eps=float(eps), max_iters=8000, verbose=False)
    solved = None if patterns.value is None else np.asarray(patterns.value, dtype=np.float64)
    value = None if problem.value is None else float(problem.value)
    verified = solved is not None and value is not None and str(problem.status) in {
        "optimal",
        "optimal_inaccurate",
    }
    return {
        "patterns": solved,
        "objective": value,
        "status": "OPTIMALITY_VERIFIED" if verified else "NUMERICALLY_UNCERTIFIED",
        "solver_status": str(problem.status),
        "solver": "cvxpy_scs_equation8",
    }


def positive_residual_stationarity(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    *,
    floor: float = 1e-8,
) -> dict[str, Any]:
    """Unique subgradient norm when no data row and no used edge is fused.

    A near-zero residual makes the norm subdifferential a ball. This helper
    refuses that case instead of clipping the quotient and calling it KKT.
    """
    residual = np.asarray(patterns, dtype=np.float64) - np.asarray(embedding, dtype=np.float64)
    data_norm = np.linalg.norm(residual, axis=1)
    src, dst, weight = _edges(affinity)
    edge_gap = patterns[src] - patterns[dst] if src.size else np.zeros((0, patterns.shape[1]))
    edge_norm = np.linalg.norm(edge_gap, axis=1) if src.size else np.zeros(0)
    if np.any(data_norm <= floor) or np.any(edge_norm <= floor):
        return {
            "status": "NUMERICALLY_UNCERTIFIED",
            "reason": "zero residual or fused edge; unique subgradient is not available",
            "n_zero_data_rows": int(np.sum(data_norm <= floor)),
            "n_fused_edges": int(np.sum(edge_norm <= floor)),
            "subgradient_norm": None,
        }
    gradient = residual / data_norm[:, None]
    unit = edge_gap / edge_norm[:, None]
    contribution = (float(gamma) * weight)[:, None] * unit
    np.add.at(gradient, src, contribution)
    np.add.at(gradient, dst, -contribution)
    return {
        "status": "OPTIMALITY_VERIFIED"
        if float(np.linalg.norm(gradient)) <= 1e-3
        else "NUMERICALLY_UNCERTIFIED",
        "reason": "unique subgradient because every residual is bounded away from zero",
        "subgradient_norm": float(np.linalg.norm(gradient)),
        "n_zero_data_rows": 0,
        "n_fused_edges": 0,
    }


def solver_status_from_irls(
    *,
    converged: bool,
    n_iterations: int,
    max_iter: int,
    stationarity: dict[str, Any] | None = None,
    independent_gap: float | None = None,
    gap_tol: float = 1e-3,
) -> str:
    """Map numeric evidence onto the campaign status vocabulary."""
    if independent_gap is not None and np.isfinite(independent_gap) and independent_gap <= gap_tol:
        return "OPTIMALITY_VERIFIED"
    if stationarity is not None and stationarity.get("status") == "OPTIMALITY_VERIFIED":
        return "OPTIMALITY_VERIFIED"
    if converged:
        return "CONVERGED_BY_ITERATE_CRITERION"
    if n_iterations >= max_iter:
        return "MAX_ITER_REACHED"
    return "NUMERICALLY_UNCERTIFIED"
