"""Tests for LDA + spectral clustering. Tiny synthetic samples only."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix

from baselines.lda_spectral import fit_predict as lda_spectral_fit_predict


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


def test_lda_spectral_is_deterministic_without_ground_truth() -> None:
    features, truth = _two_blobs()
    with pytest.raises(TypeError, match="unexpected"):
        lda_spectral_fit_predict(features, 2, 0, n_components=1, y=truth)
    labels = lda_spectral_fit_predict(
        features,
        2,
        random_state=0,
        n_components=1,
        max_iter=5,
        delta=1.0,
        n_neighbors=5,
    )
    repeat = lda_spectral_fit_predict(
        features,
        2,
        random_state=0,
        n_components=1,
        max_iter=5,
        delta=1.0,
        n_neighbors=5,
    )
    assert np.array_equal(labels, repeat)
    assert _accuracy(truth, labels) == 1.0
