"""Spectral embedding from the symmetric normalized Laplacian, Equation (4).

The embedding is the c eigenvectors for the smallest eigenvalues. It is not
PCA, and it does not call scikit-learn spectral clustering.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.linalg import eigh
from scipy.sparse.linalg import eigsh

from SSC_method.graph_construction import knn_affinity, symmetric_normalized_laplacian


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


def spectral_embedding(
    X: np.ndarray,
    n_components: int,
    k: int = 5,
    delta2: float | None = None,
    dense_threshold: int = 512,
    knn_method: str = "auto",
    bandwidth_rule: str | None = None,
    row_normalize: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    """c smallest eigenvectors of the symmetric normalized Laplacian.

    ``k`` defaults to 5, the neighborhood size stated for the spectral
    algorithms in the paper. The Gaussian bandwidth is not taken from a
    library default; see ``knn_affinity``. Raw eigenvectors are the default.
    Row normalization is a diagnostic, not the paper's stated embedding.
    """
    affinity, graph_info = knn_affinity(
        X, k=k, delta2=delta2, knn_method=knn_method, bandwidth_rule=bandwidth_rule
    )
    laplacian = symmetric_normalized_laplacian(affinity)
    eigenvalues, embedding, solver = smallest_eigenpairs(
        laplacian, n_components, dense_threshold=dense_threshold
    )
    row_normalized = bool(row_normalize)
    if row_normalized:
        norms = np.linalg.norm(embedding, axis=1, keepdims=True)
        embedding = embedding / np.maximum(norms, 1e-12)
    info = {
        "eigenvalues": eigenvalues,
        "eigen_solver": solver,
        "graph": graph_info,
        "laplacian": "symmetric_normalized_eq4",
        "row_normalize": row_normalized,
        "n_undirected_edges": int(sparse.csr_matrix(affinity).nnz // 2),
    }
    return embedding, info
