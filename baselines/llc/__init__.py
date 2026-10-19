"""Local learning clustering (Wu and Schölkopf, NIPS 2006)."""

from .llc import fit_predict, local_regression_matrix, yu_shi_discretize

__all__ = ["fit_predict", "local_regression_matrix", "yu_shi_discretize"]
