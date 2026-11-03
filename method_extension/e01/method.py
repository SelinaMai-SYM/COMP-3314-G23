"""E01: keep F, replace W by W ⊙ p^beta."""

from __future__ import annotations

import numpy as np

from method_extension.common.fitting import ExtensionConfig, fit_named_method


class EdgeRecurrenceSSC:
    def __init__(self, n_clusters: int, gamma: float = 1.0, **kwargs) -> None:
        self.n_clusters = int(n_clusters)
        self.gamma = float(gamma)
        self.config = ExtensionConfig(**kwargs) if kwargs else ExtensionConfig()

    def fit(self, X: np.ndarray, y: np.ndarray | None = None, embedding: np.ndarray | None = None):
        self.state_ = fit_named_method(
            "e01", X, self.n_clusters, gamma=self.gamma, config=self.config, embedding=embedding, y=y
        )
        self._publish()
        return self

    def _publish(self) -> None:
        self.embedding_ = self.state_.embedding
        self.shrunk_ = self.state_.patterns
        self.affinity_ = self.state_.affinity
        self.converged_ = self.state_.converged
        self.n_iter_ = self.state_.n_iterations
