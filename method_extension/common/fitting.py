"""Fit one extension. ``y`` is accepted and discarded."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse

from SSC_method.graph_construction import knn_affinity
from SSC_method.objective import graph_l2_term
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from method_extension.common.graphs import (
    apply_probability,
    bilateral_support,
    degree_normalize,
    fuse_affinities,
    local_reliability_alpha,
    recurrence_probability,
    total_edge_normalize,
)
from method_extension.common.irls import MATCH_ATOL, MATCH_RTOL, shrink_embedding_alpha


@dataclass
class ExtensionConfig:
    """Frozen settings. Nothing here is chosen by test accuracy."""

    k: int = 5
    eps: float = 1e-8
    tol: float = 1e-6
    max_iter: int = 300
    zero_residual_floor: str = "median_pairwise"
    variant: str = "E8"
    n_perturbations: int = 10
    beta: float = 1.0
    noise_rel: float = 0.02
    noise_seed: int = 20260311
    alpha_min: float = 0.5
    alpha_max: float = 2.0
    degree_eps: float = 1e-12
    fuse_lambda: float = 0.5
    n_outer: int = 3
    solver: str = "auto"


@dataclass
class FitState:
    method: str
    variant: str
    embedding: np.ndarray
    patterns: np.ndarray
    affinity: sparse.csr_matrix
    objective_name: str
    objective_value: float
    equation8_value: float
    n_iterations: int
    converged: bool
    fixed_point_residual: float
    solver: str
    f_source: str
    info: dict[str, Any] = field(default_factory=dict)

    @property
    def relative_move(self) -> float:
        denom = float(np.linalg.norm(self.embedding))
        return float(np.linalg.norm(self.patterns - self.embedding) / max(denom, 1e-12))

    @property
    def graph_total_variation(self) -> float:
        return graph_l2_term(self.patterns, self.affinity)


def _as_features(X: np.ndarray) -> np.ndarray:
    features = np.asarray(X, dtype=np.float64)
    if features.ndim != 2 or features.shape[0] < 2 or features.shape[1] < 1:
        raise ValueError("X must have shape (n_samples >= 2, n_features >= 1)")
    if not np.isfinite(features).all():
        raise ValueError("X contains non-finite values")
    return features


def embed_matrix(
    features: np.ndarray,
    n_clusters: int,
    config: ExtensionConfig,
    bandwidth_rule: str | None = None,
    symmetrization: str = "union",
    row_normalize: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    graph = SpectralGraphConfig(
        k=int(config.k),
        bandwidth_rule=bandwidth_rule,
        symmetrization=symmetrization,
        row_normalize=bool(row_normalize),
        variant="E8",
        g_init="F",
        zero_residual_floor=config.zero_residual_floor,
        tol=float(config.tol),
        max_iter=int(config.max_iter),
        eps=float(config.eps),
    )
    return spectral_embedding(features, n_components=int(n_clusters), config=graph)


def standard_affinity(
    embedding: np.ndarray,
    config: ExtensionConfig,
    bandwidth_rule: str | None = None,
    symmetrization: str = "union",
) -> tuple[sparse.csr_matrix, dict[str, Any]]:
    affinity, info = knn_affinity(
        embedding,
        k=int(config.k),
        bandwidth_rule=bandwidth_rule,
        symmetrization=symmetrization,
    )
    return affinity, info


def _shrink(embedding, affinity, alpha, gamma, config: ExtensionConfig, g_init=None):
    return shrink_embedding_alpha(
        embedding,
        affinity,
        alpha=alpha,
        gamma=float(gamma),
        eps=float(config.eps),
        tol=float(config.tol),
        max_iter=int(config.max_iter),
        G_init=embedding if g_init is None else g_init,
        zero_residual_floor=config.zero_residual_floor,
        variant=config.variant,
        solver=config.solver,
    )


def _state(method, variant, embedding, affinity, result, f_source, info) -> FitState:
    return FitState(
        method=method,
        variant=variant,
        embedding=np.asarray(embedding, dtype=np.float64),
        patterns=np.asarray(result.patterns, dtype=np.float64),
        affinity=sparse.csr_matrix(affinity),
        objective_name=result.objective_name,
        objective_value=float(result.objective_value),
        equation8_value=float(result.equation8_value),
        n_iterations=int(result.n_iterations),
        converged=bool(result.converged),
        fixed_point_residual=float(result.fixed_point_residual),
        solver=str(result.solver),
        f_source=f_source,
        info=info,
    )


def _control_embedding(features, n_clusters, config, embedding):
    if embedding is not None:
        return np.asarray(embedding, dtype=np.float64), "provided"
    embedded, _info = embed_matrix(features, n_clusters, config)
    return embedded, "control_eq4"


def fit_named_method(
    method: str,
    features: np.ndarray,
    n_clusters: int,
    gamma: float = 1.0,
    variant: str = "default",
    config: ExtensionConfig | None = None,
    embedding: np.ndarray | None = None,
    embedding_override: np.ndarray | None = None,
    y: np.ndarray | None = None,
) -> FitState:
    """Fit one named extension. ``y`` is ignored."""
    del y
    features = _as_features(features)
    config = config or ExtensionConfig()
    if int(n_clusters) > features.shape[0]:
        raise ValueError("n_clusters cannot exceed n_samples")
    name = str(method).lower()
    which = str(variant)
    if embedding_override is not None:
        embedding = np.asarray(embedding_override, dtype=np.float64)

    if name in {"ssc", "ssc_e8", "control"}:
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        affinity, graph_info = standard_affinity(embedded, config)
        result = _shrink(embedded, affinity, None, gamma, config)
        return _state(
            "SSC_E8",
            "control",
            embedded,
            affinity,
            result,
            source,
            {"graph": graph_info, "reduces_to_e8": True, "match_atol": MATCH_ATOL, "match_rtol": MATCH_RTOL},
        )

    if name == "e01":
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        affinity, _graph = standard_affinity(embedded, config)
        probability = recurrence_probability(
            embedded,
            k=config.k,
            n_perturbations=config.n_perturbations,
            noise_rel=config.noise_rel,
            seed=config.noise_seed,
        )
        reweighted = apply_probability(affinity, probability, beta=config.beta)
        result = _shrink(embedded, reweighted, None, gamma, config)
        return _state(
            "E01",
            "edge_recurrence",
            embedded,
            reweighted,
            result,
            source,
            {"beta": config.beta, "T": config.n_perturbations, "noise_rel": config.noise_rel, "changes": "W_only"},
        )

    if name == "e02":
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        affinity, _graph = standard_affinity(embedded, config)
        alpha = local_reliability_alpha(embedded, k=config.k, alpha_min=config.alpha_min, alpha_max=config.alpha_max)
        result = _shrink(embedded, affinity, alpha, gamma, config)
        return _state(
            "E02",
            "local_reliability",
            embedded,
            affinity,
            result,
            source,
            {
                "alpha_min_value": float(alpha.min()),
                "alpha_max_value": float(alpha.max()),
                "alpha_mean": float(alpha.mean()),
                "changes": "objective_weights_only",
            },
        )

    if name == "e03":
        which = which.upper()
        if which not in {"A", "W", "AW"}:
            raise ValueError("E03 variant must be A, W, or AW")
        bandwidth = "self_tuning_zelnik_manor"
        if which in {"A", "AW"} and embedding_override is None:
            embedded, embed_info = embed_matrix(features, n_clusters, config, bandwidth_rule=bandwidth)
            source = "local_scale_on_A"
        elif which in {"A", "AW"}:
            embedded, embed_info = embedding, {}
            source = "local_scale_on_A_override"
        else:
            embedded, source = _control_embedding(features, n_clusters, config, embedding)
            embed_info = {}
        if which in {"W", "AW"}:
            affinity, graph_info = standard_affinity(embedded, config, bandwidth_rule=bandwidth)
        else:
            affinity, graph_info = standard_affinity(embedded, config)
        result = _shrink(embedded, affinity, None, gamma, config)
        return _state(
            "E03",
            which,
            embedded,
            affinity,
            result,
            source,
            {"local_scale_target": which, "graph": graph_info, "embed": embed_info, "changes": f"local_scale_{which}"},
        )

    if name == "e04":
        which = which.lower()
        if which not in {"degree", "total"}:
            raise ValueError("E04 variant must be degree or total")
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        affinity, _graph = standard_affinity(embedded, config)
        extra: dict[str, Any] = {"changes": "W_only"}
        if which == "degree":
            reweighted = degree_normalize(affinity, eps=config.degree_eps)
            extra["degree_eps"] = config.degree_eps
        else:
            reweighted, scale_info = total_edge_normalize(affinity)
            extra.update(scale_info)
        result = _shrink(embedded, reweighted, None, gamma, config)
        return _state("E04", which, embedded, reweighted, result, source, extra)

    if name == "e05":
        which = which.lower()
        if which not in {"fuse", "bilateral"}:
            raise ValueError("E05 variant must be fuse or bilateral")
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        affinity_f, _graph_f = standard_affinity(embedded, config)
        affinity_x, _graph_x = standard_affinity(features, config)
        if which == "fuse":
            affinity = fuse_affinities(affinity_f, affinity_x, mix=config.fuse_lambda)
            extra = {"fuse_lambda": config.fuse_lambda, "pixel_graph_assumed_reliable": False}
        else:
            affinity = bilateral_support(affinity_f, affinity_x)
            extra = {"pixel_graph_assumed_reliable": False}
        result = _shrink(embedded, affinity, None, gamma, config)
        return _state("E05", which, embedded, affinity, result, source, extra)

    if name == "e06":
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        patterns_init = embedded
        representation = embedded
        result = None
        affinity = None
        outers = []
        for outer in range(int(config.n_outer)):
            affinity, _graph = standard_affinity(representation, config)
            result = _shrink(embedded, affinity, None, gamma, config, g_init=patterns_init)
            patterns_init = result.patterns
            representation = result.patterns
            outers.append(
                {
                    "outer": outer,
                    "converged": bool(result.converged),
                    "n_iterations": int(result.n_iterations),
                    "objective_value": float(result.objective_value),
                }
            )
        assert result is not None and affinity is not None
        return _state(
            "E06",
            "alternating",
            embedded,
            affinity,
            result,
            source,
            {
                "n_outer": int(config.n_outer),
                "outers": outers,
                "global_convergence_claimed": False,
                "each_frozen_W_subproblem_convex": True,
            },
        )

    if name == "e08":
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        affinity, _graph = standard_affinity(embedded, config)
        probability = recurrence_probability(
            embedded, k=config.k, n_perturbations=config.n_perturbations, noise_rel=config.noise_rel, seed=config.noise_seed
        )
        reweighted = apply_probability(affinity, probability, beta=config.beta)
        alpha = local_reliability_alpha(embedded, k=config.k, alpha_min=config.alpha_min, alpha_max=config.alpha_max)
        result = _shrink(embedded, reweighted, alpha, gamma, config)
        return _state(
            "E08",
            "recurrence_and_alpha",
            embedded,
            reweighted,
            result,
            source,
            {"weights_fixed_during_optimization": True, "ablation": ["SSC_E8", "E01", "E02"]},
        )

    if name == "e09":
        embedded, source = _control_embedding(features, n_clusters, config, embedding)
        local_w, _graph = standard_affinity(embedded, config, bandwidth_rule="self_tuning_zelnik_manor")
        probability = recurrence_probability(
            embedded, k=config.k, n_perturbations=config.n_perturbations, noise_rel=config.noise_rel, seed=config.noise_seed
        )
        reweighted = apply_probability(local_w, probability, beta=config.beta)
        result = _shrink(embedded, reweighted, None, gamma, config)
        return _state(
            "E09",
            "recurrence_and_E03W",
            embedded,
            reweighted,
            result,
            source,
            {"initial_F_shared_with_control": source != "local_scale_on_A", "ablation": ["SSC_E8", "E01", "E03-W"]},
        )

    raise ValueError(f"unknown method {method}")
