"""LDA subspace selection combined with spectral clustering (APPROXIMATE)."""

from .lda_spectral import fit_predict, fit_predict_oneshot

__all__ = ["fit_predict", "fit_predict_oneshot"]
