"""Execute v3 jobs. One dataset worker does not commit the worktree."""

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

from SSC_method.graph_construction import knn_affinity
from SSC_method.objective import equation8_objective
from SSC_method.optimizer import shrink_embedding
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from baselines.lda_kmeans import fit_predict as lda_fit_predict
from baselines.llc import llc_normalized_embedding, yu_shi_discretize_state
from baselines.spls import oneshot_shrunk_patterns
from experiments.v2_kmeans_protocol.kmeans_trials import (
    GREEDY,
    RANDOM,
    VANILLA,
    fit_lloyd,
    sha256_array,
)
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from experiments.v3_reproduction.dataset_registry import l2_normalize_rows, load_spec, row_normalize
from experiments.v3_reproduction.method_registry import bind_config
from experiments.v3_reproduction.provenance import cache_key, fingerprint_matrix, json_ready
from experiments.v3_reproduction.solver_validation import (
    admm_equation8,
    positive_residual_stationarity,
    solver_status_from_irls,
)

KMEANS_FAMILY = (
    (RANDOM, "min_inertia"),
    (GREEDY, "min_inertia"),
    (VANILLA, "min_inertia"),
)


def _job_dir(payload: dict[str, Any]) -> Path:
    return Path(payload["runs_dir"]) / payload["dataset_id"]


def _job_paths(payload: dict[str, Any], job_id: str) -> tuple[Path, Path]:
    folder = _job_dir(payload)
    return folder / f"{job_id}.json", folder / f"{job_id}.trials.jsonl"


def _done(payload: dict[str, Any], job_id: str) -> bool:
    if not payload.get("resume", True):
        return False
    meta_path, trials_path = _job_paths(payload, job_id)
    if not meta_path.is_file():
        return False
    meta = json.loads(meta_path.read_text())
    if meta.get("code_commit") != payload["code_commit"]:
        return False
    if meta.get("status") not in {"COMPLETED", "INFEASIBLE"}:
        return False
    if meta.get("status") == "COMPLETED" and meta.get("n_trials", 0) > 0 and not trials_path.is_file():
        return False
    return True


def _write_job(payload: dict[str, Any], job_id: str, meta: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    meta_path, trials_path = _job_paths(payload, job_id)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        temporary = trials_path.with_suffix(".jsonl.tmp")
        with temporary.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(json_ready(row)) + "\n")
        temporary.replace(trials_path)
    meta = dict(meta)
    meta["job_id"] = job_id
    meta["n_trials"] = len(rows)
    meta["code_commit"] = payload["code_commit"]
    temporary_meta = meta_path.with_suffix(".json.tmp")
    temporary_meta.write_text(json.dumps(json_ready(meta), indent=2))
    temporary_meta.replace(meta_path)


def _fail(payload: dict[str, Any], job_id: str, requested: dict[str, Any], exc: BaseException) -> None:
    _write_job(
        payload,
        job_id,
        {
            "dataset_id": payload["dataset_id"],
            "historical_benchmark": payload["historical_benchmark"],
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=20),
            "requested_config": requested,
            "effective_config": {},
        },
        [],
    )


def _base_row(payload: dict[str, Any], **fields: Any) -> dict[str, Any]:
    row = {
        "dataset_id": payload["dataset_id"],
        "historical_benchmark": payload["historical_benchmark"],
        "counts_as_historical": payload["counts_as_historical"],
        "code_commit": payload["code_commit"],
    }
    row.update(fields)
    return row


