"""Graph weights for the prespecified extensions.

Stability, mass calibration, and multi-scale sums use a fixed nonnegative W.
None of them is claimed as a new convexity result: a fixed nonnegative W keeps
the ordered-pair objective convex.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_embedding import smallest_eigenpairs
from SSC_method.graph_construction import symmetric_normalized_laplacian
from method_extension.v3_theory.common.objectives import as_csr


def knn_graph(features: np.ndarray, k: int) -> sparse.csr_matrix:
    affinity, _info = knn_affinity(features, k=int(k), delta2=None, symmetrization="union")
    return as_csr(affinity)


def total_mass(affinity: sparse.spmatrix | np.ndarray) -> float:
    return float(as_csr(affinity).sum())


def mean_mass(affinity: sparse.spmatrix | np.ndarray) -> float:
    matrix = as_csr(affinity)
    return float(matrix.sum() / max(matrix.shape[0], 1))


def scale_to_mass(affinity: sparse.spmatrix | np.ndarray, target_mass: float) -> sparse.csr_matrix:
    matrix = as_csr(affinity)
    current = float(matrix.sum())
    if current <= 0.0 or target_mass < 0.0:
        return matrix
    return (matrix * (float(target_mass) / current)).tocsr()


def upper_edges(affinity: sparse.spmatrix | np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    matrix = as_csr(affinity).tocoo()
    keep = (matrix.data > 0.0) & (matrix.row < matrix.col)
    return (
        np.asarray(matrix.row[keep], dtype=np.int64),
        np.asarray(matrix.col[keep], dtype=np.int64),
        np.asarray(matrix.data[keep], dtype=np.float64),
    )


def from_upper(n_samples: int, src: np.ndarray, dst: np.ndarray, weight: np.ndarray) -> sparse.csr_matrix:
    if src.size == 0:
        return sparse.csr_matrix((n_samples, n_samples), dtype=np.float64)
    rows = np.concatenate([src, dst])
    cols = np.concatenate([dst, src])
    data = np.concatenate([weight, weight])
    matrix = sparse.coo_matrix((data, (rows, cols)), shape=(n_samples, n_samples)).tocsr()
    matrix.sum_duplicates()
    return matrix


def support_fraction(graphs: list[sparse.spmatrix]) -> sparse.csr_matrix:
    """Fraction of graphs that contain each undirected edge. Sparse."""
    if not graphs:
        raise ValueError("support_fraction needs at least one graph")
    n_samples = graphs[0].shape[0]
    total = sparse.csr_matrix((n_samples, n_samples), dtype=np.float64)
    for graph in graphs:
        binary = as_csr(graph)
        binary.data = np.ones(binary.data.shape[0], dtype=np.float64)
        binary.setdiag(0.0)
        binary.eliminate_zeros()
        binary = ((binary + binary.T) > 0).astype(np.float64).tocsr()
        total = total + binary
    total = (total / float(len(graphs))).tocsr()
    total.eliminate_zeros()
    return total


def apply_stability(
    affinity: sparse.spmatrix,
    fraction: sparse.spmatrix,
    beta: float,
    *,
    epsilon: float = 0.05,
) -> sparse.csr_matrix:
    """W_ij * (epsilon + s_ij)^beta, then restore the original total mass.

    beta = 0 leaves every multiplier at 1, so the result is the original W.
    """
    base = as_csr(affinity)
    scores = as_csr(fraction)
    coo = base.tocoo()
    sampled = np.asarray(scores[coo.row, coo.col]).ravel()
    data = coo.data * np.power(epsilon + sampled, float(beta))
    weighted = sparse.coo_matrix((data, (coo.row, coo.col)), shape=base.shape).tocsr()
    weighted = ((weighted + weighted.T) * 0.5).tocsr()
    weighted.eliminate_zeros()
    return scale_to_mass(weighted, total_mass(base))


def permute_stability(
    affinity: sparse.spmatrix,
    fraction: sparse.spmatrix,
    beta: float,
    seed: int,
    *,
    epsilon: float = 0.05,
) -> sparse.csr_matrix:
    """Permute s_ij on the undirected support, then use the same formula."""
    base = as_csr(affinity)
    src, dst, _weight = upper_edges(base)
    scores = as_csr(fraction)
    values = np.asarray(scores[src, dst]).ravel()
    rng = np.random.default_rng(seed)
    rng.shuffle(values)
    permuted = from_upper(base.shape[0], src, dst, values)
    # Zero-score edges stay explicit so the multiplier is epsilon^beta.
    return apply_stability(base, permuted, beta, epsilon=epsilon)


def uniform_scale(affinity: sparse.spmatrix, factor: float) -> sparse.csr_matrix:
    """Global scale. This is a gamma rescaling, not a new graph rule."""
    return (as_csr(affinity) * float(factor)).tocsr()


def _configuration_edges(degree: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    stubs: list[int] = []
    for index, value in enumerate(np.asarray(degree, dtype=np.int64)):
        stubs.extend([index] * int(max(value, 0)))
    if len(stubs) % 2 == 1:
        stubs.append(int(np.argmax(degree)))
    order = rng.permutation(len(stubs))
    stubs = [stubs[int(index)] for index in order]
    pairs: set[tuple[int, int]] = set()
    for left, right in zip(stubs[0::2], stubs[1::2], strict=False):
        if left == right:
            continue
        edge = (min(left, right), max(left, right))
        pairs.add(edge)
    if not pairs:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    stacked = np.asarray(sorted(pairs), dtype=np.int64)
    return stacked[:, 0], stacked[:, 1]


def degree_matched_random(affinity: sparse.spmatrix, seed: int) -> sparse.csr_matrix:
    """Random support with the same degrees where the configuration model allows it.

    The original undirected weight multiset is reassigned and the total mass is
    restored. Leftover or missing edges are recorded by the caller via the
    returned edge count; this function always returns a symmetric nonnegative W.
    """
    base = as_csr(affinity)
    src, dst, weight = upper_edges(base)
    binary = base.copy()
    binary.data = np.ones_like(binary.data)
    degree = np.asarray(binary.sum(axis=1)).ravel().astype(np.int64)
    new_src, new_dst = _configuration_edges(degree, seed)
    n_edges = int(weight.size)
    rng = np.random.default_rng(seed + 17)
    if new_src.size == 0:
        new_src, new_dst = _random_edges(base.shape[0], n_edges, seed)
    if new_src.size > n_edges:
        choice = rng.choice(new_src.size, size=n_edges, replace=False)
        new_src = new_src[choice]
        new_dst = new_dst[choice]
    elif new_src.size < n_edges:
        extra_src, extra_dst = _random_edges(base.shape[0], n_edges - new_src.size, seed + 3)
        new_src = np.concatenate([new_src, extra_src])
        new_dst = np.concatenate([new_dst, extra_dst])
    permuted = weight.copy()
    rng.shuffle(permuted)
    graph = from_upper(base.shape[0], new_src[:n_edges], new_dst[:n_edges], permuted[:n_edges])
    return scale_to_mass(graph, total_mass(base))


def _random_edges(n_samples: int, n_edges: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    if n_samples < 2 or n_edges <= 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    max_edges = n_samples * (n_samples - 1) // 2
    n_edges = min(int(n_edges), max_edges)
    chosen: set[tuple[int, int]] = set()
    guard = 0
    while len(chosen) < n_edges and guard < n_edges * 20 + 100:
        guard += 1
        left = int(rng.integers(0, n_samples))
        right = int(rng.integers(0, n_samples))
        if left == right:
            continue
        chosen.add((min(left, right), max(left, right)))
    if not chosen:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    stacked = np.asarray(sorted(chosen), dtype=np.int64)
    return stacked[:, 0], stacked[:, 1]


def mass_matched_random(affinity: sparse.spmatrix, seed: int) -> sparse.csr_matrix:
    """Same edge count and the same total mass, with uniform edge weights."""
    base = as_csr(affinity)
    _src, _dst, weight = upper_edges(base)
    src, dst = _random_edges(base.shape[0], int(weight.size), seed)
    uniform = np.ones(src.size, dtype=np.float64)
    graph = from_upper(base.shape[0], src, dst, uniform)
    return scale_to_mass(graph, total_mass(base))


def edge_budget_matched(affinity: sparse.spmatrix, seed: int) -> sparse.csr_matrix:
    """Same edge count, same weight multiset, hence the same total mass."""
    base = as_csr(affinity)
    _src, _dst, weight = upper_edges(base)
    src, dst = _random_edges(base.shape[0], int(weight.size), seed)
    rng = np.random.default_rng(seed + 9)
    permuted = weight.copy()
    rng.shuffle(permuted)
    return from_upper(base.shape[0], src[: permuted.size], dst[: permuted.size], permuted)


def normalize_each_and_average(graphs: list[sparse.spmatrix], alphas: np.ndarray | None = None) -> sparse.csr_matrix:
    """Put every graph on one total mass, then take a fixed convex combination."""
    if not graphs:
        raise ValueError("need at least one graph")
    target = float(np.mean([total_mass(graph) for graph in graphs]))
    if alphas is None:
        alphas = np.full(len(graphs), 1.0 / len(graphs), dtype=np.float64)
    alphas = np.asarray(alphas, dtype=np.float64)
    if alphas.shape != (len(graphs),) or abs(float(alphas.sum()) - 1.0) > 1e-8:
        raise ValueError("alphas must sum to 1 and match the graph list")
    combined = sparse.csr_matrix(graphs[0].shape, dtype=np.float64)
    for alpha, graph in zip(alphas, graphs, strict=True):
        combined = combined + float(alpha) * scale_to_mass(graph, target)
    return combined.tocsr()


def mass_normalized_affinity(affinity: sparse.spmatrix, epsilon: float = 1e-12) -> tuple[sparse.csr_matrix, float]:
    """W_bar = W / max(m(W), epsilon), m(W) = sum_ij W_ij / n."""
    matrix = as_csr(affinity)
    mass = mean_mass(matrix)
    scale = max(mass, float(epsilon))
    return (matrix / scale).tocsr(), float(mass)


def graph_summary(affinity: sparse.spmatrix, name: str) -> dict[str, float | int | str]:
    matrix = as_csr(affinity)
    count, labels = connected_components(matrix, directed=False, connection="weak")
    degree = np.asarray(matrix.sum(axis=1)).ravel()
    mean = float(degree.mean()) if degree.size else 0.0
    deviation = float(degree.std()) if degree.size else 0.0
    return {
        "graph": name,
        "n_ordered_entries": int(matrix.nnz),
        "n_undirected_edges": int(np.sum(upper_edges(matrix)[2] > 0)),
        "n_components": int(count),
        "n_isolates": int(np.sum(degree <= 0.0)),
        "degree_min": float(degree.min()) if degree.size else 0.0,
        "degree_mean": mean,
        "degree_median": float(np.median(degree)) if degree.size else 0.0,
        "degree_max": float(degree.max()) if degree.size else 0.0,
        "degree_cv": float(deviation / mean) if mean > 0.0 else 0.0,
        "affinity_sum": float(matrix.sum()),
        "component_sizes_max": int(np.bincount(labels).max()) if labels.size else 0,
    }


def laplacian_spectrum(affinity: sparse.spmatrix, n_eigen: int) -> dict[str, np.ndarray | float | str]:
    """Eigenpairs of the symmetric normalized Laplacian around the requested count."""
    from scipy.linalg import eigh
    from scipy.sparse.linalg import ArpackNoConvergence

    from SSC_method.spectral_embedding import orient_eigenvector_signs

    laplacian = symmetric_normalized_laplacian(as_csr(affinity))
    n_samples = laplacian.shape[0]
    count = int(min(max(n_eigen, 1), n_samples - 1 if n_samples > 1 else 1))
    try:
        values, vectors, solver = smallest_eigenpairs(laplacian, count)
    except ArpackNoConvergence:
        # Diagnostic only. Clustering embeddings stay on the frozen ARPACK path.
        dense = laplacian.toarray()
        values, vectors = eigh(dense, subset_by_index=[0, count - 1])
        vectors = orient_eigenvector_signs(vectors)
        values = np.asarray(values, dtype=np.float64)
        solver = "scipy.linalg.eigh_after_arpack_noconvergence"
    residual = []
    for index in range(vectors.shape[1]):
        column = vectors[:, index]
        formed = laplacian @ column
        residual.append(float(np.linalg.norm(formed - values[index] * column)))
    gap = float("nan")
    if values.size >= 2:
        gap = float(values[-1] - values[-2])
    gram = vectors.T @ vectors
    eye = np.eye(gram.shape[0])
    return {
        "eigenvalues": np.asarray(values, dtype=np.float64),
        "eigen_residual_max": float(np.max(residual)) if residual else float("nan"),
        "eigen_solver": solver,
        "eigengap_last_minus_previous": gap,
        "orthogonality_frobenius": float(np.linalg.norm(gram - eye)),
        "vector_row_norm_mean": float(np.linalg.norm(vectors, axis=1).mean()) if vectors.size else float("nan"),
    }
