"""Ding--Li LDA uses K-1, rejects labels, and refits per seed."""

from __future__ import annotations

import numpy as np
import pytest

from baselines.lda_kmeans import fit_predict, scatter_objective


def _blobs():
    generator = np.random.default_rng(0)
    parts = [generator.normal(size=(15, 4)) + np.array([3.0 * i, 0, 0, 0]) for i in range(3)]
    features = np.vstack(parts)
    truth = np.repeat(np.arange(3), 15)
    return features, truth


def test_classical_lda_refuses_padding_past_k_minus_one() -> None:
    features, _truth = _blobs()
    with pytest.raises(ValueError):
        fit_predict(features, 3, 0, n_components=150)


def test_ground_truth_is_not_a_parameter() -> None:
    features, truth = _blobs()
    with pytest.raises(TypeError):
        fit_predict(features, 3, 0, n_components=2, y=truth)


def test_each_seed_is_a_full_fit() -> None:
    features, _truth = _blobs()
    first = fit_predict(features, 3, 0, n_components=2, init="random", n_init=1)
    second = fit_predict(features, 3, 1, n_components=2, init="random", n_init=1)
    assert first.shape == second.shape
    centered = features - features.mean(axis=0)
    objective = scatter_objective(centered, first, np.eye(4)[:, :2])
    assert np.isfinite(objective["ratio_of_traces"]) or objective["trace_within"] == 0.0


def test_wide_data_matches_the_ambient_generalized_eigenvectors() -> None:
    from baselines.lda_kmeans.lda_kmeans import _data_span, _lda_basis_for_fit, lda_basis

    generator = np.random.default_rng(2)
    features = generator.normal(size=(36, 80))
    features = features - features.mean(axis=0)
    labels = np.repeat(np.arange(4), 9)
    span = _data_span(features)
    assert span is not None and span.shape == (80, 35)
    reduced = _lda_basis_for_fit(features, labels, 3, 1e-8, span)
    full = lda_basis(features, labels, 3, 1e-8)
    for index in range(reduced.shape[1]):
        if np.dot(reduced[:, index], full[:, index]) < 0:
            reduced[:, index] *= -1
    assert np.allclose(reduced, full, atol=1e-6)
