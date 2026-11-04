"""Deterministic random Lloyd trials and a fixed n_init."""

from __future__ import annotations

import inspect

import numpy as np

from experiments.v2_kmeans_protocol.kmeans_trials import KMEANS_N_INIT, RANDOM, fit_lloyd


def _matrix() -> np.ndarray:
    rng = np.random.default_rng(7)
    return rng.normal(size=(40, 4))


def test_random_lloyd_is_deterministic() -> None:
    features = _matrix()
    first = fit_lloyd(features, n_clusters=3, seed=4, initialization_label=RANDOM)
    second = fit_lloyd(features, n_clusters=3, seed=4, initialization_label=RANDOM)
    assert np.array_equal(first["labels"], second["labels"])
    assert first["inertia"] == second["inertia"]


def test_n_init_is_one() -> None:
    source = inspect.getsource(fit_lloyd)
    assert "n_init" in source
    assert KMEANS_N_INIT == 1
    result = fit_lloyd(_matrix(), n_clusters=3, seed=1, initialization_label=RANDOM)
    assert result["n_init"] == 1
    assert "y_true" not in source
