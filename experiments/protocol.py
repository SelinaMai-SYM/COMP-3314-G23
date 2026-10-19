"""Protocol numbers that the experiment runner actually uses.

Track A selection uses labels and is disclosed. Track B does not.
"""

from __future__ import annotations

GAMMA_GRID = (1e-6, 1e-3, 1.0, 1e3, 1e6)
K_DEFAULT = 5
K_SWEEP = (3, 5, 7, 9)
DIM_GRID_FULL = tuple(range(10, 160, 10))
TRACK_B_GAMMA = 1.0
NOISE_FRACS = (0.1, 0.3)
CORRUPT_FRACS = (0.10,)
OUTLIER_FRACS = (0.05,)
GRAPH_DROP_FRACS = (0.10,)
SELECTION_RULE = (
    "label-informed: among completed settings of this method and dataset, "
    "select the setting with the highest mean ACC over its completed trials; "
    "then report mean±std over ALL completed trials of that selected setting. "
    "The paper is ambiguous between 50 random restarts, best-objective, and "
    "mean±std. Every trial is kept. No trial is dropped by an invented "
    "best-objective filter."
)


def dimension_grid(n_samples: int, n_features: int, n_clusters: int | None = None, lda: bool = False) -> list[int]:
    """Track A DR grid {10,20,...,150} clipped by n and d, and by K-1 for LDA."""
    cap = min(n_samples - 1, n_features)
    if lda:
        if n_clusters is None:
            raise ValueError("LDA dimension grid needs n_clusters")
        cap = min(cap, n_clusters - 1)
    values = [d for d in DIM_GRID_FULL if d <= cap]
    if not values and cap >= 1:
        values = [cap]
    return values


def track_b_dimension(n_samples: int, n_features: int, n_clusters: int, lda: bool = False) -> int:
    """Prespecified Track B dimension. No labels.

    Rule used: min(50, n_clusters, n_samples-1, n_features), and for LDA
    n_clusters is replaced by n_clusters-1 because classical LDA cannot
    exceed that rank. This is the execution brief's example rule, not a
    paper value. The protocol YAML's alternative (largest grid value
    <= min(n-1, d)) is not used for Track B.
    """
    cluster_cap = (n_clusters - 1) if lda else n_clusters
    value = min(50, cluster_cap, n_samples - 1, n_features)
    if value < 1:
        raise ValueError("Track B dimension is not positive")
    return int(value)


FAITHFUL_METHODS = (
    "kmeans",
    "sc",
    "ssc",
    "pca_kmeans",
    "pca_spectral",
    "lda_kmeans",
    "llc",
)
APPROXIMATE_METHODS = ("lda_spectral",)
NOT_IMPLEMENTED_METHODS = ("spls",)
EXTENSION_METHODS = ("rssc",)

METHOD_STATUS = {
    "kmeans": "FAITHFUL_REIMPLEMENTATION",
    "sc": "FAITHFUL_REIMPLEMENTATION",
    "ssc": "FAITHFUL_REIMPLEMENTATION",
    "pca_kmeans": "FAITHFUL_REIMPLEMENTATION",
    "pca_spectral": "FAITHFUL_REIMPLEMENTATION",
    "lda_kmeans": "FAITHFUL_REIMPLEMENTATION",
    "llc": "FAITHFUL_REIMPLEMENTATION",
    "lda_spectral": "APPROXIMATE",
    "spls": "NOT_IMPLEMENTED",
    "rssc": "EXTENSION",
}

SHORT_METHOD = {
    "kmeans": "KMEANS",
    "sc": "SC",
    "ssc": "SSC",
    "rssc": "RSSC",
    "pca_kmeans": "PCAKM",
    "pca_spectral": "PCASC",
    "lda_kmeans": "LDAKM",
    "lda_spectral": "LDASC",
    "llc": "LLC",
    "spls": "SPLS",
}
