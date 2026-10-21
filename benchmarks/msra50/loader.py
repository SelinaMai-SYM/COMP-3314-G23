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
        "Chang et al. state 1799 images and 12 classes resized to 32x32, "
        "with no URL. A sister paper (arXiv:1411.6241) cites He et al. 2004 "
        "for those counts; that bibliographic pointer is the 2005 TPAMI "
        "Laplacianfaces paper. He et al. (ICCV 2003 / TPAMI 2005) describe "
        "an MSRA collection of 12 people, 64-80 frontal images per person "
        "per session, cropped to 32x32, and do not print 1799 or a download "
        "URL. Matching 12 classes is not enough. No archive was saved. "
        "MSRA-B, MSRA10K, and MSRA-TD500 were not substituted. "
        "See benchmarks/msra50/README.md.",
    )
