"""Fixed four-scale average. Alphas are 1/4 and are not fit to labels."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from method_extension.v3_theory.common.graphs import knn_graph, normalize_each_and_average

SCALES: tuple[int, ...] = (3, 5, 10, 15)


def multiscale_graph(embedding: np.ndarray, scales: tuple[int, ...] = SCALES) -> tuple[sparse.csr_matrix, list[sparse.csr_matrix]]:
    graphs = [knn_graph(embedding, k) for k in scales]
    alphas = np.full(len(graphs), 1.0 / len(graphs), dtype=np.float64)
    return normalize_each_and_average(graphs, alphas), graphs
