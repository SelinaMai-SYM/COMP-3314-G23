"""Extended Yale B from Deng Cai's already-resized 32x32 matrix."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat

from benchmarks.exceptions import as_float_matrix, as_int_labels

from .preprocessing import preprocess

_ARCHIVE = "YaleB_32x32.mat"
_SHA256 = "3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99"


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
