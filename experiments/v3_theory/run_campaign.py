"""Run the prespecified X1--X5 grid. Grids are fixed in this file before any ACC is read."""

from __future__ import annotations

import json
import os
import resource
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy import sparse
from sklearn.metrics import adjusted_rand_score

from SSC_method.graph_construction import knn_affinity
from SSC_method.objective import equation8_objective
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from experiments.v3_reproduction.dataset_registry import l2_normalize_rows, load_spec, row_normalize
from method_extension.v3_theory.common.cluster import (
    PRIMARY_INIT,
    SENSITIVITY_INIT,
    paired_bootstrap,
    run_family,
    summarize_family,
)
from method_extension.v3_theory.common.graphs import (
    apply_stability,
    degree_matched_random,
    edge_budget_matched,
    graph_summary,
    knn_graph,
    mass_matched_random,
    mass_normalized_affinity,
    mean_mass,
    permute_stability,
    scale_to_mass,
    support_fraction,
    total_mass,
    uniform_scale,
    upper_edges,
)
from method_extension.v3_theory.common.objectives import weighted_objective
from method_extension.v3_theory.common.solvers import admm_weighted, shrink_weighted
from method_extension.v3_theory.x1_certified_path.threshold import fusion_summary, g_equals_f_is_optimal, ordered_pair_threshold
from method_extension.v3_theory.x2_stability_graph.weights import perturb_features, perturb_images, perturbation_list
from method_extension.v3_theory.x3_graph_calibration.calibrate import equivalent_gamma, threshold_gamma
from method_extension.v3_theory.x4_multiscale_consensus.combine import SCALES, multiscale_graph
from method_extension.v3_theory.x5_adaptive_fidelity.weights import (
    adaptive_fidelity,
    inverse_fidelity,
    permuted_fidelity,
    uniform_fidelity,
)

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "runs" / "v3_theory" / "cache"
JOBS = ROOT / "results" / "v3_theory" / "jobs"
OUT = ROOT / "results" / "v3_theory"

PAPER_GAMMA = (1e-6, 1e-3, 1.0, 1e3, 1e6)
X1_MULTIPLIERS = (0.1, 0.5, 1.0, 2.0, 10.0, 100.0)
X3_GRID = (1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0)
BETAS = (0.0, 0.5, 1.0, 2.0)
ALPHAS = (0.0, 0.5, 1.0, 2.0)
GAMMA_REF = 1.0
PRIMARY_CONTRASTS = ("X1", "X2", "X3", "X4", "X5")

TRACKS = (
    {"dataset_id": "ORL_att92", "loader_name": "ORL", "folder": "orl/data", "version": "att92", "benchmark": "ORL", "prep": "Y0"},
    {"dataset_id": "JAFFE", "loader_name": "JAFFE", "folder": "jaffe/data", "version": "zenodo", "benchmark": "JAFFE", "prep": "Y0"},
    {"dataset_id": "YaleB_dengcai32", "loader_name": "YaleB", "folder": "yaleb/data", "version": "dengcai32", "benchmark": "YaleB", "prep": "Y0"},
    {"dataset_id": "YaleB_dengcai32", "loader_name": "YaleB", "folder": "yaleb/data", "version": "dengcai32", "benchmark": "YaleB", "prep": "Y3"},
    {"dataset_id": "YaleB_cropped2414", "loader_name": "YaleB", "folder": "yaleb/data", "version": "cropped2414", "benchmark": "YaleB", "prep": "Y0"},
    {"dataset_id": "YaleB_cropped2414", "loader_name": "YaleB", "folder": "yaleb/data", "version": "cropped2414", "benchmark": "YaleB", "prep": "Y3"},
    {"dataset_id": "USPS", "loader_name": "USPS", "folder": "usps/data", "version": "libsvm", "benchmark": "USPS", "prep": "Y0"},
)
SUPPLEMENTAL = (
    {"dataset_id": "BinAlpha_candidate26x30", "loader_name": "BinAlpha", "folder": "binalpha/data", "version": "CANDIDATE_BIN_ALPHA", "benchmark": "BinAlpha", "prep": "Y0"},
    {"dataset_id": "UMIST_precropped575", "loader_name": "UMIST", "folder": "umist/data", "version": "precropped575", "benchmark": "UMIST", "prep": "Y0"},
)


def data_root() -> Path:
    from benchmarks.data_paths import resolve_data_root
    return resolve_data_root()


def git_commit() -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def save_csr(path: Path, matrix: sparse.spmatrix) -> None:
    matrix = sparse.csr_matrix(matrix, dtype=np.float64)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, data=matrix.data, indices=matrix.indices, indptr=matrix.indptr, shape=np.array(matrix.shape))


def load_csr(path: Path) -> sparse.csr_matrix:
    payload = np.load(path)
    return sparse.csr_matrix((payload["data"], payload["indices"], payload["indptr"]), shape=tuple(payload["shape"]))


def prepare_features(features: np.ndarray, prep: str) -> np.ndarray:
    if prep in {"Y1", "Y3"}:
        return l2_normalize_rows(features)
    return np.asarray(features, dtype=np.float64)


