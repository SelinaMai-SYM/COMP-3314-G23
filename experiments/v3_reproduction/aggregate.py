"""Build tables from raw v3 trial records. Do not invent missing scores."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from experiments.v3_reproduction.compare_paper import (
    across_batches,
    oracle_and_closest,
    signed_gap,
    summarize_batch,
)
from experiments.v3_reproduction.job_plan import historical_cells
from experiments.v3_reproduction.protocol_registry import HISTORICAL_METHODS, load_campaign
from experiments.v3_reproduction.provenance import json_ready

PAPER_METHOD = {
    "kmeans": "kmeans",
    "sc": "sc",
    "pca_kmeans": "pca_kmeans",
    "pca_sc": "pca_spectral",
    "lda_kmeans": "lda_kmeans",
    "lda_sc": "lda_spectral",
    "llc": "llc",
    "spls": "spls",
    "ssc": "ssc",
}


def _blank(value: Any) -> Any:
    return "" if value is None else value


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _blank(row.get(key)) for key in fieldnames})


def _maybe_gzip(path: Path, limit: int = 80_000_000) -> None:
    if path.stat().st_size <= limit:
        return
    gz_path = path.with_suffix(path.suffix + ".gz")
    digest = hashlib.sha256()
    with path.open("rb") as source, gzip.open(gz_path, "wb") as target:
        while True:
            chunk = source.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            target.write(chunk)
    pointer = path.with_suffix(path.suffix + ".POINTER.txt")
    pointer.write_text(
        f"uncompressed_bytes={path.stat().st_size}\n"
        f"gzip={gz_path.name}\n"
        f"sha256_uncompressed={digest.hexdigest()}\n"
        "The CSV is kept. The gzip is a size-capped twin, not a substitute that drops rows.\n"
    )


def _load_trials(runs_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    trials: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    if not runs_dir.is_dir():
        return trials, jobs
    for meta_path in sorted(runs_dir.glob("*/*.json")):
        if meta_path.name.endswith(".tmp"):
            continue
        meta = json.loads(meta_path.read_text())
        meta["path"] = str(meta_path)
        jobs.append(meta)
        trial_path = meta_path.with_suffix(".trials.jsonl")
        if not trial_path.is_file():
            continue
        with trial_path.open() as handle:
            for line in handle:
                if line.strip():
                    trials.append(json.loads(line))
    return trials, jobs


def _paper(reference: dict[str, Any], metric: str, method: str, benchmark: str) -> tuple[float | None, float | None]:
    block = reference.get(metric, {}).get(PAPER_METHOD[method], {}).get(benchmark)
    if not block:
        return None, None
    return float(block["mean"]), float(block["sd"])


def aggregate(config_path: str | Path) -> dict[str, Any]:
    campaign = load_campaign(config_path)
    workspace = Path(campaign["workspace"])
    runs_dir = workspace / "runs" / "v3_reproduction" / "jobs"
    out_dir = workspace / "results" / "v3_reproduction"
    out_dir.mkdir(parents=True, exist_ok=True)
    trials, jobs = _load_trials(runs_dir)
    if not trials or not jobs:
        raise ValueError("No raw jobs/trials: use rebuild-results for the committed release. Existing results preserved.")
    reference = campaign["_paper_reference"]
    probe_path = workspace / "docs" / "v3" / "resource_probe.json"
    probe = json.loads(probe_path.read_text()) if probe_path.is_file() else {"datasets": [], "cells": []}
    cells = probe.get("cells") or historical_cells(probe.get("datasets"))

    grouped: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for row in trials:
        key = (
            row.get("dataset_id"),
            row.get("method"),
            row.get("prep"),
            row.get("config_name"),
            row.get("variant"),
            row.get("initialization"),
            row.get("batch"),
            row.get("report_role"),
        )
        grouped[key].append(row)

    batch_summaries = []
    for key, rows in grouped.items():
        summary = summarize_batch(rows)
        dataset_id, method, prep, config_name, variant, initialization, batch, role = key
        summary.update(
            {
                "dataset_id": dataset_id,
                "historical_benchmark": rows[0].get("historical_benchmark"),
                "counts_as_historical": rows[0].get("counts_as_historical"),
                "method": method,
                "prep": prep,
                "config_name": config_name,
                "variant": variant,
                "initialization": initialization,
                "batch": batch,
                "report_role": role,
                "code_commit": rows[0].get("code_commit"),
            }
        )
        batch_summaries.append(summary)

    config_groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for row in batch_summaries:
        config_groups[
            (
                row["dataset_id"],
                row["method"],
                row["prep"],
                row["config_name"],
                row["variant"],
                row["initialization"],
                row["report_role"],
            )
        ].append(row)

    config_rows = []
    for key, rows in config_groups.items():
        rows = sorted(rows, key=lambda item: int(item["batch"]))
        first = rows[0]
        cross = across_batches(rows)
        config_rows.append(
            {
                **{k: first[k] for k in (
                    "dataset_id",
                    "historical_benchmark",
                    "counts_as_historical",
                    "method",
                    "prep",
                    "config_name",
                    "variant",
                    "initialization",
                    "report_role",
                    "code_commit",
                    "selection_rule",
                    "per_run_acc_mean",
                    "per_run_acc_sd",
                    "per_run_nmi_mean",
                    "per_run_nmi_sd",
                    "selected_acc",
                    "selected_nmi",
                    "selected_seed",
                    "selected_value",
                )},
                "batch0_selected_acc": first["selected_acc"],
                "batch0_selected_nmi": first["selected_nmi"],
                "across_selected_acc_mean": cross["selected_acc_mean"],
                "across_selected_acc_sd": cross["selected_acc_sd"],
                "across_selected_nmi_mean": cross["selected_nmi_mean"],
                "across_selected_nmi_sd": cross["selected_nmi_sd"],
                "n_batches": cross["n_batches"],
            }
        )

    _write_main_tables(out_dir, cells, config_rows, jobs, reference, trials)
    _write_long_tables(out_dir, config_rows, trials, jobs, reference)
    _figures(out_dir, jobs, config_rows)
    _per_benchmark(out_dir, cells, config_rows, jobs)
    validation = {
        "n_trials": len(trials),
        "n_jobs": len(jobs),
        "n_cells": len(cells),
        "completed_jobs": sum(1 for job in jobs if job.get("status") == "COMPLETED"),
        "failed_jobs": sum(1 for job in jobs if job.get("status") == "FAILED"),
        "infeasible_jobs": sum(1 for job in jobs if job.get("status") == "INFEASIBLE"),
    }
    (out_dir / "validation.json").write_text(json.dumps(validation, indent=2))
    return validation


def _reference_rows(config_rows: list[dict[str, Any]], method: str, benchmark: str) -> list[dict[str, Any]]:
    rows = [
        row for row in config_rows
        if row["method"] == method
        and row["historical_benchmark"] == benchmark
        and row.get("counts_as_historical")
        and row["prep"] == "Y0"
        and row["report_role"] == "reference"
    ]
    if method in {"kmeans", "sc", "ssc"}:
        rows = [row for row in rows if row["initialization"] == "RANDOM"]
    return rows


def _write_main_tables(out_dir, cells, config_rows, jobs, reference, trials) -> None:
    coverage = []
    acc_rows = []
    nmi_rows = []
    for cell in cells:
        method = cell["method"]
        benchmark = cell["benchmark"]
        refs = _reference_rows(config_rows, method, benchmark)
        paper_acc, paper_acc_sd = _paper(reference, "acc", method, benchmark)
        paper_nmi, paper_nmi_sd = _paper(reference, "nmi", method, benchmark)
        if method == "ssc":
            display = _variant_text(refs)
        elif len(refs) == 1:
            display = _fmt_mean(refs[0].get("per_run_acc_mean"), refs[0].get("per_run_acc_sd"))
        elif refs:
            display = " ; ".join(
                f"{row['dataset_id']}:{_fmt_mean(row.get('per_run_acc_mean'), row.get('per_run_acc_sd'))}"
                for row in refs
            )
        else:
            display = None
        nmi_display = None
        if method == "ssc":
            nmi_display = _variant_text(refs, metric="nmi")
        elif len(refs) == 1:
            nmi_display = _fmt_mean(refs[0].get("per_run_nmi_mean"), refs[0].get("per_run_nmi_sd"))
        elif refs:
            nmi_display = " ; ".join(
                f"{row['dataset_id']}:{_fmt_mean(row.get('per_run_nmi_mean'), row.get('per_run_nmi_sd'))}"
                for row in refs
            )
        executed = bool(refs) or any(
            job.get("method") == method and job.get("historical_benchmark") == benchmark and job.get("status") == "COMPLETED"
            for job in jobs
        )
        status = cell.get("execution_status")
        if cell.get("executable") and executed:
            status = "COMPLETED"
        elif cell.get("executable") and not executed:
            status = "PENDING"
        elif not cell.get("executable"):
            status = cell.get("blocker")
        coverage.append(
            {
                "cell_id": cell["cell_id"],
                "benchmark": benchmark,
                "method": method,
                "resource_status": cell.get("resource_status"),
                "algorithm_fidelity": cell.get("algorithm_fidelity"),
                "execution_status": status,
                "blocker": cell.get("blocker"),
                "reason": cell.get("reason"),
                "dataset_ids": "|".join(cell.get("dataset_ids") or []),
                "supplemental_dataset_ids": "|".join(cell.get("supplemental_dataset_ids") or []),
                "locked_acc": display,
                "locked_nmi": nmi_display,
            }
        )
        primary = refs[0] if len(refs) == 1 else None
        acc_rows.append(
            {
                "benchmark": benchmark,
                "method": method,
                "paper_acc_mean": paper_acc,
                "paper_acc_sd": paper_acc_sd,
                "v3_per_run_acc_mean_percent": None if primary is None else _percent(primary.get("per_run_acc_mean")),
                "v3_per_run_acc_sd_percent": None if primary is None else _percent(primary.get("per_run_acc_sd")),
                "v3_batch0_selected_acc_percent": None if primary is None else _percent(primary.get("batch0_selected_acc")),
                "v3_across_selected_acc_mean_percent": None if primary is None else _percent(primary.get("across_selected_acc_mean")),
                "v3_across_selected_acc_sd_percent": None if primary is None else _percent(primary.get("across_selected_acc_sd")),
                "acc_gap_per_run_minus_paper": None
                if primary is None
                else signed_gap(primary.get("per_run_acc_mean"), paper_acc),
                "locked_display": display,
                "execution_status": status,
                "view": "LOCKED_RECONSTRUCTION",
            }
        )
        nmi_rows.append(
            {
                "benchmark": benchmark,
                "method": method,
                "paper_nmi_mean": paper_nmi,
                "paper_nmi_sd": paper_nmi_sd,
                "v3_per_run_nmi_mean_percent": None if primary is None else _percent(primary.get("per_run_nmi_mean")),
                "v3_per_run_nmi_sd_percent": None if primary is None else _percent(primary.get("per_run_nmi_sd")),
                "v3_batch0_selected_nmi_percent": None if primary is None else _percent(primary.get("batch0_selected_nmi")),
                "nmi_gap_per_run_minus_paper": None
                if primary is None
                else signed_gap(primary.get("per_run_nmi_mean"), paper_nmi),
                "locked_display": nmi_display,
                "execution_status": status,
                "view": "LOCKED_RECONSTRUCTION",
            }
        )
    fields_c = list(coverage[0].keys()) if coverage else ["cell_id"]
    _write_csv(out_dir / "coverage_72_cells.csv", coverage, fields_c)
    _write_csv(out_dir / "table1_acc.csv", acc_rows, list(acc_rows[0].keys()))
    _write_csv(out_dir / "table2_nmi.csv", nmi_rows, list(nmi_rows[0].keys()))
    (out_dir / "coverage_72_cells.md").write_text(_markdown_table(
        "72 historical cells",
        coverage,
        ["benchmark", "method", "execution_status", "blocker", "locked_acc", "locked_nmi"],
    ))
    (out_dir / "table1_acc.md").write_text(_markdown_table(
        "Table 1 style ACC. Blank is missing, not zero. SSC shows both variants in locked_display.",
        acc_rows,
        ["benchmark", "method", "paper_acc_mean", "paper_acc_sd", "locked_display", "v3_per_run_acc_mean_percent", "acc_gap_per_run_minus_paper", "execution_status"],
    ))
    (out_dir / "table2_nmi.md").write_text(_markdown_table(
        "Table 2 style NMI. Blank is missing, not zero.",
        nmi_rows,
        ["benchmark", "method", "paper_nmi_mean", "paper_nmi_sd", "locked_display", "v3_per_run_nmi_mean_percent", "nmi_gap_per_run_minus_paper", "execution_status"],
    ))
    if len(coverage) != 72:
        raise RuntimeError(f"coverage has {len(coverage)} rows")


def _percent(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value) * 100.0


def _fmt_mean(mean: float | None, sd: float | None) -> str | None:
    if mean is None:
        return None
    if sd is None:
        return f"{mean * 100.0:.2f}"
    return f"{mean * 100.0:.2f} ± {sd * 100.0:.2f}"


def _variant_text(rows: list[dict[str, Any]], metric: str = "acc") -> str | None:
    if not rows:
        return None
    parts = []
    for row in sorted(rows, key=lambda item: str(item.get("variant"))):
        mean = row.get(f"per_run_{metric}_mean")
        sd = row.get(f"per_run_{metric}_sd")
        parts.append(f"{row.get('variant')}:{_fmt_mean(mean, sd)}")
    return " ; ".join(parts)


def _write_long_tables(out_dir, config_rows, trials, jobs, reference) -> None:
    _write_csv(out_dir / "all_configurations.csv", config_rows, list(config_rows[0].keys()) if config_rows else ["dataset_id"])
    if config_rows:
        _maybe_gzip(out_dir / "all_configurations.csv")
    trial_fields = [
        "dataset_id", "historical_benchmark", "counts_as_historical", "method", "prep",
        "config_name", "variant", "report_role", "initialization", "batch", "seed",
        "inertia", "selection_value", "selection_rule", "acc", "nmi", "ssc_gamma",
        "code_commit", "labels_sha256",
    ]
    _write_csv(out_dir / "all_trials.csv", trials, trial_fields)
    if (out_dir / "all_trials.csv").is_file():
        _maybe_gzip(out_dir / "all_trials.csv")
    selected = [row for row in config_rows if row.get("batch0_selected_acc") is not None or row["method"] == "lda_kmeans"]
    _write_csv(out_dir / "selected_runs.csv", selected, list(selected[0].keys()) if selected else ["dataset_id"])
    ablation = _ablation(config_rows)
    _write_csv(out_dir / "sc_ssc_ablation.csv", ablation, list(ablation[0].keys()) if ablation else ["dataset_id"])
    init_rows = [row for row in config_rows if row["method"] in {"kmeans", "sc", "ssc", "pca_kmeans", "pca_sc", "spls"}]
    _write_csv(out_dir / "initialization_comparison.csv", init_rows, list(init_rows[0].keys()) if init_rows else ["dataset_id"])
    dims = [row for row in config_rows if row["method"] in {"pca_kmeans", "pca_sc", "spls"}]
    _write_csv(out_dir / "dimension_sensitivity.csv", dims, list(dims[0].keys()) if dims else ["dataset_id"])
    gammas = [row for row in config_rows if row["method"] == "ssc"]
    _write_csv(out_dir / "gamma_sensitivity.csv", gammas, list(gammas[0].keys()) if gammas else ["dataset_id"])
    solver_rows = []
    for job in jobs:
        if job.get("method") == "ssc":
            solver_rows.append(
                {
                    "dataset_id": job.get("dataset_id"),
                    "prep": job.get("prep"),
                    "variant": job.get("variant"),
                    "solver_status": job.get("solver_status"),
                    "equation8_objective": job.get("equation8_objective"),
                    "continued_after_checkpoint": job.get("continued_after_checkpoint"),
                    "checkpoint_iterations": (job.get("checkpoint_300") or {}).get("n_iterations"),
                    "checkpoint_objective": (job.get("checkpoint_300") or {}).get("equation8_objective"),
                    "admm_status": (job.get("admm") or {}).get("status") if isinstance(job.get("admm"), dict) else None,
                    "admm_objective": (job.get("admm") or {}).get("objective") if isinstance(job.get("admm"), dict) else None,
                    "admm_gap": (job.get("admm") or {}).get("relative_objective_gap_vs_irls") if isinstance(job.get("admm"), dict) else None,
                    "code_commit": job.get("code_commit"),
                    "config": (job.get("effective_config") or {}).get("ssc_gamma"),
                }
            )
    _write_csv(out_dir / "solver_audit.csv", solver_rows, list(solver_rows[0].keys()) if solver_rows else ["dataset_id"])
    yale = [row for row in config_rows if str(row.get("dataset_id", "")).startswith("YaleB")]
    _write_csv(out_dir / "yaleb_diagnostics.csv", yale, list(yale[0].keys()) if yale else ["dataset_id"])
    posthoc_rows = []
    for benchmark in {row["historical_benchmark"] for row in config_rows}:
        for method in HISTORICAL_METHODS:
            paper_acc, _sd = _paper(reference, "acc", method, benchmark)
            paper_nmi, _nsd = _paper(reference, "nmi", method, benchmark)
            pool = [
                row for row in config_rows
                if row["historical_benchmark"] == benchmark
                and row["method"] == method
                and row["initialization"] in {"RANDOM", "YU_SHI", "FULL_REFIT"}
                and row["prep"] == "Y0"
            ]
            view = oracle_and_closest(pool, paper_acc, paper_nmi)
            for name, item in view.items():
                posthoc_rows.append(
                    {
                        "benchmark": benchmark,
                        "method": method,
                        "view": name,
                        "paper_acc": paper_acc,
                        "paper_nmi": paper_nmi,
                        **(item or {}),
                    }
                )
    _write_csv(
        out_dir / "posthoc_closest_to_paper.csv",
        posthoc_rows,
        ["benchmark", "method", "view", "paper_acc", "paper_nmi", "dataset_id", "config_name", "variant", "prep", "per_run_acc_mean", "per_run_nmi_mean", "initialization"],
    )
    failures = [
        {
            "dataset_id": job.get("dataset_id"),
            "job_id": job.get("job_id"),
            "method": job.get("method"),
            "status": job.get("status"),
            "error": job.get("error"),
            "solver_status": job.get("solver_status"),
        }
        for job in jobs
        if job.get("status") in {"FAILED", "TIMEOUT", "INFEASIBLE"} or job.get("solver_status") in {
            "MAX_ITER_REACHED", "NUMERICALLY_UNCERTIFIED", "FAILED", "TIMEOUT"
        }
    ]
    _write_csv(out_dir / "failures.csv", failures, ["dataset_id", "job_id", "method", "status", "solver_status", "error"])


def _ablation(config_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {
        (row["dataset_id"], row["prep"], row["config_name"], row["initialization"], row["method"]): row
        for row in config_rows
    }
    rows = []
    for row in config_rows:
        if row["method"] != "ssc" or row["initialization"] != "RANDOM":
            continue
        matched_name = f"{row['config_name']}|matched_F"
        # matched rows use config_name with |matched_F and method sc_matched_to_ssc
        partner = None
        for candidate in config_rows:
            if (
                candidate["method"] == "sc_matched_to_ssc"
                and candidate["dataset_id"] == row["dataset_id"]
                and candidate["prep"] == row["prep"]
                and candidate["initialization"] == "RANDOM"
                and str(candidate["config_name"]).startswith(str(row["config_name"]))
            ):
                partner = candidate
                break
        if partner is None:
            continue
        acc_delta = None
        nmi_delta = None
        if row.get("batch0_selected_acc") is not None and partner.get("batch0_selected_acc") is not None:
            acc_delta = row["batch0_selected_acc"] - partner["batch0_selected_acc"]
            nmi_delta = row["batch0_selected_nmi"] - partner["batch0_selected_nmi"]
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "prep": row["prep"],
                "variant": row["variant"],
                "config_name": row["config_name"],
                "ssc_selected_acc": row.get("batch0_selected_acc"),
                "sc_selected_acc": partner.get("batch0_selected_acc"),
                "acc_delta_ssc_minus_sc": acc_delta,
                "ssc_selected_nmi": row.get("batch0_selected_nmi"),
                "sc_selected_nmi": partner.get("batch0_selected_nmi"),
                "nmi_delta_ssc_minus_sc": nmi_delta,
                "note": "Inertia was minimized separately on F and on G. The inertias were not compared.",
            }
        )
    del index
    return rows


def _markdown_table(title: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = [f"# {title}", "", "| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        cells = [str(_blank(row.get(column))).replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def _per_benchmark(out_dir: Path, cells, config_rows, jobs) -> None:
    folder = out_dir / "per_benchmark"
    folder.mkdir(parents=True, exist_ok=True)
    by_bench = defaultdict(list)
    for cell in cells:
        by_bench[cell["benchmark"]].append(cell)
    for benchmark, bench_cells in by_bench.items():
        lines = [f"# {benchmark}", "", "Historical v1/v2 scores are not copied into this file.", ""]
        lines.append(_markdown_table(
            "Nine methods",
            bench_cells,
            ["method", "execution_status", "blocker", "locked_acc", "locked_nmi", "reason"],
        ))
        extra = [row for row in config_rows if row.get("historical_benchmark") == benchmark and row.get("prep") == "Y0" and row.get("initialization") in {"RANDOM", "SKLEARN_GREEDY_KMEANSPP", "YU_SHI", "FULL_REFIT"}]
        if extra:
            lines.append(_markdown_table(
                "Y0 configuration summaries",
                extra[:80],
                ["method", "dataset_id", "config_name", "variant", "initialization", "report_role", "per_run_acc_mean", "per_run_acc_sd", "batch0_selected_acc"],
            ))
        (folder / f"{benchmark}.md").write_text("\n".join(lines))


def _figures(out_dir: Path, jobs: list[dict[str, Any]], config_rows: list[dict[str, Any]]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folder = out_dir / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for job in jobs:
        if job.get("method") == "ssc" and job.get("prep") == "Y0" and job.get("history"):
            by_dataset[str(job.get("dataset_id"))].append(job)
    for dataset_id, items in by_dataset.items():
        figure, axis = plt.subplots(figsize=(7, 4))
        for job in items:
            if job.get("variant") not in {"E8", "E13"}:
                continue
            if not np.isclose(float((job.get("effective_config") or {}).get("ssc_gamma", -1)), 1.0):
                continue
            history = job["history"]
            axis.plot(
                [row["iteration"] for row in history],
                [row["equation8_objective"] for row in history],
                label=f"{job.get('variant')} gamma=1",
            )
        axis.set_xlabel("IRLS iteration")
        axis.set_ylabel("Equation (8) objective")
        axis.set_title(dataset_id)
        axis.legend(fontsize=8)
        figure.tight_layout()
        figure.savefig(folder / f"convergence_{dataset_id}.png", dpi=120)
        plt.close(figure)
    gamma_rows = [
        row for row in config_rows
        if row["method"] == "ssc" and row["prep"] == "Y0" and row["initialization"] == "RANDOM" and row["report_role"] in {"reference", "grid"}
    ]
    by_ds = defaultdict(list)
    for row in gamma_rows:
        by_ds[row["dataset_id"]].append(row)
    for dataset_id, rows in by_ds.items():
        figure, axis = plt.subplots(figsize=(7, 4))
        for variant in ("E8", "E13"):
            chosen = [row for row in rows if row.get("variant") == variant]
            chosen = sorted(chosen, key=lambda item: float((item.get("config_name") or "0").split("gamma=")[-1].replace("|matched_F", "") or "nan") if False else 0)
            # config_name is like E8|gamma=1e+00
            def gamma_of(item: dict[str, Any]) -> float:
                text = str(item.get("config_name"))
                if "gamma=" not in text:
                    return np.nan
                return float(text.split("gamma=")[-1])
            chosen = sorted(chosen, key=gamma_of)
            axis.plot(
                [gamma_of(item) for item in chosen],
                [None if item.get("per_run_acc_mean") is None else item["per_run_acc_mean"] * 100.0 for item in chosen],
                marker="o",
                label=variant,
            )
        axis.set_xscale("log")
        axis.set_xlabel("ssc_gamma")
        axis.set_ylabel("ACC percent, per-run mean")
        axis.set_title(dataset_id)
        axis.legend()
        figure.tight_layout()
        figure.savefig(folder / f"gamma_{dataset_id}.png", dpi=120)
        plt.close(figure)
