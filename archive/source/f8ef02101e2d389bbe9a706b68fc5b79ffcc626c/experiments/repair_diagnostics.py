"""Cheap diagnostics for repair-round one-factor SSC runs.

These helpers do not change solver defaults. They record graph overlap,
connected components, and history increments used by the repair runner.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

from benchmarks.metrics import clustering_accuracy


def make_g_init(
    embedding: np.ndarray,
    mode: str = "F",
    seed: int = 0,
    scale: float = 1e-3,
) -> tuple[np.ndarray, str]:
    """Build G_0. ``F`` is the default reproduction assumption."""
    patterns = np.asarray(embedding, dtype=np.float64)
    if patterns.ndim != 2:
        raise ValueError("embedding must be 2-D")
    n_samples, n_components = patterns.shape
    name = str(mode)
    if name in {"F", "f", "g0_equals_f"}:
        return np.array(patterns, dtype=np.float64, copy=True), "F"
    if name == "deterministic_perturbation":
        rows = np.arange(n_samples, dtype=np.float64)[:, None]
        cols = np.arange(1, n_components + 1, dtype=np.float64)[None, :]
        pattern = np.cos(np.pi * rows * cols / max(n_samples, 1))
        return patterns + float(scale) * pattern, "deterministic_perturbation"
    if name == "random":
        rng = np.random.default_rng(int(seed))
        return rng.standard_normal((n_samples, n_components)), "random"
    raise ValueError(
        f"unknown g_init {mode!r}; expected F, deterministic_perturbation, or random"
    )


def undirected_edge_set(affinity: sparse.spmatrix) -> set[tuple[int, int]]:
    weights = sparse.coo_matrix(affinity)
    edges: set[tuple[int, int]] = set()
    for row, col, value in zip(weights.row, weights.col, weights.data):
        if value == 0.0:
            continue
        if int(row) < int(col):
            edges.add((int(row), int(col)))
    return edges


def edge_jaccard(left: set[tuple[int, int]], right: set[tuple[int, int]]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right) / len(union))


def graph_summary(affinity: sparse.spmatrix) -> dict[str, Any]:
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    n_components, _labels = connected_components(weights, directed=False, return_labels=True)
    n_undirected = int(weights.nnz // 2)
    degrees = np.asarray(weights.sum(axis=1)).ravel()
    return {
        "n_connected_components": int(n_components),
        "n_undirected_edges": n_undirected,
        "n_stored_nnz": int(weights.nnz),
        "degree_min": float(degrees.min()) if degrees.size else 0.0,
        "degree_mean": float(degrees.mean()) if degrees.size else 0.0,
        "degree_max": float(degrees.max()) if degrees.size else 0.0,
        "symmetric_stored": bool(np.allclose((weights - weights.T).data, 0.0))
        if weights.nnz
        else True,
    }


def eigenvalue_summary(values: np.ndarray, n_list: int = 8) -> dict[str, Any]:
    evals = np.asarray(values, dtype=np.float64).reshape(-1)
    if evals.size == 0:
        return {"n": 0}
    listed = [float(v) for v in evals[:n_list]]
    summary = {
        "n": int(evals.size),
        "min": float(evals[0]),
        "max": float(evals[-1]),
        "mean": float(evals.mean()),
        "listed": listed,
    }
    if evals.size >= 2:
        summary["gap_1_2"] = float(evals[1] - evals[0])
    if evals.size >= 3:
        summary["gap_2_3"] = float(evals[2] - evals[1])
    return summary


def augment_objective_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add relative objective change. Does not alter the solver stop rule."""
    augmented: list[dict[str, Any]] = []
    previous_obj: float | None = None
    for row in history:
        item = dict(row)
        obj = item.get("equation8_objective")
        if previous_obj is None or obj is None:
            item["relative_obj_change"] = None
        else:
            item["relative_obj_change"] = float(abs(float(obj) - previous_obj) / (1.0 + abs(previous_obj)))
        step = item.get("step_frobenius")
        item["relative_iterate_change"] = float(step) if step is not None else None
        augmented.append(item)
        if obj is not None:
            previous_obj = float(obj)
    return augmented


def label_disagreement(labels_a: np.ndarray, labels_b: np.ndarray) -> float:
    """Permutation-invariant fraction of points whose aligned labels differ."""
    aligned = clustering_accuracy(np.asarray(labels_a), np.asarray(labels_b))
    return float(1.0 - aligned)
