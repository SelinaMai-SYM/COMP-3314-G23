"""Clustering accuracy with one-to-one Hungarian alignment.

Chang et al. (AAAI 2015), Equation (19): accuracy is the fraction of points
whose predicted label matches the ground truth after the optimal permutation
of cluster ids (Kuhn–Munkres).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def clustering_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """ACC in [0, 1] after an optimal one-to-one label alignment.

    Label values need not be contiguous integers. If the two partitions have
    different numbers of distinct labels, the assignment covers the smaller
    side and unmatched labels count as errors. Empty inputs and unequal
    lengths raise ``ValueError``.
    """
    truth = np.asarray(y_true)
    pred = np.asarray(y_pred)
    if truth.ndim != 1 or pred.ndim != 1:
        raise ValueError("y_true and y_pred must be one-dimensional")
    if truth.shape[0] != pred.shape[0]:
        raise ValueError("y_true and y_pred must have the same length")
    n_samples = int(truth.shape[0])
    if n_samples == 0:
        raise ValueError("y_true and y_pred must be non-empty")

    _, truth_index = np.unique(truth, return_inverse=True)
    _, pred_index = np.unique(pred, return_inverse=True)
    n_true = int(truth_index.max()) + 1
    n_pred = int(pred_index.max()) + 1
    contingency = np.zeros((n_true, n_pred), dtype=np.float64)
    np.add.at(contingency, (truth_index, pred_index), 1.0)
    row_ind, col_ind = linear_sum_assignment(-contingency)
    return float(contingency[row_ind, col_ind].sum() / n_samples)