def _kmeans_rows(
    payload: dict[str, Any],
    features: np.ndarray,
    labels: np.ndarray,
    *,
    method: str,
    prep: str,
    config_name: str,
    variant: str | None,
    report_role: str,
    n_batches: int,
    n_runs: int,
    include_vanilla: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    families = [RANDOM, GREEDY]
    if include_vanilla:
        families.append(VANILLA)
    for initialization in families:
        batches = n_batches if initialization != VANILLA else 1
        for batch in range(batches):
            for offset in range(n_runs):
                seed = n_runs * batch + offset
                fit = fit_lloyd(features, int(np.unique(labels).size), seed, initialization)
                scores = evaluate_partition(labels, fit["labels"])
                rows.append(
                    _base_row(
                        payload,
                        method=method,
                        prep=prep,
                        config_name=config_name,
                        variant=variant,
                        report_role=report_role,
                        initialization=initialization,
                        batch=batch,
                        seed=seed,
                        inertia=fit["inertia"],
                        selection_value=fit["inertia"],
                        selection_rule="min_inertia",
                        acc=scores["acc"],
                        nmi=scores["nmi"],
                        labels_sha256=sha256_array(fit["labels"]),
                        kmeans_n_iter=fit["kmeans_n_iter"],
                        kmeans_converged=fit["kmeans_converged"],
                        kmeans_warning=fit["kmeans_warning"],
                    )
                )
    return rows


def _centered_scores(features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    centered = features - features.mean(axis=0, keepdims=True)
    _left, singular, vt = np.linalg.svd(centered, full_matrices=False)
    scores = centered @ vt.T
    return scores, singular


def _graph_config(k: int, max_iter: int, tol: float) -> SpectralGraphConfig:
    return SpectralGraphConfig(
        k=int(k),
        delta2=None,
        row_normalize=False,
        symmetrization="union",
        laplacian="symmetric_normalized_eq4",
        eigenvector_selection="smallest",
        max_iter=int(max_iter),
        tol=float(tol),
        kmeans_init="random",
        kmeans_n_init=1,
        variant="E13",
    )


def _diagnostics(affinity: sparse.spmatrix, name: str) -> dict[str, Any]:
    matrix = sparse.csr_matrix(affinity)
    count, _labels = connected_components(matrix, directed=False, connection="weak")
    degree = np.asarray(matrix.sum(axis=1)).ravel()
    return {
        "graph": name,
        "n_connected_components": int(count),
        "nnz": int(matrix.nnz),
        "degree_min": float(degree.min()) if degree.size else None,
        "degree_mean": float(degree.mean()) if degree.size else None,
        "degree_max": float(degree.max()) if degree.size else None,
    }


def _priority(benchmark: str, gamma: float) -> bool:
    if benchmark == "ORL" and np.isclose(gamma, 1.0):
        return True
    if benchmark == "YaleB" and np.isclose(gamma, 1.0):
        return True
    if benchmark == "USPS" and np.isclose(gamma, 1000.0):
        return True
    return False


def _solve_ssc(
    embedding: np.ndarray,
    weights: sparse.spmatrix,
    gamma: float,
    variant: str,
    protocols: dict[str, Any],
    benchmark: str,
) -> dict[str, Any]:
    max_iter = int(protocols["ssc_max_iter"])
    tol = float(protocols["ssc_tol"])
    eps = float(protocols["ssc_eps"])
    first = shrink_embedding(
        embedding,
        weights,
        gamma=float(gamma),
        eps=eps,
        tol=tol,
        max_iter=max_iter,
        variant=variant,
        zero_residual_floor="median_pairwise",
    )
    checkpoint = {
        "n_iterations": first.n_iterations,
        "converged": bool(first.converged),
        "equation8_objective": equation8_objective(first.patterns, embedding, weights, gamma),
        "fixed_point_residual": first.fixed_point_residual,
        "max_iter": max_iter,
    }
    solved = first
    continued = False
    if (not first.converged) and _priority(benchmark, gamma):
        solved = shrink_embedding(
            embedding,
            weights,
            gamma=float(gamma),
            eps=eps,
            tol=tol,
            max_iter=int(protocols["ssc_extra_iters"]),
            G_init=first.patterns,
            variant=variant,
            zero_residual_floor="median_pairwise",
        )
        continued = True
    objective = equation8_objective(solved.patterns, embedding, weights, gamma)
    admm_summary = None
    independent_gap = None
    if variant == "E8":
        admm = admm_equation8(
            embedding,
            weights,
            float(gamma),
            max_iter=int(protocols["admm_max_iter"]),
            tol=float(protocols["admm_tol"]),
        )
        scale = max(1.0, abs(admm["objective"]))
        independent_gap = abs(objective - admm["objective"]) / scale if admm["converged"] else None
        admm_summary = {
            "status": admm["status"],
            "objective": admm["objective"],
            "n_iterations": admm["n_iterations"],
            "converged": admm["converged"],
            "relative_objective_gap_vs_irls": None
            if independent_gap is None
            else float(independent_gap),
        }
    stationarity = positive_residual_stationarity(solved.patterns, embedding, weights, float(gamma))
    status = solver_status_from_irls(
        converged=bool(solved.converged),
        n_iterations=int(solved.n_iterations),
        max_iter=int(protocols["ssc_extra_iters"] if continued else max_iter),
        stationarity=stationarity if stationarity.get("status") == "OPTIMALITY_VERIFIED" else None,
        independent_gap=independent_gap,
        gap_tol=float(protocols["optimality_gap_tol"]),
    )
    history = [
        {
            "iteration": row["iteration"],
            "equation8_objective": row["equation8_objective"],
            "sqrt_smoothed_equation8_objective": row["sqrt_smoothed_equation8_objective"],
            "irls_quadratic_surrogate": row["irls_quadratic_surrogate"],
            "linear_residual": row["linear_residual"],
            "step_frobenius": row["step_frobenius"],
        }
        for row in solved.history
    ]
    return {
        "patterns": solved.patterns,
        "status": status,
        "checkpoint_300": checkpoint,
        "continued_after_checkpoint": continued,
        "n_iterations": solved.n_iterations,
        "converged_by_iterate": bool(solved.converged),
        "equation8_objective": objective,
        "fixed_point_residual": solved.fixed_point_residual,
        "laplacian_coefficient": solved.laplacian_coefficient,
        "history": history,
        "admm": admm_summary,
        "stationarity": stationarity,
        "initial_zero_residual_floor": solved.initial_zero_residual_floor,
    }


def execute_dataset(payload: dict[str, Any]) -> dict[str, Any]:
    """Run every ready method on one loaded matrix."""
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    loaded = load_spec(Path(payload["data_root"]), payload["spec"])
    if not loaded.get("available"):
        return {
            "dataset_id": payload["dataset_id"],
            "status": loaded.get("blocker", "BLOCKED_DATA"),
            "reason": loaded.get("reason"),
        }
    features = loaded["X"]
    labels = loaded["y"]
    protocols = payload["protocols"]
    n_runs = int(protocols["n_runs"])
    n_clusters = int(np.unique(labels).size)
    preps = ["Y0", "Y1", "Y2", "Y3"] if payload["spec"].get("yaleb_factorial") else ["Y0"]
    completed = 0
    failed = 0
    for prep in preps:
        try:
            failed += _run_prep(
                payload,
                features,
                labels,
                n_clusters,
                prep,
                protocols,
                n_runs,
            )
            completed += 1
        except Exception as exc:  # noqa: BLE001 - one prep must not drop the dataset record
            failed += 1
            _fail(payload, f"prep_{prep}", {"prep": prep}, exc)
    return {
        "dataset_id": payload["dataset_id"],
        "status": "COMPLETED" if failed == 0 else "PARTIAL",
        "preps": completed,
        "prep_failures": failed,
        "n_samples": int(features.shape[0]),
        "n_classes": n_clusters,
    }


def _run_prep(
    payload: dict[str, Any],
    raw: np.ndarray,
    labels: np.ndarray,
    n_clusters: int,
    prep: str,
    protocols: dict[str, Any],
    n_runs: int,
) -> int:
    spectral_only = prep in {"Y2", "Y3"}
    prepared = raw if prep in {"Y0", "Y2"} else l2_normalize_rows(raw)
    fingerprint = fingerprint_matrix(prepared, labels)
    main_batches = int(protocols["n_batches_main"]) if prep == "Y0" else int(protocols["n_batches_grid"])
    grid_batches = int(protocols["n_batches_grid"])
    failures = 0
    if not spectral_only:
        failures += _guard(
            payload,
            f"kmeans__{prep}",
            lambda: _kmeans_on_matrix(payload, prepared, labels, fingerprint, prep, main_batches, n_runs),
        )
        failures += _guard(
            payload,
            f"pca__{prep}",
            lambda: _pca_jobs(
                payload, prepared, labels, fingerprint, prep, n_clusters, protocols, main_batches, grid_batches, n_runs
            ),
        )
        failures += _guard(
            payload,
            f"lda_kmeans__{prep}",
            lambda: _lda_job(payload, prepared, labels, fingerprint, prep, n_clusters, main_batches, n_runs),
        )
        failures += _guard(
            payload,
            f"llc__{prep}",
            lambda: _llc_jobs(
                payload, prepared, labels, fingerprint, prep, n_clusters, protocols, main_batches, grid_batches, n_runs
            ),
        )
        failures += _guard(
            payload,
            f"spls__{prep}",
            lambda: _spls_jobs(
                payload, prepared, labels, fingerprint, prep, protocols, main_batches, grid_batches, n_runs
            ),
        )
    failures += _guard(
        payload,
        f"spectral__{prep}",
        lambda: _spectral_jobs(
            payload,
            prepared,
            labels,
            fingerprint,
            prep,
            n_clusters,
            protocols,
            main_batches,
            grid_batches,
            n_runs,
        ),
    )
    return failures


def _guard(payload: dict[str, Any], job_id: str, function) -> int:
    try:
        function()
        return 0
    except Exception as exc:  # noqa: BLE001
        _fail(payload, job_id, {"job_id": job_id}, exc)
        return 1


def _kmeans_on_matrix(payload, features, labels, fingerprint, prep, n_batches, n_runs) -> None:
    job_id = f"kmeans__{prep}"
    if _done(payload, job_id):
        return
    requested = {
        "n_init": 1,
        "algorithm": "lloyd",
        "max_iter": 300,
        "tol": 1e-4,
        "initializations": [RANDOM, GREEDY, VANILLA],
        "n_runs": n_runs,
        "n_batches_random_greedy": n_batches,
        "prep": prep,
    }
    rows = _kmeans_rows(
        payload,
        features,
        labels,
        method="kmeans",
        prep=prep,
        config_name="raw",
        variant=None,
        report_role="reference" if prep == "Y0" else "diagnostic",
        n_batches=n_batches,
        n_runs=n_runs,
        include_vanilla=True,
    )
    bound = bind_config(requested, dict(requested))
    _write_job(
        payload,
        job_id,
        {
            "dataset_id": payload["dataset_id"],
            "historical_benchmark": payload["historical_benchmark"],
            "method": "kmeans",
            "prep": prep,
            "status": "COMPLETED",
            "report_role": "reference" if prep == "Y0" else "diagnostic",
            "fingerprint": fingerprint,
            "cache_key": cache_key(fingerprint=fingerprint, config=bound["effective_config"], code_commit=payload["code_commit"]),
            **bound,
        },
        rows,
    )


def _pca_jobs(payload, features, labels, fingerprint, prep, n_clusters, protocols, main_batches, grid_batches, n_runs) -> None:
    scores, singular = _centered_scores(features)
    total = float(np.sum(singular ** 2))
    rank = int(np.sum(singular > (singular[0] * 1e-10 if singular.size else 0.0)))
    for dimension in protocols["pca_dimensions"]:
        for method in ("pca_kmeans", "pca_sc"):
            job_id = f"{method}__{prep}__d{int(dimension):03d}"
            if _done(payload, job_id):
                continue
            requested = {
                "n_components": int(dimension),
                "whitening": False,
                "prep": prep,
                "n_runs": n_runs,
                "n_clusters": n_clusters,
            }
            if int(dimension) > rank or int(dimension) > scores.shape[1]:
                effective = dict(requested)
                effective["numerical_rank"] = rank
                effective["status_detail"] = "dimension exceeds centered-data rank"
                _write_job(
                    payload,
                    job_id,
                    {
                        "dataset_id": payload["dataset_id"],
                        "historical_benchmark": payload["historical_benchmark"],
                        "method": method,
                        "prep": prep,
                        "status": "INFEASIBLE",
                        "report_role": "grid",
                        "fingerprint": fingerprint,
                        "cache_key": cache_key(
                            fingerprint=fingerprint,
                            config=effective,
                            code_commit=payload["code_commit"],
                        ),
                        **bind_config(requested, effective),
                    },
                    [],
                )
                continue
            retained = float(np.sum(singular[: int(dimension)] ** 2))
            block = scores[:, : int(dimension)]
            if method == "pca_sc":
                config = _graph_config(int(protocols["spectral_k"]), int(protocols["ssc_max_iter"]), float(protocols["ssc_tol"]))
                block, info = spectral_embedding(block, n_components=n_clusters, config=config)
                eigen = np.asarray(info.get("eigenvalues", []), dtype=np.float64).tolist()
            else:
                eigen = None
            batches = grid_batches
            rows = _kmeans_rows(
                payload,
                np.asarray(block, dtype=np.float64),
                labels,
                method=method,
                prep=prep,
                config_name=f"d{int(dimension)}",
                variant=None,
                report_role="grid",
                n_batches=batches,
                n_runs=n_runs,
                include_vanilla=method == "pca_sc" and prep == "Y0",
            )
            effective = dict(requested)
            effective.update(
                {
                    "numerical_rank": rank,
                    "explained_variance_ratio": retained / total if total > 0 else None,
                    "whitening": False,
                    "n_batches": batches,
                    "eigenvalues": eigen,
                }
            )
            _write_job(
                payload,
                job_id,
                {
                    "dataset_id": payload["dataset_id"],
                    "historical_benchmark": payload["historical_benchmark"],
                    "method": method,
                    "prep": prep,
                    "status": "COMPLETED",
                    "report_role": "grid",
                    "fingerprint": fingerprint,
                    "cache_key": cache_key(
                        fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]
                    ),
                    **bind_config(requested, effective),
                },
                rows,
            )
    del main_batches


def _lda_job(payload, features, labels, fingerprint, prep, n_clusters, n_batches, n_runs) -> None:
    job_id = f"lda_kmeans__{prep}"
    if _done(payload, job_id):
        return
    requested = {
        "n_components": int(n_clusters - 1),
        "init": "random",
        "n_init": 1,
        "algorithm": "lloyd",
        "kmeans_max_iter": 300,
        "tol": 1e-4,
        "max_iter": 30,
        "sw_reg": 1e-8,
        "full_refit_each_seed": True,
        "prep": prep,
        "n_runs": n_runs,
        "n_batches": n_batches,
    }
    rows = []
    for batch in range(n_batches):
        for offset in range(n_runs):
            seed = n_runs * batch + offset
            predicted = lda_fit_predict(
                features,
                n_clusters,
                seed,
                n_components=n_clusters - 1,
                init="random",
                n_init=1,
                algorithm="lloyd",
                kmeans_max_iter=300,
                tol=1e-4,
                max_iter=30,
                sw_reg=1e-8,
            )
            scores = evaluate_partition(labels, predicted)
            rows.append(
                _base_row(
                    payload,
                    method="lda_kmeans",
                    prep=prep,
                    config_name=f"k-1={n_clusters - 1}",
                    variant=None,
                    report_role="reference" if prep == "Y0" else "diagnostic",
                    initialization="FULL_REFIT",
                    batch=batch,
                    seed=seed,
                    inertia=None,
                    selection_value=None,
                    selection_rule="not_comparable_across_subspaces",
                    acc=scores["acc"],
                    nmi=scores["nmi"],
                    labels_sha256=sha256_array(np.asarray(predicted)),
                )
            )
    effective = dict(requested)
    effective["objective"] = "ratio_of_traces_under_Sw_orthonormal_constraint"
    _write_job(
        payload,
        job_id,
        {
            "dataset_id": payload["dataset_id"],
            "historical_benchmark": payload["historical_benchmark"],
            "method": "lda_kmeans",
            "prep": prep,
            "status": "COMPLETED",
            "report_role": "reference" if prep == "Y0" else "diagnostic",
            "fingerprint": fingerprint,
            "cache_key": cache_key(fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]),
            **bind_config(requested, effective),
        },
        rows,
    )


