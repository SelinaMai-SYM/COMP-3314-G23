"""SC and SSC share one E8 upstream. Gamma does not rebuild F."""

from __future__ import annotations

import numpy as np

from SSC_method.spectral_config import SpectralGraphConfig
from experiments.methods import prepare_ssc_family
from experiments.v2_kmeans_protocol.kmeans_trials import sha256_array
from experiments.v2_kmeans_protocol.representation_cache import (
    compute_embedding,
    compute_fg,
    upstream_config,
    variant_laplacian_coefficient,
)


def test_campaign_contract_is_e8() -> None:
    config = upstream_config(1.0)
    assert config["variant"] == "E8"
    assert config["laplacian_coefficient"] == 2.0
    assert variant_laplacian_coefficient("E8") == 2.0
    assert config["g_init"] == "F"
    assert config["k"] == 5
    assert config["max_iter"] == 300


def test_same_f_and_g_as_prepare_ssc_family() -> None:
    rng = np.random.default_rng(11)
    features = rng.normal(size=(36, 6))
    params = {
        "k": 5,
        "gamma": 0.5,
        "max_iter": 4,
        "tol": 1e-6,
        "variant": "E8",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "row_normalize": False,
        "g_init": "F",
        "g_init_seed": 0,
        "g_init_scale": 1e-3,
        "zero_residual_floor": "median_pairwise",
        "kmeans_init": "random",
        "n_init": 1,
        "eps": 1e-8,
        "symmetrization": "union",
        "laplacian": "symmetric_normalized_eq4",
    }
    graph = SpectralGraphConfig.from_params(params, k=5, for_embedding=True)
    prepared = prepare_ssc_family(
        features,
        n_clusters=3,
        gamma=0.5,
        k=5,
        mutual=False,
        max_iter=4,
        tol=1e-6,
        variant="E8",
        cluster_on="G",
        bandwidth_rule=params["bandwidth_rule"],
        row_normalize=False,
        g_init="F",
        zero_residual_floor="median_pairwise",
        eps=1e-8,
        symmetrization="union",
        laplacian="symmetric_normalized_eq4",
        graph_config=graph,
    )
    ours = compute_fg(features, 3, 0.5, max_iter=4)
    assert np.allclose(ours.embedding, prepared.embedding, atol=0.0, rtol=0.0)
    assert np.allclose(ours.patterns, prepared.shrunk, atol=1e-10, rtol=1e-8)
    assert ours.solver_status.startswith("CONVERGED") or "NONCONVERGED_RETURNED_ITERATE" in ours.solver_status


def test_gamma_does_not_change_f() -> None:
    features = np.random.default_rng(3).normal(size=(28, 5))
    embedding, _graph, _seconds = compute_embedding(features, 3, max_iter=3)
    low = compute_fg(features, 3, 1e-6, max_iter=3, embedding=embedding)
    high = compute_fg(features, 3, 1e3, max_iter=3, embedding=embedding)
    assert low.f_sha256 == high.f_sha256 == sha256_array(embedding)
    assert low.g_sha256 != high.g_sha256
