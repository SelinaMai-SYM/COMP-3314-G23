#!/usr/bin/env python3
"""COMP3314 Task 2 strict reproduction campaign.

Writes configs to configs/strict_repro/, runs to runs/strict_repro/,
and matrices to results/strict_repro/ plus results/reproduction_full_matrix.*.
Does not touch method_extension/, report/, runs/, runs/repair_round1/, or
runs/round2/. Does not select gamma, dimension, or seed by ACC.
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

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aggregate import load_all_runs
from experiments.paper_reported import ACC as PAPER_ACC
from experiments.paper_reported import DATASETS as PAPER_DATASETS
from experiments.paper_reported import METHODS as PAPER_METHODS
from experiments.paper_reported import NMI as PAPER_NMI
from experiments.protocol import GAMMA_GRID, dimension_grid, track_b_dimension

PYTHON = sys.executable
RUNNER = ROOT / "scripts" / "run_experiment.py"
CONFIG_DIR = ROOT / "configs" / "strict_repro"
RUNS_DIR = ROOT / "runs" / "strict_repro"
RESULTS_DIR = ROOT / "results" / "strict_repro"
MATRIX_CSV = ROOT / "results" / "reproduction_full_matrix.csv"
MATRIX_MD = ROOT / "results" / "reproduction_full_matrix.md"
COMPLETION_MD = ROOT / "docs" / "task2_experiment_completion.md"

PILOT_N = 3
ORL_JAFFE_N = 50
YALEB_N = 10
USPS_CORE_N = 5
USPS_DR_N = 3
EXTRA_N = 3
LDASC_N = 10
SEED_START = 0

TIMEOUT_SMALL = 1800
TIMEOUT_YALEB = 3600
TIMEOUT_USPS = 3600
TIMEOUT_USPS_LLC = 7200

A = "A_PAPER_FAITHFUL"
B = "B_AMBIGUITY"
C = "C_DIAGNOSTIC"

SHAPES = {
    "ORL": (400, 1024, 40),
    "JAFFE": (213, 676, 10),
    "YaleB": (2414, 1024, 38),
    "USPS": (9298, 256, 10),
    "UMIST": (575, 10304, 20),
    "BinAlpha": (780, 320, 26),
}

IDENTITY = {
    ("ORL", "att92"): "original_source_att92_92x112_bilinear_32x32",
    ("JAFFE", "zenodo"): "verified_zenodo_213_not_paper_unpublished_copy",
    ("YaleB", "cropped2414"): "obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai",
    ("USPS", "libsvm"): "verified_libsvm_9298",
    ("AR", None): "BLOCKED_DATA_official_unavailable_zenodo_not_used",
    ("MSRA50", None): "BLOCKED_DATA_no_1799x12_archive",
    ("UMIST", None): "BLOCKED_DATA_paper_564_not_obtained",
    ("UMIST", "precropped575"): "not_paper_564_precropped575_n575_unique_pixels_565",
    ("BinAlpha", None): "BLOCKED_DATA_paper_26x30_not_identified",
    ("BinAlpha", "letters26x30_seed0"): "UNVERIFIED_reconstruction_letters26x30_seed0_not_COMPLETE_VERIFIED",
}

FAITHFUL_DATASETS = (
    ("ORL", "att92"),
    ("JAFFE", "zenodo"),
    ("YaleB", "cropped2414"),
    ("USPS", "libsvm"),
)
BLOCKED_DATASETS = ("AR", "MSRA50", "UMIST", "BinAlpha")
DISPLAY_METHOD = {
    "kmeans": "K-means",
    "sc": "SC",
    "pca_kmeans": "PCA-KM",
    "pca_spectral": "PCA-SC",
    "lda_kmeans": "LDA-KM",
    "lda_spectral": "LDA-SC",
    "llc": "LLC",
    "spls": "SPLS",
    "ssc": "SSC E8",
}

SELECTION_RULE = (
    "prespecified; mean±std over ALL completed trials; "
    "K-means init=random n_init=1 at protocol layer; "
    "gamma=1 for SSC matrix cells (full grid recorded, not compared by ACC "
    "or by raw Eq.8 objectives across gamma); "
    "PCA dim=min(50,K,n-1,d) assumption not ACC; "
    "LDA dim=K-1 (Ding–Li), grid clipped, not ACC; "
    "no seed selected by ACC; best inertia recorded separately when present"
)

for _key in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_key, "8")


def sc_params(**overrides: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "k": 5,
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "symmetrization": "union",
        "row_normalize": False,
        "laplacian": "symmetric_normalized_eq4",
        "kmeans_init": "random",
        "n_init": 1,
    }
    params.update(overrides)
    return params


def ssc_params(**overrides: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "k": 5,
        "gamma": 1.0,
        "max_iter": 300,
        "tol": 1e-6,
        "variant": "E8",
        "cluster_on": "G",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "row_normalize": False,
        "g_init": "F",
        "g_init_seed": 0,
        "g_init_scale": 1e-3,
        "zero_residual_floor": "median_pairwise",
        "kmeans_init": "random",
        "n_init": 1,
        "eps": 1e-8,
        "symmetrization": "union",
        "laplacian": "symmetric_normalized_eq4",
    }
    params.update(overrides)
    return params


def _gamma_token(value: float) -> str:
    mapping = {1e-6: "1em6", 1e-3: "1em3", 1.0: "1p0", 1e3: "1e3", 1e6: "1e6"}
    if value in mapping:
        return mapping[value]
    return str(value).replace(".", "p").replace("-", "m")


def _timeout_for(dataset: str, method: str) -> int:
    if dataset == "USPS" and method == "llc":
        return TIMEOUT_USPS_LLC
    if dataset == "USPS":
        return TIMEOUT_USPS
    if dataset == "YaleB":
        return TIMEOUT_YALEB
    return TIMEOUT_SMALL


def _job(
    *,
    method: str,
    dataset: str,
    factor: str,
    fidelity: str,
    notes: str,
    n_trials: int,
    params: dict[str, Any] | None = None,
    dataset_version: str | None,
    phase: str,
    timeout: int | None = None,
) -> dict[str, Any]:
    identity = IDENTITY.get((dataset, dataset_version), "unspecified")
    return {
        "track": "STRICT_REPRO",
        "method": method,
        "dataset": dataset,
        "dataset_version": dataset_version,
        "dataset_identity_status": identity,
        "factor": factor,
        "paper_fidelity_category": fidelity,
        "n_trials": int(n_trials),
        "trial_seed_start": SEED_START,
        "timeout_seconds": int(timeout if timeout is not None else _timeout_for(dataset, method)),
        "params": dict(params or {}),
        "notes": notes,
        "label_informed_selection": False,
        "protocol": "strict_repro_no_ACC_selection",
        "hardware_note": "8 CPU / 16 GB",
        "phase": phase,
    }


def _slug(config: dict[str, Any]) -> str:
    params = config.get("params") or {}
    parts = [
        str(config.get("dataset")),
        str(config.get("method")),
        str(config.get("factor")),
        str(params.get("variant") or "NA"),
        _gamma_token(float(params["gamma"])) if params.get("gamma") is not None else "NA",
        str(params.get("n_components") if params.get("n_components") is not None else "NA"),
        str(config.get("dataset_version") or "default"),
        f"n{config.get('n_trials')}",
    ]
    return "__".join(parts).replace(".", "p").replace("-", "m")


def _write_config(config: dict[str, Any]) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"{_slug(config)}.yaml"
    payload = {k: v for k, v in config.items() if k != "phase"}
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)
    return path


def _same_setting(existing: dict[str, Any], config: dict[str, Any]) -> bool:
    keys = (
        "track",
        "method",
        "dataset",
        "dataset_version",
        "factor",
        "n_trials",
        "trial_seed_start",
    )
    for key in keys:
        if existing.get(key) != config.get(key):
            return False
    return (existing.get("params") or {}) == (config.get("params") or {})


def _completed_match(config: dict[str, Any]) -> str | None:
    if not RUNS_DIR.is_dir():
        return None
    payload = {k: v for k, v in config.items() if k != "phase"}
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
        if not _same_setting(existing, payload):
            continue
        requested = int(config.get("n_trials") or 0)
        completed = int(metrics.get("n_trials_completed") or 0)
        if status.get("status") == "COMPLETED" and completed >= requested:
            return child.name
        if status.get("status") == "SKIPPED":
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
            "phase": config.get("phase"),
            "status": "reused",
        }
    cfg_path = _write_config(config)
    timeout = int(config.get("timeout_seconds") or 600) + 90
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
        "phase": config.get("phase"),
        "status": "launched",
    }


def pca_dim(dataset: str) -> int:
    n, d, k = SHAPES[dataset]
    return track_b_dimension(n, d, k, lda=False)


def lda_dim(dataset: str) -> int:
    n, d, k = SHAPES[dataset]
    return track_b_dimension(n, d, k, lda=True)


def build_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []

    jobs.append(
        _job(
            method="spls",
            dataset="ORL",
            factor="SPLS_NOT_IMPLEMENTED",
            fidelity=C,
            notes="SPLS Section 3 not obtained; fit_predict raises NotImplementedError; no substitute numbers.",
            n_trials=1,
            params={},
            dataset_version="att92",
            phase="P0_probes",
            timeout=60,
        )
    )
    for dataset in BLOCKED_DATASETS:
        jobs.append(
            _job(
                method="kmeans",
                dataset=dataset,
                factor="BLOCKED_DATA_PROBE",
                fidelity=A,
                notes="Paper sample set unavailable. Loader must raise DatasetUnavailable. Not a substitute subset.",
                n_trials=1,
                params={"init": "random", "n_init": 1},
                dataset_version=None,
                phase="P0_probes",
                timeout=60,
            )
        )

    orl_pilot_specs = [
        ("kmeans", "KMEANS", {"init": "random", "n_init": 1}, A, "K-means random n_init=1"),
        ("sc", "SC_EQ4", sc_params(), A, "SC Eq4 k=5 shared SpectralGraphConfig"),
        ("ssc", "SSC_E8_G1", ssc_params(variant="E8", gamma=1.0), A, "SSC E8 A=S+2gamma Ltilde gamma=1"),
        ("ssc", "SSC_E13_G1", ssc_params(variant="E13", gamma=1.0), B, "SSC E13 printed update A=S+gamma Ltilde gamma=1"),
        ("pca_kmeans", "PCAKM_PRE", {"n_components": pca_dim("ORL"), "init": "random", "n_init": 1}, A, "PCA-KM prespecified dim, not ACC"),
        ("pca_spectral", "PCASC_PRE", {**sc_params(), "n_components": pca_dim("ORL")}, A, "PCA-SC prespecified dim, not ACC"),
        ("lda_kmeans", "LDAKM_Km1", {"n_components": lda_dim("ORL"), "init": "random", "n_init": 1}, A, "LDA-KM dim=K-1 Ding-Li"),
        ("llc", "LLC", {"k": 5}, A, "LLC k=5 Yu-Shi discretization"),
    ]
    for method, factor, params, fidelity, notes in orl_pilot_specs:
        jobs.append(
            _job(
                method=method,
                dataset="ORL",
                factor=f"PILOT_{factor}",
                fidelity=fidelity,
                notes=f"ORL att92 pilot n={PILOT_N}. {notes}",
                n_trials=PILOT_N,
                params=params,
                dataset_version="att92",
                phase="P1_orl_pilots",
            )
        )

    for dataset, version, n_full, phase in (
        ("ORL", "att92", ORL_JAFFE_N, "P2_orl_priority"),
        ("JAFFE", "zenodo", ORL_JAFFE_N, "P3_jaffe_priority"),
        ("YaleB", "cropped2414", YALEB_N, "P6_yaleb"),
        ("USPS", "libsvm", USPS_CORE_N, "P7_usps"),
    ):
        core = [
            ("kmeans", "KMEANS", {"init": "random", "n_init": 1}, A, "K-means random n_init=1; all trials kept"),
            ("sc", "SC_EQ4", sc_params(), A, "SC Eq4 k=5 shared F path"),
            ("ssc", "SSC_E8_G1", ssc_params(variant="E8", gamma=1.0), A, "SSC E8 faithful stationarity gamma=1"),
            ("ssc", "SSC_E13_G1", ssc_params(variant="E13", gamma=1.0), B, "SSC E13 printed Eq13 gamma=1; separate column"),
        ]
        for method, factor, params, fidelity, notes in core:
            jobs.append(
                _job(
                    method=method,
                    dataset=dataset,
                    factor=factor,
                    fidelity=fidelity,
                    notes=notes,
                    n_trials=n_full,
                    params=params,
                    dataset_version=version,
                    phase=phase,
                )
            )

    for dataset, version, n_full, phase in (
        ("ORL", "att92", ORL_JAFFE_N, "P4_orl_dr"),
        ("JAFFE", "zenodo", ORL_JAFFE_N, "P5_jaffe_dr"),
        ("YaleB", "cropped2414", YALEB_N, "P6_yaleb"),
        ("USPS", "libsvm", USPS_DR_N, "P7_usps"),
    ):
        dr = [
            (
                "pca_kmeans",
                f"PCAKM_D{pca_dim(dataset)}",
                {"n_components": pca_dim(dataset), "init": "random", "n_init": 1},
                A,
                f"PCA-KM prespecified dim={pca_dim(dataset)}; not selected by ACC",
            ),
            (
                "pca_spectral",
                f"PCASC_D{pca_dim(dataset)}",
                {**sc_params(), "n_components": pca_dim(dataset)},
                A,
                f"PCA-SC prespecified dim={pca_dim(dataset)}; not selected by ACC",
            ),
            (
                "lda_kmeans",
                f"LDAKM_D{lda_dim(dataset)}",
                {"n_components": lda_dim(dataset), "init": "random", "n_init": 1},
                A,
                f"LDA-KM dim={lda_dim(dataset)}=K-1; cannot search 150",
            ),
            ("llc", "LLC", {"k": 5}, A, "LLC k=5"),
        ]
        for method, factor, params, fidelity, notes in dr:
            jobs.append(
                _job(
                    method=method,
                    dataset=dataset,
                    factor=factor,
                    fidelity=fidelity,
                    notes=notes,
                    n_trials=n_full,
                    params=params,
                    dataset_version=version,
                    phase=phase,
                )
            )

    n, d, _k = SHAPES["ORL"]
    for dim in dimension_grid(n, d):
        if dim == pca_dim("ORL"):
            continue
        jobs.append(
            _job(
                method="pca_kmeans",
                dataset="ORL",
                factor=f"PCAKM_GRID_D{dim}",
                fidelity=B,
                notes="PCA dim grid {10..150} clipped; recorded, not used to pick the matrix cell by ACC",
                n_trials=PILOT_N,
                params={"n_components": dim, "init": "random", "n_init": 1},
                dataset_version="att92",
                phase="P8_grids",
            )
        )
    n, d, k = SHAPES["JAFFE"]
    for dim in dimension_grid(n, d):
        if dim == pca_dim("JAFFE"):
            continue
        if dim not in {50, 150}:
            continue
        jobs.append(
            _job(
                method="pca_kmeans",
                dataset="JAFFE",
                factor=f"PCAKM_GRID_D{dim}",
                fidelity=B,
                notes="PCA dim grid subset; recorded, not selected by ACC",
                n_trials=PILOT_N,
                params={"n_components": dim, "init": "random", "n_init": 1},
                dataset_version="zenodo",
                phase="P8_grids",
            )
        )
    for dim in dimension_grid(*SHAPES["ORL"][:2], n_clusters=SHAPES["ORL"][2], lda=True):
        if dim == lda_dim("ORL"):
            continue
        jobs.append(
            _job(
                method="lda_kmeans",
                dataset="ORL",
                factor=f"LDAKM_GRID_D{dim}",
                fidelity=B,
                notes="LDA dim grid clipped by K-1; recorded, not selected by ACC. Primary cell is K-1.",
                n_trials=PILOT_N,
                params={"n_components": dim, "init": "random", "n_init": 1},
                dataset_version="att92",
                phase="P8_grids",
            )
        )
    for gamma in GAMMA_GRID:
        if float(gamma) == 1.0:
            continue
        for variant, fidelity, label in (
            ("E8", A, "faithful stationarity"),
            ("E13", B, "printed Eq 13"),
        ):
            jobs.append(
                _job(
                    method="ssc",
                    dataset="ORL",
                    factor=f"SSC_{variant}_G{_gamma_token(float(gamma))}",
                    fidelity=fidelity,
                    notes=f"SSC {variant} {label} gamma={gamma}; grid recorded; not selected by ACC; raw objectives not compared across gamma",
                    n_trials=PILOT_N,
                    params=ssc_params(variant=variant, gamma=float(gamma)),
                    dataset_version="att92",
                    phase="P8_grids",
                )
            )

    for dataset, version in (("ORL", "att92"), ("JAFFE", "zenodo")):
        jobs.append(
            _job(
                method="lda_spectral",
                dataset=dataset,
                factor=f"LDASC_D{lda_dim(dataset)}",
                fidelity=C,
                notes="LDA-SC APPROXIMATE (Ding-Li + SC). Not counted as a faithful 72-cell reproduction.",
                n_trials=LDASC_N,
                params={**sc_params(), "n_components": lda_dim(dataset)},
                dataset_version=version,
                phase="P9_ldasc",
            )
        )

    jobs.append(
        _job(
            method="kmeans",
            dataset="UMIST",
            factor="KMEANS_NOT564",
            fidelity=C,
            notes="UMIST precropped575 is not the paper 564-image set. Extra diagnostic only.",
            n_trials=EXTRA_N,
            params={"init": "random", "n_init": 1},
            dataset_version="precropped575",
            phase="P10_extras",
        )
    )
    jobs.append(
        _job(
            method="sc",
            dataset="UMIST",
            factor="SC_NOT564",
            fidelity=C,
            notes="UMIST precropped575 n=575, not paper 564. Extra diagnostic only.",
            n_trials=EXTRA_N,
            params=sc_params(),
            dataset_version="precropped575",
            phase="P10_extras",
        )
    )
    jobs.append(
        _job(
            method="kmeans",
            dataset="BinAlpha",
            factor="KMEANS_UNVERIFIED",
            fidelity=C,
            notes="letters26x30_seed0 UNVERIFIED reconstruction. Never COMPLETE_VERIFIED BinAlpha.",
            n_trials=EXTRA_N,
            params={"init": "random", "n_init": 1},
            dataset_version="letters26x30_seed0",
            phase="P10_extras",
        )
    )
    jobs.append(
        _job(
            method="sc",
            dataset="BinAlpha",
            factor="SC_UNVERIFIED",
            fidelity=C,
            notes="letters26x30_seed0 UNVERIFIED reconstruction. Never COMPLETE_VERIFIED BinAlpha.",
            n_trials=EXTRA_N,
            params=sc_params(),
            dataset_version="letters26x30_seed0",
            phase="P10_extras",
        )
    )
    return jobs


def _pct(mean: float | None, std: float | None, n: int | None = None) -> str:
    if mean is None:
        return ""
    body = f"{100.0 * mean:.1f}" if std is None else f"{100.0 * mean:.1f} ± {100.0 * std:.1f}"
    if n is not None:
        return f"{body} (n={n})"
    return body


def _paper_str(pair: tuple[float, float] | None) -> str:
    if pair is None:
        return ""
    return f"{pair[0]:.1f} ± {pair[1]:.1f}"


def _best_inertia(metrics: dict[str, Any]) -> str:
    trials = metrics.get("trials") or []
    with_inertia = [t for t in trials if t.get("kmeans_inertia") is not None]
    if not with_inertia:
        return ""
    best = min(with_inertia, key=lambda t: float(t["kmeans_inertia"]))
    acc = best.get("acc")
    acc_s = "" if acc is None else f"; ACC_at_best_inertia={100.0 * float(acc):.1f} (not a selection rule)"
    return f"seed={best.get('seed')} inertia={best['kmeans_inertia']:.6g}{acc_s}"


def _config_summary(row: dict[str, Any]) -> str:
    params = row.get("params") or {}
    bits = [
        f"method={row.get('method')}",
        f"version={row.get('metrics', {}).get('dataset_version') or (row.get('metadata') or {}).get('dataset_version')}",
        f"k={params.get('k', '-')}",
        f"gamma={params.get('gamma', '-')}",
        f"variant={params.get('variant', '-')}",
        f"n_components={params.get('n_components', '-')}",
        "kmeans=random/n_init=1",
        "label_informed=false",
    ]
    return "; ".join(str(b) for b in bits)


def _find_primary(
    rows: list[dict[str, Any]],
    method: str,
    dataset: str,
    version: str | None,
    *,
    variant: str | None = None,
    gamma: float | None = None,
    n_components: int | None = None,
    extra: bool = False,
) -> dict[str, Any] | None:
    candidates = []
    for row in rows:
        if row.get("method") != method or row.get("dataset") != dataset:
            continue
        cfg_version = (row.get("metadata") or {}).get("dataset_version")
        if cfg_version is None:
            cfg_version = (row.get("metrics") or {}).get("dataset_version")
        if version != cfg_version:
            continue
        factor = str((row.get("metadata") or {}).get("factor") or "")
        if (not extra) and factor.startswith("PILOT_"):
            continue
        if (not extra) and ("GRID" in factor or factor.endswith("UNVERIFIED") or "NOT564" in factor):
            continue
        if (not extra) and factor.startswith("BLOCKED"):
            continue
        params = row.get("params") or {}
        if variant is not None and str(params.get("variant") or "") != variant:
            continue
        if gamma is not None:
            if params.get("gamma") is None:
                continue
            if not np.isclose(float(params["gamma"]), float(gamma), rtol=1e-9, atol=0.0):
                continue
        if n_components is not None and int(params.get("n_components") or -1) != n_components:
            continue
        if row.get("status") not in {"COMPLETED", "TIMEOUT", "FAILED", "SKIPPED", "INTERRUPTED"}:
            continue
        candidates.append(row)
    if not candidates:
        return None

    def score(row: dict[str, Any]) -> tuple[int, int, int]:
        completed = int(row.get("n_trials_completed") or 0)
        ok = 1 if row.get("status") == "COMPLETED" else 0
        return (ok, completed, 1 if row.get("run_id") else 0)

    return max(candidates, key=score)


def _compare_saved_f(sc: dict[str, Any] | None, e8: dict[str, Any] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sc_run": None if sc is None else sc.get("run_id"),
        "e8_run": None if e8 is None else e8.get("run_id"),
    }
    if sc is None or e8 is None:
        payload["status"] = "not_both_completed"
        return payload
    sc_f = Path(sc["run_dir"]) / "embedding_F.npy"
    e8_f = Path(e8["run_dir"]) / "embedding_F.npy"
    if not (sc_f.is_file() and e8_f.is_file()):
        payload["status"] = "missing_embedding_files"
        return payload
    left = np.load(sc_f)
    right = np.load(e8_f)
    delta = np.abs(left - right)
    max_abs = float(delta.max()) if delta.size else 0.0
    payload.update(
        {
            "status": "compared",
            "equal_exact": bool(np.allclose(left, right, atol=0.0, rtol=0.0)),
            "equal_atol_1e-12": bool(np.allclose(left, right, atol=1e-12, rtol=0.0)),
            "max_abs_diff": max_abs,
            "shape": list(left.shape),
        }
    )
    return payload


def _shared_f_record(rows: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "note": "SC F must equal SSC F under the same SpectralGraphConfig. Compared from saved embedding_F.npy.",
        "pairs": {},
    }
    for dataset, version in FAITHFUL_DATASETS:
        sc = _find_primary(rows, "sc", dataset, version)
        e8 = _find_primary(rows, "ssc", dataset, version, variant="E8", gamma=1.0)
        payload["pairs"][f"{dataset}:{version}"] = _compare_saved_f(sc, e8)
    orl = payload["pairs"].get("ORL:att92") or {}
    payload.update({k: v for k, v in orl.items() if k != "status" or "status" not in payload})
    payload["status"] = orl.get("status", "not_both_completed")
    payload["all_equal_atol_1e-12"] = all(
        item.get("equal_atol_1e-12") is True
        for item in payload["pairs"].values()
        if item.get("status") == "compared"
    )
    return payload


def _protocol_status(dataset: str, n_completed: int, target: int, status: str) -> str:
    if status == "SKIPPED":
        return "not_executed_loader_or_method_blocked"
    if n_completed <= 0:
        return "no_trials"
    if dataset in {"YaleB", "USPS"} and n_completed < 50:
        return f"budget_limited_n={n_completed}_paper_protocol_is_50"
    if n_completed < 50:
        return f"n={n_completed}_lt_paper_50"
    if n_completed >= 50:
        return "n=50_random_clustering_trials"
    return f"n={n_completed}_target={target}"


def _cell_status(
    *,
    method: str,
    dataset: str,
    row: dict[str, Any] | None,
    blocked_data: bool,
) -> str:
    if method == "spls":
        return "BLOCKED_METHOD"
    if blocked_data:
        return "BLOCKED_DATA"
    if row is None:
        return "NOT_REPRODUCED"
    status = row.get("status")
    n = int(row.get("n_trials_completed") or 0)
    requested = int(row.get("n_trials_requested") or 0)
    if status == "SKIPPED":
        reason = str((row.get("status_payload") or {}).get("reason") or "")
        if "NOT_IMPLEMENTED" in reason:
            return "BLOCKED_METHOD"
        if "unavailable" in reason.lower() or "DatasetUnavailable" in reason:
            return "BLOCKED_DATA"
        return "NOT_REPRODUCED"
    if status == "COMPLETED" and n > 0 and (requested == 0 or n >= requested):
        return "completed"
    if status in {"TIMEOUT", "INTERRUPTED"} or (n > 0 and n < requested):
        return "INCOMPLETE"
    if status == "FAILED":
        return "INCOMPLETE" if n > 0 else "NOT_REPRODUCED"
    if n > 0:
        return "INCOMPLETE"
    return "NOT_REPRODUCED"


def _gap(reproduced: float | None, paper: tuple[float, float] | None) -> str:
    if reproduced is None or paper is None:
        return ""
    return f"{100.0 * reproduced - paper[0]:+.1f} pp vs historical paper mean"


def _matrix_row(
    *,
    display_method: str,
    method_key: str,
    dataset: str,
    paper_method: str,
    row: dict[str, Any] | None,
    fidelity: str,
    identity: str,
    blocked_data: bool,
    extra_note: str = "",
) -> dict[str, str]:
    paper_acc = PAPER_ACC.get(paper_method, {}).get(dataset)
    paper_nmi = PAPER_NMI.get(paper_method, {}).get(dataset)
    n = 0 if row is None else int(row.get("n_trials_completed") or 0)
    requested = 0 if row is None else int(row.get("n_trials_requested") or 0)
    status = _cell_status(method=method_key, dataset=dataset, row=row, blocked_data=blocked_data)
    acc_mean = None if row is None else row.get("acc_mean")
    acc_std = None if row is None else row.get("acc_std")
    nmi_mean = None if row is None else row.get("nmi_mean")
    nmi_std = None if row is None else row.get("nmi_std")
    metrics = {} if row is None else (row.get("metrics") or {})
    conv = ""
    if method_key == "ssc" and metrics:
        irls = metrics.get("irls_converged")
        n_it = metrics.get("n_irls_iterations")
        if irls is True:
            conv = f"IRLS converged in {n_it} steps; unconverged would have been left unconverged"
        elif irls is False:
            conv = f"IRLS unconverged after {n_it} steps (left unconverged; not forced)"
        else:
            conv = "IRLS status not recorded"
    elif method_key == "spls":
        conv = "not run; NotImplementedError"
    elif blocked_data:
        conv = "not run; dataset unavailable"
    else:
        conv = "n/a (no IRLS)"
    protocol = ""
    if blocked_data or method_key == "spls":
        protocol = "not executed"
    elif row is not None:
        protocol = _protocol_status(dataset, n, requested, str(row.get("status")))
    else:
        protocol = "not launched"
    run_ids = "" if row is None else str(row.get("run_id") or "")
    if row is None:
        config = extra_note
    else:
        config = _config_summary(row)
        if extra_note:
            config = f"{config}; {extra_note}"
    return {
        "Method": display_method,
        "Dataset": dataset,
        "Paper ACC": _paper_str(paper_acc) + " [historical only]",
        "Reproduced ACC": _pct(acc_mean, acc_std, n) if n else "",
        "Paper NMI": _paper_str(paper_nmi) + " [historical only]",
        "Reproduced NMI": _pct(nmi_mean, nmi_std, n) if n else "",
        "trial count": str(n),
        "config": config,
        "selection rule": SELECTION_RULE,
        "dataset identity": identity,
        "method fidelity": fidelity,
        "protocol status": protocol,
        "convergence": conv,
        "gaps": _gap(acc_mean, paper_acc) if n else "",
        "run IDs": run_ids,
        "status": status,
        "best inertia": "" if row is None else _best_inertia(metrics),
    }


def build_matrix(rows: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    main: list[dict[str, str]] = []
    extra: list[dict[str, str]] = []
    version_of = {
        "ORL": "att92",
        "JAFFE": "zenodo",
        "YaleB": "cropped2414",
        "USPS": "libsvm",
        "AR": None,
        "MSRA50": None,
        "UMIST": None,
        "BinAlpha": None,
    }
    for method in PAPER_METHODS:
        for dataset in PAPER_DATASETS:
            blocked = dataset in BLOCKED_DATASETS
            version = version_of[dataset]
            identity = IDENTITY.get((dataset, version), "unspecified")
            if method == "spls":
                main.append(
                    _matrix_row(
                        display_method="SPLS",
                        method_key="spls",
                        dataset=dataset,
                        paper_method="spls",
                        row=_find_primary(rows, "spls", "ORL", "att92"),
                        fidelity="NOT_IMPLEMENTED / BLOCKED_METHOD",
                        identity=identity,
                        blocked_data=False,
                        extra_note="Section 3 not obtained; no invented SPLS numbers",
                    )
                )
                continue
            if method == "ssc":
                row = None if blocked else _find_primary(rows, "ssc", dataset, version, variant="E8", gamma=1.0)
                main.append(
                    _matrix_row(
                        display_method="SSC E8",
                        method_key="ssc",
                        dataset=dataset,
                        paper_method="ssc",
                        row=row,
                        fidelity="A_PAPER_FAITHFUL (Eq.8 stationarity A=S+2γL̃)",
                        identity=identity,
                        blocked_data=blocked,
                        extra_note="matrix cell is E8; E13 is a separate extra row",
                    )
                )
                e13 = None if blocked else _find_primary(rows, "ssc", dataset, version, variant="E13", gamma=1.0)
                extra.append(
                    _matrix_row(
                        display_method="SSC E13",
                        method_key="ssc",
                        dataset=dataset,
                        paper_method="ssc",
                        row=e13,
                        fidelity="B_AMBIGUITY (printed Eq.13 A=S+γL̃); not chosen by ACC",
                        identity=identity,
                        blocked_data=blocked,
                        extra_note="separate from faithful E8 cell; not substituted by ACC",
                    )
                )
                continue
            if method == "lda_spectral":
                row = None if blocked else _find_primary(
                    rows, "lda_spectral", dataset, version, n_components=lda_dim(dataset) if dataset in SHAPES else None
                )
                main.append(
                    _matrix_row(
                        display_method="LDA-SC",
                        method_key="lda_spectral",
                        dataset=dataset,
                        paper_method="lda_spectral",
                        row=row,
                        fidelity="APPROXIMATE (not counted as faithful 72 scientifically reproduced)",
                        identity=identity,
                        blocked_data=blocked,
                        extra_note="Ding–Li + SC interpretation; excluded from faithful reproduction count",
                    )
                )
                continue
            n_comp = None
            if method == "pca_kmeans" and dataset in SHAPES:
                n_comp = pca_dim(dataset)
            elif method == "pca_spectral" and dataset in SHAPES:
                n_comp = pca_dim(dataset)
            elif method == "lda_kmeans" and dataset in SHAPES:
                n_comp = lda_dim(dataset)
            row = None if blocked else _find_primary(
                rows, method, dataset, version, n_components=n_comp
            )
            fidelity = {
                "kmeans": "FAITHFUL_REIMPLEMENTATION (random, n_init=1)",
                "sc": "FAITHFUL_REIMPLEMENTATION (Eq.4 k=5 shared SpectralGraphConfig)",
                "pca_kmeans": "FAITHFUL_REIMPLEMENTATION; dim prespecified not ACC",
                "pca_spectral": "FAITHFUL_REIMPLEMENTATION; dim prespecified not ACC",
                "lda_kmeans": "FAITHFUL_REIMPLEMENTATION; rank<=K-1",
                "llc": "FAITHFUL_REIMPLEMENTATION",
            }[method]
            main.append(
                _matrix_row(
                    display_method=DISPLAY_METHOD[method],
                    method_key=method,
                    dataset=dataset,
                    paper_method=method,
                    row=row,
                    fidelity=fidelity,
                    identity=identity,
                    blocked_data=blocked,
                )
            )

    umist = _find_primary(rows, "sc", "UMIST", "precropped575", extra=True)
    extra.append(
        _matrix_row(
            display_method="SC (UMIST 575 extra)",
            method_key="sc",
            dataset="UMIST",
            paper_method="sc",
            row=umist,
            fidelity="C_DIAGNOSTIC not-564",
            identity=IDENTITY[("UMIST", "precropped575")],
            blocked_data=False,
            extra_note="NOT the paper 564-image UMIST cell",
        )
    )
    binalpha = _find_primary(rows, "sc", "BinAlpha", "letters26x30_seed0", extra=True)
    extra.append(
        _matrix_row(
            display_method="SC (BinAlpha reconstruction extra)",
            method_key="sc",
            dataset="BinAlpha",
            paper_method="sc",
            row=binalpha,
            fidelity="C_DIAGNOSTIC UNVERIFIED",
            identity=IDENTITY[("BinAlpha", "letters26x30_seed0")],
            blocked_data=False,
            extra_note="UNVERIFIED letters26x30_seed0; never COMPLETE_VERIFIED BinAlpha",
        )
    )
    return main, extra


def _md_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")).replace("|", "/") for col in columns) + " |")
    return "\n".join(lines)


def write_outputs(rows: list[dict[str, Any]], launch_log: list[dict[str, Any]]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs").mkdir(parents=True, exist_ok=True)

    shared = _shared_f_record(rows)
    (RESULTS_DIR / "shared_f.json").write_text(
        json.dumps(shared, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    (RESULTS_DIR / "launch_log.json").write_text(
        json.dumps(launch_log, indent=2, default=str, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    registry_fields = [
        "run_id",
        "status",
        "track",
        "method",
        "dataset",
        "n_trials_requested",
        "n_trials_completed",
        "acc_mean",
        "acc_std",
        "nmi_mean",
        "nmi_std",
        "gamma",
        "k",
        "n_components",
        "irls_converged",
        "irls_iterations",
    ]
    with (RESULTS_DIR / "experiment_registry.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=registry_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in registry_fields})

    main, extra = build_matrix(rows)
    columns = [
        "Method",
        "Dataset",
        "Paper ACC",
        "Reproduced ACC",
        "Paper NMI",
        "Reproduced NMI",
        "trial count",
        "config",
        "selection rule",
        "dataset identity",
        "method fidelity",
        "protocol status",
        "convergence",
        "gaps",
        "run IDs",
        "status",
        "best inertia",
    ]
    with MATRIX_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in main + extra:
            writer.writerow(row)
    (RESULTS_DIR / "reproduction_full_matrix.csv").write_text(
        MATRIX_CSV.read_text(encoding="utf-8"), encoding="utf-8"
    )

    counts: dict[str, int] = {}
    for row in main:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    faithful_completed = [
        row
        for row in main
        if row["status"] == "completed"
        and "APPROXIMATE" not in row["method fidelity"]
        and "BLOCKED_METHOD" not in row["method fidelity"]
        and "NOT_IMPLEMENTED" not in row["method fidelity"]
    ]
    md = []
    md.append("# Strict reproduction full matrix (Task 2)")
    md.append("")
    md.append("Paper ACC/NMI are **historical only** (Chang et al., AAAI 2015, Tables 1–2). They are not our numbers.")
    md.append("Reproduced numbers come only from `runs/strict_repro/`. No trial was invented or extrapolated.")
    md.append("SSC matrix cells are **E8** (`A=S+2γL̃`). Printed Eq. 13 (**E13**) is a separate extra block, not chosen by ACC.")
    md.append("LDA-SC is APPROXIMATE and is **not** counted as a faithful reproduction.")
    md.append("SPLS is BLOCKED_METHOD. AR / MSRA50 / UMIST-564 / paper BinAlpha are BLOCKED_DATA.")
    md.append("Selection never uses ACC for seed, γ, or dimension.")
    md.append("")
    md.append(f"Shared F check (ORL att92 SC vs SSC E8): `{json.dumps(shared, ensure_ascii=True)}`")
    md.append("")
    md.append(f"72-cell status counts: {counts}")
    md.append(f"Faithful completed cells (excluding LDA-SC and SPLS): {len(faithful_completed)}")
    md.append("")
    compact_cols = ["Method", "Dataset", "Reproduced ACC", "Reproduced NMI", "trial count", "status", "gaps"]
    md.append("## Compact ACC/NMI (paper numbers are historical only)")
    md.append("")
    md.append(_md_table(main, compact_cols))
    md.append("")
    md.append("## 72 published method × dataset cells")
    md.append("")
    md.append(_md_table(main, columns))
    md.append("")
    md.append("## Extra columns (not substitutes for paper cells)")
    md.append("")
    md.append(_md_table(extra, columns))
    md.append("")
    MATRIX_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    (RESULTS_DIR / "reproduction_full_matrix.md").write_text(MATRIX_MD.read_text(encoding="utf-8"), encoding="utf-8")

    blockers = []
    if any(r["status"] == "BLOCKED_METHOD" for r in main):
        blockers.append("SPLS: Section 3 not obtained; `baselines/spls/spls.py` raises NotImplementedError; no substitute shrinking.")
    blockers.append("AR: official host unavailable; unofficial Zenodo dump not used; 840/120 subset not invented.")
    blockers.append("MSRA50: no 1799×12×1024 archive; other MSRA corpora not renamed.")
    blockers.append("UMIST 564: not obtained. precropped575 (n=575, 565 unique pixels) is extra, labeled not-564.")
    blockers.append("Paper BinAlpha 26×30: not identified. letters26x30_seed0 is UNVERIFIED reconstruction only.")
    if shared.get("status") == "compared" and not shared.get("equal"):
        blockers.append(f"Shared F mismatch: max_abs_diff={shared.get('max_abs_diff')}.")

    n50 = [r for r in faithful_completed if r["Dataset"] in {"ORL", "JAFFE"} and r["trial count"] == "50"]
    budgeted = [r for r in faithful_completed if r["Dataset"] in {"YaleB", "USPS"}]
    completion = [
        "# Task 2：哪些已发表实验被科学地复现了？",
        "",
        "**没有。** Chang et al. (AAAI 2015) Tables 1–2 的 72 个 method×dataset 格子，没有一格达到论文全协议复现"
        "（8 个数据集、每格 50 次随机聚类、论文未公开预处理、以及 SPLS / AR / MSRA50 / UMIST-564 / 论文 BinAlpha）。",
        "",
        "本轮只把下列格子算作**部分科学执行**（不是论文复现）：方法为忠实重实现；数据为指定忠实版本"
        "（ORL `att92`、JAFFE Zenodo、YaleB `cropped2414`、USPS LIBSVM）；数字来自 `runs/strict_repro/` 真实 trial；"
        "γ / 维数 / 种子均**不用 ACC 选择**；SC 与 SSC 共用 `SpectralGraphConfig`。"
        "LDA-SC 为 APPROXIMATE，不计入忠实 72 格科学复现。"
        "SPLS 为 BLOCKED_METHOD。"
        "E13 单独记录，不用 ACC 替换 E8。",
        "",
        f"72 格状态：`{json.dumps(counts, ensure_ascii=True)}`。"
        f"忠实已完成 {len(faithful_completed)} 格（7 方法 × 4 可加载数据集）。"
        "其中 ORL/JAFFE 为 n=50；YaleB n=10、USPS n=3 或 5，协议状态写明不是论文的 50 次。未外推。",
        "",
        "## 部分科学执行（真实日志）",
        "",
        "### n=50（ORL att92 与 JAFFE Zenodo）",
        "",
    ]
    for row in n50:
        completion.append(
            f"- {row['Method']} × {row['Dataset']}: ACC {row['Reproduced ACC']}; "
            f"NMI {row['Reproduced NMI']}; {row['gaps']}; `{row['run IDs']}`"
        )
    completion.extend(["", "### 预算受限（YaleB n=10，USPS n=3 或 5）", ""])
    for row in budgeted:
        completion.append(
            f"- {row['Method']} × {row['Dataset']}: ACC {row['Reproduced ACC']}; "
            f"NMI {row['Reproduced NMI']}; {row['protocol status']}; `{row['run IDs']}`"
        )
    completion.extend(
        [
            "",
            "## 仍然不是论文复现的原因",
            "",
            "- 论文协议是每个数据集 50 次随机聚类。YaleB 实际 n=10，USPS 实际 n≤5。INCOMPLETE 只写实际 n，绝不补成 50。",
            "- ORL `att92` 是 AT&T 92×112 原包缩到 32×32（双线性插值是假设），不是 Olivetti，也未宣称 PAPER_PROTOCOL_MATCHED。",
            "- JAFFE 是已核实 Zenodo zip，不是论文未公开预处理副本。",
            "- YaleB `cropped2414` 计数 2414 与论文一致，不声称与邓蔡 `YaleB_32x32.mat` 逐像素同一。",
            "- PCA 维数步长 `{10,20,…,150}` 是假设。矩阵格用预指定维数 min(50,K,n−1,d)，**不用网格上的最高 ACC**。",
            "- LDA 秩 ≤ K−1（Ding–Li），网格到不了 150。",
            "- SSC γ 网格 `{1e-6,1e-3,1,1e3,1e6}` 已记录。矩阵格用预指定 γ=1。不按 ACC 选 γ，也不把原始式 (8) 目标跨 γ 互比。未收敛 IRLS 保持未收敛。",
            "- 历史 Track A / Round 2 数字没有抄进本矩阵。",
            "- LDA-SC（ORL/JAFFE n=10）已跑，标 APPROXIMATE，不计入忠实复现。YaleB/USPS 的 LDA-SC 为 NOT_REPRODUCED（可选近似格，未跑）。",
            "",
            "## 阻塞",
            "",
        ]
    )
    for item in blockers:
        completion.append(f"- {item}")
    completion.extend(
        [
            "",
            "## Shared F",
            "",
            "同一 `SpectralGraphConfig` 下 SC 的 F 必须等于 SSC 的 F。ORL att92 及其余忠实数据集的 `embedding_F.npy` 比较见下。",
            "",
            f"```json\n{json.dumps(shared, indent=2, ensure_ascii=True)}\n```",
            "",
            "产物：`results/reproduction_full_matrix.csv`、`results/reproduction_full_matrix.md`、`results/strict_repro/`、`runs/strict_repro/`。",
            "未 git commit / push。",
            "",
        ]
    )
    COMPLETION_MD.write_text("\n".join(completion) + "\n", encoding="utf-8")
    print(f"Wrote {MATRIX_CSV}", flush=True)
    print(f"Wrote {COMPLETION_MD}", flush=True)
    print(f"72-cell counts: {counts}", flush=True)
    print(f"Faithful completed: {len(faithful_completed)}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task 2 strict reproduction jobs.")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--phases", default="", help="comma-separated phase prefixes to run")
    args = parser.parse_args(argv)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = build_jobs()
    if args.phases:
        allow = {item.strip() for item in args.phases.split(",") if item.strip()}
        jobs = [job for job in jobs if job.get("phase") in allow]
    launch_log_path = RESULTS_DIR / "launch_log.json"
    launch_log: list[dict[str, Any]] = []
    if launch_log_path.is_file():
        try:
            launch_log = json.loads(launch_log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            launch_log = []
    if not args.aggregate_only:
        print(f"Planning {len(jobs)} jobs -> {RUNS_DIR}", flush=True)
        for i, job in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {job['phase']} {job['factor']} {job['dataset']} n={job['n_trials']}", flush=True)
            try:
                result = _run_job(job)
            except subprocess.TimeoutExpired as exc:
                result = {
                    "config_path": str(job.get("factor")),
                    "returncode": 124,
                    "wall_seconds": None,
                    "factor": job.get("factor"),
                    "phase": job.get("phase"),
                    "status": "runner_timeout",
                    "error": str(exc),
                }
                print(f"RUNNER TIMEOUT {job['factor']}", flush=True)
            launch_log.append(result)
            write_outputs(load_all_runs(RUNS_DIR), launch_log)
    rows = load_all_runs(RUNS_DIR)
    write_outputs(rows, launch_log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
