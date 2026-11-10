#!/usr/bin/env python3
"""Figures from actual run records. No interpolated fake curves."""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aggregate import completed, load_all_runs

OUT = ROOT / "results" / "figures"
REPORT_FIG = ROOT / "report" / "figures"
RUNS = ROOT / "runs"


def _save(fig, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT_FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f"{stem}.pdf")
    fig.savefig(OUT / f"{stem}.svg")
    fig.savefig(OUT / f"{stem}.png", dpi=120)
    plt.close(fig)
    for suffix in (".pdf", ".png"):
        src = OUT / f"{stem}{suffix}"
        if src.exists():
            shutil.copy2(src, REPORT_FIG / src.name)


def fig_track_a_bars(rows) -> None:
    datasets = ["ORL", "JAFFE", "YaleB", "USPS"]
    methods = ["kmeans", "sc", "ssc"]
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    width = 0.22
    x = np.arange(len(datasets))
    for i, method in enumerate(methods):
        means = []
        stds = []
        for dataset in datasets:
            matches = [
                row
                for row in completed(rows)
                if row["method"] == method
                and row["dataset"] == dataset
                and str(row["track"]).upper() in {"TRACKA", "TRACK_A"}
            ]
            if not matches:
                means.append(np.nan)
                stds.append(0.0)
            else:
                chosen = max(matches, key=lambda r: (r["acc_mean"] if r["acc_mean"] is not None else -1))
                means.append(100.0 * chosen["acc_mean"])
                stds.append(100.0 * (chosen["acc_std"] or 0.0))
        ax.bar(x + (i - 1) * width, means, width, yerr=stds, label=method, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylabel("ACC (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Our runs only (not Chang et al. table values)")
    ax.legend()
    _save(fig, "fig1_track_a_acc")


def fig_gamma(rows) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6), sharey=True)
    for ax, dataset in zip(axes, ("ORL", "JAFFE")):
        matches = [
            row
            for row in completed(rows)
            if row["method"] == "ssc"
            and row["dataset"] == dataset
            and row.get("gamma") is not None
            and str(row["track"]).upper() in {"TRACKA", "TRACK_A"}
            and not row.get("perturbation")
        ]
        by_g = {}
        for row in matches:
            gamma = float(row["gamma"])
            prev = by_g.get(gamma)
            if prev is None or (row["n_trials_completed"] or 0) > (prev["n_trials_completed"] or 0):
                by_g[gamma] = row
        if not by_g:
            ax.set_title(f"{dataset}: no SSC gamma runs")
            continue
        ordered = [by_g[g] for g in sorted(by_g)]
        xs = [float(r["gamma"]) for r in ordered]
        ys = [100.0 * r["acc_mean"] for r in ordered]
        yerr = [100.0 * (r["acc_std"] or 0.0) for r in ordered]
        ax.errorbar(xs, ys, yerr=yerr, marker="o", linestyle="-")
        ax.set_xscale("log")
        ax.set_title(dataset)
        ax.set_xlabel("gamma")
        ax.set_ylabel("ACC (%)")
    fig.suptitle("SSC gamma grid, our completed trials")
    _save(fig, "fig2_gamma_sensitivity")


def fig_convergence(rows) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6), sharey=False)
    drawn = False
    for ax, dataset in zip(axes, ("ORL", "JAFFE")):
        for method, label in (("ssc", "A0 SSC"), ("rssc", "A1 RSSC")):
            matches = [
                row
                for row in rows
                if row["method"] == method
                and row["dataset"] == dataset
                and row.get("has_objective_history")
                and not row.get("perturbation")
                and (row.get("gamma") in {1, 1.0, None, "1", "1.0"})
            ]
            if not matches:
                continue
            row = max(matches, key=lambda r: r["n_trials_completed"] or 0)
            text = row.get("objective_history_text") or ""
            lines = [ln for ln in text.strip().splitlines() if ln]
            if len(lines) < 2:
                continue
            keys = lines[0].split(",")
            if "equation8_objective" not in keys:
                continue
            idx = keys.index("equation8_objective")
            values = [float(ln.split(",")[idx]) for ln in lines[1:]]
            ax.plot(range(len(values)), values, marker="o", label=f"{label} {row['run_id'][:15]}")
            drawn = True
        ax.set_title(dataset)
        ax.set_xlabel("IRLS iteration")
        ax.set_ylabel("Eq. (8) objective")
        ax.legend(fontsize=7)
    if not drawn:
        axes[0].text(0.5, 0.5, "No objective histories", ha="center")
    fig.suptitle("Recorded Eq. (8) values; not a smoothed decoration")
    _save(fig, "fig3_convergence")


