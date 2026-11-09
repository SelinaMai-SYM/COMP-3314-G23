"""Provenance checks. v1 metrics are a diagnostic reference, not a result source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from experiments.paper_reported import ACC, NMI
from experiments.v2_kmeans_protocol.aggregate_results import RESULTS, load_completed_trials
from experiments.v2_kmeans_protocol.dataset_registry import REPO_ROOT, DatasetEntry, load_features, load_registry
from experiments.v2_kmeans_protocol.paper_comparison import paper_stat
from experiments.v2_kmeans_protocol.protocol_runner import read_trials, trials_path
from experiments.v2_kmeans_protocol.representation_cache import MANIFEST_ROOT
from experiments.v2_kmeans_protocol.select_best_inertia import select_min_inertia

V1_METRICS = {
    ("ORL", "att92"): {
        "ssc": REPO_ROOT
        / "runs/strict_paper/20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41/metrics.json",
        "sc": REPO_ROOT
        / "runs/strict_paper/20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce/metrics.json",
    },
    ("JAFFE", "zenodo"): {
        "ssc": REPO_ROOT
        / "runs/strict_paper/20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d/metrics.json",
        "sc": REPO_ROOT
        / "runs/strict_paper/20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b/metrics.json",
    },
}


def _close(left: float, right: float, atol: float = 1e-6, rtol: float = 1e-5) -> bool:
    return abs(left - right) <= max(atol, rtol * max(abs(left), abs(right)))


def check_paper_trace() -> list[str]:
    problems = []
    for method in ("sc", "ssc"):
        for benchmark, (mean, sd) in ACC[method].items():
            got_mean, got_sd = paper_stat("acc", method, benchmark)
            if (got_mean, got_sd) != (mean, sd):
                problems.append(f"ACC mismatch {method} {benchmark}: yaml {(got_mean, got_sd)} module {(mean, sd)}")
        for benchmark, (mean, sd) in NMI[method].items():
            got_mean, got_sd = paper_stat("nmi", method, benchmark)
            if (got_mean, got_sd) != (mean, sd):
                problems.append(f"NMI mismatch {method} {benchmark}: yaml {(got_mean, got_sd)} module {(mean, sd)}")
    return problems


def _indexed(rows: list[dict[str, str]], **filters: str) -> dict[int, dict[str, str]]:
    chosen = {}
    for row in rows:
        if row.get("experiment_status") != "COMPLETED":
            continue
        if all(row.get(key) == value for key, value in filters.items()):
            chosen[int(row["seed"])] = row
    return chosen


def diagnose_entry(entry: DatasetEntry) -> dict[str, Any]:
    """Compare our P1 trials with the v1 random Lloyd metrics for this version."""
    paths = V1_METRICS.get((entry.benchmark, entry.version))
    report: dict[str, Any] = {
        "benchmark": entry.benchmark,
        "dataset_version": entry.version,
        "reference_present": paths is not None and all(path.is_file() for path in paths.values()),
    }
    if not report["reference_present"]:
        report["matches_v1_random_lloyd"] = False
        report["reason"] = "v1 metrics.json is missing"
        return report
    ours = read_trials(trials_path(entry))
    ssc_ref = json.loads(paths["ssc"].read_text(encoding="utf-8"))
    sc_ref = json.loads(paths["sc"].read_text(encoding="utf-8"))
    our_g = _indexed(ours, representation="G", initialization_label="RANDOM", gamma="1", batch_id="0")
    our_f = _indexed(ours, representation="F", initialization_label="RANDOM", gamma="NA", batch_id="0")
    mismatches = []
    for trial in ssc_ref["trials"]:
        seed = int(trial["seed"])
        if seed not in our_g or seed not in our_f:
            mismatches.append({"seed": seed, "missing": True})
            continue
        pairs = {
            "G_inertia": (float(our_g[seed]["inertia"]), float(trial["kmeans_inertia_G"])),
            "G_acc": (float(our_g[seed]["acc"]), float(trial["acc"])),
            "G_nmi": (float(our_g[seed]["nmi"]), float(trial["nmi"])),
            "F_inertia": (float(our_f[seed]["inertia"]), float(trial["kmeans_inertia_F"])),
        }
        sc_trial = next(item for item in sc_ref["trials"] if int(item["seed"]) == seed)
        pairs["F_acc"] = (float(our_f[seed]["acc"]), float(sc_trial["acc"]))
        pairs["F_nmi"] = (float(our_f[seed]["nmi"]), float(sc_trial["nmi"]))
        bad = {name: values for name, values in pairs.items() if not _close(*values)}
        if bad:
            mismatches.append({"seed": seed, "bad": {name: values for name, values in bad.items()}})
    report["n_mismatched_seeds"] = len(mismatches)
    report["matches_v1_random_lloyd"] = len(mismatches) == 0 and len(our_g) == 50 and len(our_f) == 50
    report["mismatch_preview"] = mismatches[:5]
    report["our_g_acc_mean"] = float(np.mean([float(row["acc"]) for row in our_g.values()])) if our_g else None
    report["v1_g_acc_mean"] = float(ssc_ref["acc_mean"])
    report["our_f_acc_mean"] = float(np.mean([float(row["acc"]) for row in our_f.values()])) if our_f else None
    report["v1_f_acc_mean"] = float(sc_ref["acc_mean"])
    if not report["matches_v1_random_lloyd"]:
        report["prepare_ssc_family"] = _compare_prepare_ssc_family(entry)
    else:
        report["prepare_ssc_family"] = {"skipped": True, "reason": "per-seed v1 metrics already match"}
    return report


def _compare_prepare_ssc_family(entry: DatasetEntry) -> dict[str, Any]:
    """One upstream check used only when the historical metrics do not match."""
    from experiments.methods import prepare_ssc_family
    from experiments.v2_kmeans_protocol.kmeans_trials import RANDOM, fit_lloyd, sha256_array
    from experiments.v2_kmeans_protocol.representation_cache import gamma_token

    features, labels, _meta = load_features(entry)
    n_clusters = int(np.unique(labels).size)
    prepared = prepare_ssc_family(
        features,
        n_clusters=n_clusters,
        gamma=1.0,
        k=5,
        mutual=False,
        max_iter=300,
        tol=1e-6,
        variant="E8",
        cluster_on="G",
        bandwidth_rule="median_positive_knn_squared_distance",
        row_normalize=False,
        g_init="F",
        g_init_seed=0,
        g_init_scale=1e-3,
        zero_residual_floor="median_pairwise",
        kmeans_init="random",
        eps=1e-8,
        symmetrization="union",
        laplacian="symmetric_normalized_eq4",
    )
    manifest_path = MANIFEST_ROOT / f"{entry.key}__g{gamma_token(1.0)}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    f_hash = sha256_array(prepared.embedding)
    g_hash = sha256_array(prepared.shrunk)
    ours_g = fit_lloyd(prepared.shrunk, n_clusters, 0, RANDOM)
    return {
        "f_sha_matches_manifest": manifest.get("f_sha256") == f_hash,
        "g_sha_matches_manifest": manifest.get("g_sha256") == g_hash,
        "prepare_f_sha256": f_hash,
        "prepare_g_sha256": g_hash,
        "manifest_f_sha256": manifest.get("f_sha256"),
        "manifest_g_sha256": manifest.get("g_sha256"),
        "prepare_seed0_G_inertia": ours_g["inertia"],
        "solver_converged": bool(prepared.extra.get("irls_converged")),
        "solver_iterations": prepared.extra.get("n_irls_iterations"),
    }


def check_trial_integrity() -> list[str]:
    problems = []
    entries = [entry for entry in load_registry() if entry.run_protocols]
    for entry in entries:
        rows = [row for row in read_trials(trials_path(entry)) if row.get("experiment_status") == "COMPLETED"]
        for representation, gamma, family in (
            ("F", "NA", "RANDOM"),
            ("G", "1", "RANDOM"),
            ("F", "NA", "SKLEARN_GREEDY_KMEANSPP"),
            ("G", "1", "SKLEARN_GREEDY_KMEANSPP"),
        ):
            group = [
                row
                for row in rows
                if row["representation"] == representation
                and row["gamma"] == gamma
                and row["initialization_label"] == family
                and row["batch_id"] == "0"
            ]
            if not group:
                continue
            if len(group) != 50:
                problems.append(f"{entry.key} {representation} {family} has {len(group)} primary trials")
                continue
            parsed = [
                {"inertia": float(row["inertia"]), "seed": int(row["seed"]), "acc": float(row["acc"])}
                for row in group
            ]
            selected = select_min_inertia(parsed)
            if float(selected["inertia"]) != min(float(row["inertia"]) for row in group):
                problems.append(f"{entry.key} {representation} {family} best inertia is not the minimum")
            if family == "RANDOM":
                seeds = {int(row["seed"]) for row in group}
                if seeds != set(range(50)):
                    problems.append(f"{entry.key} {representation} random seeds are not 0..49")
    counted = load_completed_trials(entries)
    if len(counted) != sum(len(read_trials(trials_path(entry))) for entry in entries):
        problems.append("aggregated trial count does not match saved trial files")
    return problems


def write_pilot_diagnosis(entries: list[DatasetEntry]) -> dict[str, Any]:
    payload = {
        "paper_trace_problems": check_paper_trace(),
        "datasets": [diagnose_entry(entry) for entry in entries],
    }
    payload["all_v1_p1_match"] = all(item.get("matches_v1_random_lloyd") for item in payload["datasets"])
    path = RESULTS / "pilot_diagnosis.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_validation() -> dict[str, Any]:
    problems = check_paper_trace() + check_trial_integrity()
    payload = {"problems": problems, "passed": not problems}
    (RESULTS / "validation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


__all__ = [
    "check_paper_trace",
    "check_trial_integrity",
    "diagnose_entry",
    "write_pilot_diagnosis",
    "write_validation",
]
