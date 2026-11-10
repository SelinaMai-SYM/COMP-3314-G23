"""Random Lloyd, k-means++, inertia-best, and aligned majority consensus.

The representation is not refit. Accuracy does not choose the initializer.
"""

from __future__ import annotations

import numpy as np

from method_extension.common.clustering import (
    consensus_labels,
    inertia_best_labels,
    partition_trials,
)


def cluster_fixed_representation(
    features: np.ndarray,
    n_clusters: int,
    seeds: list[int],
) -> dict:
    """Return four label sets for the same rows. ``features`` is F or G."""
    random_trials = partition_trials(features, n_clusters, seeds, init="random")
    plus_trials = partition_trials(features, n_clusters, seeds, init="k-means++")
    best_labels, best_inertia, best_seed = inertia_best_labels(features, n_clusters, seeds)
    agreed = consensus_labels(features, n_clusters, seeds)
    return {
        "random": random_trials,
        "kmeanspp": plus_trials,
        "inertia_best_labels": best_labels,
        "inertia_best_inertia": best_inertia,
        "inertia_best_seed": best_seed,
        "consensus_labels": agreed,
        "selection_rule": "min_kmeans_inertia_then_smallest_seed; consensus aligned to that run",
        "uses_accuracy": False,
    }
