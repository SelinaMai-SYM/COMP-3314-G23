"""Greedy scikit-learn k-means++ and vanilla k-means++ stay separate."""

from __future__ import annotations

import numpy as np

from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY, VANILLA, fit_lloyd


def test_names_are_not_merged(monkeypatch) -> None:
    calls = {}

    def fake_plusplus(features, n_clusters, **kwargs):
        calls.update(kwargs)
        centers = np.asarray(features[:n_clusters], dtype=np.float64)
        return centers, np.arange(n_clusters)

    monkeypatch.setattr(
        "experiments.v2_kmeans_protocol.vanilla_kmeanspp.kmeans_plusplus",
        fake_plusplus,
    )
    features = np.random.default_rng(0).normal(size=(20, 3))
    greedy = fit_lloyd(features, 3, seed=2, initialization_label=GREEDY)
    vanilla = fit_lloyd(features, 3, seed=2, initialization_label=VANILLA)
    assert greedy["initialization"] == "k-means++"
    assert vanilla["initialization"] == "vanilla_centers"
    assert GREEDY != VANILLA
    assert calls["n_local_trials"] == 1
    assert greedy["n_init"] == 1 and vanilla["n_init"] == 1


def test_greedy_repeat_is_deterministic() -> None:
    features = np.random.default_rng(1).normal(size=(30, 4))
    first = fit_lloyd(features, 4, seed=8, initialization_label=GREEDY)
    second = fit_lloyd(features, 4, seed=8, initialization_label=GREEDY)
    assert np.array_equal(first["labels"], second["labels"])
