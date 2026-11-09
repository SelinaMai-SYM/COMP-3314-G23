"""Command line for the v3 reproduction campaign."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from experiments.v3_reproduction.aggregate import aggregate
from experiments.v3_reproduction.dataset_registry import resolve_data_root
from experiments.v3_reproduction.protocol_registry import load_campaign
from experiments.v3_reproduction.resources import probe, recover
from experiments.v3_reproduction.runner import execute_dataset
from experiments.v3_reproduction.validate import validate


def _git(workspace: Path) -> tuple[str, str]:
    workspace.mkdir(parents=True, exist_ok=True)
    git_root = workspace if (workspace / ".git").exists() else Path(__file__).resolve().parents[2]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git_root, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--short"], cwd=git_root, text=True)
    return commit, dirty


def _protocols(campaign: dict) -> dict:
    raw = campaign["_protocols"]
    return {
        "n_runs": int(raw["n_runs"]),
        "n_batches_main": int(raw["n_batches_main"]),
        "n_batches_grid": int(raw["n_batches_grid"]),
        "pca_dimensions": [int(value) for value in raw["pca_dimensions"]],
        "ssc_gamma": [float(value) for value in raw["ssc_gamma"]],
        "ssc_variants": list(raw["ssc_variants"]),
        "ssc_max_iter": int(raw["ssc_max_iter"]),
        "ssc_extra_iters": int(raw["ssc_extra_iters"]),
        "ssc_tol": float(raw["ssc_tol"]),
        "ssc_eps": float(raw["ssc_eps"]),
        "spectral_k": int(raw["spectral_k"]),
        "llc_k": int(raw["llc_k"]),
        "llc_ridge": [float(value) for value in raw["llc_ridge"]],
        "llc_bandwidth_multipliers": [float(value) for value in raw["llc_bandwidth_multipliers"]],
        "slps_k": int(raw["slps_k"]),
        "slps_alpha": [float(value) for value in raw["slps_alpha"]],
        "admm_max_iter": int(raw["admm_max_iter"]),
        "admm_tol": float(raw["admm_tol"]),
        "optimality_gap_tol": float(raw["optimality_gap_tol"]),
    }


def _write_plan(campaign: dict, summary: dict) -> None:
    workspace = Path(campaign["workspace"])
    cells = summary["cells"]
    plan_dir = workspace / "runs" / "v3_reproduction"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "plan_cells.json").write_text(json.dumps(cells, indent=2))
    lines = [
        "# v3 experiment plan",
        "",
        f"Historical cells: {len(cells)}.",
        f"Executable historical cells: {sum(1 for cell in cells if cell['executable'])}.",
        "",
        "Supplemental versions are not additional historical cells.",
        "Labels are not used to choose seeds, gamma, dimension, or which YaleB preprocessing is primary.",
        "Y0 is the locked input. Y1--Y3 are diagnostics.",
        "PCA dimensions are a grid. Inertia is not compared across dimensions.",
        "SSC E8 and E13 are separate reconstructions of one SSC cell.",
        "",
    ]
    for cell in cells:
        lines.append(
            f"- {cell['cell_id']}: executable={cell['executable']} status={cell['execution_status']} blocker={cell['blocker']}"
        )
    (workspace / "docs" / "v3").mkdir(parents=True, exist_ok=True)
    (workspace / "docs" / "v3" / "experiment_plan.md").write_text("\n".join(lines) + "\n")


def _campaign(config: str, resume: bool, data_root=None, datasets=None, output=None) -> None:
    campaign = load_campaign(config)
    if data_root:
        campaign["data_root"] = data_root
    if datasets:
        campaign["include_datasets"] = datasets
    if output:
        campaign["workspace"] = str(Path(output).resolve())
    workspace = Path(campaign["workspace"])
    commit, dirty = _git(workspace)
    summary = probe(config, campaign_override=campaign, network=False)
    _write_plan(campaign, summary)
    protocols = _protocols(campaign)
    include = campaign.get("include_datasets")
    payloads = []
    for spec, record in zip(campaign["_datasets"]["specs"], summary["datasets"]):
        if include and spec["dataset_id"] not in include:
            continue
        if not record.get("available"):
            continue
        if spec.get("execute") is False:
            continue
        payloads.append(
            {
                "spec": spec,
                "dataset_id": spec["dataset_id"],
                "historical_benchmark": spec["historical_benchmark"],
                "counts_as_historical": bool(spec.get("counts_as_historical")),
                "data_root": str(resolve_data_root(campaign)),
                "runs_dir": str(workspace / "runs" / "v3_reproduction" / "jobs"),
                "code_commit": commit,
                "git_dirty": bool(dirty.strip()),
                "resume": resume,
                "source_hash": __import__("experiments.v3_reproduction.provenance", fromlist=["source_fingerprint"]).source_fingerprint(),
                "environment": __import__("experiments.v3_reproduction.provenance", fromlist=["environment_record"]).environment_record(),
                "protocols": protocols,
            }
        )
    (workspace / "runs" / "v3_reproduction" / "launch.json").write_text(
        json.dumps(
            {
                "code_commit": commit,
                "git_dirty": dirty,
                "n_payloads": len(payloads),
                "datasets": [item["dataset_id"] for item in payloads],
            },
            indent=2,
        )
    )
    workers = int(campaign.get("workers", 1))
    if workers <= 1 or len(payloads) <= 1:
        outcomes = [execute_dataset(payload) for payload in payloads]
    else:
        import multiprocessing as mp

        context = mp.get_context("spawn")
        with context.Pool(workers) as pool:
            outcomes = pool.map(execute_dataset, payloads)
    (workspace / "runs" / "v3_reproduction" / "outcomes.json").write_text(json.dumps(outcomes, indent=2))
    print(json.dumps(outcomes, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="experiments.v3_reproduction")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("resources", "plan", "campaign", "aggregate", "validate"):
        command = sub.add_parser(name)
        command.add_argument("--config", required=True)
        if name == "campaign":
            command.add_argument("--resume", action="store_true")
    rebuild = sub.add_parser("rebuild-results")
    rebuild.add_argument("--release-manifest", required=True)
    rebuild.add_argument("--output", required=True)
    run = sub.add_parser("run-experiments")
    run.add_argument("--config", required=True)
    run.add_argument("--data-root")
    run.add_argument("--datasets", nargs="+")
    run.add_argument("--output")
    run.add_argument("--resume", action="store_true")
    run.add_argument("--smoke", action="store_true")
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--dataset", default="synthetic", choices=["synthetic"])
    args = parser.parse_args(argv)
    if args.command == "rebuild-results":
        from experiments.v3_reproduction.release import rebuild as rebuild_release
        print(json.dumps(rebuild_release(args.release_manifest,args.output),indent=2)); return
    if args.command == "smoke":
        from experiments.next_round.smoke import synthetic_smoke
        print(json.dumps(synthetic_smoke(),indent=2)); return
    if args.command == "run-experiments":
        if args.smoke:
            from experiments.next_round.smoke import data_smoke
            print(json.dumps(data_smoke(args.config,args.data_root,args.datasets,args.output),indent=2))
        else:
            _campaign(args.config,args.resume,args.data_root,args.datasets,args.output)
        return
    if args.command == "resources":
        recovery = recover(args.config)
        summary = probe(args.config)
        print(
            f"cells={summary['n_historical_cells']} executable={summary['n_executable_cells']} "
            f"recovered={recovery['n_sources']}"
        )
    elif args.command == "plan":
        summary = probe(args.config)
        _write_plan(load_campaign(args.config), summary)
        print(f"planned_cells={len(summary['cells'])}")
    elif args.command == "campaign":
        _campaign(args.config, args.resume)
    elif args.command == "aggregate":
        print(json.dumps(aggregate(args.config), indent=2))
    elif args.command == "validate":
        report = validate(args.config)
        print(json.dumps(report, indent=2))
        if not report["ok"]:
            sys.exit(1)
    else:
        raise SystemExit(args.command)


if __name__ == "__main__":
    main()