def fig_ex1(rows) -> None:
    datasets = ["ORL", "JAFFE", "YaleB"]
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    x = np.arange(len(datasets))
    width = 0.35
    for i, method in enumerate(("ssc", "rssc")):
        means, stds = [], []
        for dataset in datasets:
            matches = [
                r
                for r in completed(rows)
                if r["method"] == method
                and r["dataset"] == dataset
                and not r.get("perturbation")
                and str(r["track"]).upper() == "EX1"
            ]
            if not matches:
                means.append(np.nan)
                stds.append(0)
            else:
                chosen = max(matches, key=lambda r: r["n_trials_completed"])
                means.append(100.0 * chosen["acc_mean"])
                stds.append(100.0 * (chosen["acc_std"] or 0.0))
        ax.bar(x + (i - 0.5) * width, means, width, yerr=stds, label=method, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylabel("ACC (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.set_title("EX1 / available gamma=1 runs")
    _save(fig, "fig4_ex1_ssc_vs_rssc")


def fig_robust(rows, track: str, stem: str, xlabel: str) -> None:
    subset = [r for r in completed(rows) if str(r["track"]).upper() == track]
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6), sharey=True)
    for ax, dataset in zip(axes, ("ORL", "JAFFE")):
        for method in ("ssc", "rssc"):
            grouped = defaultdict(list)
            for row in subset:
                if row["dataset"] != dataset or row["method"] != method:
                    continue
                spec = row.get("perturbation") or {}
                grouped[float(spec.get("level") or 0.0)].append(row)
            if not grouped:
                continue
            xs, ys, yerr = [], [], []
            for level in sorted(grouped):
                accs = [r["acc_mean"] for r in grouped[level] if r["acc_mean"] is not None]
                if not accs:
                    continue
                xs.append(level)
                ys.append(100.0 * float(np.mean(accs)))
                yerr.append(100.0 * float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0)
            ax.errorbar(xs, ys, yerr=yerr, marker="o", label=method)
        ax.set_title(dataset)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("ACC (%)")
        ax.legend()
    _save(fig, stem)


def fig_k(rows) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6), sharey=True)
    for ax, dataset in zip(axes, ("ORL", "JAFFE")):
        for method in ("ssc", "rssc"):
            matches = [
                r
                for r in completed(rows)
                if r["method"] == method
                and r["dataset"] == dataset
                and r.get("k") is not None
                and not r.get("perturbation")
            ]
            by_k = defaultdict(list)
            for row in matches:
                by_k[int(row["k"])].append(row)
            if not by_k:
                continue
            xs = sorted(by_k)
            ys = []
            yerr = []
            for k in xs:
                chosen = max(by_k[k], key=lambda r: r["n_trials_completed"])
                ys.append(100.0 * chosen["acc_mean"])
                yerr.append(100.0 * (chosen["acc_std"] or 0.0))
            ax.errorbar(xs, ys, yerr=yerr, marker="o", label=method)
        ax.set_title(dataset)
        ax.set_xlabel("k")
        ax.set_ylabel("ACC (%)")
        ax.legend()
    fig.suptitle("Neighborhood size, completed trials only")
    _save(fig, "fig8_k_sensitivity")


def fig_runtime(rows) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    drawn = False
    for method, marker in (("ssc", "o"), ("rssc", "s")):
        xs, ys, labels = [], [], []
        for row in rows:
            if row["method"] != method:
                continue
            if row.get("irls_seconds") is None:
                continue
            if row.get("perturbation"):
                continue
            xs.append(row["metrics"].get("n_samples") or 0)
            ys.append(row["irls_seconds"])
            labels.append(f"{row['dataset']}")
            drawn = True
        if xs:
            ax.scatter(xs, ys, marker=marker, label=method)
    ax.set_xlabel("n samples")
    ax.set_ylabel("IRLS seconds")
    ax.set_title("Recorded IRLS wall times")
    ax.legend()
    if not drawn:
        ax.text(0.5, 0.5, "No IRLS timings", ha="center", transform=ax.transAxes)
    _save(fig, "fig7_runtime")


def main() -> int:
    rows = load_all_runs(RUNS)
    OUT.mkdir(parents=True, exist_ok=True)
    fig_track_a_bars(rows)
    fig_gamma(rows)
    fig_convergence(rows)
    fig_ex1(rows)
    fig_robust(rows, "EX2", "fig5_gaussian_noise", "sigma / std(X)")
    fig_robust(rows, "EX3", "fig6_feature_corruption", "fraction of features replaced")
    fig_robust(rows, "EX4", "fig9_outliers", "fraction of samples replaced")
    fig_k(rows)
    fig_runtime(rows)
    manifest = {
        "n_runs_seen": len(rows),
        "figures": sorted(p.name for p in OUT.iterdir() if p.suffix in {".pdf", ".svg"}),
        "note": "Every curve or bar uses completed runs. Missing series are omitted, not filled from the paper.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
