"""Build the v2 tables from saved trial rows.

Summary accuracies are percent. The trial CSV stays in fraction units.
A missing measurement is an empty cell or ``NOT_COMPARABLE``. It is never 0.
"""

from __future__ import annotations

import csv
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from experiments.v2_kmeans_protocol.dataset_registry import (
    REPO_ROOT,
    DatasetEntry,
    load_registry,
    probe_entry,
)
from experiments.v2_kmeans_protocol.gamma_runner import ORACLE_LABEL
from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY, RANDOM, VANILLA
from experiments.v2_kmeans_protocol.metrics import mean_and_sample_sd
from experiments.v2_kmeans_protocol.paper_comparison import as_fraction, numeric_gap, paper_stat
from experiments.v2_kmeans_protocol.protocol_runner import (
    ARRAYS_ROOT,
    FAILURES_ROOT,
    TRIAL_FIELDS,
    read_trials,
    trials_path,
)
from experiments.v2_kmeans_protocol.representation_cache import GAMMA_GRID, MANIFEST_ROOT, gamma_token
from experiments.v2_kmeans_protocol.select_best_inertia import acc_rank_of_selected, select_min_inertia

RESULTS = REPO_ROOT / "results" / "v2_kmeans_protocol"
PER_BENCHMARK = RESULTS / "per_benchmark"
SELECTED = RESULTS / "selected_labels"
SELECTED_CENTERS = RESULTS / "selected_centers"

CORE_PROTOCOLS = (
    ("P1", "RANDOM_MEAN50", RANDOM, "MEAN_OF_TRIALS"),
    ("P2", "RANDOM_BEST_INERTIA50", RANDOM, "MIN_INERTIA"),
    ("P3", "KMEANSPP_MEAN50", GREEDY, "MEAN_OF_TRIALS"),
    ("P4", "KMEANSPP_BEST_INERTIA50", GREEDY, "MIN_INERTIA"),
)
VANILLA_PROTOCOLS = (
    ("V1", "VANILLA_MEAN50", VANILLA, "MEAN_OF_TRIALS"),
    ("V2", "VANILLA_BEST_INERTIA50", VANILLA, "MIN_INERTIA"),
)


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _num(value: str | float | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _percent(fraction: float | None) -> float | None:
    if fraction is None:
        return None
    return 100.0 * float(fraction)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".10g")
    return str(value)


def load_completed_trials(entries: Iterable[DatasetEntry] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple] = set()
    source = list(entries) if entries is not None else load_registry()
    for entry in source:
        for row in read_trials(trials_path(entry)):
            key = (
                row["benchmark"],
                row["dataset_version"],
                row["representation"],
                row["initialization_label"],
                row["gamma"],
                row["batch_id"],
                row["seed"],
            )
            if key in seen:
                raise RuntimeError(f"duplicate trial record {key}")
            seen.add(key)
            rows.append(row)
    return rows


