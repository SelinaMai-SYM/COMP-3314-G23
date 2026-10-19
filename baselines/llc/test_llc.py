"""Tests for LLC. Tiny synthetic samples only."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix

from baselines.llc import fit_predict as llc_fit_predict


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


def test_llc_follows_local_learning_and_is_deterministic() -> None:
    features, truth = _two_blobs(n_per_class=20)
    labels = llc_fit_predict(
        features,
        2,
        random_state=0,
        n_neighbors=5,
        reg=1.0,
        kernel="gaussian",
        gamma=1.0,
    )
    repeat = llc_fit_predict(
        features,
        2,
        random_state=0,
        n_neighbors=5,
        reg=1.0,
        kernel="gaussian",
        gamma=1.0,
    )
    assert np.array_equal(labels, repeat)
    assert _accuracy(truth, labels) == 1.0
    cosine = llc_fit_predict(
        features, 2, random_state=1, n_neighbors=5, reg=0.1, kernel="cosine"
    )
    assert cosine.shape == (features.shape[0],)
    assert set(np.unique(cosine)).issubset({0, 1})
