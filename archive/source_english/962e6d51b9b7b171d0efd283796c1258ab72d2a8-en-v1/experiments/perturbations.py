"""Explicit-magnitude perturbations for extension stress tests."""

from __future__ import annotations

import numpy as np
from scipy import sparse


def apply_perturbation(
    X: np.ndarray,
    spec: dict | None,
) -> tuple[np.ndarray, dict]:
    """Return a perturbed copy of X. Graph perturbations are handled later."""
    features = np.asarray(X, dtype=np.float64)
    if not spec:
        return features, {"type": None}
    kind = spec["type"]
    seed = int(spec.get("seed", 0))
    rng = np.random.default_rng(seed)
    if kind == "gaussian_noise":
        frac = float(spec["level"])
        scale = float(np.std(features)) * frac
        noise = rng.normal(loc=0.0, scale=scale, size=features.shape)
        out = features + noise
        info = {
            "type": kind,
            "sigma_frac_of_feature_std": frac,
            "feature_std": float(np.std(features)),
            "noise_std": scale,
            "seed": seed,
        }
        return out, info
    if kind == "feature_corruption":
        frac = float(spec["level"])
        n_features = features.shape[1]
        n_corrupt = int(round(frac * n_features))
        n_corrupt = min(max(n_corrupt, 0), n_features)
        columns = rng.choice(n_features, size=n_corrupt, replace=False)
        out = np.array(features, copy=True)
        if n_corrupt:
            out[:, columns] = rng.normal(loc=0.0, scale=1.0, size=(features.shape[0], n_corrupt))
        info = {
            "type": kind,
            "fraction": frac,
            "n_features_corrupted": int(n_corrupt),
            "columns": columns.tolist(),
            "replacement": "N(0,1)",
            "seed": seed,
        }
        return out, info
    if kind == "outlier_contamination":
        frac = float(spec["level"])
        n_samples, n_features = features.shape
        n_out = int(round(frac * n_samples))
        n_out = min(max(n_out, 0), n_samples)
        rows = rng.choice(n_samples, size=n_out, replace=False)
        out = np.array(features, copy=True)
        if n_out:
            out[rows] = rng.normal(loc=0.0, scale=10.0, size=(n_out, n_features))
        info = {
            "type": kind,
            "fraction": frac,
            "n_samples_replaced": int(n_out),
            "rows": rows.tolist(),
            "replacement": "N(0,10) isotropic in feature space",
            "seed": seed,
        }
        return out, info
    if kind == "graph_drop":
        return features, {"type": kind, "level": float(spec["level"]), "seed": seed}
    raise ValueError(f"unknown perturbation type {kind!r}")


def drop_affinity_edges(affinity: sparse.spmatrix, fraction: float, seed: int) -> sparse.csr_matrix:
    """Drop a random fraction of undirected edges. Remaining weights unchanged."""
    matrix = sparse.csr_matrix(affinity, dtype=np.float64)
    coo = sparse.triu(matrix, k=1).tocoo()
    n_edges = int(coo.nnz)
    n_drop = int(round(float(fraction) * n_edges))
    n_drop = min(max(n_drop, 0), n_edges)
    if n_drop == 0:
        return matrix
    rng = np.random.default_rng(seed)
    drop = set(rng.choice(n_edges, size=n_drop, replace=False).tolist())
    keep = [i for i in range(n_edges) if i not in drop]
    kept = sparse.csr_matrix(
        (coo.data[keep], (coo.row[keep], coo.col[keep])),
        shape=matrix.shape,
    )
    kept = kept + kept.T
    kept.setdiag(0.0)
    kept.eliminate_zeros()
    return kept
