"""Shared Eq. (4) path: no self-neighbors, and SC/SSC see the same F."""

from __future__ import annotations

import numpy as np

from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import embeddings_match, spectral_embedding


def test_knn_has_no_self_loop_and_uses_squared_bandwidth() -> None:
    generator = np.random.default_rng(0)
    features = generator.normal(size=(12, 3))
    affinity, info = knn_affinity(features, k=3, delta2=None)
    assert np.allclose(affinity.diagonal(), 0.0)
    assert info["delta2"] > 0.0
    # symmetrized union graph
    assert np.allclose(affinity.toarray(), affinity.toarray().T)


def test_sc_and_ssc_initial_f_match() -> None:
    generator = np.random.default_rng(1)
    features = np.vstack(
        [
            generator.normal(size=(10, 4)),
            generator.normal(size=(10, 4)) + 2.5,
        ]
    )
    config = SpectralGraphConfig(k=3, row_normalize=False, variant="E13")
    other = SpectralGraphConfig(k=3, row_normalize=False, variant="E8")
    left, _info = spectral_embedding(features, n_components=2, config=config)
    right, _info = spectral_embedding(features, n_components=2, config=other)
    assert embeddings_match(left, right)
