"""Check that the 72-cell delivery is internally consistent."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from experiments.v3_reproduction.protocol_registry import load_campaign

REQUIRED = (
    "coverage_72_cells.csv",
    "coverage_72_cells.md",
    "table1_acc.csv",
    "table1_acc.md",
    "table2_nmi.csv",
    "table2_nmi.md",
    "all_configurations.csv",
    "all_trials.csv",
    "selected_runs.csv",
    "sc_ssc_ablation.csv",
    "initialization_comparison.csv",
    "dimension_sensitivity.csv",
    "gamma_sensitivity.csv",
    "solver_audit.csv",
    "yaleb_diagnostics.csv",
    "posthoc_closest_to_paper.csv",
    "failures.csv",
    "validation.json",
)


def validate(config_path: str) -> dict:
    campaign = load_campaign(config_path)
    workspace = Path(campaign["workspace"])
    out = workspace / "results" / "v3_reproduction"
    errors: list[str] = []
    for name in REQUIRED:
        if not (out / name).is_file() and not (out / f"{name}.gz").is_file():
            errors.append(f"missing {name}")
    coverage_path = out / "coverage_72_cells.csv"
    n_cells = 0
    if coverage_path.is_file():
        with coverage_path.open() as handle:
            rows = list(csv.DictReader(handle))
        n_cells = len(rows)
        if n_cells != 72:
            errors.append(f"coverage has {n_cells} rows")
        ids = [row["cell_id"] for row in rows]
        if len(set(ids)) != len(ids):
            errors.append("duplicate historical cells")
        for row in rows:
            if row.get("locked_acc") in {"0", "0.0"} and row.get("execution_status") != "COMPLETED":
                errors.append(f"zero used for missing ACC in {row['cell_id']}")
    runs = workspace / "runs" / "v3_reproduction" / "jobs"
    completed = 0
    if runs.is_dir():
        for path in runs.glob("*/*.json"):
            meta = json.loads(path.read_text())
            if meta.get("status") == "COMPLETED":
                completed += 1
                if not meta.get("code_commit"):
                    errors.append(f"completed job without commit: {path.name}")
                if "requested_config" not in meta or "effective_config" not in meta:
                    errors.append(f"config audit missing: {path.name}")
    per = out / "per_benchmark"
    for name in ("AR", "JAFFE", "ORL", "UMIST", "BinAlpha", "MSRA50", "YaleB", "USPS"):
        if not (per / f"{name}.md").is_file():
            errors.append(f"missing per-benchmark note {name}")
    return {"ok": not errors, "errors": errors, "n_cells": n_cells, "completed_jobs": completed}
