"""Fit representations and cluster them. Labels are evaluation-only."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse

from baselines.lda_kmeans import fit_predict as lda_kmeans_fit_predict
from baselines.lda_spectral import fit_predict as lda_spectral_fit_predict
from baselines.llc import local_regression_matrix, yu_shi_discretize
from baselines.spls import fit_predict as spls_fit_predict
from benchmarks.metrics import clustering_accuracy, normalized_mutual_information
from experiments.perturbations import drop_affinity_edges
from method_extension.mutual_knn import mutual_knn_affinity
from SSC_method.graph_construction import combinatorial_laplacian, knn_affinity
from SSC_method.objective import equation8_objective
from SSC_method.optimizer import shrink_embedding, variant_laplacian_coefficient
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import smallest_eigenpairs, spectral_embedding
from experiments.repair_diagnostics import (
    augment_objective_history,
    edge_jaccard,
    eigenvalue_summary,
    graph_summary,
    label_disagreement,
    make_g_init,
    undirected_edge_set,
)


@dataclass
class PreparedRepresentation:
    name: str
    features: np.ndarray
    extra: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    cluster_fn: str = "kmeans_on_features"
    embedding: np.ndarray | None = None
    shrunk: np.ndarray | None = None
    kmeans_init: str = "random"


def _kmeans_labels(
    features: np.ndarray,
    n_clusters: int,
    seed: int,
    init: str = "random",
) -> tuple[np.ndarray, float]:
    from sklearn.cluster import KMeans

    model = KMeans(
        n_clusters=n_clusters,
        init=init,
        n_init=1,
        random_state=int(seed),
        algorithm="lloyd",
    )
    labels = model.fit_predict(features)
    return np.asarray(labels, dtype=np.int64), float(model.inertia_)


def prepare_ssc_family(
    X: np.ndarray,
    n_clusters: int,
    gamma: float,
    k: int,
    mutual: bool,
    graph_drop: dict | None = None,
    max_iter: int = 300,
    tol: float = 1e-6,
    variant: str = "E13",
    cluster_on: str = "G",
    bandwidth_rule: str | None = None,
    row_normalize: bool = False,
    g_init: str = "F",
    g_init_seed: int = 0,
    g_init_scale: float = 1e-3,
    zero_residual_floor: str | float = "median_pairwise",
    kmeans_init: str = "random",
    embedding_delta2: float | None = None,
    delta2: float | None = None,
    eps: float = 1e-8,
    symmetrization: str = "union",
    laplacian: str = "symmetric_normalized_eq4",
    knn_method: str = "auto",
    dense_threshold: int = 512,
    graph_config: SpectralGraphConfig | None = None,
) -> PreparedRepresentation:
    variant_name = str(variant)
    laplacian_coefficient = variant_laplacian_coefficient(variant_name)
    cluster_target = str(cluster_on).upper()
    if cluster_target not in {"F", "G"}:
        raise ValueError("cluster_on must be F or G")
    if graph_config is None:
        graph_config = SpectralGraphConfig(
            k=k,
            delta2=embedding_delta2,
            bandwidth_rule=bandwidth_rule,
            symmetrization=symmetrization,
            laplacian=laplacian,
            row_normalize=bool(row_normalize),
            knn_method=knn_method,
            dense_threshold=int(dense_threshold),
            variant=variant_name,
            g_init=str(g_init),
            g_init_seed=int(g_init_seed),
            g_init_scale=float(g_init_scale),
            zero_residual_floor=zero_residual_floor,
            tol=float(tol),
            max_iter=int(max_iter),
            eps=float(eps),
            kmeans_init=str(kmeans_init),
        )
    t0 = time.perf_counter()
    embedding, embed_info = spectral_embedding(
        X,
        n_components=n_clusters,
        config=graph_config,
    )
    t_embed = time.perf_counter() - t0
    if mutual:
        affinity, graph_info = mutual_knn_affinity(embedding, k=k)
        ablation = "A1_mutual_knn"
        # Mutual kNN stays in the extension package, not in SSC_method.
        x_affinity, x_graph = knn_affinity(X, config=graph_config)
    else:
        affinity, graph_info = knn_affinity(
            embedding,
            k=graph_config.k,
            delta2=delta2,
            bandwidth_rule=bandwidth_rule,
            knn_method=graph_config.knn_method,
            symmetrization=graph_config.symmetrization,
        )
        ablation = "A0_union_knn"
        x_affinity, x_graph = knn_affinity(X, config=graph_config)
    if graph_drop:
        affinity = drop_affinity_edges(
            affinity, float(graph_drop["level"]), int(graph_drop.get("seed", 0))
        )
        graph_info = dict(graph_info)
        graph_info["graph_drop_fraction"] = float(graph_drop["level"])
        graph_info["graph_drop_seed"] = int(graph_drop.get("seed", 0))
        graph_info["n_edges_after_drop"] = int(sparse.csr_matrix(affinity).nnz // 2)
    w_on_f = undirected_edge_set(affinity)
    a_on_x = undirected_edge_set(x_affinity)
    w_overlap = {
        "w_built_on": "F",
        "x_graph_n_undirected_edges": len(a_on_x),
        "f_graph_n_undirected_edges": len(w_on_f),
        "edge_intersection": len(w_on_f & a_on_x),
        "edge_jaccard": edge_jaccard(w_on_f, a_on_x),
        "identical_to_x_graph": w_on_f == a_on_x,
    }
    g0, g0_name = make_g_init(
        embedding, mode=str(g_init), seed=int(g_init_seed), scale=float(g_init_scale)
    )
    t1 = time.perf_counter()
    shrinkage = shrink_embedding(
        embedding,
        affinity,
        gamma=float(gamma),
        eps=float(eps),
        max_iter=int(max_iter),
        tol=float(tol),
        G_init=g0,
        zero_residual_floor=zero_residual_floor,
        variant=variant_name,
    )
    t_irls = time.perf_counter() - t1
    history = augment_objective_history(list(shrinkage.history))
    last = history[-1] if history else {}
    shrinkage_graph_stats = graph_summary(affinity)
    x_graph_stats = graph_summary(x_affinity)
    try:
        comb_evals, _vecs, _solver = smallest_eigenpairs(
            combinatorial_laplacian(affinity), min(6, affinity.shape[0])
        )
        comb_eigs = eigenvalue_summary(comb_evals)
        comb_eigs["solver"] = _solver
    except Exception as exc:  # noqa: BLE001 - diagnostic must not abort a solved F,G
        comb_eigs = {
            "status": "FAILED",
            "reason": f"{type(exc).__name__}: {exc}",
            "note": "combinatorial Laplacian eigenpairs are a post-solve diagnostic, not the SSC embedding",
        }
    g_minus_f = float(np.linalg.norm(shrinkage.patterns - embedding))
    exact_obj = equation8_objective(shrinkage.patterns, embedding, affinity, float(gamma))
    features = embedding if cluster_target == "F" else shrinkage.patterns
    linear_update = "equation_13" if variant_name == "E13" else "equation_8_stationary"
    extra = {
        "embedding_info": {
            "eigen_solver": embed_info["eigen_solver"],
            "graph": embed_info["graph"],
            "row_normalize": bool(embed_info.get("row_normalize", False)),
            "sign_convention": embed_info.get("sign_convention"),
            "laplacian": embed_info.get("laplacian"),
            "shared_eq4_path": True,
            "eigenvalues_summary": eigenvalue_summary(embed_info["eigenvalues"]),
        },
        "spectral_graph_config": graph_config.to_dict(),
        "shrinkage_graph": graph_info,
        "shrinkage_graph_stats": shrinkage_graph_stats,
        "x_graph_stats": x_graph_stats,
        "x_graph_info": x_graph,
        "w_vs_x_overlap": w_overlap,
        "combinatorial_laplacian_eigenvalues_W": comb_eigs,
        "n_irls_iterations": shrinkage.n_iterations,
        "irls_converged": bool(shrinkage.converged),
        "fixed_point_residual": shrinkage.fixed_point_residual,
        "linear_residual_last": last.get("linear_residual"),
        "relative_obj_change_last": last.get("relative_obj_change"),
        "relative_iterate_change_last": last.get("relative_iterate_change"),
        "step_frobenius_last": last.get("step_frobenius"),
        "equation8_objective": exact_obj,
        "sqrt_smoothed_equation8_objective": last.get("sqrt_smoothed_equation8_objective"),
        "irls_quadratic_surrogate": last.get("irls_quadratic_surrogate"),
        "g_minus_f_frobenius": g_minus_f,
        "initial_zero_residual_floor": shrinkage.initial_zero_residual_floor,
        "zero_residual_floor": zero_residual_floor,
        "g0": g0_name,
        "g_init_seed": int(g_init_seed),
        "g_init_scale": float(g_init_scale),
        "variant": variant_name,
        "laplacian_coefficient": laplacian_coefficient,
        "linear_update": linear_update,
        "eq13_graph_coefficient": "gamma" if variant_name == "E13" else "2_gamma",
        "eq8_graph_term_correspondence": "gamma_over_2" if variant_name == "E13" else "printed_equation_8",
        "cluster_on": cluster_target,
        "kmeans_init": str(kmeans_init),
        "protocol": "R1_solve_FG_once",
        "ablation": ablation,
        "weights_frozen_before_irls": True,
        "runtime_embedding_seconds": t_embed,
        "runtime_irls_seconds": t_irls,
        "max_iter": int(max_iter),
        "tol": float(tol),
        "eps": float(eps),
        "bandwidth_rule": graph_info.get("bandwidth_rule") or bandwidth_rule,
        "row_normalize": bool(row_normalize),
    }
    return PreparedRepresentation(
        name="rssc" if mutual else "ssc",
        features=np.asarray(features, dtype=np.float64),
        extra=extra,
        history=history,
        cluster_fn="kmeans_on_features",
        embedding=np.asarray(embedding, dtype=np.float64),
        shrunk=np.asarray(shrinkage.patterns, dtype=np.float64),
        kmeans_init=str(kmeans_init),
    )


def prepare_spectral(
    X: np.ndarray,
    n_clusters: int,
    k: int,
    *,
    graph_config: SpectralGraphConfig | None = None,
    bandwidth_rule: str | None = None,
    row_normalize: bool = False,
    embedding_delta2: float | None = None,
    symmetrization: str = "union",
    laplacian: str = "symmetric_normalized_eq4",
    knn_method: str = "auto",
    dense_threshold: int = 512,
    kmeans_init: str = "random",
) -> PreparedRepresentation:
    """Eq. (4) embedding on the shared SC/SSC path.

    There is no ``n > 1500`` backend switch. Spectral clustering and SSC
    must use this same F before shrinkage is evaluated.
    """
    if graph_config is None:
        graph_config = SpectralGraphConfig(
            k=k,
            delta2=embedding_delta2,
            bandwidth_rule=bandwidth_rule,
            symmetrization=symmetrization,
            laplacian=laplacian,
            row_normalize=bool(row_normalize),
            knn_method=knn_method,
            dense_threshold=int(dense_threshold),
            kmeans_init=str(kmeans_init),
        )
    t0 = time.perf_counter()
    embedding, info = spectral_embedding(
        X, n_components=n_clusters, config=graph_config
    )
    graph_stats = {
        "n_connected_components": info.get("n_connected_components"),
        "n_undirected_edges": info.get("n_undirected_edges"),
        "degree_min": info.get("degree_min"),
        "degree_mean": info.get("degree_mean"),
        "degree_max": info.get("degree_max"),
    }
    extra = {
        "spectral_backend": "shared_eq4",
        "eigen_solver": info["eigen_solver"],
        "graph": info["graph"],
        "graph_stats": graph_stats,
        "eigenvalues_summary": eigenvalue_summary(info["eigenvalues"]),
        "n_undirected_edges": info.get("n_undirected_edges"),
        "n_connected_components": info.get("n_connected_components"),
        "row_normalize": bool(info.get("row_normalize", False)),
        "sign_convention": info.get("sign_convention"),
        "laplacian": info.get("laplacian"),
        "shared_eq4_path": True,
        "spectral_graph_config": graph_config.to_dict(),
        "runtime_embedding_seconds": time.perf_counter() - t0,
    }
    if X.shape[0] <= 1500:
        affinity, _graph = knn_affinity(X, config=graph_config)
        try:
            comb_evals, _vecs, _solver = smallest_eigenpairs(
                combinatorial_laplacian(affinity), min(8, affinity.shape[0])
            )
            comb = eigenvalue_summary(comb_evals)
            comb["solver"] = _solver
            extra["combinatorial_laplacian_eigenvalues_A"] = comb
        except Exception as exc:  # noqa: BLE001 - diagnostic must not abort F
            extra["combinatorial_laplacian_eigenvalues_A"] = {
                "status": "FAILED",
                "reason": f"{type(exc).__name__}: {exc}",
                "note": "combinatorial Laplacian eigenpairs are a post-embedding diagnostic, not the SC embedding",
            }
    else:
        extra["combinatorial_laplacian_eigenvalues_A"] = {
            "status": "SKIPPED",
            "reason": "n>1500; combinatorial eigenpairs recorded only on small-n D5 diagnostics",
        }
    return PreparedRepresentation(
        name="sc",
        features=np.asarray(embedding, dtype=np.float64),
        extra=extra,
        cluster_fn="kmeans_on_features",
        embedding=np.asarray(embedding, dtype=np.float64),
        kmeans_init=str(graph_config.kmeans_init),
    )


def prepare_pca(X: np.ndarray, n_components: int) -> np.ndarray:
    from sklearn.decomposition import PCA

    projector = PCA(n_components=n_components, svd_solver="full")
    return np.asarray(projector.fit_transform(X), dtype=np.float64)


def prepare_llc_embedding(
    X: np.ndarray, n_clusters: int, k: int
) -> PreparedRepresentation:
    t0 = time.perf_counter()
    regression = local_regression_matrix(
        X, n_neighbors=k, reg=1.0, kernel="gaussian", gamma=None
    )
    residual = np.eye(X.shape[0], dtype=np.float64) - regression
    gram = residual.T @ residual
    gram = 0.5 * (gram + gram.T)
    _values, vectors = np.linalg.eigh(gram)
    raw = vectors[:, :n_clusters]
    row_norm = np.linalg.norm(raw, axis=1, keepdims=True)
    normalized = raw / np.maximum(row_norm, 1e-12)
    extra = {
        "llc_reg": 1.0,
        "llc_kernel": "gaussian",
        "runtime_embedding_seconds": time.perf_counter() - t0,
    }
    return PreparedRepresentation(
        name="llc",
        features=normalized,
        extra=extra,
        cluster_fn="llc_yushi",
    )


def cluster_prepared(
    prepared: PreparedRepresentation,
    n_clusters: int,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    if prepared.cluster_fn == "kmeans_on_features":
        init = prepared.kmeans_init or "random"
        labels, inertia = _kmeans_labels(prepared.features, n_clusters, seed, init=init)
        trial_extra: dict[str, Any] = {"kmeans_inertia": inertia, "kmeans_init": init}
        if prepared.embedding is not None and prepared.shrunk is not None:
            labels_f, inertia_f = _kmeans_labels(
                prepared.embedding, n_clusters, seed, init=init
            )
            labels_g, inertia_g = _kmeans_labels(
                prepared.shrunk, n_clusters, seed, init=init
            )
            trial_extra["kmeans_inertia_F"] = inertia_f
            trial_extra["kmeans_inertia_G"] = inertia_g
            trial_extra["label_disagreement_F_G"] = label_disagreement(labels_f, labels_g)
            trial_extra["aligned_agreement_F_G"] = clustering_accuracy(labels_f, labels_g)
        return labels, trial_extra
    if prepared.cluster_fn == "llc_yushi":
        labels = yu_shi_discretize(
            prepared.features, random_state=seed, max_iter=30, tol=1e-8
        )
        return np.asarray(labels, dtype=np.int64), {"discretization": "yu_shi"}
    raise ValueError(prepared.cluster_fn)


def run_stateless_method(
    method: str,
    X: np.ndarray,
    n_clusters: int,
    seed: int,
    params: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Methods whose representation is not cached across trials."""
    k = int(params.get("k", 5))
    if method == "kmeans":
        init = str(params.get("init", params.get("kmeans_init", "random")))
        labels, inertia = _kmeans_labels(X, n_clusters, seed, init=init)
        return labels, {"kmeans_inertia": inertia, "kmeans_init": init}
    if method == "lda_kmeans":
        n_components = int(params["n_components"])
        labels = lda_kmeans_fit_predict(
            X, n_clusters, seed, n_components=n_components, n_init=1, init="random"
        )
        return labels, {"n_components": n_components}
    if method == "lda_spectral":
        n_components = int(params["n_components"])
        labels = lda_spectral_fit_predict(
            X,
            n_clusters,
            seed,
            n_components=n_components,
            n_neighbors=k,
            n_init=1,
            init="random",
        )
        return labels, {"n_components": n_components, "implementation_status": "APPROXIMATE"}
    if method == "spls":
        labels = spls_fit_predict(X, n_clusters, seed)
        return labels, {}
    raise KeyError(method)


