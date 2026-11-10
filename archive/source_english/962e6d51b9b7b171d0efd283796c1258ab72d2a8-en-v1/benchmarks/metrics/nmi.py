"""Normalized mutual information with geometric-mean entropy normalization.

Chang et al. (AAAI 2015), Equations (20) and (21), following Strehl and Ghosh
(2003). The denominator is sqrt(H(P) H(Q)). The logarithm base cancels.
This is the same normalization as scikit-learn's
``normalized_mutual_info_score(..., average_method='geometric')``.
"""

from __future__ import annotations

import numpy as np


def normalized_mutual_information(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """NMI in Equation (21).

    Contingency cells that are zero are omitted, so the sum never takes
    log(0). If both partitions have zero entropy (a single label on each
    side), the value is 1. If only one entropy is zero, the value is 0.
    The paper does not state these two edge cases; they follow the usual
    geometric-mean convention so that a constant labeling is comparable
    across implementations.
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
    true_counts = contingency.sum(axis=1)
    pred_counts = contingency.sum(axis=0)

    numerator = 0.0
    for true_label in range(n_true):
        for pred_label in range(n_pred):
            count = contingency[true_label, pred_label]
            if count <= 0.0:
                continue
            numerator += count * np.log(
                n_samples * count / (true_counts[true_label] * pred_counts[pred_label])
            )

    # sum_l t_l log(t_l / n) is negative or zero. The product of the two
    # sums is nonnegative, which is what Equation (21) places under the
    # square root.
    sum_true = float(np.sum(true_counts * np.log(true_counts / n_samples)))
    sum_pred = float(np.sum(pred_counts * np.log(pred_counts / n_samples)))
    if sum_true == 0.0 and sum_pred == 0.0:
        return 1.0
    if sum_true == 0.0 or sum_pred == 0.0:
        return 0.0
    return float(numerator / np.sqrt(sum_true * sum_pred))
