"""E05-fuse and E05-bilateral. Pixel-space edges are not assumed reliable."""

from __future__ import annotations

import numpy as np

from method_extension.common.fitting import ExtensionConfig, fit_named_method


class CrossSpaceSSC:
    def __init__(self, n_clusters: int, gamma: float = 1.0, mode: str = "fuse", **kwargs) -> None:
        self.n_clusters = int(n_clusters)
        self.gamma = float(gamma)
        self.mode = str(mode)
        self.config = ExtensionConfig(**kwargs) if kwargs else ExtensionConfig()

    def fit(self, X: np.ndarray, y: np.ndarray | None = None, embedding: np.ndarray | None = None):
        self.state_ = fit_named_method(
            "e05",
            X,
            self.n_clusters,
            gamma=self.gamma,
            variant=self.mode,
            config=self.config,
            embedding=embedding,
            y=y,
        )
        self.embedding_ = self.state_.embedding
        self.shrunk_ = self.state_.patterns
        self.affinity_ = self.state_.affinity
        self.converged_ = self.state_.converged
        return self
