"""Label-blind summaries and explicitly marked post-hoc views."""

from __future__ import annotations

from typing import Any

import numpy as np

from experiments.v2_kmeans_protocol.metrics import mean_and_sample_sd


def summarize_batch(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-run mean/SD, and one selected score when the rule is label-blind.

    The selected ACC does not receive the SD of the 50 trials.
    """
    acc_mean, acc_sd = mean_and_sample_sd([row["acc"] for row in rows])
    nmi_mean, nmi_sd = mean_and_sample_sd([row["nmi"] for row in rows])
    rule = rows[0].get("selection_rule")
    selected = None
    if rule in {"min_inertia", "min_procrustes"}:
        usable = [row for row in rows if row.get("selection_value") is not None]
        if usable:
            selected = min(usable, key=lambda row: (float(row["selection_value"]), int(row["seed"])))
    return {
        "n_runs": len(rows),
        "per_run_acc_mean": acc_mean,
        "per_run_acc_sd": acc_sd,
        "per_run_nmi_mean": nmi_mean,
        "per_run_nmi_sd": nmi_sd,
        "selected_acc": None if selected is None else selected["acc"],
        "selected_nmi": None if selected is None else selected["nmi"],
        "selected_seed": None if selected is None else selected["seed"],
        "selected_value": None if selected is None else selected["selection_value"],
        "selection_rule": rule,
    }


def across_batches(batch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_acc = [row["selected_acc"] for row in batch_rows if row.get("selected_acc") is not None]
    selected_nmi = [row["selected_nmi"] for row in batch_rows if row.get("selected_nmi") is not None]
    acc_mean, acc_sd = mean_and_sample_sd(selected_acc)
    nmi_mean, nmi_sd = mean_and_sample_sd(selected_nmi)
    return {
        "n_batches": len(batch_rows),
        "selected_acc_mean": acc_mean,
        "selected_acc_sd": acc_sd,
        "selected_nmi_mean": nmi_mean,
        "selected_nmi_sd": nmi_sd,
    }


def oracle_and_closest(configs: list[dict[str, Any]], paper_acc: float | None, paper_nmi: float | None) -> dict[str, Any]:
    """Post-hoc views. They are not the locked result."""
    usable = [row for row in configs if row.get("per_run_acc_mean") is not None]
    if not usable:
        return {"ORACLE_BEST_TEST_ACC": None, "POSTHOC_CLOSEST_TO_PAPER": None}
    oracle = max(usable, key=lambda row: float(row["per_run_acc_mean"]))
    closest = None
    if paper_acc is not None and paper_nmi is not None:
        def distance(row: dict[str, Any]) -> float:
            acc = float(row["per_run_acc_mean"]) * 100.0
            nmi = float(row.get("per_run_nmi_mean") or 0.0) * 100.0
            return (acc - paper_acc) ** 2 + (nmi - paper_nmi) ** 2

        closest = min(usable, key=distance)
    return {
        "ORACLE_BEST_TEST_ACC": _public(oracle),
        "POSTHOC_CLOSEST_TO_PAPER": None if closest is None else _public(closest),
    }


def _public(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "config_name": row.get("config_name"),
        "variant": row.get("variant"),
        "prep": row.get("prep"),
        "dataset_id": row.get("dataset_id"),
        "per_run_acc_mean": row.get("per_run_acc_mean"),
        "per_run_nmi_mean": row.get("per_run_nmi_mean"),
        "initialization": row.get("initialization"),
    }


def signed_gap(measured: float | None, paper_percent: float | None) -> float | None:
    if measured is None or paper_percent is None:
        return None
    return float(measured) * 100.0 - float(paper_percent)
