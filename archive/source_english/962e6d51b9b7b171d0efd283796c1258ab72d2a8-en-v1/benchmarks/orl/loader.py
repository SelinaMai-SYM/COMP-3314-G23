"""ORL loaders.

``load_dataset()`` with no version still returns the Olivetti 64x64 matrix
resized to 32x32. The AT&T 92x112 PGM release is selected only with an
explicit version such as ``"att92"``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat

from benchmarks.exceptions import as_float_matrix, as_int_labels

from .preprocessing import preprocess, scale_uint8_to_unit

_ARCHIVE = "olivettifaces.mat"
_SHA256 = "b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794"

_ATT_DIR = "att92"
_ATT_ZIP_SHA256 = "509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec"
_ATT_INTERPOLATION = {
    "att92": "bilinear",
    "att92_nearest": "nearest",
    "att92_bilinear": "bilinear",
    "att92_bicubic": "bicubic",
}
_ATT_ARRAYS = {
    "nearest": "orl_att92_32x32_nearest_uint8.npy",
    "bilinear": "orl_att92_32x32_bilinear_uint8.npy",
    "bicubic": "orl_att92_32x32_bicubic_uint8.npy",
}


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    if version in (None, "olivetti", "olivetti64"):
        return _load_olivetti(root)
    if version in _ATT_INTERPOLATION:
        return _load_att92(root, version)
    known = ", ".join(["olivetti", *sorted(_ATT_INTERPOLATION)])
    raise ValueError(f"unknown ORL version {version!r}; known versions: {known}")


def _load_olivetti(root: Path | None) -> tuple[np.ndarray, np.ndarray, dict]:
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
        "version": "olivetti64",
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


def _load_att92(root: Path | None, version: str) -> tuple[np.ndarray, np.ndarray, dict]:
    interpolation = _ATT_INTERPOLATION[version]
    base = data_dir(root) / _ATT_DIR
    array_path = base / "processed" / _ATT_ARRAYS[interpolation]
    label_path = base / "processed" / "orl_att92_labels_int64.npy"
    if not array_path.is_file() or not label_path.is_file():
        raise FileNotFoundError(
            f"missing AT&T ORL arrays under {base}. "
            "See docs/repair_round1_dataset_recovery.md."
        )
    images = np.load(array_path)
    if images.shape != (400, 32, 32) or images.dtype != np.uint8:
        raise ValueError(f"unexpected AT&T 32x32 array {images.shape} {images.dtype}")
    x = as_float_matrix(scale_uint8_to_unit(images).reshape(400, -1))
    y = as_int_labels(np.load(label_path), x.shape[0])
    if x.shape != (400, 1024):
        raise ValueError(f"processed AT&T ORL shape {x.shape}")
    if sorted(np.unique(y).tolist()) != list(range(40)) or not np.all(np.bincount(y) == 10):
        raise ValueError("AT&T ORL labels are not 40 subjects with 10 images each")
    metadata = {
        "dataset_name": "ORL",
        "version": version,
        "verification_status": "obtained",
        "source_url": "https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip",
        "archive_path": str(base / "att_faces.zip"),
        "processed_array_path": str(array_path),
        "SHA256_checksum": _ATT_ZIP_SHA256,
        "n": 400,
        "number_of_classes": 40,
        "original_feature_dimension": 112 * 92,
        "processed_feature_dimension": 1024,
        "original_spatial_size": [112, 92],
        "processed_spatial_size": [32, 32],
        "interpolation": interpolation,
        "pixel_range_native_uint8": [0, 251],
        "orientation": (
            "PGM header width 92, height 112. Saved native array is "
            "(400, 112, 92): axis 1 is file row (height), axis 2 is file column "
            "(width). No transpose was applied."
        ),
        "preprocessing_operations": [
            "read AT&T PGM files in subject directory s1..s40 and image name 1.pgm..10.pgm",
            f"resize each uint8 image to 32x32 with PIL {interpolation}",
            "divide by 255",
            "vectorize in C order",
        ],
        "sample_selection_method": "all 400 PGM images; label = subject number minus 1",
        "random_seed": "unknown",
        "not_olivetti": (
            "This release is 92x112 PGM. It is not the Olivetti 64x64 matrix "
            "used by load_dataset('ORL')."
        ),
    }
    return x, y, metadata
