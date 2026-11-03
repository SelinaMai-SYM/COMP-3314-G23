"""Run SSC E8 and extensions. Test accuracy is recorded after fitting.

Gamma is never chosen by ACC. The primary comparison is gamma=1. Other grid
values are stored beside it. A later analysis may mark the highest ACC as an
oracle upper bound; this script does not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import traceback
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

from SSC_method.optimizer import shrink_embedding
from benchmarks import load_dataset
from benchmarks.metrics import clustering_accuracy, normalized_mutual_information
from method_extension.common.clustering import (
    consensus_labels,
    disagreement_fraction,
    inertia_best_labels,
    kmeans_once,
)
from method_extension.common.fitting import ExtensionConfig, embed_matrix, fit_named_method
from method_extension.mutual_knn import mutual_knn_affinity
from sklearn.exceptions import ConvergenceWarning

warnings.filterwarnings("ignore", category=ConvergenceWarning)

ROOT = _ROOT
GAMMA_GRID = (1e-6, 1e-3, 1.0, 1e3, 1e6)
PRIMARY_GAMMA = 1.0
SHRINK_METHODS = (
    ("ssc", "control"),
    ("e01", "default"),
    ("e02", "default"),
    ("e03", "A"),
    ("e03", "W"),
    ("e03", "AW"),
    ("e04", "degree"),
    ("e04", "total"),
    ("e05", "fuse"),
    ("e05", "bilateral"),
    ("e06", "default"),
    ("e08", "default"),
    ("e09", "default"),
)
RUNNABLE = (
    {"dataset": "ORL", "version": "att92", "eligibility": "PAPER_RECONSTRUCTION"},
    {"dataset": "JAFFE", "version": "zenodo", "eligibility": "VERIFIED_SOURCE"},
    {"dataset": "YaleB", "version": "cropped2414", "eligibility": "PRIMARY_YALEB_VERSION"},
    {
        "dataset": "YaleB",
        "version": "dengcai32",
        "eligibility": "ALTERNATE_MATRIX_NOT_AN_INDEPENDENT_BENCHMARK",
    },
    {"dataset": "USPS", "version": "libsvm", "eligibility": "VERIFIED_SOURCE"},
    {"dataset": "BinAlpha", "version": "CANDIDATE_BIN_ALPHA", "eligibility": "NON_EXACT_DATASET"},
    {"dataset": "UMIST", "version": "precropped575", "eligibility": "NON_EXACT_DATASET"},
)
BLOCKED = (
    {
        "dataset": "MSRA50",
        "version": "",
        "eligibility": "EXCLUDED",
        "status": "BLOCKED_DATA",
        "notes": "No 1799x12 archive. Excluded, not run.",
    },
    {
        "dataset": "AR",
        "version": "",
        "eligibility": "BLOCKED",
        "status": "BLOCKED",
        "notes": (
            "Not called paper AR and not named AR100_ZENODO. Official Martinez "
            "images were not obtained. The third-party Zenodo zip is 100 identities, "
            "not 120, has no single paper preprocessing rule, and is not a licensed "
            "official redistribution."
        ),
    },
)
COLUMNS = [
    "role",
    "dataset",
    "version",
    "eligibility",
    "method",
    "variant",
    "gamma",
    "status",
    "n_trials",
    "seeds",
    "sc_acc_mean",
    "sc_acc_std",
    "sc_nmi_mean",
    "sc_nmi_std",
    "ssc_acc_mean",
    "ssc_acc_std",
    "ssc_nmi_mean",
    "ssc_nmi_std",
    "label_change_fraction",
    "n_iterations",
    "converged",
    "objective_name",
    "objective_value",
    "equation8_value",
    "relative_move",
    "graph_total_variation",
    "n_edges",
    "n_components",
    "fixed_point_residual",
    "solver",
    "fit_sec",
    "kmeans_sec",
    "data_checksum",
    "config_hash",
    "commit",
    "run_id",
    "f_source",
    "notes",
]


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def _config_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _blank() -> dict:
    return {column: "" for column in COLUMNS}


def _write_csv(path: Path, rows: list[dict]) -> None:
    lines = [",".join(COLUMNS)]
    for row in rows:
        cells = []
        for column in COLUMNS:
            value = row.get(column, "")
            text = "" if value is None else str(value)
            if any(ch in text for ch in ",\"\n"):
                text = '"' + text.replace('"', '""') + '"'
            cells.append(text)
        lines.append(",".join(cells))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mean_std(values: list[float]) -> tuple[str, str]:
    if len(values) == 0:
        return "", ""
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    if array.size < 2:
        return f"{mean:.10g}", ""
    return f"{mean:.10g}", f"{float(array.std(ddof=1)):.10g}"


def _score_many(features: np.ndarray, y: np.ndarray, n_clusters: int, seeds: list[int], init: str):
    accs = []
    nmis = []
    labels = []
    for seed in seeds:
        pred, _inertia = kmeans_once(features, n_clusters, seed, init=init)
        accs.append(clustering_accuracy(y, pred))
        nmis.append(normalized_mutual_information(y, pred))
        labels.append(pred)
    return accs, nmis, labels


def _graph_counts(affinity: sparse.spmatrix) -> tuple[int, int]:
    weights = sparse.csr_matrix(affinity)
    n_components, _labels = connected_components(weights, directed=False, return_labels=True)
    return int(weights.nnz // 2), int(n_components)


def _dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _base_row(spec, method, variant, gamma, role, commit, checksum, config_hash, seeds) -> dict:
    row = _blank()
    row.update(
        {
            "role": role,
            "dataset": spec["dataset"],
            "version": spec["version"],
            "eligibility": spec["eligibility"],
            "method": method,
            "variant": variant,
            "gamma": gamma,
            "seeds": f"{seeds[0]}-{seeds[-1]}" if seeds == list(range(seeds[0], seeds[-1] + 1)) else ",".join(map(str, seeds)),
            "data_checksum": checksum,
            "config_hash": config_hash,
            "commit": commit,
            "notes": "Objective values are not comparable across different W or alpha.",
        }
    )
    return row


def _fill_scores(row, sc, ssc, label_change, fit_sec, kmeans_sec, extra):
    sc_mean, sc_std = _mean_std(sc[0])
    scn_mean, scn_std = _mean_std(sc[1])
    g_mean, g_std = _mean_std(ssc[0])
    gn_mean, gn_std = _mean_std(ssc[1])
    row.update(
        {
            "n_trials": len(sc[0]),
            "sc_acc_mean": sc_mean,
            "sc_acc_std": sc_std,
            "sc_nmi_mean": scn_mean,
            "sc_nmi_std": scn_std,
            "ssc_acc_mean": g_mean,
            "ssc_acc_std": g_std,
            "ssc_nmi_mean": gn_mean,
            "ssc_nmi_std": gn_std,
            "label_change_fraction": "" if label_change is None else f"{label_change:.10g}",
            "fit_sec": f"{fit_sec:.6g}",
            "kmeans_sec": f"{kmeans_sec:.6g}",
        }
    )
    row.update(extra)
    return row


def run_phase(phase: str, datasets: list[dict], seeds: list[int], gammas: tuple[float, ...]) -> Path:
    commit = _git_head()
    config = ExtensionConfig(solver="original")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rows: list[dict] = []
    out_name = "pilot_matrix.csv" if phase == "pilot" else "extension_matrix.csv"
    out_path = ROOT / "results" / "extension_research" / out_name
    run_root = ROOT / "runs" / "extension_research" / phase
    if phase != "pilot":
        for blocked in BLOCKED:
            row = _blank()
            row.update(
                {
                    "role": "not_run",
                    "dataset": blocked["dataset"],
                    "version": blocked["version"],
                    "eligibility": blocked["eligibility"],
                    "method": "",
                    "status": blocked["status"],
                    "commit": commit,
                    "notes": blocked["notes"],
                    "run_id": f"{stamp}__EXT__{blocked['dataset']}__{blocked['status']}",
                }
            )
            rows.append(row)
    for spec in datasets:
        print(f"load {spec['dataset']} {spec['version']}", flush=True)
        try:
            features, labels, metadata = load_dataset(spec["dataset"], version=spec["version"])
        except Exception as exc:  # noqa: BLE001
            row = _blank()
            row.update(
                {
                    "role": "not_run",
                    "dataset": spec["dataset"],
                    "version": spec["version"],
                    "eligibility": spec["eligibility"],
                    "status": "BLOCKED_DATA",
                    "commit": commit,
                    "notes": f"{type(exc).__name__}: {exc}",
                }
            )
            rows.append(row)
            _write_csv(out_path, rows)
            continue
        y = np.asarray(labels)
        n_clusters = int(len(np.unique(y)))
        checksum = _sha(features)
        t_embed = time.perf_counter()
        control_f, _embed_info = embed_matrix(features, n_clusters, config)
        local_f, _local_info = embed_matrix(
            features, n_clusters, config, bandwidth_rule="self_tuning_zelnik_manor"
        )
        print(f"embeddings {time.perf_counter() - t_embed:.2f}s n={features.shape[0]} c={n_clusters}", flush=True)
        control_state = None
        for gamma in gammas:
            role = "primary" if float(gamma) == PRIMARY_GAMMA else "gamma_grid"
            for method, variant in SHRINK_METHODS:
                override = local_f if method == "e03" and variant in {"A", "AW"} else control_f
                payload = {
                    "dataset": spec["dataset"],
                    "version": spec["version"],
                    "method": method,
                    "variant": variant,
                    "gamma": float(gamma),
                    "k": config.k,
                    "solver_variant": "E8",
                    "laplacian_coefficient": 2,
                    "max_iter": config.max_iter,
                    "tol": config.tol,
                    "seeds": seeds,
                    "phase": phase,
                }
                config_hash = _config_hash(payload)
                run_id = f"{stamp}__EXT__{spec['dataset']}__{spec['version']}__{method}__{variant}__g{gamma:.0e}__{config_hash[:8]}"
                row = _base_row(spec, method, variant, float(gamma), role, commit, checksum, config_hash, seeds)
                row["run_id"] = run_id
                t0 = time.perf_counter()
                try:
                    state = fit_named_method(
                        method,
                        features,
                        n_clusters,
                        gamma=float(gamma),
                        variant=variant,
                        config=config,
                        embedding_override=override,
                    )
                    fit_sec = time.perf_counter() - t0
                    t1 = time.perf_counter()
                    sc = _score_many(state.embedding, y, n_clusters, seeds, "random")
                    ssc = _score_many(state.patterns, y, n_clusters, seeds, "random")
                    changes = [
                        disagreement_fraction(left, right)
                        for left, right in zip(sc[2], ssc[2])
                    ]
                    kmeans_sec = time.perf_counter() - t1
                    n_edges, n_components = _graph_counts(state.affinity)
                    status = "CONVERGED" if state.converged else "NONCONVERGED"
                    _fill_scores(
                        row,
                        sc,
                        ssc,
                        float(np.mean(changes)),
                        fit_sec,
                        kmeans_sec,
                        {
                            "status": status,
                            "n_iterations": state.n_iterations,
                            "converged": state.converged,
                            "objective_name": state.objective_name,
                            "objective_value": f"{state.objective_value:.10g}",
                            "equation8_value": f"{state.equation8_value:.10g}",
                            "relative_move": f"{state.relative_move:.10g}",
                            "graph_total_variation": f"{state.graph_total_variation:.10g}",
                            "n_edges": n_edges,
                            "n_components": n_components,
                            "fixed_point_residual": f"{state.fixed_point_residual:.10g}",
                            "solver": state.solver,
                            "f_source": state.f_source,
                        },
                    )
                    _dump_json(
                        run_root / run_id / "metrics.json",
                        {
                            "run_id": run_id,
                            "metadata_version": metadata.get("version"),
                            "metadata_checksum_field": metadata.get("SHA256_checksum"),
                            "sc_acc": sc[0],
                            "sc_nmi": sc[1],
                            "ssc_acc": ssc[0],
                            "ssc_nmi": ssc[1],
                            "status": status,
                            "info": state.info,
                            "eligibility": spec["eligibility"],
                        },
                    )
                    if method == "ssc" and float(gamma) == PRIMARY_GAMMA:
                        control_state = state
                    print(
                        f"{spec['dataset']} {spec['version']} {method} {variant} g={gamma} "
                        f"{status} SSC_ACC={row['ssc_acc_mean']} {fit_sec:.1f}s",
                        flush=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    row["status"] = "FAILED"
                    row["notes"] = f"FAILED {type(exc).__name__}: {exc}"
                    (run_root / run_id).mkdir(parents=True, exist_ok=True)
                    (run_root / run_id / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
                    print(f"FAILED {spec['dataset']} {method} {variant} {exc}", flush=True)
                rows.append(row)
                _write_csv(out_path, rows)
        if control_state is not None:
            rows.extend(
                _protocol_rows(
                    spec, control_state, y, n_clusters, seeds, commit, checksum, stamp, run_root
                )
            )
            rows.extend(
                _mutual_rows(
                    spec, features, control_state.embedding, y, n_clusters, seeds, commit, checksum, stamp, run_root, config
                )
            )
            _write_csv(out_path, rows)
        del control_f, local_f
    _write_csv(out_path, rows)
    print(f"wrote {out_path}", flush=True)
    return out_path


def _protocol_rows(spec, state, y, n_clusters, seeds, commit, checksum, stamp, run_root):
    rows = []
    protocols = {
        "random": "random",
        "kmeanspp": "k-means++",
    }
    for name, init in protocols.items():
        payload_hash = _config_hash({"e07": name, "dataset": spec["dataset"], "version": spec["version"], "seeds": seeds})
        run_id = f"{stamp}__EXT__{spec['dataset']}__{spec['version']}__e07__{name}__{payload_hash[:8]}"
        row = _base_row(spec, "E07", name, PRIMARY_GAMMA, "primary", commit, checksum, payload_hash, seeds)
        row["run_id"] = run_id
        t1 = time.perf_counter()
        sc = _score_many(state.embedding, y, n_clusters, seeds, init)
        ssc = _score_many(state.patterns, y, n_clusters, seeds, init)
        change = float(np.mean([disagreement_fraction(a, b) for a, b in zip(sc[2], ssc[2])]))
        kmeans_sec = time.perf_counter() - t1
        _fill_scores(
            row,
            sc,
            ssc,
            change,
            0.0,
            kmeans_sec,
            {
                "status": "CONVERGED" if state.converged else "NONCONVERGED",
                "n_iterations": state.n_iterations,
                "converged": state.converged,
                "objective_name": state.objective_name,
                "objective_value": f"{state.objective_value:.10g}",
                "equation8_value": f"{state.equation8_value:.10g}",
                "relative_move": f"{state.relative_move:.10g}",
                "solver": state.solver,
                "f_source": state.f_source,
                "notes": "E07 does not refit G. Same control representation. Init is not chosen by ACC.",
            },
        )
        _dump_json(run_root / run_id / "metrics.json", {"sc_acc": sc[0], "ssc_acc": ssc[0], "sc_nmi": sc[1], "ssc_nmi": ssc[1]})
        rows.append(row)
    for name, builder in (
        ("inertia_best", lambda feats: inertia_best_labels(feats, n_clusters, seeds)[0]),
        ("consensus", lambda feats: consensus_labels(feats, n_clusters, seeds)),
    ):
        payload_hash = _config_hash({"e07": name, "dataset": spec["dataset"], "version": spec["version"], "seeds": seeds})
        run_id = f"{stamp}__EXT__{spec['dataset']}__{spec['version']}__e07__{name}__{payload_hash[:8]}"
        row = _base_row(spec, "E07", name, PRIMARY_GAMMA, "primary", commit, checksum, payload_hash, seeds)
        row["run_id"] = run_id
        pred_f = builder(state.embedding)
        pred_g = builder(state.patterns)
        sc_acc = [clustering_accuracy(y, pred_f)]
        sc_nmi = [normalized_mutual_information(y, pred_f)]
        g_acc = [clustering_accuracy(y, pred_g)]
        g_nmi = [normalized_mutual_information(y, pred_g)]
        _fill_scores(
            row,
            (sc_acc, sc_nmi, [pred_f]),
            (g_acc, g_nmi, [pred_g]),
            disagreement_fraction(pred_f, pred_g),
            0.0,
            0.0,
            {
                "status": "COMPLETE_SINGLE_ASSIGNMENT",
                "n_iterations": state.n_iterations,
                "converged": state.converged,
                "objective_name": state.objective_name,
                "objective_value": f"{state.objective_value:.10g}",
                "solver": state.solver,
                "f_source": state.f_source,
                "notes": (
                    "One assignment. inertia_best minimizes K-means inertia over the random seeds. "
                    "consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. "
                    "Sample sd is blank because there is one selected assignment."
                ),
            },
        )
        _dump_json(
            run_root / run_id / "metrics.json",
            {"sc_acc": sc_acc, "ssc_acc": g_acc, "sc_nmi": sc_nmi, "ssc_nmi": g_nmi, "n_candidates": len(seeds)},
        )
        rows.append(row)
    return rows


def _mutual_rows(spec, features, embedding, y, n_clusters, seeds, commit, checksum, stamp, run_root, config):
    payload_hash = _config_hash({"aux": "mutual_knn_e8", "dataset": spec["dataset"], "version": spec["version"]})
    run_id = f"{stamp}__EXT__{spec['dataset']}__{spec['version']}__mutual_knn__{payload_hash[:8]}"
    row = _base_row(spec, "mutual_knn", "auxiliary_e8", PRIMARY_GAMMA, "auxiliary", commit, checksum, payload_hash, seeds)
    row["run_id"] = run_id
    try:
        t0 = time.perf_counter()
        affinity, info = mutual_knn_affinity(embedding, k=config.k)
        result = shrink_embedding(
            embedding,
            affinity,
            gamma=PRIMARY_GAMMA,
            eps=config.eps,
            tol=config.tol,
            max_iter=config.max_iter,
            G_init=embedding,
            zero_residual_floor=config.zero_residual_floor,
            variant="E8",
        )
        fit_sec = time.perf_counter() - t0
        t1 = time.perf_counter()
        sc = _score_many(embedding, y, n_clusters, seeds, "random")
        ssc = _score_many(result.patterns, y, n_clusters, seeds, "random")
        change = float(np.mean([disagreement_fraction(a, b) for a, b in zip(sc[2], ssc[2])]))
        kmeans_sec = time.perf_counter() - t1
        n_edges, n_components = _graph_counts(affinity)
        _fill_scores(
            row,
            sc,
            ssc,
            change,
            fit_sec,
            kmeans_sec,
            {
                "status": "CONVERGED" if result.converged else "NONCONVERGED",
                "n_iterations": result.n_iterations,
                "converged": result.converged,
                "objective_name": "equation8_on_method_W",
                "objective_value": f"{result.history[-1]['equation8_objective']:.10g}",
                "equation8_value": f"{result.history[-1]['equation8_objective']:.10g}",
                "relative_move": f"{float(np.linalg.norm(result.patterns - embedding) / max(np.linalg.norm(embedding), 1e-12)):.10g}",
                "n_edges": n_edges,
                "n_components": n_components,
                "fixed_point_residual": f"{result.fixed_point_residual:.10g}",
                "solver": "original_spsolve",
                "f_source": "control_embedding",
                "notes": (
                    "Auxiliary mutual-kNN shrinkage on the control F, E8 not E13. "
                    "Not one of E01-E09. Existing historical mutual-kNN files were not copied."
                ),
            },
        )
        row["notes"] = row["notes"] + f" mutual_edges={info.get('n_mutual_undirected_edges')}"
        _dump_json(run_root / run_id / "metrics.json", {"ssc_acc": ssc[0], "sc_acc": sc[0], "graph": info})
    except Exception as exc:  # noqa: BLE001
        row["status"] = "FAILED"
        row["notes"] = f"FAILED {type(exc).__name__}: {exc}"
    return [row]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("pilot", "full"), required=True)
    parser.add_argument("--datasets", default="")
    args = parser.parse_args()
    chosen = list(RUNNABLE)
    if args.datasets:
        wanted = {item.strip() for item in args.datasets.split(",") if item.strip()}
        chosen = [item for item in chosen if item["dataset"] in wanted or item["version"] in wanted]
    if args.phase == "pilot":
        pilot_names = {"ORL", "USPS", "cropped2414"}
        chosen = [item for item in chosen if item["dataset"] in pilot_names or item["version"] in pilot_names]
        seeds = [0, 1, 2]
        gammas = (PRIMARY_GAMMA,)
    else:
        seeds = list(range(50))
        gammas = GAMMA_GRID
    run_phase(args.phase, chosen, seeds, gammas)


if __name__ == "__main__":
    main()
