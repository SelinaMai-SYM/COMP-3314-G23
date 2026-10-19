"""ORL via the Olivetti/scikit-learn 64x64 release, resized to 32x32."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat

from benchmarks.exceptions import as_float_matrix, as_int_labels

from .preprocessing import preprocess

_ARCHIVE = "olivettifaces.mat"
_SHA256 = "b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794"


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    path = data_dir(root) / _ARCHIVE
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}. Run v1/scripts/download_datasets.py."
        )
    mat = loadmat(path)
    faces = np.asarray(mat["faces"])
    if faces.shape != (4096, 400) or faces.dtype != np.uint8:
        raise ValueError(f"unexpected Olivetti array {faces.shape} {faces.dtype}")
    # Same layout as sklearn.datasets.fetch_olivetti_faces: each column is one
    # image, then transpose so the 64x64 array matches that loader's images.
    images = faces.T.reshape((400, 64, 64)).transpose(0, 2, 1)
    x = as_float_matrix(preprocess(images, 32, 32))
    y = as_int_labels(np.arange(400) // 10, x.shape[0])
    if x.shape != (400, 1024):
        raise ValueError(f"processed ORL shape {x.shape}")
    if sorted(np.unique(y).tolist()) != list(range(40)):
        raise ValueError("ORL did not yield 40 subject ids")
    if not np.all(np.bincount(y) == 10):
        raise ValueError("ORL subjects are not 10 images each")
    metadata = {
        "dataset_name": "ORL",
        "verification_status": "approximate",
        "source_url": "https://ndownloader.figshare.com/files/5976027",
        "archive_path": str(path),
        "SHA256_checksum": _SHA256,
        "n": 400,
        "number_of_classes": 40,
        "original_feature_dimension": 4096,
        "processed_feature_dimension": 1024,
        "original_spatial_size": [64, 64],
        "processed_spatial_size": [32, 32],
        "preprocessing_operations": [
            "interpret olivettifaces.mat columns as 64x64 images using the scikit-learn axis order",
            "resize each uint8 image to 32x32 with PIL bilinear",
            "divide by 255",
            "vectorize in C order",
        ],
        "sample_selection_method": "all 400 images; label = column_index // 10",
        "random_seed": "unknown",
    }
    return x, y, metadata
