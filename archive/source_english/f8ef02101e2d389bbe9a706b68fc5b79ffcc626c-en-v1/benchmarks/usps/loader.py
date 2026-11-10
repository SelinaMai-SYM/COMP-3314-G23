"""Standard USPS digits from the LIBSVM multiclass files."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from benchmarks.exceptions import as_float_matrix, as_int_labels

from .preprocessing import TEST_COUNTS, TRAIN_COUNTS, preprocess

_FILES = (
    ("usps.bz2", 7291, TRAIN_COUNTS),
    ("usps.t.bz2", 2007, TEST_COUNTS),
)


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    if version not in (None, "libsvm"):
        raise ValueError(f"unknown USPS version {version!r}")
    parts_x = []
    parts_y = []
    paths = []
    root_dir = data_dir(root)
    for relative, expected_n, expected_counts in _FILES:
        path = root_dir / relative
        if not path.is_file():
            raise FileNotFoundError(
                f"missing {path}. Run v1/scripts/download_datasets.py."
            )
        x_part, y_part = preprocess(path, expected_n, expected_counts)
        parts_x.append(x_part)
        parts_y.append(y_part)
        paths.append(str(path))
    x = as_float_matrix(np.vstack(parts_x))
    y = as_int_labels(np.concatenate(parts_y), x.shape[0])
    if x.shape != (9298, 256):
        raise ValueError(f"processed USPS shape {x.shape}")
    metadata = {
        "dataset_name": "USPS",
        "verification_status": "verified",
        "source_url": "https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass.html#usps",
        "archive_paths": paths,
        "n": 9298,
        "number_of_classes": 10,
        "original_feature_dimension": 256,
        "processed_feature_dimension": 256,
        "preprocessing_operations": [
            "parse LIBSVM files; features 1..256 become a length-256 vector",
            "map file labels 1..10 to digits 0..9",
            "no resize; the release is already 16x16",
            "no further scaling; stored values are already in [-1, 1]",
        ],
        "sample_selection_method": "all 7291 training rows followed by all 2007 test rows",
        "random_seed": "unknown",
        "SHA256_checksum": {
            "usps.bz2": "3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f",
            "usps.t.bz2": "a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e",
        },
    }
    return x, y, metadata