def _llc_jobs(payload, features, labels, fingerprint, prep, n_clusters, protocols, main_batches, grid_batches, n_runs) -> None:
    scale = float(np.mean(np.linalg.norm(features, axis=1)))
    sigma0_sq = scale ** 2 if scale > 0 else 1.0
    configs = []
    for ridge in protocols["llc_ridge"]:
        configs.append((float(ridge), 1.0, float(ridge) == 1.0))
    for multiplier in protocols["llc_bandwidth_multipliers"]:
        if float(multiplier) == 1.0:
            continue
        configs.append((1.0, float(multiplier), False))
    for ridge, multiplier, is_reference in configs:
        job_id = f"llc__{prep}__r{ridge:g}__m{multiplier:g}"
        if _done(payload, job_id):
            continue
        bandwidth = sigma0_sq * multiplier
        requested = {
            "n_neighbors": int(protocols["llc_k"]),
            "llc_ridge": ridge,
            "llc_kernel": "gaussian",
            "llc_kernel_bandwidth": bandwidth,
            "bandwidth_multiplier": multiplier,
            "sigma0_squared": sigma0_sq,
            "prep": prep,
            "n_runs": n_runs,
        }
        embedding, info = llc_normalized_embedding(
            features,
            n_clusters=n_clusters,
            n_neighbors=int(protocols["llc_k"]),
            reg=ridge,
            kernel="gaussian",
            gamma=bandwidth,
        )
        batches = main_batches if is_reference and prep == "Y0" else grid_batches
        rows = []
        for batch in range(batches):
            for offset in range(n_runs):
                seed = n_runs * batch + offset
                state = yu_shi_discretize_state(embedding, seed, max_iter=30, tol=1e-8)
                scores = evaluate_partition(labels, state["labels"])
                rows.append(
                    _base_row(
                        payload,
                        method="llc",
                        prep=prep,
                        config_name=f"ridge={ridge:g}|mult={multiplier:g}",
                        variant=None,
                        report_role="reference" if is_reference else "grid",
                        initialization="YU_SHI",
                        batch=batch,
                        seed=seed,
                        inertia=None,
                        selection_value=state["objective"],
                        selection_rule="min_procrustes",
                        acc=scores["acc"],
                        nmi=scores["nmi"],
                        labels_sha256=sha256_array(state["labels"]),
                        procrustes_objective=state["objective"],
                        discretization_converged=state["converged"],
                    )
                )
        effective = dict(requested)
        effective.update(
            {
                "eigen_solver": info["solver"],
                "llc_kernel_bandwidth": info["llc_kernel_bandwidth"],
                "n_batches": batches,
                "legacy_measurements": "PRE_FIX_LEGACY_not_copied",
            }
        )
        _write_job(
            payload,
            job_id,
            {
                "dataset_id": payload["dataset_id"],
                "historical_benchmark": payload["historical_benchmark"],
                "method": "llc",
                "prep": prep,
                "status": "COMPLETED",
                "report_role": "reference" if is_reference else "grid",
                "fingerprint": fingerprint,
                "cache_key": cache_key(fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]),
                **bind_config(requested, effective),
            },
            rows,
        )


