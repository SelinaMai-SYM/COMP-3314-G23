"""Ding and Li (ICML 2007) adaptive LDA guided by K-means labels."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import linalg
from sklearn.decomposition import PCA

from ..common import as_positive_int, check_problem, resolve_params
from ..kmeans import fit_predict as kmeans_fit_predict

_DEFAULTS: dict[str, Any] = {
    "max_iter": 30,
    "sw_reg": 1e-8,
    "n_init": 1,
    "kmeans_max_iter": 300,
    "tol": 1e-4,
    "init": "random",
    "algorithm": "lloyd",
}


def _pca_basis(features: np.ndarray, n_components: int, seed: int) -> np.ndarray:
    """Return a ``(n_features, n_components)`` PCA basis of centered data."""
    projector = PCA(n_components=n_components, svd_solver="full", random_state=seed)
    projector.fit(features)
    return np.asarray(projector.components_.T, dtype=np.float64)


def _scatter(
    features: np.ndarray, labels: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Between-class and within-class scatters from the current labels.

    The formulas follow Ding and Li, Eqs. (2)--(3). ``features`` is already
    centered. Labels are cluster indicators produced by K-means or spectral
    clustering. Ground-truth labels are not an input.
    """
    n_features = features.shape[1]
    between = np.zeros((n_features, n_features), dtype=np.float64)
    within = np.zeros((n_features, n_features), dtype=np.float64)
    overall = features.mean(axis=0)
    for label in np.unique(labels):
        members = features[labels == label]
        count = members.shape[0]
        center = members.mean(axis=0)
        centered = members - center
        within += centered.T @ centered
        gap = center - overall
        between += count * np.outer(gap, gap)
    between = 0.5 * (between + between.T)
    within = 0.5 * (within + within.T)
    return between, within


def lda_basis(
    features: np.ndarray,
    labels: np.ndarray,
    n_components: int,
    sw_reg: float,
) -> np.ndarray:
    """Return the leading generalized eigenvectors of ``(S_b, S_w)``.

    Ding and Li solve the standard LDA problem while holding the cluster
    indicator fixed. ``scipy.linalg.eigh(S_b, S_w)`` solves
    ``S_b u = lambda S_w u`` and returns ``S_w``-orthonormal eigenvectors.
    Their Euclidean scale is left unchanged because the paper does not
    specify another scaling.

    If the smallest eigenvalue of ``S_w`` is at most ``sw_reg`` times the
    largest, ``sw_reg * max(lambda_max, 1) * I`` is added. This ridge is
    only a numerical safeguard for a singular within-class scatter. Ding
    and Li do not describe the singular case. Set ``sw_reg=0`` to refuse
    that safeguard.
    """
    if not np.isfinite(sw_reg) or sw_reg < 0:
        raise ValueError("sw_reg must be a nonnegative finite float")
    between, within = _scatter(features, labels)
    eigenvalues = np.linalg.eigvalsh(within)
    floor = float(eigenvalues[0])
    ceiling = float(eigenvalues[-1])
    if sw_reg > 0 and floor <= sw_reg * max(ceiling, 1.0):
        within = within + (sw_reg * max(ceiling, 1.0)) * np.eye(within.shape[0])
    try:
        _values, vectors = linalg.eigh(between, within)
    except linalg.LinAlgError as exc:
        raise np.linalg.LinAlgError(
            "LDA generalized eigenproblem failed; S_w may be singular. "
            "Pass a positive sw_reg or a feasible n_components."
        ) from exc
    if np.iscomplexobj(vectors):
        raise np.linalg.LinAlgError("LDA returned complex eigenvectors")
    basis = np.real(vectors[:, -n_components:])
    return basis[:, ::-1]


def _prepare_subspace(
    features: np.ndarray, n_clusters: int, n_components: int
) -> tuple[np.ndarray, int]:
    """Center ``features`` and reject a dimension classical LDA cannot span."""
    if n_components > n_clusters - 1:
        raise ValueError(
            "n_components cannot exceed n_clusters - 1. "
            "Classical LDA has at most that many discriminant directions. "
            "Ding and Li set the subspace dimension to K - 1. "
            "This fitter does not pad the remaining directions with PCA."
        )
    if n_components > features.shape[1]:
        raise ValueError("n_components cannot exceed n_features")
    centered = features - features.mean(axis=0, keepdims=True)
    return centered, n_components


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """Alternate K-means in a subspace with LDA on those cluster labels.

    Objective: Ding and Li (ICML 2007), Eq. (7),
    ``max_{U, H} Tr(U^T S_b U) / Tr(U^T S_w U)``. Their Algorithm 1
    initializes ``U`` by PCA, runs K-means on ``U^T X`` to obtain ``H``,
    recomputes ``U`` by LDA from ``H``, and repeats. ``H`` is the current
    K-means labeling. It is never a ground-truth labeling.

    Assumptions and verified differences:
    - ``n_components`` is required. Algorithm 1 fixes it at ``K - 1``.
      Any positive value up to ``K - 1`` is accepted. Larger values raise
      ``ValueError`` instead of being filled with extra PCA axes.
    - The sample is centered, as Section 2 of Ding and Li assumes.
    - The loop stops when K-means labels are unchanged or after
      ``max_iter`` LDA updates. The paper does not give a numeric cap;
      the default cap is 30.
    - A relative ridge ``sw_reg`` is added only when ``S_w`` is numerically
      singular. The default is ``1e-8``.
    - Inner K-means uses ``init="random"`` and ``n_init=1`` unless overridden.
      The same ``random_state`` is reused at every iteration.

    Returns the labels from the last K-means step, shape ``(n_samples,)``.
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
    sw_reg = float(options["sw_reg"])
    kmeans_params = {
        "n_init": options["n_init"],
        "max_iter": options["kmeans_max_iter"],
        "tol": options["tol"],
        "init": options["init"],
        "algorithm": options["algorithm"],
    }
    basis = _pca_basis(centered, n_components, seed)
    labels = kmeans_fit_predict(centered @ basis, clusters, seed, **kmeans_params)
    for _ in range(max_iter):
        if np.unique(labels).size < n_components + 1:
            break
        basis = lda_basis(centered, labels, n_components, sw_reg)
        updated = kmeans_fit_predict(centered @ basis, clusters, seed, **kmeans_params)
        if np.array_equal(updated, labels):
            labels = updated
            break
        labels = updated
    return labels
