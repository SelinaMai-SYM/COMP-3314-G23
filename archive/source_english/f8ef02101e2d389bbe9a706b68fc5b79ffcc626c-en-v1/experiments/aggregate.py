"""Read run directories into a table. No number is invented here."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_run(run_dir: Path) -> dict[str, Any] | None:
    status_path = run_dir / "status.json"
    if not status_path.is_file():
        return None
    status = json.loads(status_path.read_text(encoding="utf-8"))
    config: dict[str, Any] = {}
    if (run_dir / "config.yaml").is_file():
        config = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8")) or {}
    metrics: dict[str, Any] = {}
    if (run_dir / "metrics.json").is_file():
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    metadata: dict[str, Any] = {}
    if (run_dir / "metadata.json").is_file():
        metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    history = None
    hist_path = run_dir / "objective_history.csv"
    if hist_path.is_file():
        history = hist_path.read_text(encoding="utf-8")
    params = dict(config.get("params") or {})
    perturb = config.get("perturbation")
    return {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "status": status.get("status"),
        "track": config.get("track"),
        "method": config.get("method"),
        "dataset": config.get("dataset"),
        "n_trials_requested": config.get("n_trials"),
        "n_trials_completed": metrics.get("n_trials_completed", 0),
        "acc_mean": metrics.get("acc_mean"),
        "acc_std": metrics.get("acc_std"),
        "nmi_mean": metrics.get("nmi_mean"),
        "nmi_std": metrics.get("nmi_std"),
        "gamma": params.get("gamma"),
        "k": params.get("k"),
        "n_components": params.get("n_components"),
        "perturbation": perturb,
        "params": params,
        "metrics": metrics,
        "status_payload": status,
        "metadata": metadata,
        "has_objective_history": hist_path.is_file() and hist_path.stat().st_size > 10,
        "irls_seconds": (metrics.get("runtime_irls_seconds") if metrics else None),
        "irls_iterations": (metrics.get("n_irls_iterations") if metrics else None),
        "irls_converged": (metrics.get("irls_converged") if metrics else None),
        "objective_history_text": history,
    }


def load_all_runs(runs_root: Path) -> list[dict[str, Any]]:
    rows = []
    if not runs_root.is_dir():
        return rows
    for child in sorted(runs_root.iterdir()):
        if not child.is_dir():
            continue
        row = load_run(child)
        if row is not None:
            rows.append(row)
    return rows


def completed(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["status"] == "COMPLETED" and (row["n_trials_completed"] or 0) > 0]


def select_label_informed(rows: list[dict[str, Any]], method: str, dataset: str) -> dict[str, Any] | None:
    """Pick the completed setting with highest mean ACC. Disclose this as label-informed."""
    candidates = [
        row
        for row in completed(rows)
        if row["method"] == method and row["dataset"] == dataset
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda row: (row["acc_mean"] if row["acc_mean"] is not None else -1.0))


def pct(mean: float | None, std: float | None) -> str:
    if mean is None:
        return "N/A — not reproduced"
    if std is None:
        return f"{100.0 * mean:.1f}"
    return f"{100.0 * mean:.1f} ± {100.0 * std:.1f}"
