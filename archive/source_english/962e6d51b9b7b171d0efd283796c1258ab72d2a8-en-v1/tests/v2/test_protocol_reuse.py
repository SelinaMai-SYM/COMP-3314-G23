"""P2/P4 read the saved batch. They do not launch another 50 trials."""

from __future__ import annotations

import numpy as np

from experiments.v2_kmeans_protocol.dataset_registry import DatasetEntry
from experiments.v2_kmeans_protocol.kmeans_trials import RANDOM
from experiments.v2_kmeans_protocol.protocol_runner import read_trials, run_family, trials_path
from experiments.v2_kmeans_protocol.select_best_inertia import select_min_inertia


def _entry() -> DatasetEntry:
    return DatasetEntry(
        benchmark="Toy",
        version="v",
        paper_benchmark="ORL",
        attempt_load=False,
        run_protocols=True,
        exact_dataset_status="TOY",
        comparison_class="NOT_COMPARABLE",
        benchmark_group="Toy",
        counts_as_independent_benchmark=True,
        priority_repeat=False,
        notes="synthetic",
    )


def test_second_call_does_not_append(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("experiments.v2_kmeans_protocol.protocol_runner.TRIALS_ROOT", tmp_path)
    monkeypatch.setattr("experiments.v2_kmeans_protocol.protocol_runner.ARRAYS_ROOT", tmp_path / "arrays")
    features = np.random.default_rng(0).normal(size=(24, 3))
    labels = np.array([0, 1] * 12)
    entry = _entry()
    kwargs = dict(
        method="SC",
        representation="F",
        initialization_label=RANDOM,
        seeds=[0, 1, 2],
        batch_id=0,
        gamma_label="NA",
        solver_status="NOT_APPLICABLE_SPECTRAL_EMBEDDING",
        ssc_converged="",
        representation_sha="abc",
        dataset_sha="def",
        config_hash_value="ghi",
    )
    first = run_family(entry, features, labels, **kwargs)
    second = run_family(entry, features, labels, **kwargs)
    saved = read_trials(trials_path(entry))
    assert len(first) == 3
    assert second == []
    assert len(saved) == 3
    selected = select_min_inertia(
        [{"seed": int(row["seed"]), "inertia": float(row["inertia"]), "acc": float(row["acc"])} for row in saved]
    )
    expected = min(saved, key=lambda row: (float(row["inertia"]), int(row["seed"])))
    assert int(selected["seed"]) == int(expected["seed"])
    assert float(selected["inertia"]) == float(expected["inertia"])
