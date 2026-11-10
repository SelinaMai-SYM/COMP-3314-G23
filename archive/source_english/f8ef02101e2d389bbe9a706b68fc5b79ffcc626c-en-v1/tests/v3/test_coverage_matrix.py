"""The historical matrix is exactly 72 cells."""

from __future__ import annotations

from experiments.v3_reproduction.job_plan import historical_cells
from experiments.v3_reproduction.protocol_registry import HISTORICAL_BENCHMARKS, HISTORICAL_METHODS


def test_seventy_two_cells_keep_blockers() -> None:
    cells = historical_cells([])
    assert len(cells) == len(HISTORICAL_METHODS) * len(HISTORICAL_BENCHMARKS) == 72
    blocked = {(cell["benchmark"], cell["method"]) for cell in cells if cell["blocker"]}
    assert ("AR", "kmeans") in blocked
    assert ("MSRA50", "ssc") in blocked
    assert ("JAFFE", "lda_sc") in {(cell["benchmark"], cell["method"]) for cell in cells if cell["blocker"] == "BLOCKED_METHOD"}
    assert len({cell["cell_id"] for cell in cells}) == 72
