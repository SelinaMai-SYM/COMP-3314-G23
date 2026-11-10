"""Hungarian ACC and geometric NMI share one prediction vector."""

from __future__ import annotations

import numpy as np

from experiments.v2_kmeans_protocol.metrics import evaluate_partition


def test_permuted_labels_score_one() -> None:
    truth = np.array([0, 0, 1, 1, 2, 2])
    pred = np.array([2, 2, 0, 0, 1, 1])
    scores = evaluate_partition(truth, pred)
    assert scores["acc"] == 1.0
    assert scores["nmi"] == 1.0


def test_unequal_sizes_are_not_zero_or_one() -> None:
    truth = np.array([0, 0, 0, 1, 1, 2])
    pred = np.array([0, 0, 1, 1, 1, 2])
    scores = evaluate_partition(truth, pred)
    assert 0.0 < scores["acc"] < 1.0
    assert 0.0 < scores["nmi"] < 1.0
