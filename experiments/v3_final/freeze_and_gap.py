"""Freeze the existing v3 reconstruction and restate the 72-cell gap from files."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "results" / "v3_reproduction" / "all_configurations.csv"
OUT = ROOT / "results" / "v3_final"
DOCS = ROOT / "docs" / "v3_final"
METHODS = ("kmeans", "sc", "pca_kmeans", "pca_sc", "lda_kmeans", "lda_sc", "llc", "spls", "ssc")
BENCHMARKS = ("AR", "JAFFE", "ORL", "UMIST", "BinAlpha", "MSRA50", "YaleB", "USPS")
BLOCKED = {
    "AR": "BLOCKED_DATA",
    "UMIST": "BLOCKED_DATA",
    "MSRA50": "BLOCKED_DATA",
    "BinAlpha": "SUBSET_UNVERIFIED",
}


def load_rows() -> list[dict[str, str]]:
    with CONFIGS.open() as handle:
        return list(csv.DictReader(handle))


def paper() -> dict:
    return yaml.safe_load((ROOT / "configs" / "v3" / "paper_reference.yaml").read_text())


def as_float(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def reference_rows(rows: list[dict[str, str]], benchmark: str, method: str) -> list[dict[str, str]]:
    chosen = [
        row for row in rows
        if row["historical_benchmark"] == benchmark
        and row["method"] == method
        and row["counts_as_historical"] == "True"
        and row["prep"] == "Y0"
        and row["report_role"] == "reference"
    ]
    if method in {"kmeans", "sc", "ssc"}:
        chosen = [row for row in chosen if row["initialization"] == "RANDOM"]
    return chosen


def fmt(mean: float | None, sd: float | None) -> str:
    if mean is None:
        return ""
    if sd is None:
        return f"{100 * mean:.2f}"
    return f"{100 * mean:.2f} ± {100 * sd:.2f}"


def main() -> None:
    rows = load_rows()
    reference = paper()
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    commits = sorted({row["code_commit"] for row in rows if row.get("code_commit")})
    provenance = []
    for commit in commits:
        subset = [row for row in rows if row.get("code_commit") == commit]
        provenance.append(
            {
                "source_commit": commit,
                "n_configuration_rows": len(subset),
                "methods": "|".join(sorted({row["method"] for row in subset})),
                "benchmarks": "|".join(sorted({row["historical_benchmark"] for row in subset})),
                "note": "Measurement commit stored on the frozen configuration row. Not rewritten.",
            }
        )
    _write(DOCS / "source_provenance.csv", provenance)
    matrix = []
    discrepancies = []
    for benchmark in BENCHMARKS:
        for method in METHODS:
            refs = reference_rows(rows, benchmark, method)
            paper_acc = reference["acc"][method if method != "pca_sc" else "pca_spectral"].get(benchmark, {}) if False else None
            acc_table = reference["acc"][_paper_method(method)][benchmark]
            nmi_table = reference["nmi"][_paper_method(method)][benchmark]
            blocker = "BLOCKED_METHOD" if method == "lda_sc" else BLOCKED.get(benchmark)
            if method == "lda_sc":
                status = "BLOCKED_METHOD"
            elif benchmark in {"AR", "UMIST", "MSRA50"}:
                status = "BLOCKED_DATA"
            elif benchmark == "BinAlpha":
                status = "SUBSET_UNVERIFIED"
            elif not refs:
                status = "GRID_NOT_COLLAPSED" if method in {"pca_kmeans", "pca_sc", "spls"} else "NO_REFERENCE_ROW"
            elif len(refs) == 1:
                status = "PRIMARY_REFERENCE"
            else:
                status = "MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED"
            primary = refs[0] if len(refs) == 1 else None
            measured_acc = as_float(primary["per_run_acc_mean"]) if primary else None
            measured_sd = as_float(primary["per_run_acc_sd"]) if primary else None
            measured_nmi = as_float(primary["per_run_nmi_mean"]) if primary else None
            measured_nmi_sd = as_float(primary["per_run_nmi_sd"]) if primary else None
            gap_acc = None if measured_acc is None else 100 * measured_acc - float(acc_table["mean"])
            gap_nmi = None if measured_nmi is None else 100 * measured_nmi - float(nmi_table["mean"])
            matrix.append(
                {
                    "benchmark": benchmark,
                    "method": method,
                    "execution_status": status,
                    "blocker": blocker or "",
                    "paper_acc": acc_table["mean"],
                    "paper_acc_sd": acc_table["sd"],
                    "paper_nmi": nmi_table["mean"],
                    "paper_nmi_sd": nmi_table["sd"],
                    "primary_acc": "" if measured_acc is None else 100 * measured_acc,
                    "primary_acc_sd": "" if measured_sd is None else 100 * measured_sd,
                    "primary_nmi": "" if measured_nmi is None else 100 * measured_nmi,
                    "primary_nmi_sd": "" if measured_nmi_sd is None else 100 * measured_nmi_sd,
                    "acc_gap_primary_minus_paper": "" if gap_acc is None else gap_acc,
                    "nmi_gap_primary_minus_paper": "" if gap_nmi is None else gap_nmi,
                    "primary_rule": "Y0 reference, RANDOM init, per-run mean; SSC gamma=1, both E8 and E13 kept" if method == "ssc" else "Y0 reference row; grids are not collapsed by ACC",
                    "n_reference_rows": len(refs),
                    "source_commits": "|".join(sorted({row["code_commit"] for row in refs})),
                    "locked_display_acc": _display(refs, "acc"),
                    "locked_display_nmi": _display(refs, "nmi"),
                }
            )
            if gap_acc is not None and abs(gap_acc) >= 5:
                discrepancies.append(
                    {
                        "benchmark": benchmark,
                        "method": method,
                        "kind": "PRIMARY_VERSUS_PAPER",
                        "acc_gap": gap_acc,
                        "nmi_gap": gap_nmi,
                        "note": "Prespecified primary minus printed table. Not an oracle.",
                    }
                )
    # Sensitivity views that must stay out of the primary table.
    for benchmark in ("USPS", "ORL", "JAFFE", "YaleB"):
        for row in rows:
            if row["historical_benchmark"] != benchmark or row["method"] != "ssc" or row["prep"] != "Y0":
                continue
            if row["initialization"] != "RANDOM" or row["report_role"] == "reference":
                continue
            if "1e+03" not in row["config_name"]:
                continue
            discrepancies.append(
                {
                    "benchmark": benchmark,
                    "method": "ssc",
                    "kind": "SENSITIVITY_GAMMA_1000_NOT_PRIMARY",
                    "dataset_id": row["dataset_id"],
                    "variant": row["variant"],
                    "acc_mean_percent": 100 * float(row["per_run_acc_mean"]),
                    "nmi_mean_percent": 100 * float(row["per_run_nmi_mean"]),
                    "note": "Gamma 1000 is a grid point. It is not selected because it is closer to the paper.",
                }
            )
    supplemental = [
        row for row in rows
        if row["counts_as_historical"] == "False" and row["prep"] == "Y0" and row["report_role"] == "reference"
    ]
    for row in supplemental:
        if row["historical_benchmark"] in {"UMIST", "BinAlpha"} and row["method"] in {"kmeans", "sc"} and row["initialization"] == "RANDOM":
            discrepancies.append(
                {
                    "benchmark": row["historical_benchmark"],
                    "method": row["method"],
                    "kind": "NON_EXACT_SUPPLEMENT",
                    "dataset_id": row["dataset_id"],
                    "acc_mean_percent": 100 * float(row["per_run_acc_mean"]),
                    "note": "UMIST575 and the BinAlpha candidate are not the historical 564 / full set.",
                }
            )
    _write(OUT / "reproduction_gap_matrix.csv", matrix)
    _write(DOCS / "reproduction_discrepancies.csv", discrepancies)
    _markdown(matrix)
    _docs(commits, matrix, discrepancies)


def _paper_method(method: str) -> str:
    return {"pca_sc": "pca_spectral", "lda_sc": "lda_spectral"}.get(method, method)


def _display(rows: list[dict[str, str]], metric: str) -> str:
    if not rows:
        return ""
    if len(rows) == 1:
        return fmt(as_float(rows[0][f"per_run_{metric}_mean"]), as_float(rows[0][f"per_run_{metric}_sd"]))
    parts = []
    for row in rows:
        label = row["dataset_id"]
        if row.get("variant"):
            label = f"{row['variant']}:{label}"
        parts.append(f"{label}:{fmt(as_float(row[f'per_run_{metric}_mean']), as_float(row[f'per_run_{metric}_sd']))}")
    return " ; ".join(parts)


def _markdown(matrix: list[dict]) -> None:
    lines = [
        "# 72-cell reproduction gap",
        "",
        "Primary numbers use the frozen label-blind rule: Y0, report role `reference`, and RANDOM initialization for K-means, SC, and SSC. SSC reference is gamma=1. E8 and E13 are both shown. PCA, PCA-SC, and SLPS grids are not collapsed. LDA-SC stays blocked. AR 840, UMIST 564, and MSRA50 stay blocked. Gamma 1000 is not promoted.",
        "",
        "| benchmark | method | status | primary ACC | paper ACC | ACC gap | primary NMI | paper NMI |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix:
        lines.append(
            "| {benchmark} | {method} | {execution_status} | {acc} | {paper_acc} | {gap} | {nmi} | {paper_nmi} |".format(
                benchmark=row["benchmark"],
                method=row["method"],
                execution_status=row["execution_status"],
                acc=row["locked_display_acc"],
                paper_acc=row["paper_acc"],
                gap=row["acc_gap_primary_minus_paper"],
                nmi=row["locked_display_nmi"],
                paper_nmi=row["paper_nmi"],
            )
        )
    (OUT / "reproduction_gap_matrix.md").write_text("\n".join(lines) + "\n")


def _docs(commits: list[str], matrix: list[dict], discrepancies: list[dict]) -> None:
    completed = sum(1 for row in matrix if row["execution_status"] in {"PRIMARY_REFERENCE", "MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED", "GRID_NOT_COLLAPSED"})
    (DOCS / "reproduction_freeze.md").write_text(
        "\n".join(
            [
                "# Reproduction freeze",
                "",
                "The executable v3 reconstruction is frozen as `REPRODUCTION_FROZEN_V3`.",
                "This round does not rerun the historical trial grid and does not change LLC Procrustes, parameter forwarding, LDA-Kmeans, SLPS, or the E8/E13 split.",
                "",
                f"Configuration rows were read from `results/v3_reproduction/all_configurations.csv`.",
                f"Source commits present on those rows: {', '.join(commits)}.",
                f"Cells with a frozen execution status other than a hard block: {completed} of 72.",
                "",
                "Primary SSC is gamma=1. The gamma=1000 USPS point remains a sensitivity row.",
                "Y0 remains the locked YaleB input. Y1--Y3 are diagnostics.",
                "New extensions use separate method ids X1--X5.",
                "",
            ]
        )
    )
    focus = [
        "# Reproduction root cause notes",
        "",
        "These notes restate the frozen measurements. They do not assign one cause to every gap.",
        "",
        "## ORL",
        "K-means is close to the printed ACC. SC and SSC at the prespecified gamma=1 point are lower than K-means and lower than the printed SC/SSC numbers. The gap is therefore not explained by a failed K-means baseline.",
        "",
        "## JAFFE",
        "The per-run mean is well below the printed SC/SSC numbers, while the separate min-inertia selection inside a batch is higher. The primary table keeps the per-run mean. Selection is not used as the historical protocol.",
        "",
        "## USPS",
        "At gamma=1, SSC stays near SC. Gamma=1000 was given extra solver iterations in the frozen runner because it was a prespecified priority point, not because its ACC was inspected. It is reported only as sensitivity.",
        "",
        "## UMIST and BinAlpha",
        "The historical UMIST cell is 564 images. The available 575-image sets are supplemental. The BinAlpha candidate, including any seed-0 subset, is not an exact historical cell.",
        "",
        "## YaleB",
        "Both 2414-image versions remain far from the printed SC and SSC numbers under Y0. Y3 is not promoted when its ACC is closer. See the controlled repair tables.",
        "",
        "## Still blocked",
        "LDA-SC is undefined in the source paper. AR 840, UMIST 564, and MSRA50 do not have a verified matrix. No samples were deleted to force a count of 564.",
        "",
    ]
    (OUT / "reproduction_root_cause.md").write_text("\n".join(focus))
    (DOCS / "reproduction_root_cause.md").write_text("\n".join(focus))


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()
