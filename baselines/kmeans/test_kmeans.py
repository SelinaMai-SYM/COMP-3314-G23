"""Tests for Lloyd K-means. Tiny synthetic samples only."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix

from baselines.kmeans import fit_predict as kmeans_fit_predict


def _accuracy(truth: np.ndarray, labels: np.ndarray) -> float:
    table = confusion_matrix(truth, labels)
    rows, cols = linear_sum_assignment(table.max() - table)
    return float(table[rows, cols].sum()) / float(len(truth))


def _two_blobs(seed: int = 0, n_per_class: int = 25, extra_dims: int = 0) -> tuple[np.ndarray, np.ndarray]:
    generator = np.random.default_rng(seed)
    left = generator.normal(loc=0.0, scale=0.25, size=(n_per_class, 2))
    right = generator.normal(loc=0.0, scale=0.25, size=(n_per_class, 2))
    right[:, 0] += 6.0
    features = np.vstack([left, right])
    if extra_dims:
        noise = generator.normal(loc=0.0, scale=0.05, size=(features.shape[0], extra_dims))
        features = np.hstack([features, noise])
    truth = np.repeat([0, 1], n_per_class)
    return features, truth


def test_kmeans_is_deterministic_and_separates_blobs() -> None:
    features, truth = _two_blobs()
    first = kmeans_fit_predict(features, 2, random_state=0, n_init=1, init="random")
    second = kmeans_fit_predict(features, 2, random_state=0, n_init=1, init="random")
    assert first.shape == (features.shape[0],)
    assert first.dtype == np.int64
    assert np.array_equal(first, second)
    assert _accuracy(truth, first) == 1.0


def test_kmeans_rejects_hidden_and_noninteger_controls() -> None:
    features, _truth = _two_blobs(n_per_class=8)
    with pytest.raises(TypeError, match="random_state"):
        kmeans_fit_predict(features, 2, random_state=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="unexpected"):
        kmeans_fit_predict(features, 2, 0, copied_metric=True)