def _failure_status(entry: DatasetEntry) -> str:
    statuses = []
    for path in sorted(FAILURES_ROOT.glob(f"{entry.key}__*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        statuses.append(str(payload.get("experiment_status", "FAILED")))
    if "TIMEOUT" in statuses:
        return "TIMEOUT"
    if statuses:
        return statuses[-1]
    return ""


def _group(rows: list[dict[str, str]], entry: DatasetEntry, **filters: str) -> list[dict[str, str]]:
    chosen = []
    for row in rows:
        if row["benchmark"] != entry.benchmark or row["dataset_version"] != entry.version:
            continue
        if row.get("experiment_status") != "COMPLETED":
            continue
        if all(row.get(key) == value for key, value in filters.items()):
            chosen.append(row)
    return chosen


def _summarize(trials: list[dict[str, str]], selection: str) -> dict[str, Any]:
    parsed = []
    for row in trials:
        parsed.append(
            {
                "inertia": float(row["inertia"]),
                "seed": int(row["seed"]),
                "acc": float(row["acc"]),
                "nmi": float(row["nmi"]),
                "wall_seconds": float(row["wall_seconds"]),
                "trial_id": row["trial_id"],
                "ssc_optimizer_status": row["ssc_optimizer_status"],
            }
        )
    if selection == "MEAN_OF_TRIALS":
        acc_mean, acc_sd = mean_and_sample_sd([item["acc"] for item in parsed])
        nmi_mean, nmi_sd = mean_and_sample_sd([item["nmi"] for item in parsed])
        inertia_mean, inertia_sd = mean_and_sample_sd([item["inertia"] for item in parsed])
        return {
            "acc_percent": _percent(acc_mean),
            "acc_sd_percent": _percent(acc_sd),
            "nmi_percent": _percent(nmi_mean),
            "nmi_sd_percent": _percent(nmi_sd),
            "inertia": inertia_mean,
            "inertia_sd": inertia_sd,
            "selected_seed": "",
            "acc_rank": "",
            "trial_id": "",
            "fit_time_seconds": float(sum(item["wall_seconds"] for item in parsed)),
            "ssc_optimizer_status": parsed[0]["ssc_optimizer_status"],
        }
    selected = select_min_inertia(parsed)
    return {
        "acc_percent": _percent(float(selected["acc"])),
        "acc_sd_percent": None,
        "nmi_percent": _percent(float(selected["nmi"])),
        "nmi_sd_percent": None,
        "inertia": float(selected["inertia"]),
        "inertia_sd": None,
        "selected_seed": int(selected["seed"]),
        "acc_rank": acc_rank_of_selected(parsed, selected),
        "trial_id": selected["trial_id"],
        "fit_time_seconds": float(selected["wall_seconds"]),
        "ssc_optimizer_status": selected["ssc_optimizer_status"],
    }


def _protocol_row(
    entry: DatasetEntry,
    trials: list[dict[str, str]],
    *,
    representation: str,
    protocol_id: str,
    protocol: str,
    family: str,
    selection: str,
    gamma_label: str,
    expected_n: int = 50,
) -> dict[str, Any]:
    method = "SC" if representation == "F" else "SSC"
    batch = _group(
        trials,
        entry,
        representation=representation,
        initialization_label=family,
        gamma=gamma_label,
        batch_id="0",
    )
    status = "COMPLETED" if len(batch) == expected_n else (_failure_status(entry) or "INCOMPLETE")
    if len(batch) == 0 and not entry.run_protocols:
        status = entry.exact_dataset_status
    row: dict[str, Any] = {
        "benchmark": entry.benchmark,
        "dataset_version": entry.version,
        "benchmark_group": entry.benchmark_group,
        "method": method,
        "representation": representation,
        "protocol_id": protocol_id,
        "protocol": protocol,
        "initialization_label": family,
        "selection_rule": selection,
        "gamma": gamma_label,
        "n_trials": len(batch) if entry.run_protocols or batch else "",
        "selected_seed": "",
        "acc_rank": "",
        "acc_percent": "",
        "acc_sd_percent": "",
        "nmi_percent": "",
        "nmi_sd_percent": "",
        "inertia": "",
        "inertia_sd": "",
        "fit_time_seconds": "",
        "ssc_optimizer_status": "",
        "exact_dataset_status": entry.exact_dataset_status,
        "comparison_class": entry.comparison_class,
        "experiment_status": status,
        "run_id": f"{entry.key}__{representation}__{protocol}__g{gamma_label}",
        "acc_unit": "percent",
        "result_label": "MEASUREMENT",
        "selected_trial_id": "",
    }
    if len(batch) != expected_n:
        return row
    summary = _summarize(batch, selection)
    row.update(
        {
            "n_trials": expected_n,
            "selected_seed": _text(summary["selected_seed"]),
            "acc_rank": _text(summary["acc_rank"]),
            "acc_percent": _text(summary["acc_percent"]),
            "acc_sd_percent": _text(summary["acc_sd_percent"]),
            "nmi_percent": _text(summary["nmi_percent"]),
            "nmi_sd_percent": _text(summary["nmi_sd_percent"]),
            "inertia": _text(summary["inertia"]),
            "inertia_sd": _text(summary["inertia_sd"]),
            "fit_time_seconds": _text(summary["fit_time_seconds"]),
            "ssc_optimizer_status": summary["ssc_optimizer_status"],
            "experiment_status": "COMPLETED",
            "selected_trial_id": summary["trial_id"],
        }
    )
    return row


def _copy_selected(trial_id: str) -> None:
    if not trial_id:
        return
    for suffix, destination in ((".npy", SELECTED), ("__centers.npy", SELECTED_CENTERS)):
        source = ARRAYS_ROOT / f"{trial_id}{suffix}" if suffix != ".npy" else ARRAYS_ROOT / f"{trial_id}.npy"
        if not source.is_file():
            continue
        destination.mkdir(parents=True, exist_ok=True)
        target_name = f"{trial_id}.npy" if suffix == ".npy" else f"{trial_id}__centers.npy"
        shutil.copyfile(source, destination / target_name)


def build_protocol_table(
    entries: list[DatasetEntry],
    trials: list[dict[str, str]],
    protocols: tuple,
    gamma_label_for_g: str,
) -> list[dict[str, Any]]:
    rows = []
    for entry in entries:
        for representation, gamma_label in (("F", "NA"), ("G", gamma_label_for_g)):
            for protocol_id, protocol, family, selection in protocols:
                row = _protocol_row(
                    entry,
                    trials,
                    representation=representation,
                    protocol_id=protocol_id,
                    protocol=protocol,
                    family=family,
                    selection=selection,
                    gamma_label=gamma_label,
                )
                rows.append(row)
                if selection == "MIN_INERTIA":
                    _copy_selected(str(row.get("selected_trial_id", "")))
    return rows


def _lookup(rows: list[dict[str, Any]], entry: DatasetEntry, protocol: str, representation: str) -> dict[str, Any]:
    for row in rows:
        if (
            row["benchmark"] == entry.benchmark
            and row["dataset_version"] == entry.version
            and row["protocol"] == protocol
            and row["representation"] == representation
        ):
            return row
    raise KeyError((entry.key, protocol, representation))


def _gap_text(our_percent: str, paper_percent: float, comparison_class: str) -> str:
    our = _num(our_percent)
    if our is None:
        return "NOT_COMPARABLE"
    gap = numeric_gap(our / 100.0, paper_percent, comparison_class)
    if isinstance(gap, str):
        return gap
    return _text(100.0 * gap)


def build_ablation(entries: list[DatasetEntry], primary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ablation = []
    for entry in entries:
        paper_sc, _sc_sd = paper_stat("acc", "sc", entry.paper_benchmark)
        paper_ssc, _ssc_sd = paper_stat("acc", "ssc", entry.paper_benchmark)
        paper_sc_nmi, _ = paper_stat("nmi", "sc", entry.paper_benchmark)
        paper_ssc_nmi, _ = paper_stat("nmi", "ssc", entry.paper_benchmark)
        for _protocol_id, protocol, _family, _selection in CORE_PROTOCOLS:
            sc = _lookup(primary_rows, entry, protocol, "F")
            ssc = _lookup(primary_rows, entry, protocol, "G")
            our_sc = _num(sc["acc_percent"])
            our_ssc = _num(ssc["acc_percent"])
            our_sc_nmi = _num(sc["nmi_percent"])
            our_ssc_nmi = _num(ssc["nmi_percent"])
            both = our_sc is not None and our_ssc is not None
            ablation.append(
                {
                    "benchmark": entry.benchmark,
                    "dataset_version": entry.version,
                    "benchmark_group": entry.benchmark_group,
                    "protocol": protocol,
                    "paper_sc_acc_percent": paper_sc,
                    "paper_ssc_acc_percent": paper_ssc,
                    "our_sc_acc_percent": _text(our_sc),
                    "our_ssc_acc_percent": _text(our_ssc),
                    "our_ssc_minus_sc_pp": _text(our_ssc - our_sc) if both else "",
                    "paper_ssc_minus_sc_pp": paper_ssc - paper_sc,
                    "gap_to_paper_ssc_pp": _gap_text(ssc["acc_percent"], paper_ssc, entry.comparison_class),
                    "gap_to_paper_sc_pp": _gap_text(sc["acc_percent"], paper_sc, entry.comparison_class),
                    "our_sc_nmi_percent": _text(our_sc_nmi),
                    "our_ssc_nmi_percent": _text(our_ssc_nmi),
                    "our_nmi_ssc_minus_sc_pp": _text(our_ssc_nmi - our_sc_nmi)
                    if our_sc_nmi is not None and our_ssc_nmi is not None
                    else "",
                    "paper_nmi_ssc_minus_sc_pp": paper_ssc_nmi - paper_sc_nmi,
                    "exact_dataset_status": entry.exact_dataset_status,
                    "comparison_class": entry.comparison_class,
                    "experiment_status": "COMPLETED"
                    if sc["experiment_status"] == "COMPLETED" and ssc["experiment_status"] == "COMPLETED"
                    else "INCOMPLETE",
                    "note": "Inertia is not compared across F and G. P2/P4 seeds are chosen separately.",
                }
            )
    return ablation


def build_gamma(entries: list[DatasetEntry], trials: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        for gamma in GAMMA_GRID:
            token = gamma_token(gamma)
            for representation, gamma_label in (("F", "NA"), ("G", token)):
                if representation == "F" and token != gamma_token(1.0):
                    continue
                for protocol_id, protocol, family, selection in CORE_PROTOCOLS:
                    row = _protocol_row(
                        entry,
                        trials,
                        representation=representation,
                        protocol_id=protocol_id,
                        protocol=protocol,
                        family=family,
                        selection=selection,
                        gamma_label=gamma_label,
                    )
                    row["result_label"] = "PREDECLARED_GRID"
                    row["fair_unsupervised"] = "true"
                    row["sc_reused"] = "true" if representation == "F" else "false"
                    rows.append(row)
        for _protocol_id, protocol, _family, _selection in CORE_PROTOCOLS:
            candidates = [
                row
                for row in rows
                if row["benchmark"] == entry.benchmark
                and row["dataset_version"] == entry.version
                and row["representation"] == "G"
                and row["protocol"] == protocol
                and row["experiment_status"] == "COMPLETED"
                and row["result_label"] == "PREDECLARED_GRID"
            ]
            if not candidates:
                continue
            order = {gamma_token(value): index for index, value in enumerate(GAMMA_GRID)}
            best = max(
                candidates,
                key=lambda row: (float(row["acc_percent"]), -order[str(row["gamma"])]),
            )
            oracle = dict(best)
            oracle["result_label"] = ORACLE_LABEL
            oracle["fair_unsupervised"] = "false"
            oracle["run_id"] = f"{entry.key}__G__{protocol}__{ORACLE_LABEL}"
            oracle["note"] = (
                "Maximum labeled ACC on the predetermined gamma grid. "
                "Not a fair unsupervised model selection."
            )
            rows.append(oracle)
    return rows


def build_repeatability(entries: list[DatasetEntry], trials: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    batch_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for entry in entries:
        for representation in ("F", "G"):
            gamma_label = "NA" if representation == "F" else "1"
            for protocol_id, protocol, family, selection in (
                ("P2", "RANDOM_BEST_INERTIA50", RANDOM, "MIN_INERTIA"),
                ("P4", "KMEANSPP_BEST_INERTIA50", GREEDY, "MIN_INERTIA"),
            ):
                batch_ids = sorted(
                    {
                        int(row["batch_id"])
                        for row in trials
                        if row["benchmark"] == entry.benchmark
                        and row["dataset_version"] == entry.version
                        and row["representation"] == representation
                        and row["initialization_label"] == family
                        and row["gamma"] == gamma_label
                        and row["experiment_status"] == "COMPLETED"
                    }
                )
                selected_acc = []
                selected_nmi = []
                complete = 0
                for batch_id in batch_ids:
                    group = [
                        row
                        for row in trials
                        if row["benchmark"] == entry.benchmark
                        and row["dataset_version"] == entry.version
                        and row["representation"] == representation
                        and row["initialization_label"] == family
                        and row["gamma"] == gamma_label
                        and int(row["batch_id"]) == batch_id
                        and row["experiment_status"] == "COMPLETED"
                    ]
                    status = "COMPLETED" if len(group) == 50 else "INCOMPLETE"
                    record: dict[str, Any] = {
                        "benchmark": entry.benchmark,
                        "dataset_version": entry.version,
                        "method": "SC" if representation == "F" else "SSC",
                        "representation": representation,
                        "protocol": protocol,
                        "batch_id": batch_id,
                        "n_trials": len(group),
                        "experiment_status": status,
                        "selected_seed": "",
                        "selected_acc_percent": "",
                        "selected_nmi_percent": "",
                        "selected_inertia": "",
                        "acc_rank": "",
                    }
                    if len(group) == 50:
                        summary = _summarize(group, selection)
                        record.update(
                            {
                                "selected_seed": summary["selected_seed"],
                                "selected_acc_percent": _text(summary["acc_percent"]),
                                "selected_nmi_percent": _text(summary["nmi_percent"]),
                                "selected_inertia": _text(summary["inertia"]),
                                "acc_rank": summary["acc_rank"],
                            }
                        )
                        selected_acc.append(float(summary["acc_percent"]))
                        selected_nmi.append(float(summary["nmi_percent"]))
                        complete += 1
                    batch_rows.append(record)
                acc_mean, acc_sd = mean_and_sample_sd(selected_acc)
                nmi_mean, nmi_sd = mean_and_sample_sd(selected_nmi)
                summary_rows.append(
                    {
                        "benchmark": entry.benchmark,
                        "dataset_version": entry.version,
                        "representation": representation,
                        "protocol": protocol,
                        "n_complete_batches": complete,
                        "selected_acc_mean_percent": _text(acc_mean),
                        "selected_acc_sd_percent": _text(acc_sd),
                        "selected_nmi_mean_percent": _text(nmi_mean),
                        "selected_nmi_sd_percent": _text(nmi_sd),
                        "statistic": "across_selected_batches_not_within_batch",
                    }
                )
    return batch_rows, summary_rows


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, rule, *body])


def _benchmark_file(entry: DatasetEntry) -> str:
    if entry.benchmark == "YaleB" and entry.version.startswith("cropped"):
        return "YaleB_cropped.md"
    if entry.benchmark == "YaleB":
        return "YaleB_dengcai.md"
    return f"{entry.benchmark}.md"


def _fmt_pair(mean: str, sd: str) -> str:
    if mean == "":
        return ""
    if sd == "":
        return str(mean)
    return f"{mean} ± {sd}"


def write_markdown_views(
    entries: list[DatasetEntry],
    primary_rows: list[dict[str, Any]],
    ablation_rows: list[dict[str, Any]],
    repeat_summary: list[dict[str, Any]],
) -> None:
    sections = ["# Primary 2×4 matrix", "", "Accuracies are percent. P2 and P4 do not carry a within-batch SD.", ""]
    for entry in entries:
        block = [row for row in primary_rows if row["benchmark"] == entry.benchmark and row["dataset_version"] == entry.version]
        sections.append(f"## {entry.benchmark} `{entry.version}`")
        sections.append("")
        sections.append(f"Status `{entry.exact_dataset_status}`, comparison `{entry.comparison_class}`.")
        sections.append("")
        display = []
        for row in block:
            display.append(
                {
                    "method": row["method"],
                    "protocol": row["protocol"],
                    "ACC": _fmt_pair(str(row["acc_percent"]), str(row["acc_sd_percent"])),
                    "NMI": _fmt_pair(str(row["nmi_percent"]), str(row["nmi_sd_percent"])),
                    "inertia": row["inertia"],
                    "seed": row["selected_seed"],
                    "ACC rank": row["acc_rank"],
                    "solver": row["ssc_optimizer_status"],
                    "status": row["experiment_status"],
                }
            )
        sections.append(_markdown_table(display, ["method", "protocol", "ACC", "NMI", "inertia", "seed", "ACC rank", "solver", "status"]))
        sections.append("")
    _write_md(RESULTS / "primary_2x4_matrix.md", "\n".join(sections) + "\n")

    ablation_md = ["# SC versus SSC", "", "Same protocol on F and on G. Seeds for minimum inertia are chosen independently.", ""]
    ablation_md.append(
        _markdown_table(
            ablation_rows,
            [
                "benchmark",
                "dataset_version",
                "protocol",
                "our_sc_acc_percent",
                "our_ssc_acc_percent",
                "our_ssc_minus_sc_pp",
                "paper_ssc_minus_sc_pp",
                "gap_to_paper_ssc_pp",
                "comparison_class",
                "experiment_status",
            ],
        )
    )
    _write_md(RESULTS / "sc_vs_ssc_ablation.md", "\n".join(ablation_md) + "\n")

    repeat_lines = [
        "# Best-of-50 repeatability",
        "",
        "Each batch contributes one selected trial. The SD below is the sample SD across those selected trials.",
        "It is not the SD of the 50 K-means runs inside a batch.",
        "",
        _markdown_table(
            repeat_summary,
            [
                "benchmark",
                "dataset_version",
                "representation",
                "protocol",
                "n_complete_batches",
                "selected_acc_mean_percent",
                "selected_acc_sd_percent",
                "selected_nmi_mean_percent",
                "selected_nmi_sd_percent",
            ],
        ),
        "",
    ]
    _write_md(RESULTS / "repeatability_summary.md", "\n".join(repeat_lines))

    grouped: dict[str, list[DatasetEntry]] = defaultdict(list)
    for entry in entries:
        grouped[_benchmark_file(entry)].append(entry)
    for name, group in grouped.items():
        lines = [f"# {name[:-3]}", ""]
        for entry in group:
            lines.append(f"## `{entry.version}`")
            lines.append("")
            lines.append(entry.notes)
            lines.append("")
            lines.append(f"Exact status: `{entry.exact_dataset_status}`.")
            lines.append("")
            block = [
                row
                for row in primary_rows
                if row["benchmark"] == entry.benchmark and row["dataset_version"] == entry.version
            ]
            if block:
                lines.append(
                    _markdown_table(
                        block,
                        ["method", "protocol", "acc_percent", "acc_sd_percent", "nmi_percent", "experiment_status", "ssc_optimizer_status"],
                    )
                )
            else:
                lines.append("No protocol rows.")
            lines.append("")
        _write_md(PER_BENCHMARK / name, "\n".join(lines))


def write_failures(entries: list[DatasetEntry], primary_rows: list[dict[str, Any]]) -> None:
    lines = ["# Failures and blocked cells", ""]
    found = False
    for path in sorted(FAILURES_ROOT.glob("*.json")):
        found = True
        payload = json.loads(path.read_text(encoding="utf-8"))
        lines.append(f"- `{path.name}`: {payload.get('experiment_status')} — {payload.get('message')}")
    for row in primary_rows:
        if row["experiment_status"] != "COMPLETED":
            found = True
            lines.append(
                f"- {row['benchmark']} {row['dataset_version']} {row['method']} {row['protocol']}: "
                f"{row['experiment_status']} (n_trials={row['n_trials']})"
            )
    if not found:
        lines.append("No failed K-means cells were recorded. Blocked datasets stay in `dataset_status.csv` with an explicit status.")
    blocked = [entry for entry in entries if not entry.run_protocols]
    lines.extend(["", "## Not run", ""])
    for entry in blocked:
        lines.append(f"- {entry.benchmark} `{entry.version}`: {entry.exact_dataset_status}. {entry.notes}")
    _write_md(RESULTS / "failures.md", "\n".join(lines) + "\n")


def write_dataset_status(entries: list[DatasetEntry]) -> list[dict[str, Any]]:
    rows = [probe_entry(entry) for entry in entries]
    fields = [
        "benchmark",
        "dataset_version",
        "paper_benchmark",
        "benchmark_group",
        "counts_as_independent_benchmark",
        "exact_dataset_status",
        "comparison_class",
        "loader_status",
        "experiment_status",
        "n",
        "n_features",
        "n_classes",
        "dataset_sha256",
        "archive_sha256",
        "run_protocols",
        "notes",
    ]
    _write_csv(RESULTS / "dataset_status.csv", rows, fields)
    return rows


def aggregate() -> dict[str, Any]:
    entries = load_registry()
    trials = load_completed_trials(entries)
    _write_csv(RESULTS / "all_trial_results.csv", trials, TRIAL_FIELDS)
    status_rows = write_dataset_status(entries)
    primary = build_protocol_table(entries, trials, CORE_PROTOCOLS, "1")
    primary_fields = list(primary[0].keys()) if primary else ["benchmark"]
    _write_csv(RESULTS / "primary_2x4_matrix.csv", primary, primary_fields)
    ablation = build_ablation(entries, primary)
    _write_csv(RESULTS / "sc_vs_ssc_ablation.csv", ablation, list(ablation[0].keys()))
    _write_csv(RESULTS / "paper_acc_comparison.csv", ablation, list(ablation[0].keys()))
    nmi_rows = []
    for row in ablation:
        nmi_rows.append(
            {
                "benchmark": row["benchmark"],
                "dataset_version": row["dataset_version"],
                "protocol": row["protocol"],
                "our_sc_nmi_percent": row["our_sc_nmi_percent"],
                "our_ssc_nmi_percent": row["our_ssc_nmi_percent"],
                "our_nmi_ssc_minus_sc_pp": row["our_nmi_ssc_minus_sc_pp"],
                "paper_nmi_ssc_minus_sc_pp": row["paper_nmi_ssc_minus_sc_pp"],
                "comparison_class": row["comparison_class"],
                "exact_dataset_status": row["exact_dataset_status"],
                "experiment_status": row["experiment_status"],
            }
        )
    _write_csv(RESULTS / "paper_nmi_comparison.csv", nmi_rows, list(nmi_rows[0].keys()))
    _write_csv(RESULTS / "discrepancies.csv", ablation, list(ablation[0].keys()))
    gamma_rows = build_gamma(entries, trials)
    _write_csv(RESULTS / "gamma_sensitivity.csv", gamma_rows, list(gamma_rows[0].keys()) if gamma_rows else ["benchmark"])
    vanilla = build_protocol_table(entries, trials, VANILLA_PROTOCOLS, "1")
    _write_csv(RESULTS / "vanilla_kmeanspp.csv", vanilla, list(vanilla[0].keys()) if vanilla else ["benchmark"])
    selected = [
        row
        for row in primary + vanilla
        if row["selection_rule"] == "MIN_INERTIA"
    ]
    _write_csv(RESULTS / "best_inertia_selected_runs.csv", selected, list(selected[0].keys()) if selected else ["benchmark"])
    batch_rows, repeat_summary = build_repeatability(entries, trials)
    _write_csv(
        RESULTS / "repeatability_batches.csv",
        batch_rows,
        list(batch_rows[0].keys()) if batch_rows else ["benchmark"],
    )
    write_markdown_views(entries, primary, ablation, repeat_summary)
    write_failures(entries, primary)
    manifest_note = {
        "n_manifests": len(list(MANIFEST_ROOT.glob("*.json"))),
        "n_trial_rows": len(trials),
        "n_completed_primary_cells": sum(1 for row in primary if row["experiment_status"] == "COMPLETED"),
        "dataset_status_rows": len(status_rows),
    }
    (RESULTS / "run_count.json").write_text(json.dumps(manifest_note, indent=2) + "\n", encoding="utf-8")
    return manifest_note


__all__ = ["RESULTS", "aggregate", "load_completed_trials"]
