"""Vanilla k-means++ with one local candidate per center.

This is not scikit-learn's greedy ``KMeans(init='k-means++')``.
The campaign labels it ``VANILLA_KMEANSPP`` and keeps it out of the
P3/P4 table.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import kmeans_plusplus


def vanilla_kmeanspp_centers(
    features: np.ndarray,
    n_clusters: int,
    seed: int,
) -> np.ndarray:
    """Return centers from ``kmeans_plusplus(..., n_local_trials=1)``."""
    centers, _indices = kmeans_plusplus(
        np.asarray(features, dtype=np.float64),
        n_clusters,
        random_state=int(seed),
        n_local_trials=1,
    )
    centers = np.asarray(centers, dtype=np.float64)
    if centers.shape != (int(n_clusters), features.shape[1]):
        raise RuntimeError(f"vanilla k-means++ returned shape {centers.shape}")
    return centers


__all__ = ["vanilla_kmeanspp_centers"]
