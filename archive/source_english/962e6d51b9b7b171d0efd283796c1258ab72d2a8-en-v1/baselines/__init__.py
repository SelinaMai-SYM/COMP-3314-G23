"""Baselines compared with spectral shrunk clustering.

Each implemented method exposes ``fit_predict(X, n_clusters, random_state, **params)``.
Import the method package you need. :func:`baselines.spls.fit_predict` always raises
``NotImplementedError``.
"""

from . import (
    kmeans,
    lda_kmeans,
    lda_spectral,
    llc,
    pca_kmeans,
    pca_spectral,
    spectral_clustering,
    spls,
)

# Short alias so ``from baselines import spectral`` still resolves while the
# canonical package is ``baselines.spectral_clustering``.
spectral = spectral_clustering

__all__ = [
    "kmeans",
    "spectral_clustering",
    "spectral",
    "pca_kmeans",
    "pca_spectral",
    "lda_kmeans",
    "lda_spectral",
    "llc",
    "spls",
]
