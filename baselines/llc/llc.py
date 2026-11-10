"""Local learning clustering (Wu and Schölkopf, NIPS 2006)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, eigsh

from ..common import as_positive_int, check_problem, resolve_params
from ..spectral_clustering import neighbor_indices

_DEFAULTS: dict[str, Any] = {
    "n_neighbors": 5,
    "reg": 1.0,
    "kernel": "gaussian",
    "gamma": None,
    "discretization_max_iter": 30,
    "discretization_tol": 1e-8,
    "dense_threshold": 512,
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
    passed_gamma = None if kernel == "cosine" else gamma
    return np.asarray(local_regression_sparse(
        X, n_neighbors, reg, kernel, passed_gamma
    ).toarray(), dtype=np.float64)


def local_regression_sparse(
    X: np.ndarray,
    n_neighbors: int,
    reg: float,
    kernel: str,
    gamma: float | None,
) -> sparse.csr_matrix:
    """Same local ridge matrix as :func:`local_regression_matrix`, stored sparse.

    Each row has ``n_neighbors`` coefficients. Callers that only need
    matvecs of ``(I - A)^T (I - A)`` should use this form.
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
    identity = np.eye(width, dtype=np.float64)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for i in range(n_samples):
        chosen = neighbors[i]
        gram, column = _kernel_blocks(X[i : i + 1], X[chosen], kernel, float(gamma))
        coefficients = np.linalg.solve(gram + reg * identity, column)
        rows.extend([i] * width)
        cols.extend(int(index) for index in chosen)
        data.extend(float(value) for value in coefficients)
    return sparse.csr_matrix((data, (rows, cols)), shape=(n_samples, n_samples))


def _orient_signs(vectors: np.ndarray) -> np.ndarray:
    oriented = np.array(vectors, dtype=np.float64, copy=True)
    for column in range(oriented.shape[1]):
        pivot = int(np.argmax(np.abs(oriented[:, column])))
        if oriented[pivot, column] < 0.0:
            oriented[:, column] *= -1.0
    return oriented


