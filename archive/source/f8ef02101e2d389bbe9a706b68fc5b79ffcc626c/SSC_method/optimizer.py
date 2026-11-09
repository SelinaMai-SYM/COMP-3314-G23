"""IRLS shrinkage. The default linear step is Equation (13), not Algorithm 1 line 10.

The solve uses scipy.sparse.linalg.spsolve. It does not form an explicit inverse.
``variant="E13"`` keeps A = S + gamma * Ltilde. ``variant="E8"`` uses
A = S + 2 * gamma * Ltilde, the stationary system of the printed Equation (8)
under the ordered-pair sum. The two variants are not the same problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from SSC_method.graph_construction import median_positive
from SSC_method.objective import (
    equation8_objective,
    row_l2_norms,
    shrinkage_laplacian,
    sqrt_smoothed_equation8_objective,
    trace_surrogate,
)

# Multiplier on gamma * Ltilde inside A = S + c * gamma * Ltilde.
# E13 is the printed Equation (13). E8 is the ordered-pair stationary
# system of the printed Equation (8); the 2 is derived, not tuned.
LINEAR_SYSTEM_VARIANTS: dict[str, float] = {
    "E13": 1.0,
    "E8": 2.0,
}


@dataclass
class ShrinkResult:
    """Shrunk patterns and diagnostics for one linear-system variant.

    ``equation8_objective`` in the history is the nonsmooth printed Equation (8).
    ``sqrt_smoothed_equation8_objective`` is a different function.
    ``irls_quadratic_surrogate`` is the frozen-weight quadratic the linear step
    minimized. ``fixed_point_residual`` is a matrix residual of that variant's
    linear system. These four numbers are not interchangeable.
    """

    patterns: np.ndarray
    n_iterations: int
    converged: bool
    history: list[dict[str, float]] = field(default_factory=list)
    initial_zero_residual_floor: float | None = None
    fixed_point_residual: float = np.nan
    variant: str = "E13"
    laplacian_coefficient: float = 1.0

    @property
    def G(self) -> np.ndarray:
        return self.patterns


def variant_laplacian_coefficient(variant: str) -> float:
    """Return c in A = S + c * gamma * Ltilde.

    ``E13`` returns 1 (printed Equation 13). ``E8`` returns 2 (ordered-pair
    stationary system of printed Equation 8).
    """
    if variant not in LINEAR_SYSTEM_VARIANTS:
        known = ", ".join(LINEAR_SYSTEM_VARIANTS)
        raise ValueError(f"unknown linear-system variant {variant!r}; expected one of {known}")
    return float(LINEAR_SYSTEM_VARIANTS[variant])


def _median_pairwise_row_distance(patterns: np.ndarray) -> float:
    """Median positive pairwise row distance, used only when every residual is zero.

    For n > 1500 the median is estimated from a deterministic subsample of
    pairs. The value is a scale for an otherwise undefined weight, not the
    Gaussian bandwidth delta.
    """
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


def _initial_denominator_floor(
    patterns: np.ndarray,
    eps: float,
    zero_residual_floor: str | float,
) -> float:
    """Scale that replaces a zero row norm at the initial all-zero residual.

    Equation (10) divides by ||h_i||. At G_0 = F every residual is zero. Using
    ``eps`` there makes S enormous, and the next G stays at F even when F is
    not stationary. The default scale is the median pairwise distance between
    rows of G_0. This scale is applied only on that initial undefined step.
    Re-applying it whenever a later iterate is numerically close to F makes
    the iteration cycle, so callers must not use it again.
    """
    if zero_residual_floor == "median_pairwise":
        floor = _median_pairwise_row_distance(patterns)
    elif zero_residual_floor == "eps":
        floor = eps
    else:
        floor = float(zero_residual_floor)
    if not np.isfinite(floor) or floor < 0.0:
        raise ValueError("zero_residual_floor must be finite and nonnegative")
    return max(float(floor), float(eps))


def solve_spd_system(matrix: sparse.spmatrix, rhs: np.ndarray) -> np.ndarray:
    """Solve a sparse symmetric system without forming an inverse.

    The coefficient is symmetrized before the call. ``spsolve`` factorizes
    the sparse matrix (SuperLU when UMFPACK is absent); it does not compute
    a dense inverse.
    """
    coefficient = sparse.csc_matrix(matrix, dtype=np.float64)
    coefficient = ((coefficient + coefficient.T) * 0.5).tocsc()
    rhs = np.asarray(rhs, dtype=np.float64)
    solution = np.asarray(spsolve(coefficient, rhs), dtype=np.float64)
    if rhs.ndim == 1:
        return solution.reshape(-1)
    return solution.reshape(rhs.shape)


def shrink_embedding(
    embedding: np.ndarray,
    affinity: sparse.spmatrix | np.ndarray,
    gamma: float,
    eps: float = 1e-8,
    tol: float = 1e-6,
    max_iter: int = 100,
    G_init: np.ndarray | None = None,
    zero_residual_floor: str | float = "median_pairwise",
    variant: str = "E13",
) -> ShrinkResult:
    """Iterate A G = S F, with A = S + c * gamma * Ltilde.

    ``variant="E13"`` (the default) uses c = 1, which is the printed
    Equation (13): G = (S + gamma Ltilde)^{-1} S F. ``variant="E8"`` uses
    c = 2, the stationary system of the printed Equation (8) when the graph
    sum runs over ordered pairs of a symmetric W. Omitting ``variant`` keeps
    the historical Equation (13) solve.

    ``affinity`` is the fixed kNN weight W built on the spectral embedding.
    Wtilde and Ltilde are recomputed from the current G on every iteration,
    because Equation (11) depends on G. Algorithm 1 line 10, which multiplies
    by X and uses Wtilde in place of Ltilde, is not implemented. S stays the
    n by n row-wise diagonal; Equation (10)'s embedding-dimension diagonal is
    not used.

    The default start is G_0 = F. The paper does not specify an initialization;
    G_0 = F is an assumption. Equation (10) is undefined at that point because
    every row residual is zero. The first iteration only replaces that zero
    scale by ``zero_residual_floor`` (default: median pairwise row distance).
    Later iterations floor individual zero rows with ``eps``. Using the large
    scale on every later visit to F makes the iteration cycle.
    ``zero_residual_floor="eps"`` is retained and still stays at F.

    Each history row records, as separate fields, the nonsmooth Equation (8),
    the square-root smoothed objective, and the frozen IRLS quadratic
    surrogate. The returned ``fixed_point_residual`` is a fourth quantity:
    the linear residual after rebuilding S and Ltilde at the returned G.
    Convergence is the relative Frobenius step of G. The paper does not
    state a stopping rule; ``tol`` and ``max_iter`` are reproduction
    assumptions.
    """
    embedding = np.asarray(embedding, dtype=np.float64)
    if embedding.ndim != 2:
        raise ValueError("embedding F must have shape (n_samples, n_components)")
    n_samples, n_components = embedding.shape
    if not np.isfinite(embedding).all():
        raise ValueError("embedding contains non-finite values")
    gamma = float(gamma)
    if not np.isfinite(gamma) or gamma < 0.0:
        raise ValueError("gamma must be finite and nonnegative")
    eps = float(eps)
    if not np.isfinite(eps) or eps < 0.0:
        raise ValueError("eps must be finite and nonnegative")
    if tol < 0.0 or not np.isfinite(tol):
        raise ValueError("tol must be finite and nonnegative")
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1")
    laplacian_coefficient = variant_laplacian_coefficient(variant)
    weights = sparse.csr_matrix(affinity, dtype=np.float64)
    if weights.shape != (n_samples, n_samples):
        raise ValueError("affinity must be square with one row per embedding row")
    if np.any(weights.data < 0.0):
        raise ValueError("affinity weights must be nonnegative")

    if G_init is None:
        patterns = np.array(embedding, dtype=np.float64, copy=True)
    else:
        patterns = np.array(G_init, dtype=np.float64, copy=True)
        if patterns.shape != embedding.shape:
            raise ValueError("G_init must have the same shape as F")
        if not np.isfinite(patterns).all():
            raise ValueError("G_init contains non-finite values")

    history: list[dict[str, float]] = []
    initial_floor: float | None = None
    converged = False
    for iteration in range(max_iter):
        residual_norms = row_l2_norms(patterns - embedding)
        # The median scale is only for the initial undefined residual. Later
        # iterations always floor with eps, including rows that individually hit 0.
        if initial_floor is None and np.all(residual_norms <= eps):
            floor = _initial_denominator_floor(patterns, eps, zero_residual_floor)
            initial_floor = floor
        else:
            floor = eps
        s_diagonal = 1.0 / (2.0 * np.maximum(residual_norms, floor))
        _, laplacian = shrinkage_laplacian(weights, patterns, eps=eps)
        coefficient = sparse.diags(s_diagonal) + (laplacian_coefficient * gamma) * laplacian
        rhs = s_diagonal[:, None] * embedding
        updated = solve_spd_system(coefficient, rhs)
        if not np.isfinite(updated).all():
            raise RuntimeError(f"variant {variant} produced a non-finite G")
        residual_matrix = coefficient @ updated - rhs
        linear_residual = float(np.linalg.norm(residual_matrix))
        step = float(np.linalg.norm(updated - patterns))
        # Printed nonsmooth Equation (8), independent of which linear system
        # was solved. E13 does not minimize this function.
        exact = equation8_objective(updated, embedding, weights, gamma)
        smoothed = sqrt_smoothed_equation8_objective(updated, embedding, weights, gamma, eps)
        # Quadratic actually minimized with S and Ltilde frozen. The graph
        # multiplier is c * gamma, so E8's surrogate is not printed Equation (12).
        surrogate = trace_surrogate(
            updated,
            embedding,
            s_diagonal,
            laplacian,
            laplacian_coefficient * gamma,
        )
        history.append(
            {
                "iteration": float(iteration),
                "equation8_objective": exact,
                "sqrt_smoothed_equation8_objective": smoothed,
                "irls_quadratic_surrogate": surrogate,
                "linear_residual": linear_residual,
                "step_frobenius": step,
                "denominator_floor": float(floor),
                "s_min": float(np.min(s_diagonal)),
                "s_max": float(np.max(s_diagonal)),
                "laplacian_coefficient": laplacian_coefficient,
            }
        )
        scale = 1.0 + float(np.linalg.norm(patterns))
        patterns = updated
        if step <= tol * scale:
            converged = True
            break

    final_norms = row_l2_norms(patterns - embedding)
    # Same ongoing floor as every iteration after the initial step.
    final_floor = eps
    # The fixed-point residual rebuilds S and Ltilde at the returned G.
    # A small linear residual inside the loop only says that one frozen
    # system was solved. This residual says that variant's system
    # A G = S F holds at G. For E13, A is Equation (13). For E8, A carries
    # the extra factor 2. It is not the Equation (8) objective.
    s_final = 1.0 / (2.0 * np.maximum(final_norms, final_floor))
    _, laplacian_final = shrinkage_laplacian(weights, patterns, eps=eps)
    coefficient_final = sparse.diags(s_final) + (laplacian_coefficient * gamma) * laplacian_final
    rhs_final = s_final[:, None] * embedding
    fixed_point_residual = float(np.linalg.norm(coefficient_final @ patterns - rhs_final))
    return ShrinkResult(
        patterns=patterns,
        n_iterations=len(history),
        converged=converged,
        history=history,
        initial_zero_residual_floor=initial_floor,
        fixed_point_residual=fixed_point_residual,
        variant=variant,
        laplacian_coefficient=laplacian_coefficient,
    )


def iteration_diagnostics(result: ShrinkResult) -> dict[str, Any]:
    """Compact view of the last recorded iteration."""
    if not result.history:
        return {"n_iterations": 0, "converged": result.converged}
    last = result.history[-1]
    return {
        "n_iterations": result.n_iterations,
        "converged": result.converged,
        "variant": result.variant,
        "laplacian_coefficient": result.laplacian_coefficient,
        "equation8_objective": last["equation8_objective"],
        "sqrt_smoothed_equation8_objective": last["sqrt_smoothed_equation8_objective"],
        "irls_quadratic_surrogate": last["irls_quadratic_surrogate"],
        "linear_residual": last["linear_residual"],
        "fixed_point_residual": result.fixed_point_residual,
        "initial_zero_residual_floor": result.initial_zero_residual_floor,
    }
