#!/usr/bin/env python3
"""Build Tables 1-8 from actual run records. Paper numbers stay labeled as reported."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aggregate import completed, load_all_runs, pct
from experiments.paper_reported import ACC as PAPER_ACC
from experiments.paper_reported import DATASETS as PAPER_DATASETS
from experiments.paper_reported import NMI as PAPER_NMI
from experiments.protocol import SELECTION_RULE

OUT = ROOT / "results" / "tables"
REPORT_TABLES = ROOT / "report" / "tables"
RUNS = ROOT / "runs"
GAMMA_TEX = {
    1e-6: r"$10^{-6}$",
    1e-3: r"$10^{-3}$",
    1.0: r"$1$",
    1e3: r"$10^{3}$",
    1e6: r"$10^{6}$",
}

MAIN_METHODS = [
    "kmeans",
    "sc",
    "pca_kmeans",
    "pca_spectral",
    "lda_kmeans",
    "llc",
    "spls",
    "ssc",
]
METHOD_LABEL = {
    "kmeans": "K-means",
    "sc": "SC",
    "pca_kmeans": "PCA-KM",
    "pca_spectral": "PCA-SC",
    "lda_kmeans": "LDA-KM",
    "lda_spectral": "LDA-SC (APPROXIMATE)",
    "llc": "LLC",
    "spls": "SPLS",
    "ssc": "SSC",
    "rssc": "RSSC",
}
AVAILABLE = ("ORL", "JAFFE", "YaleB", "USPS")
UNAVAILABLE = ("AR", "UMIST", "BinAlpha", "MSRA50")


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _write_md(path: Path, title: str, caption: str, header: list[str], rows: list[list[Any]]) -> None:
    lines = [f"# {title}", "", caption, "", "| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _filter(rows, **kwargs):
    out = []
    for row in rows:
        ok = True
        for key, value in kwargs.items():
            if row.get(key) != value:
                ok = False
                break
        if ok:
            out.append(row)
    return out


def table1_inventory(rows: list[dict[str, Any]]) -> tuple[list[str], list[list[Any]]]:
    header = [
        "Dataset",
        "Availability",
        "n",
        "c",
        "d",
        "Verification",
        "Completed runs",
        "Notes",
    ]
    notes = {
        "ORL": "Olivetti 64x64 resized to 32x32; approximate vs 92x112 originals",
        "JAFFE": "Zenodo 213 TIFF, 26x26; research-only, images not committed",
        "YaleB": "Deng Cai 32x32 mat; approximate vs from-scratch UCSD resize",
        "USPS": "LIBSVM 16x16 9298 samples; verified counts",
        "AR": "passworded license; DatasetUnavailable",
        "UMIST": "archive not retrieved",
        "BinAlpha": "exact 26x30 set not found; Binary Alphadigits not substituted",
        "MSRA50": "1799/12 archive not found; other MSRA not substituted",
    }
    counts = defaultdict(int)
    shapes = {}
    for row in rows:
        if row.get("dataset"):
            counts[row["dataset"]] += 1 if row["status"] == "COMPLETED" else 0
            metrics = row.get("metrics") or {}
            if metrics.get("n_samples"):
                shapes[row["dataset"]] = (
                    metrics.get("n_samples"),
                    metrics.get("n_clusters"),
                    metrics.get("n_features"),
                )
    body = []
    known_shapes = {
        "ORL": (400, 40, 1024),
        "JAFFE": (213, 10, 676),
        "YaleB": (2414, 38, 1024),
        "USPS": (9298, 10, 256),
    }
    for name in PAPER_DATASETS:
        avail = "available" if name in AVAILABLE else "unavailable"
        ver = {
            "ORL": "approximate",
            "JAFFE": "verified",
            "YaleB": "approximate",
            "USPS": "verified",
        }.get(name, "unavailable")
        n, c, d = shapes.get(name) or known_shapes.get(name) or ("N/A", "N/A", "N/A")
        body.append([name, avail, n, c, d, ver, counts.get(name, 0), notes[name]])
    return header, body


def _best_track_a(rows, method, dataset):
    subset = [
        row
        for row in completed(rows)
        if row["method"] == method
        and row["dataset"] == dataset
        and str(row["track"]).upper() in {"TRACKA", "TRACK_A", "PILOT"}
    ]
    # Prefer TRACKA over PILOT when both exist.
    tracka = [row for row in subset if str(row["track"]).upper() in {"TRACKA", "TRACK_A"}]
    pool = tracka or subset
    if not pool:
        return None
    return max(pool, key=lambda row: (row["acc_mean"] if row["acc_mean"] is not None else -1.0))


def table_track_a(rows, metric: str) -> tuple[list[str], list[list[Any]], list[list[Any]]]:
    paper = PAPER_ACC if metric == "acc" else PAPER_NMI
    header = ["Method", "Source"] + list(PAPER_DATASETS)
    body = []
    run_ids = []
    for method in MAIN_METHODS:
        paper_row = [METHOD_LABEL[method], "Reported in Chang et al. (2015)"]
        our_row = [METHOD_LABEL[method], "Our Reproduction"]
        id_row = [METHOD_LABEL[method], "run_id"]
        for dataset in PAPER_DATASETS:
            pmean, pstd = paper[method][dataset]
            paper_row.append(f"{pmean:.1f} ± {pstd:.1f}")
            if method == "spls":
                our_row.append("N/A — not reproduced")
                id_row.append("SKIPPED")
                continue
            if dataset in UNAVAILABLE:
                our_row.append("N/A — not reproduced")
                id_row.append("dataset unavailable")
                continue
            chosen = _best_track_a(rows, method, dataset)
            if chosen is None:
                our_row.append("N/A — not reproduced")
                id_row.append("no completed run")
            else:
                mean = chosen["acc_mean"] if metric == "acc" else chosen["nmi_mean"]
                std = chosen["acc_std"] if metric == "acc" else chosen["nmi_std"]
                n = chosen["n_trials_completed"]
                our_row.append(f"{pct(mean, std)} (n={n})")
                extra = []
                if chosen.get("gamma") is not None:
                    extra.append(f"gamma={chosen['gamma']}")
                if chosen.get("n_components") is not None:
                    extra.append(f"dim={chosen['n_components']}")
                id_row.append(chosen["run_id"] + ((" " + " ".join(extra)) if extra else ""))
        body.append(paper_row)
        body.append(our_row)
        run_ids.append(id_row)
    return header, body, run_ids


def table_track_b(rows) -> tuple[list[str], list[list[Any]]]:
    header = ["Method", "Metric"] + list(AVAILABLE)
    methods = ["kmeans", "sc", "pca_kmeans", "pca_spectral", "lda_kmeans", "llc", "ssc"]
    body = []
    for method in methods:
        for metric, key_mean, key_std in (("ACC%", "acc_mean", "acc_std"), ("NMI%", "nmi_mean", "nmi_std")):
            line = [METHOD_LABEL[method], metric]
            for dataset in AVAILABLE:
                matches = [
                    row
                    for row in completed(rows)
                    if row["method"] == method and row["dataset"] == dataset and str(row["track"]).upper() in {"TRACKB", "TRACK_B"}
                ]
                if not matches:
                    # Track B gamma=1 SSC may reuse a TRACKA gamma=1 completed run if TRACKB was not launched.
                    if method == "ssc":
                        matches = [
                            row
                            for row in completed(rows)
                            if row["method"] == "ssc"
                            and row["dataset"] == dataset
                            and row.get("gamma") in {1, 1.0, "1", "1.0"}
                        ]
                if not matches:
                    line.append("N/A — not reproduced")
                else:
                    chosen = max(matches, key=lambda r: r["n_trials_completed"])
                    line.append(
                        f"{pct(chosen[key_mean], chosen[key_std])} (n={chosen['n_trials_completed']}; {chosen['run_id']})"
                    )
            body.append(line)
    return header, body


def table_ex1(rows) -> tuple[list[str], list[list[Any]]]:
    header = ["Dataset", "A0 SSC ACC", "A1 RSSC ACC", "A0 SSC NMI", "A1 RSSC NMI", "n trials", "run ids"]
    body = []
    for dataset in AVAILABLE:
        pair = {}
        for method in ("ssc", "rssc"):
            matches = [
                row
                for row in completed(rows)
                if row["method"] == method
                and row["dataset"] == dataset
                and str(row["track"]).upper() in {"EX1", "TRACKB", "TRACKA", "PILOT"}
                and (row.get("gamma") in {1, 1.0, None, "1", "1.0"} or method != "ssc")
            ]
            # Prefer EX1.
            preferred = [row for row in matches if str(row["track"]).upper() == "EX1"] or matches
            if preferred:
                pair[method] = max(preferred, key=lambda r: r["n_trials_completed"])
        if "ssc" not in pair and "rssc" not in pair:
            body.append([dataset, "N/A — not reproduced", "N/A — not reproduced", "N/A — not reproduced", "N/A — not reproduced", "0", ""])
            continue
        def cell(method, metric):
            row = pair.get(method)
            if row is None:
                return "N/A — not reproduced"
            mean = row["acc_mean"] if metric == "acc" else row["nmi_mean"]
            std = row["acc_std"] if metric == "acc" else row["nmi_std"]
            return pct(mean, std)
        n = min((pair[m]["n_trials_completed"] for m in pair), default=0)
        ids = "; ".join(f"{m}={pair[m]['run_id']}" for m in pair)
        body.append([dataset, cell("ssc", "acc"), cell("rssc", "acc"), cell("ssc", "nmi"), cell("rssc", "nmi"), n, ids])
    return header, body


def _perturb_key(row) -> tuple:
    spec = row.get("perturbation") or {}
    if not spec:
        return (None, None, None)
    return (spec.get("type"), spec.get("level"), spec.get("seed"))


def table_robustness(rows) -> tuple[list[str], list[list[Any]]]:
    header = ["Experiment", "Dataset", "Level", "Perturb seed", "SSC ACC", "RSSC ACC", "SSC NMI", "RSSC NMI", "n", "run ids"]
    body = []
    for track, default_level in (("EX2", None), ("EX3", 0.1), ("EX4", 0.05), ("EX5", 0.1)):
        subset = [row for row in completed(rows) if str(row["track"]).upper() == track]
        grouped = defaultdict(dict)
        for row in subset:
            spec = row.get("perturbation") or {}
            key = (row["dataset"], spec.get("level"), spec.get("seed"))
            grouped[key][row["method"]] = row
        for key in sorted(grouped, key=lambda t: (str(t[0]), float(t[1] or 0), int(t[2] or 0))):
            pair = grouped[key]
            dataset, level, seed = key
            def cell(method, metric):
                row = pair.get(method)
                if row is None:
                    return "N/A — not reproduced"
                mean = row["acc_mean"] if metric == "acc" else row["nmi_mean"]
                std = row["acc_std"] if metric == "acc" else row["nmi_std"]
                return f"{pct(mean, std)} (n={row['n_trials_completed']})"
            ids = "; ".join(f"{m}={pair[m]['run_id']}" for m in pair)
            n = min((pair[m]["n_trials_completed"] for m in pair), default=0)
            body.append(
                [
                    track,
                    dataset,
                    level,
                    seed,
                    cell("ssc", "acc"),
                    cell("rssc", "acc"),
                    cell("ssc", "nmi"),
                    cell("rssc", "nmi"),
                    n,
                    ids,
                ]
            )
    if not body:
        body.append(["EX2-EX4", "—", "—", "—", "N/A — not reproduced", "N/A — not reproduced", "N/A — not reproduced", "N/A — not reproduced", 0, ""])
    return header, body


def table_k_and_ablation(rows) -> tuple[list[str], list[list[Any]]]:
    header = ["Dataset", "k", "A0 SSC ACC", "A1 RSSC ACC", "A0 NMI", "A1 NMI", "n", "run ids"]
    body = []
    subset = [row for row in completed(rows) if str(row["track"]).upper() in {"EX6", "EX1", "TRACKB", "TRACKA"}]
    for dataset in ("ORL", "JAFFE", "YaleB"):
        for k in (3, 5, 7, 9):
            pair = {}
            for method in ("ssc", "rssc"):
                matches = [
                    row
                    for row in subset
                    if row["method"] == method
                    and row["dataset"] == dataset
                    and int(row.get("k") or 5) == k
                    and (row.get("gamma") in {1, 1.0, None, "1", "1.0"})
                    and not row.get("perturbation")
                ]
                preferred = [row for row in matches if str(row["track"]).upper() == "EX6"] or matches
                if preferred:
                    pair[method] = max(preferred, key=lambda r: r["n_trials_completed"])
            if not pair:
                continue
            def cell(method, metric):
                row = pair.get(method)
                if row is None:
                    return "N/A — not reproduced"
                mean = row["acc_mean"] if metric == "acc" else row["nmi_mean"]
                std = row["acc_std"] if metric == "acc" else row["nmi_std"]
                return pct(mean, std)
            ids = "; ".join(f"{m}={pair[m]['run_id']}" for m in pair)
            n = min((pair[m]["n_trials_completed"] for m in pair), default=0)
            body.append([dataset, k, cell("ssc", "acc"), cell("rssc", "acc"), cell("ssc", "nmi"), cell("rssc", "nmi"), n, ids])
    if not body:
        body.append(["—", "—", "N/A — not reproduced", "N/A — not reproduced", "N/A — not reproduced", "N/A — not reproduced", 0, ""])
    return header, body


def table_runtime(rows) -> tuple[list[str], list[list[Any]]]:
    header = [
        "Dataset",
        "Method",
        "IRLS seconds",
        "IRLS iters",
        "Converged",
        "Final Eq8",
        "n trials",
        "run_id",
        "status",
    ]
    body = []
    for row in rows:
        if row["method"] not in {"ssc", "rssc"}:
            continue
        if str(row["track"]).upper() not in {"EX1", "TRACKB", "TRACKA", "PILOT", "EX7", "EX8"}:
            continue
        if row.get("perturbation"):
            continue
        hist = row.get("objective_history_text") or ""
        final_obj = ""
        if hist:
            lines = [ln for ln in hist.strip().splitlines() if ln]
            if len(lines) >= 2:
                keys = lines[0].split(",")
                last = lines[-1].split(",")
                if "equation8_objective" in keys:
                    final_obj = last[keys.index("equation8_objective")]
        body.append(
            [
                row["dataset"],
                row["method"],
                row.get("irls_seconds"),
                row.get("irls_iterations"),
                row.get("irls_converged"),
                final_obj,
                row.get("n_trials_completed"),
                row["run_id"],
                row["status"],
            ]
        )
    if not body:
        body.append(["—", "—", "N/A — not reproduced", "", "", "", 0, "", ""])
    return header, body


def table_gamma(rows) -> tuple[list[str], list[list[Any]]]:
    header = ["Dataset", "gamma", "ACC%", "NMI%", "n trials", "run_id"]
    body = []
    for dataset in AVAILABLE:
        matches = [
            row
            for row in completed(rows)
            if row["method"] == "ssc"
            and row["dataset"] == dataset
            and str(row["track"]).upper() in {"TRACKA", "TRACK_A"}
            and row.get("gamma") is not None
            and not row.get("perturbation")
        ]
        by_g: dict[float, dict[str, Any]] = {}
        for row in matches:
            gamma = float(row["gamma"])
            prev = by_g.get(gamma)
            if prev is None or (row["n_trials_completed"] or 0) > (prev["n_trials_completed"] or 0):
                by_g[gamma] = row
        for gamma in sorted(by_g):
            row = by_g[gamma]
            n = row["n_trials_completed"]
            body.append(
                [
                    dataset,
                    gamma,
                    f"{pct(row['acc_mean'], row['acc_std'] if n and n > 1 else None)} (n={n})",
                    f"{pct(row['nmi_mean'], row['nmi_std'] if n and n > 1 else None)} (n={n})",
                    n,
                    row["run_id"],
                ]
            )
    if not body:
        body.append(["—", "—", "N/A — not reproduced", "N/A — not reproduced", 0, ""])
    return header, body


def _fmt_pct_tex(mean: float | None, std: float | None, n: int | None) -> str:
    if mean is None:
        return r"N/A"
    n_int = int(n) if n is not None else 0
    if n_int <= 1 or std is None:
        return rf"{100.0 * float(mean):.1f} ($n$={n_int})"
    return rf"{100.0 * float(mean):.1f}$\pm${100.0 * float(std):.1f} ($n$={n_int})"


def _fmt_gamma_tex(gamma: float) -> str:
    for key, label in GAMMA_TEX.items():
        if abs(float(gamma) - key) <= 1e-18 * max(1.0, abs(key)):
            return label
        if key > 0 and abs(float(gamma) - key) / key < 1e-9:
            return label
    return f"{gamma:g}"


def _write_tex_tabular(path: Path, colspec: str, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{tabular}{" + colspec + "}",
        r"\toprule",
        " & ".join(header) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(str(cell) for cell in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report_tex(rows: list[dict[str, Any]]) -> None:
    REPORT_TABLES.mkdir(parents=True, exist_ok=True)
    notes = {
        "ORL": r"Olivetti $64\times64\to32\times32$",
        "JAFFE": r"Zenodo TIFF $\to26\times26$",
        "YaleB": r"Deng Cai $32\times32$ mat",
        "USPS": r"LIBSVM $16\times16$",
        "AR": r"access URLs failed",
        "UMIST": r"WAF / 404; no archive",
        "BinAlpha": r"no $26\times30$ file",
        "MSRA50": r"no $1799/12$ file",
    }
    ds_header = [r"Dataset", r"Status", r"$n$", r"$c$", r"$d$", r"Notes"]
    ds_body = []
    shapes = {
        "ORL": (400, 40, 1024),
        "JAFFE": (213, 10, 676),
        "YaleB": (2414, 38, 1024),
        "USPS": (9298, 10, 256),
    }
    status = {
        "ORL": "approximate",
        "JAFFE": "verified",
        "YaleB": "approximate",
        "USPS": "verified",
    }
    for name in PAPER_DATASETS:
        if name in AVAILABLE:
            n, c, d = shapes[name]
            ds_body.append([name, status[name], str(n), str(c), str(d), notes[name]])
        else:
            ds_body.append([name, "unavailable", "---", "---", "---", notes[name]])
    _write_tex_tabular(REPORT_TABLES / "dataset_status.tex", "llrrrl", ds_header, ds_body)

    obtained = list(AVAILABLE)
    for metric, filename in (("acc", "track_a_acc.tex"), ("nmi", "track_a_nmi.tex")):
        paper = PAPER_ACC if metric == "acc" else PAPER_NMI
        header = [r"Method", r"Source"] + obtained
        body = []
        for method in MAIN_METHODS:
            paper_row = [METHOD_LABEL[method], r"Chang et al.\ (2015)"]
            our_row = [METHOD_LABEL[method], r"Our Reproduction"]
            for dataset in obtained:
                pmean, pstd = paper[method][dataset]
                paper_row.append(rf"{pmean:.1f}$\pm${pstd:.1f}")
                if method == "spls":
                    our_row.append(r"N/A --- not reproduced")
                    continue
                chosen = _best_track_a(rows, method, dataset)
                if chosen is None:
                    our_row.append(r"N/A --- not reproduced")
                else:
                    mean = chosen["acc_mean"] if metric == "acc" else chosen["nmi_mean"]
                    std = chosen["acc_std"] if metric == "acc" else chosen["nmi_std"]
                    our_row.append(_fmt_pct_tex(mean, std, chosen["n_trials_completed"]))
            body.append(paper_row)
            body.append(our_row)
        _write_tex_tabular(REPORT_TABLES / filename, "llcccc", header, body)

    for metric, key_mean, key_std, filename in (
        ("ACC", "acc_mean", "acc_std", "track_b_acc.tex"),
        ("NMI", "nmi_mean", "nmi_std", "track_b_nmi.tex"),
    ):
        header = [r"Method"] + obtained
        body = []
        for method in ["kmeans", "sc", "pca_kmeans", "pca_spectral", "lda_kmeans", "llc", "ssc"]:
            line = [METHOD_LABEL[method]]
            for dataset in obtained:
                matches = [
                    row
                    for row in completed(rows)
                    if row["method"] == method
                    and row["dataset"] == dataset
                    and str(row["track"]).upper() in {"TRACKB", "TRACK_B"}
                ]
                reused_track_a = False
                if not matches and method == "ssc":
                    matches = [
                        row
                        for row in completed(rows)
                        if row["method"] == "ssc"
                        and row["dataset"] == dataset
                        and row.get("gamma") in {1, 1.0, "1", "1.0"}
                    ]
                    reused_track_a = bool(matches)
                if not matches:
                    line.append(r"N/A --- not reproduced")
                else:
                    chosen = max(matches, key=lambda r: r["n_trials_completed"] or 0)
                    cell = _fmt_pct_tex(chosen[key_mean], chosen[key_std], chosen["n_trials_completed"])
                    if reused_track_a and dataset == "USPS":
                        cell = cell + r"\textsuperscript{$\dagger$}"
                    line.append(cell)
            body.append(line)
        _write_tex_tabular(REPORT_TABLES / filename, "lcccc", header, body)

    g_header, g_body_raw = table_gamma(rows)
    g_body = []
    for dataset, gamma, acc, nmi, n, run_id in g_body_raw:
        g_body.append(
            [
                dataset,
                _fmt_gamma_tex(float(gamma)),
                str(acc).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A"),
                str(nmi).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A"),
                str(n),
            ]
        )
    _write_tex_tabular(
        REPORT_TABLES / "sensitivity_gamma.tex",
        "lcccc",
        [r"Dataset", r"$\gamma$", r"ACC\%", r"NMI\%", r"$n$"],
        g_body,
    )

    conv_header = [r"Dataset", r"Method", r"$\gamma$", r"IRLS iter.", r"Converged", r"Eq.~(8)", r"$n$", r"sec."]
    conv_body = []
    selected = []
    for dataset in AVAILABLE:
        ssc_matches = [
            row
            for row in rows
            if row["method"] == "ssc"
            and row["dataset"] == dataset
            and row.get("gamma") in {1, 1.0, "1", "1.0"}
            and not row.get("perturbation")
            and str(row["track"]).upper() in {"TRACKA", "TRACKB", "EX1"}
        ]
        if ssc_matches:
            preferred = [row for row in ssc_matches if str(row["track"]).upper() == "TRACKA"] or ssc_matches
            selected.append(max(preferred, key=lambda r: r["n_trials_completed"] or 0))
        rssc_matches = [
            row
            for row in rows
            if row["method"] == "rssc"
            and row["dataset"] == dataset
            and not row.get("perturbation")
            and str(row["track"]).upper() == "EX1"
        ]
        if rssc_matches:
            selected.append(max(rssc_matches, key=lambda r: r["n_trials_completed"] or 0))
    for row in selected:
        hist = row.get("objective_history_text") or ""
        final_obj = "---"
        if hist:
            lines = [ln for ln in hist.strip().splitlines() if ln]
            if len(lines) >= 2 and "equation8_objective" in lines[0].split(","):
                keys = lines[0].split(",")
                last = lines[-1].split(",")
                try:
                    final_obj = f"{float(last[keys.index('equation8_objective')]):.3g}"
                except (ValueError, IndexError):
                    final_obj = "---"
        conv_body.append(
            [
                row["dataset"],
                METHOD_LABEL.get(row["method"], row["method"]),
                _fmt_gamma_tex(float(row["gamma"])) if row.get("gamma") is not None else "---",
                str(row.get("irls_iterations") if row.get("irls_iterations") is not None else "---"),
                r"yes" if row.get("irls_converged") else r"no",
                final_obj,
                str(row.get("n_trials_completed") or 0),
                f"{float(row['irls_seconds']):.2f}" if row.get("irls_seconds") is not None else "---",
            ]
        )
    _write_tex_tabular(REPORT_TABLES / "convergence.tex", "llcccccc", conv_header, conv_body)

    ext_header, ext_raw = table_ex1(rows)
    ext_body = []
    for dataset, a0a, a1a, a0n, a1n, n, _ids in ext_raw:
        ext_body.append(
            [
                dataset,
                str(a0a).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(a1a).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(a0n).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(a1n).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(n),
            ]
        )
    _write_tex_tabular(
        REPORT_TABLES / "extension_comparison.tex",
        "lccccc",
        [r"Dataset", r"A0 SSC ACC", r"A1 RSSC ACC", r"A0 SSC NMI", r"A1 RSSC NMI", r"$n$"],
        ext_body,
    )

    abl_header, abl_raw = table_k_and_ablation(rows)
    abl_body = []
    for dataset, k, a0a, a1a, a0n, a1n, n, _ids in abl_raw:
        abl_body.append(
            [
                dataset,
                str(k),
                str(a0a).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(a1a).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(a0n).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(a1n).replace(" ± ", r"$\pm$").replace("N/A — not reproduced", r"N/A --- not reproduced"),
                str(n),
            ]
        )
    _write_tex_tabular(
        REPORT_TABLES / "ablation.tex",
        "lcccccc",
        [r"Dataset", r"$k$", r"A0 SSC ACC", r"A1 RSSC ACC", r"A0 NMI", r"A1 NMI", r"$n$"],
        abl_body,
    )

    grouped: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for row in completed(rows):
        track = str(row["track"]).upper()
        if track not in {"EX2", "EX3", "EX4", "EX5"}:
            continue
        spec = row.get("perturbation") or {}
        key = (track, row["dataset"], spec.get("level"))
        grouped[key][row["method"]].append(row)
    rob_header = [r"Exp.", r"Dataset", r"Level", r"SSC ACC", r"RSSC ACC", r"seeds", r"$n$/seed"]
    rob_body = []
    for key in sorted(grouped, key=lambda t: (t[0], str(t[1]), float(t[2] or 0))):
        track, dataset, level = key
        pair = grouped[key]

        def _mean_cell(method: str) -> str:
            items = pair.get(method) or []
            accs = [r["acc_mean"] for r in items if r["acc_mean"] is not None]
            if not accs:
                return r"N/A --- not reproduced"
            mean = float(sum(accs) / len(accs))
            if len(accs) == 1:
                return _fmt_pct_tex(mean, None, items[0]["n_trials_completed"])
            var = sum((a - mean) ** 2 for a in accs) / (len(accs) - 1)
            return _fmt_pct_tex(mean, var**0.5, items[0]["n_trials_completed"])

        n_seed = min(len(pair.get("ssc") or []), len(pair.get("rssc") or []) or 10**9)
        n_per = min((r["n_trials_completed"] for r in (pair.get("ssc") or pair.get("rssc") or [])), default=0)
        rob_body.append(
            [
                track,
                dataset,
                f"{level}",
                _mean_cell("ssc"),
                _mean_cell("rssc"),
                str(n_seed if n_seed < 10**9 else max(len(pair.get("ssc") or []), len(pair.get("rssc") or []))),
                str(n_per),
            ]
        )
    _write_tex_tabular(REPORT_TABLES / "robustness.tex", "lllcccc", rob_header, rob_body)

    pending = REPORT_TABLES / "pending_from_runs.tex"
    pending.write_text(
        "\\begin{center}\n\\footnotesize\n"
        "\\textit{Filled from completed \\texttt{runs/} records by "
        "\\texttt{scripts/generate\\_report\\_tables.py}.}\n"
        "\\end{center}\n",
        encoding="utf-8",
    )


def counts_block(rows) -> dict[str, Any]:
    tallies = defaultdict(int)
    for row in rows:
        tallies[row["status"] or "UNKNOWN"] += 1
    return dict(tallies)


def main() -> int:
    rows = load_all_runs(RUNS)
    OUT.mkdir(parents=True, exist_ok=True)
    index_path = ROOT / "results" / "run_index.csv"
    _write_csv(
        index_path,
        ["run_id", "status", "track", "method", "dataset", "n_trials_completed", "n_trials_requested", "acc_mean", "nmi_mean", "gamma", "k", "n_components"],
        [
            [
                r["run_id"],
                r["status"],
                r["track"],
                r["method"],
                r["dataset"],
                r["n_trials_completed"],
                r["n_trials_requested"],
                r["acc_mean"],
                r["nmi_mean"],
                r["gamma"],
                r["k"],
                r["n_components"],
            ]
            for r in rows
        ],
    )

    caption_a = (
        "Track A is label-informed. "
        + SELECTION_RULE
        + " Paper percentages are copied from Chang et al. (2015) Tables 1–2 and are not our runs. "
        "Our values are 100× mean±std over completed trials of the selected setting. "
        "n is the actual completed trial count."
    )
    h1, b1 = table1_inventory(rows)
    _write_csv(OUT / "table1_datasets.csv", h1, b1)
    _write_md(OUT / "table1_datasets.md", "Table 1. Datasets", "Inventory of paper datasets and this reproduction.", h1, b1)

    h2, b2, ids2 = table_track_a(rows, "acc")
    _write_csv(OUT / "table2_track_a_acc.csv", h2, b2)
    _write_md(OUT / "table2_track_a_acc.md", "Table 2. Track A ACC%", caption_a, h2, b2)
    _write_csv(OUT / "table2_track_a_acc_run_ids.csv", h2, ids2)

    h3, b3, ids3 = table_track_a(rows, "nmi")
    _write_csv(OUT / "table3_track_a_nmi.csv", h3, b3)
    _write_md(OUT / "table3_track_a_nmi.md", "Table 3. Track A NMI%", caption_a, h3, b3)
    _write_csv(OUT / "table3_track_a_nmi_run_ids.csv", h3, ids3)

    h4, b4 = table_track_b(rows)
    cap4 = (
        "Track B: same data and preprocessing; gamma=1 a priori; DR dimension "
        "min(50, n_clusters, n-1, d), and K-1 for LDA. No labels for training or tuning. "
        "Separate from Track A. LDA-SC is APPROXIMATE and is omitted. SPLS is N/A — not reproduced."
    )
    _write_csv(OUT / "table4_track_b.csv", h4, b4)
    _write_md(OUT / "table4_track_b.md", "Table 4. Track B fair comparison", cap4, h4, b4)

    h5, b5 = table_ex1(rows)
    _write_csv(OUT / "table5_ex1_ssc_vs_rssc.csv", h5, b5)
    _write_md(
        OUT / "table5_ex1_ssc_vs_rssc.md",
        "Table 5. EX1 original SSC vs Reliability-aware SSC",
        "A0 = union kNN W. A1 = mutual kNN W. Same optimizer, gamma=1, k=5 unless noted.",
        h5,
        b5,
    )

    h6, b6 = table_robustness(rows)
    _write_csv(OUT / "table6_robustness.csv", h6, b6)
    _write_md(
        OUT / "table6_robustness.md",
        "Table 6. EX2–EX5 robustness",
        "EX2: isotropic Gaussian noise with sigma = {0.1, 0.3} × std(X). "
        "EX3: 10% of features replaced by N(0,1). EX4: 5% of samples replaced by N(0,10). "
        "EX5: drop 10% of shrinkage-graph edges. Negative results are kept.",
        h6,
        b6,
    )

    h7, b7 = table_k_and_ablation(rows)
    _write_csv(OUT / "table7_k_ablation.csv", h7, b7)
    _write_md(
        OUT / "table7_k_ablation.md",
        "Table 7. Ablation A0 vs A1 and neighborhood size",
        "EX6 k in {3,5,7,9}. A0 original SSC, A1 mutual kNN only.",
        h7,
        b7,
    )

    h8, b8 = table_runtime(rows)
    _write_csv(OUT / "table8_runtime_convergence.csv", h8, b8)
    _write_md(
        OUT / "table8_runtime_convergence.md",
        "Table 8. EX7–EX8 runtime and convergence",
        "IRLS wall time and iteration count from the actual solve. No decorative curves.",
        h8,
        b8,
    )

    hg, bg = table_gamma(rows)
    _write_csv(OUT / "table_gamma_sensitivity.csv", hg, bg)
    _write_md(
        OUT / "table_gamma_sensitivity.md",
        "Gamma sensitivity (Track A SSC)",
        "Track A SSC completed trials on the gamma grid. YaleB and USPS have only gamma=1.",
        hg,
        bg,
    )

    write_report_tex(rows)

    summary = {
        "n_run_directories": len(rows),
        "status_counts": counts_block(rows),
        "selection_rule": SELECTION_RULE,
        "lda_sc": "APPROXIMATE; omitted from the main faithful tables",
        "spls": "NOT_IMPLEMENTED; N/A — not reproduced",
    }
    (ROOT / "results" / "aggregation_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote tables under {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
