"""Observed minimal port of ClustPy LDAKmeans at 4ac9d00685efc7432800684f5bfac0f01af59172.

The original core and helper source and BSD-3-Clause notice are in vendor/clustpy.
Algorithmic failures, the mutable inner RNG, and the source's possibly newer
returned rotation are retained. A scoped NumPy global seed makes the source's
unseeded PCA reproducible; its previous global state is restored on return.
This determinism modification is disclosed in each returned state.
"""
from __future__ import annotations
import time
import numpy as np
from scipy.linalg import eigh
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import normalized_mutual_info_score
from sklearn.utils import check_random_state
from ..common import check_problem, as_positive_int
from .lda_kmeans import _array_hash, _matrix_diagnostics, partitions_equal

COMMIT = "4ac9d00685efc7432800684f5bfac0f01af59172"
BLOB = "e2d952694a20ccabe0d38bd54ba9e5b5c5d4b846"


def _source_scatter(X, K, labels):
    # Verbatim calculation from the pinned _update_centers_and_scatter_matrix.
    centers = np.array([np.mean(X[labels == cluster_id],axis=0) for cluster_id in range(K)])
    centered = X[labels >= 0]-centers[labels[labels >= 0]]
    return centers,centered.T @ centered


def fit_reference_state(X: np.ndarray,n_clusters: int,random_state: int,*,
                        n_components: int | None = None,max_iter: int = 300,
                        kmeans_repetitions: int = 10,retain_trajectory: bool = True) -> dict:
    """Observe the pinned reference with outer n_init=1 and no numerical repair.

    ``projection_used`` matches labels/centers; ``projection_returned`` preserves
    the actual reference return. The reference fits X@R, not centered X@R.
    A no-success fit is explicitly labelled DEGENERATED_TO_PCA_KMEANS.
    """
    started = time.process_time()
    X,K,seed = check_problem(X,n_clusters,random_state)
    max_iter = as_positive_int("max_iter",max_iter)
    repetitions = as_positive_int("kmeans_repetitions",kmeans_repetitions)
    r = max(1,K-1 if n_components is None else as_positive_int("n_components",n_components))
    # Match LDAKmeans.fit's one outer seed draw rather than calling the core with
    # the user's external seed directly.
    local_seed = int(check_random_state(seed).choice(10000,1,replace=False)[0])
    rng = check_random_state(local_seed)
    saved_global = np.random.get_state()
    np.random.seed(seed)
    try:
        if r >= X.shape[1]:
            R = np.eye(X.shape[1])
        else:
            R = PCA(r).fit(X).components_.T
    finally:
        np.random.set_state(saved_global)
    mean = X.mean(axis=0); centered = X-mean
    St = centered.T @ centered / (len(X)-1)
    previous = None; history=[];trajectory=[];attempts=successes=0;reason="MAX_ITER"
    for iteration in range(1 if r >= X.shape[1] else max_iter):
        used = R.copy()
        model=KMeans(K,n_init=repetitions,random_state=rng).fit(X @ used)
        labels=model.labels_.copy()
        row={"iteration":iteration+1,"inertia":float(model.inertia_),"inner_iterations":int(model.n_iter_),
             "projection_hash":_array_hash(used),"labels_hash":_array_hash(labels),
             "changed_labels":None if previous is None else int(np.count_nonzero(labels!=previous)),
             "partition_stable_exact":False if previous is None else partitions_equal(previous,labels),
             "regularization":0.0}
        history.append(row)
        if retain_trajectory:
            trajectory.append({"iteration":iteration+1,"projection":used.copy(),"labels":labels.copy(),
                               "centers":model.cluster_centers_.copy(),"inertia":float(model.inertia_),
                               "rng_state_after_kmeans":rng.get_state()})
        if r >= X.shape[1]:
            reason="FULL_DIMENSION_KMEANS";break
        # Preserve the source's default arithmetic-NMI equality stopping rule.
        if previous is not None and normalized_mutual_info_score(labels,previous)==1:
            reason="SOURCE_NMI_STABLE";break
        previous=labels.copy()
        _,scatter=_source_scatter(X,K,labels)
        Sw=scatter/(len(X)-1);Sb=St-Sw
        row.update(_matrix_diagnostics(Sw))
        row.update(trace_between=float(np.trace(used.T @ Sb @ used)),
                   trace_within=float(np.trace(used.T @ Sw @ used)))
        attempts+=1
        try:
            _,vectors=eigh(Sb,Sw)
            R=vectors[:,::-1][:,:r]
            successes+=1;row["lda_update"]="SUCCESS"
        except BaseException as exc:
            # The source has a bare except. This port makes that failure visible
            # while retaining the unchanged projection and continuation behavior.
            row["lda_update"]="FAILED";row["exception"]=repr(exc)
    consistent=bool(np.array_equal(used,R))
    status="DEGENERATED_TO_PCA_KMEANS" if successes==0 and r<X.shape[1] else reason
    return {"method":"ClustPy LDAKmeans pinned reference (observed)","source_commit":COMMIT,"source_blob":BLOB,
            "labels":labels,"projection_used":used,"projection":used,"projection_returned":R,
            "training_mean":np.zeros(X.shape[1]),"scatter_mean":mean,"centers":model.cluster_centers_.copy(),
            "representation":X @ used,"source_returned_representation":X @ R,"inertia":float(model.inertia_),
            "history":history,"trajectory":trajectory,"termination_reason":reason,"status":status,
            "lda_update_attempts":attempts,"lda_update_successes":successes,"lda_update_failures":attempts-successes,
            "outer_iterations":len(history),"outer_n_init":1,"inner_kmeans_repetitions":repetitions,
            "seed":seed,"source_local_seed":local_seed,"returned_state_consistent":consistent,
            "determinism_modifications":["Scoped global NumPy seed for the source PCA; restored after fitting"],
            "native_cross_subspace_selection":"UNAVAILABLE", "cpu_seconds":time.process_time()-started}
