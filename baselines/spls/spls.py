"""Placeholder for SPLS / SLPS. The optimizer is not implemented."""

from __future__ import annotations

from typing import Any

import numpy as np


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """Do not cluster.

    Hou, Nie, Jiao, Zhang, and Wu (Information Processing & Management,
    2013) call the method subspace learning via pattern shrinking (SLPS).
    Chang et al. (AAAI 2015) abbreviate it SPLS. The publisher abstract
    describes shrinking patterns before a linear subspace is learned. The
    Section 3 optimization was not available from the open abstract, and no
    official code was found. This function therefore raises rather than
    substituting K-means or spectral clustering.

    The arguments are accepted so callers have the same positional shape as
    the implemented baselines. They are not used.
    """
    del X, n_clusters, random_state, params
    raise NotImplementedError(
        "SPLS (Hou, Nie, Jiao, Zhang, and Wu, Information Processing & "
        "Management 2013; called SLPS in that paper) is NOT_IMPLEMENTED. "
        "The optimization in Section 3 was not available from the open "
        "sources checked, and no official code was found. This function "
        "does not run a substitute clustering method."
    )
