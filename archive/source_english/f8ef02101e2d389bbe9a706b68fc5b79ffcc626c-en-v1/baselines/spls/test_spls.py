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


def test_equation18_matches_dense_solve() -> None:
    """Paper Eq. (18) with samples stored as rows: Y = alpha * M^{-1} X."""
    features, _truth = _two_blobs(n_per_class=8)
    alpha = 0.35
    shrunk, _info = oneshot_shrunk_patterns(features, alpha=alpha, n_neighbors=4)
    affinity = __import__("baselines.spls.spls", fromlist=["local_scaling_affinity"]).local_scaling_affinity(
        features, 4
    )
    degree = np.asarray(affinity.sum(axis=1)).ravel()
    laplacian = np.diag(degree) - affinity.toarray()
    coefficient = (1.0 - alpha) * laplacian + alpha * np.eye(features.shape[0])
    expected = alpha * np.linalg.solve(coefficient, features)
    assert np.allclose(shrunk, expected, atol=1e-8)


def test_local_scaling_uses_zelnik_product_without_extra_two() -> None:
    """Section 4 replaces Eq. (7)'s global 2*r^2 by Zelnik-Manor local scaling."""
    from baselines.spls import local_scaling_affinity

    features = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [3.0, 0.0],
            [6.0, 0.0],
        ]
    )
    affinity = local_scaling_affinity(features, n_neighbors=1).toarray()
    sigma = np.array([1.0, 1.0, 2.0, 3.0])
    distance = 1.0
    expected = np.exp(-(distance ** 2) / (sigma[0] * sigma[1]))
    assert affinity[0, 1] == pytest.approx(expected)
    assert affinity[1, 0] == pytest.approx(expected)
    assert affinity[0, 2] == 0.0


def test_alpha_changes_the_shrunk_pattern() -> None:
    features, _truth = _two_blobs()
    left, _info = oneshot_shrunk_patterns(features, alpha=0.2, n_neighbors=5)
    right, _info = oneshot_shrunk_patterns(features, alpha=0.8, n_neighbors=5)
    assert not np.allclose(left, right)
