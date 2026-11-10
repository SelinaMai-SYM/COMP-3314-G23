"""Hungarian ACC and geometric-mean NMI."""

import numpy as np

from experiments.v2_kmeans_protocol.metrics import (
    clustering_accuracy,
    evaluate_partition,
    mean_and_sample_sd,
    normalized_mutual_information,
)


def test_permutation_and_identical_partitions() -> None:
    truth = np.array([0, 0, 1, 1, 2, 2])
    permuted = np.array([2, 2, 0, 0, 1, 1])
    scores = evaluate_partition(truth, permuted)
    assert scores["acc"] == 1.0
    assert scores["nmi"] == 1.0
    swapped = evaluate_partition(truth, np.array([1, 1, 2, 2, 0, 0]))
    assert swapped["acc"] == scores["acc"]
    assert swapped["nmi"] == scores["nmi"]


def test_disagreement_and_unequal_sizes() -> None:
    truth = np.array([0, 0, 0, 1, 1, 2])
    pred = np.array([0, 1, 0, 1, 0, 2])
    acc = clustering_accuracy(truth, pred)
    nmi = normalized_mutual_information(truth, pred)
    assert 0.0 < acc < 1.0
    assert 0.0 < nmi < 1.0
    both = evaluate_partition(truth, pred)
    assert both["acc"] == acc and both["nmi"] == nmi


def test_single_observation_has_no_sample_sd() -> None:
    mean, sd = mean_and_sample_sd([0.5])
    assert mean == 0.5
    assert sd is None
