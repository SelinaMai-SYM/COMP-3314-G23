"""Completed measurements survive a later resource-only commit."""

import json
from pathlib import Path

from experiments.v3_reproduction.runner import _done


def test_prior_measurement_commit_is_reused(tmp_path: Path) -> None:
    payload = {
        "runs_dir": str(tmp_path),
        "dataset_id": "JAFFE",
        "code_commit": "new",
        "accepted_measurement_commits": ["962e6d51b9b7b171d0efd283796c1258ab72d2a8"],
        "invalidate_methods": [],
        "resume": True,
    }
    folder = tmp_path / "JAFFE"
    folder.mkdir()
    (folder / "kmeans__Y0.json").write_text(
        json.dumps(
            {
                "status": "COMPLETED",
                "code_commit": "962e6d51b9b7b171d0efd283796c1258ab72d2a8",
                "method": "kmeans",
                "n_trials": 1,
            }
        )
    )
    (folder / "kmeans__Y0.trials.jsonl").write_text("{}\n")
    assert _done(payload, "kmeans__Y0")


def test_invalidated_method_is_not_reused(tmp_path: Path) -> None:
    payload = {
        "runs_dir": str(tmp_path),
        "dataset_id": "JAFFE",
        "code_commit": "new",
        "accepted_measurement_commits": ["old"],
        "invalidate_methods": ["spls"],
        "resume": True,
    }
    folder = tmp_path / "JAFFE"
    folder.mkdir()
    (folder / "spls__Y0.json").write_text(
        json.dumps(
            {"status": "COMPLETED", "code_commit": "old", "method": "spls", "n_trials": 1}
        )
    )
    (folder / "spls__Y0.trials.jsonl").write_text("{}\n")
    assert not _done(payload, "spls__Y0")
