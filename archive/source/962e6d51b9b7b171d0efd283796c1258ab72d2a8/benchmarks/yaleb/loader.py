"""Extended Yale B from Deng Cai's already-resized 32x32 matrix."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat

from benchmarks.exceptions import as_float_matrix, as_int_labels

from .preprocessing import preprocess, scale_uint8_to_unit

_ARCHIVE = "YaleB_32x32.mat"
_SHA256 = "3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99"


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


_CROPPED_DIR = "cropped_wayback"
_CROPPED_ZIP_SHA256 = "8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573"
_CROPPED_INTERPOLATION = {
    "cropped2414": "bilinear",
    "cropped2414_nearest": "nearest",
    "cropped2414_bilinear": "bilinear",
    "cropped2414_bicubic": "bicubic",
}
_CROPPED_ARRAYS = {
    "nearest": "yaleb_cropped2414_32x32_nearest_uint8.npy",
    "bilinear": "yaleb_cropped2414_32x32_bilinear_uint8.npy",
    "bicubic": "yaleb_cropped2414_32x32_bicubic_uint8.npy",
}


def load_dataset(root: Path | None = None, version: str | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    if version in (None, "dengcai32"):
        return _load_dengcai(root)
    if version in _CROPPED_INTERPOLATION:
        return _load_cropped2414(root, version)
    raise ValueError(
        f"unknown YaleB version {version!r}; known versions: dengcai32, "
        + ", ".join(sorted(_CROPPED_INTERPOLATION))
    )


def _load_dengcai(root: Path | None) -> tuple[np.ndarray, np.ndarray, dict]:
    path = data_dir(root) / _ARCHIVE
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}. Run v1/scripts/download_datasets.py."
        )
    mat = loadmat(path)
    features = np.asarray(mat["fea"])
    ground = np.asarray(mat["gnd"]).reshape(-1)
    if features.shape != (2414, 1024) or features.dtype != np.uint8:
        raise ValueError(f"unexpected YaleB fea {features.shape} {features.dtype}")
    if ground.min() != 1 or ground.max() != 38 or len(np.unique(ground)) != 38:
        raise ValueError("YaleB gnd is not 38 labels in 1..38")
    x = as_float_matrix(preprocess(features))
    # File labels are 1..38. Integer ids below are those values minus 1.
    y = as_int_labels(ground.astype(np.int64) - 1, x.shape[0])
    metadata = {
        "dataset_name": "YaleB",
        "version": "dengcai32",
        "verification_status": "approximate",
        "source_url": "http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat",
        "archive_path": str(path),
        "SHA256_checksum": _SHA256,
        "n": 2414,
        "number_of_classes": 38,
        "original_feature_dimension": 1024,
        "processed_feature_dimension": 1024,
        "preprocessing_operations": [
            "no resize; the obtained matrix is already 32x32 (1024 uint8 values)",
            "divide by 255",
            "keep Deng Cai row order; MATLAB reshape on his page is column-major",
        ],
        "sample_selection_method": "all 2414 rows in YaleB_32x32.mat",
        "random_seed": "unknown",
        "label_encoding": "stored gnd 1..38 mapped to 0..37",
    }
    return x, y, metadata


def _load_cropped2414(root: Path | None, version: str) -> tuple[np.ndarray, np.ndarray, dict]:
    interpolation = _CROPPED_INTERPOLATION[version]
    base = data_dir(root) / _CROPPED_DIR
    array_path = base / "processed" / _CROPPED_ARRAYS[interpolation]
    label_path = base / "processed" / "yaleb_cropped2414_labels_int64.npy"
    if not array_path.is_file() or not label_path.is_file():
        raise FileNotFoundError(
            f"missing cropped Yale B arrays under {base}. "
            "See docs/repair_round1_dataset_recovery.md."
        )
    images = np.load(array_path)
    if images.shape != (2414, 32, 32) or images.dtype != np.uint8:
        raise ValueError(f"unexpected cropped Yale B array {images.shape} {images.dtype}")
    x = as_float_matrix(scale_uint8_to_unit(images).reshape(2414, -1))
    y = as_int_labels(np.load(label_path), x.shape[0])
    if sorted(np.unique(y).tolist()) != list(range(38)):
        raise ValueError("cropped Yale B did not yield 38 labels")
    metadata = {
        "dataset_name": "YaleB",
        "version": version,
        "verification_status": "obtained",
        "source_url": (
            "https://web.archive.org/web/20220127084451id_/"
            "http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip"
        ),
        "archive_path": str(base / "CroppedYale_wayback_20220127.zip"),
        "processed_array_path": str(array_path),
        "SHA256_checksum": _CROPPED_ZIP_SHA256,
        "n": 2414,
        "number_of_classes": 38,
        "original_feature_dimension": 192 * 168,
        "processed_feature_dimension": 1024,
        "original_spatial_size": [192, 168],
        "processed_spatial_size": [32, 32],
        "interpolation": interpolation,
        "pixel_range_native_uint8": [0, 255],
        "orientation": (
            "Non-ambient PGM files have header width 168 and height 192. "
            "The native stack before resize is (2414, 192, 168)."
        ),
        "preprocessing_operations": [
            "drop filenames containing Ambient",
            "drop non-PGM sidecars, including *.pgm.bad",
            "keep the remaining 2414 PGM images, all shaped (192, 168)",
            "sort by subject number then filename",
            f"resize to 32x32 with PIL {interpolation}",
            "divide by 255",
            "vectorize in C order",
        ],
        "sample_selection_method": (
            "2414 non-ambient PGM images from 38 subject folders "
            "(yaleB01-yaleB13 and yaleB15-yaleB39; yaleB14 is absent). "
            "This count matches the paper. It is not a claim that these "
            "pixels equal YaleB_32x32.mat."
        ),
        "random_seed": "unknown",
        "label_encoding": "subject numbers mapped to 0..37 in ascending subject-number order",
    }
    return x, y, metadata
