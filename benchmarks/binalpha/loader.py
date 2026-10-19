"""BinAlpha loader. No traceable 26-by-30 release was found."""

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
        "BinAlpha",
        "No traceable 26-class by 30-image BinAlpha release was found. "
        "Binary Alphadigits was not substituted. "
        "See benchmarks/binalpha/manifest.yaml.",
    )
