"""Lloyd K-means with every sklearn control passed explicitly."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.cluster import KMeans

from ..common import check_problem, resolve_params

_DEFAULTS: dict[str, Any] = {
    "n_init": 1,
    "max_iter": 300,
    "tol": 1e-4,
    "init": "random",
    "algorithm": "lloyd",
}


def fit_predict(
    X: np.ndarray,
    n_clusters: int,
    random_state: int,
    **params: Any,
) -> np.ndarray:
    """Minimize the K-means within-cluster sum of squares.

    Objective: given cluster indicators, minimize
    ``sum_k sum_{i in C_k} ||x_i - m_k||^2``, where ``m_k`` is the mean of
    cluster ``C_k``. This is the classical baseline named by Chang et al.
    (AAAI 2015). The fitter runs one seeded Lloyd procedure. It does not
    repeat the paper's 50 random restarts and it does not keep the best
    objective across a hidden grid.

    Assumptions:
    - ``X`` has shape ``(n_samples, n_features)`` and Euclidean distance is
      meaningful after the caller's preprocessing.
    - ``n_clusters`` is given. It is not estimated.
    - Chang et al. say they use random initialization. The default ``init``
      is therefore ``"random"``, not ``k-means++``.
    - ``n_init`` defaults to 1 so each call is one initialization. sklearn
      draws further seeds from ``random_state`` when ``n_init`` > 1 and
      keeps the lowest inertia. That choice stays in the caller's hands.
    - ``algorithm="lloyd"`` is Lloyd's method. ``"elkan"`` is accepted only
      when the caller sets it.

    Returns cluster labels of shape ``(n_samples,)``. The same
    ``random_state`` and parameters reproduce the same labels.
    """
    features, clusters, seed = check_problem(X, n_clusters, random_state)
    options = resolve_params(params, _DEFAULTS)
    n_init = options["n_init"]
    max_iter = options["max_iter"]
    if isinstance(n_init, bool) or not isinstance(n_init, (int, np.integer)):
        raise TypeError("n_init must be a positive int")
    if int(n_init) < 1:
        raise ValueError("n_init must be a positive int")
    if isinstance(max_iter, bool) or not isinstance(max_iter, (int, np.integer)):
        raise TypeError("max_iter must be a positive int")
    if int(max_iter) < 1:
        raise ValueError("max_iter must be a positive int")
    if options["init"] not in {"random", "k-means++"}:
        raise ValueError("init must be 'random' or 'k-means++'")
    if options["algorithm"] not in {"lloyd", "elkan"}:
        raise ValueError("algorithm must be 'lloyd' or 'elkan'")
    tol = float(options["tol"])
    if not np.isfinite(tol) or tol <= 0:
        raise ValueError("tol must be a positive finite float")
    model = KMeans(
        n_clusters=clusters,
        init=options["init"],
        n_init=int(n_init),
        max_iter=int(max_iter),
        tol=tol,
        random_state=seed,
        copy_x=True,
        algorithm=options["algorithm"],
    )
    return model.fit_predict(features).astype(np.int64, copy=False)
