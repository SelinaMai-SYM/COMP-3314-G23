"""Explicit knobs for the shared Eq. (4) spectral graph and embedding.

Chang et al. (AAAI 2015) use the same neighborhood graph and symmetric
normalized Laplacian for spectral clustering and for the SSC embedding F.
This config is that shared contract. LLC and LDA graphs are not forced
through it: those methods keep the constructions defined in their papers.

Fields above the shrinkage block determine F. Fields below it are recorded
so E8/E13, G0, the IRLS tolerance, and K-means are not silent. They do not
change the eigenvectors.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping


SIGN_CONVENTION = "largest_magnitude_positive"
DEFAULT_LAPLACIAN = "symmetric_normalized_eq4"
DEFAULT_EIGENVECTORS = "smallest"
DEFAULT_SYMMETRIZATION = "union"
DEFAULT_BANDWIDTH_RULE = "median_positive_knn_squared_distance"

SYMMETRIZATION_ALIASES = {
    "union": "union_maximum",
    "union_maximum": "union_maximum",
    "mutual": "mutual_and",
    "mutual_and": "mutual_and",
}

LAPLACIANS = {
    "symmetric_normalized_eq4",
    "combinatorial",
}

EIGENVECTOR_SELECTIONS = {"smallest"}
SIGN_CONVENTIONS = {SIGN_CONVENTION}


@dataclass(frozen=True)
class SpectralGraphConfig:
    """Shared Eq. (4) graph / Laplacian / eigensolve configuration.

    Paper-stated or locked defaults:
    - ``k=5`` for the spectral algorithms.
    - ``symmetrization="union"`` (the paper does not name union vs mutual).
    - ``laplacian="symmetric_normalized_eq4"``.
    - ``eigenvector_selection="smallest"`` (c eigenvectors, ascending).
    - ``row_normalize=False`` (Ng-Jordan-Weiss row-norm is Category C).

    Reproduction assumptions, not paper values:
    - omitted ``delta2`` uses the median of positive directed kNN squared
      distances as ``delta^2``;
    - ``knn_method="auto"`` is dense mergesort for n <= 1500, otherwise block
      ``argpartition``;
    - ``dense_threshold=512`` switches ``eigh`` to ``eigsh``;
    - eigenvector signs follow ``largest_magnitude_positive``.

    Shrinkage / clustering knobs default to the historical call-site values.
    ``variant="E13"`` is the printed Equation (13), not a claim that the
    authors' unreleased code used Equation (8)'s stationary system.
    """

    k: int = 5
    delta2: float | None = None
    delta: float | None = None
    bandwidth_rule: str | None = None
    symmetrization: str = DEFAULT_SYMMETRIZATION
    laplacian: str = DEFAULT_LAPLACIAN
    eigenvector_selection: str = DEFAULT_EIGENVECTORS
    row_normalize: bool = False
    knn_method: str = "auto"
    dense_threshold: int = 512
    sign_convention: str = SIGN_CONVENTION
    variant: str = "E13"
    g_init: str = "F"
    g_init_seed: int = 0
    g_init_scale: float = 1e-3
    zero_residual_floor: str | float = "median_pairwise"
    tol: float = 1e-6
    max_iter: int = 300
    eps: float = 1e-8
    kmeans_init: str = "random"
    kmeans_n_init: int = 1
    seed: int | None = None

    def __post_init__(self) -> None:
        if int(self.k) < 1:
            raise ValueError("k must be >= 1")
        if self.delta is not None and self.delta2 is not None:
            raise ValueError("set only one of delta and delta2")
        if self.delta is not None:
            bandwidth = float(self.delta)
            if not np_isfinite_positive(bandwidth):
                raise ValueError("delta must be a positive finite float")
        if self.delta2 is not None:
            squared = float(self.delta2)
            if not np_isfinite_positive(squared):
                raise ValueError("delta2 must be a positive finite float")
        if normalize_symmetrization(self.symmetrization) not in {"union_maximum", "mutual_and"}:
            raise ValueError("symmetrization must be 'union' or 'mutual'")
        if self.laplacian not in LAPLACIANS:
            known = ", ".join(sorted(LAPLACIANS))
            raise ValueError(f"laplacian must be one of {known}")
        if self.eigenvector_selection not in EIGENVECTOR_SELECTIONS:
            raise ValueError("eigenvector_selection must be 'smallest'")
        if self.sign_convention not in SIGN_CONVENTIONS:
            raise ValueError(
                "sign_convention must be 'largest_magnitude_positive'"
            )
        if int(self.dense_threshold) < 1:
            raise ValueError("dense_threshold must be >= 1")
        if int(self.max_iter) < 1:
            raise ValueError("max_iter must be >= 1")
        if int(self.kmeans_n_init) < 1:
            raise ValueError("kmeans_n_init must be >= 1")

    def resolved_delta2(self) -> float | None:
        """Return the squared bandwidth, or ``None`` to use ``bandwidth_rule``."""
        if self.delta is not None:
            return float(self.delta) ** 2
        if self.delta2 is not None:
            return float(self.delta2)
        return None

    def resolved_symmetrization(self) -> str:
        return normalize_symmetrization(self.symmetrization)

    def resolved_bandwidth_rule(self) -> str | None:
        if self.bandwidth_rule is not None:
            return self.bandwidth_rule
        if self.resolved_delta2() is not None:
            return "provided"
        return DEFAULT_BANDWIDTH_RULE

    def affinity_kwargs(self) -> dict[str, Any]:
        return {
            "k": int(self.k),
            "delta2": self.resolved_delta2(),
            "knn_method": self.knn_method,
            "bandwidth_rule": self.bandwidth_rule,
            "symmetrization": self.symmetrization,
        }

    def embedding_kwargs(self) -> dict[str, Any]:
        kwargs = self.affinity_kwargs()
        kwargs.update(
            {
                "dense_threshold": int(self.dense_threshold),
                "row_normalize": bool(self.row_normalize),
                "laplacian": self.laplacian,
                "eigenvector_selection": self.eigenvector_selection,
                "sign_convention": self.sign_convention,
            }
        )
        return kwargs

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["resolved_delta2"] = self.resolved_delta2()
        payload["resolved_symmetrization"] = self.resolved_symmetrization()
        payload["resolved_bandwidth_rule"] = self.resolved_bandwidth_rule()
        payload["affects_F"] = True
        return payload

    def with_updates(self, **changes: Any) -> "SpectralGraphConfig":
        return replace(self, **changes)

    @classmethod
    def from_params(
        cls,
        params: Mapping[str, Any] | None = None,
        *,
        k: int = 5,
        for_embedding: bool = True,
    ) -> "SpectralGraphConfig":
        """Build a config from an experiment parameter mapping.

        ``embedding_delta2`` is the bandwidth of graph A on X. ``delta2`` is
        the bandwidth of graph W on F and is ignored when ``for_embedding``
        is true, so the two graphs are not silently forced to share a scale.
        """
        raw = dict(params or {})
        delta2 = raw.get("embedding_delta2") if for_embedding else raw.get("delta2")
        return cls(
            k=int(raw.get("k", k)),
            delta2=delta2,
            delta=raw.get("delta"),
            bandwidth_rule=raw.get("bandwidth_rule"),
            symmetrization=str(raw.get("symmetrization", raw.get("knn_mode", DEFAULT_SYMMETRIZATION))),
            laplacian=str(raw.get("laplacian", DEFAULT_LAPLACIAN)),
            eigenvector_selection=str(
                raw.get("eigenvector_selection", DEFAULT_EIGENVECTORS)
            ),
            row_normalize=bool(raw.get("row_normalize", False)),
            knn_method=str(raw.get("knn_method", "auto")),
            dense_threshold=int(raw.get("dense_threshold", raw.get("eigen_dense_threshold", 512))),
            sign_convention=str(raw.get("sign_convention", SIGN_CONVENTION)),
            variant=str(raw.get("variant", "E13")),
            g_init=str(raw.get("g_init", "F")),
            g_init_seed=int(raw.get("g_init_seed", 0)),
            g_init_scale=float(raw.get("g_init_scale", 1e-3)),
            zero_residual_floor=raw.get("zero_residual_floor", "median_pairwise"),
            tol=float(raw.get("tol", 1e-6)),
            max_iter=int(raw.get("max_iter", 300)),
            eps=float(raw.get("eps", 1e-8)),
            kmeans_init=str(raw.get("kmeans_init", "random")),
            kmeans_n_init=int(raw.get("kmeans_n_init", raw.get("n_init", 1))),
            seed=raw.get("seed", raw.get("random_state")),
        )


def normalize_symmetrization(name: str) -> str:
    key = str(name)
    if key not in SYMMETRIZATION_ALIASES:
        raise ValueError("symmetrization must be 'union' or 'mutual'")
    return SYMMETRIZATION_ALIASES[key]


def np_isfinite_positive(value: float) -> bool:
    return bool(math.isfinite(value) and value > 0.0)


__all__ = [
    "DEFAULT_BANDWIDTH_RULE",
    "DEFAULT_EIGENVECTORS",
    "DEFAULT_LAPLACIAN",
    "DEFAULT_SYMMETRIZATION",
    "SIGN_CONVENTION",
    "SpectralGraphConfig",
    "normalize_symmetrization",
]
