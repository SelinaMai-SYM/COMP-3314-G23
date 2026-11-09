"""Threshold at which G = F is optimal for the ordered-pair objective.

For a symmetric W that stores both triangles, a noncoincident edge {i, j}
contributes 2 W_ij u_ij to the graph subgradient at row i, where
u_ij = (f_i - f_j) / ||f_i - f_j||. With

    q_i = sum_j W_ij (f_i - f_j) / ||f_i - f_j||

over noncoincident stored pairs, G = F is optimal when

    2 * gamma * max_i ||q_i||_2 <= 1,

so gamma_0 = 1 / (2 max_i ||q_i||) when that maximum is positive.
Coincident edges are not divided; their subgradient is a Euclidean ball and
feasibility is a second-order cone constraint. The factor 2 is the ordered-pair
count, not a tuned constant. Convex clustering and ADMM are standard tools.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse

from method_extension.v3_theory.common.objectives import as_csr


def _edge_arrays(affinity: sparse.spmatrix | np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    weights = as_csr(affinity).tocoo()
    keep = (weights.data > 0.0) & (weights.row < weights.col)
    return (
        np.asarray(weights.row[keep], dtype=np.int64),
        np.asarray(weights.col[keep], dtype=np.int64),
        np.asarray(weights.data[keep], dtype=np.float64),
    )


def ordered_pair_threshold(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    *,
    distance_tol: float = 1e-12,
    certify_coincident: bool = True,
) -> dict[str, Any]:
    """Return gamma_0 and whether the closed form applies."""
    from method_extension.next_round.certified_solver import threshold,graph_arrays
    features=np.asarray(embedding,dtype=float);info=threshold(features,as_csr(affinity));B,i,j,w=graph_arrays(affinity);diff=B@features;r=np.linalg.norm(diff,axis=1);u=np.divide(diff,r[:,None],out=np.zeros_like(diff),where=r[:,None]>0);q=B.T@(w[:,None]*u)
    return {'gamma_0':info['gamma0'],'max_q_norm':float(np.linalg.norm(q,axis=1).max()),'n_undirected_edges':len(w),'n_coincident_edges':info['coincident_edges'],'threshold_source':'zero_TV_analytic' if info['tv_F']==0 else ('coincident_subgradient_zero_choice_sufficient' if info['coincident_edges'] else 'closed_form_noncoincident'),'q_norm':np.linalg.norm(q,axis=1),'sufficient_only':info['sufficient_only'],'distance_tolerance_used':0.}


def g_equals_f_is_optimal(threshold: dict[str, Any], gamma: float) -> bool:
    value=float(threshold['gamma_0'])
    return bool(gamma>=0 and (np.isinf(value) or (np.isfinite(value) and gamma<=value)))


def fusion_summary(patterns: np.ndarray, affinity: sparse.spmatrix | np.ndarray, *, tol: float = 1e-6) -> dict[str, float]:
    """How many stored ordered pairs and rows collapsed."""
    from method_extension.v3_theory.common.objectives import as_csr as _csr

    matrix = np.asarray(patterns, dtype=np.float64)
    weights = _csr(affinity).tocoo()
    difference = matrix[weights.row] - matrix[weights.col]
    distance = np.linalg.norm(difference, axis=1)
    active = weights.data > 0.0
    n_active = int(np.sum(active))
    n_fused = int(np.sum((distance <= tol) & active))
    rounded = np.round(matrix / max(tol, 1e-8))
    # Distinct rows after a tolerance rounding. This is a diagnostic, not a cluster count.
    distinct = np.unique(rounded, axis=0).shape[0]
    return {
        "n_active_ordered_pairs": n_active,
        "n_fused_ordered_pairs": n_fused,
        "fused_pair_fraction": float(n_fused / max(n_active, 1)),
        "n_distinct_rounded_rows": int(distinct),
    }
