"""MSRA50 loader. No 1799-image, 12-class archive was obtained."""

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
        "MSRA50",
        "No public archive with 1799 images and 12 classes was obtained. "
        "Other MSRA datasets were not substituted. "
        "See benchmarks/msra50/manifest.yaml.",
    )
