"""Fingerprints notice a swapped sample. Missing data stays blocked."""

from __future__ import annotations

import numpy as np

from experiments.v3_reproduction.job_plan import historical_cells
from experiments.v3_reproduction.provenance import fingerprint_matrix


def test_swapping_rows_changes_the_fingerprint() -> None:
    features = np.arange(8, dtype=np.float64).reshape(4, 2)
    labels = np.array([0, 0, 1, 1])
    assert fingerprint_matrix(features, labels)["x_sha256"] != fingerprint_matrix(features[::-1], labels)["x_sha256"]


def test_blocked_historical_datasets_remain_cells() -> None:
    cells = historical_cells(
        [
            {
                "dataset_id": "AR",
                "historical_benchmark": "AR",
                "counts_as_historical": True,
                "available": False,
                "blocker": "BLOCKED_DATA",
            }
        ]
    )
    ar = [cell for cell in cells if cell["benchmark"] == "AR"]
    assert len(ar) == 9
    assert all(cell["blocker"] for cell in ar)
