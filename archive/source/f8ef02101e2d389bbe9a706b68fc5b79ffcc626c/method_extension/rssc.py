"""Reliability-aware SSC: mutual kNN shrinkage weights, original IRLS.

The spectral embedding F is the original SSC embedding (union kNN on X).
The shrinkage affinity W is a mutual kNN graph on F and is frozen before
IRLS. The linear step is still Equation (13) via SSC_method.optimizer.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.cluster import KMeans

from SSC_method.optimizer import shrink_embedding
from SSC_method.spectral_embedding import spectral_embedding
from method_extension.mutual_knn import mutual_knn_affinity


class ReliabilityAwareSSC:
    """Original SSC optimizer with a mutual-kNN shrinkage graph on F."""

    def __init__(
        self,
        n_clusters: int,
        gamma: float = 1.0,
        k: int = 5,
        eps: float = 1e-8,
        tol: float = 1e-6,
        max_iter: int = 100,
        delta2: float | None = None,
        embedding_delta2: float | None = None,
        kmeans_n_init: int = 10,
        kmeans_random_state: int = 0,
        kmeans_init: str = "random",
        zero_residual_floor: str | float = "median_pairwise",
        eigen_dense_threshold: int = 512,
    ) -> None:
        self.n_clusters = int(n_clusters)
        self.gamma = float(gamma)
        self.k = int(k)
        self.eps = float(eps)
        self.tol = float(tol)
        self.max_iter = int(max_iter)
        self.delta2 = delta2
        self.embedding_delta2 = embedding_delta2
        self.kmeans_n_init = int(kmeans_n_init)
        self.kmeans_random_state = kmeans_random_state
        self.kmeans_init = str(kmeans_init)
        self.zero_residual_floor = zero_residual_floor
        self.eigen_dense_threshold = int(eigen_dense_threshold)
        if self.n_clusters < 1:
            raise ValueError("n_clusters must be >= 1")
        if self.kmeans_n_init < 1:
            raise ValueError("kmeans_n_init must be >= 1")

    def fit_shrinkage(
        self, X: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, Any]:
        """Return F, G, and the ShrinkResult. No labels are used."""
        features = np.asarray(X, dtype=np.float64)
        if features.ndim != 2:
            raise ValueError("X must have shape (n_samples, n_features)")
        n_samples, n_features = features.shape
        if n_features < 1:
            raise ValueError("X must have at least one feature")
        if n_samples < 2:
            raise ValueError("RSSC requires at least 2 samples")
        if self.n_clusters > n_samples:
            raise ValueError("n_clusters cannot exceed n_samples")
        if not np.isfinite(features).all():
            raise ValueError("X contains non-finite values")

        embedding, embed_info = spectral_embedding(
            features,
            n_components=self.n_clusters,
            k=self.k,
            delta2=self.embedding_delta2,
            dense_threshold=self.eigen_dense_threshold,
        )
        affinity, affinity_info = mutual_knn_affinity(
            embedding, k=self.k, delta2=self.delta2
        )
        shrinkage = shrink_embedding(
            embedding,
            affinity,
            gamma=self.gamma,
            eps=self.eps,
            tol=self.tol,
            max_iter=self.max_iter,
            G_init=embedding,
            zero_residual_floor=self.zero_residual_floor,
        )
        self.embedding_ = embedding
        self.affinity_ = affinity
        self.shrunk_ = shrinkage.patterns
        self.n_iter_ = shrinkage.n_iterations
        self.converged_ = shrinkage.converged
        self.objective_history_ = shrinkage.history
        self.fixed_point_residual_ = shrinkage.fixed_point_residual
        self.info_: dict[str, Any] = {
            "embedding_graph": embed_info["graph"],
            "embedding_eigenvalues": embed_info["eigenvalues"],
            "eigen_solver": embed_info["eigen_solver"],
            "shrinkage_graph": affinity_info,
            "initial_zero_residual_floor": shrinkage.initial_zero_residual_floor,
            "g0": "F",
            "linear_update": "equation_13",
            "objective_monitored": "equation_8",
            "ablation": "A1_mutual_knn_shrinkage_weights",
            "weights_frozen_before_irls": True,
        }
        self._shrinkage_ = shrinkage
        return embedding, shrinkage.patterns, shrinkage

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> "ReliabilityAwareSSC":
        del y
        self.fit_shrinkage(X)
        kmeans = KMeans(
            n_clusters=self.n_clusters,
            init=self.kmeans_init,
            n_init=self.kmeans_n_init,
            random_state=self.kmeans_random_state,
            algorithm="lloyd",
        )
        labels = kmeans.fit_predict(self.shrunk_)
        self.labels_ = np.asarray(labels, dtype=int)
        self.kmeans_inertia_ = float(kmeans.inertia_)
        return self

    def fit_predict(self, X: np.ndarray, y: np.ndarray | None = None) -> np.ndarray:
        self.fit(X, y=y)
        return self.labels_


__all__ = ["ReliabilityAwareSSC"]
