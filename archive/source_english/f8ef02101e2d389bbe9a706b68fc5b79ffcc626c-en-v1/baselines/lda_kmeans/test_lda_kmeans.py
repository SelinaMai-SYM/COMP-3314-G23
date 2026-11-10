"""Tests for LDA + K-means. Tiny synthetic samples only."""

from __future__ import annotations

import inspect

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix

from baselines.lda_kmeans import fit_predict as lda_kmeans_fit_predict


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


def test_lda_kmeans_uses_cluster_labels_and_respects_rank() -> None:
    features, truth = _two_blobs(extra_dims=2)
    signature = inspect.signature(lda_kmeans_fit_predict)
    assert list(signature.parameters)[:3] == ["X", "n_clusters", "random_state"]
    assert "y" not in signature.parameters
    with pytest.raises(TypeError, match="n_components"):
        lda_kmeans_fit_predict(features, 2, random_state=0)
    with pytest.raises(ValueError, match="n_clusters - 1"):
        lda_kmeans_fit_predict(features, 2, random_state=0, n_components=2)
    with pytest.raises(TypeError, match="unexpected"):
        lda_kmeans_fit_predict(features, 2, 0, n_components=1, y=truth)
    labels = lda_kmeans_fit_predict(
        features, 2, random_state=0, n_components=1, max_iter=10
    )
    assert np.array_equal(
        labels,
        lda_kmeans_fit_predict(features, 2, random_state=0, n_components=1, max_iter=10),
    )
    assert _accuracy(truth, labels) == 1.0
