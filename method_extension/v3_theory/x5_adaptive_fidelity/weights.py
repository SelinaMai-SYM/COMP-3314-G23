"""Fixed positive fidelity weights. alpha = 0 matches unweighted SSC."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from method_extension.v3_theory.common.objectives import as_csr


def neighbor_median_distances(embedding: np.ndarray, affinity: sparse.spmatrix) -> np.ndarray:
    features = np.asarray(embedding, dtype=np.float64)
    matrix = as_csr(affinity)
    distances = np.zeros(features.shape[0], dtype=np.float64)
    for index in range(features.shape[0]):
        neighbors = matrix.indices[matrix.indptr[index] : matrix.indptr[index + 1]]
        neighbors = neighbors[matrix.data[matrix.indptr[index] : matrix.indptr[index + 1]] > 0.0]
        neighbors = neighbors[neighbors != index]
        if neighbors.size == 0:
            distances[index] = 0.0
            continue
        distances[index] = float(np.median(np.linalg.norm(features[index] - features[neighbors], axis=1)))
    return distances


def adaptive_fidelity(
    embedding: np.ndarray,
    affinity: sparse.spmatrix,
    alpha: float,
    *,
    epsilon: float = 0.05,
    lower: float = 0.25,
    upper: float = 4.0,
) -> np.ndarray:
    """a_i = clip(1 / (epsilon + u_tilde)^alpha, 0.25, 4), then mean a_i = 1.

    u_i is the median neighbor distance in the fixed graph. alpha = 0 makes
    every unclipped weight 1, so the rescaled vector is exactly 1.
    """
    distances = neighbor_median_distances(embedding, affinity)
    scale = max(float(np.median(distances)), float(epsilon))
    normalized = distances / scale
    raw = 1.0 / np.power(float(epsilon) + normalized, float(alpha))
    clipped = np.clip(raw, lower, upper)
    return clipped / float(np.mean(clipped))


def inverse_fidelity(
    embedding: np.ndarray,
    affinity: sparse.spmatrix,
    alpha: float,
    *,
    epsilon: float = 0.05,
    lower: float = 0.25,
    upper: float = 4.0,
) -> np.ndarray:
    """Control: a proportional to (epsilon + u_tilde)^alpha, same clip, mean 1."""
    distances = neighbor_median_distances(embedding, affinity)
    scale = max(float(np.median(distances)), float(epsilon))
    normalized = distances / scale
    raw = np.power(float(epsilon) + normalized, float(alpha))
    clipped = np.clip(raw, lower, upper)
    return clipped / float(np.mean(clipped))


def permuted_fidelity(fidelity: np.ndarray, seed: int) -> np.ndarray:
    permuted = np.array(fidelity, dtype=np.float64, copy=True)
    np.random.default_rng(seed).shuffle(permuted)
    return permuted


def uniform_fidelity(n_samples: int, value: float) -> np.ndarray:
    if value <= 0.0:
        raise ValueError("uniform fidelity must be positive")
    return np.full(int(n_samples), float(value), dtype=np.float64)
