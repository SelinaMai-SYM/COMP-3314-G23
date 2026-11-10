"""Build and cache the E8 spectral embedding F and the shrunk patterns G.

F is computed once per dataset version. Gamma changes rebuild G only.
The calls match ``experiments.methods.prepare_ssc_family`` for
``variant='E8'``: k=5, G0=F, union kNN, symmetric normalized Laplacian,
median positive kNN bandwidth, Laplacian coefficient 2.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from SSC_method.graph_construction import knn_affinity
from SSC_method.objective import equation8_objective
from SSC_method.optimizer import shrink_embedding, variant_laplacian_coefficient
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from experiments.repair_diagnostics import make_g_init
from experiments.v2_kmeans_protocol.dataset_registry import REPO_ROOT, refuse_write_under_data_root
from experiments.v2_kmeans_protocol.kmeans_trials import sha256_array

RUNS_ROOT = REPO_ROOT / "runs" / "v2_kmeans_protocol"
CACHE_ROOT = RUNS_ROOT / "cache"
MANIFEST_ROOT = RUNS_ROOT / "manifests"

PRIMARY_GAMMA = 1.0
GAMMA_GRID = (1e-6, 1e-3, 1.0, 1e3, 1e6)
GAMMA_TOKENS = {
    1e-6: "1e-6",
    1e-3: "1e-3",
    1.0: "1",
    1e3: "1e3",
    1e6: "1e6",
}
SSC_MAX_ITER = 300
SSC_TOL = 1e-6
SSC_EPS = 1e-8


def gamma_token(gamma: float) -> str:
    for value, token in GAMMA_TOKENS.items():
        if abs(float(gamma) - value) <= 1e-15 * max(1.0, abs(value)):
            return token
    raise ValueError(f"gamma {gamma} is outside the predetermined grid")


def e8_graph_config() -> SpectralGraphConfig:
    """Shared Eq. (4) graph used for F. Shrinkage knobs are recorded only."""
    return SpectralGraphConfig(
        k=5,
        delta2=None,
        bandwidth_rule="median_positive_knn_squared_distance",
        symmetrization="union",
        laplacian="symmetric_normalized_eq4",
        eigenvector_selection="smallest",
        row_normalize=False,
        knn_method="auto",
        dense_threshold=512,
        variant="E8",
        g_init="F",
        g_init_seed=0,
        g_init_scale=1e-3,
        zero_residual_floor="median_pairwise",
        tol=SSC_TOL,
        max_iter=SSC_MAX_ITER,
        eps=SSC_EPS,
        kmeans_init="random",
        kmeans_n_init=1,
        seed=0,
    )


def upstream_config(gamma: float, max_iter: int = SSC_MAX_ITER) -> dict[str, Any]:
    coefficient = variant_laplacian_coefficient("E8")
    if coefficient != 2.0:
        raise RuntimeError("E8 Laplacian coefficient must be 2")
    return {
        "k": 5,
        "gamma": float(gamma),
        "variant": "E8",
        "laplacian_coefficient": coefficient,
        "g_init": "F",
        "g_init_seed": 0,
        "g_init_scale": 1e-3,
        "zero_residual_floor": "median_pairwise",
        "max_iter": int(max_iter),
        "tol": SSC_TOL,
        "eps": SSC_EPS,
        "symmetrization": "union",
        "laplacian": "symmetric_normalized_eq4",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "row_normalize": False,
        "knn_method": "auto",
        "dense_threshold": 512,
        "sign_convention": "largest_magnitude_positive",
        "eigenvector_selection": "smallest",
    }


def config_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def ssc_method_sha256() -> str:
    digest = hashlib.sha256()
    for path in sorted((REPO_ROOT / "SSC_method").glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def solver_status(converged: bool, n_iterations: int, max_iter: int) -> str:
    if converged:
        return f"CONVERGED n_iter={n_iterations}"
    return (
        "NONCONVERGED_RETURNED_ITERATE "
        f"n_iter={n_iterations} max_iter={max_iter} "
        "NOT_CERTIFIED_GLOBAL_OPTIMUM"
    )


@dataclass
class Representation:
    embedding: np.ndarray
    patterns: np.ndarray
    gamma: float
    converged: bool
    n_iterations: int
    fixed_point_residual: float
    equation8_objective: float
    solver_status: str
    f_sha256: str
    g_sha256: str
    config_hash: str
    embed_seconds: float
    shrink_seconds: float
    graph_k: int
    bandwidth_rule: str


def _affinity_on_f(embedding: np.ndarray, graph: SpectralGraphConfig):
    """W on F. Bandwidth is the median on F, not the bandwidth of the X graph."""
    return knn_affinity(
        embedding,
        k=graph.k,
        delta2=None,
        bandwidth_rule=graph.bandwidth_rule,
        knn_method=graph.knn_method,
        symmetrization=graph.symmetrization,
    )


def compute_embedding(
    features: np.ndarray,
    n_clusters: int,
    *,
    max_iter: int = SSC_MAX_ITER,
) -> tuple[np.ndarray, SpectralGraphConfig, float]:
    graph = e8_graph_config()
    if max_iter != graph.max_iter:
        graph = graph.with_updates(max_iter=int(max_iter))
    started = time.perf_counter()
    embedding, _info = spectral_embedding(
        np.asarray(features, dtype=np.float64),
        n_components=int(n_clusters),
        config=graph,
    )
    elapsed = time.perf_counter() - started
    return np.asarray(embedding, dtype=np.float64), graph, elapsed


def compute_patterns(
    embedding: np.ndarray,
    graph: SpectralGraphConfig,
    gamma: float,
    *,
    max_iter: int = SSC_MAX_ITER,
) -> Representation:
    affinity, graph_info = _affinity_on_f(embedding, graph)
    g0, g0_name = make_g_init(embedding, mode="F", seed=0, scale=1e-3)
    if g0_name != "F":
        raise RuntimeError("G0 must be F")
    started = time.perf_counter()
    shrinkage = shrink_embedding(
        embedding,
        affinity,
        gamma=float(gamma),
        eps=SSC_EPS,
        tol=SSC_TOL,
        max_iter=int(max_iter),
        G_init=g0,
        zero_residual_floor="median_pairwise",
        variant="E8",
    )
    shrink_seconds = time.perf_counter() - started
    objective = float(equation8_objective(shrinkage.patterns, embedding, affinity, float(gamma)))
    status = solver_status(bool(shrinkage.converged), int(shrinkage.n_iterations), int(max_iter))
    patterns = np.asarray(shrinkage.patterns, dtype=np.float64)
    config = upstream_config(gamma, max_iter=max_iter)
    return Representation(
        embedding=np.asarray(embedding, dtype=np.float64),
        patterns=patterns,
        gamma=float(gamma),
        converged=bool(shrinkage.converged),
        n_iterations=int(shrinkage.n_iterations),
        fixed_point_residual=float(shrinkage.fixed_point_residual),
        equation8_objective=objective,
        solver_status=status,
        f_sha256=sha256_array(embedding),
        g_sha256=sha256_array(patterns),
        config_hash=config_hash(config),
        embed_seconds=0.0,
        shrink_seconds=shrink_seconds,
        graph_k=int(graph_info["k"]),
        bandwidth_rule=str(graph_info.get("bandwidth_rule")),
    )


def compute_fg(
    features: np.ndarray,
    n_clusters: int,
    gamma: float,
    *,
    max_iter: int = SSC_MAX_ITER,
    embedding: np.ndarray | None = None,
    embed_seconds: float = 0.0,
) -> Representation:
    if embedding is None:
        embedding, graph, embed_seconds = compute_embedding(
            features, n_clusters, max_iter=max_iter
        )
    else:
        graph = e8_graph_config()
        if max_iter != graph.max_iter:
            graph = graph.with_updates(max_iter=int(max_iter))
        embedding = np.asarray(embedding, dtype=np.float64)
    result = compute_patterns(embedding, graph, gamma, max_iter=max_iter)
    result.embed_seconds = float(embed_seconds)
    return result


def _cache_paths(dataset_key: str, token: str) -> tuple[Path, Path]:
    cache = CACHE_ROOT / f"{dataset_key}__g{token}.npz"
    meta = CACHE_ROOT / f"{dataset_key}__g{token}.json"
    return cache, meta


def _manifest_path(dataset_key: str, token: str) -> Path:
    return MANIFEST_ROOT / f"{dataset_key}__g{token}.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    refuse_write_under_data_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def manifest_payload(
    result: Representation,
    *,
    dataset_key: str,
    dataset_sha: str,
    n_clusters: int,
) -> dict[str, Any]:
    return {
        "dataset_key": dataset_key,
        "dataset_sha256": dataset_sha,
        "gamma": result.gamma,
        "gamma_token": gamma_token(result.gamma),
        "variant": "E8",
        "laplacian_coefficient": 2.0,
        "g_init": "F",
        "k": result.graph_k,
        "bandwidth_rule": result.bandwidth_rule,
        "converged": result.converged,
        "n_iterations": result.n_iterations,
        "fixed_point_residual": result.fixed_point_residual,
        "equation8_objective": result.equation8_objective,
        "solver_status": result.solver_status,
        "f_sha256": result.f_sha256,
        "g_sha256": result.g_sha256,
        "config_hash": result.config_hash,
        "ssc_method_sha256": ssc_method_sha256(),
        "code_commit": git_head(),
        "n_clusters": int(n_clusters),
        "embed_seconds": result.embed_seconds,
        "shrink_seconds": result.shrink_seconds,
        "shape_f": list(result.embedding.shape),
        "shape_g": list(result.patterns.shape),
        "certified_global_optimum": False if not result.converged else "SOLVER_CONVERGED_NOT_A_PAPER_CERTIFICATE",
    }


def save_representation(
    result: Representation,
    *,
    dataset_key: str,
    dataset_sha: str,
    n_clusters: int,
) -> dict[str, Any]:
    token = gamma_token(result.gamma)
    cache, meta = _cache_paths(dataset_key, token)
    refuse_write_under_data_root(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    partial = cache.with_name(cache.name + ".partial")
    with partial.open("wb") as handle:
        np.savez_compressed(handle, F=result.embedding, G=result.patterns)
    partial.replace(cache)
    payload = manifest_payload(
        result,
        dataset_key=dataset_key,
        dataset_sha=dataset_sha,
        n_clusters=n_clusters,
    )
    _write_json(meta, payload)
    _write_json(_manifest_path(dataset_key, token), payload)
    return payload


def load_cached_representation(
    dataset_key: str,
    gamma: float,
    *,
    dataset_sha: str,
    n_clusters: int,
) -> Representation | None:
    """Reuse a cache only when the E8 contract and dataset hash match."""
    token = gamma_token(gamma)
    cache, meta_path = _cache_paths(dataset_key, token)
    if not cache.is_file() or not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    expected = upstream_config(gamma)
    if meta.get("dataset_sha256") != dataset_sha:
        return None
    if meta.get("ssc_method_sha256") != ssc_method_sha256():
        return None
    if meta.get("variant") != "E8" or float(meta.get("laplacian_coefficient", 0)) != 2.0:
        return None
    if meta.get("g_init") != "F" or int(meta.get("k", 0)) != 5:
        return None
    if meta.get("config_hash") != config_hash(expected):
        return None
    if int(meta.get("n_clusters", -1)) != int(n_clusters):
        return None
    with np.load(cache) as handle:
        embedding = np.asarray(handle["F"], dtype=np.float64)
        patterns = np.asarray(handle["G"], dtype=np.float64)
    if sha256_array(embedding) != meta["f_sha256"] or sha256_array(patterns) != meta["g_sha256"]:
        raise RuntimeError(f"cache checksum mismatch for {dataset_key} gamma={token}")
    return Representation(
        embedding=embedding,
        patterns=patterns,
        gamma=float(gamma),
        converged=bool(meta["converged"]),
        n_iterations=int(meta["n_iterations"]),
        fixed_point_residual=float(meta["fixed_point_residual"]),
        equation8_objective=float(meta["equation8_objective"]),
        solver_status=str(meta["solver_status"]),
        f_sha256=str(meta["f_sha256"]),
        g_sha256=str(meta["g_sha256"]),
        config_hash=str(meta["config_hash"]),
        embed_seconds=float(meta.get("embed_seconds", 0.0)),
        shrink_seconds=float(meta.get("shrink_seconds", 0.0)),
        graph_k=int(meta.get("k", 5)),
        bandwidth_rule=str(meta.get("bandwidth_rule", "")),
    )


__all__ = [
    "CACHE_ROOT",
    "GAMMA_GRID",
    "GAMMA_TOKENS",
    "MANIFEST_ROOT",
    "PRIMARY_GAMMA",
    "RUNS_ROOT",
    "SSC_MAX_ITER",
    "Representation",
    "compute_embedding",
    "compute_fg",
    "compute_patterns",
    "config_hash",
    "e8_graph_config",
    "gamma_token",
    "git_head",
    "load_cached_representation",
    "manifest_payload",
    "save_representation",
    "solver_status",
    "ssc_method_sha256",
    "upstream_config",
]
