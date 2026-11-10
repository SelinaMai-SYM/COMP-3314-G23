"""Equation (8), the printed trace surrogate (12), and epsilon-smoothed norms.

Equation (8) is the sum of row l2 norms of G - F plus gamma times
sum_{i,j} W_ij ||g_i - g_j||_2. The square-root smoothing below is a
different function. The IRLS denominator floor is a third, separate
approximation. None of these three is claimed to be identical to the others.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from SSC_method.graph_construction import combinatorial_laplacian


def row_l2_norms(matrix: np.ndarray) -> np.ndarray:
    """Euclidean norm of each row."""
    values = np.asarray(matrix, dtype=np.float64)
    return np.linalg.norm(values, axis=1)


def row_l21_diagonal(residual: np.ndarray, eps: float) -> np.ndarray:
    """Diagonal of the row-wise weight in the corrected Equation (10).

    S is n by n. S_ii = 1 / (2 max(||h_i||_2, eps)), where h_i is row i of
    G - F. The paper's display of S as a diagonal whose length is the
    embedding dimension is not used; it is incompatible with the trace in
    Equation (9) and with the row-wise l2,1 norm of Nie et al. (2010).
    """
    if eps < 0.0 or not np.isfinite(eps):
        raise ValueError("eps must be finite and nonnegative")
    norms = row_l2_norms(residual)
    return 1.0 / (2.0 * np.maximum(norms, eps))


def reweighted_affinity(
    affinity: sparse.spmatrix,
    patterns: np.ndarray,
    eps: float,
) -> sparse.csr_matrix:
    """Equation (11): Wtilde_ij = W_ij / (2 max(||g_i - g_j||_2, eps)).

    ``eps`` floors only the denominator. A zero affinity stays zero. The
    result is symmetrized by averaging with its transpose.
    """
    if eps < 0.0 or not np.isfinite(eps):
        raise ValueError("eps must be finite and nonnegative")
    weights = sparse.coo_matrix(affinity, dtype=np.float64)
    patterns = np.asarray(patterns, dtype=np.float64)
    difference = patterns[weights.row] - patterns[weights.col]
    distance = np.linalg.norm(difference, axis=1)
    data = np.zeros_like(weights.data)
    active = weights.data != 0.0
    data[active] = weights.data[active] / (2.0 * np.maximum(distance[active], eps))
    reweighted = sparse.coo_matrix((data, (weights.row, weights.col)), shape=weights.shape).tocsr()
    reweighted = ((reweighted + reweighted.T) * 0.5).tocsr()
    reweighted.eliminate_zeros()
    return reweighted


def _as_csr(affinity: sparse.spmatrix | np.ndarray) -> sparse.csr_matrix:
    if sparse.issparse(affinity):
        return sparse.csr_matrix(affinity, dtype=np.float64)
    return sparse.csr_matrix(np.asarray(affinity, dtype=np.float64))


def graph_l2_term(patterns: np.ndarray, affinity: sparse.spmatrix | np.ndarray) -> float:
    """sum_{i,j} W_ij ||g_i - g_j||_2 over the stored entries of W.

    A symmetric affinity with both triangles stored counts each ordered pair
    once, which is the sum written in Equation (8).
    """
    weights = _as_csr(affinity).tocoo()
    patterns = np.asarray(patterns, dtype=np.float64)
    difference = patterns[weights.row] - patterns[weights.col]
    distance = np.linalg.norm(difference, axis=1)
    return float(np.sum(weights.data * distance))


def equation8_objective(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
) -> float:
    """Literal Equation (8), with unsmoothed Euclidean norms."""
    residual = np.asarray(patterns, dtype=np.float64) - np.asarray(embedding, dtype=np.float64)
    data_term = float(np.sum(row_l2_norms(residual)))
    return data_term + float(gamma) * graph_l2_term(patterns, affinity)


def sqrt_smoothed_equation8_objective(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    eps: float,
) -> float:
    """Equation (8) with every Euclidean norm replaced by sqrt(||v||^2 + eps^2).

    This is an epsilon-smoothed objective. It is not Equation (8), and it is
    not the same smoothing as the denominator floor max(||v||, eps) used to
    build S and Wtilde.
    """
    if eps < 0.0 or not np.isfinite(eps):
        raise ValueError("eps must be finite and nonnegative")
    patterns = np.asarray(patterns, dtype=np.float64)
    embedding = np.asarray(embedding, dtype=np.float64)
    residual = patterns - embedding
    data_term = float(np.sum(np.sqrt(np.sum(residual * residual, axis=1) + eps * eps)))
    weights = _as_csr(affinity).tocoo()
    difference = patterns[weights.row] - patterns[weights.col]
    smoothed_distance = np.sqrt(np.sum(difference * difference, axis=1) + eps * eps)
    graph_term = float(np.sum(weights.data * smoothed_distance))
    return data_term + float(gamma) * graph_term


def trace_surrogate(
    patterns: np.ndarray,
    embedding: np.ndarray,
    s_diagonal: np.ndarray,
    laplacian: sparse.spmatrix | np.ndarray,
    gamma: float,
) -> float:
    """Printed Equation (12): Tr((G-F)^T S (G-F)) + gamma Tr(G^T Ltilde G).

    S is the diagonal matrix given by ``s_diagonal``. This expression is the
    one whose stationary point is Equation (13). It is not Equation (8).
    """
    patterns = np.asarray(patterns, dtype=np.float64)
    embedding = np.asarray(embedding, dtype=np.float64)
    residual = patterns - embedding
    weighted = residual * np.asarray(s_diagonal, dtype=np.float64)[:, None]
    data_term = float(np.sum(weighted * residual))
    if sparse.issparse(laplacian):
        lg = laplacian @ patterns
    else:
        lg = np.asarray(laplacian, dtype=np.float64) @ patterns
    graph_term = float(np.sum(patterns * lg))
    return data_term + float(gamma) * graph_term


def shrinkage_laplacian(
    affinity: sparse.spmatrix,
    patterns: np.ndarray,
    eps: float,
) -> tuple[sparse.csr_matrix, sparse.csr_matrix]:
    """Recompute Wtilde and its combinatorial Laplacian from the current G."""
    reweighted = reweighted_affinity(affinity, patterns, eps=eps)
    return reweighted, combinatorial_laplacian(reweighted)
