#!/usr/bin/env python3
"""COMP3314 Round 2 controlled diagnostics D1–D12.

Writes configs to configs/round2/ and runs to runs/round2/.
Does not touch Phase 1, repair_round1, the 4-page report, or git.
Default SSC remains E13; the faithful table uses E8. K-means seeds are
never selected by ACC. Invalid / Category C variants do not get 50 trials.
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

from benchmarks.metrics import clustering_accuracy, normalized_mutual_information
from experiments.aggregate import load_run
from experiments.paper_reported import ACC as PAPER_ACC
from experiments.paper_reported import NMI as PAPER_NMI

PYTHON = sys.executable
RUNNER = ROOT / "scripts" / "run_experiment.py"
CONFIG_DIR = ROOT / "configs" / "round2"
RUNS_DIR = ROOT / "runs" / "round2"
RESULTS_DIR = ROOT / "results" / "round2"

PILOT_N = 5
SHORTLIST_N = 50
YALEB_N = 10
USPS_N = 3
SEED_START = 0
TIMEOUT_SMALL = 1800
TIMEOUT_USPS = 3600

A = "A_PAPER_FAITHFUL"
B = "B_AMBIGUITY"
C = "C_DIAGNOSTIC"

IDENTITY = {
    ("ORL", "olivetti"): "approximate_olivetti_64_to_32_not_att92_native",
    ("ORL", "att92"): "original_source_att92_92x112_bilinear_32x32",
    ("ORL", "att92_nearest"): "original_source_att92_92x112_nearest_32x32_interpolation_B",
    ("ORL", "att92_bicubic"): "original_source_att92_92x112_bicubic_32x32_interpolation_B",
    ("JAFFE", "zenodo"): "verified_zenodo_213_not_paper_unpublished_copy",
    ("YaleB", "dengcai32"): "approximate_dengcai32_not_claimed_sample_identity_with_paper",
    ("YaleB", "cropped2414"): "obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai",
    ("USPS", "libsvm"): "verified_libsvm_9298",
}

HISTORICAL_SC_ORL = {
    "acc_mean": 0.54215,
    "acc_std": 0.031432670187275545,
    "n": 50,
    "run_id": "20261020_015207__TRACKA__SC__ORL__a86c9d70",
    "backend": "baselines.spectral",
    "dataset": "olivetti 64->32",
}

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
        "symmetrization": "union",
        "laplacian": "symmetric_normalized_eq4",
    }
    params.update(overrides)
    return params


def _job(
    *,
    method: str,
    dataset: str,
    factor: str,
    fidelity: str,
    notes: str,
    n_trials: int,
    params: dict[str, Any],
    dataset_version: str,
    timeout: int = TIMEOUT_SMALL,
) -> dict[str, Any]:
    identity = IDENTITY[(dataset, dataset_version)]
    if dataset == "ORL" and dataset_version == "olivetti":
        assert "original_source" not in identity
    return {
        "track": "ROUND2",
        "method": method,
        "dataset": dataset,
        "dataset_version": dataset_version,
        "dataset_identity_status": identity,
        "factor": factor,
        "paper_fidelity_category": fidelity,
        "n_trials": int(n_trials),
        "trial_seed_start": SEED_START,
        "timeout_seconds": int(timeout),
        "params": dict(params),
        "notes": notes,
        "label_informed_selection": False,
        "protocol": "R2_one_factor_then_kmeans_seeds",
        "hardware_note": "8 CPU / 16 GB",
    }


def _slug(config: dict[str, Any]) -> str:
    params = config.get("params") or {}
    parts = [
        str(config.get("dataset")),
        str(config.get("method")),
        str(config.get("factor")),
        str(params.get("variant") or "NA"),
        str(params.get("gamma") if params.get("gamma") is not None else "NA"),
        str(params.get("cluster_on") or "NA"),
        str(params.get("kmeans_init") or "random").replace("+", "p"),
        str(config.get("dataset_version")),
        f"n{config.get('n_trials')}",
    ]
    return "__".join(parts).replace(".", "p").replace("-", "m")


def _write_config(config: dict[str, Any]) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"{_slug(config)}.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
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
        if status.get("status") not in {"COMPLETED", "TIMEOUT"}:
            continue
        if not _same_setting(existing, config):
            continue
        requested = int(config.get("n_trials") or 0)
        completed = int(metrics.get("n_trials_completed") or 0)
        if status.get("status") == "COMPLETED" and completed >= requested:
            return child.name
        if status.get("status") == "TIMEOUT" and str(config.get("dataset")) == "USPS":
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
            "dataset": config.get("dataset"),
        }
    cfg_path = _write_config(config)
    timeout = int(config.get("timeout_seconds") or TIMEOUT_SMALL) + 120
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
        "dataset": config.get("dataset"),
    }


def d1_jobs() -> list[dict[str, Any]]:
    notes_sc = (
        "Shared Eq.(4) SC, k=5, union kNN, median directed positive kNN "
        "squared bandwidth, raw eigenvectors, K-means random n_init=1. "
        "Do not label Olivetti as original-source."
    )
    return [
        _job(
            method="sc",
            dataset="ORL",
            factor="D01_OLIVETTI_SC",
            fidelity=A,
            notes=notes_sc + " Olivetti 64x64->32x32; NOT original-source AT&T PGM.",
            n_trials=SHORTLIST_N,
            params=sc_params(),
            dataset_version="olivetti",
        ),
        _job(
            method="sc",
            dataset="ORL",
            factor="D01_ATT92_SC",
            fidelity=A,
            notes=notes_sc + " att92 original-source reconstruction 92x112 bilinear 32x32.",
            n_trials=SHORTLIST_N,
            params=sc_params(),
            dataset_version="att92",
        ),
        _job(
            method="sc",
            dataset="ORL",
            factor="D01_ATT92_NEAREST_SC",
            fidelity=B,
            notes="Interpolation B: att92 nearest 32x32. Same SC config. Pilot only.",
            n_trials=PILOT_N,
            params=sc_params(),
            dataset_version="att92_nearest",
        ),
        _job(
            method="sc",
            dataset="ORL",
            factor="D01_ATT92_BICUBIC_SC",
            fidelity=B,
            notes="Interpolation B: att92 bicubic 32x32. Same SC config. Pilot only.",
            n_trials=PILOT_N,
            params=sc_params(),
            dataset_version="att92_bicubic",
        ),
    ]


def d3_d6_jobs() -> list[dict[str, Any]]:
    return [
        _job(
            method="sc",
            dataset="ORL",
            factor="D03_BW_MEAN_SC",
            fidelity=B,
            notes="One-factor bandwidth: mean positive kNN Euclidean distance squared.",
            n_trials=PILOT_N,
            params=sc_params(bandwidth_rule="mean_knn_distance_scale"),
            dataset_version="att92",
        ),
        _job(
            method="sc",
            dataset="ORL",
            factor="D03_BW_UNDIRECTED_MEDIAN_SC",
            fidelity=B,
            notes="One-factor bandwidth: median of remaining undirected-edge squared distances.",
            n_trials=PILOT_N,
            params=sc_params(bandwidth_rule="median_undirected_edge_squared_distance"),
            dataset_version="att92",
        ),
        _job(
            method="sc",
            dataset="ORL",
            factor="D04_MUTUAL_SC",
            fidelity=C,
            notes="Mutual (AND) symmetrization. C even if ACC rises. Pilot only.",
            n_trials=PILOT_N,
            params=sc_params(symmetrization="mutual"),
            dataset_version="att92",
        ),
        _job(
            method="sc",
            dataset="ORL",
            factor="D06_ROW_NORM_SC",
            fidelity=C,
            notes="Ng-Jordan-Weiss row-normalization. C even if ACC rises. Pilot only.",
            n_trials=PILOT_N,
            params=sc_params(row_normalize=True),
            dataset_version="att92",
        ),
    ]


def d7_d9_jobs() -> list[dict[str, Any]]:
    return [
        _job(
            method="ssc",
            dataset="ORL",
            factor="D08_E13_ATT92",
            fidelity=B,
            notes="E13 printed Eq.(13) A=S+gamma Ltilde. Separate column from faithful E8.",
            n_trials=SHORTLIST_N,
            params=ssc_params(variant="E13"),
            dataset_version="att92",
        ),
        _job(
            method="ssc",
            dataset="ORL",
            factor="D08_E8_ATT92",
            fidelity=A,
            notes="E8 stationary A=S+2*gamma Ltilde. Faithful Round 2 table. gamma=1.",
            n_trials=SHORTLIST_N,
            params=ssc_params(variant="E8"),
            dataset_version="att92",
        ),
        _job(
            method="ssc",
            dataset="ORL",
            factor="D09_E8_ITER1000_ATT92",
            fidelity=B,
            notes="D9 convergence budget max_iter=1000 on att92 E8. Pilot only.",
            n_trials=PILOT_N,
            params=ssc_params(variant="E8", max_iter=1000),
            dataset_version="att92",
        ),
    ]


def d12_jaffe_jobs() -> list[dict[str, Any]]:
    return [
        _job(
            method="sc",
            dataset="JAFFE",
            factor="D12_JAFFE_SC",
            fidelity=A,
            notes="D12 shortlist SC on verified Zenodo JAFFE. Shared Eq.(4) path.",
            n_trials=SHORTLIST_N,
            params=sc_params(),
            dataset_version="zenodo",
        ),
        _job(
            method="ssc",
            dataset="JAFFE",
            factor="D12_JAFFE_E8",
            fidelity=A,
            notes="D12 shortlist E8 gamma=1 on JAFFE.",
            n_trials=SHORTLIST_N,
            params=ssc_params(variant="E8"),
            dataset_version="zenodo",
        ),
        _job(
            method="ssc",
            dataset="JAFFE",
            factor="D12_JAFFE_E13",
            fidelity=B,
            notes="D12 shortlist E13 gamma=1 on JAFFE. Separate column.",
            n_trials=SHORTLIST_N,
            params=ssc_params(variant="E13"),
            dataset_version="zenodo",
        ),
    ]


def yaleb_jobs() -> list[dict[str, Any]]:
    jobs = []
    for version, factor_tag in (
        ("dengcai32", "DENGCAI32"),
        ("cropped2414", "CROPPED2414"),
    ):
        jobs.append(
            _job(
                method="sc",
                dataset="YaleB",
                factor=f"D01_{factor_tag}_SC",
                fidelity=A,
                notes=f"YaleB SC n=10, version={version}. Not 50 trials.",
                n_trials=YALEB_N,
                params=sc_params(),
                dataset_version=version,
            )
        )
        jobs.append(
            _job(
                method="ssc",
                dataset="YaleB",
                factor=f"D08_{factor_tag}_E8",
                fidelity=A,
                notes=f"YaleB E8 n=10, version={version}. Not 50 trials.",
                n_trials=YALEB_N,
                params=ssc_params(variant="E8"),
                dataset_version=version,
            )
        )
    return jobs


def usps_jobs() -> list[dict[str, Any]]:
    return [
        _job(
            method="sc",
            dataset="USPS",
            factor="D12_USPS_SC",
            fidelity=A,
            notes="USPS SC pilot 1-3 inits on shared Eq.(4) path. Timeout allowed.",
            n_trials=USPS_N,
            params=sc_params(),
            dataset_version="libsvm",
            timeout=TIMEOUT_USPS,
        ),
        _job(
            method="ssc",
            dataset="USPS",
            factor="D08_USPS_E8",
            fidelity=A,
            notes="USPS E8 pilot 1-3 inits. Timeout allowed.",
            n_trials=USPS_N,
            params=ssc_params(variant="E8"),
            dataset_version="libsvm",
            timeout=TIMEOUT_USPS,
        ),
    ]


def extension_jobs() -> list[dict[str, Any]]:
    return [
        _job(
            method="rssc",
            dataset="JAFFE",
            factor="EXT_JAFFE_MUTUAL_KNN",
            fidelity=C,
            notes="Extension: mutual-kNN vs SSC on same F, JAFFE n=50. Category C.",
            n_trials=SHORTLIST_N,
            params=ssc_params(variant="E8"),
            dataset_version="zenodo",
        )
    ]


def run_d2_shared_f() -> dict[str, Any]:
    from baselines.spectral_clustering.spectral_clustering import (
        spectral_embedding as sc_embed,
    )
    from benchmarks import load_dataset
    from SSC_method.spectral_config import SpectralGraphConfig
    from SSC_method.spectral_embedding import embeddings_match
    from SSC_method.spectral_embedding import spectral_embedding as ssc_embed

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "factor": "D02_SHARED_F",
        "sign_convention": "largest_magnitude_positive",
        "note": "Same SpectralGraphConfig => SC F equals SSC F. Not a clustering trial.",
        "versions": {},
    }
    for version in ("olivetti", "att92"):
        X, y, meta = load_dataset("ORL", version=version)
        n_clusters = int(np.unique(y).size)
        config = SpectralGraphConfig(k=5)
        F_sc, info_sc = sc_embed(X, n_clusters=n_clusters, return_info=True)
        F_ssc, info_ssc = ssc_embed(X, n_components=n_clusters, config=config)
        payload["versions"][version] = {
            "n": int(X.shape[0]),
            "d": int(X.shape[1]),
            "c": n_clusters,
            "dataset_version": meta.get("version"),
            "checksum": meta.get("SHA256_checksum"),
            "identity": IDENTITY[("ORL", version)],
            "embeddings_match": bool(embeddings_match(F_sc, F_ssc)),
            "allclose": bool(np.allclose(F_sc, F_ssc, rtol=1e-8, atol=1e-8)),
            "max_abs_diff": float(np.max(np.abs(F_sc - F_ssc))),
            "sc_n_undirected_edges": info_sc.get("n_undirected_edges"),
            "ssc_n_undirected_edges": info_ssc.get("n_undirected_edges"),
            "sc_n_connected_components": info_sc.get("n_connected_components"),
            "ssc_n_connected_components": info_ssc.get("n_connected_components"),
            "sc_graph": info_sc.get("graph"),
            "ssc_graph": info_ssc.get("graph"),
            "sc_eigenvalues": [float(v) for v in np.asarray(info_sc["eigenvalues"]).ravel()],
            "ssc_eigenvalues": [float(v) for v in np.asarray(info_ssc["eigenvalues"]).ravel()],
            "sc_degree_mean": info_sc.get("degree_mean"),
            "ssc_degree_mean": info_ssc.get("degree_mean"),
            "original_source_label_allowed": version == "att92",
        }
        print(
            f"[D2] ORL {version}: match={payload['versions'][version]['embeddings_match']} "
            f"max_abs_diff={payload['versions'][version]['max_abs_diff']:.3e} "
            f"edges={payload['versions'][version]['sc_n_undirected_edges']} "
            f"cc={payload['versions'][version]['sc_n_connected_components']}",
            flush=True,
        )
    path = RESULTS_DIR / "d2_shared_f.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _kmeans_on_matrix(
    features: np.ndarray,
    y: np.ndarray,
    n_clusters: int,
    init: str,
    n_trials: int,
    seed_start: int = 0,
) -> dict[str, Any]:
    from sklearn.cluster import KMeans

    trials = []
    for i in range(n_trials):
        seed = seed_start + i
        model = KMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=1,
            random_state=int(seed),
            algorithm="lloyd",
        )
        labels = np.asarray(model.fit_predict(features), dtype=np.int64)
        acc = float(clustering_accuracy(y, labels))
        nmi = float(normalized_mutual_information(y, labels))
        trials.append(
            {
                "trial_index": i,
                "seed": seed,
                "acc": acc,
                "nmi": nmi,
                "kmeans_inertia": float(model.inertia_),
                "kmeans_init": init,
            }
        )
    accs = np.array([t["acc"] for t in trials], dtype=np.float64)
    nmis = np.array([t["nmi"] for t in trials], dtype=np.float64)
    inertias = np.array([t["kmeans_inertia"] for t in trials], dtype=np.float64)
    best_i = int(np.argmin(inertias))
    return {
        "init": init,
        "n_trials": n_trials,
        "acc_mean": float(accs.mean()),
        "acc_std": float(accs.std(ddof=1)) if n_trials > 1 else 0.0,
        "nmi_mean": float(nmis.mean()),
        "nmi_std": float(nmis.std(ddof=1)) if n_trials > 1 else 0.0,
        "inertia_mean": float(inertias.mean()),
        "inertia_std": float(inertias.std(ddof=1)) if n_trials > 1 else 0.0,
        "best_inertia": float(inertias[best_i]),
        "best_inertia_seed": trials[best_i]["seed"],
        "best_inertia_acc": trials[best_i]["acc"],
        "best_inertia_nmi": trials[best_i]["nmi"],
        "selection_rule": "minimum_kmeans_inertia_not_ACC",
        "trials": trials,
    }


def _find_run(factor: str, dataset: str | None = None) -> Path | None:
    if not RUNS_DIR.is_dir():
        return None
    matches: list[Path] = []
    for child in RUNS_DIR.iterdir():
        cfg_path = child / "config.yaml"
        status_path = child / "status.json"
        if not (cfg_path.is_file() and status_path.is_file()):
            continue
        config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if status.get("status") != "COMPLETED":
            continue
        if config.get("factor") != factor:
            continue
        if dataset is not None and config.get("dataset") != dataset:
            continue
        if not (child / "embedding_F.npy").is_file():
            continue
        matches.append(child)
    if not matches:
        return None
    return max(matches, key=lambda p: p.name)


def run_d10_d11() -> dict[str, Any]:
    from benchmarks import load_dataset

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        ("D01_ATT92_SC", "ORL", "att92", "D10_ATT92_SC_SAVED_F"),
        ("D01_OLIVETTI_SC", "ORL", "olivetti", "D10_OLIVETTI_SC_SAVED_F"),
        ("D12_JAFFE_SC", "JAFFE", "zenodo", "D10_JAFFE_SC_SAVED_F"),
        ("D08_E8_ATT92", "ORL", "att92", "D10_ATT92_E8_SAVED_F"),
    ]
    payload: dict[str, Any] = {
        "note": (
            "K-means on saved F. 50 random n_init=1 and 50 k-means++ n_init=1. "
            "Report mean±std over ALL trials. Best inertia is recorded separately "
            "and is NOT selected by ACC."
        ),
        "runs": {},
    }
    for factor, dataset, version, out_name in specs:
        run_dir = _find_run(factor, dataset)
        if run_dir is None:
            payload["runs"][out_name] = {"status": "SKIPPED", "reason": f"no COMPLETED {factor}"}
            print(f"[D10] SKIP {out_name}: no saved F from {factor}", flush=True)
            continue
        X, y, meta = load_dataset(dataset, version=version)
        y = np.asarray(y).reshape(-1)
        features = np.load(run_dir / "embedding_F.npy")
        n_clusters = int(np.unique(y).size)
        if features.shape[0] != y.shape[0]:
            raise RuntimeError(f"{run_dir} F rows {features.shape[0]} != y {y.shape[0]}")
        random_block = _kmeans_on_matrix(features, y, n_clusters, "random", SHORTLIST_N)
        plusplus_block = _kmeans_on_matrix(features, y, n_clusters, "k-means++", SHORTLIST_N)
        record = {
            "status": "COMPLETED",
            "source_run_id": run_dir.name,
            "source_factor": factor,
            "dataset": dataset,
            "dataset_version": version,
            "dataset_identity_status": IDENTITY[(dataset, version)],
            "paper_fidelity_category": {
                "random": A if factor.endswith("_SC") or "E8" in factor else B,
                "k-means++": B,
            },
            "n_samples": int(features.shape[0]),
            "n_components": int(features.shape[1]),
            "n_clusters": n_clusters,
            "checksum": meta.get("SHA256_checksum"),
            "random": {k: v for k, v in random_block.items() if k != "trials"},
            "kmeans_plusplus": {k: v for k, v in plusplus_block.items() if k != "trials"},
            "random_trials": random_block["trials"],
            "kmeans_plusplus_trials": plusplus_block["trials"],
        }
        out_dir = RUNS_DIR / out_name
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "metrics.json").write_text(
            json.dumps(record, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        (out_dir / "status.json").write_text(
            json.dumps({"status": "COMPLETED", "factor": out_name}, indent=2) + "\n",
            encoding="utf-8",
        )
        payload["runs"][out_name] = {
            k: v for k, v in record.items() if k not in {"random_trials", "kmeans_plusplus_trials"}
        }
        print(
            f"[D10] {out_name}: random ACC={100*random_block['acc_mean']:.1f}±{100*random_block['acc_std']:.1f} "
            f"best_inertia_ACC={100*random_block['best_inertia_acc']:.1f} "
            f"++ ACC={100*plusplus_block['acc_mean']:.1f}±{100*plusplus_block['acc_std']:.1f} "
            f"++best_inertia_ACC={100*plusplus_block['best_inertia_acc']:.1f}",
            flush=True,
        )
    path = RESULTS_DIR / "d10_d11_kmeans_on_saved_f.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _pct(mean: float | None, std: float | None, n: int | None) -> str:
    if mean is None:
        return "n/a"
    acc = 100.0 * float(mean)
    if std is None or n is None or n <= 1:
        return f"{acc:.1f} (n={n or 0})"
    return f"{acc:.1f} ± {100.0 * float(std):.1f} (n={n})"


def _inertia_from_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    inertias = [t.get("kmeans_inertia") for t in trials if t.get("kmeans_inertia") is not None]
    if not inertias:
        return {}
    best_i = int(np.argmin(np.asarray(inertias, dtype=np.float64)))
    usable = [t for t in trials if t.get("kmeans_inertia") is not None]
    best = usable[best_i]
    return {
        "best_inertia": float(best["kmeans_inertia"]),
        "best_inertia_seed": best.get("seed"),
        "best_inertia_acc": best.get("acc"),
        "best_inertia_nmi": best.get("nmi"),
        "selection_rule": "minimum_kmeans_inertia_not_ACC",
    }


def aggregate() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    if RUNS_DIR.is_dir():
        for child in sorted(RUNS_DIR.iterdir()):
            if child.is_dir() and (child / "status.json").is_file():
                loaded = load_run(child)
                if loaded is not None:
                    rows.append(loaded)

    header = [
        "run_id",
        "status",
        "factor",
        "method",
        "variant",
        "paper_fidelity_category",
        "dataset",
        "dataset_version",
        "dataset_identity_status",
        "dataset_checksum",
        "gamma",
        "k",
        "cluster_on",
        "bandwidth_rule",
        "symmetrization",
        "row_normalize",
        "kmeans_init",
        "n_trials_requested",
        "n_trials_completed",
        "acc_mean",
        "acc_std",
        "nmi_mean",
        "nmi_std",
        "acc_pct",
        "nmi_pct",
        "best_inertia",
        "best_inertia_acc",
        "irls_converged",
        "n_irls_iterations",
        "equation8_objective",
        "g_minus_f_frobenius",
        "n_connected_components",
        "n_undirected_edges",
        "w_edge_jaccard_vs_X",
        "w_identical_to_X_graph",
        "w_built_on",
        "git_head",
        "git_uncommitted_note",
        "notes",
    ]
    registry_rows: list[list[Any]] = []
    for row in rows:
        metrics = row.get("metrics") or {}
        metadata = row.get("metadata") or {}
        params = row.get("params") or {}
        cfg_path = Path(row["run_dir"]) / "config.yaml"
        config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
        data_meta = metrics.get("dataset_metadata") or {}
        trials = metrics.get("trials") or []
        inertia = _inertia_from_trials(trials)
        graph_stats = metrics.get("graph_stats") or metrics.get("shrinkage_graph_stats") or {}
        overlap = metrics.get("w_vs_x_overlap") or {}
        n_completed = int(row.get("n_trials_completed") or 0)
        acc_mean = row.get("acc_mean")
        acc_std = row.get("acc_std")
        nmi_mean = row.get("nmi_mean")
        nmi_std = row.get("nmi_std")
        registry_rows.append(
            [
                row.get("run_id"),
                row.get("status"),
                config.get("factor") or metadata.get("factor"),
                row.get("method") or config.get("method"),
                params.get("variant") or metrics.get("variant"),
                config.get("paper_fidelity_category") or metrics.get("paper_fidelity_category"),
                row.get("dataset"),
                config.get("dataset_version") or metrics.get("dataset_version"),
                config.get("dataset_identity_status") or metrics.get("dataset_identity_status"),
                metrics.get("dataset_checksum") or data_meta.get("SHA256_checksum"),
                params.get("gamma"),
                params.get("k"),
                params.get("cluster_on") or metrics.get("cluster_on"),
                params.get("bandwidth_rule") or metrics.get("bandwidth_rule"),
                params.get("symmetrization") or (metrics.get("graph") or {}).get("symmetrization"),
                params.get("row_normalize"),
                params.get("kmeans_init") or metrics.get("kmeans_init"),
                config.get("n_trials"),
                n_completed,
                acc_mean,
                acc_std,
                nmi_mean,
                nmi_std,
                _pct(acc_mean, acc_std, n_completed),
                _pct(nmi_mean, nmi_std, n_completed),
                inertia.get("best_inertia"),
                inertia.get("best_inertia_acc"),
                metrics.get("irls_converged"),
                metrics.get("n_irls_iterations"),
                metrics.get("equation8_objective"),
                metrics.get("g_minus_f_frobenius"),
                graph_stats.get("n_connected_components") or metrics.get("n_connected_components"),
                graph_stats.get("n_undirected_edges") or metrics.get("n_undirected_edges"),
                overlap.get("edge_jaccard"),
                overlap.get("identical_to_x_graph"),
                overlap.get("w_built_on"),
                metadata.get("git_head") or metrics.get("git_head"),
                metadata.get("git_uncommitted_note") or metrics.get("git_uncommitted_note"),
                config.get("notes"),
            ]
        )

    registry_path = RESULTS_DIR / "experiment_registry.csv"
    with registry_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(registry_rows)

    summary = {
        "n_runs": len(rows),
        "n_completed": sum(1 for r in rows if r.get("status") == "COMPLETED"),
        "historical_sc_orl_olivetti_n50": HISTORICAL_SC_ORL,
        "paper_sc_orl_acc": PAPER_ACC["sc"]["ORL"],
        "paper_ssc_orl_acc": PAPER_ACC["ssc"]["ORL"],
        "paper_sc_orl_nmi": PAPER_NMI["sc"]["ORL"],
        "paper_ssc_orl_nmi": PAPER_NMI["ssc"]["ORL"],
        "registry": str(registry_path),
    }
    (RESULTS_DIR / "aggregation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {registry_path} ({len(registry_rows)} rows)", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Round 2 D1–D12 diagnostics")
    parser.add_argument(
        "--skip-extension",
        action="store_true",
        help="Skip JAFFE mutual-kNN n=50 extension",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Run named phases only: d1 d2 d3 d8 d10 d12 yaleb usps ext",
    )
    args = parser.parse_args(argv)
    wanted = set(args.only) if args.only else None

    def want(name: str) -> bool:
        return wanted is None or name in wanted

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    launch_log: list[dict[str, Any]] = []

    if want("d1"):
        print("\n===== D1 dataset SC =====", flush=True)
        for job in d1_jobs():
            launch_log.append(_run_job(job))
    if want("d2"):
        print("\n===== D2 shared F / graph A / eigenvalues =====", flush=True)
        run_d2_shared_f()
    if want("d3"):
        print("\n===== D3–D6 one-factor SC on att92 =====", flush=True)
        for job in d3_d6_jobs():
            launch_log.append(_run_job(job))
    if want("d8"):
        print("\n===== D7–D9 SSC E8/E13 / IRLS on att92 =====", flush=True)
        for job in d7_d9_jobs():
            launch_log.append(_run_job(job))
    if want("d12"):
        print("\n===== D12 JAFFE shortlist n=50 =====", flush=True)
        for job in d12_jaffe_jobs():
            launch_log.append(_run_job(job))
    if want("d10"):
        print("\n===== D10/D11 k-means on saved F =====", flush=True)
        run_d10_d11()
    if want("yaleb"):
        print("\n===== YaleB n=10 E8/SC =====", flush=True)
        for job in yaleb_jobs():
            launch_log.append(_run_job(job))
    if want("usps"):
        print("\n===== USPS pilot E8/SC =====", flush=True)
        for job in usps_jobs():
            launch_log.append(_run_job(job))
    if want("ext") and not args.skip_extension:
        print("\n===== Extension mutual-kNN JAFFE n=50 =====", flush=True)
        for job in extension_jobs():
            launch_log.append(_run_job(job))
    elif want("ext") and args.skip_extension:
        print("SKIP extension by flag", flush=True)

    aggregate()
    (RESULTS_DIR / "launch_log.json").write_text(
        json.dumps(launch_log, indent=2, default=str) + "\n", encoding="utf-8"
    )
    failed = [row for row in launch_log if int(row.get("returncode") or 0) != 0]
    print(f"Round 2 launch finished. failures={len(failed)} / {len(launch_log)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
