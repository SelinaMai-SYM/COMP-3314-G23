"""LDA subspace selection combined with spectral clustering.

Chang et al. (AAAI 2015) name "LDA spectral clustering / LDA SC" in the
comparison list and in Tables 1--2. They do not give an algorithm box,
equation, or citation other than the name. Ding and Li (ICML 2007) define
the K-means version only. This module therefore keeps two clearly named
APPROXIMATE interpretations:

- ``fit_predict``: INTERPRETATION_A_ALTERNATE. Ding--Li alternation with
  spectral clustering in place of K-means.
- ``fit_predict_oneshot``: INTERPRETATION_B_ONESHOT. PCA initialization,
  one spectral clustering, one LDA step from those cluster labels, one
  spectral clustering in the LDA subspace, then stop.

Neither interpretation uses ground-truth labels. Neither belongs in a
faithful main table, even if a later ACC is closer to Chang et al.
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


def _spectral_params(options: dict[str, Any]) -> dict[str, Any]:
    return {
        "n_neighbors": options["n_neighbors"],
        "delta": options["delta"],
        "knn_mode": options["knn_mode"],
        "n_init": options["n_init"],
        "max_iter": options["max_iter_kmeans"],
        "tol": options["tol"],
        "init": options["init"],
        "algorithm": options["algorithm"],
    }


def _run_lda_spectral(
    features: np.ndarray,
    clusters: int,
    seed: int,
    n_components: int,
    options: dict[str, Any],
    max_lda_updates: int,
) -> np.ndarray:
    """Shared loop: PCA init, spectral clustering, then up to ``max_lda_updates`` LDA+SC steps."""
    centered, n_components = _prepare_subspace(features, clusters, n_components)
    spectral_params = _spectral_params(options)
    basis = _pca_basis(centered, n_components, seed)
    labels = spectral_fit_predict(centered @ basis, clusters, seed, **spectral_params)
    for _ in range(max_lda_updates):
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


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """INTERPRETATION_A_ALTERNATE: Ding--Li loop with spectral clustering.

    Objective actually optimized: the same alternation as Ding and Li
    (ICML 2007) Algorithm 1, except the partition inside the subspace is
    :func:`baselines.spectral_clustering.fit_predict` rather than K-means.
    Chang et al. do not write this loop. Status: APPROXIMATE.

    The LDA step uses only the current spectral clustering labels. There is
    no ground-truth argument. Passing ``y=...`` raises ``TypeError``.

    Assumptions:
    - ``n_components`` is required and must be at most ``n_clusters - 1``.
    - ``max_iter`` caps the number of LDA updates after the initial
      spectral clustering. Default 30.
    - Graph parameters follow the spectral baseline. Default ``k=5``.

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
    max_iter = as_positive_int("max_iter", options["max_iter"])
    return _run_lda_spectral(
        features, clusters, seed, n_components, options, max_lda_updates=max_iter
    )


def fit_predict_oneshot(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """INTERPRETATION_B_ONESHOT: one LDA update, then stop.

    Pipeline: PCA initialization, spectral clustering once, LDA from those
    cluster labels, spectral clustering once in the LDA subspace. This is a
    second named reconstruction of the unnamed "LDA SC" baseline. It is
    still APPROXIMATE and still must not enter a faithful main table.

    ``max_iter`` is rejected because a oneshot interpretation does not
    iterate. Ground-truth ``y`` is rejected.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    if "n_components" not in params:
        raise TypeError("n_components is required and is not searched internally")
    if "max_iter" in params:
        raise TypeError(
            "fit_predict_oneshot does not iterate; do not pass max_iter. "
            "Use fit_predict for INTERPRETATION_A_ALTERNATE."
        )
    n_components = as_positive_int("n_components", params["n_components"])
    options = resolve_params(
        {key: value for key, value in params.items() if key != "n_components"},
        {key: value for key, value in _DEFAULTS.items() if key != "max_iter"},
    )
    options["max_iter"] = 1
    return _run_lda_spectral(
        features, clusters, seed, n_components, options, max_lda_updates=1
    )
