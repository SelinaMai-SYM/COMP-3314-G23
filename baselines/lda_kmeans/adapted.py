"""Explicit PCA-preconditioned ridge LDA-Kmeans adaptation; not historical LDA-SC."""
from __future__ import annotations

import time
from typing import Any
import numpy as np
from scipy.linalg import eigh
from sklearn.cluster import KMeans

from ..common import check_problem, as_positive_int
from .lda_kmeans import _scatter, partitions_equal, _array_hash, _matrix_diagnostics


def prepare_pca(X: np.ndarray, n_clusters: int) -> dict[str, Any]:
    """Prepare deterministic full-SVD coordinates, independent of fitting seeds.

    Rank uses the usual float64 tolerance ``eps * max(n,p) * sigma_max``.
    Covariances in this adapted pipeline are divided by n-1, matching the
    pinned reference's scatter convention. The ridge follows that convention.
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2 or len(X) < 2 or not np.isfinite(X).all():
        raise ValueError("X must be a finite matrix with at least two rows")
    K = as_positive_int("n_clusters", n_clusters)
    mean = X.mean(axis=0)
    centered = X - mean
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    tolerance = float(np.finfo(np.float64).eps * max(centered.shape) * singular[0]) if len(singular) else 0.0
    rank = int(np.sum(singular > tolerance))
    p0 = min(100, X.shape[1], len(X) - K, rank)
    if p0 < 1 or not len(singular) or singular[0] <= 0:
        return {"status": "DEGENERATE_INPUT", "p0": p0, "numerical_rank": rank,
                "rank_tolerance": tolerance, "training_mean": mean,
                "input_hash": _array_hash(X), "K": K}
    P = vt[:p0].T.copy()
    # Resolve sign ambiguity by a fixed feature-index rule.
    for j in range(p0):
        if P[np.argmax(np.abs(P[:,j])),j] < 0:
            P[:,j] *= -1
    Z = centered @ P
    St = Z.T @ Z / (len(Z) - 1)
    eta = float(1e-6 * np.trace(St) / p0)
    return {"status": "PREPARED", "training_mean": mean, "pca_projection": P,
            "coordinates": Z, "p0": p0, "r": min(K - 1,p0), "K": K,
            "numerical_rank": rank, "rank_tolerance": tolerance,
            "singular_values": singular, "St": St, "eta": eta,
            "input_hash": _array_hash(X), "covariance_divisor": len(Z) - 1}


def fit_adapted_state(X: np.ndarray, n_clusters: int, random_state: int, *,
                      max_iter: int = 300, prepared: dict | None = None,
                      retain_trajectory: bool = True) -> dict[str, Any]:
    """Fit the fixed adapted pipeline without receiving ground-truth labels.

    The mutable RandomState and ten greedy K-means++ starts follow the pinned
    reference's inner-clustering convention. Final coordinates use the last
    projection actually clustered, even if another LDA update was possible.
    ``max_iter`` is exposed for small validation cases; campaign value is 300.
    """
    started = time.process_time()
    features, K, seed = check_problem(X, n_clusters, random_state)
    max_iter = as_positive_int("max_iter", max_iter)
    prepared = prepare_pca(features,K) if prepared is None else prepared
    if prepared["input_hash"] != _array_hash(features) or prepared["K"] != K:
        raise ValueError("prepared PCA belongs to a different input or cluster count")
    if prepared["status"] != "PREPARED":
        return {**prepared, "termination_reason": "DEGENERATE_INPUT", "cpu_seconds": time.process_time()-started}
    Z = prepared["coordinates"]; r = prepared["r"]; p0 = prepared["p0"]
    if r < 1:
        return {**prepared,"termination_reason":"DEGENERATE_INPUT","cpu_seconds":time.process_time()-started}
    R = np.eye(p0,r); rng = np.random.RandomState(seed)
    previous = None; history = []; trajectory = []; attempts = successes = 0
    reason = "MAX_ITER"
    for iteration in range(max_iter):
        used = R.copy()
        embedded = Z @ used
        model = KMeans(n_clusters=K,n_init=10,init="k-means++",algorithm="lloyd",
                       max_iter=300,tol=1e-4,random_state=rng,copy_x=True).fit(embedded)
        labels = model.labels_.astype(np.int64,copy=False)
        between, within = _scatter(Z,labels)
        between /= len(Z)-1; within /= len(Z)-1
        row = {"iteration":iteration+1,"inertia":float(model.inertia_),
               "inner_iterations":int(model.n_iter_),"projection_hash":_array_hash(used),
               "labels_hash":_array_hash(labels),"eta":prepared["eta"],
               "trace_between":float(np.trace(used.T @ between @ used)),
               "trace_within":float(np.trace(used.T @ within @ used)),
               "changed_labels":None if previous is None else int(np.count_nonzero(labels!=previous)),
               "partition_stable":False if previous is None else partitions_equal(previous,labels),
               **_matrix_diagnostics(within)}
        history.append(row)
        if retain_trajectory:
            trajectory.append({"iteration":iteration+1,"projection":used.copy(),"labels":labels.copy(),
                               "centers":model.cluster_centers_.copy(),"inertia":float(model.inertia_),
                               "rng_state_after_kmeans":rng.get_state()})
        if previous is not None and partitions_equal(previous,labels):
            reason = "PARTITION_STABLE"; break
        if iteration + 1 == max_iter:
            break
        attempts += 1
        try:
            _, eigenvectors = eigh(between,within+prepared["eta"]*np.eye(p0))
            R = eigenvectors[:,::-1][:,:r]
            successes += 1
            row["lda_update"] = "SUCCESS"
        except Exception as exc:
            row["lda_update"] = "FAILED"; row["exception"] = repr(exc)
            reason = "LDA_UPDATE_FAILED"; break
        previous = labels.copy()
    projection = prepared["pca_projection"] @ used
    return {"method":"PCA-preconditioned ridge LDA-Kmeans -> SC (adapted)",
            "labels":labels.copy(),"centers":model.cluster_centers_.copy(),
            "training_mean":prepared["training_mean"].copy(),
            "pca_projection":prepared["pca_projection"].copy(),
            "lda_projection":used,"projection":projection,"projection_used":projection,
            "representation":embedded,"pca_coordinates":Z,
            "inertia":float(model.inertia_),"history":history,"trajectory":trajectory,
            "termination_reason":reason,"outer_iterations":len(history),
            "lda_update_attempts":attempts,"lda_update_successes":successes,
            "p0":p0,"r":r,"eta":prepared["eta"],"numerical_rank":prepared["numerical_rank"],
            "rank_tolerance":prepared["rank_tolerance"],"covariance_divisor":len(Z)-1,
            "inner_kmeans_repetitions":10,"outer_n_init":1,"seed":seed,
            "returned_state_consistent":True,"row_normalization":False,
            "native_cross_subspace_selection":"UNAVAILABLE", "cpu_seconds":time.process_time()-started}
