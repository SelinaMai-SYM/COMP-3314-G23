"""PCA followed by the explicit spectral-clustering baseline."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.decomposition import PCA

from ..common import as_positive_int, check_problem, resolve_params
from ..spectral_clustering import fit_predict as spectral_fit_predict

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


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """Project onto a PCA subspace, then run spectral clustering there.

    Objective: the PCA variance objective, followed by the normalized-cut
    objective of :func:`baselines.spectral_clustering.fit_predict` in the projected
    coordinates. Chang et al. call this PCA spectral clustering. As with
    PCA plus K-means, the subspace dimension is an argument. Dimensions
    from 10 to 150 are not searched here.

    Assumptions:
    - ``n_components`` is required.
    - PCA uses a full SVD and centers the sample.
    - Spectral clustering uses Eq. (4), default ``k=5``, and the same
      explicit K-means controls as the spectral baseline.

    Returns labels of shape ``(n_samples,)``.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    if "n_components" not in params:
        raise TypeError("n_components is required and is not searched internally")
    n_components = as_positive_int("n_components", params["n_components"])
    limit = min(features.shape)
    if n_components > limit:
        raise ValueError(
            f"n_components={n_components} exceeds min(n_samples, n_features)={limit}"
        )
    options = resolve_params(
        {key: value for key, value in params.items() if key != "n_components"},
        _DEFAULTS,
    )
    projector = PCA(n_components=n_components, svd_solver="full", random_state=seed)
    projected = projector.fit_transform(features)
    return spectral_fit_predict(projected, clusters, seed, **options)
