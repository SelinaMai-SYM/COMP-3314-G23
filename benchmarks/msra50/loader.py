"""MSRA50 loader. No 1799-image, 12-class archive was obtained."""

from __future__ import annotations

from pathlib import Path

from benchmarks.exceptions import DatasetUnavailable


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    from benchmarks.data_paths import resolve_data_root
    return resolve_data_root() / "msra50" / "data"


def load_dataset(root: Path | None = None, version: str | None = None):
    del root, version
    raise DatasetUnavailable(
        "MSRA50",
        "MSRA50 is BLOCKED_NO_VERIFIED_DATA_URL. Chang et al. state 1799 "
        "images and 12 classes resized to 32x32, with no URL. Round 2 "
        "was given a null direct download URL. The page "
        "https://arxiv.org/html/2311.15214v1 is reference material only "
        "and was not saved as data. No MSRA-B, MSRA10K, TD500, or MSRC "
        "file was substituted. See benchmarks/msra50/README.md.",
    )
