"""Method identities for the nine-baseline comparison."""

from __future__ import annotations

from typing import Any

METHODS: dict[str, dict[str, str]] = {
    "kmeans": {"family": "kmeans", "clustering": "lloyd"},
    "sc": {"family": "spectral", "clustering": "kmeans_on_F"},
    "pca_kmeans": {"family": "pca", "clustering": "kmeans_on_scores"},
    "pca_sc": {"family": "pca_spectral", "clustering": "kmeans_on_F"},
    "lda_kmeans": {"family": "lda", "clustering": "full_alternation"},
    "lda_sc": {"family": "blocked", "clustering": "undefined"},
    "llc": {"family": "llc", "clustering": "yu_shi"},
    "spls": {"family": "slps_oneshot", "clustering": "kmeans_on_embedding"},
    "ssc": {"family": "ssc", "clustering": "kmeans_on_G"},
}


def bind_config(requested: dict[str, Any], effective: dict[str, Any]) -> dict[str, Any]:
    """Reject requested keys that never reach the recorded effective config."""
    ignored = sorted(str(key) for key in requested if key not in effective)
    if ignored:
        raise RuntimeError(f"ignored parameters: {ignored}")
    return {
        "requested_config": dict(requested),
        "effective_config": dict(effective),
    }
