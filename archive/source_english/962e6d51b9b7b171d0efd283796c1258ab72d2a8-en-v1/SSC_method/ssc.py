"""Spectral shrunk clustering pipeline.

Learning uses only X. Cluster labels are produced by K-means on the shrunk
patterns G and are not fed back into the affinity, the embedding, or G.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.cluster import KMeans

from SSC_method.graph_construction import knn_affinity
from SSC_method.optimizer import shrink_embedding, variant_laplacian_coefficient
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding


class SpectralShrunkClustering:
    """Chang et al., AAAI 2015, with the corrections recorded in the audit.

    Parameters
    ----------
    n_clusters:
        Number of clusters c. Also the number of Laplacian eigenvectors.
    gamma:
        Tradeoff in Equation (8) / Equation (13). The default 1 is an API
        default. The paper tunes gamma and reports that 1 often works; that
        is not a claim that every dataset should use 1.
    k:
        Neighborhood size. The paper sets k = 5 for the spectral algorithms.
    eps:
        Denominator floor in S and Wtilde. Objectives that use it are
        smoothed and are stored separately from Equation (8).
    tol, max_iter:
        Relative Frobenius stopping rule. Not stated in the paper.
    delta2:
        Squared bandwidth for the kNN graph on the spectral embedding F.
        ``None`` selects the median of positive kNN squared distances.
    embedding_delta2:
        Squared bandwidth for the kNN graph on the original features, used
        only to form the normalized Laplacian. ``None`` uses the same median
        rule on that graph. The two graphs are not forced to share one delta.
    kmeans_init, kmeans_n_init, kmeans_random_state:
        Explicit K-means settings. The library default remains
        ``k-means++`` with ``kmeans_n_init=10`` so old call sites do not
        change. Experiment runners pass ``init="random"`` and ``n_init=1``.
        The paper's experimental count of 50 restarts is a protocol choice
        and is not hard-wired here.
    zero_residual_floor:
        How to define Equation (10) when G - F is entirely zero. The default
        ``'median_pairwise'`` is the numerical correction documented in
        ``docs/reproduction_deviations.md``. ``'eps'`` is the literal floor
        and stays at F.
    variant:
        Linear system. ``'E13'`` (default) is the printed Equation (13),
        A = S + gamma Ltilde. ``'E8'`` is A = S + 2 gamma Ltilde, the
        ordered-pair stationary system of the printed Equation (8). The
        default preserves the historical Equation (13) solve.
    """

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
        kmeans_init: str = "k-means++",
        kmeans_n_init: int = 10,
        kmeans_random_state: int = 0,
        zero_residual_floor: str | float = "median_pairwise",
        eigen_dense_threshold: int = 512,
        variant: str = "E13",
    ) -> None:
        self.n_clusters = int(n_clusters)
        self.gamma = float(gamma)
        self.k = int(k)
        self.eps = float(eps)
        self.tol = float(tol)
        self.max_iter = int(max_iter)
        self.delta2 = delta2
        self.embedding_delta2 = embedding_delta2
        self.kmeans_init = str(kmeans_init)
        self.kmeans_n_init = int(kmeans_n_init)
        self.kmeans_random_state = kmeans_random_state
        self.zero_residual_floor = zero_residual_floor
        self.eigen_dense_threshold = int(eigen_dense_threshold)
        self.variant = str(variant)
        self.laplacian_coefficient = variant_laplacian_coefficient(self.variant)
        if self.n_clusters < 1:
            raise ValueError("n_clusters must be >= 1")
        if self.kmeans_n_init < 1:
            raise ValueError("kmeans_n_init must be >= 1")

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> "SpectralShrunkClustering":
        """Fit on rows of X. ``y`` is ignored and is never used to form G."""
        del y
        features = np.asarray(X, dtype=np.float64)
        if features.ndim != 2:
            raise ValueError("X must have shape (n_samples, n_features)")
        n_samples, n_features = features.shape
        if n_features < 1:
            raise ValueError("X must have at least one feature")
        if n_samples < 2:
            raise ValueError("SSC requires at least 2 samples")
        if self.n_clusters > n_samples:
            raise ValueError("n_clusters cannot exceed n_samples")
        if not np.isfinite(features).all():
            raise ValueError("X contains non-finite values")

        graph_config = SpectralGraphConfig(
            k=self.k,
            delta2=self.embedding_delta2,
            dense_threshold=self.eigen_dense_threshold,
            variant=self.variant,
            g_init="F",
            zero_residual_floor=self.zero_residual_floor,
            tol=self.tol,
            max_iter=self.max_iter,
            eps=self.eps,
            kmeans_init=self.kmeans_init,
            kmeans_n_init=self.kmeans_n_init,
            seed=self.kmeans_random_state,
        )
        embedding, embed_info = spectral_embedding(
            features,
            n_components=self.n_clusters,
            config=graph_config,
        )
        affinity, affinity_info = knn_affinity(
            embedding, k=self.k, delta2=self.delta2, knn_method=graph_config.knn_method
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
            variant=self.variant,
        )
        kmeans = KMeans(
            n_clusters=self.n_clusters,
            init=self.kmeans_init,
            n_init=self.kmeans_n_init,
            random_state=self.kmeans_random_state,
            algorithm="lloyd",
        )
        labels = kmeans.fit_predict(shrinkage.patterns)

        self.embedding_ = embedding
        self.affinity_ = affinity
        self.shrunk_ = shrinkage.patterns
        self.labels_ = np.asarray(labels, dtype=int)
        self.n_iter_ = shrinkage.n_iterations
        self.converged_ = shrinkage.converged
        self.objective_history_ = shrinkage.history
        self.fixed_point_residual_ = shrinkage.fixed_point_residual
        self.kmeans_inertia_ = float(kmeans.inertia_)
        self.info_: dict[str, Any] = {
            "embedding_graph": embed_info["graph"],
            "embedding_eigenvalues": embed_info["eigenvalues"],
            "eigen_solver": embed_info["eigen_solver"],
            "sign_convention": embed_info.get("sign_convention"),
            "row_normalize": bool(embed_info.get("row_normalize", False)),
            "shared_eq4_path": True,
            "spectral_graph_config": graph_config.to_dict(),
            "shrinkage_graph": affinity_info,
            "initial_zero_residual_floor": shrinkage.initial_zero_residual_floor,
            "g0": "F",
            "variant": shrinkage.variant,
            "laplacian_coefficient": shrinkage.laplacian_coefficient,
            "linear_update": "equation_13" if shrinkage.variant == "E13" else "equation_8_stationary",
            "objective_monitored": "equation_8",
            "sqrt_smoothed_objective_key": "sqrt_smoothed_equation8_objective",
            "kmeans_init": self.kmeans_init,
            "kmeans_n_init": self.kmeans_n_init,
        }
        return self

    def fit_predict(self, X: np.ndarray, y: np.ndarray | None = None) -> np.ndarray:
        """Fit and return K-means labels of G. Labels are for evaluation only."""
        self.fit(X, y=y)
        return self.labels_


__all__ = ["SpectralShrunkClustering"]
