#!/usr/bin/env python3
"""Run one experiment config from the v1 root and write a complete run directory."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import DatasetUnavailable, load_dataset
from experiments.io import RunWriter, config_hash, make_run_id, _token
from experiments.methods import (
    CACHEABLE,
    STATELESS,
    cluster_prepared,
    evaluate_labels,
    prepare_method,
    run_stateless_method,
)
from experiments.perturbations import apply_perturbation
from experiments.protocol import METHOD_STATUS, SHORT_METHOD


VALID_FIDELITY = {"A_PAPER_FAITHFUL", "B_AMBIGUITY", "C_DIAGNOSTIC"}


def _git_state(root: Path) -> dict[str, Any]:
    import subprocess

    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        porcelain = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001 - environment note must not abort a run
        return {
            "git_head": None,
            "git_branch": None,
            "git_uncommitted": None,
            "git_uncommitted_note": f"unavailable: {type(exc).__name__}: {exc}",
            "git_status_porcelain": "",
        }
    dirty = bool(porcelain.strip())
    return {
        "git_head": head,
        "git_branch": branch,
        "git_uncommitted": dirty,
        "git_uncommitted_note": (
            "working tree has uncommitted changes; numbers are from this dirty tree"
            if dirty
            else "clean"
        ),
        "git_status_porcelain": porcelain.strip()[:8000],
    }


def _tagged_run_id(track: str, dataset: str, factor: str, hashed: str, when: datetime) -> str:
    stamp = when.strftime("%Y%m%d_%H%M%S")
    return f"{stamp}__{_token(track)}__{_token(dataset)}__{_token(factor)}__{hashed}"


class TimeoutError_(Exception):
    pass


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("config must be a mapping")
    required = ("track", "method", "dataset", "n_trials")
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"config missing {missing}")
    return config


def _unique_run_dir(runs_root: Path, run_id: str) -> Path:
    candidate = runs_root / run_id
    if not candidate.exists():
        return candidate
    for suffix in range(2, 1000):
        alt = runs_root / f"{run_id}_{suffix}"
        if not alt.exists():
            return alt
    raise RuntimeError("could not allocate a unique run directory")


def run_config(config: dict[str, Any], runs_root: Path) -> Path:
    method = str(config["method"])
    dataset_name = str(config["dataset"])
    track = str(config["track"])
    n_trials = int(config["n_trials"])
    timeout_seconds = config.get("timeout_seconds")
    deadline = None if timeout_seconds is None else time.monotonic() + float(timeout_seconds)
    params = dict(config.get("params") or {})
    perturbation_spec = config.get("perturbation")
    seed_start = int(config.get("trial_seed_start", 0))
    dataset_version = config.get("dataset_version")
    fidelity = config.get("paper_fidelity_category")
    if fidelity is not None and fidelity not in VALID_FIDELITY:
        raise ValueError(
            f"paper_fidelity_category must be one of {sorted(VALID_FIDELITY)}; got {fidelity!r}"
        )
    hashed = config_hash(config)
    started = datetime.now().astimezone()
    if track.upper() in {"REPAIR1", "ROUND2", "STRICT_REPRO", "STRICT_PAPER"}:
        factor = str(config.get("factor") or params.get("variant") or method)
        run_id = _tagged_run_id(track, dataset_name, factor, hashed, started)
    else:
        run_id = make_run_id(track, SHORT_METHOD.get(method, method), dataset_name, hashed, when=started)
    git_state = _git_state(ROOT)
    run_dir = _unique_run_dir(Path(runs_root), run_id)
    writer = RunWriter(run_dir)
    writer.write_config(config)
    writer.write_environment({"run_id": run_id, **git_state})
    writer.write_metadata(
        {
            "run_id": run_id,
            "config_hash": hashed,
            "track": track,
            "method": method,
            "dataset": dataset_name,
            "dataset_version": dataset_version,
            "dataset_identity_status": config.get("dataset_identity_status"),
            "factor": config.get("factor"),
            "variant": params.get("variant"),
            "paper_fidelity_category": fidelity,
            "implementation_status": METHOD_STATUS.get(method, "UNKNOWN"),
            "created_at": started.isoformat(timespec="seconds"),
            "selection_uses_labels": bool(config.get("label_informed_selection", track.upper().startswith("TRACKA") or track.upper() == "TRACK_A" or "TRACKA" in track.upper())),
            "notes": config.get("notes", ""),
            **git_state,
        }
    )
    writer.write_status("PLANNED", run_id=run_id)
    writer.capture_stdio()

    interrupted = {"flag": False}

    def _on_signal(signum, _frame):
        interrupted["flag"] = True
        interrupted["signum"] = signum

    previous_int = signal.signal(signal.SIGINT, _on_signal)
    previous_term = signal.signal(signal.SIGTERM, _on_signal)
    status_written = False
    try:
        if method == "spls":
            writer.write_status(
                "SKIPPED",
                reason="SPLS is NOT_IMPLEMENTED; no substitute numbers",
            )
            writer.write_metrics({"n_trials_requested": n_trials, "n_trials_completed": 0, "reason": "NOT_IMPLEMENTED"})
            status_written = True
            return run_dir

        print(f"[{run_id}] loading {dataset_name} version={dataset_version}", flush=True)
        try:
            if dataset_version in (None, ""):
                X, y, data_meta = load_dataset(dataset_name)
            else:
                X, y, data_meta = load_dataset(dataset_name, version=str(dataset_version))
        except DatasetUnavailable as exc:
            writer.write_status("SKIPPED", reason=str(exc))
            writer.write_metrics({"n_trials_requested": n_trials, "n_trials_completed": 0, "reason": str(exc)})
            status_written = True
            return run_dir

        writer.write_status("RUNNING")
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)
        n_clusters = int(np.unique(y).size)
        X_used, perturb_info = apply_perturbation(X, perturbation_spec)
        print(
            f"[{run_id}] n={X_used.shape[0]} d={X_used.shape[1]} c={n_clusters} "
            f"method={method} trials={n_trials}",
            flush=True,
        )

        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError_("timeout before any trial")

        prepared = None
        extra_global: dict[str, Any] = {
            "perturbation": perturb_info,
            "dataset_metadata": {k: data_meta[k] for k in data_meta if k != "archive_path"},
            "dataset_identity_status": config.get("dataset_identity_status"),
            "paper_fidelity_category": fidelity,
            "hardware_note": "8 CPU / 16 GB target; see environment.json",
            **git_state,
        }
        if method in CACHEABLE:
            graph_spec = perturbation_spec if perturbation_spec and perturbation_spec.get("type") == "graph_drop" else None
            prepared = prepare_method(method, X_used, n_clusters, params, perturbation=graph_spec)
            extra_global.update(prepared.extra)
            if prepared.embedding is not None:
                np.save(run_dir / "embedding_F.npy", prepared.embedding)
            if prepared.shrunk is not None:
                np.save(run_dir / "embedding_G.npy", prepared.shrunk)
            if prepared.history:
                writer.write_objective_history(prepared.history)
            print(
                f"[{run_id}] prepared {method} in "
                f"{prepared.extra.get('runtime_irls_seconds', prepared.extra.get('runtime_embedding_seconds', 'n/a'))}s",
                flush=True,
            )
        elif method not in STATELESS:
            raise KeyError(f"unknown method {method}")

        trials: list[dict[str, Any]] = []

        def _flush_metrics(partial: bool) -> None:
            accs = np.array([t["acc"] for t in trials], dtype=np.float64)
            nmis = np.array([t["nmi"] for t in trials], dtype=np.float64)
            metrics = {
                "n_samples": int(X_used.shape[0]),
                "n_features": int(X_used.shape[1]),
                "n_clusters": n_clusters,
                "n_trials_requested": n_trials,
                "n_trials_completed": len(trials),
                "partial": partial,
                "trial_seeds": [t["seed"] for t in trials],
                "acc_mean": float(accs.mean()) if trials else None,
                "acc_std": float(accs.std(ddof=1)) if len(trials) > 1 else (0.0 if trials else None),
                "nmi_mean": float(nmis.mean()) if trials else None,
                "nmi_std": float(nmis.std(ddof=1)) if len(trials) > 1 else (0.0 if trials else None),
                "runtime_seconds_mean": float(np.mean([t["runtime_seconds"] for t in trials])) if trials else None,
                "trials": trials,
                "params": params,
                "paper_fidelity_category": fidelity,
                "dataset_version": dataset_version,
                "dataset_checksum": extra_global.get("dataset_metadata", {}).get("SHA256_checksum")
                if isinstance(extra_global.get("dataset_metadata"), dict)
                else None,
                "factor": config.get("factor"),
                "variant": params.get("variant") or extra_global.get("variant"),
                "gamma": params.get("gamma"),
                **extra_global,
            }
            writer.write_metrics(metrics)

        for i in range(n_trials):
            if interrupted["flag"]:
                _flush_metrics(partial=True)
                raise KeyboardInterrupt
            if deadline is not None and time.monotonic() > deadline:
                _flush_metrics(partial=True)
                raise TimeoutError_(f"timeout after {len(trials)} completed trials")
            seed = seed_start + i
            t0 = time.perf_counter()
            if prepared is not None:
                labels, trial_extra = cluster_prepared(prepared, n_clusters, seed)
            else:
                labels, trial_extra = run_stateless_method(method, X_used, n_clusters, seed, params)
            elapsed = time.perf_counter() - t0
            scores = evaluate_labels(y, labels)
            trial = {
                "trial_index": i,
                "seed": seed,
                "runtime_seconds": elapsed,
                **scores,
                **trial_extra,
            }
            trials.append(trial)
            print(
                f"[{run_id}] trial {i} seed={seed} ACC={scores['acc']:.4f} "
                f"NMI={scores['nmi']:.4f} t={elapsed:.3f}s",
                flush=True,
            )

        _flush_metrics(partial=False)
        writer.write_status(
            "COMPLETED",
            n_trials_completed=len(trials),
            n_trials_requested=n_trials,
        )
        status_written = True
        print(f"[{run_id}] COMPLETED {len(trials)}/{n_trials}", flush=True)
        return run_dir
    except TimeoutError_ as exc:
        writer.append_exception(exc)
        writer.write_status("TIMEOUT", reason=str(exc))
        status_written = True
        print(f"[{run_id}] TIMEOUT: {exc}", flush=True)
        return run_dir
    except KeyboardInterrupt as exc:
        writer.append_exception(exc)
        writer.write_status("INTERRUPTED", reason="signal")
        status_written = True
        print(f"[{run_id}] INTERRUPTED", flush=True)
        return run_dir
    except Exception as exc:  # noqa: BLE001 - record the real failure
        writer.append_exception(exc)
        writer.write_status("FAILED", reason=f"{type(exc).__name__}: {exc}")
        status_written = True
        print(f"[{run_id}] FAILED: {type(exc).__name__}: {exc}", flush=True)
        return run_dir
    finally:
        signal.signal(signal.SIGINT, previous_int)
        signal.signal(signal.SIGTERM, previous_term)
        if not status_written:
            try:
                writer.write_status("FAILED", reason="exit without status")
            except Exception:
                pass
        writer.release_stdio()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one SSC Phase 1 experiment.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    args = parser.parse_args(argv)
    config = _load_config(args.config.resolve())
    run_dir = run_config(config, args.runs_dir.resolve())
    status = (run_dir / "status.json").read_text(encoding="utf-8")
    print(run_dir)
    if '"status": "COMPLETED"' in status:
        return 0
    if '"status": "SKIPPED"' in status:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
