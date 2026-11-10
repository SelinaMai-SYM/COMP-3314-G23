"""K-means protocols. Ground-truth labels are not an input to these choices."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans


def kmeans_once(
    features: np.ndarray,
    n_clusters: int,
    seed: int,
    init: str = "random",
) -> tuple[np.ndarray, float]:
    model = KMeans(
        n_clusters=int(n_clusters),
        init=str(init),
        n_init=1,
        random_state=int(seed),
        algorithm="lloyd",
    )
    labels = np.asarray(model.fit_predict(features), dtype=np.int64)
    return labels, float(model.inertia_)


def align_labels(reference: np.ndarray, other: np.ndarray) -> np.ndarray:
    """Permute ``other`` to maximize overlap with ``reference``."""
    reference = np.asarray(reference, dtype=np.int64)
    other = np.asarray(other, dtype=np.int64)
    ref_ids, ref_index = np.unique(reference, return_inverse=True)
    other_ids, other_index = np.unique(other, return_inverse=True)
    table = np.zeros((ref_ids.size, other_ids.size), dtype=np.float64)
    np.add.at(table, (ref_index, other_index), 1.0)
    rows, cols = linear_sum_assignment(-table)
    mapping = {int(other_ids[col]): int(ref_ids[row]) for row, col in zip(rows, cols)}
    used = set(mapping.values())
    next_id = int(max(ref_ids.max(), other_ids.max()) + 1) if ref_ids.size else 0
    for label in other_ids:
        label = int(label)
        if label not in mapping:
            while next_id in used:
                next_id += 1
            mapping[label] = next_id
            used.add(next_id)
            next_id += 1
    return np.asarray([mapping[int(label)] for label in other], dtype=np.int64)


def partition_trials(
    features: np.ndarray,
    n_clusters: int,
    seeds: list[int],
    init: str,
) -> list[tuple[np.ndarray, float, int]]:
    trials = []
    for seed in seeds:
        labels, inertia = kmeans_once(features, n_clusters, seed, init=init)
        trials.append((labels, inertia, int(seed)))
    return trials


def inertia_best_labels(
    features: np.ndarray,
    n_clusters: int,
    seeds: list[int],
) -> tuple[np.ndarray, float, int]:
    """One assignment: the random Lloyd run with the smallest inertia.

    Inertia is the K-means objective. Accuracy is not the selection rule.
    """
    trials = partition_trials(features, n_clusters, seeds, init="random")
    labels, inertia, seed = min(trials, key=lambda item: (item[1], item[2]))
    return labels, inertia, seed


def consensus_labels(
    features: np.ndarray,
    n_clusters: int,
    seeds: list[int],
) -> np.ndarray:
    """Majority vote after aligning every random run to the inertia-best run.

    Ties go to the smallest label id. Labels are not used.
    """
    trials = partition_trials(features, n_clusters, seeds, init="random")
    _labels, _inertia, ref_pos = min(
        ((labels, inertia, index) for index, (labels, inertia, _seed) in enumerate(trials)),
        key=lambda item: (item[1], item[2]),
    )
    reference = trials[ref_pos][0]
    aligned = [align_labels(reference, labels) for labels, _inertia, _seed in trials]
    stacked = np.vstack(aligned)
    largest = int(stacked.max()) + 1
    votes = np.zeros((features.shape[0], largest), dtype=np.int16)
    for labels in aligned:
        votes[np.arange(features.shape[0]), labels] += 1
    return np.argmax(votes, axis=1).astype(np.int64)


def disagreement_fraction(left: np.ndarray, right: np.ndarray) -> float:
    aligned = align_labels(left, right)
    return float(np.mean(np.asarray(left) != aligned))


def bootstrap_mean_interval(
    values: np.ndarray,
    n_boot: int = 2000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Percentile interval for the mean of a fixed list of paired differences.

    This interval is K-means noise on one representation. It is not a
    confidence interval for a new draw of the dataset.
    """
    sample = np.asarray(values, dtype=np.float64)
    if sample.size == 0:
        raise ValueError("bootstrap sample is empty")
    rng = np.random.default_rng(int(seed))
    draws = rng.integers(0, sample.size, size=(int(n_boot), sample.size))
    means = sample[draws].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(sample.mean()), float(low), float(high)
