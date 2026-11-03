"""Alpha-weighted IRLS for the ordered-pair E8 system.

When every alpha_i is 1, the linear system is the original E8 system
A = S + 2 gamma Ltilde. The extension calls the original sparse solve for
n <= 4000. Larger systems use Jacobi-preconditioned CG and fall back to the
original solve if CG does not return. Callers that need a byte-level match
pass ``solver='original'``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, cg

from SSC_method.graph_construction import median_positive
from SSC_method.objective import equation8_objective, graph_l2_term, row_l2_norms, shrinkage_laplacian
from SSC_method.optimizer import solve_spd_system, variant_laplacian_coefficient

DIRECT_SOLVER_MAX_N = 20000
CG_RTOL = 1e-12
CG_ATOL = 1e-10
MATCH_ATOL = 1e-5
MATCH_RTOL = 1e-5


@dataclass
class AlphaShrinkResult:
    patterns: np.ndarray
    n_iterations: int
    converged: bool
    history: list[dict[str, float]] = field(default_factory=list)
    fixed_point_residual: float = np.nan
    objective_name: str = "alpha_weighted_equation8"
    objective_value: float = np.nan
    equation8_value: float = np.nan
    solver: str = "original_spsolve"
    cg_fallbacks: int = 0
    laplacian_coefficient: float = 2.0


def _median_pairwise(patterns: np.ndarray) -> float:
    patterns = np.asarray(patterns, dtype=np.float64)
    n_samples = patterns.shape[0]
    if n_samples <= 1500:
        difference = patterns[:, None, :] - patterns[None, :, :]
        distance = np.linalg.norm(difference, axis=-1)
        iu = np.triu_indices(n_samples, k=1)
        return median_positive(distance[iu], fallback=1.0)
    rng = np.random.default_rng(0)
    n_pairs = min(8192, n_samples * (n_samples - 1) // 2)
    left = rng.integers(0, n_samples, size=n_pairs)
    right = rng.integers(0, n_samples, size=n_pairs)
    distinct = left != right
    distance = np.linalg.norm(patterns[left[distinct]] - patterns[right[distinct]], axis=1)
    return median_positive(distance, fallback=1.0)


def _initial_floor(patterns: np.ndarray, eps: float, zero_residual_floor: str | float) -> float:
    if zero_residual_floor == "median_pairwise":
        floor = _median_pairwise(patterns)
    elif zero_residual_floor == "eps":
        floor = eps
    else:
        floor = float(zero_residual_floor)
    if not np.isfinite(floor) or floor < 0.0:
        raise ValueError("zero_residual_floor must be finite and nonnegative")
    return max(float(floor), float(eps))


def _solve_cg(matrix: sparse.spmatrix, rhs: np.ndarray) -> np.ndarray:
    coefficient = sparse.csc_matrix(matrix, dtype=np.float64)
    coefficient = ((coefficient + coefficient.T) * 0.5).tocsc()
    rhs = np.asarray(rhs, dtype=np.float64)
    diagonal = np.abs(np.asarray(coefficient.diagonal(), dtype=np.float64).ravel())
    inverse = 1.0 / np.maximum(diagonal, 1e-18)
    preconditioner = LinearOperator(coefficient.shape, matvec=lambda vector: inverse * vector)
    columns = []
    for column in range(rhs.shape[1]):
        solution, info = cg(
            coefficient,
            rhs[:, column],
            rtol=CG_RTOL,
            atol=CG_ATOL,
            M=preconditioner,
            maxiter=20000,
        )
        if int(info) != 0 or not np.isfinite(solution).all():
            raise RuntimeError(f"cg info {info}")
        columns.append(solution)
    return np.column_stack(columns)


def solve_extension_system(
    matrix: sparse.spmatrix,
    rhs: np.ndarray,
    solver: str = "auto",
) -> tuple[np.ndarray, str, bool]:
    """Return the solution, the solver name, and whether CG fell back."""
    rhs = np.asarray(rhs, dtype=np.float64)
    n_samples = int(matrix.shape[0])
    use_direct = solver == "original" or (solver == "auto" and n_samples <= DIRECT_SOLVER_MAX_N)
    if use_direct:
        return solve_spd_system(matrix, rhs), "original_spsolve", False
    try:
        return _solve_cg(matrix, rhs), "jacobi_cg", False
    except RuntimeError:
        return solve_spd_system(matrix, rhs), "original_spsolve_fallback", True


def alpha_weighted_equation8(
    patterns: np.ndarray,
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    alpha: np.ndarray,
) -> float:
    """sum_i alpha_i ||g_i - f_i|| + gamma * sum_ij W_ij ||g_i - g_j||.

    This is Equation (8) only when every alpha_i equals 1. Do not compare the
    number with a different weight matrix or a different alpha.
    """
    residual = np.asarray(patterns, dtype=np.float64) - np.asarray(embedding, dtype=np.float64)
    data = float(np.sum(np.asarray(alpha, dtype=np.float64) * row_l2_norms(residual)))
    return data + float(gamma) * graph_l2_term(patterns, affinity)


def shrink_embedding_alpha(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    alpha: np.ndarray | None = None,
    gamma: float = 1.0,
    eps: float = 1e-8,
    tol: float = 1e-6,
    max_iter: int = 100,
    G_init: np.ndarray | None = None,
    zero_residual_floor: str | float = "median_pairwise",
    variant: str = "E8",
    solver: str = "auto",
) -> AlphaShrinkResult:
    """Iterate A G = S_alpha F with S_ii = alpha_i / (2 max(||g_i-f_i||, floor))."""
    embedding = np.asarray(embedding, dtype=np.float64)
    n_samples, _n_components = embedding.shape
    if alpha is None:
        alpha = np.ones(n_samples, dtype=np.float64)
    alpha = np.asarray(alpha, dtype=np.float64)
    if alpha.shape != (n_samples,):
        raise ValueError("alpha must have one weight per row")
    if not np.isfinite(alpha).all() or np.any(alpha < 0.0):
        raise ValueError("alpha must be finite and nonnegative")
    gamma = float(gamma)
    eps = float(eps)
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1")
    coefficient_scale = variant_laplacian_coefficient(variant)
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    if weights.shape != (n_samples, n_samples):
        raise ValueError("affinity must be square")
    if weights.nnz and np.any(weights.data < 0.0):
        raise ValueError("affinity weights must be nonnegative")
    patterns = np.array(embedding if G_init is None else G_init, dtype=np.float64, copy=True)
    history: list[dict[str, float]] = []
    initial_floor: float | None = None
    converged = False
    solver_name = "original_spsolve"
    fallbacks = 0
    for iteration in range(int(max_iter)):
        residual_norms = row_l2_norms(patterns - embedding)
        if initial_floor is None and np.all(residual_norms <= eps):
            floor = _initial_floor(patterns, eps, zero_residual_floor)
            initial_floor = floor
        else:
            floor = eps
        s_diagonal = alpha / (2.0 * np.maximum(residual_norms, floor))
        _reweighted, laplacian = shrinkage_laplacian(weights, patterns, eps=eps)
        coefficient = sparse.diags(s_diagonal) + (coefficient_scale * gamma) * laplacian
        rhs = s_diagonal[:, None] * embedding
        updated, solver_name, fell_back = solve_extension_system(coefficient, rhs, solver=solver)
        fallbacks += int(fell_back)
        if not np.isfinite(updated).all():
            raise RuntimeError("alpha-weighted shrinkage produced a non-finite G")
        step = float(np.linalg.norm(updated - patterns))
        objective = alpha_weighted_equation8(updated, embedding, weights, gamma, alpha)
        exact = equation8_objective(updated, embedding, weights, gamma)
        history.append(
            {
                "iteration": float(iteration),
                "alpha_weighted_equation8": objective,
                "equation8_objective": exact,
                "step_frobenius": step,
                "denominator_floor": float(floor),
                "laplacian_coefficient": coefficient_scale,
            }
        )
        scale = 1.0 + float(np.linalg.norm(patterns))
        patterns = updated
        if step <= float(tol) * scale:
            converged = True
            break
    final_norms = row_l2_norms(patterns - embedding)
    s_final = alpha / (2.0 * np.maximum(final_norms, eps))
    _reweighted, laplacian_final = shrinkage_laplacian(weights, patterns, eps=eps)
    coefficient_final = sparse.diags(s_final) + (coefficient_scale * gamma) * laplacian_final
    rhs_final = s_final[:, None] * embedding
    residual = float(np.linalg.norm(coefficient_final @ patterns - rhs_final))
    return AlphaShrinkResult(
        patterns=patterns,
        n_iterations=len(history),
        converged=converged,
        history=history,
        fixed_point_residual=residual,
        objective_name="alpha_weighted_equation8",
        objective_value=float(history[-1]["alpha_weighted_equation8"]) if history else np.nan,
        equation8_value=float(history[-1]["equation8_objective"]) if history else np.nan,
        solver=solver_name,
        cg_fallbacks=fallbacks,
        laplacian_coefficient=coefficient_scale,
    )
