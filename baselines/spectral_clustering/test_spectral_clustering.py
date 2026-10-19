"""Tests for the Eq. (4) spectral baseline. Tiny synthetic samples only."""

from __future__ import annotations

import inspect

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix

from baselines.spectral_clustering import (
    fit_predict as spectral_fit_predict,
    gaussian_knn_affinity,
    symmetric_normalized_laplacian,
)


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


def test_spectral_laplacian_matches_equation_4() -> None:
    affinity = np.array(
        [
            [0.0, 0.5, 0.0],
            [0.5, 0.0, 0.5],
            [0.0, 0.5, 0.0],
        ]
    )
    degree = affinity.sum(axis=1)
    scale = 1.0 / np.sqrt(degree)
    normalized = (scale[:, None] * affinity) * scale[None, :]
    expected = np.eye(3) - normalized
    actual = symmetric_normalized_laplacian(affinity)
    assert np.allclose(actual, expected)
    assert np.allclose(actual, actual.T)


def test_gaussian_weights_and_mutual_knn_rule() -> None:
    points = np.array([[0.0], [1.0], [10.0]])
    union = gaussian_knn_affinity(points, n_neighbors=1, delta=1.0, knn_mode="union")
    mutual = gaussian_knn_affinity(points, n_neighbors=1, delta=1.0, knn_mode="mutual")
    assert mutual[0, 1] == pytest.approx(np.exp(-1.0))
    assert mutual[1, 2] == 0.0
    assert union[1, 2] == pytest.approx(np.exp(-81.0))
    assert np.count_nonzero(union) > np.count_nonzero(mutual)
    rows, cols = np.nonzero(np.triu(union, k=1))
    for i, j in zip(rows, cols):
        gap = float(np.sum((points[i] - points[j]) ** 2))
        assert union[i, j] == pytest.approx(np.exp(-gap))


def test_spectral_clustering_does_not_use_sklearn_estimator() -> None:
    module_source = inspect.getsource(inspect.getmodule(spectral_fit_predict))
    assert "import SpectralClustering" not in module_source
    assert "SpectralClustering(" not in module_source
    features, truth = _two_blobs()
    labels = spectral_fit_predict(
        features, 2, random_state=0, n_neighbors=5, delta=1.0, knn_mode="union"
    )
    repeat = spectral_fit_predict(
        features, 2, random_state=0, n_neighbors=5, delta=1.0, knn_mode="union"
    )
    assert np.array_equal(labels, repeat)
    assert _accuracy(truth, labels) == 1.0
