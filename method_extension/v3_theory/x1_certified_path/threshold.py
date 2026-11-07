"""Threshold at which G = F is optimal for the ordered-pair objective.

For a symmetric W that stores both triangles, a noncoincident edge {i, j}
contributes 2 W_ij u_ij to the graph subgradient at row i, where
u_ij = (f_i - f_j) / ||f_i - f_j||. With

    q_i = sum_j W_ij (f_i - f_j) / ||f_i - f_j||

over noncoincident stored pairs, G = F is optimal when

    2 * gamma * max_i ||q_i||_2 <= 1,

so gamma_0 = 1 / (2 max_i ||q_i||) when that maximum is positive.
Coincident edges are not divided; their subgradient is a Euclidean ball and
feasibility is a second-order cone constraint. The factor 2 is the ordered-pair
count, not a tuned constant. Convex clustering and ADMM are standard tools.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse

from method_extension.v3_theory.common.objectives import as_csr


def _edge_arrays(affinity: sparse.spmatrix | np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    weights = as_csr(affinity).tocoo()
    keep = (weights.data > 0.0) & (weights.row < weights.col)
    return (
        np.asarray(weights.row[keep], dtype=np.int64),
        np.asarray(weights.col[keep], dtype=np.int64),
        np.asarray(weights.data[keep], dtype=np.float64),
    )


def ordered_pair_threshold(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    *,
    distance_tol: float = 1e-12,
    certify_coincident: bool = True,
) -> dict[str, Any]:
    """Return gamma_0 and whether the closed form applies."""
    features = np.asarray(embedding, dtype=np.float64)
    src, dst, weight = _edge_arrays(affinity)
    q_vector = np.zeros_like(features)
    coincident_src: list[int] = []
    coincident_dst: list[int] = []
    coincident_weight: list[float] = []
    for left, right, value in zip(src, dst, weight, strict=True):
        difference = features[left] - features[right]
        distance = float(np.linalg.norm(difference))
        if distance <= distance_tol:
            coincident_src.append(int(left))
            coincident_dst.append(int(right))
            coincident_weight.append(float(value))
            continue
        unit = difference / distance
        q_vector[left] += float(value) * unit
        q_vector[right] -= float(value) * unit
    q_norm = np.linalg.norm(q_vector, axis=1)
    max_q = float(q_norm.max()) if q_norm.size else 0.0
    n_coincident = len(coincident_src)
    if max_q <= distance_tol and n_coincident == 0:
        gamma_0 = float("inf")
        source = "no_graph_force"
    elif n_coincident == 0:
        gamma_0 = float(1.0 / (2.0 * max_q))
        source = "closed_form_noncoincident"
    elif certify_coincident and features.shape[0] <= 250:
        gamma_0, source = _bisection_gamma(
            q_vector,
            np.asarray(coincident_src, dtype=np.int64),
            np.asarray(coincident_dst, dtype=np.int64),
            np.asarray(coincident_weight, dtype=np.float64),
            upper_hint=float("inf") if max_q <= distance_tol else 1.0 / (2.0 * max_q),
        )
    else:
        gamma_0 = float("inf") if max_q <= distance_tol else float(1.0 / (2.0 * max_q))
        source = "closed_form_sufficient_coincident_uncertified"
    return {
        "gamma_0": gamma_0,
        "max_q_norm": max_q,
        "n_undirected_edges": int(src.size),
        "n_coincident_edges": n_coincident,
        "threshold_source": source,
        "q_norm": q_norm,
    }


def g_equals_f_is_optimal(threshold: dict[str, Any], gamma: float) -> bool:
    gamma_0 = float(threshold["gamma_0"])
    if threshold["threshold_source"] == "closed_form_sufficient_coincident_uncertified":
        return False
    if not np.isfinite(gamma_0):
        return True
    return float(gamma) <= gamma_0 * (1.0 + 1e-9)


def _bisection_gamma(
    q_vector: np.ndarray,
    src: np.ndarray,
    dst: np.ndarray,
    weight: np.ndarray,
    upper_hint: float,
) -> tuple[float, str]:
    """Largest gamma at which G = F stays feasible, via a cone feasibility test."""
    import cvxpy as cp

    def feasible_assembled(gamma: float) -> bool:
        n_samples, dimension = q_vector.shape
        subgradient = cp.Variable((n_samples, dimension))
        constraints = [cp.norm(subgradient, axis=1) <= 1.0]
        expression = subgradient + 2.0 * float(gamma) * q_vector
        if src.size:
            direction = cp.Variable((src.size, dimension))
            constraints.append(cp.norm(direction, axis=1) <= 1.0)
            increment = np.zeros((n_samples, src.size))
            increment[src, np.arange(src.size)] = 2.0 * float(gamma) * weight
            increment[dst, np.arange(src.size)] = -2.0 * float(gamma) * weight
            expression = expression + increment @ direction
        constraints.append(expression == 0)
        problem = cp.Problem(cp.Minimize(0), constraints)
        problem.solve(solver=cp.SCS, eps=1e-6, max_iters=5000, verbose=False)
        return str(problem.status) in {"optimal", "optimal_inaccurate"}

    if feasible_assembled(1e6):
        return float("inf"), "coincident_subgradient_unbounded"
    low = 0.0
    high = 1.0 if not np.isfinite(upper_hint) else max(float(upper_hint), 1.0)
    while feasible_assembled(high):
        high *= 2.0
        if high > 1e6:
            return float("inf"), "coincident_subgradient_unbounded"
    for _ in range(40):
        mid = 0.5 * (low + high)
        if feasible_assembled(mid):
            low = mid
        else:
            high = mid
    return float(low), "coincident_subgradient_bisection"


def fusion_summary(patterns: np.ndarray, affinity: sparse.spmatrix | np.ndarray, *, tol: float = 1e-6) -> dict[str, float]:
    """How many stored ordered pairs and rows collapsed."""
    from method_extension.v3_theory.common.objectives import as_csr as _csr

    matrix = np.asarray(patterns, dtype=np.float64)
    weights = _csr(affinity).tocoo()
    difference = matrix[weights.row] - matrix[weights.col]
    distance = np.linalg.norm(difference, axis=1)
    active = weights.data > 0.0
    n_active = int(np.sum(active))
    n_fused = int(np.sum((distance <= tol) & active))
    rounded = np.round(matrix / max(tol, 1e-8))
    # Distinct rows after a tolerance rounding. This is a diagnostic, not a cluster count.
    distinct = np.unique(rounded, axis=0).shape[0]
    return {
        "n_active_ordered_pairs": n_active,
        "n_fused_ordered_pairs": n_fused,
        "fused_pair_fraction": float(n_fused / max(n_active, 1)),
        "n_distinct_rounded_rows": int(distinct),
    }
