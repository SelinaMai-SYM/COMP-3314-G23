"""Labels do not enter initialization or inertia selection."""

from __future__ import annotations

import inspect

import numpy as np

from experiments.v2_kmeans_protocol.kmeans_trials import RANDOM, fit_lloyd
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from experiments.v2_kmeans_protocol.select_best_inertia import select_min_inertia


def test_fit_source_has_no_labels() -> None:
    source = inspect.getsource(fit_lloyd)
    assert "y_true" not in source
    assert "clustering_accuracy" not in source


def test_permuted_labels_do_not_change_inertia() -> None:
    features = np.random.default_rng(5).normal(size=(30, 3))
    fit = fit_lloyd(features, n_clusters=3, seed=9, initialization_label=RANDOM)
    truth = np.array([0, 1, 2] * 10)
    permuted = truth[::-1]
    first = evaluate_partition(truth, fit["labels"])
    evaluate_partition(permuted, fit["labels"])
    assert fit["inertia"] == fit_lloyd(features, 3, 9, RANDOM)["inertia"]
    trials = [
        {"seed": 9, "inertia": fit["inertia"], "acc": first["acc"]},
        {"seed": 1, "inertia": fit["inertia"] + 1.0, "acc": 1.0},
    ]
    assert select_min_inertia(trials)["seed"] == 9
