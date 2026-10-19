"""JAFFE from the official Zenodo zip, resized to 26x26."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from benchmarks.exceptions import as_float_matrix, as_int_labels

from .preprocessing import preprocess

_ARCHIVE = "jaffe.zip"
_SHA256 = "6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b"
# Sorted two-letter poser codes from the filenames. README_FIRST.txt lists
# KM, KA, YM, KR, NM, MK, UY, KL, TM, NA.
_SUBJECTS = ("KA", "KL", "KM", "KR", "MK", "NA", "NM", "TM", "UY", "YM")


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    path = data_dir(root) / _ARCHIVE
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}. The official zip is https://zenodo.org/records/14974867. "
            "curl on this network received HTTP 403; see download_datasets.py."
        )
    rows = []
    labels = []
    palette_count = 0
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if name.lower().endswith((".tif", ".tiff"))
        )
        for name in names:
            with archive.open(name) as handle:
                image = Image.open(io.BytesIO(handle.read()))
                image.load()
            if image.mode == "P":
                palette_count += 1
            if image.size != (256, 256):
                raise ValueError(f"{name} has size {image.size}, expected 256x256")
            rows.append(preprocess(image, 26, 26))
            code = Path(name).name[:2]
            if code not in _SUBJECTS:
                raise ValueError(f"unrecognized JAFFE poser code in {name}")
            labels.append(_SUBJECTS.index(code))
    x = as_float_matrix(np.vstack(rows))
    y = as_int_labels(np.asarray(labels), x.shape[0])
    if x.shape != (213, 676):
        raise ValueError(f"processed JAFFE shape {x.shape}")
    if sorted(np.unique(y).tolist()) != list(range(10)):
        raise ValueError("JAFFE did not yield 10 subjects")
    metadata = {
        "dataset_name": "JAFFE",
        "verification_status": "verified",
        "source_url": "https://zenodo.org/records/14974867",
        "archive_path": str(path),
        "SHA256_checksum": _SHA256,
        "n": 213,
        "number_of_classes": 10,
        "original_feature_dimension": 65536,
        "processed_feature_dimension": 676,
        "original_spatial_size": [256, 256],
        "processed_spatial_size": [26, 26],
        "subject_codes": {code: index for index, code in enumerate(_SUBJECTS)},
        "palette_mode_images": palette_count,
        "preprocessing_operations": [
            "convert each TIFF to 8-bit grayscale",
            "resize uint8 image from 256x256 to 26x26 with PIL bilinear",
            "divide by 255",
            "vectorize in C order",
        ],
        "sample_selection_method": "all 213 TIFFs in jaffe.zip, sorted by filename",
        "random_seed": "unknown",
        "redistribution": "forbidden by the Zenodo/JAFFE conditions of use",
    }
    return x, y, metadata
