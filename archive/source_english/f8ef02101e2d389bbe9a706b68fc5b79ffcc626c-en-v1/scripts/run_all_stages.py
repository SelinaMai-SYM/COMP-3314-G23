#!/usr/bin/env python3
"""Execute Stage A through D. Every number comes from a real run_experiment job."""

from __future__ import annotations

import argparse
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

from experiments.protocol import GAMMA_GRID, K_SWEEP, TRACK_B_GAMMA, dimension_grid, track_b_dimension

PYTHON = sys.executable
RUNNER = ROOT / "scripts" / "run_experiment.py"
GEN_CONFIGS = ROOT / "configs" / "generated"
RUNS = ROOT / "runs"


def _write_config(name: str, config: dict[str, Any]) -> Path:
    GEN_CONFIGS.mkdir(parents=True, exist_ok=True)
    path = GEN_CONFIGS / f"{name}.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    return path


def _job(
    track: str,
    method: str,
    dataset: str,
    n_trials: int,
    timeout: int,
    params: dict | None = None,
    perturbation: dict | None = None,
    notes: str = "",
    seed_start: int = 0,
) -> dict[str, Any]:
    params = dict(params or {})
    if method in {"ssc", "rssc"}:
        params.setdefault("k", 5)
        params.setdefault("max_iter", 300)
        params.setdefault("gamma", 1.0)
    config: dict[str, Any] = {
        "track": track,
        "method": method,
        "dataset": dataset,
        "n_trials": int(n_trials),
        "trial_seed_start": int(seed_start),
        "timeout_seconds": int(timeout),
        "params": params,
        "notes": notes,
        "label_informed_selection": track.upper().startswith("TRACKA") or track.upper() == "TRACK_A",
    }
    if perturbation:
        config["perturbation"] = perturbation
    return config


def _equivalent_completed(config: dict[str, Any]) -> str | None:
    """Resume helper: skip if a completed run already matches this setting."""
    if not RUNS.is_dir():
        return None
    target_params = config.get("params") or {}
    target_perturb = config.get("perturbation")
    for child in RUNS.iterdir():
        cfg_path = child / "config.yaml"
        status_path = child / "status.json"
        metrics_path = child / "metrics.json"
        if not (cfg_path.is_file() and status_path.is_file()):
            continue
        try:
            existing = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            status = json.loads(status_path.read_text(encoding="utf-8"))
            metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.is_file() else {}
        except Exception:
            continue
        if status.get("status") != "COMPLETED":
            continue
        if existing.get("track") != config.get("track"):
            continue
        if existing.get("method") != config.get("method"):
            continue
        if existing.get("dataset") != config.get("dataset"):
            continue
        if (existing.get("params") or {}) != target_params:
            continue
        if existing.get("perturbation") != target_perturb:
            continue
        if int(metrics.get("n_trials_completed") or 0) < int(config.get("n_trials") or 0):
            continue
        return child.name
    return None


def _run_job(config: dict[str, Any], extra_timeout: int = 90) -> dict[str, Any]:
    existing = _equivalent_completed(config)
    if existing:
        print(f"SKIP already completed {existing}", flush=True)
        return {"config_path": "reused", "returncode": 0, "wall_seconds": 0.0, "reused_run_id": existing}
    slug = "__".join(
        [
            str(config["track"]),
            str(config["method"]),
            str(config["dataset"]),
            str(config.get("params", {}).get("gamma", "")),
            str(config.get("params", {}).get("k", "")),
            str(config.get("params", {}).get("n_components", "")),
            str((config.get("perturbation") or {}).get("type", "")),
            str((config.get("perturbation") or {}).get("level", "")),
            str((config.get("perturbation") or {}).get("seed", "")),
        ]
    )
    slug = slug.replace(".", "p").replace("-", "m")
    cfg_path = _write_config(slug, config)
    timeout = int(config.get("timeout_seconds") or 600) + extra_timeout
    print(f"\n=== launching {cfg_path.name} timeout={timeout}s ===", flush=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        [PYTHON, str(RUNNER), "--config", str(cfg_path), "--runs-dir", str(RUNS)],
        cwd=str(ROOT),
        capture_output=False,
        timeout=timeout,
        check=False,
    )
    elapsed = time.perf_counter() - t0
    print(f"=== finished {cfg_path.name} exit={proc.returncode} wall={elapsed:.1f}s ===", flush=True)
    return {"config_path": str(cfg_path), "returncode": proc.returncode, "wall_seconds": elapsed}


def stage_a() -> list[dict[str, Any]]:
    jobs = []
    for method in ("kmeans", "sc", "ssc"):
        params = {"k": 5, "gamma": 1.0, "max_iter": 300} if method == "ssc" else ({"k": 5} if method == "sc" else {})
        jobs.append(
            _job(
                "PILOT",
                method,
                "ORL",
                n_trials=3,
                timeout=600,
                params=params,
                notes="Stage A ORL pilot: 3 K-means inits, gamma=1, k=5",
            )
        )
    return jobs


