"""Mutual kNN Gaussian affinity for the Reliability-aware SSC extension.

The construction lives here, not in SSC_method. Spectral embedding still uses
the original union-kNN graph. Only the shrinkage weight W on F changes.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse

from SSC_method.graph_construction import knn_neighbor_squared_distances, median_positive


def directed_knn_mask(
    neighbor_idx: np.ndarray,
    n_samples: int,
) -> sparse.csr_matrix:
    """Binary directed kNN adjacency with a zero diagonal."""
    k = int(neighbor_idx.shape[1])
    rows = np.repeat(np.arange(n_samples, dtype=np.int64), k)
    cols = np.asarray(neighbor_idx, dtype=np.int64).ravel()
    data = np.ones(rows.shape[0], dtype=np.float64)
    directed = sparse.csr_matrix((data, (rows, cols)), shape=(n_samples, n_samples))
    directed.setdiag(0.0)
    directed.eliminate_zeros()
    return directed


def mutual_knn_affinity(
    X: np.ndarray,
    k: int = 5,
    delta2: float | None = None,
    knn_method: str = "auto",
) -> tuple[sparse.csr_matrix, dict[str, Any]]:
    """Symmetric mutual-kNN Gaussian affinity on the rows of ``X``.

    An undirected edge is kept only when each point lists the other among its
    ``k`` nearest neighbors (the AND rule). Gaussian weights use the same
    bandwidth rule as original SSC: if ``delta2`` is omitted, it is the median
    of the positive *directed* kNN squared distances, computed before the
    mutual filter. Using the directed median keeps the scale comparable with
    union kNN; the extension then only deletes edges.

    The diagonal is 0. Weights are nonnegative. The matrix is symmetric.
    """
    dist2, idx = knn_neighbor_squared_distances(X, k, method=knn_method)
    n_samples = int(X.shape[0])
    if delta2 is None:
        delta2_used = median_positive(dist2, fallback=1.0)
        delta2_source = "median_positive_knn_squared_distance"
    else:
        delta2_used = float(delta2)
        delta2_source = "provided"
        if not np.isfinite(delta2_used) or delta2_used <= 0.0:
            raise ValueError("delta2 must be finite and positive")

    directed = directed_knn_mask(idx, n_samples)
    mutual_mask = directed.multiply(directed.T).tocsr()
    mutual_mask.eliminate_zeros()

    rows = np.repeat(np.arange(n_samples), k)
    cols = idx.ravel()
    gauss = np.exp(-dist2.ravel() / delta2_used)
    directed_weighted = sparse.csr_matrix(
        (gauss, (rows, cols)), shape=(n_samples, n_samples)
    )
    directed_weighted.setdiag(0.0)
    affinity = directed_weighted.multiply(mutual_mask)
    affinity = ((affinity + affinity.T) * 0.5).tocsr()
    affinity.setdiag(0.0)
    affinity.eliminate_zeros()
    if affinity.nnz and np.any(affinity.data < 0.0):
        raise RuntimeError("mutual kNN produced a negative weight")

    union = directed.maximum(directed.T)
    union.setdiag(0.0)
    union.eliminate_zeros()
    info = {
        "k": int(k),
        "delta2": float(delta2_used),
        "delta": float(np.sqrt(delta2_used)),
        "delta2_source": delta2_source,
        "symmetrization": "mutual_and",
        "knn_method": knn_method
        if knn_method != "auto"
        else ("dense" if n_samples <= 1500 else "block"),
        "n_directed_edges": int(directed.nnz),
        "n_union_undirected_edges": int(union.nnz // 2),
        "n_mutual_undirected_edges": int(affinity.nnz // 2),
    }
    return affinity, info
