"""Tables and figures from results/extension_research/extension_matrix.csv.

Numbers are read from that CSV and from the per-run metrics.json files.
Nothing is filled from an older experiment.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from method_extension.common.clustering import bootstrap_mean_interval

ROOT = _ROOT
RESULT_DIR = ROOT / "results" / "extension_research"
FIG_DIR = RESULT_DIR / "figures"
MATRIX = RESULT_DIR / "extension_matrix.csv"
RUNS = ROOT / "runs" / "extension_research" / "full"


def _float(value: str):
    if value is None or value == "":
        return None
    return float(value)


def load_rows() -> list[dict]:
    with MATRIX.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _label(row: dict) -> str:
    variant = row["variant"]
    if variant in {"", "default", "control"}:
        return row["method"]
    return f"{row['method']}-{variant}"


def write_primary_markdown(rows: list[dict]) -> None:
    primary = [
        row
        for row in rows
        if row["role"] in {"primary", "auxiliary"} and row["gamma"] in {"1.0", "1"}
    ]
    lines = [
        "# Primary matrix, gamma = 1",
        "",
        "Source: `results/extension_research/extension_matrix.csv`. "
        "Sample standard deviation uses ddof=1 over the K-means seeds on one fixed representation. "
        "A blank standard deviation is a single assignment. "
        "Objective values are omitted here because different weights are different functions.",
        "",
        "| Dataset | Version | Eligibility | Method | Status | Trials | SC ACC | SSC ACC | SC NMI | SSC NMI | Move | W edges | W components | Fit s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in primary:
        def cell(key, digits=4):
            value = _float(row[key])
            if value is None:
                return ""
            return f"{value:.{digits}f}"

        std_sc = cell("sc_acc_std")
        std_g = cell("ssc_acc_std")
        sc = cell("sc_acc_mean")
        g = cell("ssc_acc_mean")
        sc_txt = sc if not std_sc else f"{sc} ± {std_sc}"
        g_txt = g if not std_g else f"{g} ± {std_g}"
        sn = cell("sc_nmi_mean")
        gn = cell("ssc_nmi_mean")
        lines.append(
            "| {dataset} | {version} | {eligibility} | {method} | {status} | {n} | {sc} | {g} | {sn} | {gn} | {move} | {edges} | {comp} | {fit} |".format(
                dataset=row["dataset"],
                version=row["version"],
                eligibility=row["eligibility"],
                method=_label(row),
                status=row["status"],
                n=row["n_trials"],
                sc=sc_txt,
                g=g_txt,
                sn=sn,
                gn=gn,
                move=cell("relative_move"),
                edges=row["n_edges"],
                comp=row["n_components"],
                fit=row["fit_sec"],
            )
        )
    (RESULT_DIR / "primary_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gamma_and_oracle(rows: list[dict]) -> None:
    grid = [row for row in rows if row["role"] in {"primary", "gamma_grid"} and row["method"] not in {"E07", "mutual_knn"}]
    lines = [
        "# Gamma grid",
        "",
        "Every preset gamma is listed. The largest ACC in a dataset/method block is not the selected operating point.",
        "",
        "| Dataset | Version | Method | Gamma | Status | SSC ACC | SC ACC |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    oracle_lines = [
        "dataset,version,method,variant,oracle_gamma,oracle_ssc_acc,oracle_status,label",
    ]
    grouped = defaultdict(list)
    for row in grid:
        lines.append(
            f"| {row['dataset']} | {row['version']} | {_label(row)} | {row['gamma']} | {row['status']} | {row['ssc_acc_mean']} | {row['sc_acc_mean']} |"
        )
        grouped[(row["dataset"], row["version"], row["method"], row["variant"])].append(row)
    for key, group in sorted(grouped.items()):
        scored = [row for row in group if _float(row["ssc_acc_mean"]) is not None]
        if not scored:
            oracle_lines.append(",".join([*key, "", "", "NOT_RUN", "ORACLE_UPPER_BOUND"]))
            continue
        best = max(scored, key=lambda row: _float(row["ssc_acc_mean"]))
        oracle_lines.append(
            ",".join(
                [
                    key[0],
                    key[1],
                    key[2],
                    key[3],
                    best["gamma"],
                    best["ssc_acc_mean"],
                    best["status"],
                    "ORACLE_UPPER_BOUND",
                ]
            )
        )
    (RESULT_DIR / "gamma_sensitivity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULT_DIR / "oracle_upper_bound.csv").write_text("\n".join(oracle_lines) + "\n", encoding="utf-8")


def write_failures(rows: list[dict]) -> None:
    lines = ["# Statuses that are not a completed numeric cell", ""]
    interesting = {"FAILED", "NONCONVERGED", "BLOCKED", "BLOCKED_DATA", "EXCLUDED", "NOT_RUN", "COMPLETE_SINGLE_ASSIGNMENT"}
    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    lines.append("Counts by status:")
    lines.append("")
    for status, count in sorted(counts.items()):
        lines.append(f"- `{status}`: {count}")
    lines.append("")
    lines.append("NONCONVERGED rows still contain the ACC/NMI of the returned G. They are not missing cells and they are not zeros.")
    lines.append("")
    lines.append("| Dataset | Version | Method | Gamma | Status | Notes |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for row in rows:
        if row["status"] in interesting and row["status"] != "NONCONVERGED":
            note = (row.get("notes") or "").replace("|", "/")
            lines.append(
                f"| {row['dataset']} | {row['version']} | {_label(row)} | {row['gamma']} | {row['status']} | {note} |"
            )
    (RESULT_DIR / "failures.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_runtime(rows: list[dict]) -> None:
    lines = ["# Runtime", "", "| Dataset | Version | Method | Gamma | Fit seconds | K-means seconds | Status |", "| --- | --- | --- | --- | --- | --- | --- |"]
    total = 0.0
    timed_out = 0
    for row in rows:
        fit = _float(row["fit_sec"])
        km = _float(row["kmeans_sec"])
        if fit is not None:
            total += fit
        if km is not None:
            total += km
        if row["status"] == "FAILED" and "exceeded 180s" in (row.get("notes") or ""):
            timed_out += 1
        if row["fit_sec"] or row["kmeans_sec"]:
            lines.append(
                f"| {row['dataset']} | {row['version']} | {_label(row)} | {row['gamma']} | {row['fit_sec']} | {row['kmeans_sec']} | {row['status']} |"
            )
    lines.append("")
    lines.append(f"Sum of recorded fit and K-means seconds: {total:.1f}.")
    lines.append(
        f"Blank fit times are excluded. {timed_out} FAILED cells each stopped at the 180s solver timeout and are not in that sum."
    )
    (RESULT_DIR / "runtime.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _control_map(rows: list[dict]) -> dict:
    out = {}
    for row in rows:
        if row["method"] == "ssc" and row["variant"] == "control" and row["role"] == "primary":
            out[(row["dataset"], row["version"])] = row
    return out


def write_ablation(rows: list[dict]) -> None:
    control = _control_map(rows)
    lines = [
        "# Ablation against the E8 control at gamma = 1",
        "",
        "Delta is extension SSC ACC minus control SSC ACC on the same dataset version. "
        "It is not a comparison of objective values.",
        "",
        "| Dataset | Version | Method | SSC ACC | Control SSC ACC | Delta ACC | Delta vs its SC |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    primary = [row for row in rows if row["role"] in {"primary", "auxiliary"} and row["method"] != "E07"]
    for row in primary:
        base = control.get((row["dataset"], row["version"]))
        acc = _float(row["ssc_acc_mean"])
        sc = _float(row["sc_acc_mean"])
        base_acc = _float(base["ssc_acc_mean"]) if base else None
        delta = "" if acc is None or base_acc is None else f"{acc - base_acc:.4f}"
        versus_sc = "" if acc is None or sc is None else f"{acc - sc:.4f}"
        lines.append(
            f"| {row['dataset']} | {row['version']} | {_label(row)} | {row['ssc_acc_mean']} | "
            f"{'' if base is None else base['ssc_acc_mean']} | {delta} | {versus_sc} |"
        )
    (RESULT_DIR / "ablation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_bootstrap(rows: list[dict]) -> None:
    lines = [
        "# Bootstrap intervals for paired K-means seeds",
        "",
        "Each interval is a 2000-draw percentile interval for the mean of seed-wise ACC differences on one fixed pair of representations. "
        "It does not cover a new sample of images.",
        "",
        "| Dataset | Version | Contrast | Mean delta | 2.5% | 97.5% | Seeds |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    payload = []
    by_key = {(row["dataset"], row["version"], row["method"], row["variant"], row["role"]): row for row in rows}
    for row in rows:
        if row["role"] not in {"primary", "auxiliary"}:
            continue
        if row["n_trials"] != "50":
            continue
        path = RUNS / row["run_id"] / "metrics.json"
        if not path.is_file():
            continue
        metrics = json.loads(path.read_text(encoding="utf-8"))
        if "ssc_acc" not in metrics or "sc_acc" not in metrics:
            continue
        ssc = np.asarray(metrics["ssc_acc"], dtype=np.float64)
        sc = np.asarray(metrics["sc_acc"], dtype=np.float64)
        if ssc.shape != sc.shape or ssc.size != 50:
            continue
        mean, low, high = bootstrap_mean_interval(ssc - sc, n_boot=2000, seed=0)
        lines.append(
            f"| {row['dataset']} | {row['version']} | {_label(row)} G minus F | {mean:.4f} | {low:.4f} | {high:.4f} | 50 |"
        )
        payload.append({"dataset": row["dataset"], "version": row["version"], "method": _label(row), "contrast": "G_minus_F", "mean": mean, "low": low, "high": high})
        if row["method"] == "ssc":
            continue
        control = by_key.get((row["dataset"], row["version"], "ssc", "control", "primary"))
        if control is None:
            continue
        control_path = RUNS / control["run_id"] / "metrics.json"
        if not control_path.is_file():
            continue
        control_metrics = json.loads(control_path.read_text(encoding="utf-8"))
        base = np.asarray(control_metrics["ssc_acc"], dtype=np.float64)
        if base.shape != ssc.shape:
            continue
        mean, low, high = bootstrap_mean_interval(ssc - base, n_boot=2000, seed=0)
        lines.append(
            f"| {row['dataset']} | {row['version']} | {_label(row)} minus SSC | {mean:.4f} | {low:.4f} | {high:.4f} | 50 |"
        )
        payload.append({"dataset": row["dataset"], "version": row["version"], "method": _label(row), "contrast": "minus_SSC", "mean": mean, "low": low, "high": high})
    (RESULT_DIR / "bootstrap.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULT_DIR / "bootstrap.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_dataset_pages(rows: list[dict]) -> None:
    grouped = defaultdict(list)
    for row in rows:
        if row["role"] in {"primary", "auxiliary"}:
            grouped[(row["dataset"], row["version"])].append(row)
    for (dataset, version), group in grouped.items():
        lines = [f"# {dataset} {version}", "", f"Eligibility: `{group[0]['eligibility']}`.", ""]
        for row in group:
            lines.append(
                f"- `{_label(row)}` status `{row['status']}` SSC ACC `{row['ssc_acc_mean']}` "
                f"SC ACC `{row['sc_acc_mean']}` NMI SSC/SC `{row['ssc_nmi_mean']}`/`{row['sc_nmi_mean']}` "
                f"trials `{row['n_trials']}` run `{row['run_id']}`"
            )
        safe = f"{dataset}_{version or 'blocked'}".replace("/", "_")
        (RESULT_DIR / f"benchmark_{safe}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _heatmap(rows: list[dict]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    control = _control_map(rows)
    methods = []
    datasets = []
    for row in rows:
        if row["role"] != "primary" or row["method"] in {"E07", "ssc"}:
            continue
        label = _label(row)
        key = (row["dataset"], row["version"])
        if label not in methods:
            methods.append(label)
        if key not in datasets:
            datasets.append(key)
    if not methods or not datasets:
        return
    matrix = np.full((len(methods), len(datasets)), np.nan)
    for row in rows:
        if row["role"] != "primary" or row["method"] in {"E07", "ssc"}:
            continue
        base = control.get((row["dataset"], row["version"]))
        acc = _float(row["ssc_acc_mean"])
        base_acc = _float(base["ssc_acc_mean"]) if base else None
        if acc is None or base_acc is None:
            continue
        i = methods.index(_label(row))
        j = datasets.index((row["dataset"], row["version"]))
        matrix[i, j] = acc - base_acc
    fig, ax = plt.subplots(figsize=(12, 7))
    image = ax.imshow(matrix, cmap="coolwarm", aspect="auto")
    ax.set_xticks(range(len(datasets)))
    ax.set_xticklabels([f"{a}\n{b}" for a, b in datasets], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods, fontsize=8)
    ax.set_title("SSC ACC minus E8 control at gamma=1")
    fig.colorbar(image, ax=ax, fraction=0.03)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "delta_acc_heatmap.png", dpi=140)
    plt.close(fig)

    # ACC bars for the control only, SC vs SSC.
    labels = []
    sc_vals = []
    g_vals = []
    for key, row in control.items():
        if _float(row["sc_acc_mean"]) is None:
            continue
        labels.append(f"{key[0]}\n{key[1]}")
        sc_vals.append(_float(row["sc_acc_mean"]))
        g_vals.append(_float(row["ssc_acc_mean"]))
    if labels:
        fig, ax = plt.subplots(figsize=(10, 4))
        x = np.arange(len(labels))
        ax.bar(x - 0.18, sc_vals, width=0.36, label="SC on F")
        ax.bar(x + 0.18, g_vals, width=0.36, label="SSC E8 on G")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel("ACC")
        ax.set_title("Control E8, gamma=1")
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIG_DIR / "control_acc_nmi.png", dpi=140)
        plt.close(fig)

    # Gamma curves of SSC ACC for the control.
    fig, ax = plt.subplots(figsize=(8, 4))
    for key in datasets:
        series = [
            row
            for row in rows
            if row["dataset"] == key[0]
            and row["version"] == key[1]
            and row["method"] == "ssc"
            and row["variant"] == "control"
            and _float(row["ssc_acc_mean"]) is not None
        ]
        series.sort(key=lambda row: _float(row["gamma"]))
        if not series:
            continue
        ax.plot([_float(row["gamma"]) for row in series], [_float(row["ssc_acc_mean"]) for row in series], marker="o", label=f"{key[0]} {key[1]}")
    ax.set_xscale("log")
    ax.set_xlabel("gamma")
    ax.set_ylabel("SSC ACC")
    ax.set_title("E8 gamma grid (not selected by ACC)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "gamma_curves.png", dpi=140)
    plt.close(fig)

    # Graph diagnostics: components vs delta ACC for primary extensions.
    fig, ax = plt.subplots(figsize=(6, 4))
    for row in rows:
        if row["role"] != "primary" or row["method"] == "E07":
            continue
        comps = _float(row["n_components"])
        base = control.get((row["dataset"], row["version"]))
        acc = _float(row["ssc_acc_mean"])
        base_acc = _float(base["ssc_acc_mean"]) if base else None
        if comps is None or acc is None or base_acc is None:
            continue
        ax.scatter(comps, acc - base_acc, s=18)
    ax.set_xlabel("Connected components of W")
    ax.set_ylabel("SSC ACC minus control")
    ax.set_title("Graph fragmentation versus ACC change")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "graph_diagnostics.png", dpi=140)
    plt.close(fig)


def main() -> None:
    if not MATRIX.is_file():
        raise SystemExit(f"missing {MATRIX}")
    rows = load_rows()
    write_primary_markdown(rows)
    write_gamma_and_oracle(rows)
    write_failures(rows)
    write_runtime(rows)
    write_ablation(rows)
    write_bootstrap(rows)
    write_dataset_pages(rows)
    _heatmap(rows)
    print(f"rows {len(rows)}", flush=True)


if __name__ == "__main__":
    main()
