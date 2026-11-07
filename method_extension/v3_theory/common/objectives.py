"""Ordered-pair shrinkage objectives.

The printed objective is

    J(G) = sum_i a_i ||g_i - f_i||_2 + gamma * sum_{i,j} W_ij ||g_i - g_j||_2

with a_i = 1 for SSC. A symmetric W that stores both triangles counts each
ordered pair once. This is the same convention as ``equation8_objective``.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from SSC_method.objective import equation8_objective, graph_l2_term


def as_csr(affinity: sparse.spmatrix | np.ndarray) -> sparse.csr_matrix:
    matrix = sparse.csr_matrix(affinity, dtype=np.float64)
    matrix.sum_duplicates()
    return matrix


def fidelity_vector(fidelity: np.ndarray | None, n_samples: int) -> np.ndarray:
    if fidelity is None:
        return np.ones(n_samples, dtype=np.float64)
    weights = np.asarray(fidelity, dtype=np.float64).reshape(-1)
    if weights.shape != (n_samples,):
        raise ValueError("fidelity weights must have one value per row")
    if not np.isfinite(weights).all() or np.any(weights <= 0.0):
        raise ValueError("fidelity weights must be finite and positive")
    return weights


def weighted_objective(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    fidelity: np.ndarray | None = None,
) -> float:
    """Exact nonsmooth objective. a_i = 1 reproduces Equation (8)."""
    patterns = np.asarray(patterns, dtype=np.float64)
    embedding = np.asarray(embedding, dtype=np.float64)
    weights = fidelity_vector(fidelity, patterns.shape[0])
    residual = np.linalg.norm(patterns - embedding, axis=1)
    if np.allclose(weights, 1.0):
        return equation8_objective(patterns, embedding, affinity, gamma)
    return float(np.sum(weights * residual) + float(gamma) * graph_l2_term(patterns, affinity))


def relative_change(numerator: float, denominator: float) -> float:
    return float(numerator / max(abs(denominator), 1e-12))
