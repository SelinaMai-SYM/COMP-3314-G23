"""Command line for the v2 K-means protocol campaign.

Run from the repository root:

    python -m experiments.v2_kmeans_protocol probe
    python -m experiments.v2_kmeans_protocol pilot
    python -m experiments.v2_kmeans_protocol primary --benchmark ORL --version att92
    python -m experiments.v2_kmeans_protocol gamma --benchmark ORL --version att92
    python -m experiments.v2_kmeans_protocol vanilla --benchmark ORL --version att92
    python -m experiments.v2_kmeans_protocol repeat --benchmark ORL --version att92
    python -m experiments.v2_kmeans_protocol aggregate
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import traceback

os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "8")

from experiments.v2_kmeans_protocol.aggregate_results import aggregate
from experiments.v2_kmeans_protocol.batch_repeatability import run as run_repeat
from experiments.v2_kmeans_protocol.dataset_registry import REPO_ROOT, load_registry
from experiments.v2_kmeans_protocol.gamma_runner import run as run_gamma
from experiments.v2_kmeans_protocol.make_figures import make_figures
from experiments.v2_kmeans_protocol.protocol_runner import run_primary, run_vanilla, write_failure
from experiments.v2_kmeans_protocol.verify_provenance import write_pilot_diagnosis, write_validation


def _entry(benchmark: str, version: str):
    for entry in load_registry():
        if entry.benchmark == benchmark and entry.version == version:
            return entry
    raise SystemExit(f"unknown dataset {benchmark} {version}")


def _eligible():
    return [entry for entry in load_registry() if entry.run_protocols]


def _timeout(entry, stage: str) -> int:
    large = entry.benchmark in {"YaleB", "USPS"}
    if stage == "primary":
        return 14400 if entry.benchmark == "USPS" else 7200 if large else 2400
    if stage == "gamma":
        return 43200 if entry.benchmark == "USPS" else 21600 if large else 7200
    if stage == "repeat":
        return 7200 if entry.benchmark == "USPS" else 3600
    return 3600


def _spawn(stage: str, entry, timeout: int) -> None:
    command = [
        sys.executable,
        "-m",
        "experiments.v2_kmeans_protocol",
        stage,
        "--benchmark",
        entry.benchmark,
        "--version",
        entry.version,
    ]
    print(f"START {stage} {entry.key} timeout={timeout}s", flush=True)
    try:
        completed = subprocess.run(command, cwd=str(REPO_ROOT), timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        write_failure(entry, stage, "TIMEOUT", f"{stage} exceeded {timeout}s")
        print(f"TIMEOUT {stage} {entry.key}", flush=True)
        return
    if completed.returncode != 0:
        write_failure(entry, stage, "FAILED", f"{stage} exited {completed.returncode}")
        print(f"FAILED {stage} {entry.key} code={completed.returncode}", flush=True)
        return
    print(f"DONE {stage} {entry.key}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="v2 K-means protocol campaign")
    parser.add_argument(
        "stage",
        choices=("probe", "pilot", "primary", "gamma", "vanilla", "repeat", "aggregate", "campaign"),
    )
    parser.add_argument("--benchmark")
    parser.add_argument("--version")
    parser.add_argument("--batches", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        if args.stage == "probe":
            from experiments.v2_kmeans_protocol.aggregate_results import write_dataset_status

            rows = write_dataset_status(load_registry())
            for row in rows:
                print(
                    f"{row['benchmark']} {row['dataset_version']}: {row['experiment_status']} "
                    f"n={row['n']} classes={row['n_classes']}",
                    flush=True,
                )
            return 0
        if args.stage == "pilot":
            targets = [_entry("ORL", "att92"), _entry("JAFFE", "zenodo")]
            for entry in targets:
                print(f"PILOT primary {entry.key}", flush=True)
                run_primary(entry)
            diagnosis = write_pilot_diagnosis(targets)
            print(json_dumps(diagnosis), flush=True)
            return 0 if diagnosis["all_v1_p1_match"] else 2
        if args.stage == "primary":
            run_primary(_entry(args.benchmark, args.version))
            return 0
        if args.stage == "gamma":
            run_gamma(_entry(args.benchmark, args.version))
            return 0
        if args.stage == "vanilla":
            run_vanilla(_entry(args.benchmark, args.version))
            return 0
        if args.stage == "repeat":
            entry = _entry(args.benchmark, args.version)
            run_repeat(entry, n_batches=args.batches)
            return 0
        if args.stage == "aggregate":
            summary = aggregate()
            figures = make_figures()
            validation = write_validation()
            print(summary, flush=True)
            print({"figures": figures, "validation": validation}, flush=True)
            return 0 if validation["passed"] else 2
        if args.stage == "campaign":
            for entry in _eligible():
                for stage in ("primary", "gamma", "vanilla", "repeat"):
                    _spawn(stage, entry, _timeout(entry, stage))
            return main(["aggregate"])
    except Exception as exc:  # noqa: BLE001 - the campaign must record the failure
        if args.benchmark and args.version:
            write_failure(_entry(args.benchmark, args.version), args.stage, "FAILED", f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1
    return 0


def json_dumps(payload) -> str:
    import json

    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
