"""Tests for the mutual-kNN shrinkage graph (extension only)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from method_extension.mutual_knn import mutual_knn_affinity
from method_extension.rssc import ReliabilityAwareSSC
from SSC_method.graph_construction import knn_affinity


def _asymmetric_points() -> np.ndarray:
    """Five points where 0 lists 1 as a neighbor but 1 does not list 0 when k=1."""
    return np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [1.1, 0.0],
            [10.0, 0.0],
            [10.2, 0.0],
        ],
        dtype=np.float64,
    )


def test_mutual_affinity_is_symmetric_and_nonnegative():
    rng = np.random.default_rng(2)
    features = rng.normal(size=(18, 4))
    affinity, info = mutual_knn_affinity(features, k=3)
    dense = affinity.toarray()
    assert np.allclose(dense, dense.T, atol=1e-12)
    assert np.all(affinity.data >= 0.0)
    assert np.allclose(affinity.diagonal(), 0.0)
    assert info["symmetrization"] == "mutual_and"


def test_mutual_has_fewer_or_equal_edges_than_union():
    points = _asymmetric_points()
    union, _ = knn_affinity(points, k=1)
    mutual, info = mutual_knn_affinity(points, k=1)
    assert mutual.nnz <= union.nnz
    assert info["n_mutual_undirected_edges"] <= info["n_union_undirected_edges"]
    # Point 0's unique 1-NN is 1; point 1's unique 1-NN is 2. Union keeps 0-1; mutual does not.
    assert union[0, 1] > 0.0
    assert mutual[0, 1] == 0.0
    assert mutual[1, 2] > 0.0
    assert union[1, 2] > 0.0


def test_mutual_equals_union_when_directed_knn_is_already_symmetric():
    points = np.array([[0.0], [0.1], [10.0], [10.1]])
    union, _ = knn_affinity(points, k=1)
    mutual, _ = mutual_knn_affinity(points, k=1)
    assert np.allclose(union.toarray(), mutual.toarray())
    assert mutual[0, 1] > 0.0
    assert mutual[2, 3] > 0.0
    assert mutual[0, 2] == 0.0


def test_rssc_runs_and_uses_mutual_graph():
    rng = np.random.default_rng(0)
    x = np.vstack(
        [
            rng.normal(loc=0.0, scale=0.1, size=(8, 3)),
            rng.normal(loc=3.0, scale=0.1, size=(8, 3)),
        ]
    )
    model = ReliabilityAwareSSC(n_clusters=2, gamma=1.0, k=3, kmeans_n_init=1, kmeans_random_state=0)
    labels = model.fit_predict(x)
    assert labels.shape == (16,)
    assert model.info_["ablation"] == "A1_mutual_knn_shrinkage_weights"
    assert model.info_["linear_update"] == "equation_13"
    assert model.info_["shrinkage_graph"]["symmetrization"] == "mutual_and"
    assert sparse.issparse(model.affinity_)
    assert np.allclose((model.affinity_ - model.affinity_.T).toarray(), 0.0)
    assert np.all(model.affinity_.data >= 0.0)
