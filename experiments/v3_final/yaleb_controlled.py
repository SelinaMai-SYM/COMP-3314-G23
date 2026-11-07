"""YaleB Y0--Y3 diagnostics. Does not replace the locked Y0 reconstruction."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.metrics import adjusted_rand_score

from SSC_method.graph_construction import knn_affinity, knn_neighbor_squared_distances
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from experiments.v3_reproduction.dataset_registry import l2_normalize_rows, load_spec, row_normalize
from experiments.v3_theory.run_campaign import data_root, embed_track
from method_extension.v3_theory.common.graphs import graph_summary, knn_graph, laplacian_spectrum
from method_extension.v3_theory.common.solvers import compare_solvers
from method_extension.v3_theory.x1_certified_path.threshold import ordered_pair_threshold

ROOT = Path(__file__).resolve().parents[2]
JOBS = ROOT / "runs" / "v3_reproduction" / "jobs"
OUT = ROOT / "results" / "v3_final"
VERSIONS = ("YaleB_dengcai32", "YaleB_cropped2414")
PREPS = ("Y0", "Y1", "Y2", "Y3")
SOLVER_CELLS = (("Y0", 1.0), ("Y3", 1.0), ("Y3", 1000.0))


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key, value in row.items():
            if key not in seen and not isinstance(value, (list, dict, np.ndarray)):
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def load_version(dataset_id: str) -> dict:
    version = "dengcai32" if dataset_id.endswith("dengcai32") else "cropped2414"
    record = load_spec(
        data_root(),
        {
            "dataset_id": dataset_id,
            "historical_benchmark": "YaleB",
            "loader_name": "YaleB",
            "folder": "yaleb/data",
            "version": version,
        },
    )
    if not record.get("available"):
        raise RuntimeError(record.get("reason"))
    return record


def matrix_audit(left: dict, right: dict) -> dict:
    x0 = np.asarray(left["X"])
    x1 = np.asarray(right["X"])
    y0 = np.asarray(left["y"])
    y1 = np.asarray(right["y"])
    same_shape = x0.shape == x1.shape
    identical = bool(same_shape and np.array_equal(x0, x1) and np.array_equal(y0, y1))
    # Orientation check uses the loader matrices as stored. It does not pick a flip.
    correlation = float("nan")
    transposed = float("nan")
    if same_shape and x0.shape[1] == 1024:
        a = x0.reshape(-1, 32, 32)
        b = x1.reshape(-1, 32, 32)
        correlation = float(np.corrcoef(a.reshape(len(a), -1).ravel()[:200000], b.reshape(len(b), -1).ravel()[:200000])[0, 1])
        transposed = float(np.mean([np.corrcoef(a[i].ravel(), b[i].T.ravel())[0, 1] for i in range(0, len(a), 50)]))
    def duplicates(matrix: np.ndarray) -> int:
        view = np.ascontiguousarray(matrix).view(np.dtype((np.void, matrix.dtype.itemsize * matrix.shape[1])))
        _unique, counts = np.unique(view, return_counts=True)
        return int(np.sum(counts - 1))
    return {
        "identical_values_and_labels": identical,
        "same_shape": same_shape,
        "label_agreement": float(np.mean(y0 == y1)) if y0.shape == y1.shape else float("nan"),
        "max_abs_difference": float(np.max(np.abs(x0 - x1))) if same_shape else float("nan"),
        "flattened_correlation_prefix": correlation,
        "mean_transpose_correlation": transposed,
        "left_duplicate_extra_rows": duplicates(x0),
        "right_duplicate_extra_rows": duplicates(x1),
        "left_min": float(x0.min()),
        "left_max": float(x0.max()),
        "right_min": float(x1.min()),
        "right_max": float(x1.max()),
        "left_fingerprint": left["fingerprint"]["x_sha256"],
        "right_fingerprint": right["fingerprint"]["x_sha256"],
        "left_label_fingerprint": left["fingerprint"]["y_sha256"],
        "right_label_fingerprint": right["fingerprint"]["y_sha256"],
    }


def neighbor_overlap(raw: np.ndarray, normalized: np.ndarray, k: int = 5) -> dict:
    _d0, i0 = knn_neighbor_squared_distances(raw, k)
    _d1, i1 = knn_neighbor_squared_distances(normalized, k)
    overlaps = []
    for left, right in zip(i0, i1, strict=True):
        overlaps.append(len(set(left.tolist()) & set(right.tolist())) / k)
    graph_raw = knn_graph(raw, k)
    graph_l2 = knn_graph(normalized, k)
    return {
        "mean_neighbor_overlap": float(np.mean(overlaps)),
        "raw_components": graph_summary(graph_raw, "raw")["n_components"],
        "l2_components": graph_summary(graph_l2, "l2")["n_components"],
        "raw_degree_mean": graph_summary(graph_raw, "raw")["degree_mean"],
        "l2_degree_mean": graph_summary(graph_l2, "l2")["degree_mean"],
        "raw_isolates": graph_summary(graph_raw, "raw")["n_isolates"],
        "l2_isolates": graph_summary(graph_l2, "l2")["n_isolates"],
    }


def posthoc_same_identity(affinity: sparse.spmatrix, labels: np.ndarray) -> float:
    matrix = sparse.csr_matrix(affinity).tocoo()
    keep = matrix.row < matrix.col
    if not np.any(keep):
        return float("nan")
    return float(np.mean(labels[matrix.row[keep]] == labels[matrix.col[keep]]))


def aggregate_trials(dataset_id: str, prep: str, method: str, variant: str | None, gamma: float | None, initialization: str) -> dict:
    folder = JOBS / dataset_id
    if method == "sc":
        path = folder / f"sc__{prep}.trials.jsonl"
    else:
        path = folder / f"ssc__{prep}__{variant}__g{gamma:.0e}.trials.jsonl"
    rows = []
    if not path.is_file():
        return {"n": 0}
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("method") != method:
                continue
            if int(row.get("seed", -1)) > 49:
                continue
            if row.get("initialization") != initialization:
                continue
            if variant and row.get("variant") != variant:
                continue
            rows.append(row)
    if not rows:
        return {"n": 0}
    acc = np.asarray([row["acc"] for row in rows], dtype=np.float64)
    nmi = np.asarray([row["nmi"] for row in rows], dtype=np.float64)
    selected = min(rows, key=lambda item: (float(item["inertia"]), int(item["seed"])))
    return {
        "n": len(rows),
        "acc_mean": float(acc.mean()),
        "acc_sd": float(acc.std(ddof=1)) if len(rows) > 1 else float("nan"),
        "nmi_mean": float(nmi.mean()),
        "nmi_sd": float(nmi.std(ddof=1)) if len(rows) > 1 else float("nan"),
        "min_inertia_acc": float(selected["acc"]),
        "min_inertia_nmi": float(selected["nmi"]),
        "min_inertia_seed": int(selected["seed"]),
        "source_commit": rows[0].get("code_commit"),
    }


def spectrum_row(name: str, affinity, n_keep: int, dataset_id: str, prep: str) -> dict:
    summary = graph_summary(affinity, name)
    spectral = laplacian_spectrum(affinity, n_keep + 1)
    values = np.asarray(spectral["eigenvalues"], dtype=np.float64)
    row = {
        "dataset_id": dataset_id,
        "prep": prep,
        "graph": name,
        **summary,
        "eigen_solver": spectral["eigen_solver"],
        "eigen_residual_max": spectral["eigen_residual_max"],
        "orthogonality_frobenius": spectral["orthogonality_frobenius"],
        "vector_row_norm_mean": spectral["vector_row_norm_mean"],
    }
    if values.size > n_keep:
        row["lambda_K"] = float(values[n_keep - 1])
        row["lambda_K_plus_1"] = float(values[n_keep])
        row["eigengap_K"] = float(values[n_keep] - values[n_keep - 1])
    else:
        row["lambda_K"] = float(values[-1]) if values.size else float("nan")
        row["lambda_K_plus_1"] = float("nan")
        row["eigengap_K"] = float("nan")
    row["eigenvalues"] = " ".join(f"{value:.8g}" for value in values)
    return row


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    loaded = {name: load_version(name) for name in VERSIONS}
    audit = matrix_audit(loaded["YaleB_dengcai32"], loaded["YaleB_cropped2414"])
    graph_rows = []
    eigen_rows = []
    cluster_rows = []
    distance_rows = []
    solver_rows = []
    bundles = {}
    for dataset_id, record in loaded.items():
        raw = np.asarray(record["X"], dtype=np.float64)
        labels = np.asarray(record["y"])
        normalized = l2_normalize_rows(raw)
        distance = neighbor_overlap(raw, normalized)
        distance["dataset_id"] = dataset_id
        # Post-hoc only. Not used to choose the graph.
        distance["posthoc_same_identity_raw"] = posthoc_same_identity(knn_graph(raw, 5), labels)
        distance["posthoc_same_identity_l2"] = posthoc_same_identity(knn_graph(normalized, 5), labels)
        distance_rows.append(distance)
        for prep in PREPS:
            features = normalized if prep in {"Y1", "Y3"} else raw
            built = embed_track(features, int(np.unique(labels).size), prep)
            bundles[(dataset_id, prep)] = built
            embedding = built["F"]
            for graph_name, affinity in (("A_initial", built["A"]), ("W_shrinkage", built["W"])):
                row = spectrum_row(graph_name, affinity, embedding.shape[1], dataset_id, prep)
                row["embedding_row_norm_mean"] = float(np.linalg.norm(embedding, axis=1).mean())
                row["embedding_row_norm_cv"] = float(np.linalg.norm(embedding, axis=1).std() / max(np.linalg.norm(embedding, axis=1).mean(), 1e-12))
                row["embedding_rank"] = int(np.linalg.matrix_rank(embedding, tol=1e-8))
                gram = embedding.T @ embedding
                row["embedding_orthogonality"] = float(np.linalg.norm(gram - np.eye(gram.shape[0])))
                graph_rows.append({key: value for key, value in row.items() if key != "eigenvalues"})
                eigen_rows.append(row)
                if graph_name == "A_initial":
                    row_copy = dict(row)
                    row_copy["posthoc_same_identity_edge_fraction"] = posthoc_same_identity(affinity, labels)
            for initialization in ("RANDOM", "SKLEARN_GREEDY_KMEANSPP"):
                sc = aggregate_trials(dataset_id, prep, "sc", None, None, initialization)
                cluster_rows.append({"dataset_id": dataset_id, "prep": prep, "method": "sc", "variant": "", "gamma": "", "initialization": initialization, **sc})
                for variant in ("E8", "E13"):
                    for gamma in (1e-6, 1e-3, 1.0, 1e3, 1e6):
                        ssc = aggregate_trials(dataset_id, prep, "ssc", variant, gamma, initialization)
                        cluster_rows.append(
                            {
                                "dataset_id": dataset_id,
                                "prep": prep,
                                "method": "ssc",
                                "variant": variant,
                                "gamma": gamma,
                                "initialization": initialization,
                                **ssc,
                            }
                        )
    for dataset_id, prep in ((dataset, cell[0]) for dataset in VERSIONS for cell in SOLVER_CELLS):
        gamma = dict(SOLVER_CELLS)[prep] if False else None
    for dataset_id in VERSIONS:
        for prep, gamma in SOLVER_CELLS:
            built = bundles[(dataset_id, prep)]
            print("SOLVER", dataset_id, prep, gamma, flush=True)
            compared = compare_solvers(
                built["F"],
                built["W"],
                gamma,
                irls_max_iter=1000,
                admm_max_iter=200,
                variant="E8",
            )
            threshold = ordered_pair_threshold(built["F"], built["W"])
            solver_rows.append(
                {
                    "dataset_id": dataset_id,
                    "prep": prep,
                    "gamma": gamma,
                    "gamma_0": threshold["gamma_0"],
                    "status": compared["status"],
                    "irls_objective": compared["irls_objective"],
                    "independent_objective": compared["independent_objective"],
                    "objective_gap_irls_minus_independent": compared["objective_gap_irls_minus_independent"],
                    "relative_objective_gap": compared["relative_objective_gap"],
                    "primal_residual": compared["primal_residual"],
                    "dual_residual": compared["dual_residual"],
                    "irls_fixed_point_residual": compared["irls_fixed_point_residual"],
                    "irls_iterations": compared["irls_iterations"],
                    "independent_iterations": compared["independent_iterations"],
                    "irls_wall_seconds": compared["irls_wall_seconds"],
                    "independent_wall_seconds": compared["independent_wall_seconds"],
                    "relative_g_minus_f": compared["relative_g_minus_f"],
                    "irls_converged": compared["irls_converged"],
                    "independent_converged": compared["independent_converged"],
                }
            )
    _write(OUT / "yaleb_version_audit.csv", [audit])
    _write(OUT / "yaleb_distance_control.csv", distance_rows)
    _write(OUT / "yaleb_graph_stats.csv", graph_rows)
    _write(OUT / "yaleb_eigenvalues.csv", eigen_rows)
    _write(OUT / "yaleb_clustering_reaggregated.csv", cluster_rows)
    _write(OUT / "yaleb_solver_check.csv", solver_rows)
    (OUT / "yaleb_version_audit.json").write_text(json.dumps(audit, indent=2))
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
