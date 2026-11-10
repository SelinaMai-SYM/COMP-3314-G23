"""Saved rows, blank SDs, and traceable paper numbers."""

from experiments.paper_reported import ACC
from experiments.v2_kmeans_protocol.aggregate_results import _summarize
from experiments.v2_kmeans_protocol.paper_comparison import numeric_gap, paper_stat
from experiments.v2_kmeans_protocol.verify_provenance import check_paper_trace


def test_best_inertia_summary_has_no_sd() -> None:
    trials = [
        {
            "inertia": "2.0",
            "seed": "0",
            "acc": "0.4",
            "nmi": "0.5",
            "wall_seconds": "0.1",
            "trial_id": "a",
            "ssc_optimizer_status": "CONVERGED n_iter=1",
        },
        {
            "inertia": "1.0",
            "seed": "1",
            "acc": "0.7",
            "nmi": "0.6",
            "wall_seconds": "0.2",
            "trial_id": "b",
            "ssc_optimizer_status": "CONVERGED n_iter=1",
        },
    ]
    summary = _summarize(trials, "MIN_INERTIA")
    assert summary["acc_sd_percent"] is None
    assert summary["nmi_sd_percent"] is None
    assert summary["inertia_sd"] is None
    assert summary["trial_id"] == "b"
    assert summary["selected_seed"] == 1
    mean = _summarize(trials, "MEAN_OF_TRIALS")
    assert mean["acc_sd_percent"] is not None
    assert len(trials) == 2


def test_incomparable_gap_is_not_zero() -> None:
    assert numeric_gap(0.5, 40.0, "NOT_COMPARABLE") == "NOT_COMPARABLE"
    assert numeric_gap(None, 40.0, "EXPLORATORY") == "NOT_COMPARABLE"


def test_paper_numbers_match_the_audited_module() -> None:
    assert check_paper_trace() == []
    mean, sd = paper_stat("acc", "ssc", "YaleB")
    assert (mean, sd) == ACC["ssc"]["YaleB"] == (49.8, 1.6)
    sc_nmi, _ = paper_stat("nmi", "sc", "YaleB")
    ssc_nmi, _ = paper_stat("nmi", "ssc", "YaleB")
    assert ssc_nmi < sc_nmi
