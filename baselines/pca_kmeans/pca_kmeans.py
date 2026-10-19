"""PCA followed by K-means. The subspace dimension is an argument."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.decomposition import PCA

from ..common import as_positive_int, check_problem, resolve_params
from ..kmeans import fit_predict as kmeans_fit_predict

_DEFAULTS: dict[str, Any] = {
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
    """Project onto a PCA subspace and run K-means there.

    Objective: maximize captured variance in a ``n_components``-dimensional
    linear subspace, then minimize the K-means sum of squares in that
    subspace. Chang et al. (AAAI 2015) cite Xu and Wunsch (IEEE TNN 2005)
    for this baseline. Their survey does not define a new estimator. The
    paper reports the best result over dimensions 10 through 150 and does
    not state the step. This function does not search that range.

    Assumptions:
    - ``n_components`` is required. It must be at most
      ``min(n_samples, n_features)``.
    - sklearn PCA with ``svd_solver="full"`` centers ``X`` and computes a
      deterministic full SVD. ``random_state`` is forwarded only to K-means.
    - K-means parameters match :func:`baselines.kmeans.fit_predict`.

    Returns labels of shape ``(n_samples,)``.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    if "n_components" not in params:
        raise TypeError("n_components is required and is not searched internally")
    raw_components = params["n_components"]
    n_components = as_positive_int("n_components", raw_components)
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
    return kmeans_fit_predict(projected, clusters, seed, **options)
