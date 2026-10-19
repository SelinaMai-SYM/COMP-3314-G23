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
    describes shrinking patterns before a linear subspace is learned, and
    names a parameter alpha. A 2026-10-20 re-search of the publisher,
    Unpaywall, OpenAlex, Semantic Scholar, arXiv (0 hits), Crossref,
    Chenping Hou's homepage (the listed PDF is the Elsevier DOI), Feiping
    Nie's NWPU page, the old UTA page (404), and GitHub did not produce
    Section 3 or official code. A citing recap in arXiv:1705.01206 uses
    different parameter names and is not treated as the original solver.
    This function therefore raises rather than substituting K-means,
    spectral clustering, generic shrinking, or PSLSR/SLSR.

    The arguments are accepted so callers have the same positional shape as
    the implemented baselines. They are not used.
    """
    del X, n_clusters, random_state, params
    raise NotImplementedError(
        "SPLS (Hou, Nie, Jiao, Zhang, and Wu, Information Processing & "
        "Management 2013; called SLPS in that paper) is NOT_IMPLEMENTED. "
        "The optimization in Section 3 was not available from the open "
        "sources checked on 2026-10-20 (publisher, Unpaywall, OpenAlex, "
        "arXiv 0 hits, author DOI link, no official code). This function "
        "does not run a substitute clustering method."
    )
