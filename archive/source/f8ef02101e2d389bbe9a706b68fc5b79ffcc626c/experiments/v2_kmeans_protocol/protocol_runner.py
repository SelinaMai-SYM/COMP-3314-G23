"""Run P1–P4 on one cached representation without refitting SSC per seed.

P1 and P2 are two aggregations of the same random Lloyd trials.
P3 and P4 are two aggregations of the same scikit-learn greedy k-means++ trials.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from experiments.v2_kmeans_protocol.dataset_registry import (
    DatasetEntry,
    dataset_sha256,
    load_features,
    refuse_write_under_data_root,
)
from experiments.v2_kmeans_protocol.kmeans_trials import (
    GREEDY,
    RANDOM,
    VANILLA,
    run_seed,
)
from experiments.v2_kmeans_protocol.representation_cache import (
    GAMMA_GRID,
    PRIMARY_GAMMA,
    RUNS_ROOT,
    Representation,
    compute_fg,
    gamma_token,
    git_head,
    load_cached_representation,
    save_representation,
)

TRIALS_ROOT = RUNS_ROOT / "trials"
ARRAYS_ROOT = RUNS_ROOT / "arrays"
FAILURES_ROOT = RUNS_ROOT / "failures"
CORE_SEEDS = list(range(50))
CORE_FAMILIES = (RANDOM, GREEDY)

TRIAL_FIELDS = [
    "trial_id",
    "benchmark",
    "dataset_version",
    "benchmark_group",
    "exact_dataset_status",
    "comparison_class",
    "method",
    "representation",
    "initialization_label",
    "initialization",
    "gamma",
    "batch_id",
    "seed",
    "n_init",
    "algorithm",
    "max_iter",
    "tol",
    "n_clusters",
    "inertia",
    "kmeans_n_iter",
    "kmeans_converged",
    "kmeans_warning",
    "acc",
    "nmi",
    "n_unique_predicted",
    "wall_seconds",
    "ssc_optimizer_status",
    "ssc_converged",
    "representation_sha256",
    "dataset_sha256",
    "config_hash",
    "code_commit",
    "sklearn_version",
    "numpy_version",
    "scipy_version",
    "python_version",
    "centers_sha256",
    "labels_sha256",
    "experiment_status",
]


def trials_path(entry: DatasetEntry) -> Path:
    return TRIALS_ROOT / f"{entry.key}.csv"


def library_versions() -> dict[str, str]:
    import sys

    import scipy
    import sklearn

    return {
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "sklearn_version": sklearn.__version__,
    }


def read_trials(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        missing = [name for name in TRIAL_FIELDS if name not in reader.fieldnames]
        if missing:
            raise RuntimeError(f"{path} is missing columns {missing}")
        return list(reader)


def _trial_key(row: dict[str, Any]) -> tuple[str, str, str, int, int]:
    return (
        str(row["initialization_label"]),
        str(row["representation"]),
        str(row["gamma"]),
        int(row["seed"]),
        int(row["batch_id"]),
    )


def append_trials(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    refuse_write_under_data_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.is_file()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAL_FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TRIAL_FIELDS})


def write_failure(entry: DatasetEntry, stage: str, status: str, message: str) -> Path:
    path = FAILURES_ROOT / f"{entry.key}__{stage}.json"
    refuse_write_under_data_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": entry.benchmark,
        "dataset_version": entry.version,
        "stage": stage,
        "experiment_status": status,
        "message": message,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def obtain_representation(
    entry: DatasetEntry,
    features: np.ndarray,
    labels: np.ndarray,
    gamma: float,
    *,
    embedding: np.ndarray | None = None,
    embed_seconds: float = 0.0,
    max_iter: int = 300,
) -> Representation:
    n_clusters = int(np.unique(labels).size)
    digest = dataset_sha256(features, labels)
    cached = load_cached_representation(
        entry.key,
        gamma,
        dataset_sha=digest,
        n_clusters=n_clusters,
    )
    if cached is not None and embedding is not None:
        from experiments.v2_kmeans_protocol.kmeans_trials import sha256_array

        if sha256_array(embedding) != cached.f_sha256:
            cached = None
    if cached is not None:
        return cached
    result = compute_fg(
        features,
        n_clusters,
        gamma,
        max_iter=max_iter,
        embedding=embedding,
        embed_seconds=embed_seconds,
    )
    if embedding is not None:
        from experiments.v2_kmeans_protocol.kmeans_trials import sha256_array

        if sha256_array(result.embedding) != sha256_array(embedding):
            raise RuntimeError("G was built on a different F than the cached embedding")
    save_representation(
        result,
        dataset_key=entry.key,
        dataset_sha=digest,
        n_clusters=n_clusters,
    )
    return result


def _identity(
    entry: DatasetEntry,
    *,
    method: str,
    representation: str,
    initialization_label: str,
    gamma_label: str,
    batch_id: int,
    n_clusters: int,
    solver_status: str,
    ssc_converged: str,
    representation_sha: str,
    dataset_sha: str,
    config_hash: str,
) -> dict[str, Any]:
    versions = library_versions()
    return {
        "benchmark": entry.benchmark,
        "dataset_version": entry.version,
        "benchmark_group": entry.benchmark_group,
        "exact_dataset_status": entry.exact_dataset_status,
        "comparison_class": entry.comparison_class,
        "method": method,
        "representation": representation,
        "initialization_label": initialization_label,
        "gamma": gamma_label,
        "batch_id": int(batch_id),
        "n_clusters": int(n_clusters),
        "ssc_optimizer_status": solver_status,
        "ssc_converged": ssc_converged,
        "representation_sha256": representation_sha,
        "dataset_sha256": dataset_sha,
        "config_hash": config_hash,
        "code_commit": git_head(),
        **versions,
    }


def run_family(
    entry: DatasetEntry,
    features_matrix: np.ndarray,
    labels: np.ndarray,
    *,
    method: str,
    representation: str,
    initialization_label: str,
    seeds: Iterable[int],
    batch_id: int,
    gamma_label: str,
    solver_status: str,
    ssc_converged: str,
    representation_sha: str,
    dataset_sha: str,
    config_hash_value: str,
) -> list[dict[str, Any]]:
    """Run missing seeds of one initialization family on one fixed matrix."""
    path = trials_path(entry)
    done = {
        _trial_key(row)
        for row in read_trials(path)
        if row.get("experiment_status") == "COMPLETED"
    }
    n_clusters = int(np.unique(labels).size)
    identity = _identity(
        entry,
        method=method,
        representation=representation,
        initialization_label=initialization_label,
        gamma_label=gamma_label,
        batch_id=batch_id,
        n_clusters=n_clusters,
        solver_status=solver_status,
        ssc_converged=ssc_converged,
        representation_sha=representation_sha,
        dataset_sha=dataset_sha,
        config_hash=config_hash_value,
    )
    written: list[dict[str, Any]] = []
    for seed in seeds:
        key = (initialization_label, representation, gamma_label, int(seed), int(batch_id))
        if key in done:
            continue
        row, assignment, centers = run_seed(
            features_matrix,
            labels,
            n_clusters,
            int(seed),
            initialization_label,
            identity,
        )
        row["trial_id"] = (
            f"{entry.key}__{representation}__{initialization_label}"
            f"__g{gamma_label}__b{batch_id}__s{seed}"
        )
        append_trials(path, [row])
        refuse_write_under_data_root(ARRAYS_ROOT)
        ARRAYS_ROOT.mkdir(parents=True, exist_ok=True)
        np.save(ARRAYS_ROOT / f"{row['trial_id']}.npy", np.asarray(assignment, dtype=np.int16))
        np.save(ARRAYS_ROOT / f"{row['trial_id']}__centers.npy", np.asarray(centers, dtype=np.float64))
        written.append(row)
        done.add(key)
    return written


def _matrix_jobs(result: Representation, include_f: bool, include_g: bool):
    jobs = []
    if include_f:
        jobs.append(
            (
                "SC",
                "F",
                result.embedding,
                "NA",
                "NOT_APPLICABLE_SPECTRAL_EMBEDDING",
                "",
                result.f_sha256,
            )
        )
    if include_g:
        jobs.append(
            (
                "SSC",
                "G",
                result.patterns,
                gamma_token(result.gamma),
                result.solver_status,
                str(result.converged),
                result.g_sha256,
            )
        )
    return jobs


def run_protocols_on_representation(
    entry: DatasetEntry,
    labels: np.ndarray,
    result: Representation,
    *,
    families: tuple[str, ...] = CORE_FAMILIES,
    seeds: Iterable[int] = CORE_SEEDS,
    batch_id: int = 0,
    include_f: bool = True,
    include_g: bool = True,
    dataset_sha: str,
) -> None:
    for method, representation, matrix, gamma_label, status, converged, digest in _matrix_jobs(
        result, include_f, include_g
    ):
        for family in families:
            run_family(
                entry,
                matrix,
                labels,
                method=method,
                representation=representation,
                initialization_label=family,
                seeds=seeds,
                batch_id=batch_id,
                gamma_label=gamma_label,
                solver_status=status,
                ssc_converged=converged,
                representation_sha=digest,
                dataset_sha=dataset_sha,
                config_hash_value=result.config_hash,
            )


def run_primary(entry: DatasetEntry, *, max_iter: int = 300) -> Representation:
    features, labels, _meta = load_features(entry)
    digest = dataset_sha256(features, labels)
    result = obtain_representation(entry, features, labels, PRIMARY_GAMMA, max_iter=max_iter)
    run_protocols_on_representation(
        entry,
        labels,
        result,
        families=CORE_FAMILIES,
        seeds=CORE_SEEDS,
        batch_id=0,
        include_f=True,
        include_g=True,
        dataset_sha=digest,
    )
    return result


def run_gamma_grid(entry: DatasetEntry, *, max_iter: int = 300) -> None:
    """Recompute G on the gamma grid. SC trials stay on the original F."""
    features, labels, _meta = load_features(entry)
    digest = dataset_sha256(features, labels)
    primary = obtain_representation(entry, features, labels, PRIMARY_GAMMA, max_iter=max_iter)
    run_protocols_on_representation(
        entry,
        labels,
        primary,
        families=CORE_FAMILIES,
        seeds=CORE_SEEDS,
        batch_id=0,
        include_f=True,
        include_g=True,
        dataset_sha=digest,
    )
    for gamma in GAMMA_GRID:
        if gamma_token(gamma) == gamma_token(PRIMARY_GAMMA):
            continue
        result = obtain_representation(
            entry,
            features,
            labels,
            gamma,
            embedding=primary.embedding,
            embed_seconds=primary.embed_seconds,
            max_iter=max_iter,
        )
        if result.f_sha256 != primary.f_sha256:
            raise RuntimeError(
                f"{entry.key} gamma {gamma_token(gamma)} changed F "
                f"({result.f_sha256} != {primary.f_sha256})"
            )
        run_protocols_on_representation(
            entry,
            labels,
            result,
            families=CORE_FAMILIES,
            seeds=CORE_SEEDS,
            batch_id=0,
            include_f=False,
            include_g=True,
            dataset_sha=digest,
        )


def run_vanilla(entry: DatasetEntry, *, max_iter: int = 300) -> None:
    features, labels, _meta = load_features(entry)
    digest = dataset_sha256(features, labels)
    result = obtain_representation(entry, features, labels, PRIMARY_GAMMA, max_iter=max_iter)
    run_protocols_on_representation(
        entry,
        labels,
        result,
        families=(VANILLA,),
        seeds=CORE_SEEDS,
        batch_id=0,
        include_f=True,
        include_g=True,
        dataset_sha=digest,
    )


def repeat_seeds(batch_id: int, batch_size: int = 50) -> list[int]:
    start = int(batch_id) * int(batch_size)
    return list(range(start, start + int(batch_size)))


def run_repeatability(
    entry: DatasetEntry,
    *,
    n_batches: int = 10,
    max_iter: int = 300,
) -> int:
    """Independent best-of-50 batches. Batch 0 is the primary seed block 0..49.

    Returns the number of batch ids that have a complete core family set
    after this call, including batch 0 when the primary trials already exist.
    """
    if n_batches < 1:
        raise ValueError("n_batches must be >= 1")
    features, labels, _meta = load_features(entry)
    digest = dataset_sha256(features, labels)
    result = obtain_representation(entry, features, labels, PRIMARY_GAMMA, max_iter=max_iter)
    for batch_id in range(int(n_batches)):
        run_protocols_on_representation(
            entry,
            labels,
            result,
            families=CORE_FAMILIES,
            seeds=repeat_seeds(batch_id),
            batch_id=batch_id,
            include_f=True,
            include_g=True,
            dataset_sha=digest,
        )
    return int(n_batches)


__all__ = [
    "ARRAYS_ROOT",
    "CORE_FAMILIES",
    "CORE_SEEDS",
    "TRIAL_FIELDS",
    "TRIALS_ROOT",
    "append_trials",
    "obtain_representation",
    "read_trials",
    "repeat_seeds",
    "run_family",
    "run_gamma_grid",
    "run_primary",
    "run_repeatability",
    "run_vanilla",
    "trials_path",
    "write_failure",
]