def llc_normalized_embedding(
    X: np.ndarray,
    n_clusters: int,
    n_neighbors: int,
    reg: float,
    kernel: str,
    gamma: float | None,
    dense_threshold: int = 512,
    *,
    return_state: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Smallest eigenvectors of ``(I-A)^T (I-A)``, then row-normalize.

    For ``n_samples > dense_threshold`` the product is applied as a
    sparse matvec. That is the same operator as the dense Gram matrix,
    not a landmark or subsampled approximation.
    """
    regression = local_regression_sparse(X, n_neighbors, reg, kernel, gamma)
    n_samples = regression.shape[0]
    clusters = int(n_clusters)
    if n_samples <= dense_threshold or clusters >= n_samples - 1:
        residual = sparse.eye(n_samples, format="csr") - regression
        gram = (residual.T @ residual).toarray()
        gram = 0.5 * (gram + gram.T)
        values, vectors = np.linalg.eigh(gram)
        raw = vectors[:, :clusters]
        solver = "numpy.linalg.eigh"
        eigenvalues = np.asarray(values[:clusters], dtype=np.float64)
    else:
        def matvec(vector: np.ndarray) -> np.ndarray:
            residual = vector - regression @ vector
            return residual - regression.T @ residual

        operator = LinearOperator(
            (n_samples, n_samples), matvec=matvec, dtype=np.float64
        )
        eigenvalues, raw = eigsh(operator, k=clusters, which="SA")
        order = np.argsort(eigenvalues)
        eigenvalues = np.asarray(eigenvalues[order], dtype=np.float64)
        raw = raw[:, order]
        solver = "scipy.sparse.linalg.eigsh"
    raw = _orient_signs(raw)
    row_norm = np.linalg.norm(raw, axis=1, keepdims=True)
    normalized = raw / np.maximum(row_norm, 1e-12)
    effective_gamma = gamma
    if kernel == "gaussian" and gamma is None:
        scale = float(np.mean(np.linalg.norm(X, axis=1)))
        effective_gamma = scale ** 2 if scale > 0 else 1.0
    info = {
        "solver": solver,
        "eigenvalues": eigenvalues,
        "llc_ridge": float(reg),
        "llc_kernel": kernel,
        "llc_kernel_bandwidth": None if kernel == "cosine" else float(effective_gamma),
        "n_neighbors": int(n_neighbors),
        "n_samples": int(n_samples),
    }
    if return_state:
        info["fit_state"] = {"regression_matrix": regression, "raw_embedding": raw, "row_norms": row_norm}
    return normalized, info


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


def orthogonal_procrustes_rotation(target: np.ndarray, embedding: np.ndarray) -> np.ndarray:
    """Return ``R`` minimizing ``||target - embedding @ R||_F`` with ``R.T @ R = I``.

    If ``target.T @ embedding = U diag(s) V.T``, the minimizer on the
    column-orthonormal case (and the classical orthogonal Procrustes
    solution) is ``R = V @ U.T``. NumPy's ``svd`` returns ``Vt = V.T``, so
    ``R = Vt.T @ U.T``. The previous orientation ``U @ Vt`` solves the
    swapped factor and is not this update.
    """
    left, _values, right = np.linalg.svd(target.T @ embedding, full_matrices=False)
    return right.T @ left.T


def _assignment_labels(embedding: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    return np.argmax(embedding @ rotation, axis=1).astype(np.int64, copy=False)


def _one_hot(labels: np.ndarray, n_clusters: int) -> np.ndarray:
    discrete = np.zeros((labels.shape[0], n_clusters), dtype=np.float64)
    discrete[np.arange(labels.shape[0]), labels] = 1.0
    return discrete


def procrustes_objective(target: np.ndarray, embedding: np.ndarray, rotation: np.ndarray) -> float:
    """Squared Frobenius distance ``||target - embedding @ rotation||_F^2``."""
    residual = target - embedding @ rotation
    return float(np.sum(residual * residual))


def yu_shi_discretize_state(
    embedding: np.ndarray,
    random_state: int,
    max_iter: int,
    tol: float,
) -> dict[str, Any]:
    """Yu--Shi iteration with a Procrustes rotation that matches its labels.

    The returned labels are ``argmax`` of ``embedding @ R`` for the returned
    ``R``. The logged objective is ``||Y - embedding @ R||_F^2`` for that
    same one-hot ``Y``. The rotation itself is the orthogonal Procrustes
    factor of the assignment from the previous ``R``, then labels are
    refreshed from the updated ``R`` so the pair is the state that is scored.
    """
    n_samples, n_clusters = embedding.shape
    if n_clusters == 1:
        labels = np.zeros(n_samples, dtype=np.int64)
        rotation = np.ones((1, 1), dtype=np.float64)
        return {
            "labels": labels,
            "rotation": rotation,
            "objective": 0.0,
            "singular_value_sum": 0.0,
            "n_iterations": 0,
            "converged": True,
        }
    rotation = _initialize_rotation(embedding, random_state)
    previous_score = None
    converged = False
    iterations = 0
    for iterations in range(1, max_iter + 1):
        labels = _assignment_labels(embedding, rotation)
        discrete = _one_hot(labels, n_clusters)
        left, values, right = np.linalg.svd(discrete.T @ embedding, full_matrices=False)
        score = float(np.sum(values))
        rotation = right.T @ left.T
        if previous_score is not None and abs(score - previous_score) <= tol:
            converged = True
            break
        previous_score = score
    labels = _assignment_labels(embedding, rotation)
    discrete = _one_hot(labels, n_clusters)
    objective = procrustes_objective(discrete, embedding, rotation)
    _left, values, _right = np.linalg.svd(discrete.T @ embedding, full_matrices=False)
    return {
        "labels": labels,
        "rotation": rotation,
        "objective": objective,
        "singular_value_sum": float(np.sum(values)),
        "n_iterations": iterations,
        "converged": converged,
    }


def yu_shi_discretize(
    embedding: np.ndarray,
    random_state: int,
    max_iter: int,
    tol: float,
) -> np.ndarray:
    """Solve Wu and Schölkopf Eqs. (17)--(19) by the Yu and Shi iteration.

    ``embedding`` is the row-normalized eigenvector matrix. Given ``R``, each
    row is assigned by non-maximum suppression. Given that discrete matrix
    ``Y``, the rotation is the orthogonal Procrustes factor
    ``R = V @ U.T`` of ``Y.T @ embedding = U diag(s) V.T``
    (NumPy: ``R = Vt.T @ U.T``). The returned labels are recomputed from
    that rotation, so they refer to the same ``R`` as the logged objective
    in :func:`yu_shi_discretize_state`.
    """
    return yu_shi_discretize_state(embedding, random_state, max_iter, tol)["labels"]


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
    normalized, _info = llc_normalized_embedding(
        features,
        n_clusters=clusters,
        n_neighbors=options["n_neighbors"],
        reg=options["reg"],
        kernel=options["kernel"],
        gamma=options["gamma"],
        dense_threshold=as_positive_int("dense_threshold", options["dense_threshold"]),
    )
    return yu_shi_discretize(
        normalized,
        seed,
        max_iter=as_positive_int(
            "discretization_max_iter", options["discretization_max_iter"]
        ),
        tol=float(options["discretization_tol"]),
    )
