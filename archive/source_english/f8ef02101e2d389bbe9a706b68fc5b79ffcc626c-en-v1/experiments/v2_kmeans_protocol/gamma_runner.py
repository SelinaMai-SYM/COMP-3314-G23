"""Gamma grid on a fixed F.

G is rebuilt for each predetermined gamma. SC trials are not recomputed.
The gamma that maximizes labeled ACC is recorded only as ORACLE_BEST_TEST_ACC.
"""

from __future__ import annotations

from experiments.v2_kmeans_protocol.dataset_registry import DatasetEntry
from experiments.v2_kmeans_protocol.protocol_runner import run_gamma_grid
from experiments.v2_kmeans_protocol.representation_cache import GAMMA_GRID

ORACLE_LABEL = "ORACLE_BEST_TEST_ACC"


def run(entry: DatasetEntry, *, max_iter: int = 300) -> None:
    """Recompute G on ``GAMMA_GRID`` and cluster each G with P1–P4."""
    if list(GAMMA_GRID) != [1e-6, 1e-3, 1.0, 1e3, 1e6]:
        raise RuntimeError("the gamma grid was edited after it was predetermined")
    run_gamma_grid(entry, max_iter=max_iter)


__all__ = ["ORACLE_LABEL", "run"]
