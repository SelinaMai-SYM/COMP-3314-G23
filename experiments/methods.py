"""Fit representations and cluster them. Labels are evaluation-only."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse

from baselines.kmeans import fit_predict as kmeans_fit_predict
from baselines.lda_kmeans import fit_predict as lda_kmeans_fit_predict
from baselines.lda_spectral import fit_predict as lda_spectral_fit_predict
from baselines.llc import local_regression_matrix, yu_shi_discretize
from baselines.pca_kmeans import fit_predict as pca_kmeans_fit_predict
from baselines.pca_spectral import fit_predict as pca_spectral_fit_predict
from baselines.spectral_clustering import spectral_embedding as sc_spectral_embedding
from baselines.spls import fit_predict as spls_fit_predict
from benchmarks.metrics import clustering_accuracy, normalized_mutual_information
from experiments.perturbations import drop_affinity_edges
from method_extension.mutual_knn import mutual_knn_affinity
from SSC_method.graph_construction import knn_affinity
from SSC_method.optimizer import shrink_embedding
from SSC_method.spectral_embedding import spectral_embedding


@dataclass
class PreparedRepresentation:
    name: str
    features: np.ndarray
    extra: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    cluster_fn: str = "kmeans_on_features"


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
) -> PreparedRepresentation:
    t0 = time.perf_counter()
    embedding, embed_info = spectral_embedding(X, n_components=n_clusters, k=k)
    t_embed = time.perf_counter() - t0
    if mutual:
        affinity, graph_info = mutual_knn_affinity(embedding, k=k)
        ablation = "A1_mutual_knn"
    else:
        affinity, graph_info = knn_affinity(embedding, k=k)
        ablation = "A0_union_knn"
    if graph_drop:
        affinity = drop_affinity_edges(
            affinity, float(graph_drop["level"]), int(graph_drop.get("seed", 0))
        )
        graph_info = dict(graph_info)
        graph_info["graph_drop_fraction"] = float(graph_drop["level"])
        graph_info["graph_drop_seed"] = int(graph_drop.get("seed", 0))
        graph_info["n_edges_after_drop"] = int(sparse.csr_matrix(affinity).nnz // 2)
    t1 = time.perf_counter()
    shrinkage = shrink_embedding(
        embedding,
        affinity,
        gamma=float(gamma),
        max_iter=int(max_iter),
        tol=float(tol),
        G_init=embedding,
        zero_residual_floor="median_pairwise",
    )
    t_irls = time.perf_counter() - t1
    extra = {
        "embedding_info": {
            "eigen_solver": embed_info["eigen_solver"],
            "graph": embed_info["graph"],
        },
        "shrinkage_graph": graph_info,
        "n_irls_iterations": shrinkage.n_iterations,
        "irls_converged": bool(shrinkage.converged),
        "fixed_point_residual": shrinkage.fixed_point_residual,
        "initial_zero_residual_floor": shrinkage.initial_zero_residual_floor,
        "g0": "F",
        "linear_update": "equation_13",
        "eq13_graph_coefficient": "gamma",
        "eq8_graph_term_correspondence": "gamma_over_2",
        "ablation": ablation,
        "weights_frozen_before_irls": True,
        "runtime_embedding_seconds": t_embed,
        "runtime_irls_seconds": t_irls,
        "max_iter": int(max_iter),
        "tol": float(tol),
    }
    return PreparedRepresentation(
        name="rssc" if mutual else "ssc",
        features=shrinkage.patterns,
        extra=extra,
        history=list(shrinkage.history),
        cluster_fn="kmeans_on_features",
    )


def prepare_spectral(X: np.ndarray, n_clusters: int, k: int) -> PreparedRepresentation:
    t0 = time.perf_counter()
    n_samples = int(X.shape[0])
    if n_samples > 1500:
        embedding, info = spectral_embedding(X, n_components=n_clusters, k=k)
        extra = {
            "spectral_backend": "ssc_method_sparse",
            "reason": "n>1500; dense eigh of the baseline module is not used",
            "eigen_solver": info["eigen_solver"],
            "runtime_embedding_seconds": time.perf_counter() - t0,
        }
    else:
        embedding = sc_spectral_embedding(
            X, n_clusters=n_clusters, n_neighbors=k, knn_mode="union"
        )
        extra = {
            "spectral_backend": "baselines.spectral_clustering",
            "runtime_embedding_seconds": time.perf_counter() - t0,
        }
    return PreparedRepresentation(
        name="sc",
        features=np.asarray(embedding, dtype=np.float64),
        extra=extra,
        cluster_fn="kmeans_on_features",
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
        labels, inertia = _kmeans_labels(prepared.features, n_clusters, seed, init="random")
        return labels, {"kmeans_inertia": inertia, "kmeans_init": "random"}
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
        labels = kmeans_fit_predict(X, n_clusters, seed, n_init=1, init="random")
        return labels, {}
    if method == "pca_kmeans":
        n_components = int(params["n_components"])
        labels = pca_kmeans_fit_predict(
            X, n_clusters, seed, n_components=n_components, n_init=1, init="random"
        )
        return labels, {"n_components": n_components}
    if method == "pca_spectral":
        n_components = int(params["n_components"])
        labels = pca_spectral_fit_predict(
            X,
            n_clusters,
            seed,
            n_components=n_components,
            n_neighbors=k,
            n_init=1,
            init="random",
        )
        return labels, {"n_components": n_components}
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


CACHEABLE = {"ssc", "rssc", "sc", "llc"}
STATELESS = {"kmeans", "pca_kmeans", "pca_spectral", "lda_kmeans", "lda_spectral", "spls"}


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
    if method == "sc":
        return prepare_spectral(X, n_clusters, k)
    if method == "llc":
        return prepare_llc_embedding(X, n_clusters, k)
    gamma = float(params.get("gamma", 1.0))
    graph_drop = perturbation if perturbation and perturbation.get("type") == "graph_drop" else None
    return prepare_ssc_family(
        X,
        n_clusters=n_clusters,
        gamma=gamma,
        k=k,
        mutual=(method == "rssc"),
        graph_drop=graph_drop,
        max_iter=int(params.get("max_iter", 300)),
        tol=float(params.get("tol", 1e-6)),
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
