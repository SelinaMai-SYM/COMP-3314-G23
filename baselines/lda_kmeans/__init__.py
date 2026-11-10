"""Ding and Li adaptive LDA guided by K-means labels."""

from .lda_kmeans import (
    _pca_basis, _prepare_subspace, fit_predict, fit_state, lda_basis,
    scatter_objective, partitions_equal, trajectory_prefix_matches,
)
from .adapted import prepare_pca, fit_adapted_state
from .reference import fit_reference_state

__all__ = ["fit_predict", "fit_state", "lda_basis", "scatter_objective",
           "partitions_equal", "trajectory_prefix_matches", "prepare_pca",
           "fit_adapted_state", "fit_reference_state"]