def _spls_jobs(payload, features, labels, fingerprint, prep, protocols, main_batches, grid_batches, n_runs) -> None:
    for alpha in protocols["slps_alpha"]:
        shrunk, info = oneshot_shrunk_patterns(
            features, alpha=float(alpha), n_neighbors=int(protocols["slps_k"])
        )
        scores, singular = _centered_scores(shrunk)
        rank = int(scores.shape[1])
        for dimension in protocols["pca_dimensions"]:
            reference = np.isclose(float(alpha), 0.5) and int(dimension) == 50 and prep == "Y0"
            job_id = f"spls__{prep}__a{float(alpha):.2f}__d{int(dimension):03d}"
            if _done(payload, job_id):
                continue
            requested = {
                "alpha": float(alpha),
                "beta": 0.0,
                "form": "one_shot_eq18",
                "n_neighbors": int(protocols["slps_k"]),
                "n_components": int(dimension),
                "local_scaling": "zelnik_manor",
                "clustering_stage": "kmeans",
                "prep": prep,
                "n_runs": n_runs,
            }
            if int(dimension) > rank:
                effective = dict(requested)
                effective["numerical_rank"] = rank
                _write_job(
                    payload,
                    job_id,
                    {
                        "dataset_id": payload["dataset_id"],
                        "historical_benchmark": payload["historical_benchmark"],
                        "method": "spls",
                        "prep": prep,
                        "status": "INFEASIBLE",
                        "report_role": "grid",
                        "fingerprint": fingerprint,
                        "graph": info,
                        "cache_key": cache_key(fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]),
                        **bind_config(requested, effective),
                    },
                    [],
                )
                continue
            batches = main_batches if reference else grid_batches
            rows = _kmeans_rows(
                payload,
                scores[:, : int(dimension)],
                labels,
                method="spls",
                prep=prep,
                config_name=f"alpha={float(alpha):.2f}|d={int(dimension)}",
                variant="one_shot",
                report_role="repeatability_probe" if reference else "grid",
                n_batches=batches,
                n_runs=n_runs,
                include_vanilla=False,
            )
            effective = dict(requested)
            effective["numerical_rank"] = rank
            effective["n_batches"] = batches
            effective["explained_variance_ratio_numerator"] = float(np.sum(singular[: int(dimension)] ** 2))
            _write_job(
                payload,
                job_id,
                {
                    "dataset_id": payload["dataset_id"],
                    "historical_benchmark": payload["historical_benchmark"],
                    "method": "spls",
                    "prep": prep,
                    "status": "COMPLETED",
                    "report_role": "repeatability_probe" if reference else "grid",
                    "fingerprint": fingerprint,
                    "cache_key": cache_key(fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]),
                    **bind_config(requested, effective),
                },
                rows,
            )
    del grid_batches



