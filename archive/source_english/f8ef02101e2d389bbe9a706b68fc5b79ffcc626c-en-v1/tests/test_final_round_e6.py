"""E6 checks that are not already in tests/test_metrics.py.

The Hungarian ACC and geometric NMI definitions stay in benchmarks.metrics.
These tests cover non-contiguous labels, a one-to-one mismatch, numerical
label magnitude, and the Equation (8) edge sum (each stored ordered pair
once, no extra factor of two).
"""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import normalized_mutual_info_score
from scipy import sparse

from benchmarks.metrics.accuracy import clustering_accuracy
from benchmarks.metrics.nmi import normalized_mutual_information
from SSC_method.objective import equation8_objective, graph_l2_term


def test_noncontiguous_labels_are_permutation_invariant():
    truth = np.array([0, 0, 5, 5, 5, 9])
    pred = np.array([4, 4, 1, 1, 1, 7])
    assert clustering_accuracy(truth, pred) == 1.0
    assert normalized_mutual_information(truth, pred) == pytest.approx(1.0)
    sklearn_value = normalized_mutual_info_score(truth, pred, average_method="geometric")
    assert normalized_mutual_information(truth, pred) == pytest.approx(sklearn_value)


def test_unequal_sizes_and_partial_match():
    truth = np.array([0, 0, 0, 0, 1, 1])
    pred = np.array([0, 0, 0, 1, 1, 0])
    # Contingency [[3, 1], [1, 1]]. Best one-to-one assignment has weight 4.
    assert clustering_accuracy(truth, pred) == pytest.approx(4.0 / 6.0)
    score = normalized_mutual_information(truth, pred)
    sklearn_value = normalized_mutual_info_score(truth, pred, average_method="geometric")
    assert score == pytest.approx(sklearn_value)
    assert 0.0 < score < 1.0


def test_large_label_ids_do_not_change_acc():
    truth = np.array([0, 0, 1, 1])
    pred = np.array([10**15, 10**15, 10**15 + 3, 10**15 + 3])
    assert clustering_accuracy(truth, pred) == 1.0
    assert normalized_mutual_information(truth, pred) == pytest.approx(1.0)


def test_single_cluster_prediction_on_unequal_truth():
    truth = np.array([0, 1, 2, 0, 1, 2])
    pred = np.array([8, 8, 8, 8, 8, 8])
    assert clustering_accuracy(truth, pred) == pytest.approx(2.0 / 6.0)
    assert normalized_mutual_information(truth, pred) == 0.0


def test_graph_term_counts_each_stored_ordered_pair_once():
    # Two nodes, both ordered pairs stored, distance ||g0-g1|| = 2.
    # sum_{i,j} W_ij ||gi-gj|| = 0.5*2 + 0.5*2 = 2.
    # An extra factor of 2 would give 4. Dropping one triangle would give 1.
    patterns = np.array([[0.0, 0.0], [2.0, 0.0]], dtype=np.float64)
    weights = sparse.csr_matrix(np.array([[0.0, 0.5], [0.5, 0.0]]))
    tv = graph_l2_term(patterns, weights)
    assert tv == pytest.approx(2.0)
    embedding = np.zeros_like(patterns)
    # ||G-F||_{2,1} = 0 + 2 = 2, gamma = 1, objective = 4.
    assert equation8_objective(patterns, embedding, weights, gamma=1.0) == pytest.approx(4.0)
