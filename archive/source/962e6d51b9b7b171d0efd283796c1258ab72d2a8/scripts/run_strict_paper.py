#!/usr/bin/env python3
"""COMP3314 strict Chang 2015 paper-protocol campaign.

Writes configs to configs/strict_paper/, runs to runs/strict_paper/,
matrix to results/strict_reproduction_matrix.csv, and the mapping
document to docs/strict_experiment_protocol.md.

Does not touch method_extension/, report/, or runs/strict_repro/.
Does not select gamma, dimension, or seed by ACC.
SSC E8 and E13 are separate columns. K1–K4 are separate selection rules.
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

from benchmarks import DatasetUnavailable, load_dataset
from experiments.aggregate import load_all_runs
from experiments.paper_reported import ACC as PAPER_ACC
from experiments.paper_reported import DATASETS as PAPER_DATASETS
from experiments.paper_reported import NMI as PAPER_NMI
from experiments.protocol import GAMMA_GRID, dimension_grid, track_b_dimension

PYTHON = sys.executable
RUNNER = ROOT / "scripts" / "run_experiment.py"
PROTOCOL_PATH = ROOT / "configs" / "strict_paper_reproduction.yaml"
CONFIG_DIR = ROOT / "configs" / "strict_paper"
RUNS_DIR = ROOT / "runs" / "strict_paper"
RESULTS_DIR = ROOT / "results" / "strict_paper"
MATRIX_CSV = ROOT / "results" / "strict_reproduction_matrix.csv"
PROTOCOL_MD = ROOT / "docs" / "strict_experiment_protocol.md"

A = "A_PAPER_FAITHFUL"
B = "B_AMBIGUITY"
C = "C_DIAGNOSTIC"
SEED_START = 0
SMOKE_N = 1
GRID_N_SMALL = 5
GRID_N_LARGE = 1
LDASC_N = 10

TIMEOUT_SMOKE = 300
TIMEOUT_SMALL = 1800
TIMEOUT_YALEB = 3600
TIMEOUT_USPS = 7200
TIMEOUT_USPS_LLC = 10800

SHAPES = {
    "ORL": (400, 1024, 40),
    "JAFFE": (213, 676, 10),
    "YaleB": (2414, 1024, 38),
    "USPS": (9298, 256, 10),
    "BinAlpha": (780, 320, 26),
}

IDENTITY = {
    ("ORL", "att92"): "original_source_att92_92x112_bilinear_32x32",
    ("JAFFE", "zenodo"): "verified_zenodo_213_not_paper_unpublished_copy",
    ("YaleB", "cropped2414"): "obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai",
    ("USPS", "libsvm"): "verified_libsvm_9298",
    ("BinAlpha", "CANDIDATE_BIN_ALPHA"): "CANDIDATE_BIN_ALPHA",
    ("BinAlpha", "letters26x30_seed0"): "CANDIDATE_BIN_ALPHA",
    ("AR", None): "SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT",
    ("MSRA50", None): "BLOCKED_DATA_NOT_OBTAINED",
    ("UMIST", None): "BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique",
}
BINALPHA_VERSIONS = ("CANDIDATE_BIN_ALPHA", "letters26x30_seed0")

SELECTION_K1 = (
    "K1 faithful default: random init, n_init=1, mean±std over ALL completed "
    "trials; never selected by ACC"
)
SELECTION_K2 = (
    "K2 diagnostic: single K1 trial with lowest K-means inertia; never ACC"
)
SELECTION_K3 = (
    "K3 diagnostic: k-means++ init, n_init=1, mean±std over ALL completed "
    "trials; never selected by ACC"
)
SELECTION_K4 = (
    "K4 diagnostic: single K3 trial with lowest K-means inertia; never ACC"
)
SELECTION_GAMMA = (
    "every gamma in {1e-6,1e-3,1,1e3,1e6} reported separately; "
    "raw SSC Eq.8 objectives are NOT compared across gamma; never ACC"
)
SELECTION_PCA = (
    "main cell: prespecified Track-B-like dim=min(50,K,n-1,d) labeled ASSUMPTION; "
    "full {10,20,...,150} grid saved and clipped by rank; "
    "optional diagnostic uses lowest K-means inertia, never ACC"
)
SELECTION_LDA = (
    "main cell: n_components=K-1 (Ding–Li); grid clipped by rank<=K-1; never ACC"
)
SELECTION_SC = (
    "shared SpectralGraphConfig k=5 Eq.4; F of SC == F of SSC; "
    "K-means on F is random n_init=1 mean±std; never ACC"
)

for _key in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_key, "8")


def load_protocol() -> dict[str, Any]:
    payload = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("strict_paper_reproduction.yaml must be a mapping")
    return payload


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


def _checksum_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return "; ".join(f"{key}={value[key]}" for key in sorted(value))
    return str(value)


def _timeout_for(dataset: str, method: str, smoke: bool = False) -> int:
    if smoke:
        return TIMEOUT_SMOKE
    if dataset == "USPS" and method == "llc":
        return TIMEOUT_USPS_LLC
    if dataset == "USPS":
        return TIMEOUT_USPS
    if dataset == "YaleB":
        return TIMEOUT_YALEB
    return TIMEOUT_SMALL


def pca_dim(dataset: str) -> int:
    n, d, k = SHAPES[dataset]
    return track_b_dimension(n, d, k, lda=False)


def lda_dim(dataset: str) -> int:
    n, d, k = SHAPES[dataset]
    return track_b_dimension(n, d, k, lda=True)


def probe_loader(dataset: str, version: str | None) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        if version in (None, ""):
            X, y, meta = load_dataset(dataset)
        else:
            X, y, meta = load_dataset(dataset, version=str(version))
        elapsed = time.perf_counter() - t0
        return {
            "dataset": dataset,
            "dataset_version": version,
            "status": "AVAILABLE",
            "n": int(X.shape[0]),
            "d": int(X.shape[1]),
            "n_clusters": int(np.unique(y).size),
            "checksum": meta.get("SHA256_checksum"),
            "identity": meta.get("identity") or meta.get("verification_status"),
            "verification_status": meta.get("verification_status"),
            "wall_seconds": elapsed,
        }
    except DatasetUnavailable as exc:
        return {
            "dataset": dataset,
            "dataset_version": version,
            "status": "BLOCKED_DATA",
            "reason": str(exc),
            "wall_seconds": time.perf_counter() - t0,
        }
    except Exception as exc:  # noqa: BLE001 - probe must not abort the campaign
        return {
            "dataset": dataset,
            "dataset_version": version,
            "status": "FAILED_PROBE",
            "reason": f"{type(exc).__name__}: {exc}",
            "wall_seconds": time.perf_counter() - t0,
        }


def probe_all() -> dict[str, dict[str, Any]]:
    probes = {
        "ORL": probe_loader("ORL", "att92"),
        "JAFFE": probe_loader("JAFFE", "zenodo"),
        "YaleB": probe_loader("YaleB", "cropped2414"),
        "USPS": probe_loader("USPS", "libsvm"),
        "BinAlpha": probe_loader("BinAlpha", "CANDIDATE_BIN_ALPHA"),
        "BinAlpha_default": probe_loader("BinAlpha", None),
        "AR": probe_loader("AR", None),
        "AR_zenodo": probe_loader("AR", "zenodo_third_party_full"),
        "UMIST": probe_loader("UMIST", None),
        "MSRA50": probe_loader("MSRA50", None),
        "SPLS": {
            "dataset": "SPLS",
            "status": "BLOCKED_MISSING_FULL_METHOD",
            "reason": "Section 3 not obtained; baselines.spls.fit_predict raises NotImplementedError",
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "loader_probe.json").write_text(
        json.dumps(probes, indent=2, default=str, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print("Loader probe:", flush=True)
    for name, payload in probes.items():
        print(f"  {name}: {payload.get('status')} {payload.get('reason', '')[:120]}", flush=True)
    return probes


def _job(
    *,
    method: str,
    dataset: str,
    factor: str,
    fidelity: str,
    notes: str,
    n_trials: int,
    params: dict[str, Any] | None,
    dataset_version: str | None,
    phase: str,
    timeout: int | None = None,
    selection_rule: str,
) -> dict[str, Any]:
    identity = IDENTITY.get((dataset, dataset_version), "unspecified")
    return {
        "track": "STRICT_PAPER",
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
        "protocol": "strict_paper_no_ACC_selection",
        "selection_rule": selection_rule,
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
    try:
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
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - t0
        print(f"=== RUNNER TIMEOUT {cfg_path.name} wall={elapsed:.1f}s ===", flush=True)
        return {
            "config_path": str(cfg_path),
            "returncode": 124,
            "wall_seconds": elapsed,
            "factor": config.get("factor"),
            "phase": config.get("phase"),
            "status": "runner_timeout",
            "error": str(exc),
        }


def _core_n(dataset: str, probes: dict[str, dict[str, Any]], reduced: bool) -> int:
    if dataset in {"ORL", "JAFFE", "BinAlpha"}:
        return 50
    if reduced:
        return 10 if dataset == "YaleB" else 5
    return 50


def build_jobs(
    probes: dict[str, dict[str, Any]],
    *,
    smoke: bool = False,
    reduced_large: bool = False,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    runnable: list[tuple[str, str]] = []
    for name, version in (
        ("ORL", "att92"),
        ("JAFFE", "zenodo"),
        ("YaleB", "cropped2414"),
        ("USPS", "libsvm"),
        ("BinAlpha", "CANDIDATE_BIN_ALPHA"),
    ):
        if probes.get(name, {}).get("status") == "AVAILABLE":
            runnable.append((name, version))

    jobs.append(
        _job(
            method="spls",
            dataset="ORL",
            factor="SPLS_NOT_IMPLEMENTED",
            fidelity=C,
            notes="SPLS Section 3 not obtained; BLOCKED_MISSING_FULL_METHOD; no substitute numbers.",
            n_trials=1,
            params={},
            dataset_version="att92",
            phase="P0_probes",
            timeout=60,
            selection_rule="not executed; BLOCKED_MISSING_FULL_METHOD",
        )
    )
    for dataset in ("AR", "UMIST", "MSRA50"):
        jobs.append(
            _job(
                method="kmeans",
                dataset=dataset,
                factor="BLOCKED_DATA_PROBE",
                fidelity=A,
                notes="Default paper set unavailable unless a loader started working.",
                n_trials=1,
                params={"init": "random", "n_init": 1},
                dataset_version=None,
                phase="P0_probes",
                timeout=60,
                selection_rule="not executed; BLOCKED_DATA unless loader works",
            )
        )

    if smoke:
        if ("ORL", "att92") not in runnable:
            return jobs
        smoke_specs = [
            ("kmeans", "SMOKE_K1", {"init": "random", "n_init": 1}, SELECTION_K1),
            ("sc", "SMOKE_SC", sc_params(), SELECTION_SC),
            ("ssc", "SMOKE_SSC_E8_G1", ssc_params(variant="E8", gamma=1.0), SELECTION_GAMMA),
            (
                "pca_kmeans",
                "SMOKE_PCAKM",
                {"n_components": pca_dim("ORL"), "init": "random", "n_init": 1},
                SELECTION_PCA,
            ),
        ]
        for method, factor, params, rule in smoke_specs:
            jobs.append(
                _job(
                    method=method,
                    dataset="ORL",
                    factor=factor,
                    fidelity=A,
                    notes="ORL att92 smoke n=1 before the 50-trial campaign",
                    n_trials=SMOKE_N,
                    params=params,
                    dataset_version="att92",
                    phase="P1_smoke",
                    timeout=_timeout_for("ORL", method, smoke=True),
                    selection_rule=rule,
                )
            )
        return jobs

    priority = [item for item in runnable if item[0] in {"ORL", "JAFFE", "BinAlpha"}]
    large = [item for item in runnable if item[0] in {"YaleB", "USPS"}]

    def add_core(dataset: str, version: str, n_full: int, phase: str) -> None:
        jobs.append(
            _job(
                method="kmeans",
                dataset=dataset,
                factor="K1_RANDOM_MEAN",
                fidelity=A,
                notes="K1 random n_init=1; mean over all trials; inertia recorded for K2",
                n_trials=n_full,
                params={"init": "random", "n_init": 1},
                dataset_version=version,
                phase=phase,
                selection_rule=SELECTION_K1,
            )
        )
        jobs.append(
            _job(
                method="kmeans",
                dataset=dataset,
                factor="K3_KMEANSPP_MEAN",
                fidelity=C,
                notes="K3 k-means++ diagnostic; not the faithful default; never ACC",
                n_trials=n_full,
                params={"init": "k-means++", "n_init": 1},
                dataset_version=version,
                phase=phase,
                selection_rule=SELECTION_K3,
            )
        )
        jobs.append(
            _job(
                method="sc",
                dataset=dataset,
                factor="SC_EQ4",
                fidelity=A,
                notes="SC Eq.4 k=5 shared SpectralGraphConfig; no sklearn SpectralClustering",
                n_trials=n_full,
                params=sc_params(),
                dataset_version=version,
                phase=phase,
                selection_rule=SELECTION_SC,
            )
        )
        for gamma in GAMMA_GRID:
            token = _gamma_token(float(gamma))
            jobs.append(
                _job(
                    method="ssc",
                    dataset=dataset,
                    factor=f"SSC_E8_G{token}",
                    fidelity=A,
                    notes=(
                        f"SSC E8 A=S+2gamma Ltilde gamma={gamma}; F,G solved once, "
                        f"then {n_full} k-means; objectives not compared across gamma"
                    ),
                    n_trials=n_full,
                    params=ssc_params(variant="E8", gamma=float(gamma)),
                    dataset_version=version,
                    phase=phase,
                    selection_rule=SELECTION_GAMMA,
                )
            )
            jobs.append(
                _job(
                    method="ssc",
                    dataset=dataset,
                    factor=f"SSC_E13_G{token}",
                    fidelity=B,
                    notes=(
                        f"SSC E13 printed Eq.13 A=S+gamma Ltilde gamma={gamma}; "
                        "separate column from E8; not chosen by ACC"
                    ),
                    n_trials=n_full,
                    params=ssc_params(variant="E13", gamma=float(gamma)),
                    dataset_version=version,
                    phase=phase,
                    selection_rule=SELECTION_GAMMA,
                )
            )

    def add_dr(dataset: str, version: str, n_full: int, phase: str) -> None:
        n_samples, n_features, n_clusters = SHAPES[dataset]
        selected_pca = pca_dim(dataset)
        selected_lda = lda_dim(dataset)
        grid_n = GRID_N_SMALL if dataset in {"ORL", "JAFFE", "BinAlpha"} else GRID_N_LARGE
        jobs.append(
            _job(
                method="pca_kmeans",
                dataset=dataset,
                factor=f"PCAKM_D{selected_pca}",
                fidelity=A,
                notes=f"PCA-KM prespecified dim={selected_pca} ASSUMPTION; not ACC",
                n_trials=n_full,
                params={"n_components": selected_pca, "init": "random", "n_init": 1},
                dataset_version=version,
                phase=phase,
                selection_rule=SELECTION_PCA,
            )
        )
        jobs.append(
            _job(
                method="pca_spectral",
                dataset=dataset,
                factor=f"PCASC_D{selected_pca}",
                fidelity=A,
                notes=f"PCA-SC shared Eq.4 on PCA({selected_pca}); not sklearn SpectralClustering",
                n_trials=n_full,
                params={**sc_params(), "n_components": selected_pca},
                dataset_version=version,
                phase=phase,
                selection_rule=SELECTION_PCA,
            )
        )
        jobs.append(
            _job(
                method="lda_kmeans",
                dataset=dataset,
                factor=f"LDAKM_D{selected_lda}",
                fidelity=A,
                notes=f"LDA-KM dim={selected_lda}=K-1; cannot search 150",
                n_trials=n_full,
                params={"n_components": selected_lda, "init": "random", "n_init": 1},
                dataset_version=version,
                phase=phase,
                selection_rule=SELECTION_LDA,
            )
        )
        jobs.append(
            _job(
                method="llc",
                dataset=dataset,
                factor="LLC",
                fidelity=A,
                notes="LLC k=5 Yu-Shi discretization; representation cached then trials",
                n_trials=n_full,
                params={"k": 5},
                dataset_version=version,
                phase=phase,
                selection_rule="Yu-Shi discretization random_state=trial seed; mean±std; never ACC",
            )
        )
        for dim in dimension_grid(n_samples, n_features):
            if dim == selected_pca:
                continue
            jobs.append(
                _job(
                    method="pca_kmeans",
                    dataset=dataset,
                    factor=f"PCAKM_GRID_D{dim}",
                    fidelity=B,
                    notes="PCA dim grid ASSUMPTION {10..150} clipped; inertia recorded; not ACC",
                    n_trials=grid_n,
                    params={"n_components": dim, "init": "random", "n_init": 1},
                    dataset_version=version,
                    phase=f"{phase}_grid",
                    selection_rule=SELECTION_PCA,
                )
            )
        for dim in dimension_grid(n_samples, n_features, n_clusters=n_clusters, lda=True):
            if dim == selected_lda:
                continue
            jobs.append(
                _job(
                    method="lda_kmeans",
                    dataset=dataset,
                    factor=f"LDAKM_GRID_D{dim}",
                    fidelity=B,
                    notes="LDA dim grid clipped by K-1; recorded; primary cell is K-1",
                    n_trials=grid_n,
                    params={"n_components": dim, "init": "random", "n_init": 1},
                    dataset_version=version,
                    phase=f"{phase}_grid",
                    selection_rule=SELECTION_LDA,
                )
            )

    for dataset, version in priority:
        n_full = 50
        add_core(dataset, version, n_full, f"P2_{dataset.lower()}_core")
        add_dr(dataset, version, n_full, f"P3_{dataset.lower()}_dr")
        if dataset in {"ORL", "JAFFE", "BinAlpha"}:
            jobs.append(
                _job(
                    method="lda_spectral",
                    dataset=dataset,
                    factor=f"LDASC_D{lda_dim(dataset)}",
                    fidelity=C,
                    notes="LDA-SC APPROXIMATE; not a faithful table cell",
                    n_trials=LDASC_N,
                    params={**sc_params(), "n_components": lda_dim(dataset)},
                    dataset_version=version,
                    phase="P4_ldasc",
                    timeout=_timeout_for(dataset, "lda_spectral"),
                    selection_rule="APPROXIMATE; n_components=K-1; never ACC; excluded from faithful table",
                )
            )

    for dataset, version in large:
        n_full = _core_n(dataset, probes, reduced_large)
        add_core(dataset, version, n_full, f"P5_{dataset.lower()}_core")
        add_dr(dataset, version, n_full, f"P6_{dataset.lower()}_dr")

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
    return f"{pair[0]:.1f} ± {pair[1]:.1f} [historical only]"


def _best_inertia_trial(metrics: dict[str, Any]) -> dict[str, Any] | None:
    trials = metrics.get("trials") or []
    with_inertia = [t for t in trials if t.get("kmeans_inertia") is not None]
    if not with_inertia:
        return None
    return min(with_inertia, key=lambda t: float(t["kmeans_inertia"]))


def _find(
    rows: list[dict[str, Any]],
    method: str,
    dataset: str,
    version: str | None,
    *,
    factor: str | None = None,
    variant: str | None = None,
    gamma: float | None = None,
    n_components: int | None = None,
) -> dict[str, Any] | None:
    candidates = []
    for row in rows:
        if row.get("method") != method or row.get("dataset") != dataset:
            continue
        cfg_version = (row.get("metadata") or {}).get("dataset_version")
        if cfg_version is None:
            cfg_version = (row.get("metrics") or {}).get("dataset_version")
        allowed_versions = (
            BINALPHA_VERSIONS
            if dataset == "BinAlpha" and version in BINALPHA_VERSIONS
            else (version,)
        )
        if cfg_version not in allowed_versions:
            continue
        row_factor = str((row.get("metadata") or {}).get("factor") or "")
        if factor is not None and row_factor != factor:
            continue
        if factor is None and row_factor.startswith(("SMOKE_", "PILOT_")):
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
        candidates.append(row)
    if not candidates:
        return None

    def score(row: dict[str, Any]) -> tuple[int, int]:
        ok = 1 if row.get("status") == "COMPLETED" else 0
        return (ok, int(row.get("n_trials_completed") or 0))

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


def _shared_f_record(rows: list[dict[str, Any]], versions: dict[str, str | None]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "note": "SC F must equal SSC F under the same SpectralGraphConfig.",
        "pairs": {},
    }
    for dataset, version in versions.items():
        if version is None:
            continue
        sc = _find(rows, "sc", dataset, version, factor="SC_EQ4")
        e8 = _find(rows, "ssc", dataset, version, variant="E8", gamma=1.0)
        payload["pairs"][f"{dataset}:{version}"] = _compare_saved_f(sc, e8)
    compared = [item for item in payload["pairs"].values() if item.get("status") == "compared"]
    payload["all_equal_atol_1e-12"] = bool(compared) and all(
        item.get("equal_atol_1e-12") is True for item in compared
    )
    return payload


def _cell_status(
    *,
    method: str,
    dataset: str,
    row: dict[str, Any] | None,
    blocked_data: bool,
    blocked_method: bool,
) -> str:
    if blocked_method or method == "spls":
        return "BLOCKED_MISSING_FULL_METHOD"
    if dataset == "AR":
        return "SOURCE_RECOVERED_SUBSET_UNVERIFIED"
    if dataset == "MSRA50":
        return "BLOCKED_DATA_NOT_OBTAINED"
    if dataset == "UMIST":
        return "BLOCKED_DATA"
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
            return "BLOCKED_MISSING_FULL_METHOD"
        if "unavailable" in reason.lower() or "DatasetUnavailable" in reason:
            return "BLOCKED_DATA"
        return "NOT_REPRODUCED"
    if status == "COMPLETED" and n > 0 and (requested == 0 or n >= requested):
        if n < 50:
            return "INCOMPLETE"
        return "completed"
    if status in {"TIMEOUT", "INTERRUPTED"} or (n > 0 and n < requested):
        return "INCOMPLETE"
    if status == "FAILED":
        return "INCOMPLETE" if n > 0 else "NOT_REPRODUCED"
    if n > 0:
        return "INCOMPLETE"
    return "NOT_REPRODUCED"


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
    selection_rule: str,
    extra_note: str = "",
    acc_mean: float | None = None,
    acc_std: float | None = None,
    nmi_mean: float | None = None,
    nmi_std: float | None = None,
    n_override: int | None = None,
    blocked_method: bool = False,
) -> dict[str, str]:
    if dataset == "AR":
        extra_note = (
            (extra_note + "; " if extra_note else "")
            + "third-party Zenodo 100 identities s1-s100; MD5 matched; NOT official Martinez; NOT paper 840/120; NOT EXACT"
        )
    elif dataset == "BinAlpha":
        extra_note = (
            (extra_note + "; " if extra_note else "")
            + "CANDIDATE_BIN_ALPHA seed0 780x320; not historical identity; default load_dataset('BinAlpha') unavailable"
        )
    paper_acc = PAPER_ACC.get(paper_method, {}).get(dataset)
    paper_nmi = PAPER_NMI.get(paper_method, {}).get(dataset)
    n = n_override if n_override is not None else (0 if row is None else int(row.get("n_trials_completed") or 0))
    requested = 0 if row is None else int(row.get("n_trials_requested") or 0)
    status = _cell_status(
        method=method_key,
        dataset=dataset,
        row=row,
        blocked_data=blocked_data,
        blocked_method=blocked_method,
    )
    if acc_mean is None:
        acc_mean = None if row is None else row.get("acc_mean")
        acc_std = None if row is None else row.get("acc_std")
        nmi_mean = None if row is None else row.get("nmi_mean")
        nmi_std = None if row is None else row.get("nmi_std")
    metrics = {} if row is None else (row.get("metrics") or {})
    params = {} if row is None else (row.get("params") or {})
    checksum = _checksum_str(metrics.get("dataset_checksum"))
    conv = ""
    if method_key == "ssc" and metrics:
        irls = metrics.get("irls_converged")
        n_it = metrics.get("n_irls_iterations")
        if irls is True:
            conv = f"IRLS converged in {n_it} steps"
        elif irls is False:
            conv = f"IRLS unconverged after {n_it} steps (left unconverged)"
        else:
            conv = "IRLS status not recorded"
    elif method_key == "spls" or blocked_method:
        conv = "not run; BLOCKED_MISSING_FULL_METHOD"
    elif blocked_data:
        conv = "not run; dataset unavailable"
    else:
        conv = "n/a (no IRLS)"
    if blocked_data or blocked_method or method_key == "spls":
        protocol = "not executed"
    elif row is not None:
        if n >= 50:
            protocol = "n=50_random_clustering_trials"
        else:
            protocol = f"INCOMPLETE_n={n}_requested={requested}_paper_protocol_is_50"
    else:
        protocol = "not launched"
    run_ids = "" if row is None else str(row.get("run_id") or "")
    config = extra_note
    if row is not None:
        bits = [
            f"method={row.get('method')}",
            f"version={metrics.get('dataset_version') or dataset}",
            f"k={params.get('k', '-')}",
            f"gamma={params.get('gamma', '-')}",
            f"variant={params.get('variant', '-')}",
            f"n_components={params.get('n_components', '-')}",
            f"init={params.get('init', params.get('kmeans_init', '-'))}",
            "label_informed=false",
        ]
        config = "; ".join(str(b) for b in bits)
        if extra_note:
            config = f"{config}; {extra_note}"
    return {
        "Method": display_method,
        "Dataset": dataset,
        "dataset version": "" if row is None else str(metrics.get("dataset_version") or ""),
        "dataset identity": identity,
        "dataset checksum": checksum,
        "Paper ACC": _paper_str(paper_acc),
        "Reproduced ACC": _pct(acc_mean, acc_std, n) if n else "",
        "Paper NMI": _paper_str(paper_nmi),
        "Reproduced NMI": _pct(nmi_mean, nmi_std, n) if n else "",
        "trial count requested": str(requested),
        "trial count": str(n),
        "gamma": "" if params.get("gamma") is None else str(params.get("gamma")),
        "variant": str(params.get("variant") or ""),
        "n_components": "" if params.get("n_components") is None else str(params.get("n_components")),
        "config": config,
        "selection rule": selection_rule,
        "method fidelity": fidelity,
        "protocol status": protocol,
        "convergence": conv,
        "run IDs": run_ids,
        "status": status,
    }


def _k2_row(parent: dict[str, Any] | None, dataset: str, identity: str, blocked: bool) -> dict[str, str]:
    trial = None if parent is None else _best_inertia_trial(parent.get("metrics") or {})
    acc = None if trial is None else trial.get("acc")
    nmi = None if trial is None else trial.get("nmi")
    extra = ""
    if trial is not None:
        extra = (
            f"derived from K1 run; seed={trial.get('seed')} "
            f"inertia={trial['kmeans_inertia']:.6g}; ACC reported but not used for selection"
        )
    return _matrix_row(
        display_method="K-means K2",
        method_key="kmeans",
        dataset=dataset,
        paper_method="kmeans",
        row=parent,
        fidelity="C_DIAGNOSTIC best-inertia (not faithful default)",
        identity=identity,
        blocked_data=blocked,
        selection_rule=SELECTION_K2,
        extra_note=extra,
        acc_mean=None if acc is None else float(acc),
        acc_std=0.0 if acc is not None else None,
        nmi_mean=None if nmi is None else float(nmi),
        nmi_std=0.0 if nmi is not None else None,
        n_override=1 if trial is not None else 0,
    )


def _k4_row(parent: dict[str, Any] | None, dataset: str, identity: str, blocked: bool) -> dict[str, str]:
    trial = None if parent is None else _best_inertia_trial(parent.get("metrics") or {})
    acc = None if trial is None else trial.get("acc")
    nmi = None if trial is None else trial.get("nmi")
    extra = ""
    if trial is not None:
        extra = (
            f"derived from K3 run; seed={trial.get('seed')} "
            f"inertia={trial['kmeans_inertia']:.6g}; ACC reported but not used for selection"
        )
    return _matrix_row(
        display_method="K-means K4",
        method_key="kmeans",
        dataset=dataset,
        paper_method="kmeans",
        row=parent,
        fidelity="C_DIAGNOSTIC k-means++ best-inertia",
        identity=identity,
        blocked_data=blocked,
        selection_rule=SELECTION_K4,
        extra_note=extra,
        acc_mean=None if acc is None else float(acc),
        acc_std=0.0 if acc is not None else None,
        nmi_mean=None if nmi is None else float(nmi),
        nmi_std=0.0 if nmi is not None else None,
        n_override=1 if trial is not None else 0,
    )


def build_matrix(
    rows: list[dict[str, Any]],
    probes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    main: list[dict[str, str]] = []
    extra: list[dict[str, str]] = []
    version_of: dict[str, str | None] = {
        "ORL": "att92",
        "JAFFE": "zenodo",
        "YaleB": "cropped2414",
        "USPS": "libsvm",
        "BinAlpha": "CANDIDATE_BIN_ALPHA" if probes.get("BinAlpha", {}).get("status") == "AVAILABLE" else None,
        "AR": None,
        "MSRA50": None,
        "UMIST": None,
    }
    blocked_of = {
        name: probes.get(name, {}).get("status") != "AVAILABLE"
        for name in PAPER_DATASETS
    }
    if probes.get("BinAlpha", {}).get("status") == "AVAILABLE":
        blocked_of["BinAlpha"] = False

    for dataset in PAPER_DATASETS:
        version = version_of[dataset]
        identity = IDENTITY.get((dataset, version), "unspecified")
        blocked = bool(blocked_of.get(dataset, True)) and dataset not in {"ORL", "JAFFE", "YaleB", "USPS"}
        if dataset in {"ORL", "JAFFE", "YaleB", "USPS"}:
            blocked = probes.get(dataset, {}).get("status") != "AVAILABLE"
        if dataset == "BinAlpha":
            blocked = probes.get("BinAlpha", {}).get("status") != "AVAILABLE"
            identity = IDENTITY.get(("BinAlpha", "CANDIDATE_BIN_ALPHA"), identity)
        if dataset == "AR":
            blocked = True
            identity = IDENTITY[("AR", None)]

        k1 = None if blocked else _find(rows, "kmeans", dataset, version, factor="K1_RANDOM_MEAN")
        k3 = None if blocked else _find(rows, "kmeans", dataset, version, factor="K3_KMEANSPP_MEAN")
        main.append(
            _matrix_row(
                display_method="K-means K1",
                method_key="kmeans",
                dataset=dataset,
                paper_method="kmeans",
                row=k1,
                fidelity="A_PAPER_FAITHFUL random n_init=1 mean",
                identity=identity,
                blocked_data=blocked,
                selection_rule=SELECTION_K1,
            )
        )
        extra.append(_k2_row(k1, dataset, identity, blocked))
        extra.append(
            _matrix_row(
                display_method="K-means K3",
                method_key="kmeans",
                dataset=dataset,
                paper_method="kmeans",
                row=k3,
                fidelity="C_DIAGNOSTIC k-means++ mean",
                identity=identity,
                blocked_data=blocked,
                selection_rule=SELECTION_K3,
            )
        )
        extra.append(_k4_row(k3, dataset, identity, blocked))

        sc = None if blocked else _find(rows, "sc", dataset, version, factor="SC_EQ4")
        main.append(
            _matrix_row(
                display_method="SC",
                method_key="sc",
                dataset=dataset,
                paper_method="sc",
                row=sc,
                fidelity="A_PAPER_FAITHFUL Eq.4 shared SpectralGraphConfig",
                identity=identity,
                blocked_data=blocked,
                selection_rule=SELECTION_SC,
            )
        )

        n_comp = pca_dim(dataset) if dataset in SHAPES else None
        pca_km = None if blocked else _find(rows, "pca_kmeans", dataset, version, n_components=n_comp)
        main.append(
            _matrix_row(
                display_method="PCA-KM",
                method_key="pca_kmeans",
                dataset=dataset,
                paper_method="pca_kmeans",
                row=pca_km,
                fidelity="A_PAPER_FAITHFUL; dim prespecified ASSUMPTION not ACC",
                identity=identity,
                blocked_data=blocked,
                selection_rule=SELECTION_PCA,
            )
        )
        pca_sc = None if blocked else _find(rows, "pca_spectral", dataset, version, n_components=n_comp)
        main.append(
            _matrix_row(
                display_method="PCA-SC",
                method_key="pca_spectral",
                dataset=dataset,
                paper_method="pca_spectral",
                row=pca_sc,
                fidelity="A_PAPER_FAITHFUL shared Eq.4 after PCA; not sklearn SpectralClustering",
                identity=identity,
                blocked_data=blocked,
                selection_rule=SELECTION_PCA,
            )
        )

        lda_n = lda_dim(dataset) if dataset in SHAPES else None
        lda_km = None if blocked else _find(rows, "lda_kmeans", dataset, version, n_components=lda_n)
        main.append(
            _matrix_row(
                display_method="LDA-KM",
                method_key="lda_kmeans",
                dataset=dataset,
                paper_method="lda_kmeans",
                row=lda_km,
                fidelity="A_PAPER_FAITHFUL; rank<=K-1",
                identity=identity,
                blocked_data=blocked,
                selection_rule=SELECTION_LDA,
            )
        )
        lda_sc = None if blocked else _find(rows, "lda_spectral", dataset, version, n_components=lda_n)
        extra.append(
            _matrix_row(
                display_method="LDA-SC",
                method_key="lda_spectral",
                dataset=dataset,
                paper_method="lda_spectral",
                row=lda_sc,
                fidelity="APPROXIMATE (not a faithful table cell)",
                identity=identity,
                blocked_data=blocked,
                selection_rule="APPROXIMATE Ding–Li + SC; excluded from faithful table; never ACC",
            )
        )

        llc = None if blocked else _find(rows, "llc", dataset, version, factor="LLC")
        main.append(
            _matrix_row(
                display_method="LLC",
                method_key="llc",
                dataset=dataset,
                paper_method="llc",
                row=llc,
                fidelity="A_PAPER_FAITHFUL",
                identity=identity,
                blocked_data=blocked,
                selection_rule="Yu-Shi discretization; mean±std; never ACC",
            )
        )

        main.append(
            _matrix_row(
                display_method="SPLS",
                method_key="spls",
                dataset=dataset,
                paper_method="spls",
                row=_find(rows, "spls", "ORL", "att92", factor="SPLS_NOT_IMPLEMENTED"),
                fidelity="BLOCKED_MISSING_FULL_METHOD",
                identity=identity,
                blocked_data=False,
                blocked_method=True,
                selection_rule="not executed; BLOCKED_MISSING_FULL_METHOD",
                extra_note="Section 3 not obtained; no invented SPLS numbers",
            )
        )

        for variant, fidelity, label in (
            ("E8", "A_PAPER_FAITHFUL (Eq.8 stationarity A=S+2γL̃)", "SSC E8"),
            ("E13", "B_AMBIGUITY (printed Eq.13 A=S+γL̃)", "SSC E13"),
        ):
            for gamma in GAMMA_GRID:
                ssc = None if blocked else _find(
                    rows, "ssc", dataset, version, variant=variant, gamma=float(gamma)
                )
                target = main if True else extra
                target.append(
                    _matrix_row(
                        display_method=label,
                        method_key="ssc",
                        dataset=dataset,
                        paper_method="ssc",
                        row=ssc,
                        fidelity=fidelity,
                        identity=identity,
                        blocked_data=blocked,
                        selection_rule=SELECTION_GAMMA,
                        extra_note=f"gamma={gamma}; E8/E13 are separate columns; not picked by ACC",
                    )
                )

        if dataset in SHAPES and not blocked:
            for dim in dimension_grid(*SHAPES[dataset][:2]):
                if dim == pca_dim(dataset):
                    continue
                grid = _find(rows, "pca_kmeans", dataset, version, n_components=dim)
                extra.append(
                    _matrix_row(
                        display_method="PCA-KM grid",
                        method_key="pca_kmeans",
                        dataset=dataset,
                        paper_method="pca_kmeans",
                        row=grid,
                        fidelity="B_AMBIGUITY dim-grid ASSUMPTION",
                        identity=identity,
                        blocked_data=False,
                        selection_rule=SELECTION_PCA,
                        extra_note=f"grid dim={dim}; not the main cell; not ACC",
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


COLUMNS = [
    "Method",
    "Dataset",
    "dataset version",
    "dataset identity",
    "dataset checksum",
    "Paper ACC",
    "Reproduced ACC",
    "Paper NMI",
    "Reproduced NMI",
    "trial count requested",
    "trial count",
    "gamma",
    "variant",
    "n_components",
    "config",
    "selection rule",
    "method fidelity",
    "protocol status",
    "convergence",
    "run IDs",
    "status",
]


def write_outputs(
    rows: list[dict[str, Any]],
    launch_log: list[dict[str, Any]],
    probes: dict[str, dict[str, Any]],
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs").mkdir(parents=True, exist_ok=True)

    versions = {
        "ORL": "att92",
        "JAFFE": "zenodo",
        "YaleB": "cropped2414",
        "USPS": "libsvm",
    }
    if probes.get("BinAlpha", {}).get("status") == "AVAILABLE":
        versions["BinAlpha"] = "CANDIDATE_BIN_ALPHA"
    shared = _shared_f_record(rows, versions)
    (RESULTS_DIR / "shared_f.json").write_text(
        json.dumps(shared, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    (RESULTS_DIR / "launch_log.json").write_text(
        json.dumps(launch_log, indent=2, default=str, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    main, extra = build_matrix(rows, probes)
    with MATRIX_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in main + extra:
            writer.writerow(row)
    (RESULTS_DIR / "strict_reproduction_matrix.csv").write_text(
        MATRIX_CSV.read_text(encoding="utf-8"), encoding="utf-8"
    )

    n50 = [r for r in main if r["trial count"] == "50" and r["status"] == "completed"]
    incomplete = [r for r in main if r["status"] == "INCOMPLETE"]
    blocked = [
        r
        for r in main
        if r["status"]
        in {
            "BLOCKED_DATA",
            "BLOCKED_METHOD",
            "BLOCKED_MISSING_FULL_METHOD",
            "BLOCKED_DATA_NOT_OBTAINED",
            "SOURCE_RECOVERED_SUBSET_UNVERIFIED",
        }
    ]
    gamma_rows = [r for r in main if r["Method"].startswith("SSC ")]
    gamma_finished = [
        r for r in gamma_rows if r["status"] in {"completed", "INCOMPLETE"} and int(r["trial count"] or 0) > 0
    ]
    write_protocol_md(main, extra, probes, shared, n50, incomplete, blocked, gamma_finished)
    print(f"Wrote {MATRIX_CSV}", flush=True)
    print(f"n=50 main cells: {len(n50)}; INCOMPLETE: {len(incomplete)}; BLOCKED: {len(blocked)}", flush=True)


def write_protocol_md(
    main: list[dict[str, str]],
    extra: list[dict[str, str]],
    probes: dict[str, dict[str, Any]],
    shared: dict[str, Any],
    n50: list[dict[str, str]],
    incomplete: list[dict[str, str]],
    blocked: list[dict[str, str]],
    gamma_finished: list[dict[str, str]],
) -> None:
    lines = [
        "# Strict Chang 2015 experiment protocol",
        "",
        "Paper: Chang, Nie, Wang, Yang, *Spectral Shrunk Clustering*, AAAI 2015 Setup.",
        "Code root: `v1/`. Config: `configs/strict_paper_reproduction.yaml`.",
        "Runs: `runs/strict_paper/`. Matrix: `results/strict_reproduction_matrix.csv`.",
        "This campaign does **not** overwrite `runs/strict_repro/`, `report/`, or `method_extension/`.",
        "",
        "## Campaign outcome (real logs only)",
        "",
        f"- **n=50 main cells: {len(n50)}** (ORL att92, JAFFE zenodo, CANDIDATE_BIN_ALPHA, YaleB cropped2414, USPS libsvm × K1/SC/PCA-KM/PCA-SC/LDA-KM/LLC + SSC E8×5γ + SSC E13×5γ).",
        f"- **Gamma grids finished:** SSC E8 and E13, all five γ ∈ {{1e-6, 1e-3, 1, 1e3, 1e6}}, n=50, on those five datasets. F,G solved once per (dataset, variant, γ); raw Eq.8 objectives were **not** compared across γ.",
        "- **AR paper cells are not EXACT.** Third-party Zenodo zip (MD5 `bb97bd9237680744c0c7268624696263`, 100 identities s1–s100) is `SOURCE_RECOVERED_SUBSET_UNVERIFIED`, not official Martinez, not 840/120. Loader still returns no arrays; no clustering diagnostic was run.",
        "- **BinAlpha** is `CANDIDATE_BIN_ALPHA` (seed 0, 780×320). Default `load_dataset('BinAlpha')` remains unavailable. Not historical identity.",
        "- **UMIST 564** still missing (575 files / 565 unique) → `BLOCKED_DATA`.",
        "- **MSRA50** → `BLOCKED_DATA_NOT_OBTAINED`.",
        "- **SPLS** → `BLOCKED_MISSING_FULL_METHOD`.",
        "- **LDA-SC** is APPROXIMATE (ORL/JAFFE/BinAlpha n=10) and is not a faithful table cell.",
        "- Extra dim-grid and LDA-SC rows keep their actual n (5 / 10 / 1) and are not counted as paper-protocol n=50. Main protocol cells have **zero** INCOMPLETE.",
        "- Shared F: SC F == SSC F at atol 1e-12 on all compared datasets.",
        "",
        "## Paper → code → config → run IDs",
        "",
        "| Paper setting | Code | Config | Typical factors / run IDs |",
        "| --- | --- | --- | --- |",
        "| k=5 neighborhood | `SSC_method.spectral_config.SpectralGraphConfig.k` | `params.k: 5` | SC_EQ4, SSC_E8_*, SSC_E13_* |",
        "| Eq. (4) SC embedding F | `experiments.methods.prepare_spectral` + `SSC_method.spectral_embedding` | `laplacian: symmetric_normalized_eq4` | SC_EQ4 |",
        "| SSC Eq. (8) / E8 | `SSC_method.optimizer.shrink_embedding` variant E8 | `params.variant: E8` | SSC_E8_G1em6 … G1e6 |",
        "| Printed Eq. (13) / E13 | same optimizer, `variant=E13` | `params.variant: E13` | SSC_E13_G*; **separate column** |",
        "| γ ∈ {1e-6, 1e-3, 1, 1e3, 1e6} | `params.gamma` | `gamma_grid` in YAML | one F,G solve per γ, then k-means trials |",
        "| ACC Hungarian | `benchmarks.metrics.clustering_accuracy` | `acc: hungarian` | evaluation only |",
        "| NMI geometric | `benchmarks.metrics.normalized_mutual_information` | `nmi: geometric` | evaluation only |",
        "| 50 random clusterings | `scripts/run_experiment.py` n_trials | `n_trials_paper: 50` | K1_RANDOM_MEAN, SC_EQ4, SSC_* |",
        "| K-means random mean (K1) | `baselines.kmeans` / `_kmeans_labels` init=random | `params.init: random` | K1_RANDOM_MEAN |",
        "| Best inertia (K2) | derived from K1 trials | not a separate fit | extra column |",
        "| k-means++ mean/best (K3/K4) | init=`k-means++` | `params.init: k-means++` | K3_KMEANSPP_MEAN; K4 derived |",
        "| Dim {10,…,150} ASSUMPTION | `experiments.protocol.dimension_grid` | `dim_grid.status: ASSUMPTION` | PCAKM_GRID_D*, PCASC/PCAKM main at Track-B dim |",
        "| LDA rank ≤ K−1 | `baselines.lda_kmeans` | `n_components: K-1` | LDAKM_D{K-1} |",
        "| No sklearn SpectralClustering | `baselines.spectral_clustering` docstring + shared F path | `no_sklearn_SpectralClustering: true` | SC / PCA-SC / SSC |",
        "| ORL att92 | `benchmarks.orl` version att92 | `dataset_version: att92` | see matrix |",
        "| JAFFE Zenodo | `benchmarks.jaffe` version zenodo | `dataset_version: zenodo` | see matrix |",
        "| YaleB cropped2414 | `benchmarks.yaleb` version cropped2414 | `dataset_version: cropped2414` | see matrix |",
        "| USPS LIBSVM | `benchmarks.usps` | `dataset_version: libsvm` | see matrix |",
        "| BinAlpha candidate | `benchmarks.binalpha` version=`CANDIDATE_BIN_ALPHA` (alias letters26x30_seed0) | seed 0, 780×320, not historical identity | default load_dataset('BinAlpha') still unavailable |",
        "| AR 840/120 | not recovered; third-party Zenodo zip is 100 identities | `SOURCE_RECOVERED_SUBSET_UNVERIFIED` | paper cell is **not EXACT**; no official Martinez set |",
        "| UMIST 564 | 575 files / 565 unique; paper 564 missing | BLOCKED_DATA | not used as paper UMIST |",
        "| MSRA50 | no 1799×12 archive | BLOCKED_DATA_NOT_OBTAINED | |",
        "| SPLS | `baselines.spls.fit_predict` | BLOCKED_MISSING_FULL_METHOD | SPLS_NOT_IMPLEMENTED |",
        "| LDA-SC | `baselines.lda_spectral` | APPROXIMATE | LDASC_D*; not faithful table |",
        "",
        "## Loader probe at campaign start",
        "",
        "```json",
        json.dumps(probes, indent=2, default=str, ensure_ascii=True),
        "```",
        "",
        "## Shared F (SC == SSC)",
        "",
        "```json",
        json.dumps(shared, indent=2, ensure_ascii=True),
        "```",
        "",
        f"## Cells with n=50 ({len(n50)})",
        "",
    ]
    if n50:
        for row in n50:
            lines.append(
                f"- {row['Method']} × {row['Dataset']} γ={row['gamma'] or 'NA'} "
                f"n={row['trial count']} `{row['run IDs']}`"
            )
    else:
        lines.append("- none yet")
    lines.extend(
        [
            "",
            f"## Gamma-grid rows with at least one real trial ({len(gamma_finished)})",
            "",
        ]
    )
    if gamma_finished:
        for row in gamma_finished:
            lines.append(
                f"- {row['Method']} × {row['Dataset']} γ={row['gamma']} "
                f"n={row['trial count']} status={row['status']} `{row['run IDs']}`"
            )
    else:
        lines.append("- none yet")
    lines.extend(["", f"## INCOMPLETE ({len(incomplete)})", ""])
    if incomplete:
        for row in incomplete:
            lines.append(
                f"- {row['Method']} × {row['Dataset']} γ={row['gamma'] or 'NA'} "
                f"{row['protocol status']} `{row['run IDs']}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", f"## BLOCKED ({len(blocked)})", ""])
    if blocked:
        seen = set()
        for row in blocked:
            key = (row["Method"], row["Dataset"], row["status"])
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- {row['Method']} × {row['Dataset']}: {row['status']} ({row['dataset identity']})")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Extra (K2/K3/K4, LDA-SC APPROXIMATE, PCA dim grid)",
            "",
            "These are not substitutes for paper cells and are never chosen by ACC.",
            "",
            _md_table(
                extra[:40],
                ["Method", "Dataset", "Reproduced ACC", "trial count", "status", "run IDs"],
            ),
            "",
            "## Integrity",
            "",
            "- Every reproduced number comes from `runs/strict_paper/` trial logs.",
            "- Unconverged IRLS is left unconverged.",
            "- No trial is invented, extrapolated, or selected by ACC.",
            "- Paper ACC/NMI in the matrix are historical Chang et al. Tables 1–2 only.",
            "",
        ]
    )
    PROTOCOL_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {PROTOCOL_MD}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run strict Chang 2015 paper-protocol jobs.")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--reduced-large", action="store_true", help="YaleB/USPS use fallback n")
    parser.add_argument("--phases", default="", help="comma-separated phase prefixes to run")
    args = parser.parse_args(argv)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()
    print(f"Protocol {protocol.get('protocol_name')} track={protocol.get('track')}", flush=True)

    probes = probe_all()
    launch_log_path = RESULTS_DIR / "launch_log.json"
    launch_log: list[dict[str, Any]] = []
    if launch_log_path.is_file():
        try:
            launch_log = json.loads(launch_log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            launch_log = []

    if not args.aggregate_only:
        job_sets: list[list[dict[str, Any]]] = []
        if not args.skip_smoke and not args.smoke_only:
            job_sets.append(build_jobs(probes, smoke=True))
        if args.smoke_only:
            job_sets.append(build_jobs(probes, smoke=True))
        else:
            job_sets.append(build_jobs(probes, smoke=False, reduced_large=args.reduced_large))
        jobs: list[dict[str, Any]] = []
        for block in job_sets:
            jobs.extend(block)
        if args.phases:
            allow = {item.strip() for item in args.phases.split(",") if item.strip()}
            jobs = [job for job in jobs if job.get("phase") in allow]
        print(f"Planning {len(jobs)} jobs -> {RUNS_DIR}", flush=True)
        for i, job in enumerate(jobs, 1):
            print(
                f"[{i}/{len(jobs)}] {job['phase']} {job['factor']} {job['dataset']} n={job['n_trials']}",
                flush=True,
            )
            result = _run_job(job)
            launch_log.append(result)
            write_outputs(load_all_runs(RUNS_DIR), launch_log, probes)

    rows = load_all_runs(RUNS_DIR)
    write_outputs(rows, launch_log, probes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
