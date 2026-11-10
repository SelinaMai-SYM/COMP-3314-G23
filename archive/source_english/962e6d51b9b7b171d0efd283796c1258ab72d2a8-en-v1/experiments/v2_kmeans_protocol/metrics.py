"""Hungarian ACC and geometric-mean NMI.

Both scores are computed from the same predicted labeling.
The implementations live in ``benchmarks.metrics`` and follow
Chang et al. (AAAI 2015), Equations (19)–(21).
"""

from __future__ import annotations

import numpy as np

from benchmarks.metrics.accuracy import clustering_accuracy
from benchmarks.metrics.nmi import normalized_mutual_information


def evaluate_partition(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Return ACC and NMI for one partition.

    ``y_true`` is read only here. Callers must not pass it into K-means
    or into inertia selection.
    """
    truth = np.asarray(y_true).reshape(-1)
    pred = np.asarray(y_pred).reshape(-1)
    acc = float(clustering_accuracy(truth, pred))
    nmi = float(normalized_mutual_information(truth, pred))
    if not (0.0 <= acc <= 1.0 and 0.0 <= nmi <= 1.0):
        raise RuntimeError(f"metric out of range: ACC={acc} NMI={nmi}")
    return {
        "acc": acc,
        "nmi": nmi,
        "n_unique_predicted": int(np.unique(pred).size),
    }


def mean_and_sample_sd(values: list[float] | np.ndarray) -> tuple[float | None, float | None]:
    """Sample mean and sample standard deviation (ddof=1).

    A single observation has no sample SD. The missing SD is ``None``,
    which writers render as an empty cell rather than 0.
    """
    array = np.asarray(list(values), dtype=np.float64)
    if array.size == 0:
        return None, None
    if not np.isfinite(array).all():
        raise ValueError("metric summary received a non-finite value")
    mean = float(array.mean())
    if array.size < 2:
        return mean, None
    return mean, float(array.std(ddof=1))


__all__ = [
    "clustering_accuracy",
    "evaluate_partition",
    "mean_and_sample_sd",
    "normalized_mutual_information",
]
