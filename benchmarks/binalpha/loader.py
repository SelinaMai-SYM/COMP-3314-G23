"""BinAlpha loader. No traceable 26-by-30 release was found."""

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
        "BinAlpha",
        "No 26-class by 30-image BinAlpha file was found on 2026-10-20. "
        "The NYU page cited by later papers describes Binary Alphadigits "
        "(36 classes, 39 images each). That file was not substituted. "
        "See docs/repair_round1_dataset_recovery.md.",
    )