def _one_ssc_gamma(
    payload, embedding, affinity_f, labels, fingerprint, prep, diagnostics,
    protocols, variant, gamma, main_batches, grid_batches, n_runs, job_id,
) -> None:
    solved = _solve_ssc(
        embedding,
        affinity_f,
        float(gamma),
        str(variant),
        protocols,
        payload["historical_benchmark"],
    )
    reference = prep == "Y0" and np.isclose(float(gamma), 1.0)
    batches = main_batches if reference else grid_batches
    rows = _kmeans_rows(
        payload,
        solved["patterns"],
        labels,
        method="ssc",
        prep=prep,
        config_name=f"{variant}|gamma={float(gamma):.0e}",
        variant=str(variant),
        report_role="reference" if reference else "grid",
        n_batches=batches,
        n_runs=n_runs,
        include_vanilla=True,
    )
    matched = _kmeans_rows(
        payload,
        embedding,
        labels,
        method="sc_matched_to_ssc",
        prep=prep,
        config_name=f"{variant}|gamma={float(gamma):.0e}|matched_F",
        variant=str(variant),
        report_role="matched_F",
        n_batches=batches,
        n_runs=n_runs,
        include_vanilla=False,
    )
    for row in matched:
        row["paired_method"] = "ssc"
        row["paired_variant"] = str(variant)
        row["ssc_gamma"] = float(gamma)
    for row in rows:
        row["ssc_gamma"] = float(gamma)
    requested = {
        "ssc_gamma": float(gamma),
        "variant": str(variant),
        "k": int(protocols["spectral_k"]),
        "affinity_delta_squared": None,
        "max_iter": int(protocols["ssc_max_iter"]),
        "tol": float(protocols["ssc_tol"]),
        "eps": float(protocols["ssc_eps"]),
        "zero_residual_floor": "median_pairwise",
        "prep": prep,
        "n_runs": n_runs,
        "n_batches": batches,
    }
    effective = dict(requested)
    effective["laplacian_coefficient"] = solved["laplacian_coefficient"]
    effective["solver_status"] = solved["status"]
    _write_job(
        payload,
        job_id,
        {
            "dataset_id": payload["dataset_id"],
            "historical_benchmark": payload["historical_benchmark"],
            "method": "ssc",
            "prep": prep,
            "variant": str(variant),
            "status": "COMPLETED",
            "solver_status": solved["status"],
            "report_role": "reference" if reference else "grid",
            "fingerprint": fingerprint,
            "graph_diagnostics": diagnostics,
            "checkpoint_300": solved["checkpoint_300"],
            "continued_after_checkpoint": solved["continued_after_checkpoint"],
            "equation8_objective": solved["equation8_objective"],
            "fixed_point_residual": solved["fixed_point_residual"],
            "history": solved["history"],
            "admm": solved["admm"],
            "stationarity": solved["stationarity"],
            "initial_zero_residual_floor": solved["initial_zero_residual_floor"],
            "cache_key": cache_key(fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]),
            **bind_config(requested, effective),
        },
        rows + matched,
    )


