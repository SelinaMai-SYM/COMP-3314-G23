"""Declared LLC parameters must change the embedding that is clustered."""

from __future__ import annotations

import numpy as np

from baselines.llc import local_regression_matrix
from experiments.methods import prepare_llc_embedding
from experiments.v3_reproduction.method_registry import bind_config


def _blobs() -> np.ndarray:
    generator = np.random.default_rng(0)
    left = generator.normal(size=(12, 3))
    right = generator.normal(size=(12, 3)) + np.array([3.0, 0.0, 0.0])
    return np.vstack([left, right])


def test_ridge_changes_the_local_regression_matrix() -> None:
    features = _blobs()
    low = local_regression_matrix(features, n_neighbors=3, reg=0.1, kernel="gaussian", gamma=1.0)
    high = local_regression_matrix(features, n_neighbors=3, reg=10.0, kernel="gaussian", gamma=1.0)
    assert low.shape == high.shape
    assert not np.allclose(low, high)


def test_prepare_llc_forwards_ridge_and_bandwidth() -> None:
    features = _blobs()
    prepared = prepare_llc_embedding(features, 2, k=3, reg=0.2, kernel="gaussian", gamma=0.5)
    assert prepared.extra["llc_reg"] == 0.2
    assert prepared.extra["llc_kernel_bandwidth"] == 0.5
    other = prepare_llc_embedding(features, 2, k=3, reg=5.0, kernel="gaussian", gamma=2.0)
    assert other.extra["llc_reg"] == 5.0
    assert other.extra["llc_kernel_bandwidth"] == 2.0
    low = local_regression_matrix(features, n_neighbors=3, reg=0.2, kernel="gaussian", gamma=0.5)
    high = local_regression_matrix(features, n_neighbors=3, reg=5.0, kernel="gaussian", gamma=2.0)
    assert not np.allclose(low, high)


def test_ignored_requested_keys_are_rejected() -> None:
    try:
        bind_config({"llc_ridge": 1.0, "dropped": 3}, {"llc_ridge": 1.0})
    except RuntimeError as exc:
        assert "dropped" in str(exc)
    else:
        raise AssertionError("ignored parameter was accepted")
