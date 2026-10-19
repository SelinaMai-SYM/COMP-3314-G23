"""AR Face Database loader. The archive was not obtained."""

from __future__ import annotations

from pathlib import Path

from benchmarks.exceptions import DatasetUnavailable


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None):
    del root
    raise DatasetUnavailable(
        "AR",
        "The AR Face Database is distributed by request with a password. "
        "No image archive was downloaded. See benchmarks/ar/manifest.yaml.",
    )
