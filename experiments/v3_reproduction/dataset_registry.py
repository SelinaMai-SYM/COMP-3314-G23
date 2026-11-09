"""Load matrices from the shared, independent benchmark data root."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from benchmarks import DatasetUnavailable, load_dataset
from experiments.v3_reproduction.provenance import fingerprint_matrix


def resolve_data_root(campaign: dict[str, Any] | None = None) -> Path:
    from benchmarks.data_paths import resolve_data_root as shared_resolver
    return shared_resolver(None if not campaign else campaign.get("data_root"))


def l2_normalize_rows(features: np.ndarray) -> np.ndarray:
    scale = np.linalg.norm(features, axis=1, keepdims=True)
    return features / np.maximum(scale, 1e-12)


def row_normalize(features: np.ndarray) -> np.ndarray:
    return l2_normalize_rows(features)


def load_spec(data_root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Return a load record. Failures stay visible and do not invent a matrix."""
    folder = data_root / spec["folder"]
    version = spec.get("version")
    record: dict[str, Any] = {
        "dataset_id": spec["dataset_id"],
        "historical_benchmark": spec["historical_benchmark"],
        "counts_as_historical": bool(spec.get("counts_as_historical", False)),
        "version": version,
        "folder": str(folder),
        "role": spec.get("role"),
    }
    try:
        features, labels, metadata = load_dataset(
            spec["loader_name"], root=folder, version=version
        )
    except DatasetUnavailable as exc:
        record["available"] = False
        record["blocker"] = spec.get("blocker", "BLOCKED_DATA")
        record["reason"] = str(exc)
        return record
    except (FileNotFoundError, OSError, ValueError) as exc:
        record["available"] = False
        record["blocker"] = spec.get("blocker", "BLOCKED_DATA")
        record["reason"] = f"{type(exc).__name__}: {exc}"
        return record
    features = np.asarray(features, dtype=np.float64)
    labels = np.asarray(labels).reshape(-1)
    record.update(
        {
            "available": True,
            "blocker": None,
            "reason": None,
            "X": features,
            "y": labels,
            "metadata": {key: metadata[key] for key in metadata if key != "images"},
            "n_samples": int(features.shape[0]),
            "n_features": int(features.shape[1]),
            "n_classes": int(np.unique(labels).size),
            "fingerprint": fingerprint_matrix(features, labels),
            "class_counts": {
                str(int(label)): int(count)
                for label, count in zip(*np.unique(labels, return_counts=True))
            },
        }
    )
    return record
