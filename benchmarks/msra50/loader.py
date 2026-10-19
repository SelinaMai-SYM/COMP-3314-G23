"""MSRA50 loader. No 1799-image, 12-class archive was obtained."""

from __future__ import annotations

from pathlib import Path

from benchmarks.exceptions import DatasetUnavailable


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None):
    del root, version
    raise DatasetUnavailable(
        "MSRA50",
        "No archive with 1799 images and 12 classes was obtained on 2026-10-20. "
        "MSRA-B, MSRA10K, and MSRA-TD500 were not substituted. "
        "See docs/repair_round1_dataset_recovery.md.",
    )
