"""Historical protocol registry using the current shared benchmark data root."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from benchmarks import DatasetUnavailable, load_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "configs" / "v2_dataset_registry.yaml"

_PACKAGE = {
    "ORL": "orl",
    "JAFFE": "jaffe",
    "YaleB": "yaleb",
    "USPS": "usps",
    "BinAlpha": "binalpha",
    "UMIST": "umist",
    "AR": "ar",
    "MSRA50": "msra50",
}


@dataclass(frozen=True)
class DatasetEntry:
    benchmark: str
    version: str
    paper_benchmark: str
    attempt_load: bool
    run_protocols: bool
    exact_dataset_status: str
    comparison_class: str
    benchmark_group: str
    counts_as_independent_benchmark: bool
    priority_repeat: bool
    notes: str

    @property
    def key(self) -> str:
        return f"{self.benchmark}__{self.version}"


def data_root() -> Path:
    """Shared benchmark root containing orl/data, jaffe/data, etc."""
    from benchmarks.data_paths import resolve_data_root
    return resolve_data_root()


def refuse_write_under_data_root(path: Path) -> None:
    """Raise if a campaign output would land inside the read-only data tree."""
    root = data_root()
    resolved = Path(path).resolve()
    if resolved == root or root in resolved.parents:
        raise RuntimeError(f"refusing to write inside DATA_ROOT: {resolved}")


def load_registry(path: Path | None = None) -> list[DatasetEntry]:
    payload = yaml.safe_load((path or DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    rows = payload.get("datasets") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("v2_dataset_registry.yaml needs a datasets list")
    entries: list[DatasetEntry] = []
    for row in rows:
        entries.append(
            DatasetEntry(
                benchmark=str(row["benchmark"]),
                version=str(row["version"]),
                paper_benchmark=str(row.get("paper_benchmark", row["benchmark"])),
                attempt_load=bool(row.get("attempt_load", False)),
                run_protocols=bool(row.get("run_protocols", False)),
                exact_dataset_status=str(row["exact_dataset_status"]),
                comparison_class=str(row["comparison_class"]),
                benchmark_group=str(row.get("benchmark_group", row["benchmark"])),
                counts_as_independent_benchmark=bool(
                    row.get("counts_as_independent_benchmark", True)
                ),
                priority_repeat=bool(row.get("priority_repeat", False)),
                notes=str(row.get("notes", "")).strip(),
            )
        )
    return entries


def data_dir_for(benchmark: str) -> Path:
    package = _PACKAGE.get(benchmark)
    if package is None:
        raise KeyError(f"no data package for {benchmark}")
    return data_root() / package / "data"


def dataset_sha256(features: np.ndarray, labels: np.ndarray) -> str:
    digest = hashlib.sha256()
    array = np.ascontiguousarray(features, dtype=np.float64)
    target = np.ascontiguousarray(labels, dtype=np.int64)
    digest.update(array.shape.__repr__().encode())
    digest.update(array.tobytes())
    digest.update(target.tobytes())
    return digest.hexdigest()


def probe_entry(entry: DatasetEntry) -> dict[str, Any]:
    """Load one registry row or record an explicit blocked status.

    A blocked row never becomes a numeric result of 0.
    """
    base = {
        "benchmark": entry.benchmark,
        "dataset_version": entry.version,
        "paper_benchmark": entry.paper_benchmark,
        "benchmark_group": entry.benchmark_group,
        "counts_as_independent_benchmark": entry.counts_as_independent_benchmark,
        "exact_dataset_status": entry.exact_dataset_status,
        "comparison_class": entry.comparison_class,
        "run_protocols": entry.run_protocols,
        "notes": entry.notes,
        "n": "",
        "n_features": "",
        "n_classes": "",
        "dataset_sha256": "",
        "archive_sha256": "",
        "loader_status": "",
        "experiment_status": "",
    }
    if not entry.attempt_load:
        base["loader_status"] = "NOT_ATTEMPTED"
        base["experiment_status"] = entry.exact_dataset_status
        return base
    try:
        features, labels, meta = load_dataset(
            entry.benchmark,
            root=data_dir_for(entry.benchmark),
            version=entry.version,
        )
    except DatasetUnavailable as exc:
        base["loader_status"] = "DATASET_UNAVAILABLE"
        base["experiment_status"] = "BLOCKED_DATA" if "BLOCKED" in str(exc).upper() or entry.benchmark == "MSRA50" else entry.exact_dataset_status
        base["notes"] = f"{entry.notes} Loader: {exc}".strip()
        if entry.benchmark == "MSRA50":
            base["experiment_status"] = "BLOCKED_DATA"
        elif entry.benchmark == "AR":
            base["experiment_status"] = "BLOCKED"
        elif not entry.run_protocols:
            base["experiment_status"] = entry.exact_dataset_status
        return base
    except FileNotFoundError as exc:
        base["loader_status"] = "MISSING_FILE"
        base["experiment_status"] = "BLOCKED_DATA"
        base["notes"] = f"{entry.notes} {exc}".strip()
        return base
    features = np.asarray(features, dtype=np.float64)
    labels = np.asarray(labels).reshape(-1)
    base.update(
        {
            "loader_status": "LOADED",
            "experiment_status": "READY" if entry.run_protocols else entry.exact_dataset_status,
            "n": int(features.shape[0]),
            "n_features": int(features.shape[1]),
            "n_classes": int(np.unique(labels).size),
            "dataset_sha256": dataset_sha256(features, labels),
            "archive_sha256": str(meta.get("SHA256_checksum", "")),
            "source_url": str(meta.get("source_url", "")),
            "loader_version": str(meta.get("version", entry.version)),
            "verification_status": str(meta.get("verification_status", "")),
        }
    )
    return base


def load_features(entry: DatasetEntry) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if not entry.run_protocols:
        raise RuntimeError(f"{entry.key} is not an eligible protocol target")
    features, labels, meta = load_dataset(
        entry.benchmark,
        root=data_dir_for(entry.benchmark),
        version=entry.version,
    )
    return (
        np.asarray(features, dtype=np.float64),
        np.asarray(labels).reshape(-1),
        dict(meta),
    )


__all__ = [
    "DEFAULT_REGISTRY",
    "DatasetEntry",
    "data_dir_for",
    "data_root",
    "dataset_sha256",
    "load_features",
    "load_registry",
    "probe_entry",
    "refuse_write_under_data_root",
]