CACHEABLE = {"ssc", "rssc", "sc", "llc", "pca_kmeans", "pca_spectral"}
STATELESS = {"kmeans", "lda_kmeans", "lda_spectral", "spls"}


def prepare_method(
    method: str,
    X: np.ndarray,
    n_clusters: int,
    params: dict[str, Any],
    perturbation: dict | None = None,
) -> PreparedRepresentation | None:
    if method not in CACHEABLE:
        return None
    k = int(params.get("k", 5))
    if method == "llc":
        return prepare_llc_embedding(X, n_clusters, k)
    if method == "pca_kmeans":
        n_components = int(params["n_components"])
        init = str(params.get("init", params.get("kmeans_init", "random")))
        features = prepare_pca(X, n_components)
        return PreparedRepresentation(
            name="pca_kmeans",
            features=np.asarray(features, dtype=np.float64),
            extra={
                "n_components": n_components,
                "pca_solver": "full",
                "kmeans_init": init,
                "protocol": "pca_once_then_kmeans_trials",
            },
            cluster_fn="kmeans_on_features",
            kmeans_init=init,
        )
    graph_config = SpectralGraphConfig.from_params(params, k=k, for_embedding=True)
    if method == "pca_spectral":
        n_components = int(params["n_components"])
        projected = prepare_pca(X, n_components)
        prepared = prepare_spectral(X=projected, n_clusters=n_clusters, k=k, graph_config=graph_config)
        prepared.name = "pca_spectral"
        prepared.extra = dict(prepared.extra)
        prepared.extra["n_components"] = n_components
        prepared.extra["pca_solver"] = "full"
        prepared.extra["protocol"] = "pca_once_then_shared_eq4_F_then_kmeans"
        return prepared
    if method == "sc":
        return prepare_spectral(X, n_clusters, k, graph_config=graph_config)
    gamma = float(params.get("gamma", 1.0))
    graph_drop = perturbation if perturbation and perturbation.get("type") == "graph_drop" else None
    return prepare_ssc_family(
        X,
        n_clusters=n_clusters,
        gamma=gamma,
        k=k,
        mutual=(method == "rssc"),
        graph_drop=graph_drop,
        max_iter=int(params.get("max_iter", graph_config.max_iter)),
        tol=float(params.get("tol", graph_config.tol)),
        variant=str(params.get("variant", graph_config.variant)),
        cluster_on=str(params.get("cluster_on", "G")),
        bandwidth_rule=params.get("bandwidth_rule"),
        row_normalize=bool(params.get("row_normalize", False)),
        g_init=str(params.get("g_init", graph_config.g_init)),
        g_init_seed=int(params.get("g_init_seed", graph_config.g_init_seed)),
        g_init_scale=float(params.get("g_init_scale", graph_config.g_init_scale)),
        zero_residual_floor=params.get("zero_residual_floor", graph_config.zero_residual_floor),
        kmeans_init=str(params.get("kmeans_init", graph_config.kmeans_init)),
        embedding_delta2=params.get("embedding_delta2"),
        delta2=params.get("delta2"),
        eps=float(params.get("eps", graph_config.eps)),
        graph_config=graph_config,
    )


def evaluate_labels(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    pred = np.asarray(y_pred).reshape(-1)
    truth = np.asarray(y_true).reshape(-1)
    acc = clustering_accuracy(truth, pred)
    nmi = normalized_mutual_information(truth, pred)
    if not (0.0 <= acc <= 1.0 and 0.0 <= nmi <= 1.0):
        raise RuntimeError(f"metric out of [0,1]: ACC={acc} NMI={nmi}")
    if pred.shape[0] != truth.shape[0]:
        raise RuntimeError("label length mismatch")
    return {
        "acc": float(acc),
        "nmi": float(nmi),
        "n_predicted_labels": int(pred.shape[0]),
        "n_unique_predicted": int(np.unique(pred).size),
    }
