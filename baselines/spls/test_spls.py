"""Tests for the SPLS placeholder. Tiny synthetic samples only."""

from __future__ import annotations

import numpy as np
import pytest

from baselines.spls import fit_predict as spls_fit_predict


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


def test_spls_is_not_implemented() -> None:
    features, _truth = _two_blobs(n_per_class=6)
    with pytest.raises(NotImplementedError, match="NOT_IMPLEMENTED"):
        spls_fit_predict(features, 2, random_state=0, n_components=2)
