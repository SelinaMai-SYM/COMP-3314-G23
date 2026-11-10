"""Unsupervised graph reweighting. None of these functions read labels."""

from __future__ import annotations

import hashlib

import numpy as np
from scipy import sparse

from SSC_method.graph_construction import knn_neighbor_squared_distances

_CACHE: dict[tuple, sparse.csr_matrix] = {}


def clear_graph_cache() -> None:
    _CACHE.clear()


def _sha(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def symmetrize(affinity: sparse.spmatrix | np.ndarray) -> sparse.csr_matrix:
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    weights = ((weights + weights.T) * 0.5).tocsr()
    weights.setdiag(0.0)
    weights.eliminate_zeros()
    return weights


def recurrence_probability(
    embedding: np.ndarray,
    k: int = 5,
    n_perturbations: int = 10,
    noise_rel: float = 0.02,
    seed: int = 20260311,
) -> sparse.csr_matrix:
    """Fraction of T perturbed union-kNN graphs that contain each undirected edge.

    Noise is isotropic Gaussian on F. Its scale is ``noise_rel`` times the RMS
    of F. The seed is fixed. Labels are not an argument.
    """
    embedding = np.asarray(embedding, dtype=np.float64)
    key = (
        "p",
        _sha(embedding),
        int(k),
        int(n_perturbations),
        float(noise_rel),
        int(seed),
    )
    cached = _CACHE.get(key)
    if cached is not None:
        return cached.copy()
    n_samples, n_components = embedding.shape
    rms = float(np.linalg.norm(embedding) / np.sqrt(n_samples * n_components))
    sigma = float(noise_rel) * rms
    rng = np.random.default_rng(int(seed))
    accumulator = sparse.csr_matrix((n_samples, n_samples), dtype=np.float64)
    for _ in range(int(n_perturbations)):
        perturbed = embedding if sigma == 0.0 else embedding + sigma * rng.normal(size=embedding.shape)
        _distances, neighbors = knn_neighbor_squared_distances(perturbed, k)
        rows = np.repeat(np.arange(n_samples, dtype=np.int64), k)
        cols = np.asarray(neighbors, dtype=np.int64).ravel()
        data = np.ones(rows.shape[0], dtype=np.float64)
        directed = sparse.csr_matrix((data, (rows, cols)), shape=(n_samples, n_samples))
        union = directed.maximum(directed.T).tocsr()
        union.data = np.ones(union.data.shape[0], dtype=np.float64)
        union.setdiag(0.0)
        union.eliminate_zeros()
        accumulator = accumulator + union
    if accumulator.nnz:
        accumulator.data = accumulator.data / float(n_perturbations)
    accumulator.setdiag(0.0)
    accumulator.eliminate_zeros()
    _CACHE[key] = accumulator.copy()
    return accumulator


def apply_probability(
    affinity: sparse.spmatrix,
    probability: sparse.spmatrix,
    beta: float = 1.0,
) -> sparse.csr_matrix:
    """Elementwise product W ⊙ p^beta. Missing probability entries count as zero."""
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    chance = sparse.csr_matrix(probability, dtype=np.float64)
    if float(beta) != 1.0:
        chance = chance.copy()
        chance.data = np.power(chance.data, float(beta))
    product = weights.multiply(chance)
    return symmetrize(product)


def local_reliability_alpha(
    embedding: np.ndarray,
    k: int = 5,
    alpha_min: float = 0.5,
    alpha_max: float = 2.0,
) -> np.ndarray:
    """Map the mutual-neighbor rate on F into [alpha_min, alpha_max].

    alpha_i = alpha_min + (alpha_max - alpha_min) * (mutual neighbors of i) / k.
    A point with no mutual neighbor gets the floor. A fully mutual neighborhood
    gets the cap. This does not read labels.
    """
    embedding = np.asarray(embedding, dtype=np.float64)
    _distances, neighbors = knn_neighbor_squared_distances(embedding, k)
    n_samples = embedding.shape[0]
    neighbor_sets = [set(int(j) for j in neighbors[i]) for i in range(n_samples)]
    alpha = np.empty(n_samples, dtype=np.float64)
    span = float(alpha_max) - float(alpha_min)
    for index in range(n_samples):
        mutual = sum(1 for other in neighbor_sets[index] if index in neighbor_sets[other])
        alpha[index] = float(alpha_min) + span * (mutual / float(k))
    return np.clip(alpha, float(alpha_min), float(alpha_max))


def degree_normalize(affinity: sparse.spmatrix, eps: float = 1e-12) -> sparse.csr_matrix:
    """W_ij / sqrt((d_i + eps)(d_j + eps)). Not a single global scale on irregular graphs."""
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    degrees = np.asarray(weights.sum(axis=1), dtype=np.float64).ravel()
    scale = 1.0 / np.sqrt(degrees + float(eps))
    normalized = sparse.diags(scale) @ weights @ sparse.diags(scale)
    return symmetrize(normalized)


def total_edge_normalize(affinity: sparse.spmatrix) -> tuple[sparse.csr_matrix, dict]:
    """Divide by the sum of stored weights.

    For a nonnegative W this is exactly a global scale, hence a rescaling of
    gamma, not a new shrinkage mechanism.
    """
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    total = float(weights.sum())
    if total <= 0.0:
        scale = 1.0
        scaled = weights
    else:
        scale = 1.0 / total
        scaled = symmetrize(weights * scale)
    info = {
        "equivalent_to_global_gamma_scale": True,
        "mechanism": "control_not_a_new_mechanism",
        "weight_sum": total,
        "applied_scale": scale,
    }
    return scaled, info


def fuse_affinities(
    affinity_f: sparse.spmatrix,
    affinity_x: sparse.spmatrix,
    mix: float = 0.5,
) -> sparse.csr_matrix:
    """mix * W_F + (1 - mix) * W_X. ``mix`` is fixed before any accuracy is seen."""
    fused = float(mix) * sparse.csr_matrix(affinity_f) + (1.0 - float(mix)) * sparse.csr_matrix(affinity_x)
    return symmetrize(fused)


def bilateral_support(
    affinity_f: sparse.spmatrix,
    affinity_x: sparse.spmatrix,
) -> sparse.csr_matrix:
    """Keep W_F only where W_X is also nonzero. Pixel-space support is not assumed reliable."""
    mask = sparse.csr_matrix(affinity_x, dtype=np.float64).copy()
    if mask.nnz:
        mask.data = np.ones(mask.data.shape[0], dtype=np.float64)
    kept = sparse.csr_matrix(affinity_f, dtype=np.float64).multiply(mask)
    return symmetrize(kept)
