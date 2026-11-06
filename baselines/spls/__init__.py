"""One-shot SLPS / SPLS from Hou et al., IPM 2013, Eqs. (18)--(19)."""

from .spls import fit_predict, oneshot_shrunk_patterns, pca_embedding

__all__ = ["fit_predict"]