def stage_b() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    # ORL + JAFFE: 50 trials. SSC gamma grid. KM, SC. DR baselines. LLC.
    for dataset in ("ORL", "JAFFE"):
        jobs.append(_job("TRACKA", "kmeans", dataset, 50, 1200, notes="Track A K-means 50 random inits"))
        jobs.append(_job("TRACKA", "sc", dataset, 50, 1200, {"k": 5}, notes="Track A SC; embedding once then 50 K-means"))
        for gamma in GAMMA_GRID:
            jobs.append(
                _job(
                    "TRACKA",
                    "ssc",
                    dataset,
                    50,
                    1800,
                    {"k": 5, "gamma": float(gamma)},
                    notes="Track A SSC: IRLS once per gamma, 50 K-means on G",
                )
            )
        jobs.append(_job("TRACKA", "llc", dataset, 50, 1800, {"k": 5}, notes="Track A LLC"))
        jobs.append(_job("TRACKA", "spls", dataset, 50, 60, notes="SPLS skipped"))
        # Dimension grids require n, d, c. Hard-code from manifests; LDA clips K-1.
        n_d_c = {"ORL": (400, 1024, 40), "JAFFE": (213, 676, 10)}[dataset]
        for dim in dimension_grid(*n_d_c[:2]):
            jobs.append(
                _job(
                    "TRACKA",
                    "pca_kmeans",
                    dataset,
                    50,
                    1200,
                    {"n_components": dim},
                    notes="Track A PCA-KM dimension grid, label-informed later",
                )
            )
            jobs.append(
                _job(
                    "TRACKA",
                    "pca_spectral",
                    dataset,
                    10 if dataset == "JAFFE" else 10,
                    1800,
                    {"n_components": dim, "k": 5},
                    notes="Track A PCA-SC: 10 trials per dim for selection (cost)",
                )
            )
        for dim in dimension_grid(*n_d_c, lda=True):
            jobs.append(
                _job(
                    "TRACKA",
                    "lda_kmeans",
                    dataset,
                    10,
                    1800,
                    {"n_components": dim},
                    notes="Track A LDA-KM: 10 trials per feasible dim",
                )
            )
    # YaleB: at least 10 trials for SSC gamma=1, K-means, SC.
    jobs.append(_job("TRACKA", "kmeans", "YaleB", 10, 1800, notes="Track A YaleB reduced: 10 K-means trials"))
    jobs.append(_job("TRACKA", "sc", "YaleB", 10, 2400, {"k": 5}, notes="Track A YaleB reduced: 10 SC trials"))
    jobs.append(
        _job(
            "TRACKA",
            "ssc",
            "YaleB",
            10,
            2400,
            {"k": 5, "gamma": 1.0},
            notes="Track A YaleB reduced: SSC gamma=1, 10 K-means on G",
        )
    )
    return jobs


def stage_usps() -> list[dict[str, Any]]:
    """USPS last: expensive n=9298. Timeout is a valid outcome."""
    return [
        _job(
            "TRACKA",
            "ssc",
            "USPS",
            1,
            2700,
            {"k": 5, "gamma": 1.0},
            notes="USPS SSC gamma=1, 45 min timeout, 1 clustering if IRLS finishes. Not a 9298 50-trial reproduction.",
        ),
        _job("TRACKA", "spls", "USPS", 1, 60, notes="SPLS skipped"),
        _job("TRACKA", "kmeans", "USPS", 10, 1800, notes="USPS K-means 10 trials; cheap relative to SSC"),
    ]


def stage_c() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    specs = {
        "ORL": (400, 1024, 40, 50, 1800),
        "JAFFE": (213, 676, 10, 50, 1800),
        "YaleB": (2414, 1024, 38, 10, 2400),
    }
    for dataset, (n, d, c, trials, timeout) in specs.items():
        jobs.append(_job("TRACKB", "kmeans", dataset, trials, timeout, notes="Track B K-means, no label tuning"))
        jobs.append(_job("TRACKB", "sc", dataset, trials, timeout, {"k": 5}, notes="Track B SC, k=5, no label tuning"))
        jobs.append(
            _job(
                "TRACKB",
                "ssc",
                dataset,
                trials,
                timeout,
                {"k": 5, "gamma": TRACK_B_GAMMA},
                notes="Track B SSC gamma=1 a priori",
            )
        )
        jobs.append(
            _job(
                "TRACKB",
                "pca_kmeans",
                dataset,
                trials,
                timeout,
                {"n_components": track_b_dimension(n, d, c, lda=False)},
                notes="Track B PCA-KM prespecified dimension, no labels",
            )
        )
        if dataset != "YaleB":
            jobs.append(
                _job(
                    "TRACKB",
                    "pca_spectral",
                    dataset,
                    trials,
                    timeout,
                    {"n_components": track_b_dimension(n, d, c, lda=False), "k": 5},
                    notes="Track B PCA-SC prespecified dimension",
                )
            )
            jobs.append(
                _job(
                    "TRACKB",
                    "lda_kmeans",
                    dataset,
                    trials,
                    timeout,
                    {"n_components": track_b_dimension(n, d, c, lda=True)},
                    notes="Track B LDA-KM prespecified dimension clipped to K-1",
                )
            )
            jobs.append(_job("TRACKB", "llc", dataset, trials, timeout, {"k": 5}, notes="Track B LLC"))
        jobs.append(_job("TRACKB", "spls", dataset, 1, 60, notes="SPLS skipped"))
    return jobs


