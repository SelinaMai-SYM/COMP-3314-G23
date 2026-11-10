"""Ding and Li (ICML 2007) adaptive LDA guided by K-means labels."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import linalg
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import hashlib
import time

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


def _data_span(features: np.ndarray) -> np.ndarray | None:
    """Orthonormal basis of the row space when there are more features than samples.

    Centered samples span at most ``n_samples - 1`` directions. The leading
    generalized eigenvectors of the ridged pencil live in that span, so the
    ambient eigenproblem reduces to an equivalent smaller one. This is not a
    landmark or subsample approximation.
    """
    n_samples, n_features = features.shape
    if n_features <= n_samples:
        return None
    _left, singular, vt = np.linalg.svd(features, full_matrices=False)
    if singular.size == 0 or singular[0] <= 0:
        return None
    rank = int(np.sum(singular > singular[0] * 1e-10))
    if rank <= 0 or rank >= n_features:
        return None
    return np.ascontiguousarray(vt[:rank].T)


def lda_basis(
    features: np.ndarray,
    labels: np.ndarray,
    n_components: int,
    sw_reg: float,
    ambient_dimension: int | None = None,
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
    # A wide ambient scatter has a null space even when this reduced within
    # scatter does not. The ridge decision follows that ambient matrix.
    ambient = features.shape[1] if ambient_dimension is None else int(ambient_dimension)
    floor = 0.0 if ambient > features.shape[1] else float(eigenvalues[0])
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


def _lda_basis_for_fit(
    features: np.ndarray,
    labels: np.ndarray,
    n_components: int,
    sw_reg: float,
    span: np.ndarray | None,
) -> np.ndarray:
    if span is None:
        return lda_basis(features, labels, n_components, sw_reg)
    reduced = lda_basis(
        features @ span,
        labels,
        n_components,
        sw_reg,
        ambient_dimension=features.shape[1],
    )
    return span @ reduced


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


def scatter_objective(
    features: np.ndarray, labels: np.ndarray, basis: np.ndarray
) -> dict[str, float]:
    """Ratio of traces on the current subspace, after centering is assumed.

    Ding and Li write ``Tr(U^T S_b U) / Tr(U^T S_w U)``. The generalized
    eigenproblem instead maximizes ``Tr(U^T S_b U)`` subject to
    ``U^T S_w U = I``. Under that constraint the denominator equals the
    number of columns, so the ratio of traces is the mean of the retained
    generalized eigenvalues. This is not ``Tr(S_w^{-1} S_b)``.
    """
    between, within = _scatter(features, labels)
    numerator = float(np.trace(basis.T @ between @ basis))
    denominator = float(np.trace(basis.T @ within @ basis))
    ratio = float(numerator / denominator) if denominator > 0.0 else float("nan")
    return {
        "trace_between": numerator,
        "trace_within": denominator,
        "ratio_of_traces": ratio,
    }


def partitions_equal(left: np.ndarray, right: np.ndarray) -> bool:
    """Compare partitions without relying on numeric cluster names or NMI rounding."""
    left = np.asarray(left); right = np.asarray(right)
    if left.shape != right.shape:
        return False
    forward = {}; backward = {}
    for a, b in zip(left.tolist(), right.tolist()):
        if (a in forward and forward[a] != b) or (b in backward and backward[b] != a):
            return False
        forward[a] = b; backward[b] = a
    return True


def _array_hash(value: np.ndarray) -> str:
    value = np.ascontiguousarray(value)
    return hashlib.sha256(str(value.shape).encode() + str(value.dtype).encode() + value.tobytes()).hexdigest()


def _matrix_diagnostics(within: np.ndarray) -> dict[str, Any]:
    eigenvalues = np.linalg.eigvalsh(within)
    largest = float(np.max(np.abs(eigenvalues), initial=0.0))
    tolerance = np.finfo(np.float64).eps * max(within.shape) * largest
    positive = eigenvalues[eigenvalues > tolerance]
    return {"within_rank": int(len(positive)), "within_dimension": len(eigenvalues),
            "within_min_eigenvalue": float(eigenvalues.min()) if len(eigenvalues) else None,
            "within_max_eigenvalue": largest,
            "within_condition_positive": float(largest / positive.min()) if len(positive) else None,
            "rank_tolerance": tolerance}


def fit_state(X: np.ndarray, n_clusters: int, random_state: int, *,
              permutation_invariant_stop: bool = False, retain_trajectory: bool = True,
              failure_policy: str = "raise", record_diagnostics: bool = True,
              **params: Any) -> dict[str, Any]:
    """Return the exact state used by the legacy LDA-Kmeans fit.

    Default convergence preserves the historical literal-label test. Setting
    ``permutation_invariant_stop=True`` is an explicitly named behavioral
    change. The representation and centers always correspond to the returned
    labels, including at the update cap. No ground-truth labels are accepted.
    """
    started = time.process_time()
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    if "n_components" not in params:
        raise TypeError("n_components is required and is not searched internally")
    n_components = as_positive_int("n_components", params["n_components"])
    options = resolve_params({k:v for k,v in params.items() if k != "n_components"}, _DEFAULTS)
    centered, n_components = _prepare_subspace(features, clusters, n_components)
    max_iter = as_positive_int("max_iter", options["max_iter"])
    sw_reg = float(options["sw_reg"])
    kmeans_params = {"n_init": options["n_init"], "max_iter": options["kmeans_max_iter"],
                     "tol": options["tol"], "init": options["init"],
                     "algorithm": options["algorithm"]}
    span = _data_span(centered)
    basis = _pca_basis(centered, n_components, seed)
    if failure_policy not in {"raise", "record"}:
        raise ValueError("failure_policy must be 'raise' or 'record'")
    history = []; trajectory = []; attempts = successes = 0
    def cluster(projection, update):
        model = KMeans(n_clusters=clusters, random_state=seed, copy_x=True, **kmeans_params).fit(centered @ projection)
        labels = model.labels_.astype(np.int64, copy=False)
        diagnostics = scatter_objective(centered, labels, projection) if record_diagnostics else {}
        row = {"outer_update": update, "inertia": float(model.inertia_),
               "inner_iterations": int(model.n_iter_), "projection_hash": _array_hash(projection),
               "labels_hash": _array_hash(labels), **diagnostics}
        history.append(row)
        if retain_trajectory:
            trajectory.append({"outer_update": update, "projection": projection.copy(),
                               "labels": labels.copy(), "centers": model.cluster_centers_.copy(),
                               "inertia": float(model.inertia_)})
        return model, labels
    model, labels = cluster(basis, 0)
    reason = "MAX_ITER"
    for update in range(1, max_iter + 1):
        if np.unique(labels).size < n_components + 1:
            reason = "INSUFFICIENT_PSEUDO_CLASSES"; break
        attempts += 1
        previous = labels.copy()
        diagnostic = {}; ridge = None
        if record_diagnostics:
            diagnostic_coordinates = centered if span is None else centered @ span
            _, within = _scatter(diagnostic_coordinates, labels)
            diagnostic = _matrix_diagnostics(within)
            floor = 0.0 if features.shape[1] > within.shape[0] else diagnostic["within_min_eigenvalue"]
            ceiling = diagnostic["within_max_eigenvalue"]
            ridge = sw_reg * max(ceiling, 1.0) if sw_reg > 0 and floor <= sw_reg * max(ceiling, 1.0) else 0.0
        try:
            updated_basis = _lda_basis_for_fit(centered, labels, n_components, sw_reg, span)
        except Exception as exc:
            history.append({"outer_update": update, "lda_update": "FAILED", "exception": repr(exc),
                            "ridge": ridge, **diagnostic})
            if failure_policy == "raise":
                raise
            reason = "LDA_UPDATE_FAILED"; break
        basis = updated_basis
        successes += 1
        model, labels = cluster(basis, update)
        history[-1].update(lda_update="SUCCESS",ridge=ridge,**diagnostic)
        history[-1].update(changed_labels=int(np.count_nonzero(labels != previous)),
                           partition_stable=partitions_equal(labels, previous))
        stable = partitions_equal(labels, previous) if permutation_invariant_stop else np.array_equal(labels, previous)
        if stable:
            reason = "PARTITION_STABLE" if permutation_invariant_stop else "LABELS_STABLE"; break
    return {"labels": labels.copy(), "projection": basis.copy(), "projection_used": basis.copy(),
            "training_mean": features.mean(axis=0), "centers": model.cluster_centers_.copy(),
            "representation": centered @ basis, "inertia": float(model.inertia_),
            "history": history, "trajectory": trajectory, "termination_reason": reason,
            "outer_updates": successes, "lda_update_attempts": attempts, "lda_update_successes": successes,
            "inner_kmeans_repetitions": int(options["n_init"]), "outer_n_init": 1,
            "seed": seed, "parameters": {"n_components": n_components, **options},
            "convergence_rule": "partition_equivalence" if permutation_invariant_stop else "literal_labels",
            "returned_state_consistent": True, "native_cross_subspace_selection": "UNAVAILABLE",
            "cpu_seconds": time.process_time() - started, "status": reason,
            "lda_update_failures": attempts - successes}


def trajectory_prefix_matches(short: dict, long: dict, *, atol: float = 0.0) -> bool:
    """Verify actual projections, labels, centers and objectives before prefix reuse."""
    if short["seed"] != long["seed"] or len(short["trajectory"]) > len(long["trajectory"]):
        return False
    for a, b in zip(short["trajectory"], long["trajectory"]):
        if a["outer_update"] != b["outer_update"] or a["inertia"] != b["inertia"]:
            return False
        for key in ["projection", "labels", "centers"]:
            if not np.allclose(a[key], b[key], rtol=0.0, atol=atol):
                return False
    return True


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
    return fit_state(X, n_clusters, random_state, retain_trajectory=False,
                     record_diagnostics=False, **params)["labels"]
