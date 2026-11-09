"""Spectral clustering with the symmetric normalized Laplacian in Eq. (4)."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

from ..common import as_positive_int, check_problem, resolve_params
from ..kmeans import fit_predict as kmeans_fit_predict
from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding as shared_spectral_embedding

_DEFAULTS: dict[str, Any] = {
    "n_neighbors": 5,
    "delta": None,
    "knn_mode": "union",
    "bandwidth_rule": None,
    "row_normalize": False,
    "laplacian": "symmetric_normalized_eq4",
    "knn_method": "auto",
    "dense_threshold": 512,
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

    This helper is the LLC local-regression neighborhood. It is **not** the
    Eq. (4) graph used by spectral clustering and SSC. Those methods share
    ``SSC_method.graph_construction.knn_affinity``.
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
    bandwidth_rule: str | None = None,
    knn_method: str = "auto",
) -> np.ndarray:
    """Build the Gaussian kNN affinity used by Chang et al.

    ``A_ij = exp(-||x_i - x_j||^2 / delta^2)`` when the selected neighborhood
    relation holds, and ``A_ij = 0`` otherwise. Self-loops are omitted.

    ``knn_mode="union"`` keeps an undirected edge when either point is among
    the other's ``k`` neighbors (the usual symmetric kNN graph).
    ``knn_mode="mutual"`` keeps the edge only when each point is among the
    other's ``k`` neighbors. The SSC paper does not say "mutual", so the
    baseline default is ``"union"``.

    If ``delta`` is ``None``, ``delta^2`` follows the shared SSC bandwidth
    rule: the median of the positive directed kNN squared distances, unless
    ``bandwidth_rule`` selects another explicit scale. The paper leaves
    ``delta`` unspecified; that median is an assumption, not a search.

    The neighbors, Gaussian, and symmetrization are the shared Eq. (4)
    construction in ``SSC_method.graph_construction.knn_affinity``. This
    wrapper returns a dense array for the historical SC API.
    """
    if knn_mode not in {"union", "mutual"}:
        raise ValueError("knn_mode must be 'union' or 'mutual'")
    if delta is not None:
        delta = float(delta)
        if not np.isfinite(delta) or delta <= 0:
            raise ValueError("delta must be a positive finite float")
    affinity, _info = knn_affinity(
        X,
        k=as_positive_int("n_neighbors", n_neighbors),
        delta2=None if delta is None else float(delta) ** 2,
        knn_method=knn_method,
        bandwidth_rule=bandwidth_rule,
        symmetrization=knn_mode,
    )
    return np.asarray(affinity.toarray(), dtype=np.float64)


def symmetric_normalized_laplacian(affinity: np.ndarray) -> np.ndarray:
    """Return ``L_n = I - D^{-1/2} A D^{-1/2}`` from Eq. (4).

    Isolated vertices keep a zero row in the normalized affinity, so their
    diagonal entry in ``L_n`` is 1. The matrix is symmetrized after this
    product to remove roundoff asymmetry. The shared sparse operator in
    ``SSC_method.graph_construction`` is the same formula; this dense form
    is kept for small hand checks.
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


def _embedding_config(
    n_neighbors: int,
    delta: float | None,
    knn_mode: str,
    bandwidth_rule: str | None = None,
    row_normalize: bool = False,
    laplacian: str = "symmetric_normalized_eq4",
    knn_method: str = "auto",
    dense_threshold: int = 512,
) -> SpectralGraphConfig:
    return SpectralGraphConfig(
        k=int(n_neighbors),
        delta=delta,
        bandwidth_rule=bandwidth_rule,
        symmetrization=knn_mode,
        laplacian=laplacian,
        row_normalize=bool(row_normalize),
        knn_method=knn_method,
        dense_threshold=int(dense_threshold),
    )


def spectral_embedding(
    X: np.ndarray,
    n_clusters: int,
    n_neighbors: int = 5,
    delta: float | None = None,
    knn_mode: str = "union",
    bandwidth_rule: str | None = None,
    row_normalize: bool = False,
    laplacian: str = "symmetric_normalized_eq4",
    knn_method: str = "auto",
    dense_threshold: int = 512,
    return_info: bool = False,
) -> np.ndarray | tuple[np.ndarray, dict[str, Any]]:
    """Return the ``n_clusters`` eigenvectors for the smallest eigenvalues.

    Ng, Jordan, and Weiss row-normalize this embedding before K-means.
    Eq. (3) with the Laplacian in Eq. (4) does not, so this function does
    not row-normalize unless ``row_normalize=True`` is passed as a
    Category C diagnostic.

    The graph, Laplacian, eigensolve, and sign convention are the shared
    Eq. (4) path used by SSC. Column signs follow
    ``largest_magnitude_positive``. Compare that aligned F with
    ``SSC_method.spectral_embedding``; do not evaluate shrinkage against a
    second independent embedding.
    """
    config = _embedding_config(
        n_neighbors=n_neighbors,
        delta=delta,
        knn_mode=knn_mode,
        bandwidth_rule=bandwidth_rule,
        row_normalize=row_normalize,
        laplacian=laplacian,
        knn_method=knn_method,
        dense_threshold=dense_threshold,
    )
    embedding, info = shared_spectral_embedding(
        X, n_components=n_clusters, config=config
    )
    if return_info:
        return embedding, info
    return embedding


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
    and the final K-means controls are all arguments. The Eq. (4) embedding
    is the shared path with SSC.

    Assumptions:
    - Default ``n_neighbors`` is 5, the value Chang et al. fix for the
      spectral baselines.
    - Default ``knn_mode`` is ``"union"``. Mutual kNN is available by
      argument, but it is not the silent default.
    - Default ``delta=None`` uses the shared median of positive directed
      kNN squared distances as ``delta^2``. Pass a positive ``delta`` to
      override that assumption.
    - The final K-means step uses the same explicit controls as
      :func:`baselines.kmeans.fit_predict`, including ``init="random"`` and
      ``n_init=1``. ``tol`` here is the sklearn K-means tolerance, not the
      SSC IRLS tolerance.

    Returns labels of shape ``(n_samples,)``.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    options = resolve_params(params, _DEFAULTS)
    embedding = spectral_embedding(
        features,
        n_clusters=clusters,
        n_neighbors=options["n_neighbors"],
        delta=options["delta"],
        knn_mode=options["knn_mode"],
        bandwidth_rule=options["bandwidth_rule"],
        row_normalize=bool(options["row_normalize"]),
        laplacian=options["laplacian"],
        knn_method=options["knn_method"],
        dense_threshold=options["dense_threshold"],
    )
    kmeans_params = {
        key: options[key]
        for key in ("n_init", "max_iter", "tol", "init", "algorithm")
    }
    return kmeans_fit_predict(embedding, clusters, seed, **kmeans_params)
