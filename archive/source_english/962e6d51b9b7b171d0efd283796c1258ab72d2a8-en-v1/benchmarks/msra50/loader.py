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
        "MSRA50 is BLOCKED_DATA_NOT_OBTAINED. Chang et al. state 1799 "
        "images and 12 classes resized to 32x32, with no URL. Local "
        "inspection plus the UTS-affiliation AAAI 2015 PDF and the local "
        "arXiv:1411.6241v1 sister PDF give only literature counts "
        "(1799/12/1024), not a file. No 1799x12x1024 archive is in "
        "benchmarks/msra50/data/. Other MSRA corpora were not substituted. "
        "See benchmarks/msra50/README.md.",
    )
