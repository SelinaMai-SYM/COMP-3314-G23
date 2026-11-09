"""The experiment runner must write the required artifacts and status transitions."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

import pytest

from experiments.io import RunWriter, config_hash, make_run_id
from experiments.protocol import track_b_dimension
from scripts import run_experiment as runner


def test_status_transitions_are_recorded(tmp_path: Path):
    writer = RunWriter(tmp_path / "run")
    writer.write_status("PLANNED")
    writer.write_status("RUNNING")
    writer.write_status("COMPLETED")
    status = writer.read_status()
    assert status["status"] == "COMPLETED"
    names = [row["status"] for row in status["transitions"]]
    assert names == ["PLANNED", "RUNNING", "COMPLETED"]
    assert "started_at" in status
    assert "finished_at" in status


def test_illegal_transition_is_rejected(tmp_path: Path):
    writer = RunWriter(tmp_path / "run")
    writer.write_status("PLANNED")
    with pytest.raises(RuntimeError, match="illegal status transition"):
        writer.write_status("COMPLETED")


def test_run_id_uses_clock_and_hash():
    cfg = {"track": "PILOT", "method": "ssc", "dataset": "ORL", "n_trials": 3}
    hashed = config_hash(cfg)
    run_id = make_run_id("PILOT", "SSC", "ORL", hashed)
    parts = run_id.split("__")
    assert len(parts) == 5
    assert parts[1] == "PILOT"
    assert parts[2] == "SSC"
    assert parts[3] == "ORL"
    assert parts[4] == hashed
    assert len(parts[0]) == 15


def test_track_b_dimension_does_not_use_labels():
    assert track_b_dimension(400, 1024, 40, lda=False) == 40
    assert track_b_dimension(400, 1024, 40, lda=True) == 39
    assert track_b_dimension(213, 676, 10, lda=True) == 9
    assert track_b_dimension(2414, 1024, 38, lda=False) == 38


def test_synthetic_runner_writes_required_files(tmp_path: Path, monkeypatch):
    x = np.array([[0.0, 0.0], [0.1, 0.0], [5.0, 0.0], [5.1, 0.0]], dtype=np.float64)
    y = np.array([0, 0, 1, 1], dtype=np.int64)

    def fake_load(_name):
        return x, y, {"dataset_name": "SYNTHETIC", "n": 4, "number_of_classes": 2}

    monkeypatch.setattr(runner, "load_dataset", fake_load)
    config = {
        "track": "PILOT",
        "method": "kmeans",
        "dataset": "SYNTHETIC",
        "n_trials": 2,
        "trial_seed_start": 0,
        "params": {},
        "notes": "artifact test",
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    run_dir = runner.run_config(config, tmp_path / "runs")
    required = [
        "config.yaml",
        "metadata.json",
        "environment.json",
        "stdout.log",
        "stderr.log",
        "status.json",
        "metrics.json",
    ]
    for name in required:
        assert (run_dir / name).is_file(), name
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "COMPLETED"
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["n_trials_completed"] == 2
    assert metrics["n_samples"] == 4
    for trial in metrics["trials"]:
        assert 0.0 <= trial["acc"] <= 1.0
        assert 0.0 <= trial["nmi"] <= 1.0
        assert trial["n_predicted_labels"] == 4
