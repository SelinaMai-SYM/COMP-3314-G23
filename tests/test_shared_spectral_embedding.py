"""Shared Eq. (4) graph and embedding: SC and SSC must produce the same F."""

from __future__ import annotations

import inspect

import numpy as np
import pytest
from scipy.linalg import eigh

from baselines.spectral_clustering import (
    gaussian_knn_affinity,
    spectral_embedding as sc_spectral_embedding,
)
from experiments.methods import prepare_spectral, prepare_ssc_family
from SSC_method.graph_construction import knn_affinity, symmetric_normalized_laplacian
from SSC_method.optimizer import LINEAR_SYSTEM_VARIANTS
from SSC_method.spectral_config import SIGN_CONVENTION, SpectralGraphConfig
from SSC_method.spectral_embedding import (
    embeddings_match,
    orient_eigenvector_signs,
    spectral_embedding as ssc_spectral_embedding,
)


def _features(seed: int = 0, n_samples: int = 36, n_features: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n_samples, n_features))


def test_shared_affinity_is_symmetric_nonnegative_and_zero_diagonal() -> None:
    features = _features()
    config = SpectralGraphConfig(k=5, symmetrization="union")
    sparse_affinity, info = knn_affinity(features, config=config)
    dense_affinity = gaussian_knn_affinity(features, n_neighbors=5, knn_mode="union")
    assert info["symmetrization"] == "union_maximum"
    assert np.allclose(sparse_affinity.toarray(), dense_affinity, atol=1e-12)
    assert np.allclose(dense_affinity, dense_affinity.T, atol=1e-12)
    assert np.all(dense_affinity >= 0.0)
    assert np.allclose(np.diag(dense_affinity), 0.0)
    if sparse_affinity.nnz:
        assert np.all(sparse_affinity.data >= 0.0)


def test_shared_laplacian_eigenvalues_are_ascending() -> None:
    features = _features(seed=1)
    affinity, _ = knn_affinity(features, k=5)
    laplacian = symmetric_normalized_laplacian(affinity).toarray()
    assert np.allclose(laplacian, laplacian.T, atol=1e-12)
    eigenvalues = eigh(laplacian, eigvals_only=True)
    assert np.all(np.diff(eigenvalues) >= -1e-10)
    embedding, info = ssc_spectral_embedding(features, n_components=4, k=5)
    assert np.all(np.diff(info["eigenvalues"]) >= -1e-8)
    assert info["eigenvalues"] == pytest.approx(eigenvalues[:4], abs=1e-8)
    assert info["sign_convention"] == SIGN_CONVENTION
    assert info["row_normalize"] is False
    assert embedding.shape == (features.shape[0], 4)


def test_sc_and_ssc_embeddings_match_after_sign_convention() -> None:
    features = _features(seed=2, n_samples=40, n_features=6)
    config = SpectralGraphConfig(k=5, symmetrization="union", row_normalize=False)
    sc_embedding, sc_info = sc_spectral_embedding(
        features,
        n_clusters=3,
        n_neighbors=5,
        knn_mode="union",
        return_info=True,
    )
    ssc_embedding, ssc_info = ssc_spectral_embedding(
        features, n_components=3, config=config
    )
    assert sc_info["shared_eq4_path"] is True
    assert ssc_info["shared_eq4_path"] is True
    assert sc_info["graph"]["symmetrization"] == ssc_info["graph"]["symmetrization"]
    assert sc_info["graph"]["delta2"] == pytest.approx(ssc_info["graph"]["delta2"])
    assert sc_info["row_normalize"] is False
    assert ssc_info["row_normalize"] is False
    aligned_sc = orient_eigenvector_signs(sc_embedding)
    aligned_ssc = orient_eigenvector_signs(ssc_embedding)
    assert np.allclose(aligned_sc, aligned_ssc, rtol=1e-8, atol=1e-8)
    assert embeddings_match(sc_embedding, ssc_embedding)
    assert np.allclose(sc_embedding, ssc_embedding, rtol=1e-8, atol=1e-8)


def test_prepare_spectral_uses_same_f_as_ssc_and_does_not_switch_on_n() -> None:
    source = inspect.getsource(prepare_spectral)
    assert "n_samples > 1500" not in source
    assert "ssc_method_sparse" not in source
    assert "sc_spectral_embedding" not in source
    features = _features(seed=3, n_samples=24, n_features=4)
    config = SpectralGraphConfig(k=5, symmetrization="union", row_normalize=False)
    prepared_sc = prepare_spectral(features, n_clusters=3, k=5, graph_config=config)
    prepared_ssc = prepare_ssc_family(
        features,
        n_clusters=3,
        gamma=1.0,
        k=5,
        mutual=False,
        graph_config=config,
    )
    assert prepared_sc.extra["spectral_backend"] == "shared_eq4"
    assert prepared_sc.extra["shared_eq4_path"] is True
    assert prepared_ssc.extra["embedding_info"]["shared_eq4_path"] is True
    assert embeddings_match(prepared_sc.features, prepared_ssc.embedding)
    assert np.allclose(prepared_sc.features, prepared_ssc.embedding, rtol=1e-8, atol=1e-8)
    assert prepared_sc.extra["row_normalize"] is False


def test_e8_and_e13_remain_distinct_linear_systems() -> None:
    assert set(LINEAR_SYSTEM_VARIANTS) == {"E13", "E8"}
    assert LINEAR_SYSTEM_VARIANTS["E13"] == 1.0
    assert LINEAR_SYSTEM_VARIANTS["E8"] == 2.0
    default = SpectralGraphConfig()
    assert default.variant == "E13"
    assert default.row_normalize is False
    assert default.g_init == "F"
    assert default.kmeans_init == "random"


def test_explicit_delta_keeps_union_and_mutual_distinct() -> None:
    points = np.array([[0.0], [1.0], [10.0]])
    union = gaussian_knn_affinity(points, n_neighbors=1, delta=1.0, knn_mode="union")
    mutual = gaussian_knn_affinity(points, n_neighbors=1, delta=1.0, knn_mode="mutual")
    shared_union, union_info = knn_affinity(
        points, k=1, delta2=1.0, symmetrization="union"
    )
    shared_mutual, mutual_info = knn_affinity(
        points, k=1, delta2=1.0, symmetrization="mutual"
    )
    assert union_info["symmetrization"] == "union_maximum"
    assert mutual_info["symmetrization"] == "mutual_and"
    assert np.allclose(union, shared_union.toarray())
    assert np.allclose(mutual, shared_mutual.toarray())
    assert np.count_nonzero(union) > np.count_nonzero(mutual)
