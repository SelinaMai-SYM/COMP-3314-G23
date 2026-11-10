"""One-shot SLPS on a separable toy. It is not a placeholder."""

from __future__ import annotations

import numpy as np
import pytest

from baselines.spls import fit_predict, oneshot_shrunk_patterns


def _two_blobs(seed: int = 0, n_per_class: int = 12) -> tuple[np.ndarray, np.ndarray]:
    generator = np.random.default_rng(seed)
    left = generator.normal(loc=0.0, scale=0.2, size=(n_per_class, 4))
    right = generator.normal(loc=0.0, scale=0.2, size=(n_per_class, 4))
    right[:, 0] += 5.0
    features = np.vstack([left, right])
    truth = np.repeat([0, 1], n_per_class)
    return features, truth


def test_oneshot_returns_finite_patterns_and_rejects_labels() -> None:
    features, truth = _two_blobs()
    shrunk, info = oneshot_shrunk_patterns(features, alpha=0.5, n_neighbors=5)
    assert shrunk.shape == features.shape
    assert np.isfinite(shrunk).all()
    assert info["form"] == "one_shot_eq18"
    with pytest.raises(TypeError):
        fit_predict(features, 2, 0, n_components=1, alpha=0.5, y=truth)


def test_alpha_changes_the_shrunk_pattern() -> None:
    features, _truth = _two_blobs()
    left, _info = oneshot_shrunk_patterns(features, alpha=0.2, n_neighbors=5)
    right, _info = oneshot_shrunk_patterns(features, alpha=0.8, n_neighbors=5)
    assert not np.allclose(left, right)
