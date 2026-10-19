#!/usr/bin/env python3
"""Transfer ORL-validated SSC repair settings to JAFFE, YaleB, and USPS.

Does not re-run the ORL 31-run matrix. Does not delete Phase 1 runs.
New runs go under runs/repair_round1/ with REPAIR1 ids. Registry and gap
tables are appended. The 4-page report is not rewritten here.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aggregate import load_run
from experiments.paper_reported import ACC as PAPER_ACC
from experiments.paper_reported import NMI as PAPER_NMI
from scripts.run_repair_round1_orl import (
    A,
    B,
    C,
    CONFIG_DIR,
    RESULTS_DIR,
    RUNS_DIR,
    _base_params,
    _pct,
    _run_job,
    _write_config,
)

JAFFE_N = 50
YALEB_N = 10
USPS_N = 3
CROPPED_N = 10
SEED_START = 0
JAFFE_TIMEOUT = 1800
YALEB_TIMEOUT = 1800
USPS_TIMEOUT = 3600
ROW_NORM_LIFT_PP = 5.0

IDENTITY = {
    "JAFFE": "verified_zenodo_213_not_paper_unpublished_copy",
    "ORL": "approximate_olivetti_64_to_32_not_att92_native",
    "YaleB": "approximate_dengcai32_not_claimed_sample_identity_with_paper",
    "YaleB_cropped": "obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai",
    "USPS": "verified_libsvm_9298",
}

V1_PREVIOUS = {
    "JAFFE": {
        "acc": "68.6 ± 11.3",
        "n": 50,
        "run_id": "20261020_015452__TRACKA__SSC__JAFFE__536c9eb1",
        "acc_mean_pct": 68.6,
        "protocol": "Track A/B gamma=1 E13 union kNN k=5 random K-means",
    },
    "ORL": {
        "acc": "53.9 ± 3.0",
        "n": 50,
        "run_id": "20261020_015209__TRACKA__SSC__ORL__5f95ad90",
        "acc_mean_pct": 53.9,
        "protocol": "Track A selected gamma=1e-6; gamma=1 was 53.7 ± 2.8",
    },
    "YaleB": {
        "acc": "19.7 ± 1.1",
        "n": 10,
        "run_id": "20261020_015611__TRACKA__SSC__YALEB__cff9a04e",
        "acc_mean_pct": 19.7,
        "protocol": "Track A/B gamma=1 E13 union kNN k=5 random K-means n=10",
    },
    "USPS": {
        "acc": "62.1 (n=1)",
        "n": 1,
        "run_id": "20261020_020231__TRACKA__SSC__USPS__829559a2",
        "acc_mean_pct": 62.1,
        "protocol": "Track A gamma=1 E13 n=1 (not 50)",
    },
}

PHASE1_EX1 = {
    "ORL": {
        "ssc": "20261020_015848__EX1__SSC__ORL__26fa9502",
        "rssc": "20261020_015850__EX1__RSSC__ORL__536aa460",
        "ssc_acc": "53.7 ± 2.8",
        "rssc_acc": "54.0 ± 2.8",
        "n": 50,
    },
    "JAFFE": {
        "ssc": "20261020_015852__EX1__SSC__JAFFE__63609097",
        "rssc": "20261020_015854__EX1__RSSC__JAFFE__a0e6ba16",
        "ssc_acc": "68.6 ± 11.3",
        "rssc_acc": "68.7 ± 11.3",
        "n": 50,
    },
    "YaleB": {
        "ssc": "20261020_015856__EX1__SSC__YALEB__034ffdfa",
        "rssc": "20261020_015905__EX1__RSSC__YALEB__73e58859",
        "ssc_acc": "19.7 ± 1.1",
        "rssc_acc": "19.9 ± 1.3",
        "n": 10,
    },
}

REGISTRY_HEADER = [
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

GAP_HEADER = [
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


def _job(
    dataset: str,
    factor: str,
    fidelity: str,
    notes: str,
    n_trials: int,
    params: dict[str, Any],
    *,
    method: str = "ssc",
    dataset_version: str | None = None,
    identity: str | None = None,
    timeout: int = JAFFE_TIMEOUT,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "track": "REPAIR1",
        "method": method,
        "dataset": dataset,
        "factor": factor,
        "paper_fidelity_category": fidelity,
        "dataset_identity_status": identity or IDENTITY[dataset],
        "n_trials": int(n_trials),
        "trial_seed_start": SEED_START,
        "timeout_seconds": int(timeout),
        "params": dict(params),
        "notes": notes,
        "label_informed_selection": False,
        "protocol": "R1_solve_FG_once_then_kmeans_seeds",
        "hardware_note": "8 CPU / 16 GB",
    }
    if dataset_version is not None:
        config["dataset_version"] = dataset_version
    return config


def _slug(config: dict[str, Any]) -> str:
    params = config.get("params") or {}
    version = config.get("dataset_version") or "default"
    parts = [
        str(config.get("dataset")),
        str(config.get("method")),
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


def write_named_config(config: dict[str, Any]) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"{_slug(config)}.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    return path


def launch(config: dict[str, Any]) -> dict[str, Any]:
    write_named_config(config)
    return _run_job(config)


def jaffe_shortlist() -> list[dict[str, Any]]:
    version = "zenodo"
    identity = IDENTITY["JAFFE"]
    timeout = JAFFE_TIMEOUT
    shared = "JAFFE verified Zenodo 213x676, k=5, gamma=1, G0=F, union kNN, median positive kNN squared bandwidth, raw eigenvectors, max_iter=300. Track B, no label tuning."
    return [
        _job(
            "JAFFE",
            "D12_KMEANS_F",
            C,
            f"{shared} K-means on F. Paper clusters G. C_DIAGNOSTIC.",
            JAFFE_N,
            _base_params(cluster_on="F"),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "JAFFE",
            "D12_KMEANS_G_E13",
            B,
            f"{shared} E13 printed update, cluster G. Canonical B reconstruction.",
            JAFFE_N,
            _base_params(),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "JAFFE",
            "D12_KMEANS_G_E8",
            A,
            f"{shared} E8 stationary system A=S+2*gamma*Ltilde. A_PAPER_FAITHFUL.",
            JAFFE_N,
            _base_params(variant="E8"),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "JAFFE",
            "D09_KM_PLUSPLUS",
            B,
            f"{shared} E13 with k-means++. Historical protocol is random. B_AMBIGUITY.",
            JAFFE_N,
            _base_params(kmeans_init="k-means++"),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "JAFFE",
            "D05_ROW_NORM",
            C,
            f"{shared} Row-normalized eigenvectors. ONE C_DIAGNOSTIC to test ORL 60% lift. Not the paper method.",
            JAFFE_N,
            _base_params(row_normalize=True),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
    ]


def yaleb_shortlist(*, include_row_norm: bool) -> list[dict[str, Any]]:
    version = "dengcai32"
    identity = IDENTITY["YaleB"]
    timeout = YALEB_TIMEOUT
    shared = (
        "YaleB Deng Cai 32x32 n=2414 c=38, k=5, gamma=1, G0=F, union kNN, "
        "median bandwidth, raw eigenvectors, max_iter=300. n_trials=10 (not 50). "
        "dataset_identity_status does not claim sample identity with the paper."
    )
    jobs = [
        _job(
            "YaleB",
            "D12_KMEANS_F",
            C,
            f"{shared} K-means on F. C_DIAGNOSTIC.",
            YALEB_N,
            _base_params(cluster_on="F"),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "YaleB",
            "D12_KMEANS_G_E13",
            B,
            f"{shared} E13 printed update, cluster G.",
            YALEB_N,
            _base_params(),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "YaleB",
            "D12_KMEANS_G_E8",
            A,
            f"{shared} E8 stationary system. A_PAPER_FAITHFUL.",
            YALEB_N,
            _base_params(variant="E8"),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
        _job(
            "YaleB",
            "D09_KM_PLUSPLUS",
            B,
            f"{shared} E13 with k-means++. B_AMBIGUITY.",
            YALEB_N,
            _base_params(kmeans_init="k-means++"),
            dataset_version=version,
            identity=identity,
            timeout=timeout,
        ),
    ]
    if include_row_norm:
        jobs.append(
            _job(
                "YaleB",
                "D05_ROW_NORM",
                C,
                f"{shared} Row-normalized eigenvectors because JAFFE showed an ORL-scale lift. Still C_DIAGNOSTIC.",
                YALEB_N,
                _base_params(row_normalize=True),
                dataset_version=version,
                identity=identity,
                timeout=timeout,
            )
        )
    jobs.append(
        _job(
            "YaleB",
            "D01_CROPPED2414_E13",
            B,
            "YaleB cropped2414 bilinear 32x32 from Wayback CroppedYale.zip, E13 gamma=1. Not claimed identical to Deng Cai pixels.",
            CROPPED_N,
            _base_params(),
            dataset_version="cropped2414",
            identity=IDENTITY["YaleB_cropped"],
            timeout=timeout,
        )
    )
    return jobs


def usps_pilot() -> list[dict[str, Any]]:
    return [
        _job(
            "USPS",
            "D12_KMEANS_G_E13",
            B,
            "USPS LIBSVM 9298x256 E13 gamma=1 k=5 union kNN median bandwidth G0=F. PILOT 1-3 K-means inits. Sparse IRLS. TIMEOUT is a kept record. Not a 50-trial reproduction.",
            USPS_N,
            _base_params(),
            dataset_version="libsvm",
            identity=IDENTITY["USPS"],
            timeout=USPS_TIMEOUT,
        )
    ]


def extension_jobs() -> list[dict[str, Any]]:
    shared = (
        "Reliability-aware SSC: mutual kNN W on F, median bandwidth taken from "
        "the directed kNN of F before the mutual filter. Same preprocessing, "
        "k=5, gamma=1, E13, G0=F, raw eigenvectors, same seeds as the repaired SSC E13. "
        "C_DIAGNOSTIC extension, not a paper method."
    )
    return [
        _job(
            "JAFFE",
            "EXT_MUTUAL_KNN",
            C,
            f"{shared} JAFFE n=50.",
            JAFFE_N,
            _base_params(),
            method="rssc",
            dataset_version="zenodo",
            identity=IDENTITY["JAFFE"],
            timeout=JAFFE_TIMEOUT,
        ),
        _job(
            "ORL",
            "EXT_MUTUAL_KNN",
            C,
            f"{shared} ORL Olivetti n=50 paired with repair1 E13. Phase 1 EX1 was 53.7 vs 54.0.",
            50,
            _base_params(),
            method="rssc",
            dataset_version=None,
            identity=IDENTITY["ORL"],
            timeout=JAFFE_TIMEOUT,
        ),
        _job(
            "YaleB",
            "EXT_MUTUAL_KNN",
            C,
            f"{shared} YaleB Deng Cai n=10.",
            YALEB_N,
            _base_params(),
            method="rssc",
            dataset_version="dengcai32",
            identity=IDENTITY["YaleB"],
            timeout=YALEB_TIMEOUT,
        ),
    ]


def _completed_row(dataset: str, factor: str, n_trials: int, dataset_version: str | None = None) -> dict[str, Any] | None:
    if not RUNS_DIR.is_dir():
        return None
    matches = []
    for child in RUNS_DIR.iterdir():
        if not child.is_dir():
            continue
        cfg_path = child / "config.yaml"
        if not cfg_path.is_file():
            continue
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if cfg.get("dataset") != dataset:
            continue
        if cfg.get("factor") != factor:
            continue
        if int(cfg.get("n_trials") or 0) != int(n_trials):
            continue
        if dataset_version is not None and (cfg.get("dataset_version") or None) != dataset_version:
            continue
        loaded = load_run(child)
        if loaded is None:
            continue
        matches.append(loaded)
    if not matches:
        return None
    return max(matches, key=lambda r: (r.get("status") == "COMPLETED", r.get("n_trials_completed") or 0))


def _acc_pct(row: dict[str, Any] | None) -> float | None:
    if row is None or row.get("acc_mean") is None:
        return None
    return 100.0 * float(row["acc_mean"])


def _checksum(metrics: dict[str, Any], data_meta: dict[str, Any]) -> Any:
    value = metrics.get("dataset_checksum") or data_meta.get("SHA256_checksum")
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return value


def _registry_row(row: dict[str, Any]) -> list[Any]:
    metrics = row.get("metrics") or {}
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
    identity = config.get("dataset_identity_status") or metrics.get("dataset_identity_status")
    notes = config.get("notes") or ""
    if identity and "dataset_identity_status=" not in notes:
        notes = f"dataset_identity_status={identity}. {notes}"
    return [
        row.get("run_id"),
        row.get("status"),
        config.get("factor"),
        params.get("variant") or metrics.get("variant"),
        config.get("paper_fidelity_category") or metrics.get("paper_fidelity_category"),
        row.get("dataset"),
        config.get("dataset_version") or metrics.get("dataset_version"),
        _checksum(metrics, data_meta),
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
        notes,
    ]


def _gap_row(row: dict[str, Any]) -> list[Any] | None:
    if row.get("status") not in {"COMPLETED", "TIMEOUT"}:
        return None
    acc_mean = row.get("acc_mean")
    if acc_mean is None and row.get("status") != "TIMEOUT":
        return None
    metrics = row.get("metrics") or {}
    params = row.get("params") or {}
    cfg_path = Path(row["run_dir"]) / "config.yaml"
    config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    dataset = str(row.get("dataset"))
    paper = PAPER_ACC.get("ssc", {}).get(dataset)
    paper_nmi = PAPER_NMI.get("ssc", {}).get(dataset)
    paper_acc = None if paper is None else float(paper[0])
    paper_nmi_pct = None if paper_nmi is None else float(paper_nmi[0])
    previous = V1_PREVIOUS.get(dataset, {})
    n_completed = int(row.get("n_trials_completed") or 0)
    acc_std = row.get("acc_std")
    nmi_mean = row.get("nmi_mean")
    nmi_std = row.get("nmi_std")
    acc_pct = None if acc_mean is None else 100.0 * float(acc_mean)
    nmi_pct = None if nmi_mean is None else 100.0 * float(nmi_mean)
    gap_paper = None if acc_pct is None or paper_acc is None else acc_pct - paper_acc
    prev_pct = previous.get("acc_mean_pct")
    gap_v1 = None if acc_pct is None or prev_pct is None else acc_pct - float(prev_pct)
    identity = config.get("dataset_identity_status")
    notes = f"[{dataset}] dataset_identity_status={identity}. {config.get('notes') or ''}"
    return [
        config.get("factor"),
        params.get("variant") or metrics.get("variant"),
        config.get("paper_fidelity_category") or metrics.get("paper_fidelity_category"),
        config.get("dataset_version") or metrics.get("dataset_version"),
        n_completed,
        acc_pct,
        None if acc_std is None else 100.0 * float(acc_std),
        nmi_pct,
        None if nmi_std is None else 100.0 * float(nmi_std),
        _pct(acc_mean, acc_std, n_completed) if acc_mean is not None else f"TIMEOUT (n={n_completed})",
        _pct(nmi_mean, nmi_std, n_completed) if nmi_mean is not None else "n/a",
        paper_acc,
        paper_nmi_pct,
        previous.get("acc"),
        previous.get("n"),
        previous.get("run_id"),
        gap_paper,
        gap_v1,
        metrics.get("irls_converged"),
        bool(acc_pct is not None and acc_pct >= 70.0),
        row.get("run_id"),
        notes,
    ]


def _append_csv(path: Path, header: list[str], rows: list[list[Any]], id_index: int) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    write_header = not path.is_file()
    if path.is_file():
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            key = header[id_index]
            for old in reader:
                existing.add(old.get(key))
    added = 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if write_header:
            writer.writerow(header)
        for item in rows:
            if item[id_index] in existing:
                continue
            writer.writerow(item)
            existing.add(item[id_index])
            added += 1
    return added


def _all_repair_rows() -> list[dict[str, Any]]:
    rows = []
    if not RUNS_DIR.is_dir():
        return rows
    for child in sorted(RUNS_DIR.iterdir()):
        if child.is_dir():
            loaded = load_run(child)
            if loaded is not None:
                rows.append(loaded)
    return rows


def _display(row: dict[str, Any] | None) -> str:
    if row is None:
        return "n/a — no completed run"
    n = int(row.get("n_trials_completed") or 0)
    if row.get("status") == "TIMEOUT":
        base = _pct(row.get("acc_mean"), row.get("acc_std"), n) if row.get("acc_mean") is not None else "no ACC"
        return f"TIMEOUT after {n} trials ({base})"
    if row.get("status") != "COMPLETED" or row.get("acc_mean") is None:
        return f"{row.get('status')} (n={n})"
    return _pct(row.get("acc_mean"), row.get("acc_std"), n)


def _nmi_display(row: dict[str, Any] | None) -> str:
    if row is None or row.get("nmi_mean") is None:
        return "n/a"
    n = int(row.get("n_trials_completed") or 0)
    return _pct(row.get("nmi_mean"), row.get("nmi_std"), n)


def _pick_closest(rows: list[dict[str, Any]], dataset: str, allowed: set[str], paper_acc: float) -> dict[str, Any] | None:
    candidates = []
    for row in rows:
        if row.get("dataset") != dataset:
            continue
        if row.get("status") != "COMPLETED" or row.get("acc_mean") is None:
            continue
        cfg = yaml.safe_load((Path(row["run_dir"]) / "config.yaml").read_text(encoding="utf-8"))
        cat = cfg.get("paper_fidelity_category")
        if cat not in allowed:
            continue
        if cfg.get("method") == "rssc":
            continue
        n_done = int(row.get("n_trials_completed") or 0)
        candidates.append(
            (n_done, abs(100.0 * float(row["acc_mean"]) - paper_acc), -float(row["acc_mean"]), row, cfg)
        )
    if not candidates:
        return None
    max_n = max(item[0] for item in candidates)
    preferred = [item for item in candidates if item[0] == max_n] if max_n >= 10 else candidates
    preferred.sort(key=lambda item: (item[1], item[2]))
    _n, _gap, _acc, row, cfg = preferred[0]
    return {"row": row, "config": cfg}


def write_comparison_tables(rows: list[dict[str, Any]]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    header = [
        "dataset",
        "n_samples_protocol",
        "paper_acc_pct_reported_not_ours",
        "paper_nmi_pct_reported_not_ours",
        "previous_v1_gamma1_acc",
        "previous_v1_n",
        "previous_v1_run_id",
        "repaired_faithful_A_method",
        "repaired_faithful_A_category",
        "repaired_faithful_A_acc",
        "repaired_faithful_A_nmi",
        "repaired_faithful_A_n",
        "repaired_faithful_A_run_id",
        "closest_AB_reconstruction_method",
        "closest_AB_category",
        "closest_AB_acc",
        "closest_AB_nmi",
        "closest_AB_n",
        "closest_AB_run_id",
        "closest_C_diagnostic_method",
        "closest_C_category",
        "closest_C_acc",
        "closest_C_nmi",
        "closest_C_n",
        "closest_C_run_id",
        "C_is_not_the_paper_method",
        "KMeans_F_acc",
        "E13_B_acc",
        "E8_A_acc",
        "kmeanspp_B_acc",
        "row_norm_C_acc",
        "shrinkage_helped_vs_KMeansF",
        "kmeanspp_transferred",
        "row_norm_transferred",
        "extension_union_SSC_acc",
        "extension_mutual_RSSC_acc",
        "extension_union_run_id",
        "extension_mutual_run_id",
        "extension_outcome",
        "remaining_gap_vs_paper_pp_using_closest_AB",
        "dataset_identity_status",
        "notes",
    ]
    table_rows: list[list[Any]] = []
    md_lines = [
        "# Repair-round 1 closest reconstruction",
        "",
        "Ranked by **paper fidelity first**, then by numerical agreement with Chang et al. (2015).",
        "Category A is the printed Equation (8) stationary update (factor 2).",
        "Category B is the printed Equation (13) reconstruction plus unspecified bandwidth / K-means init.",
        "Category C is diagnostic (K-means on F, row-normalized eigenvectors, mutual kNN). **C is never the paper method.**",
        "Paper ACC/NMI are reported from the paper, not copied as ours. Hardware: 8 CPU, 16 GB.",
        "Track B remains γ=1 with no label-informed γ selection.",
        "",
    ]
    datasets = [
        ("ORL", None, 50, IDENTITY["ORL"]),
        ("JAFFE", "zenodo", 50, IDENTITY["JAFFE"]),
        ("YaleB", "dengcai32", 10, IDENTITY["YaleB"]),
        ("USPS", "libsvm", 3, IDENTITY["USPS"]),
    ]
    for dataset, version, n_default, identity in datasets:
        paper = PAPER_ACC["ssc"][dataset]
        paper_nmi = PAPER_NMI["ssc"][dataset]
        paper_acc = float(paper[0])
        kmeans_f = _completed_row(dataset, "D12_KMEANS_F", 50 if dataset != "YaleB" else 10, version)
        e13 = _completed_row(dataset, "D12_KMEANS_G_E13", 50 if dataset == "JAFFE" else (10 if dataset == "YaleB" else (3 if dataset == "USPS" else 50)), version)
        e8 = _completed_row(dataset, "D12_KMEANS_G_E8", 50 if dataset == "JAFFE" else (10 if dataset == "YaleB" else 50), version)
        plusplus = _completed_row(dataset, "D09_KM_PLUSPLUS", 50 if dataset != "YaleB" else 10, version)
        row_norm = _completed_row(dataset, "D05_ROW_NORM", 50 if dataset != "YaleB" else 10, version)
        rssc = _completed_row(dataset, "EXT_MUTUAL_KNN", 50 if dataset != "YaleB" else 10, version)
        faithful = e8
        closest_ab = _pick_closest(rows, dataset, {"A_PAPER_FAITHFUL", "B_AMBIGUITY"}, paper_acc)
        closest_c = _pick_closest(rows, dataset, {"C_DIAGNOSTIC"}, paper_acc)
        e13_pct = _acc_pct(e13)
        f_pct = _acc_pct(kmeans_f)
        e8_pct = _acc_pct(e8)
        pp_pct = _acc_pct(plusplus)
        rn_pct = _acc_pct(row_norm)
        shrinkage_helped = None
        if f_pct is not None and e13_pct is not None:
            shrinkage_helped = bool(e13_pct - f_pct >= 1.0)
        kmeanspp_transferred = None
        if e13_pct is not None and pp_pct is not None:
            kmeanspp_transferred = bool(pp_pct - e13_pct >= 3.0)
        row_norm_transferred = None
        if e13_pct is not None and rn_pct is not None:
            row_norm_transferred = bool(rn_pct - e13_pct >= ROW_NORM_LIFT_PP)
        ext_ssc_acc = _display(e13)
        ext_rssc_acc = _display(rssc)
        if rssc is None and dataset == "ORL":
            ext_outcome = (
                f"repair1 RSSC not present; Phase 1 EX1 reused as historical pair: "
                f"SSC {PHASE1_EX1['ORL']['ssc_acc']} ({PHASE1_EX1['ORL']['ssc']}) vs "
                f"RSSC {PHASE1_EX1['ORL']['rssc_acc']} ({PHASE1_EX1['ORL']['rssc']})"
            )
        elif rssc is None or e13 is None:
            ext_outcome = "extension not completed"
        else:
            ssc_p = _acc_pct(e13)
            rssc_p = _acc_pct(rssc)
            delta = None if ssc_p is None or rssc_p is None else rssc_p - ssc_p
            if delta is None:
                ext_outcome = "extension incomplete"
            elif abs(delta) < 1.0:
                ext_outcome = f"negative/neutral: mutual-kNN {delta:+.1f} pp vs union SSC"
            elif delta > 0:
                ext_outcome = f"mutual-kNN higher by {delta:.1f} pp (still C_DIAGNOSTIC)"
            else:
                ext_outcome = f"negative: mutual-kNN lower by {abs(delta):.1f} pp"
        ab_acc = None if closest_ab is None else _acc_pct(closest_ab["row"])
        remaining = None if ab_acc is None else ab_acc - paper_acc
        prev = V1_PREVIOUS[dataset]
        table_rows.append(
            [
                dataset,
                n_default,
                f"{paper[0]:.1f} ± {paper[1]:.1f} (reported)",
                f"{paper_nmi[0]:.1f} ± {paper_nmi[1]:.1f} (reported)",
                prev["acc"],
                prev["n"],
                prev["run_id"],
                "SSC E8 G0=F union kNN median bandwidth k=5 gamma=1 random K-means" if faithful else "n/a",
                "A_PAPER_FAITHFUL" if faithful else "n/a",
                _display(faithful),
                _nmi_display(faithful),
                None if faithful is None else faithful.get("n_trials_completed"),
                None if faithful is None else faithful.get("run_id"),
                None if closest_ab is None else closest_ab["config"].get("factor"),
                None if closest_ab is None else closest_ab["config"].get("paper_fidelity_category"),
                None if closest_ab is None else _display(closest_ab["row"]),
                None if closest_ab is None else _nmi_display(closest_ab["row"]),
                None if closest_ab is None else closest_ab["row"].get("n_trials_completed"),
                None if closest_ab is None else closest_ab["row"].get("run_id"),
                None if closest_c is None else closest_c["config"].get("factor"),
                None if closest_c is None else closest_c["config"].get("paper_fidelity_category"),
                None if closest_c is None else _display(closest_c["row"]),
                None if closest_c is None else _nmi_display(closest_c["row"]),
                None if closest_c is None else closest_c["row"].get("n_trials_completed"),
                None if closest_c is None else closest_c["row"].get("run_id"),
                "YES — C is diagnostic only; never call it the paper method",
                _display(kmeans_f),
                _display(e13),
                _display(e8),
                _display(plusplus),
                _display(row_norm),
                shrinkage_helped,
                kmeanspp_transferred,
                row_norm_transferred,
                ext_ssc_acc,
                ext_rssc_acc,
                None if e13 is None else e13.get("run_id"),
                None if rssc is None else rssc.get("run_id"),
                ext_outcome,
                remaining,
                identity,
                prev["protocol"],
            ]
        )
        md_lines.extend(
            [
                f"## {dataset}",
                "",
                f"- Paper (reported, not ours): ACC {paper[0]:.1f}±{paper[1]:.1f}, NMI {paper_nmi[0]:.1f}±{paper_nmi[1]:.1f}.",
                f"- Previous v1 γ=1: {prev['acc']} (n={prev['n']}, `{prev['run_id']}`).",
                f"- Dataset identity: `{identity}`.",
                f"- **A faithful (E8):** {_display(e8)} NMI {_nmi_display(e8)}"
                + (f" `{e8['run_id']}`" if e8 else ""),
                f"- **Closest A/B reconstruction:** "
                + (
                    f"{closest_ab['config'].get('factor')} / {closest_ab['config'].get('paper_fidelity_category')} "
                    f"{_display(closest_ab['row'])} `{closest_ab['row']['run_id']}`"
                    if closest_ab
                    else "n/a"
                ),
                f"- **Closest C diagnostic (NOT the paper method):** "
                + (
                    f"{closest_c['config'].get('factor')} {_display(closest_c['row'])} `{closest_c['row']['run_id']}`"
                    if closest_c
                    else "n/a"
                ),
                f"- KMeans(F): {_display(kmeans_f)}. E13: {_display(e13)}. k-means++: {_display(plusplus)}. row-norm: {_display(row_norm)}.",
                f"- Shrinkage helped vs KMeans(F): {shrinkage_helped}. k-means++ transferred (≥3pp): {kmeanspp_transferred}. row-norm transferred (≥{ROW_NORM_LIFT_PP:.0f}pp): {row_norm_transferred}.",
                f"- Extension union vs mutual: {ext_ssc_acc} vs {ext_rssc_acc}. {ext_outcome}.",
                f"- Remaining gap vs paper using closest A/B: {remaining if remaining is None else f'{remaining:.1f} pp'}.",
                "",
            ]
        )
    csv_path = RESULTS_DIR / "reproduction_comparison.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(table_rows)
    tex_path = RESULTS_DIR / "reproduction_comparison.tex"
    tex = [
        r"% Explicit labels: C is never the paper-faithful method.",
        r"% Paper ACC/NMI are reported from Chang et al. 2015, not our numbers.",
        r"\begin{tabular}{lcccccc}",
        r"\hline",
        r"Dataset & Paper ACC (reported) & Previous v1 $\gamma{=}1$ & Repaired faithful A (E8) & Closest A/B reconstruction & Closest C diagnostic (not paper) & $n$ \\",
        r"\hline",
    ]
    for item in table_rows:
        closest_ab = item[15] if item[15] else "n/a"
        closest_ab_cat = item[14] if item[14] else "n/a"
        closest_c = item[21] if item[21] else "n/a"
        closest_c_method = item[19] if item[19] else "n/a"
        tex.append(
            f"{item[0]} & {item[2]} & {item[4]} & {item[9]} & {closest_ab} "
            f"({closest_ab_cat}) & {closest_c} ({closest_c_method}; not paper) & {item[1]} \\\\"
        )
    tex.extend([r"\hline", r"\end{tabular}", ""])
    tex_path.write_text("\n".join(tex), encoding="utf-8")
    auto_md = RESULTS_DIR / "closest_reconstruction_auto.md"
    auto_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"wrote {csv_path}", flush=True)
    print(f"wrote {tex_path}", flush=True)
    print(f"wrote {auto_md} (docs/repair_round1_closest_reconstruction.md is authored separately)", flush=True)


def aggregate_append() -> None:
    rows = _all_repair_rows()
    registry_rows = [_registry_row(row) for row in rows]
    gap_rows = []
    for row in rows:
        gap = _gap_row(row)
        if gap is not None:
            gap_rows.append(gap)
    n_reg = _append_csv(RESULTS_DIR / "experiment_registry.csv", REGISTRY_HEADER, registry_rows, 0)
    n_gap = _append_csv(RESULTS_DIR / "paper_gap_analysis.csv", GAP_HEADER, gap_rows, -2)
    write_comparison_tables(rows)
    summary_path = RESULTS_DIR / "aggregation_summary.json"
    previous = {}
    if summary_path.is_file():
        previous = json.loads(summary_path.read_text(encoding="utf-8"))
    previous.update(
        {
            "n_runs_repair_round1": len(rows),
            "n_completed_repair_round1": sum(1 for r in rows if r.get("status") == "COMPLETED"),
            "n_timeout_repair_round1": sum(1 for r in rows if r.get("status") == "TIMEOUT"),
            "registry_appended_rows": n_reg,
            "gap_appended_rows": n_gap,
            "hardware": "8 CPU / 16 GB",
            "transfer_note": (
                "JAFFE/YaleB/USPS and extension rows were appended. "
                "ORL 31-run matrix was not re-run. C is never labeled faithful."
            ),
        }
    )
    summary_path.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
    print(f"appended {n_reg} registry rows, {n_gap} gap rows", flush=True)


def _row_norm_transferred() -> bool:
    e13 = _completed_row("JAFFE", "D12_KMEANS_G_E13", JAFFE_N, "zenodo")
    row_norm = _completed_row("JAFFE", "D05_ROW_NORM", JAFFE_N, "zenodo")
    e13_pct = _acc_pct(e13)
    rn_pct = _acc_pct(row_norm)
    if e13_pct is None or rn_pct is None:
        print("JAFFE row-norm transfer undecided (missing ACC); skipping YaleB row-norm.", flush=True)
        return False
    lift = rn_pct - e13_pct
    transferred = lift >= ROW_NORM_LIFT_PP
    print(
        f"JAFFE row-norm ACC={rn_pct:.1f} vs E13 {e13_pct:.1f} lift={lift:.1f}pp "
        f"threshold={ROW_NORM_LIFT_PP:.1f} transferred={transferred}",
        flush=True,
    )
    return transferred


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Transfer repair-round 1 SSC settings beyond ORL.")
    parser.add_argument(
        "--stage",
        choices=("jaffe", "yaleb", "usps", "extension", "aggregate", "all"),
        default="all",
    )
    args = parser.parse_args(argv)
    os.environ.setdefault("OMP_NUM_THREADS", "8")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
    os.environ.setdefault("MKL_NUM_THREADS", "8")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "8")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.stage in {"jaffe", "all"}:
        for config in jaffe_shortlist():
            result = launch(config)
            if result.get("returncode") not in (0, None) and not result.get("reused_run_id"):
                print(f"WARNING non-zero exit for JAFFE {config.get('factor')}", flush=True)
        aggregate_append()
    if args.stage in {"yaleb", "all"}:
        include_row_norm = _row_norm_transferred()
        for config in yaleb_shortlist(include_row_norm=include_row_norm):
            result = launch(config)
            if result.get("returncode") not in (0, None) and not result.get("reused_run_id"):
                print(f"WARNING non-zero exit for YaleB {config.get('factor')}", flush=True)
        aggregate_append()
    if args.stage in {"usps", "all"}:
        for config in usps_pilot():
            result = launch(config)
            if result.get("returncode") not in (0, None) and not result.get("reused_run_id"):
                print(f"WARNING non-zero exit for USPS {config.get('factor')} (TIMEOUT is kept)", flush=True)
        aggregate_append()
    if args.stage in {"extension", "all"}:
        for config in extension_jobs():
            result = launch(config)
            if result.get("returncode") not in (0, None) and not result.get("reused_run_id"):
                print(f"WARNING non-zero exit for extension {config.get('dataset')}", flush=True)
        aggregate_append()
    if args.stage == "aggregate":
        aggregate_append()
    return 0


if __name__ == "__main__":
    sys.exit(main())
