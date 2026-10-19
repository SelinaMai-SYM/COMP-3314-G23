"""Local learning clustering (Wu and Schölkopf, NIPS 2006)."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..common import as_positive_int, check_problem, resolve_params
from ..spectral_clustering import neighbor_indices

_DEFAULTS: dict[str, Any] = {
    "n_neighbors": 5,
    "reg": 1.0,
    "kernel": "gaussian",
    "gamma": None,
    "discretization_max_iter": 30,
    "discretization_tol": 1e-8,
}


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_norm = np.sum(left * left, axis=1)[:, None]
    right_norm = np.sum(right * right, axis=1)[None, :]
    product = left @ right.T
    return np.maximum(left_norm + right_norm - 2.0 * product, 0.0)


def _cosine(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_norm = np.linalg.norm(left, axis=1, keepdims=True)
    right_norm = np.linalg.norm(right, axis=1, keepdims=True)
    left_unit = left / np.maximum(left_norm, 1e-12)
    right_unit = right / np.maximum(right_norm, 1e-12)
    return left_unit @ right_unit.T


def _kernel_blocks(
    point: np.ndarray,
    neighbors: np.ndarray,
    kernel: str,
    gamma: float,
) -> tuple[np.ndarray, np.ndarray]:
    if kernel == "gaussian":
        gram = np.exp(-_squared_distances(neighbors, neighbors) / gamma)
        column = np.exp(-_squared_distances(point, neighbors).ravel() / gamma)
        return gram, column
    if kernel == "cosine":
        gram = _cosine(neighbors, neighbors)
        column = _cosine(point, neighbors).ravel()
        return gram, column
    raise ValueError("kernel must be 'gaussian' or 'cosine'")


def local_regression_matrix(
    X: np.ndarray,
    n_neighbors: int,
    reg: float,
    kernel: str,
    gamma: float | None,
) -> np.ndarray:
    """Build the matrix ``A`` in Wu and Schölkopf, Eq. (10).

    For each point, kernel ridge regression is trained on its ``k`` neighbors
    only. Eq. (9) gives ``alpha_i^T = k_i^T (K_i + lambda I)^{-1}``. ``A``
    places those coefficients in the neighbor columns and zeros elsewhere.
    The Gaussian kernel is their Eq. (23), ``exp(-||x_i - x_j||^2 / gamma)``,
    which divides by ``gamma`` rather than by ``gamma^2``.
    """
    if kernel not in {"gaussian", "cosine"}:
        raise ValueError("kernel must be 'gaussian' or 'cosine'")
    reg = float(reg)
    if not np.isfinite(reg) or reg <= 0:
        raise ValueError("reg must be a positive finite float")
    if kernel == "cosine":
        if gamma is not None:
            raise ValueError("gamma is not used when kernel='cosine'")
        gamma = 1.0
    else:
        if gamma is None:
            scale = float(np.mean(np.linalg.norm(X, axis=1)))
            gamma = scale ** 2 if scale > 0 else 1.0
        gamma = float(gamma)
        if not np.isfinite(gamma) or gamma <= 0:
            raise ValueError("gamma must be a positive finite float")
    n_samples = X.shape[0]
    neighbors, _distances = neighbor_indices(X, n_neighbors)
    width = neighbors.shape[1]
    matrix = np.zeros((n_samples, n_samples), dtype=np.float64)
    identity = np.eye(width, dtype=np.float64)
    for i in range(n_samples):
        chosen = neighbors[i]
        gram, column = _kernel_blocks(X[i : i + 1], X[chosen], kernel, gamma)
        coefficients = np.linalg.solve(gram + reg * identity, column)
        matrix[i, chosen] = coefficients
    return matrix


def _initialize_rotation(embedding: np.ndarray, seed: int) -> np.ndarray:
    """Yu and Shi step 4, with the first row drawn from ``seed``.

    The ICCV 2003 procedure picks the first row uniformly at random and each
    later row by ``argmin`` of the accumulated absolute projections. The
    draw uses ``numpy.random.Generator(seed)``. Ties keep the smallest index.
    """
    n_samples, n_clusters = embedding.shape
    generator = np.random.default_rng(seed)
    rotation = np.zeros((n_clusters, n_clusters), dtype=np.float64)
    first = int(generator.integers(0, n_samples))
    rotation[:, 0] = embedding[first]
    accumulated = np.zeros(n_samples, dtype=np.float64)
    for column in range(1, n_clusters):
        accumulated = accumulated + np.abs(embedding @ rotation[:, column - 1])
        rotation[:, column] = embedding[int(np.argmin(accumulated))]
    return rotation


def yu_shi_discretize(
    embedding: np.ndarray,
    random_state: int,
    max_iter: int,
    tol: float,
) -> np.ndarray:
    """Solve Wu and Schölkopf Eqs. (17)--(19) by the Yu and Shi iteration.

    ``embedding`` is the row-normalized eigenvector matrix ``P*`` from their
    Eq. (2). Given ``R``, each row is assigned by non-maximum suppression.
    Given the discrete matrix, ``R`` is the orthogonal Procrustes factor
    ``U V^T`` from the SVD of ``X^T P*``. The paper stops at machine
    precision on the singular-value sum. ``tol`` defaults to ``1e-8`` because
    that sum does not reliably agree to float64 epsilon.
    """
    n_samples, n_clusters = embedding.shape
    if n_clusters == 1:
        return np.zeros(n_samples, dtype=np.int64)
    rotation = _initialize_rotation(embedding, random_state)
    previous_score = 0.0
    labels = np.zeros(n_samples, dtype=np.int64)
    for _ in range(max_iter):
        labels = np.argmax(embedding @ rotation, axis=1).astype(np.int64, copy=False)
        discrete = np.zeros((n_samples, n_clusters), dtype=np.float64)
        discrete[np.arange(n_samples), labels] = 1.0
        left, values, right = np.linalg.svd(discrete.T @ embedding, full_matrices=False)
        score = float(np.sum(values))
        rotation = left @ right
        if abs(score - previous_score) <= tol:
            break
        previous_score = score
    return labels


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """Cluster by local kernel ridge regression and Yu--Shi discretization.

    Objective: Wu and Schölkopf (NIPS 2006), Eq. (14),
    ``min_F Tr(F^T T F)`` subject to ``F^T F = I``, where
    ``T = (I - A)^T (I - A)`` and ``A`` is the local ridge-regression
    matrix. The discrete partition minimizes their Eq. (17), the distance
    from the row-normalized eigenvectors to an orthogonal transform. They
    explicitly adopt Yu and Shi (ICCV 2003) for that step rather than
    K-means on the embedding.

    Assumptions:
    - Default ``n_neighbors`` is 5 so the call matches the neighborhood size
      Chang et al. fix for spectral methods. The LLC paper instead searches
      ``k``. This fitter does not search it.
    - Default ``reg`` is 1, one value on their grid ``{0.1, 1, 1.5}``.
    - Default ``kernel`` is ``"gaussian"``. If ``gamma`` is ``None``, it is
      set to the square of the mean Euclidean norm of the rows. That is the
      center ``sigma_0^2`` of their gamma grid, not a selected optimum.
    - ``"cosine"`` implements their Eq. (22) and does not use ``gamma``.

    Returns labels of shape ``(n_samples,)``. A cluster index may be unused
    if non-maximum suppression leaves it empty.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    options = resolve_params(params, _DEFAULTS)
    regression = local_regression_matrix(
        features,
        n_neighbors=options["n_neighbors"],
        reg=options["reg"],
        kernel=options["kernel"],
        gamma=options["gamma"],
    )
    residual = np.eye(features.shape[0], dtype=np.float64) - regression
    gram = residual.T @ residual
    gram = 0.5 * (gram + gram.T)
    _values, vectors = np.linalg.eigh(gram)
    raw = vectors[:, :clusters]
    row_norm = np.linalg.norm(raw, axis=1, keepdims=True)
    normalized = raw / np.maximum(row_norm, 1e-12)
    return yu_shi_discretize(
        normalized,
        seed,
        max_iter=as_positive_int(
            "discretization_max_iter", options["discretization_max_iter"]
        ),
        tol=float(options["discretization_tol"]),
    )