def embed_track(features: np.ndarray, n_clusters: int, prep: str) -> dict[str, Any]:
    config = SpectralGraphConfig(
        k=5,
        delta2=None,
        row_normalize=False,
        symmetrization="union",
        laplacian="symmetric_normalized_eq4",
        eigenvector_selection="smallest",
    )
    embedding, info = spectral_embedding(features, n_components=n_clusters, config=config)
    affinity_x, _graph = knn_affinity(features, config=config)
    if prep in {"Y2", "Y3"}:
        embedding = row_normalize(embedding)
    affinity_f = knn_graph(embedding, 5)
    threshold = ordered_pair_threshold(embedding, affinity_f)
    return {
        "F": embedding,
        "A": affinity_x,
        "W": affinity_f,
        "eigenvalues": np.asarray(info.get("eigenvalues"), dtype=np.float64),
        "gamma_0": float(threshold["gamma_0"]),
        "threshold_source": threshold["threshold_source"],
        "n_coincident_edges": int(threshold["n_coincident_edges"]),
        "max_q_norm": float(threshold["max_q_norm"]),
    }


def iteration_budget(gamma: float) -> int:
    """300 below the usual threshold region; 1000 once shrinkage can move.

    The extra budget follows the frozen priority continuation (300 + 700).
    It is not chosen from ACC.
    """
    return 300 if float(gamma) < 0.5 else 1000


