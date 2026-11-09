"""One Lloyd run per seed. ``n_init`` is fixed at 1."""

from __future__ import annotations

import hashlib
import time
import warnings
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning

from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from experiments.v2_kmeans_protocol.vanilla_kmeanspp import vanilla_kmeanspp_centers

KMEANS_MAX_ITER = 300
KMEANS_TOL = 1e-4
KMEANS_ALGORITHM = "lloyd"
KMEANS_N_INIT = 1

RANDOM = "RANDOM"
GREEDY = "SKLEARN_GREEDY_KMEANSPP"
VANILLA = "VANILLA_KMEANSPP"

_INIT_ARGUMENT = {
    RANDOM: "random",
    GREEDY: "k-means++",
    VANILLA: "vanilla_centers",
}


def sha256_array(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.shape).encode())
    digest.update(str(contiguous.dtype).encode())
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def fit_lloyd(
    features: np.ndarray,
    n_clusters: int,
    seed: int,
    initialization_label: str,
) -> dict[str, Any]:
    """Fit one Lloyd run.

    The ground-truth vector is intentionally absent from this function.
    """
    if initialization_label not in _INIT_ARGUMENT:
        raise ValueError(f"unknown initialization {initialization_label}")
    if int(KMEANS_N_INIT) != 1:
        raise RuntimeError("n_init must stay 1")
    matrix = np.asarray(features, dtype=np.float64)
    if initialization_label == VANILLA:
        init: str | np.ndarray = vanilla_kmeanspp_centers(matrix, n_clusters, seed)
    else:
        init = _INIT_ARGUMENT[initialization_label]
    kwargs = {
        "n_clusters": int(n_clusters),
        "init": init,
        "n_init": KMEANS_N_INIT,
        "algorithm": KMEANS_ALGORITHM,
        "max_iter": KMEANS_MAX_ITER,
        "tol": KMEANS_TOL,
        "random_state": int(seed),
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model = KMeans(**kwargs)
        labels = np.asarray(model.fit_predict(matrix), dtype=np.int64)
    warning_text = " | ".join(str(item.message) for item in caught)
    n_iter = int(np.max(model.n_iter_))
    return {
        "labels": labels,
        "centers": np.asarray(model.cluster_centers_, dtype=np.float64),
        "inertia": float(model.inertia_),
        "kmeans_n_iter": n_iter,
        "kmeans_converged": bool(n_iter < KMEANS_MAX_ITER and not warning_text),
        "kmeans_warning": warning_text,
        "initialization": _INIT_ARGUMENT[initialization_label],
        "n_init": KMEANS_N_INIT,
    }


def trial_record(
    *,
    fit: dict[str, Any],
    y_true: np.ndarray,
    wall_seconds: float,
    identity: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray]:
    """Attach ACC/NMI after Lloyd returns. Selection still uses inertia only."""
    scores = evaluate_partition(y_true, fit["labels"])
    row = dict(identity)
    row.update(
        {
            "initialization": fit["initialization"],
            "n_init": fit["n_init"],
            "algorithm": KMEANS_ALGORITHM,
            "max_iter": KMEANS_MAX_ITER,
            "tol": KMEANS_TOL,
            "inertia": fit["inertia"],
            "kmeans_n_iter": fit["kmeans_n_iter"],
            "kmeans_converged": fit["kmeans_converged"],
            "kmeans_warning": fit["kmeans_warning"],
            "acc": scores["acc"],
            "nmi": scores["nmi"],
            "n_unique_predicted": scores["n_unique_predicted"],
            "wall_seconds": wall_seconds,
            "centers_sha256": sha256_array(fit["centers"]),
            "labels_sha256": sha256_array(fit["labels"]),
            "experiment_status": "COMPLETED",
        }
    )
    return row, fit["labels"]


def run_seed(
    features: np.ndarray,
    y_true: np.ndarray,
    n_clusters: int,
    seed: int,
    initialization_label: str,
    identity: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    started = time.perf_counter()
    fit = fit_lloyd(features, n_clusters, seed, initialization_label)
    elapsed = time.perf_counter() - started
    row, labels = trial_record(
        fit=fit,
        y_true=y_true,
        wall_seconds=elapsed,
        identity={**identity, "seed": int(seed)},
    )
    return row, labels, np.asarray(fit["centers"], dtype=np.float64)


__all__ = [
    "GREEDY",
    "KMEANS_ALGORITHM",
    "KMEANS_MAX_ITER",
    "KMEANS_N_INIT",
    "KMEANS_TOL",
    "RANDOM",
    "VANILLA",
    "fit_lloyd",
    "run_seed",
    "sha256_array",
    "trial_record",
]
