"""kNN Gaussian affinities and Laplacians used by spectral shrunk clustering.

Samples are rows. Chang et al. (AAAI 2015) write the data matrix in Algorithm 1
as X in R^{d x n}; this package uses the array shape (n_samples, n_features).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse


def squared_euclidean(X: np.ndarray) -> np.ndarray:
    """Pairwise squared Euclidean distances. The diagonal is zero."""
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError("X must have shape (n_samples, n_features)")
    sq = np.sum(X * X, axis=1, keepdims=True)
    dist2 = sq + sq.T - 2.0 * (X @ X.T)
    np.maximum(dist2, 0.0, out=dist2)
    np.fill_diagonal(dist2, 0.0)
    return dist2


def knn_neighbor_squared_distances(
    X: np.ndarray,
    k: int,
    method: str = "auto",
) -> tuple[np.ndarray, np.ndarray]:
    """k nearest neighbors of each row, excluding the point itself.

    Returns squared distances and neighbor indices, each of shape (n, k).
    Ties break toward the smaller neighbor index. ``method='dense'`` uses a
    stable full sort. ``method='block'`` avoids an n by n matrix and, on the
    distance-cutoff boundary, follows ``argpartition``. ``method='auto'`` uses
    the dense sort for n <= 1500.
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError("X must have shape (n_samples, n_features)")
    n_samples, n_features = X.shape
    if n_features < 1:
        raise ValueError("X must have at least one feature")
    if n_samples < 2:
        raise ValueError("kNN affinity requires at least 2 samples")
    if k < 1:
        raise ValueError("k must be >= 1")
    if k >= n_samples:
        raise ValueError(f"k={k} must be strictly less than n_samples={n_samples}")
    if method == "auto":
        method = "dense" if n_samples <= 1500 else "block"
    if method == "dense":
        return _knn_dense(X, k)
    if method == "block":
        return _knn_block(X, k)
    raise ValueError("method must be 'auto', 'dense', or 'block'")


