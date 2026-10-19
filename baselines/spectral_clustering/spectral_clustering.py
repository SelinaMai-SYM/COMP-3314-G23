"""Spectral clustering with the symmetric normalized Laplacian in Eq. (4)."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

from ..common import as_positive_int, check_problem, resolve_params
from ..kmeans import fit_predict as kmeans_fit_predict

_DEFAULTS: dict[str, Any] = {
    "n_neighbors": 5,
    "delta": None,
    "knn_mode": "union",
    "n_init": 1,
    "max_iter": 300,
    "tol": 1e-4,
    "init": "random",
    "algorithm": "lloyd",
}


def neighbor_indices(
    X: np.ndarray, n_neighbors: int
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``k`` Euclidean neighbors of each row, excluding the row itself.

    ``NearestNeighbors`` uses brute-force search so tied distances follow a
    fixed scan of the sample. The result has shape ``(n_samples, k)``.
    """
    n_samples = X.shape[0]
    k = as_positive_int("n_neighbors", n_neighbors)
    k = min(k, n_samples - 1)
    finder = NearestNeighbors(
        n_neighbors=k + 1, algorithm="brute", metric="euclidean"
    )
    finder.fit(X)
    distances, indices = finder.kneighbors(X, return_distance=True)
    neighbors = np.empty((n_samples, k), dtype=np.int64)
    neighbor_distances = np.empty((n_samples, k), dtype=np.float64)
    for i in range(n_samples):
        keep = np.flatnonzero(indices[i] != i)[:k]
        if keep.size != k:
            raise RuntimeError(f"point {i} did not have {k} neighbors other than itself")
        neighbors[i] = indices[i, keep]
        neighbor_distances[i] = distances[i, keep]
    return neighbors, neighbor_distances


def gaussian_knn_affinity(
    X: np.ndarray,
    n_neighbors: int = 5,
    delta: float | None = None,
    knn_mode: str = "union",
) -> np.ndarray:
    """Build the Gaussian kNN affinity used by Chang et al.

    ``A_ij = exp(-||x_i - x_j||^2 / delta^2)`` when the selected neighborhood
    relation holds, and ``A_ij = 0`` otherwise. Self-loops are omitted.

    ``knn_mode="union"`` keeps an undirected edge when either point is among
    the other's ``k`` neighbors (the usual symmetric kNN graph).
    ``knn_mode="mutual"`` keeps the edge only when each point is among the
    other's ``k`` neighbors. The SSC paper does not say "mutual", so the
    baseline default is ``"union"``.

    If ``delta`` is ``None``, ``delta^2`` is the median of the squared
    distances on the edges that remain. The paper leaves ``delta``
    unspecified; this median is an explicit assumption, not a search. If
    that median is zero, every retained edge receives weight 1.
    """
    if knn_mode not in {"union", "mutual"}:
        raise ValueError("knn_mode must be 'union' or 'mutual'")
    if delta is not None:
        delta = float(delta)
        if not np.isfinite(delta) or delta <= 0:
            raise ValueError("delta must be a positive finite float")
    n_samples = X.shape[0]
    neighbors, neighbor_distances = neighbor_indices(X, n_neighbors)
    directed = np.zeros((n_samples, n_samples), dtype=bool)
    squared = np.zeros((n_samples, n_samples), dtype=np.float64)
    for i in range(n_samples):
        directed[i, neighbors[i]] = True
        squared[i, neighbors[i]] = neighbor_distances[i] ** 2
    squared = np.maximum(squared, squared.T)
    if knn_mode == "union":
        mask = np.logical_or(directed, directed.T)
    else:
        mask = np.logical_and(directed, directed.T)
    np.fill_diagonal(mask, False)
    rows, cols = np.nonzero(np.triu(mask, k=1))
    affinity = np.zeros((n_samples, n_samples), dtype=np.float64)
    if rows.size == 0:
        return affinity
    edge_squared = squared[rows, cols]
    if delta is None:
        scale = float(np.median(edge_squared))
        weights = (
            np.ones(rows.size, dtype=np.float64)
            if scale <= 0
            else np.exp(-edge_squared / scale)
        )
    else:
        weights = np.exp(-edge_squared / (delta ** 2))
    affinity[rows, cols] = weights
    affinity[cols, rows] = weights
    return affinity


def symmetric_normalized_laplacian(affinity: np.ndarray) -> np.ndarray:
    """Return ``L_n = I - D^{-1/2} A D^{-1/2}`` from Eq. (4).

    Isolated vertices keep a zero row in the normalized affinity, so their
    diagonal entry in ``L_n`` is 1. The matrix is symmetrized after this
    product to remove roundoff asymmetry.
    """
    weights = np.asarray(affinity, dtype=np.float64)
    weights = 0.5 * (weights + weights.T)
    np.fill_diagonal(weights, 0.0)
    degree = weights.sum(axis=1)
    scale = np.zeros_like(degree)
    positive = degree > 0
    scale[positive] = 1.0 / np.sqrt(degree[positive])
    normalized = (scale[:, None] * weights) * scale[None, :]
    laplacian = np.eye(weights.shape[0], dtype=np.float64) - normalized
    return 0.5 * (laplacian + laplacian.T)


def spectral_embedding(
    X: np.ndarray,
    n_clusters: int,
    n_neighbors: int = 5,
    delta: float | None = None,
    knn_mode: str = "union",
) -> np.ndarray:
    """Return the ``n_clusters`` eigenvectors for the smallest eigenvalues.

    Ng, Jordan, and Weiss row-normalize this embedding before K-means.
    Eq. (3) with the Laplacian in Eq. (4) does not, so this function does
    not row-normalize.
    """
    affinity = gaussian_knn_affinity(X, n_neighbors, delta, knn_mode)
    laplacian = symmetric_normalized_laplacian(affinity)
    _eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    return eigenvectors[:, :n_clusters]


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """Cluster with a normalized-cut embedding followed by K-means.

    Objective: minimize ``Tr(F^T L_n F)`` over the spectral embedding, where
    ``L_n`` is the symmetric normalized Laplacian in Eq. (4) of Chang et al.
    (AAAI 2015), then minimize the K-means objective on the rows of ``F``.

    The implementation does not call ``sklearn.cluster.SpectralClustering``.
    Neighborhood size, Gaussian bandwidth, graph symmetrization, Laplacian,
    and the final K-means controls are all arguments.

    Assumptions:
    - Default ``n_neighbors`` is 5, the value Chang et al. fix for the
      spectral baselines.
    - Default ``knn_mode`` is ``"union"``. Mutual kNN is available by
      argument, but it is not the silent default.
    - Default ``delta=None`` uses the median squared edge length as
      ``delta^2``. Pass a positive ``delta`` to override that assumption.
    - The final K-means step uses the same explicit controls as
      :func:`baselines.kmeans.fit_predict`, including ``init="random"`` and
      ``n_init=1``.

    Returns labels of shape ``(n_samples,)``.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    options = resolve_params(params, _DEFAULTS)
    embedding = spectral_embedding(
        features,
        clusters,
        n_neighbors=options["n_neighbors"],
        delta=options["delta"],
        knn_mode=options["knn_mode"],
    )
    kmeans_params = {
        key: options[key]
        for key in ("n_init", "max_iter", "tol", "init", "algorithm")
    }
    return kmeans_fit_predict(embedding, clusters, seed, **kmeans_params)