def stage_d() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    # EX1 clean comparison, same gamma=1, k=5, seeds.
    for dataset, trials, timeout in (("ORL", 50, 1800), ("JAFFE", 50, 1800), ("YaleB", 10, 2400)):
        jobs.append(
            _job("EX1", "ssc", dataset, trials, timeout, {"k": 5, "gamma": 1.0}, notes="EX1 original SSC A0")
        )
        jobs.append(
            _job("EX1", "rssc", dataset, trials, timeout, {"k": 5, "gamma": 1.0}, notes="EX1 Reliability-aware SSC A1")
        )
    # EX2 Gaussian noise
    for dataset, trials in (("ORL", 20), ("JAFFE", 20)):
        for frac in (0.1, 0.3):
            for pseed in (0, 1, 2):
                perturb = {"type": "gaussian_noise", "level": frac, "seed": pseed}
                for method in ("ssc", "rssc"):
                    jobs.append(
                        _job(
                            "EX2",
                            method,
                            dataset,
                            trials,
                            1800,
                            {"k": 5, "gamma": 1.0},
                            perturbation=perturb,
                            notes=f"EX2 Gaussian noise sigma={frac}*std seed={pseed}",
                        )
                    )
    # EX3 feature corruption 10%
    for dataset, trials in (("ORL", 20), ("JAFFE", 20)):
        for pseed in (0, 1, 2):
            perturb = {"type": "feature_corruption", "level": 0.10, "seed": pseed}
            for method in ("ssc", "rssc"):
                jobs.append(
                    _job(
                        "EX3",
                        method,
                        dataset,
                        trials,
                        1800,
                        {"k": 5, "gamma": 1.0},
                        perturbation=perturb,
                        notes=f"EX3 10% features -> N(0,1) seed={pseed}",
                    )
                )
    # EX4 outliers 5%
    for dataset, trials in (("ORL", 20), ("JAFFE", 20)):
        for pseed in (0, 1, 2):
            perturb = {"type": "outlier_contamination", "level": 0.05, "seed": pseed}
            for method in ("ssc", "rssc"):
                jobs.append(
                    _job(
                        "EX4",
                        method,
                        dataset,
                        trials,
                        1800,
                        {"k": 5, "gamma": 1.0},
                        perturbation=perturb,
                        notes=f"EX4 5% samples -> N(0,10) seed={pseed}",
                    )
                )
    # EX5 graph drop 10%
    for dataset, trials in (("ORL", 20), ("JAFFE", 20)):
        for pseed in (0, 1):
            perturb = {"type": "graph_drop", "level": 0.10, "seed": pseed}
            for method in ("ssc", "rssc"):
                jobs.append(
                    _job(
                        "EX5",
                        method,
                        dataset,
                        trials,
                        1800,
                        {"k": 5, "gamma": 1.0},
                        perturbation=perturb,
                        notes=f"EX5 drop 10% of W edges seed={pseed}",
                    )
                )
    # EX6 neighborhood k
    for dataset, trials in (("ORL", 20), ("JAFFE", 20)):
        for k in K_SWEEP:
            for method in ("ssc", "rssc"):
                jobs.append(
                    _job(
                        "EX6",
                        method,
                        dataset,
                        trials,
                        1800,
                        {"k": int(k), "gamma": 1.0},
                        notes=f"EX6 k={k}",
                    )
                )
    # EX7/EX8 reuse EX1 histories and runtimes; one extra timed pair is enough.
    return jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stages", default="A,B,C,D,USPS")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    RUNS.mkdir(parents=True, exist_ok=True)
    stage_map = {"A": stage_a, "B": stage_b, "C": stage_c, "D": stage_d, "USPS": stage_usps}
    wanted = [s.strip().upper() for s in args.stages.split(",") if s.strip()]
    jobs: list[dict[str, Any]] = []
    for key in wanted:
        jobs.extend(stage_map[key]())
    print(f"planned jobs: {len(jobs)} stages={wanted}", flush=True)
    if args.dry_run:
        for job in jobs:
            print(json.dumps({k: job[k] for k in ("track", "method", "dataset", "n_trials", "params", "perturbation") if k in job or True}, default=str))
        return 0
    started = time.time()
    results = []
    for job in jobs:
        try:
            results.append(_run_job(job))
        except subprocess.TimeoutExpired as exc:
            print(f"PARENT TIMEOUT {exc}", flush=True)
            results.append({"config_path": "unknown", "returncode": -9, "wall_seconds": None, "parent_timeout": True})
        except KeyboardInterrupt:
            print("orchestrator interrupted", flush=True)
            break
    summary = {
        "n_jobs": len(jobs),
        "n_launched": len(results),
        "wall_seconds": time.time() - started,
        "results": results,
    }
    out = ROOT / "results" / "orchestrator_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"orchestrator launched {len(results)}/{len(jobs)} jobs", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
