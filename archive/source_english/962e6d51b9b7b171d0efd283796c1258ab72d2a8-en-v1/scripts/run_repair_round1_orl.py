#!/usr/bin/env python3
"""ORL repair-round 1 one-factor diagnostics.

Writes configs to configs/repair_round1/ and runs to runs/repair_round1/.
Does not touch Phase 1 runs/, does not rewrite historical metrics, and
does not commit. Default SSC remains E13; E8 is an explicit variant.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aggregate import load_run
from experiments.protocol import GAMMA_GRID

PYTHON = sys.executable
RUNNER = ROOT / "scripts" / "run_experiment.py"
CONFIG_DIR = ROOT / "configs" / "repair_round1"
RUNS_DIR = ROOT / "runs" / "repair_round1"
RESULTS_DIR = ROOT / "results" / "repair_round1"

PILOT_N = 5
SHORTLIST_N = 50
SEED_START = 0
TIMEOUT = 1800
FIXED_DELTA2 = 1.0
PAPER_ORL_ACC = 76.0
PAPER_ORL_NMI = 88.6
V1_ORL_ACC = "53.9 ± 3.0"
V1_ORL_N = 50
V1_ORL_RUN = "20261020_015209__TRACKA__SSC__ORL__5f95ad90"
V1_ORL_GAMMA1_ACC = "53.7 ± 2.8"
V1_ORL_GAMMA1_RUN = "20261020_015212__TRACKA__SSC__ORL__0fe4a166"

A = "A_PAPER_FAITHFUL"
B = "B_AMBIGUITY"
C = "C_DIAGNOSTIC"


def _base_params(**overrides: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "k": 5,
        "gamma": 1.0,
        "max_iter": 300,
        "tol": 1e-6,
        "variant": "E13",
        "cluster_on": "G",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "row_normalize": False,
        "g_init": "F",
        "g_init_seed": 0,
        "g_init_scale": 1e-3,
        "zero_residual_floor": "median_pairwise",
        "kmeans_init": "random",
        "eps": 1e-8,
    }
    params.update(overrides)
    return params


def _job(
    factor: str,
    fidelity: str,
    notes: str,
    n_trials: int,
    params: dict[str, Any],
    dataset_version: str | None = None,
    covers: list[str] | None = None,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "track": "REPAIR1",
        "method": "ssc",
        "dataset": "ORL",
        "factor": factor,
        "paper_fidelity_category": fidelity,
        "n_trials": int(n_trials),
        "trial_seed_start": SEED_START,
        "timeout_seconds": TIMEOUT,
        "params": dict(params),
        "notes": notes,
        "label_informed_selection": False,
        "protocol": "R1_solve_FG_once_then_kmeans_seeds",
        "covers_factors": list(covers or [factor.split("_")[0]]),
    }
    if dataset_version is not None:
        config["dataset_version"] = dataset_version
    return config


def _slug(config: dict[str, Any]) -> str:
    params = config.get("params") or {}
    version = config.get("dataset_version") or "olivetti"
    parts = [
        str(config.get("factor")),
        str(params.get("variant")),
        str(params.get("gamma")),
        str(params.get("cluster_on")),
        str(params.get("max_iter")),
        str(params.get("kmeans_init")).replace("+", "p"),
        str(version),
        f"n{config.get('n_trials')}",
    ]
    slug = "__".join(parts)
    return slug.replace(".", "p").replace("-", "m")


def _write_config(config: dict[str, Any]) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"{_slug(config)}.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    return path


def _same_setting(existing: dict[str, Any], config: dict[str, Any]) -> bool:
    if existing.get("track") != config.get("track"):
        return False
    if existing.get("method") != config.get("method"):
        return False
    if existing.get("dataset") != config.get("dataset"):
        return False
    if existing.get("dataset_version") != config.get("dataset_version"):
        return False
    if existing.get("factor") != config.get("factor"):
        return False
    if (existing.get("params") or {}) != (config.get("params") or {}):
        return False
    if int(existing.get("n_trials") or 0) != int(config.get("n_trials") or 0):
        return False
    if int(existing.get("trial_seed_start") or 0) != int(config.get("trial_seed_start") or 0):
        return False
    return True


def _completed_match(config: dict[str, Any]) -> str | None:
    if not RUNS_DIR.is_dir():
        return None
    for child in sorted(RUNS_DIR.iterdir()):
        cfg_path = child / "config.yaml"
        status_path = child / "status.json"
        metrics_path = child / "metrics.json"
        if not (cfg_path.is_file() and status_path.is_file() and metrics_path.is_file()):
            continue
        try:
            existing = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            status = json.loads(status_path.read_text(encoding="utf-8"))
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if status.get("status") != "COMPLETED":
            continue
        if not _same_setting(existing, config):
            continue
        if int(metrics.get("n_trials_completed") or 0) < int(config.get("n_trials") or 0):
            continue
        return child.name
    return None


def _run_job(config: dict[str, Any]) -> dict[str, Any]:
    existing = _completed_match(config)
    if existing:
        print(f"SKIP already completed {existing}", flush=True)
        return {
            "config_path": "reused",
            "returncode": 0,
            "wall_seconds": 0.0,
            "reused_run_id": existing,
            "factor": config.get("factor"),
        }
    cfg_path = _write_config(config)
    timeout = int(config.get("timeout_seconds") or TIMEOUT) + 90
    print(f"\n=== launching {cfg_path.name} timeout={timeout}s ===", flush=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        [PYTHON, str(RUNNER), "--config", str(cfg_path), "--runs-dir", str(RUNS_DIR)],
        cwd=str(ROOT),
        capture_output=False,
        timeout=timeout,
        check=False,
    )
    elapsed = time.perf_counter() - t0
    print(
        f"=== finished {cfg_path.name} exit={proc.returncode} wall={elapsed:.1f}s ===",
        flush=True,
    )
    return {
        "config_path": str(cfg_path),
        "returncode": proc.returncode,
        "wall_seconds": elapsed,
        "factor": config.get("factor"),
    }


def _gamma_token(gamma: float) -> str:
    mapping = {
        1e-6: "1EM6",
        1e-3: "1EM3",
        1.0: "1",
        1e3: "1E3",
        1e6: "1E6",
    }
    if gamma in mapping:
        return mapping[gamma]
    return str(gamma).replace("-", "M").replace(".", "P")


def unique_pilot_configs() -> list[dict[str, Any]]:
    """One-factor unique settings. The Olivetti E13 gamma=1 baseline is not repeated."""
    jobs: list[dict[str, Any]] = []
    baseline_notes = (
        "Olivetti ORL, k=5, gamma=1, E13, union kNN, median positive kNN "
        "squared bandwidth, raw eigenvectors, G0=F, median_pairwise floor, "
        "max_iter=300, K-means random. Canonical reconstruction. Also covers "
        "D03-median, D04-union, D05-raw, D07-G0=F, D08-iter300, D09-random, "
        "D01-Olivetti."
    )
    jobs.append(
        _job(
            "D12_KMEANS_G_E13",
            B,
            baseline_notes,
            PILOT_N,
            _base_params(),
            dataset_version=None,
            covers=["D12", "D03", "D04", "D05", "D07", "D08", "D09", "D01"],
        )
    )
    jobs.append(
        _job(
            "D12_KMEANS_F",
            C,
            "K-means on raw spectral embedding F. Paper clusters G. Diagnostic pipeline attribution.",
            PILOT_N,
            _base_params(cluster_on="F"),
            covers=["D12"],
        )
    )
    jobs.append(
        _job(
            "D12_KMEANS_G_E8",
            A,
            "Same reconstruction as baseline; linear system A=S+2*gamma*Ltilde (printed Eq 8 stationary).",
            PILOT_N,
            _base_params(variant="E8"),
            covers=["D12"],
        )
    )
    jobs.append(
        _job(
            "D03_BW_MEAN",
            B,
            "One-factor bandwidth: mean kNN Euclidean distance squared, both X-graph and F-graph.",
            PILOT_N,
            _base_params(bandwidth_rule="mean_knn_distance_scale"),
            covers=["D03"],
        )
    )
    jobs.append(
        _job(
            "D03_BW_FIXED1",
            B,
            f"One-factor bandwidth: fixed global delta2={FIXED_DELTA2} on both X-graph and F-graph.",
            PILOT_N,
            _base_params(
                bandwidth_rule="fixed",
                delta2=FIXED_DELTA2,
                embedding_delta2=FIXED_DELTA2,
            ),
            covers=["D03"],
        )
    )
    jobs.append(
        _job(
            "D03_BW_SELFTUNE",
            C,
            "Zelnik-Manor self-tuning local scale. Cheap n=400 diagnostic, not the paper affinity.",
            PILOT_N,
            _base_params(bandwidth_rule="self_tuning_zelnik_manor"),
            covers=["D03"],
        )
    )
    jobs.append(
        _job(
            "D05_ROW_NORM",
            C,
            "Row-normalized eigenvectors before building W and shrinking. C_DIAGNOSTIC even if ACC is higher.",
            PILOT_N,
            _base_params(row_normalize=True),
            covers=["D05"],
        )
    )
    jobs.append(
        _job(
            "D07_G0_DET",
            B,
            "G0 = F + 1e-3 * deterministic cosine pattern. Epsilon not chosen by ACC.",
            PILOT_N,
            _base_params(g_init="deterministic_perturbation"),
            covers=["D07"],
        )
    )
    jobs.append(
        _job(
            "D07_G0_RAND",
            B,
            "G0 = fixed-seed standard normal, seed 0. Epsilon not chosen by ACC.",
            PILOT_N,
            _base_params(g_init="random"),
            covers=["D07"],
        )
    )
    jobs.append(
        _job(
            "D07_FLOOR_EPS",
            B,
            "zero_residual_floor=eps at the initial all-zero residual. Not selected by ACC.",
            PILOT_N,
            _base_params(zero_residual_floor="eps"),
            covers=["D07"],
        )
    )
    jobs.append(
        _job(
            "D08_ITER100",
            B,
            "Convergence budget max_iter=100, stop early on the existing relative Frobenius rule.",
            PILOT_N,
            _base_params(max_iter=100),
            covers=["D08"],
        )
    )
    jobs.append(
        _job(
            "D08_ITER1000",
            B,
            "Convergence budget max_iter=1000, stop early on the existing relative Frobenius rule.",
            PILOT_N,
            _base_params(max_iter=1000),
            covers=["D08"],
        )
    )
    jobs.append(
        _job(
            "D09_KM_PLUSPLUS",
            B,
            "K-means++ initialization. Historical protocol is random. Paper unspecified.",
            PILOT_N,
            _base_params(kmeans_init="k-means++"),
            covers=["D09"],
        )
    )
    for gamma in GAMMA_GRID:
        if float(gamma) == 1.0:
            continue
        token = _gamma_token(float(gamma))
        jobs.append(
            _job(
                f"GAMMA_E13_{token}",
                B,
                f"Paper gamma grid, E13, gamma={gamma}. Selection will not use raw SSC objectives.",
                PILOT_N,
                _base_params(gamma=float(gamma)),
                covers=["GAMMA"],
            )
        )
    for gamma in GAMMA_GRID:
        token = _gamma_token(float(gamma))
        if float(gamma) == 1.0:
            continue
        jobs.append(
            _job(
                f"GAMMA_E8_{token}",
                A,
                f"Paper gamma grid, E8, gamma={gamma}. Selection will not use raw SSC objectives.",
                PILOT_N,
                _base_params(variant="E8", gamma=float(gamma)),
                covers=["GAMMA"],
            )
        )
    jobs.append(
        _job(
            "D01_ATT92_E13",
            B,
            "AT&T 92x112 bilinear 32x32 vs Olivetti baseline. Interpolation unspecified in the paper.",
            PILOT_N,
            _base_params(),
            dataset_version="att92",
            covers=["D01", "D02"],
        )
    )
    jobs.append(
        _job(
            "D01_ATT92_E8",
            B,
            "AT&T 92x112 bilinear 32x32, E8, same k=5 gamma=1 reconstruction.",
            PILOT_N,
            _base_params(variant="E8"),
            dataset_version="att92",
            covers=["D01"],
        )
    )
    jobs.append(
        _job(
            "D02_ATT92_NEAREST",
            B,
            "AT&T 92x112 nearest-neighbor 32x32, E13 only. Interpolation is B_AMBIGUITY.",
            PILOT_N,
            _base_params(),
            dataset_version="att92_nearest",
            covers=["D02"],
        )
    )
    jobs.append(
        _job(
            "D02_ATT92_BICUBIC",
            B,
            "AT&T 92x112 bicubic 32x32, E13 only. Interpolation is B_AMBIGUITY.",
            PILOT_N,
            _base_params(),
            dataset_version="att92_bicubic",
            covers=["D02"],
        )
    )
    return jobs


def _pilot_row(factor: str) -> dict[str, Any] | None:
    if not RUNS_DIR.is_dir():
        return None
    matches = []
    for child in RUNS_DIR.iterdir():
        if not child.is_dir():
            continue
        row = load_run(child)
        if row is None:
            continue
        cfg = yaml.safe_load((child / "config.yaml").read_text(encoding="utf-8")) if (child / "config.yaml").is_file() else {}
        if cfg.get("factor") != factor:
            continue
        if int(cfg.get("n_trials") or 0) != PILOT_N:
            continue
        if row["status"] != "COMPLETED":
            continue
        matches.append(row)
    if not matches:
        return None
    return max(matches, key=lambda r: r.get("n_trials_completed") or 0)


def _acc(row: dict[str, Any] | None) -> float | None:
    if row is None:
        return None
    value = row.get("acc_mean")
    return None if value is None else float(value)


def _valid(row: dict[str, Any] | None) -> bool:
    if row is None:
        return False
    if row.get("status") != "COMPLETED":
        return False
    if int(row.get("n_trials_completed") or 0) < 1:
        return False
    acc = _acc(row)
    return acc is not None and 0.0 <= acc <= 1.0


def _moved(a: float | None, b: float | None, threshold: float = 0.03) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) >= threshold


def shortlist_configs() -> list[dict[str, Any]]:
    """n=50 only for a few valid configs. Gamma=1 is the paper-highlighted value."""
    jobs: list[dict[str, Any]] = []
    baseline = _pilot_row("D12_KMEANS_G_E13")
    e8 = _pilot_row("D12_KMEANS_G_E8")
    kmeans_f = _pilot_row("D12_KMEANS_F")
    att92 = _pilot_row("D01_ATT92_E13")
    plusplus = _pilot_row("D09_KM_PLUSPLUS")
    row_norm = _pilot_row("D05_ROW_NORM")
    iter1000 = _pilot_row("D08_ITER1000")
    bw_mean = _pilot_row("D03_BW_MEAN")
    bw_fixed = _pilot_row("D03_BW_FIXED1")
    bw_self = _pilot_row("D03_BW_SELFTUNE")

    if _valid(kmeans_f):
        jobs.append(
            _job(
                "D12_KMEANS_F",
                C,
                "n=50 R1 shortlist: K-means on F. Diagnostic.",
                SHORTLIST_N,
                _base_params(cluster_on="F"),
                covers=["D12"],
            )
        )
    if _valid(baseline):
        jobs.append(
            _job(
                "D12_KMEANS_G_E13",
                B,
                "n=50 R1 shortlist: gamma=1 E13 Olivetti. Not selected by SSC objective.",
                SHORTLIST_N,
                _base_params(),
                covers=["D12", "D01"],
            )
        )
    if _valid(e8):
        jobs.append(
            _job(
                "D12_KMEANS_G_E8",
                A,
                "n=50 R1 shortlist: gamma=1 E8 Olivetti. Not selected by SSC objective.",
                SHORTLIST_N,
                _base_params(variant="E8"),
                covers=["D12"],
            )
        )

    extras: list[dict[str, Any]] = []
    if _valid(att92) and _moved(_acc(att92), _acc(baseline)):
        extras.append(
            _job(
                "D01_ATT92_E13",
                B,
                "n=50 because att92 bilinear E13 changed ACC vs Olivetti E13 on the n=5 pilot.",
                SHORTLIST_N,
                _base_params(),
                dataset_version="att92",
                covers=["D01", "D02"],
            )
        )
    if _valid(plusplus) and _moved(_acc(plusplus), _acc(baseline)):
        extras.append(
            _job(
                "D09_KM_PLUSPLUS",
                B,
                "n=50 because k-means++ moved ACC vs random on the n=5 pilot.",
                SHORTLIST_N,
                _base_params(kmeans_init="k-means++"),
                covers=["D09"],
            )
        )
    if _valid(row_norm) and (
        (_acc(row_norm) or 0.0) >= 0.65 or _moved(_acc(row_norm), _acc(baseline), 0.05)
    ):
        extras.append(
            _job(
                "D05_ROW_NORM",
                C,
                "n=50 C_DIAGNOSTIC: row-normalized eigenvectors moved ACC. Not a paper-faithful claim.",
                SHORTLIST_N,
                _base_params(row_normalize=True),
                covers=["D05"],
            )
        )
    if _valid(iter1000) and _moved(_acc(iter1000), _acc(baseline)):
        extras.append(
            _job(
                "D08_ITER1000",
                B,
                "n=50 because max_iter=1000 moved ACC vs the unconverged 300-iter baseline.",
                SHORTLIST_N,
                _base_params(max_iter=1000),
                covers=["D08"],
            )
        )
    bandwidth_candidates = [
        ("D03_BW_MEAN", bw_mean, _base_params(bandwidth_rule="mean_knn_distance_scale"), B),
        (
            "D03_BW_FIXED1",
            bw_fixed,
            _base_params(
                bandwidth_rule="fixed",
                delta2=FIXED_DELTA2,
                embedding_delta2=FIXED_DELTA2,
            ),
            B,
        ),
        (
            "D03_BW_SELFTUNE",
            bw_self,
            _base_params(bandwidth_rule="self_tuning_zelnik_manor"),
            C,
        ),
    ]
    bandwidth_moved = [
        (name, row, params, fidelity)
        for name, row, params, fidelity in bandwidth_candidates
        if _valid(row) and _moved(_acc(row), _acc(baseline))
    ]
    if bandwidth_moved:
        name, _row, params, fidelity = max(
            bandwidth_moved, key=lambda item: abs((_acc(item[1]) or 0.0) - (_acc(baseline) or 0.0))
        )
        extras.append(
            _job(
                name,
                fidelity,
                "n=50 because this bandwidth rule moved ACC vs median on the n=5 pilot.",
                SHORTLIST_N,
                params,
                covers=["D03"],
            )
        )

    jobs.extend(extras[:3])
    return jobs


def _pct(mean: float | None, std: float | None, n: int | None) -> str:
    if mean is None:
        return "n/a"
    acc = 100.0 * float(mean)
    if std is None or n is None or n <= 1:
        return f"{acc:.1f} (n={n or 0})"
    return f"{acc:.1f} ± {100.0 * float(std):.1f} (n={n})"


def aggregate() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    if RUNS_DIR.is_dir():
        for child in sorted(RUNS_DIR.iterdir()):
            if child.is_dir():
                loaded = load_run(child)
                if loaded is not None:
                    rows.append(loaded)

    registry_header = [
        "run_id",
        "status",
        "factor",
        "variant",
        "paper_fidelity_category",
        "dataset",
        "dataset_version",
        "dataset_checksum",
        "gamma",
        "k",
        "cluster_on",
        "n_trials_requested",
        "n_trials_completed",
        "trial_seed_start",
        "acc_mean",
        "acc_std",
        "nmi_mean",
        "nmi_std",
        "acc_pct",
        "nmi_pct",
        "irls_converged",
        "n_irls_iterations",
        "fixed_point_residual",
        "equation8_objective",
        "g_minus_f_frobenius",
        "label_disagreement_mean",
        "n_connected_components",
        "n_undirected_edges",
        "w_edge_jaccard_vs_X",
        "w_identical_to_X_graph",
        "bandwidth_rule",
        "row_normalize",
        "g0",
        "zero_residual_floor",
        "max_iter",
        "kmeans_init",
        "notes",
    ]
    registry_rows: list[list[Any]] = []
    gap_header = [
        "factor",
        "variant",
        "paper_fidelity_category",
        "dataset_version",
        "n_trials",
        "acc_mean_pct",
        "acc_std_pct",
        "nmi_mean_pct",
        "nmi_std_pct",
        "acc_display",
        "nmi_display",
        "paper_acc_pct",
        "paper_nmi_pct",
        "v1_previous_acc",
        "v1_previous_n",
        "v1_previous_run_id",
        "acc_gap_vs_paper_pp",
        "acc_gap_vs_v1_pp",
        "irls_converged",
        "approached_76pct",
        "run_id",
        "notes",
    ]
    gap_rows: list[list[Any]] = []
    for row in rows:
        if row.get("dataset") not in (None, "ORL"):
            continue
        metrics = row.get("metrics") or {}
        metadata = row.get("metadata") or {}
        params = row.get("params") or {}
        cfg_path = Path(row["run_dir"]) / "config.yaml"
        config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
        data_meta = metrics.get("dataset_metadata") or {}
        trials = metrics.get("trials") or []
        disagreements = [
            t.get("label_disagreement_F_G")
            for t in trials
            if t.get("label_disagreement_F_G") is not None
        ]
        disagreement_mean = (
            float(sum(disagreements) / len(disagreements)) if disagreements else None
        )
        graph_stats = metrics.get("shrinkage_graph_stats") or {}
        overlap = metrics.get("w_vs_x_overlap") or {}
        n_completed = int(row.get("n_trials_completed") or 0)
        acc_mean = row.get("acc_mean")
        acc_std = row.get("acc_std")
        nmi_mean = row.get("nmi_mean")
        nmi_std = row.get("nmi_std")
        fidelity = (
            config.get("paper_fidelity_category")
            or metadata.get("paper_fidelity_category")
            or metrics.get("paper_fidelity_category")
        )
        version = config.get("dataset_version") or "olivetti"
        checksum = metrics.get("dataset_checksum") or data_meta.get("SHA256_checksum")
        registry_rows.append(
            [
                row.get("run_id"),
                row.get("status"),
                config.get("factor"),
                params.get("variant") or metrics.get("variant"),
                fidelity,
                row.get("dataset"),
                version,
                checksum,
                params.get("gamma"),
                params.get("k"),
                params.get("cluster_on") or metrics.get("cluster_on"),
                config.get("n_trials"),
                n_completed,
                config.get("trial_seed_start"),
                acc_mean,
                acc_std,
                nmi_mean,
                nmi_std,
                _pct(acc_mean, acc_std, n_completed),
                _pct(nmi_mean, nmi_std, n_completed),
                metrics.get("irls_converged"),
                metrics.get("n_irls_iterations"),
                metrics.get("fixed_point_residual"),
                metrics.get("equation8_objective"),
                metrics.get("g_minus_f_frobenius"),
                disagreement_mean,
                graph_stats.get("n_connected_components"),
                graph_stats.get("n_undirected_edges"),
                overlap.get("edge_jaccard"),
                overlap.get("identical_to_x_graph"),
                params.get("bandwidth_rule") or metrics.get("bandwidth_rule"),
                params.get("row_normalize"),
                metrics.get("g0"),
                params.get("zero_residual_floor"),
                params.get("max_iter"),
                params.get("kmeans_init"),
                config.get("notes"),
            ]
        )
        if row.get("status") == "COMPLETED" and acc_mean is not None:
            acc_pct = 100.0 * float(acc_mean)
            nmi_pct = None if nmi_mean is None else 100.0 * float(nmi_mean)
            gap_paper = acc_pct - PAPER_ORL_ACC
            gap_v1 = acc_pct - 53.9
            gap_rows.append(
                [
                    config.get("factor"),
                    params.get("variant") or metrics.get("variant"),
                    fidelity,
                    version,
                    n_completed,
                    acc_pct,
                    None if acc_std is None else 100.0 * float(acc_std),
                    nmi_pct,
                    None if nmi_std is None else 100.0 * float(nmi_std),
                    _pct(acc_mean, acc_std, n_completed),
                    _pct(nmi_mean, nmi_std, n_completed),
                    PAPER_ORL_ACC,
                    PAPER_ORL_NMI,
                    V1_ORL_ACC,
                    V1_ORL_N,
                    V1_ORL_RUN,
                    gap_paper,
                    gap_v1,
                    metrics.get("irls_converged"),
                    bool(acc_pct >= 70.0),
                    row.get("run_id"),
                    config.get("notes"),
                ]
            )

    registry_path = RESULTS_DIR / "experiment_registry.csv"
    write_header = not registry_path.is_file()
    existing_ids = set()
    if registry_path.is_file():
        with registry_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for old in reader:
                existing_ids.add(old.get("run_id"))
    with registry_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if write_header:
            writer.writerow(registry_header)
        for item in registry_rows:
            if item[0] in existing_ids:
                continue
            writer.writerow(item)
            existing_ids.add(item[0])

    gap_path = RESULTS_DIR / "paper_gap_analysis.csv"
    write_gap_header = not gap_path.is_file()
    existing_gap_ids: set[str] = set()
    if gap_path.is_file():
        with gap_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for old in reader:
                rid = old.get("run_id")
                if rid:
                    existing_gap_ids.add(rid)
    with gap_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if write_gap_header:
            writer.writerow(gap_header)
        for item in gap_rows:
            run_id = item[-2]
            if run_id in existing_gap_ids:
                continue
            writer.writerow(item)
            existing_gap_ids.add(run_id)

    summary = {
        "n_runs": len(rows),
        "n_completed": sum(1 for r in rows if r.get("status") == "COMPLETED"),
        "paper_orl_acc_pct": PAPER_ORL_ACC,
        "paper_orl_nmi_pct": PAPER_ORL_NMI,
        "v1_previous_acc": V1_ORL_ACC,
        "v1_previous_run_id": V1_ORL_RUN,
        "v1_gamma1_acc": V1_ORL_GAMMA1_ACC,
        "v1_gamma1_run_id": V1_ORL_GAMMA1_RUN,
        "registry": str(registry_path),
        "gap_table": str(gap_path),
        "note": "Paper numbers are reported, not copied as ours. All ACC/NMI are from actual runs.",
    }
    (RESULTS_DIR / "aggregation_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {registry_path} ({len(registry_rows)} rows scanned)", flush=True)
    print(f"wrote {gap_path} ({len(gap_rows)} completed rows)", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ORL repair-round 1 one-factor diagnostics.")
    parser.add_argument("--stage", choices=("pilots", "shortlist", "aggregate", "all"), default="all")
    args = parser.parse_args(argv)

    os.environ.setdefault("OMP_NUM_THREADS", "8")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
    os.environ.setdefault("MKL_NUM_THREADS", "8")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "8")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.stage in {"pilots", "all"}:
        for config in unique_pilot_configs():
            _write_config(config)
            result = _run_job(config)
            if result.get("returncode") not in (0, None) and not result.get("reused_run_id"):
                print(f"WARNING non-zero exit for {config.get('factor')}", flush=True)
        aggregate()
    if args.stage in {"shortlist", "all"}:
        chosen = shortlist_configs()
        print(f"shortlist size={len(chosen)}", flush=True)
        for config in chosen:
            _write_config(config)
            result = _run_job(config)
            if result.get("returncode") not in (0, None) and not result.get("reused_run_id"):
                print(f"WARNING non-zero exit for {config.get('factor')}", flush=True)
        aggregate()
    if args.stage == "aggregate":
        aggregate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
