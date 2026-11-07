"""Load v3 matrices from the read-only v1 archives."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from benchmarks import DatasetUnavailable, load_dataset
from experiments.v3_reproduction.provenance import fingerprint_matrix


def resolve_data_root(campaign: dict[str, Any] | None = None) -> Path:
    """External benchmark directory. A blank campaign field is not a sibling path."""
    if campaign and campaign.get("data_root"):
        root = Path(campaign["data_root"])
    else:
        env = os.environ.get("COMP3314_DATA_ROOT") or os.environ.get("DATA_ROOT")
        pointer = Path(__file__).resolve().parents[2] / "local" / "data_root.txt"
        if env:
            root = Path(env)
        elif pointer.is_file() and pointer.read_text().strip():
            root = Path(pointer.read_text().strip())
        else:
            raise FileNotFoundError("Set COMP3314_DATA_ROOT or local/data_root.txt")
    if not root.is_dir():
        raise FileNotFoundError(f"external data directory does not exist: {root}")
    return root


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
