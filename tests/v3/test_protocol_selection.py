"""Best inertia is not best accuracy."""

from __future__ import annotations

from experiments.v3_reproduction.compare_paper import summarize_batch


def test_min_inertia_is_not_max_accuracy() -> None:
    rows = [
        {"acc": 0.9, "nmi": 0.8, "selection_value": 5.0, "selection_rule": "min_inertia", "seed": 1},
        {"acc": 0.4, "nmi": 0.3, "selection_value": 1.0, "selection_rule": "min_inertia", "seed": 2},
    ]
    summary = summarize_batch(rows)
    assert summary["selected_acc"] == 0.4
    assert summary["per_run_acc_sd"] is not None
    assert "selected_sd" not in summary
