"""LDA subspace selection alternated with spectral clustering.

Chang et al. name LDA spectral clustering but do not state whether the LDA
labels come from one initial clustering or from an alternation. This module
reuses the Ding and Li iteration with spectral clustering in place of
K-means. The status of that choice is APPROXIMATE; see the package README.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..common import as_positive_int, check_problem, resolve_params
from ..lda_kmeans import _pca_basis, _prepare_subspace, lda_basis
from ..spectral_clustering import fit_predict as spectral_fit_predict

_DEFAULTS: dict[str, Any] = {
    "max_iter": 30,
    "sw_reg": 1e-8,
    "n_neighbors": 5,
    "delta": None,
    "knn_mode": "union",
    "n_init": 1,
    "max_iter_kmeans": 300,
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
    """Alternate spectral clustering in a subspace with LDA on its labels.

    Objective actually optimized: the same alternation as Ding and Li
    (ICML 2007), except the partition inside the subspace is the spectral
    clustering partition from :func:`baselines.spectral_clustering.fit_predict` rather
    than K-means. Chang et al. (AAAI 2015) list "LDA spectral clustering"
    without an algorithm box, so this is an explicit approximation of that
    baseline, not a line-by-line reproduction.

    The LDA step uses only the current spectral clustering labels. There is
    no ground-truth argument.

    Assumptions:
    - ``n_components`` is required and must be at most ``n_clusters - 1``.
    - ``max_iter`` caps the alternation. ``max_iter_kmeans`` is forwarded
      to the K-means step inside spectral clustering.
    - Graph parameters ``n_neighbors``, ``delta``, and ``knn_mode`` follow
      the spectral baseline. The default neighborhood size is 5.

    Returns labels of shape ``(n_samples,)``.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    if "n_components" not in params:
        raise TypeError("n_components is required and is not searched internally")
    n_components = as_positive_int("n_components", params["n_components"])
    options = resolve_params(
        {key: value for key, value in params.items() if key != "n_components"},
        _DEFAULTS,
    )
    centered, n_components = _prepare_subspace(features, clusters, n_components)
    max_iter = as_positive_int("max_iter", options["max_iter"])
    spectral_params = {
        "n_neighbors": options["n_neighbors"],
        "delta": options["delta"],
        "knn_mode": options["knn_mode"],
        "n_init": options["n_init"],
        "max_iter": options["max_iter_kmeans"],
        "tol": options["tol"],
        "init": options["init"],
        "algorithm": options["algorithm"],
    }
    basis = _pca_basis(centered, n_components, seed)
    labels = spectral_fit_predict(centered @ basis, clusters, seed, **spectral_params)
    for _ in range(max_iter):
        if np.unique(labels).size < n_components + 1:
            break
        basis = lda_basis(centered, labels, n_components, float(options["sw_reg"]))
        updated = spectral_fit_predict(
            centered @ basis, clusters, seed, **spectral_params
        )
        if np.array_equal(updated, labels):
            labels = updated
            break
        labels = updated
    return labels
