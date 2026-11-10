"""One-shot SLPS (Hou et al., IPM 2013), called SPLS by Chang et al.

The experiments in Hou et al. use the one-shot form (their Eqs. 18--19),
which is the beta -> 0 case of the alternating procedure. Clustering in
that paper is K-means or Ncut on the embedding. This module implements
the one-shot embedding. It does not treat K-means-on-raw-pixels as SLPS.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from ..common import as_positive_int, check_problem, resolve_params
from ..kmeans import fit_predict as kmeans_fit_predict
from ..spectral_clustering import neighbor_indices

_DEFAULTS: dict[str, Any] = {
    "n_components": None,
    "alpha": 0.5,
    "n_neighbors": 7,
    "n_init": 1,
    "max_iter": 300,
    "tol": 1e-4,
    "init": "random",
    "algorithm": "lloyd",
}


def local_scaling_affinity(X: np.ndarray, n_neighbors: int) -> sparse.csr_matrix:
    """Union kNN weights with Zelnik-Manor local scaling.

    Hou et al. Eq. (7) is a Gaussian kNN graph. Section 4 replaces the
    global width by the local scale of Zelnik-Manor and Perona (2004):
    sigma_i is the distance to the k-th neighbor, and
    ``W_ij = exp(-||x_i-x_j||^2 / (sigma_i sigma_j))`` when either point
    is among the other's k neighbors. Their experiments fix k = 7.
    """
    neighbors, distances = neighbor_indices(X, n_neighbors)
    sigma = np.maximum(distances[:, -1], 1e-12)
    n_samples, width = neighbors.shape
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for i in range(n_samples):
        for t in range(width):
            j = int(neighbors[i, t])
            weight = float(np.exp(-(distances[i, t] ** 2) / (sigma[i] * sigma[j])))
            rows.append(i)
            cols.append(j)
            data.append(weight)
    affinity = sparse.csr_matrix((data, (rows, cols)), shape=(n_samples, n_samples))
    # The weight is symmetric in (i, j). maximum keeps a one-sided edge
    # at that value instead of averaging it with a structural zero.
    return affinity.maximum(affinity.T).tocsr()


def oneshot_shrunk_patterns(
    X: np.ndarray,
    alpha: float,
    n_neighbors: int = 7,
    *,
    return_state: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Hou et al. Eq. (18): ``Y = alpha X [(1-alpha) L + alpha I]^{-1}``.

    ``X`` here has shape ``(n_samples, n_features)``. The paper stores
    samples as columns, so the solve is on the left.
    """
    alpha = float(alpha)
    if not np.isfinite(alpha) or not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must lie in (0, 1]")
    features = np.asarray(X, dtype=np.float64)
    affinity = local_scaling_affinity(features, n_neighbors)
    degree = np.asarray(affinity.sum(axis=1)).ravel()
    laplacian = sparse.diags(degree) - affinity
    n_samples = features.shape[0]
    coefficient = (1.0 - alpha) * laplacian + alpha * sparse.eye(n_samples, format="csc")
    coefficient = ((coefficient + coefficient.T) * 0.5).tocsc()
    shrunk = alpha * np.asarray(spsolve(coefficient, features), dtype=np.float64)
    if shrunk.ndim == 1:
        shrunk = shrunk.reshape(-1, 1)
    if not np.isfinite(shrunk).all():
        raise RuntimeError("one-shot SLPS produced non-finite shrunk patterns")
    info = {
        "alpha": alpha,
        "n_neighbors": int(n_neighbors),
        "graph": "zelnik_manor_local_scaling_union_knn",
        "form": "one_shot_eq18",
        "beta": 0.0,
        "n_undirected_edges": int(np.count_nonzero(np.triu(affinity.toarray(), k=1)))
        if n_samples <= 1500
        else int(affinity.nnz // 2),
    }
    if return_state:
        info["fit_state"] = {"affinity": affinity, "laplacian": laplacian, "coefficient": coefficient}
    return shrunk, info


def pca_embedding(patterns: np.ndarray, n_components: int) -> tuple[np.ndarray, dict[str, Any]]:
    """Max-variance projection of centered shrunk patterns, Hou et al. Eq. (19)."""
    centered = patterns - patterns.mean(axis=0, keepdims=True)
    _u, singular, vt = np.linalg.svd(centered, full_matrices=False)
    rank = int(np.sum(singular > singular[0] * 1e-10)) if singular.size else 0
    if n_components > rank:
        raise ValueError(
            f"n_components={n_components} exceeds numerical rank {rank} of the shrunk patterns"
        )
    scores = centered @ vt[:n_components].T
    total = float(np.sum(singular ** 2))
    retained = float(np.sum(singular[:n_components] ** 2))
    return scores, {
        "n_components": int(n_components),
        "numerical_rank": rank,
        "explained_variance_ratio": retained / total if total > 0 else float("nan"),
        "whitening": False,
    }


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """One-shot SLPS followed by one K-means run on the embedding.

    Ground-truth labels are not an argument. ``n_components`` is required.
    Hou et al. select the subspace dimension and alpha by a search whose
    unsupervised criterion is not stated; this function does not search.
    """
    if "y" in params:
        raise TypeError("SLPS fit does not accept ground-truth labels")
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    if "n_components" not in params or params["n_components"] is None:
        raise TypeError("n_components is required and is not searched internally")
    options = resolve_params(params, _DEFAULTS)
    n_components = as_positive_int("n_components", options["n_components"])
    shrunk, _info = oneshot_shrunk_patterns(
        features,
        alpha=float(options["alpha"]),
        n_neighbors=as_positive_int("n_neighbors", options["n_neighbors"]),
    )
    embedding, _pca = pca_embedding(shrunk, n_components)
    return kmeans_fit_predict(
        embedding,
        clusters,
        seed,
        n_init=options["n_init"],
        max_iter=options["max_iter"],
        tol=options["tol"],
        init=options["init"],
        algorithm=options["algorithm"],
    )
