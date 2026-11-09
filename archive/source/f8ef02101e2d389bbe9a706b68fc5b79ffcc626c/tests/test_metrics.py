"""Unit tests for ACC and geometric-mean NMI."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import normalized_mutual_info_score

from benchmarks.metrics.accuracy import clustering_accuracy
from benchmarks.metrics.nmi import normalized_mutual_information


def test_perfect_clustering_scores_one():
    labels = np.array([0, 0, 1, 1, 2, 2])
    assert clustering_accuracy(labels, labels) == 1.0
    assert normalized_mutual_information(labels, labels) == 1.0


def test_permuted_labels_score_one():
    truth = np.array([0, 0, 1, 1, 2, 2])
    permuted = np.array([2, 2, 0, 0, 1, 1])
    assert clustering_accuracy(truth, permuted) == 1.0
    assert normalized_mutual_information(truth, permuted) == pytest.approx(1.0)


def test_string_labels_are_aligned():
    truth = np.array(["a", "a", "b", "b"])
    pred = np.array(["red", "red", "blue", "blue"])
    assert clustering_accuracy(truth, pred) == 1.0
    assert normalized_mutual_information(truth, pred) == pytest.approx(1.0)


def test_small_contingency_accuracy():
    # Rows are ground truth {0, 1}, columns are predictions {0, 1}:
    # [[2, 1], [0, 1]]. Best matching has weight 3, so ACC = 3/4.
    truth = np.array([0, 0, 0, 1])
    pred = np.array([0, 0, 1, 1])
    assert clustering_accuracy(truth, pred) == pytest.approx(0.75)


def test_small_contingency_nmi_matches_direct_arithmetic():
    truth = np.array([0, 0, 0, 1])
    pred = np.array([0, 0, 1, 1])
    # n=4, counts t_true=(3,1), t_pred=(2,2), cells (2,1), (0,1).
    numerator = (
        2.0 * np.log(4.0 * 2.0 / (3.0 * 2.0))
        + 1.0 * np.log(4.0 * 1.0 / (3.0 * 2.0))
        + 1.0 * np.log(4.0 * 1.0 / (1.0 * 2.0))
    )
    sum_true = 3.0 * np.log(3.0 / 4.0) + 1.0 * np.log(1.0 / 4.0)
    sum_pred = 2.0 * np.log(2.0 / 4.0) + 2.0 * np.log(2.0 / 4.0)
    expected = numerator / np.sqrt(sum_true * sum_pred)
    assert normalized_mutual_information(truth, pred) == pytest.approx(expected)
    sklearn_value = normalized_mutual_info_score(truth, pred, average_method="geometric")
    assert normalized_mutual_information(truth, pred) == pytest.approx(sklearn_value)


def test_degenerate_constant_prediction():
    truth = np.array([0, 0, 1, 1])
    pred = np.array([7, 7, 7, 7])
    assert clustering_accuracy(truth, pred) == pytest.approx(0.5)
    assert normalized_mutual_information(truth, pred) == 0.0


def test_both_constant_partitions_have_nmi_one():
    truth = np.array([3, 3, 3])
    pred = np.array([0, 0, 0])
    assert clustering_accuracy(truth, pred) == 1.0
    assert normalized_mutual_information(truth, pred) == 1.0


def test_single_sample():
    assert clustering_accuracy(np.array([4]), np.array(["z"])) == 1.0
    assert normalized_mutual_information(np.array([4]), np.array(["z"])) == 1.0


def test_more_predicted_clusters_than_truth():
    truth = np.array([0, 0, 0, 1, 1, 1])
    pred = np.array([0, 1, 2, 3, 4, 5])
    # Each predicted label is unique, so a one-to-one map can match at most
    # one point per true class. Two true classes give ACC = 2/6.
    assert clustering_accuracy(truth, pred) == pytest.approx(2.0 / 6.0)
    score = normalized_mutual_information(truth, pred)
    sklearn_value = normalized_mutual_info_score(truth, pred, average_method="geometric")
    assert score == pytest.approx(sklearn_value)
    assert 0.0 < score < 1.0


def test_rejected_shapes():
    with pytest.raises(ValueError):
        clustering_accuracy(np.array([0, 1]), np.array([0]))
    with pytest.raises(ValueError):
        normalized_mutual_information(np.array([]), np.array([]))
    with pytest.raises(ValueError):
        clustering_accuracy(np.array([[0, 1]]), np.array([[0, 1]]))
