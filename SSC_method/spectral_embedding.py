"""Spectral embedding from the symmetric normalized Laplacian, Equation (4).

The embedding is the c eigenvectors for the smallest eigenvalues. It is not
PCA, and it does not call scikit-learn spectral clustering.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.linalg import eigh
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import eigsh

from SSC_method.graph_construction import (
    combinatorial_laplacian,
    knn_affinity,
    symmetric_normalized_laplacian,
)
from SSC_method.spectral_config import (
    SIGN_CONVENTION,
    SpectralGraphConfig,
)


def orient_eigenvector_signs(vectors: np.ndarray) -> np.ndarray:
    """Flip each column so its largest-magnitude entry is positive.

    The paper does not fix eigenvector signs. This rule makes the embedding
    deterministic without changing the spanned subspace.
    """
    oriented = np.array(vectors, dtype=np.float64, copy=True)
    for column in range(oriented.shape[1]):
        values = oriented[:, column]
        pivot = int(np.argmax(np.abs(values)))
        if values[pivot] < 0.0:
            oriented[:, column] *= -1.0
    return oriented


def smallest_eigenpairs(
    laplacian: sparse.spmatrix | np.ndarray,
    n_components: int,
    dense_threshold: int = 512,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Smallest eigenpairs of a real symmetric matrix, ascending eigenvalues."""
    if sparse.issparse(laplacian):
        n_samples = int(laplacian.shape[0])
        matrix = laplacian
    else:
        matrix = np.asarray(laplacian, dtype=np.float64)
        n_samples = int(matrix.shape[0])
    if n_components < 1 or n_components > n_samples:
        raise ValueError("n_components must lie in 1..n_samples")
    use_dense = n_samples <= dense_threshold or n_components >= n_samples - 1
    if use_dense:
        dense = matrix.toarray() if sparse.issparse(matrix) else matrix
        evals, evecs = eigh(dense, subset_by_index=[0, n_components - 1])
        solver = "scipy.linalg.eigh"
    else:
        # k must be strictly less than n for ARPACK; the branch above sends
        # the near-full case to the dense solver.
        evals, evecs = eigsh(sparse.csr_matrix(matrix), k=n_components, which="SA")
        order = np.argsort(evals)
        evals = evals[order]
        evecs = evecs[:, order]
        solver = "scipy.sparse.linalg.eigsh"
    return np.asarray(evals, dtype=np.float64), orient_eigenvector_signs(evecs), solver


def embeddings_match(
    left: np.ndarray,
    right: np.ndarray,
    *,
    rtol: float = 1e-8,
    atol: float = 1e-8,
) -> bool:
    """Return whether two embeddings agree after the shared sign convention.

    Eigenvector signs are not identified by Equation (4). Column-wise
    flipping to make the largest-magnitude entry positive is the documented
    convention used by this package. Pairwise row distances are invariant
    to those flips; K-means coordinates are not, so shrinkage comparisons
    must use this aligned F rather than a second independent embedding.
    """
    aligned_left = orient_eigenvector_signs(left)
    aligned_right = orient_eigenvector_signs(right)
    return bool(np.allclose(aligned_left, aligned_right, rtol=rtol, atol=atol))


def _laplacian_from_affinity(affinity, laplacian_name: str):
    if laplacian_name == "symmetric_normalized_eq4":
        return symmetric_normalized_laplacian(affinity), laplacian_name
    if laplacian_name == "combinatorial":
        return combinatorial_laplacian(affinity), "combinatorial"
    raise ValueError(
        f"unknown laplacian {laplacian_name!r}; expected "
        "symmetric_normalized_eq4 or combinatorial"
    )


def spectral_embedding(
    X: np.ndarray,
    n_components: int,
    k: int = 5,
    delta2: float | None = None,
    dense_threshold: int = 512,
    knn_method: str = "auto",
    bandwidth_rule: str | None = None,
    row_normalize: bool = False,
    symmetrization: str = "union",
    laplacian: str = "symmetric_normalized_eq4",
    eigenvector_selection: str = "smallest",
    sign_convention: str = SIGN_CONVENTION,
    config: SpectralGraphConfig | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """c smallest eigenvectors of the symmetric normalized Laplacian.

    ``k`` defaults to 5, the neighborhood size stated for the spectral
    algorithms in the paper. The Gaussian bandwidth is not taken from a
    library default; see ``knn_affinity``. Raw eigenvectors are the default.
    Row normalization is a diagnostic, not the paper's stated embedding.

    Spectral clustering and SSC call this function with the same
    :class:`SpectralGraphConfig` when Equation (4) is the shared math.
    Passing different configs, or mixing this embedding with a second
    independent eigensolve, is not a valid shrinkage comparison.
    """
    if config is not None:
        k = config.k
        delta2 = config.resolved_delta2()
        dense_threshold = config.dense_threshold
        knn_method = config.knn_method
        bandwidth_rule = config.bandwidth_rule
        row_normalize = config.row_normalize
        symmetrization = config.symmetrization
        laplacian = config.laplacian
        eigenvector_selection = config.eigenvector_selection
        sign_convention = config.sign_convention
    if eigenvector_selection != "smallest":
        raise ValueError("eigenvector_selection must be 'smallest'")
    if sign_convention != SIGN_CONVENTION:
        raise ValueError(
            "sign_convention must be 'largest_magnitude_positive'"
        )
    affinity, graph_info = knn_affinity(
        X,
        k=k,
        delta2=delta2,
        knn_method=knn_method,
        bandwidth_rule=bandwidth_rule,
        symmetrization=symmetrization,
    )
    laplacian_matrix, laplacian_name = _laplacian_from_affinity(affinity, laplacian)
    eigenvalues, embedding, solver = smallest_eigenpairs(
        laplacian_matrix, n_components, dense_threshold=dense_threshold
    )
    row_normalized = bool(row_normalize)
    if row_normalized:
        norms = np.linalg.norm(embedding, axis=1, keepdims=True)
        embedding = embedding / np.maximum(norms, 1e-12)
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    n_components_graph, _labels = connected_components(
        weights, directed=False, return_labels=True
    )
    degrees = np.asarray(weights.sum(axis=1)).ravel()
    info = {
        "eigenvalues": eigenvalues,
        "eigen_solver": solver,
        "graph": graph_info,
        "laplacian": laplacian_name,
        "eigenvector_selection": eigenvector_selection,
        "sign_convention": sign_convention,
        "row_normalize": row_normalized,
        "n_undirected_edges": int(weights.nnz // 2),
        "n_connected_components": int(n_components_graph),
        "degree_min": float(degrees.min()) if degrees.size else 0.0,
        "degree_mean": float(degrees.mean()) if degrees.size else 0.0,
        "degree_max": float(degrees.max()) if degrees.size else 0.0,
        "shared_eq4_path": True,
    }
    return embedding, info