def _knn_dense(X: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    dist2 = squared_euclidean(X)
    work = dist2.copy()
    np.fill_diagonal(work, np.inf)
    order = np.argsort(work, axis=1, kind="mergesort")[:, :k]
    rows = np.arange(X.shape[0])[:, None]
    return dist2[rows, order], order


def _knn_block(X: np.ndarray, k: int, block_size: int = 128) -> tuple[np.ndarray, np.ndarray]:
    n_samples = X.shape[0]
    squared_norm = np.sum(X * X, axis=1)
    neighbor_dist2 = np.empty((n_samples, k), dtype=np.float64)
    neighbor_idx = np.empty((n_samples, k), dtype=np.int64)
    for start in range(0, n_samples, block_size):
        end = min(start + block_size, n_samples)
        block = X[start:end]
        dist2 = squared_norm[start:end, None] + squared_norm[None, :] - 2.0 * (block @ X.T)
        np.maximum(dist2, 0.0, out=dist2)
        for local, global_i in enumerate(range(start, end)):
            row = dist2[local]
            row[global_i] = np.inf
            part = np.argpartition(row, kth=k - 1)[:k]
            order = np.lexsort((part, row[part]))
            chosen = part[order]
            neighbor_idx[global_i] = chosen
            neighbor_dist2[global_i] = row[chosen]
    return neighbor_dist2, neighbor_idx


def median_positive(values: np.ndarray, fallback: float = 1.0) -> float:
    """Median of strictly positive entries, or ``fallback`` when there are none."""
    flat = np.asarray(values, dtype=np.float64).ravel()
    positive = flat[np.isfinite(flat) & (flat > 0.0)]
    if positive.size == 0:
        return float(fallback)
    return float(np.median(positive))


def knn_affinity(
    X: np.ndarray,
    k: int = 5,
    delta2: float | None = None,
    knn_method: str = "auto",
    bandwidth_rule: str | None = None,
) -> tuple[sparse.csr_matrix, dict[str, Any]]:
    """Symmetric kNN Gaussian affinity.

    The paper sets A_ij = exp(-||x_i - x_j||^2 / delta^2) when x_i and x_j
    are k nearest neighbors, and 0 otherwise. It does not say how to
    symmetrize a directed kNN relation or how to choose delta. This
    reproduction connects the undirected edge when either point lists the
    other (union), and sets delta^2 to the median of the positive directed
    kNN squared distances when ``delta2`` is omitted. The diagonal is 0.
    ``k`` is an explicit argument; the scikit-learn default neighbor count
    and the scikit-learn RBF bandwidth are not used.

    ``bandwidth_rule`` is optional and does not change that default. None
    with ``delta2 is None`` is still the median of positive kNN squared
    distances. ``mean_knn_distance_scale`` uses (mean positive kNN Euclidean
    distance)^2. ``fixed`` requires a positive ``delta2``. 
    ``self_tuning_zelnik_manor`` is a local-scale diagnostic, not the
    paper's stated affinity.
    """
    dist2, idx = knn_neighbor_squared_distances(X, k, method=knn_method)
    n_samples = X.shape[0]
    rows = np.repeat(np.arange(n_samples), k)
    cols = idx.ravel()
    rule = bandwidth_rule
    if rule is None:
        rule = "provided" if delta2 is not None else "median_positive_knn_squared_distance"
    extra_info: dict[str, Any] = {}
    if rule == "self_tuning_zelnik_manor":
        if delta2 is not None:
            raise ValueError("self-tuning bandwidth does not take a global delta2")
        sigma = np.sqrt(np.maximum(dist2[:, -1], 0.0))
        sigma = np.maximum(sigma, 1e-12)
        weights = np.exp(-dist2.ravel() / (sigma[rows] * sigma[cols]))
        delta2_used = None
        delta2_source = "self_tuning_zelnik_manor"
        extra_info["local_scale_min"] = float(sigma.min())
        extra_info["local_scale_median"] = float(np.median(sigma))
        extra_info["local_scale_max"] = float(sigma.max())
    elif rule == "mean_knn_distance_scale":
        if delta2 is not None:
            raise ValueError("mean_knn_distance_scale does not take a provided delta2")
        distances = np.sqrt(np.maximum(dist2, 0.0))
        positive = distances[dist2 > 0.0]
        mean_distance = float(np.mean(positive)) if positive.size else 1.0
        delta2_used = mean_distance * mean_distance
        if not np.isfinite(delta2_used) or delta2_used <= 0.0:
            delta2_used = 1.0
        delta2_source = "mean_knn_distance_scale"
        extra_info["mean_knn_euclidean"] = mean_distance
        weights = np.exp(-dist2.ravel() / delta2_used)
    elif rule in {"median_positive_knn_squared_distance", "provided", "fixed"}:
        if delta2 is None:
            if rule == "fixed":
                raise ValueError("fixed bandwidth requires a positive delta2")
            delta2_used = median_positive(dist2, fallback=1.0)
            delta2_source = "median_positive_knn_squared_distance"
        else:
            delta2_used = float(delta2)
            if not np.isfinite(delta2_used) or delta2_used <= 0.0:
                raise ValueError("delta2 must be finite and positive")
            delta2_source = "fixed_global" if rule == "fixed" else "provided"
        weights = np.exp(-dist2.ravel() / delta2_used)
    else:
        raise ValueError(
            f"unknown bandwidth_rule {bandwidth_rule!r}; expected median, "
            "mean_knn_distance_scale, fixed, or self_tuning_zelnik_manor"
        )
    directed = sparse.coo_matrix((weights, (rows, cols)), shape=(n_samples, n_samples))
    affinity = directed.maximum(directed.T).tocsr()
    affinity.setdiag(0.0)
    affinity.eliminate_zeros()
    info = {
        "k": int(k),
        "delta2": None if delta2_used is None else float(delta2_used),
        "delta": None if delta2_used is None else float(np.sqrt(delta2_used)),
        "delta2_source": delta2_source,
        "bandwidth_rule": rule,
        "symmetrization": "union_maximum",
        "knn_method": knn_method if knn_method != "auto" else ("dense" if n_samples <= 1500 else "block"),
    }
    info.update(extra_info)
    return affinity, info


def combinatorial_laplacian(affinity: sparse.spmatrix) -> sparse.csr_matrix:
    """L = D - W with D_ii = sum_j W_ij."""
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    degrees = np.asarray(weights.sum(axis=1)).ravel()
    return (sparse.diags(degrees) - weights).tocsr()


def symmetric_normalized_laplacian(affinity: sparse.spmatrix) -> sparse.csr_matrix:
    """Equation (4): L_n = I - D^{-1/2} A D^{-1/2}.

    A degree-zero vertex uses (D^{-1/2})_ii = 0, so its diagonal entry in
    L_n is 1 and its off-diagonal entries are 0.
    """
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    n_samples = weights.shape[0]
    degrees = np.asarray(weights.sum(axis=1)).ravel()
    inv_sqrt = np.zeros(n_samples, dtype=np.float64)
    positive = degrees > 0.0
    inv_sqrt[positive] = 1.0 / np.sqrt(degrees[positive])
    scaling = sparse.diags(inv_sqrt)
    normalized = (scaling @ weights @ scaling).tocsr()
    laplacian = sparse.eye(n_samples, format="csr", dtype=np.float64) - normalized
    return ((laplacian + laplacian.T) * 0.5).tocsr()