def _spectral_jobs(
    payload, features, labels, fingerprint, prep, n_clusters, protocols, main_batches, grid_batches, n_runs
) -> None:
    config = _graph_config(int(protocols["spectral_k"]), int(protocols["ssc_max_iter"]), float(protocols["ssc_tol"]))
    embedding, info = spectral_embedding(features, n_components=n_clusters, config=config)
    if prep in {"Y2", "Y3"}:
        embedding = row_normalize(embedding)
    affinity_x, _graph_x = knn_affinity(features, config=config)
    affinity_f, graph_f = knn_affinity(embedding, k=int(protocols["spectral_k"]), delta2=None)
    diagnostics = {
        "A_on_X": _diagnostics(affinity_x, "A_on_X"),
        "W_on_F": _diagnostics(affinity_f, "W_on_F"),
        "embedding_eigenvalues": np.asarray(info.get("eigenvalues", []), dtype=np.float64).tolist(),
        "eigen_solver": info.get("eigen_solver"),
        "row_normalized_F": prep in {"Y2", "Y3"},
        "bandwidth_on_F": graph_f.get("delta2", graph_f.get("bandwidth")),
    }
    sc_batches = main_batches if prep == "Y0" else grid_batches
    sc_id = f"sc__{prep}"
    if not _done(payload, sc_id):
        requested = {
            "k": int(protocols["spectral_k"]),
            "affinity_delta_squared": None,
            "bandwidth_rule": "median_positive_knn_squared_distance",
            "symmetrization": "union",
            "laplacian": "symmetric_normalized_eq4",
            "row_normalize_input": False,
            "row_normalize_F": prep in {"Y2", "Y3"},
            "prep": prep,
            "n_runs": n_runs,
            "n_batches": sc_batches,
        }
        rows = _kmeans_rows(
            payload,
            embedding,
            labels,
            method="sc",
            prep=prep,
            config_name="k5_median_delta2",
            variant=None,
            report_role="reference" if prep == "Y0" else "diagnostic",
            n_batches=sc_batches,
            n_runs=n_runs,
            include_vanilla=True,
        )
        effective = dict(requested)
        effective["shared_F_with_ssc"] = True
        _write_job(
            payload,
            sc_id,
            {
                "dataset_id": payload["dataset_id"],
                "historical_benchmark": payload["historical_benchmark"],
                "method": "sc",
                "prep": prep,
                "status": "COMPLETED",
                "report_role": "reference" if prep == "Y0" else "diagnostic",
                "fingerprint": fingerprint,
                "graph_diagnostics": diagnostics,
                "cache_key": cache_key(fingerprint=fingerprint, config=effective, code_commit=payload["code_commit"]),
                **bind_config(requested, effective),
            },
            rows,
        )
    for variant in protocols["ssc_variants"]:
        for gamma in protocols["ssc_gamma"]:
            job_id = f"ssc__{prep}__{variant}__g{gamma:.0e}"
            if _done(payload, job_id):
                continue
            try:
                _one_ssc_gamma(
                    payload, embedding, affinity_f, labels, fingerprint, prep, diagnostics,
                    protocols, variant, float(gamma), main_batches, grid_batches, n_runs, job_id,
                )
            except Exception as exc:  # noqa: BLE001 - keep the other gamma values
                _fail(payload, job_id, {"ssc_gamma": float(gamma), "variant": str(variant), "prep": prep}, exc)