def build_track(spec: dict[str, str], features: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    key = f"{spec['dataset_id']}__{spec['prep']}"
    folder = CACHE / key
    labels = np.asarray(labels)
    cached = folder / "meta.json"
    if os.environ.get("V3_REBUILD") != "1" and cached.is_file() and (folder / "F.npy").is_file():
        meta = json.loads(cached.read_text())
        built = {
            "F": np.load(folder / "F.npy"),
            "A": load_csr(folder / "A.npz"),
            "W": load_csr(folder / "W.npz"),
            "eigenvalues": np.load(folder / "eigenvalues.npy") if (folder / "eigenvalues.npy").is_file() else np.array([]),
            "gamma_0": float(meta["gamma_0"]),
            "threshold_source": meta["threshold_source"],
            "n_coincident_edges": int(meta["n_coincident_edges"]),
            "max_q_norm": float(meta["max_q_norm"]),
            "meta": meta,
            "folder": folder,
            "y": labels,
            "X": np.load(folder / "X.npy"),
        }
        print(" REUSE", key, "gamma0", meta["gamma_0"], flush=True)
        return built
    prepared = prepare_features(features, spec["prep"])
    built = embed_track(prepared, int(np.unique(labels).size), spec["prep"])
    folder.mkdir(parents=True, exist_ok=True)
    np.save(folder / "F.npy", built["F"])
    np.save(folder / "y.npy", labels)
    np.save(folder / "X.npy", prepared)
    save_csr(folder / "W.npz", built["W"])
    save_csr(folder / "A.npz", built["A"])
    meta = {
        "key": key,
        "dataset_id": spec["dataset_id"],
        "prep": spec["prep"],
        "benchmark": spec["benchmark"],
        "n_samples": int(built["F"].shape[0]),
        "n_components": int(built["F"].shape[1]),
        "n_classes": int(np.unique(labels).size),
        "gamma_0": built["gamma_0"],
        "threshold_source": built["threshold_source"],
        "n_coincident_edges": built["n_coincident_edges"],
        "max_q_norm": built["max_q_norm"],
        "counts_as_primary_benchmark": spec["benchmark"] in {"ORL", "JAFFE", "YaleB", "USPS"} and spec["prep"] == "Y0",
        "yaleb_track": spec["prep"],
    }
    (folder / "meta.json").write_text(json.dumps(meta))
    built["meta"] = meta
    built["folder"] = folder
    built["y"] = labels
    built["X"] = prepared
    return built


def _weight_path(key: str, name: str) -> Path:
    return CACHE / key / "weights" / f"{name}.npz"


def _fidelity_path(key: str, name: str) -> Path:
    return CACHE / key / "fidelity" / f"{name}.npy"


def store_weight(key: str, name: str, matrix: sparse.spmatrix) -> str:
    path = _weight_path(key, name)
    save_csr(path, matrix)
    return str(path)


def store_fidelity(key: str, name: str, vector: np.ndarray) -> str:
    path = _fidelity_path(key, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(vector, dtype=np.float64))
    return str(path)


def make_tasks(built: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    meta = built["meta"]
    key = meta["key"]
    base_w = store_weight(key, "W_k5", built["W"])
    tasks: list[dict[str, Any]] = []
    graphs: list[dict[str, Any]] = []
    gamma_0 = float(meta["gamma_0"])

    def add(extension: str, name: str, gamma: float, weight: str, *, fidelity: str | None = None, role: str, contrast: str | None = None, certificate: bool = False) -> None:
        tasks.append(
            {
                "job_id": f"{extension}__{key}__{name}",
                "extension": extension,
                "name": name,
                "dataset_id": meta["dataset_id"],
                "benchmark": meta["benchmark"],
                "prep": meta["prep"],
                "role": role,
                "contrast": contrast,
                "gamma": float(gamma),
                "gamma_0": gamma_0,
                "weight_path": weight,
                "fidelity_path": fidelity,
                "bundle": str(built["folder"]),
                "max_iter": iteration_budget(gamma),
                "run_admm": extension == "X1" or meta["n_samples"] <= 500 or contrast in PRIMARY_CONTRASTS,
                "certificate_region": bool(certificate and np.isfinite(gamma_0) and g_equals_f_is_optimal({"gamma_0": gamma_0, "threshold_source": meta["threshold_source"]}, gamma)),
                "threshold_source": meta["threshold_source"],
                "n_samples": meta["n_samples"],
                "counts_as_primary_benchmark": meta["counts_as_primary_benchmark"],
            }
        )

    gammas = set(PAPER_GAMMA)
    for multiplier in X1_MULTIPLIERS:
        if np.isfinite(gamma_0):
            gammas.add(float(multiplier) * gamma_0)
    for gamma in sorted(gammas):
        multiplier = gamma / gamma_0 if np.isfinite(gamma_0) and gamma_0 > 0 else float("nan")
        name = f"gamma_{gamma:.6e}"
        contrast = "X1" if np.isfinite(multiplier) and np.isclose(multiplier, 1.0) else None
        role = "baseline" if np.isclose(gamma, GAMMA_REF) else "grid"
        add("X1", name, gamma, base_w, role=role, contrast=contrast, certificate=True)
    add("X1", "control_G_equals_F", 0.0, base_w, role="control", certificate=True)

    # X2 stability graphs from image perturbations of the prepared matrix.
    perturbed = []
    for index, (kind, brightness, contrast) in enumerate(perturbation_list("fit")):
        if meta["benchmark"] == "BinAlpha":
            changed = perturb_features(built["X"], seed=1000 + index)
        else:
            changed = perturb_images(built["X"], brightness, contrast)
        embedding, _info = spectral_embedding(
            changed,
            n_components=meta["n_components"],
            config=SpectralGraphConfig(k=5, delta2=None, row_normalize=False, symmetrization="union"),
        )
        if meta["prep"] in {"Y2", "Y3"}:
            embedding = row_normalize(embedding)
        perturbed.append(knn_graph(embedding, 5))
    fraction = support_fraction(perturbed)
    original = built["W"]
    for beta in BETAS:
        stable = apply_stability(original, fraction, beta)
        path = store_weight(key, f"stable_beta_{beta:g}", stable)
        add(
            "X2",
            f"beta_{beta:g}",
            GAMMA_REF,
            path,
            role="baseline" if beta == 0.0 else "grid",
            contrast="X2" if beta == 1.0 else None,
        )
        summary = graph_summary(stable, f"X2_beta_{beta:g}")
        summary.update({"dataset_id": meta["dataset_id"], "prep": meta["prep"], "extension": "X2"})
        graphs.append(summary)
    uniform = uniform_scale(original, 2.0)
    add("X2", "control_uniform_scale_2", GAMMA_REF, store_weight(key, "uniform_scale_2", uniform), role="control")
    permuted = permute_stability(original, fraction, beta=1.0, seed=11)
    add("X2", "control_permuted_s_beta_1", GAMMA_REF, store_weight(key, "permuted_s", permuted), role="control")
    matched = degree_matched_random(original, seed=19)
    add("X2", "control_degree_matched", GAMMA_REF, store_weight(key, "degree_matched", matched), role="control")
    heldout_graphs = []
    for index, (kind, brightness, contrast) in enumerate(perturbation_list("heldout")):
        if meta["benchmark"] == "BinAlpha":
            changed = perturb_features(built["X"], seed=2000 + index)
        else:
            changed = perturb_images(built["X"], brightness, contrast)
        embedding, _info = spectral_embedding(
            changed,
            n_components=meta["n_components"],
            config=SpectralGraphConfig(k=5, delta2=None, row_normalize=False, symmetrization="union"),
        )
        heldout_graphs.append(knn_graph(embedding, 5))
    save_csr(built["folder"] / "heldout_union.npz", support_fraction(heldout_graphs))

    # X3. Mass normalization is an exact rescaling; both systems are still solved
    # for tau in {1, 10, 100}. Smaller taus sit at G=F when the threshold holds.
    mass = mean_mass(original)
    normalized, _mass = mass_normalized_affinity(original)
    normalized_path = store_weight(key, "W_bar", normalized)
    for tau in X3_GRID:
        add("X3", f"original_gamma_{tau:.6e}", tau, base_w, role="grid" if not np.isclose(tau, 1.0) else "baseline", contrast="X3" if np.isclose(tau, 1.0) else None)
        add("X3", f"mass_tau_{tau:.6e}", tau, normalized_path, role="grid", contrast="X3" if np.isclose(tau, 1.0) else None)
        gamma_equiv = equivalent_gamma(tau, mass)
        add("X3", f"control_equiv_gamma_{tau:.6e}", gamma_equiv, base_w, role="control")
        if np.isfinite(gamma_0):
            add("X3", f"threshold_tau_{tau:.6e}", threshold_gamma(tau, gamma_0), base_w, role="grid", certificate=True)
    graphs.append({**graph_summary(original, "W_k5"), "dataset_id": meta["dataset_id"], "prep": meta["prep"], "extension": "base", "mean_mass": mass})

    # X4 fixed F, varying W. A second block refits F and is labeled separately.
    multi, singles = multiscale_graph(built["F"], SCALES)
    for scale, graph in zip(SCALES, singles, strict=True):
        normalized_k = scale_to_mass(graph, total_mass(original))
        add(
            "X4",
            f"single_k_{scale}",
            GAMMA_REF,
            store_weight(key, f"k_{scale}", normalized_k),
            role="baseline" if scale == 5 else "grid",
            contrast="X4" if scale == 5 else None,
        )
    add("X4", "multi", GAMMA_REF, store_weight(key, "multi", multi), role="grid", contrast="X4")
    add("X4", "control_mass_matched_random", GAMMA_REF, store_weight(key, "mass_random", mass_matched_random(multi, 23)), role="control")
    add("X4", "control_edge_budget_random", GAMMA_REF, store_weight(key, "edge_random", edge_budget_matched(multi, 29)), role="control")
    for scale in SCALES:
        if scale == 5:
            continue
        refit, _info = spectral_embedding(
            built["X"],
            n_components=meta["n_components"],
            config=SpectralGraphConfig(k=int(scale), delta2=None, row_normalize=False, symmetrization="union"),
        )
        if meta["prep"] in {"Y2", "Y3"}:
            refit = row_normalize(refit)
        refit_w = knn_graph(refit, int(scale))
        refit_path = built["folder"] / f"F_k{scale}.npy"
        np.save(refit_path, refit)
        weight_file = store_weight(key, f"refit_k_{scale}", refit_w)
        tasks.append(
            {
                "job_id": f"X4refit__{key}__k_{scale}",
                "extension": "X4_refit_F",
                "name": f"refit_k_{scale}",
                "dataset_id": meta["dataset_id"],
                "benchmark": meta["benchmark"],
                "prep": meta["prep"],
                "role": "separate_experiment",
                "contrast": None,
                "gamma": GAMMA_REF,
                "gamma_0": gamma_0,
                "weight_path": weight_file,
                "fidelity_path": None,
                "bundle": str(built["folder"]),
                "embedding_path": str(refit_path),
                "max_iter": iteration_budget(GAMMA_REF),
                "run_admm": meta["n_samples"] <= 500,
                "certificate_region": False,
                "threshold_source": meta["threshold_source"],
                "n_samples": meta["n_samples"],
                "counts_as_primary_benchmark": False,
            }
        )

    for alpha in ALPHAS:
        vector = adaptive_fidelity(built["F"], original, alpha)
        add(
            "X5",
            f"alpha_{alpha:g}",
            GAMMA_REF,
            base_w,
            fidelity=store_fidelity(key, f"alpha_{alpha:g}", vector),
            role="baseline" if alpha == 0.0 else "grid",
            contrast="X5" if alpha == 1.0 else None,
        )
    inverse = inverse_fidelity(built["F"], original, alpha=1.0)
    add("X5", "control_inverse_alpha_1", GAMMA_REF, base_w, fidelity=store_fidelity(key, "inverse", inverse), role="control")
    base_a = adaptive_fidelity(built["F"], original, 1.0)
    add("X5", "control_permuted_a", GAMMA_REF, base_w, fidelity=store_fidelity(key, "permuted", permuted_fidelity(base_a, 13)), role="control")
    add("X5", "control_uniform_a_2", GAMMA_REF, base_w, fidelity=store_fidelity(key, "uniform2", uniform_fidelity(meta["n_samples"], 2.0)), role="control")
    return tasks, graphs


def _jsonable(row: dict[str, Any]) -> dict[str, Any]:
    clean = {}
    for key, value in row.items():
        if isinstance(value, np.ndarray):
            continue
        if isinstance(value, (np.floating, np.integer)):
            clean[key] = value.item()
        else:
            clean[key] = value
    return clean


def execute_task(task: dict[str, Any]) -> dict[str, Any]:
    destination = JOBS / f"{task['job_id']}.json"
    if destination.is_file() and os.environ.get("V3_RERUN", "") != "1":
        return json.loads(destination.read_text())
    started = time.perf_counter()
    try:
        folder = Path(task["bundle"])
        embedding = np.load(task["embedding_path"]) if task.get("embedding_path") else np.load(folder / "F.npy")
        labels = np.load(folder / "y.npy")
        affinity = load_csr(Path(task["weight_path"]))
        fidelity = None if not task.get("fidelity_path") else np.load(task["fidelity_path"])
        gamma = float(task["gamma"])
        reference_objective = weighted_objective(embedding, embedding, affinity, gamma, fidelity)
        if gamma == 0.0:
            solved = {
                "patterns": np.array(embedding, copy=True),
                "objective": float(reference_objective),
                "n_iterations": 0,
                "converged": True,
                "fixed_point_residual": 0.0,
                "wall_seconds": 0.0,
                "solver": "closed_form_gamma0",
            }
        else:
            solved = shrink_weighted(
            embedding,
            affinity,
            gamma,
            fidelity,
            variant="E8",
            max_iter=int(task["max_iter"]),
        )
        movement = float(np.linalg.norm(solved["patterns"] - embedding) / max(np.linalg.norm(embedding), 1e-12))
        admm = None
        if task.get("run_admm") and gamma > 0.0:
            admm = admm_weighted(
                embedding,
                affinity,
                gamma,
                fidelity,
                max_iter=120 if task["n_samples"] > 1500 else 250,
                G_init=solved["patterns"],
            )
        relative_gap = None
        if admm is not None:
            relative_gap = abs(solved["objective"] - admm["objective"]) / max(abs(admm["objective"]), 1e-12)
        certificate_holds = bool(task["certificate_region"]) and abs(solved["objective"] - reference_objective) <= 1e-3 * max(1.0, abs(reference_objective)) and movement <= 1e-2
        if certificate_holds:
            optimality = "ANALYTIC_G_EQUALS_F"
        elif relative_gap is not None and relative_gap <= 1e-3 and admm and admm["converged"]:
            optimality = "SOLVER_AGREEMENT_UNCERTIFIED"
        else:
            optimality = "NUMERICALLY_UNCERTIFIED"
        if task["extension"] == "X1":
            accepted = optimality == "ANALYTIC_G_EQUALS_F"
            patterns = embedding if certificate_holds else solved["patterns"]
        else:
            accepted = bool(solved["converged"])
            patterns = solved["patterns"]
        if task["extension"] == "X1" and task["name"] == "control_G_equals_F":
            accepted = True
            patterns = embedding
            optimality = "ANALYTIC_G_EQUALS_F" if certificate_holds or gamma == 0.0 else optimality
        fused = fusion_summary(patterns, affinity)
        row: dict[str, Any] = {
            "job_id": task["job_id"],
            "extension": task["extension"],
            "name": task["name"],
            "dataset_id": task["dataset_id"],
            "benchmark": task["benchmark"],
            "prep": task["prep"],
            "role": task["role"],
            "contrast": task["contrast"],
            "gamma": gamma,
            "gamma_0": task["gamma_0"],
            "objective": float(weighted_objective(patterns, embedding, affinity, gamma, fidelity)),
            "irls_objective": float(solved["objective"]),
            "reference_G_equals_F_objective": float(reference_objective),
            "independent_objective": None if admm is None else float(admm["objective"]),
            "relative_objective_gap": relative_gap,
            "optimality_status": optimality,
            "clustering_accepted": bool(accepted),
            "irls_converged": bool(solved["converged"]),
            "irls_iterations": int(solved["n_iterations"]),
            "independent_converged": None if admm is None else bool(admm["converged"]),
            "independent_iterations": None if admm is None else int(admm["n_iterations"]),
            "primal_residual": None if admm is None else float(admm["primal_residual"]),
            "dual_residual": None if admm is None else float(admm["dual_residual"]),
            "fixed_point_residual": float(solved["fixed_point_residual"]),
            "relative_g_minus_f": movement,
            "edge_mass": float(total_mass(affinity)),
            "n_components": int(graph_summary(affinity, "W")["n_components"]),
            "wall_seconds": float(solved["wall_seconds"] + (0.0 if admm is None else admm["wall_seconds"])),
            "memory_kb": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "solver": solved["solver"],
            **fused,
        }
        if accepted or task["role"] in {"baseline", "control"}:
            greedy = summarize_family(run_family(patterns, labels, PRIMARY_INIT))
            row.update({f"greedy_{key}": value for key, value in greedy.items() if not isinstance(value, (list, np.ndarray))})
            row["greedy_acc_seeds"] = greedy["per_seed_acc"]
            row["greedy_nmi_seeds"] = greedy["per_seed_nmi"]
            row["greedy_inertia_seeds"] = greedy["per_seed_inertia"]
            row["labels_seed0"] = greedy["labels_seed0"].astype(int).tolist()
            if task["contrast"] in PRIMARY_CONTRASTS or task["role"] == "baseline":
                random_rows = summarize_family(run_family(patterns, labels, SENSITIVITY_INIT))
                row["random_acc_mean"] = random_rows["acc_mean"]
                row["random_acc_sd"] = random_rows["acc_sd"]
                row["random_nmi_mean"] = random_rows["nmi_mean"]
                row["random_nmi_sd"] = random_rows["nmi_sd"]
                row["random_min_inertia_acc"] = random_rows["min_inertia_acc"]
                row["random_min_inertia_nmi"] = random_rows["min_inertia_nmi"]
            if task["extension"] == "X5":
                movement_rows = np.linalg.norm(patterns - embedding, axis=1)
                prediction = greedy["labels_seed0"]
                # Post-hoc only. Not used to choose alpha.
                error = (prediction != labels).astype(np.float64)
                if movement_rows.std() > 0 and error.std() > 0:
                    row["posthoc_movement_error_corr"] = float(np.corrcoef(movement_rows, error)[0, 1])
                else:
                    row["posthoc_movement_error_corr"] = float("nan")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(_jsonable(row)))
        row["wall_seconds_total"] = time.perf_counter() - started
        return row
    except Exception as exc:  # noqa: BLE001 - keep one failed job from dropping the campaign
        failure = {"job_id": task["job_id"], "extension": task.get("extension"), "status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc(limit=12)}
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(failure))
        return failure


def assemble(commit: str) -> None:
    rows = []
    for path in sorted(JOBS.glob("*.json")):
        rows.append(json.loads(path.read_text()))
    OUT.mkdir(parents=True, exist_ok=True)
    configs = []
    trials = []
    solvers = []
    for row in rows:
        if row.get("status") == "FAILED":
            configs.append(row)
            continue
        configs.append({key: value for key, value in row.items() if not key.endswith("_seeds") and key != "labels_seed0"})
        solvers.append(
            {
                "job_id": row["job_id"],
                "extension": row["extension"],
                "dataset_id": row["dataset_id"],
                "prep": row["prep"],
                "gamma": row.get("gamma"),
                "objective": row.get("objective"),
                "irls_objective": row.get("irls_objective"),
                "independent_objective": row.get("independent_objective"),
                "relative_objective_gap": row.get("relative_objective_gap"),
                "optimality_status": row.get("optimality_status"),
                "irls_converged": row.get("irls_converged"),
                "independent_converged": row.get("independent_converged"),
                "primal_residual": row.get("primal_residual"),
                "dual_residual": row.get("dual_residual"),
                "fixed_point_residual": row.get("fixed_point_residual"),
                "relative_g_minus_f": row.get("relative_g_minus_f"),
                "irls_iterations": row.get("irls_iterations"),
                "independent_iterations": row.get("independent_iterations"),
            }
        )
        acc_seeds = row.get("greedy_acc_seeds") or []
        nmi_seeds = row.get("greedy_nmi_seeds") or []
        inertia = row.get("greedy_inertia_seeds") or []
        for seed, acc, nmi, value in zip(range(len(acc_seeds)), acc_seeds, nmi_seeds, inertia, strict=False):
            trials.append(
                {
                    "job_id": row["job_id"],
                    "extension": row["extension"],
                    "dataset_id": row["dataset_id"],
                    "benchmark": row["benchmark"],
                    "prep": row["prep"],
                    "name": row["name"],
                    "contrast": row.get("contrast"),
                    "role": row.get("role"),
                    "seed": seed,
                    "initialization": PRIMARY_INIT,
                    "acc": acc,
                    "nmi": nmi,
                    "inertia": value,
                    "clustering_accepted": row.get("clustering_accepted"),
                    "optimality_status": row.get("optimality_status"),
                }
            )
    _write_csv(OUT / "all_configurations.csv", configs)
    _write_csv(OUT / "solver_validation.csv", solvers)
    trial_path = OUT / "all_trials.csv"
    _write_csv(trial_path, trials)
    if trial_path.stat().st_size > 80_000_000:
        import gzip
        import hashlib

        compressed = OUT / "all_trials.csv.gz"
        with trial_path.open("rb") as source, gzip.open(compressed, "wb") as target:
            target.write(source.read())
        digest = hashlib.sha256(compressed.read_bytes()).hexdigest()
        (OUT / "all_trials.csv.gz.sha256").write_text(digest + "\n")
    paired = _paired(rows)
    _write_csv(OUT / "paired_ablation.csv", paired)
    manifest = {
        "commit": commit,
        "n_jobs": len(rows),
        "n_failed": sum(1 for row in rows if row.get("status") == "FAILED"),
        "n_trials": len(trials),
        "primary_contrasts": list(PRIMARY_CONTRASTS),
        "paper_gamma": list(PAPER_GAMMA),
        "x1_multipliers": list(X1_MULTIPLIERS),
        "x3_grid": list(X3_GRID),
        "betas": list(BETAS),
        "alphas": list(ALPHAS),
        "scales": list(SCALES),
        "primary_init": PRIMARY_INIT,
        "seeds": "0..49",
        "note": "Grids were fixed before measurement. YaleB versions are one benchmark when wins are counted.",
    }
    (OUT / "experiment_manifest.csv").write_text("key,value\n" + "\n".join(f"{key},{json.dumps(value)}" for key, value in manifest.items()) + "\n")
    _write_comparisons(rows, paired, commit)
    _figures(rows)


def _paired(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {(row.get("extension"), row.get("dataset_id"), row.get("prep"), row.get("name")): row for row in rows}
    specs = [
        ("X1", "gamma multiplier 1 versus SSC E8 gamma=1", "X1", None, "X1"),
        ("X2", "beta=1 versus beta=0", "beta_1", "beta_0", "X2"),
        ("X3", "mass-normalized tau=1 versus original gamma=1", "mass_tau_1.000000e+00", "original_gamma_1.000000e+00", "X3"),
        ("X4", "multi-scale versus mass-matched k=5", "multi", "single_k_5", "X4"),
        ("X5", "alpha=1 versus alpha=0", "alpha_1", "alpha_0", "X5"),
    ]
    # X1 baseline is the gamma=1 job. Find it by value rather than by the multiplier name.
    output = []
    datasets = sorted({(row.get("dataset_id"), row.get("prep")) for row in rows})
    for dataset_id, prep in datasets:
        for contrast, description, left_name, right_name, extension in specs:
            if contrast == "X1":
                candidates = [
                    row for row in rows
                    if row.get("extension") == "X1"
                    and row.get("dataset_id") == dataset_id
                    and row.get("prep") == prep
                    and row.get("contrast") == "X1"
                ]
                baseline_candidates = [
                    row for row in rows
                    if row.get("extension") == "X1"
                    and row.get("dataset_id") == dataset_id
                    and row.get("prep") == prep
                    and np.isclose(float(row.get("gamma") or -1), 1.0)
                    and str(row.get("name", "")).startswith("gamma_")
                ]
                if not candidates or not baseline_candidates:
                    continue
                left, right = candidates[0], baseline_candidates[0]
            else:
                left = index.get((extension, dataset_id, prep, left_name))
                right = index.get((extension, dataset_id, prep, right_name))
                if left is None or right is None:
                    continue
            if not left.get("greedy_acc_seeds") or not right.get("greedy_acc_seeds"):
                output.append(
                    {
                        "contrast": contrast,
                        "description": description,
                        "dataset_id": dataset_id,
                        "prep": prep,
                        "status": "NOT_CLUSTERED",
                        "left_job": left.get("job_id"),
                        "right_job": right.get("job_id"),
                        "left_optimality": left.get("optimality_status"),
                        "right_optimality": right.get("optimality_status"),
                    }
                )
                continue
            acc = np.asarray(left["greedy_acc_seeds"]) - np.asarray(right["greedy_acc_seeds"])
            nmi = np.asarray(left["greedy_nmi_seeds"]) - np.asarray(right["greedy_nmi_seeds"])
            acc_ci = paired_bootstrap(acc, seed=0)
            nmi_ci = paired_bootstrap(nmi, seed=1)
            output.append(
                {
                    "contrast": contrast,
                    "description": description,
                    "dataset_id": dataset_id,
                    "prep": prep,
                    "status": "PAIRED_CONDITIONAL_ON_FIXED_FG",
                    "left_job": left["job_id"],
                    "right_job": right["job_id"],
                    "left_optimality": left.get("optimality_status"),
                    "right_optimality": right.get("optimality_status"),
                    "left_accepted": left.get("clustering_accepted"),
                    "right_accepted": right.get("clustering_accepted"),
                    "acc_diff_mean": acc_ci["mean"],
                    "acc_ci_low": acc_ci["ci_low"],
                    "acc_ci_high": acc_ci["ci_high"],
                    "nmi_diff_mean": nmi_ci["mean"],
                    "nmi_ci_low": nmi_ci["ci_low"],
                    "nmi_ci_high": nmi_ci["ci_high"],
                    "ci_note": "95% bootstrap over seeds 0..49. Conditional on this fixed F and G. Not a dataset-level test.",
                }
            )
    return output


def _dataset_level(paired_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One number per independent dataset. Two YaleB versions are averaged on Y0."""
    summary = []
    for contrast in PRIMARY_CONTRASTS:
        per_dataset = []
        for benchmark, members in (
            ("ORL", [("ORL_att92", "Y0")]),
            ("JAFFE", [("JAFFE", "Y0")]),
            ("USPS", [("USPS", "Y0")]),
            ("YaleB", [("YaleB_dengcai32", "Y0"), ("YaleB_cropped2414", "Y0")]),
        ):
            values = [
                row["acc_diff_mean"]
                for row in paired_rows
                if row.get("contrast") == contrast
                and row.get("status") == "PAIRED_CONDITIONAL_ON_FIXED_FG"
                and (row.get("dataset_id"), row.get("prep")) in members
                and row.get("acc_diff_mean") is not None
            ]
            if values:
                per_dataset.append((benchmark, float(np.mean(values))))
        if not per_dataset:
            summary.append({"contrast": contrast, "n_datasets": 0, "mean_acc_diff": None})
            continue
        values = np.asarray([value for _name, value in per_dataset], dtype=np.float64)
        corrected = paired_bootstrap(values, seed=PRIMARY_CONTRASTS.index(contrast) + 3, n_boot=2000)
        # Report a Bonferroni 99% interval as well (5 prespecified contrasts).
        rng = np.random.default_rng(PRIMARY_CONTRASTS.index(contrast) + 17)
        draws = values[rng.integers(0, values.size, size=(4000, values.size))].mean(axis=1)
        low, high = np.quantile(draws, [0.005, 0.995])
        summary.append(
            {
                "contrast": contrast,
                "n_datasets": int(values.size),
                "datasets": "|".join(name for name, _value in per_dataset),
                "mean_acc_diff": float(values.mean()),
                "uncorrected_95_low": corrected["ci_low"],
                "uncorrected_95_high": corrected["ci_high"],
                "bonferroni_99_low": float(low),
                "bonferroni_99_high": float(high),
                "corrected_interval_excludes_0": bool(low > 0 or high < 0),
                "unit": "dataset, YaleB versions averaged, Y3 excluded",
            }
        )
    return summary


def _write_comparisons(rows: list[dict[str, Any]], paired_rows: list[dict[str, Any]], commit: str) -> None:
    level = _dataset_level(paired_rows)
    _write_csv(OUT / "dataset_level_contrasts.csv", level)
    lines = [
        "# Primary comparisons",
        "",
        f"Source commit recorded at assembly: `{commit}`.",
        "",
        "The five contrasts were fixed before measurement: X1 multiplier 1 versus SSC gamma=1; X2 beta=1 versus beta=0; X3 mass-normalized tau=1 versus original gamma=1; X4 multi-scale versus k=5; X5 alpha=1 versus alpha=0. Seed-level intervals are conditional on fixed F and G. Dataset-level intervals use ORL, JAFFE, USPS, and one YaleB unit. A Bonferroni 99% interval is reported across the five contrasts. An interval that covers 0 is not a significant improvement.",
        "",
        "| contrast | datasets | mean ACC diff | uncorrected 95% | Bonferroni 99% | excludes 0 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in level:
        lines.append(
            "| {contrast} | {datasets} | {mean} | [{lo}, {hi}] | [{clo}, {chi}] | {flag} |".format(
                contrast=row["contrast"],
                datasets=row.get("datasets", ""),
                mean="" if row.get("mean_acc_diff") is None else f"{row['mean_acc_diff']:.4f}",
                lo="" if row.get("uncorrected_95_low") is None else f"{row['uncorrected_95_low']:.4f}",
                hi="" if row.get("uncorrected_95_high") is None else f"{row['uncorrected_95_high']:.4f}",
                clo="" if row.get("bonferroni_99_low") is None else f"{row['bonferroni_99_low']:.4f}",
                chi="" if row.get("bonferroni_99_high") is None else f"{row['bonferroni_99_high']:.4f}",
                flag=row.get("corrected_interval_excludes_0", False),
            )
        )
    lines.append("")
    lines.append("Negative differences mean the prespecified extension scored lower than its matched SSC control on that contrast.")
    (OUT / "primary_comparison.md").write_text("\n".join(lines) + "\n")
    failures = [row for row in rows if row.get("status") == "FAILED" or row.get("optimality_status") == "NUMERICALLY_UNCERTIFIED" or row.get("clustering_accepted") is False]
    failure_lines = [
        "# Failure analysis",
        "",
        "Nonconverged solves and solver gaps are negative results. They are not certified improvements. X3's mass normalization is an exact gamma rescaling when the equivalent-gamma control matches; that match is not an algorithmic improvement. Stability weights are not class labels. Multi-scale neighborhoods can add edges; that was the prespecified failure hypothesis, not a result to be hidden.",
        "",
        f"Jobs assembled: {len(rows)}. Rows with a failed status, an uncertified optimum, or rejected clustering: {len(failures)}.",
        "",
    ]
    for row in failures[:80]:
        failure_lines.append(
            f"- {row.get('job_id')}: status={row.get('status', row.get('optimality_status'))}, converged={row.get('irls_converged')}, gap={row.get('relative_objective_gap')}, error={row.get('error', '')}"
        )
    (OUT / "failure_analysis.md").write_text("\n".join(failure_lines) + "\n")


def _figures(rows: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folder = OUT / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    by_dataset: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("extension") == "X1" and str(row.get("name", "")).startswith("gamma_"):
            by_dataset.setdefault(f"{row['dataset_id']}_{row['prep']}", []).append(row)
    for name, items in by_dataset.items():
        items = sorted(items, key=lambda item: float(item.get("gamma") or 0))
        figure, axis = plt.subplots(figsize=(6.5, 4))
        axis.plot([item["gamma"] for item in items], [item.get("relative_g_minus_f") or 0 for item in items], marker="o")
        gamma_0 = items[0].get("gamma_0")
        if gamma_0 and np.isfinite(gamma_0):
            axis.axvline(gamma_0, color="gray", linestyle="--", label="gamma_0")
        axis.set_xscale("log")
        axis.set_xlabel("gamma")
        axis.set_ylabel("||G-F|| / ||F||")
        axis.set_title(name)
        axis.legend()
        figure.tight_layout()
        figure.savefig(folder / f"x1_movement_{name}.png", dpi=120)
        plt.close(figure)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen and not isinstance(row[key], (list, dict)):
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def selected_tracks() -> list[dict[str, str]]:
    tracks = list(TRACKS)
    if os.environ.get("V3_PILOT") == "1":
        allowed = {"ORL_att92", "JAFFE", "USPS", "YaleB_dengcai32"}
        tracks = [track for track in tracks if track["dataset_id"] in allowed and track["prep"] == "Y0"]
    else:
        tracks.extend(SUPPLEMENTAL)
    only = os.environ.get("V3_ONLY")
    if only:
        chosen = set(only.split(","))
        tracks = [track for track in tracks if track["dataset_id"] in chosen]
    return tracks


def main() -> None:
    commit = git_commit()
    root = data_root()
    workers = int(os.environ.get("V3_WORKERS", "4"))
    graph_rows: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for spec in selected_tracks():
        payload = dict(spec)
        payload["historical_benchmark"] = spec["benchmark"]
        record = load_spec(root, payload)
        if not record.get("available"):
            print("SKIP", spec["dataset_id"], record.get("reason"))
            continue
        print("BUILD", spec["dataset_id"], spec["prep"], flush=True)
        built = build_track(spec, record["X"], record["y"])
        new_tasks, graphs = make_tasks(built)
        tasks.extend(new_tasks)
        graph_rows.extend(graphs)
        print(" tasks", len(new_tasks), "gamma0", built["meta"]["gamma_0"], flush=True)
    _write_csv(OUT / "graph_diagnostics.csv", graph_rows)
    pending = [task for task in tasks if not (JOBS / f"{task['job_id']}.json").is_file()]
    print(f"TASKS {len(tasks)} PENDING {len(pending)} WORKERS {workers}", flush=True)
    if pending:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(execute_task, task) for task in pending]
            for index, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                print(f"[{index}/{len(pending)}]", result.get("job_id"), result.get("optimality_status", result.get("status")), flush=True)
    assemble(commit)


if __name__ == "__main__":
    main()
