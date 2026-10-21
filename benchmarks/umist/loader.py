"""Sheffield/UMIST loader.

The default call still raises ``DatasetUnavailable``. The 1997 archive and
the pre-cropped archive were saved, but neither file contains 564 images.
``version="precropped575"`` loads the 575-image cropped release and records
that it is not the 564-image set.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat

from benchmarks.exceptions import DatasetUnavailable, as_float_matrix, as_int_labels

_UNAVAILABLE = (
    "No 564-image UMIST/Sheffield archive was obtained on 2026-10-20. "
    "The Wayback copy of http://images.ee.umist.ac.uk/danny/face.tar.gz "
    "has 1012 unique PGM files of 20 people with 122 different shapes. "
    "The pre-cropped cropped.tar.gz has 575 PGM files, 20 people, all "
    "112x92, of which 565 pixel arrays are unique. "
    "Figshare 67153214 is also 575 slices and is not pixel-identical to that tar. "
    "Use version='precropped575' or version='figshare575' to load those "
    "non-exact files. See docs/repair_round1_dataset_recovery.md."
)


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None):
    if version in (None, "sheffield564"):
        raise DatasetUnavailable("UMIST", _UNAVAILABLE)
    if version == "precropped575":
        return _load_precropped(root)
    if version == "figshare575":
        return _load_figshare(root)
    if version == "uncropped1012":
        raise DatasetUnavailable(
            "UMIST",
            "The uncropped face.tar.gz has 1012 unique PGM files and 122 "
            "spatial shapes, so it is not a single (n, d) matrix and it is "
            "not the 564-image set.",
        )
    raise ValueError(
        "unknown UMIST version "
        f"{version!r}; known versions: sheffield564, precropped575, "
        "figshare575, uncropped1012"
    )


def _load_precropped(root: Path | None):
    base = data_dir(root) / "wayback_sheffield" / "processed"
    images = np.load(base / "umist_precropped575_uint8.npy")
    labels = np.load(base / "umist_precropped575_labels_int64.npy")
    if images.shape != (575, 112, 92) or images.dtype != np.uint8:
        raise ValueError(f"unexpected UMIST cropped array {images.shape} {images.dtype}")
    x = as_float_matrix(images.astype(np.float64).reshape(575, -1) / 255.0)
    y = as_int_labels(labels, x.shape[0])
    if len(np.unique(y)) != 20:
        raise ValueError("UMIST cropped labels are not 20 classes")
    metadata = {
        "dataset_name": "UMIST",
        "version": "precropped575",
        "verification_status": "approximate",
        "source_url": (
            "https://web.archive.org/web/20070805190146id_/"
            "http://images.ee.umist.ac.uk/danny/cropped.tar.gz"
        ),
        "archive_path": str(
            data_dir(root) / "wayback_sheffield" / "cropped_wayback_20070805.tar.gz"
        ),
        "SHA256_checksum": "c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4",
        "n": 575,
        "number_of_classes": 20,
        "original_feature_dimension": 112 * 92,
        "processed_feature_dimension": 112 * 92,
        "original_spatial_size": [112, 92],
        "pixel_range_native_uint8": [0, 238],
        "unique_pixel_arrays": 565,
        "duplicate_filenames": 0,
        "pixel_duplicate_pairs": [
            ["1b/face/1b014.pgm", "1b/face/final00.pgm"],
            ["1b/face/1b016.pgm", "1b/face/final01.pgm"],
            ["1b/face/1b024.pgm", "1b/face/final02.pgm"],
            ["1b/face/1b032.pgm", "1b/face/final03.pgm"],
            ["1b/face/1b038.pgm", "1b/face/final04.pgm"],
            ["1b/face/1b040.pgm", "1b/face/final05.pgm"],
            ["1b/face/1b048.pgm", "1b/face/final06.pgm"],
            ["1b/face/1b056.pgm", "1b/face/final07.pgm"],
            ["1b/face/1b064.pgm", "1b/face/final08.pgm"],
            ["1b/face/1b072.pgm", "1b/face/final09.pgm"],
        ],
        "preprocessing_operations": [
            "read every PGM in the pre-cropped tar",
            "sort by archive member name",
            "divide by 255",
            "vectorize in C order",
            "no resize",
        ],
        "sample_selection_method": (
            "all 575 cropped PGM files; this is not the 564-image count "
            "stated by Chang et al. and by the 2001 UMIST web page. "
            "Dropping the 10 pixel-identical final*.pgm copies yields 565, "
            "not 564. Eleven images were not dropped to force the paper count."
        ),
        "random_seed": "unknown",
        "not_exact_564": True,
    }
    return x, y, metadata


def _load_figshare(root: Path | None):
    path = data_dir(root) / "figshare_umist_cropped" / "umist_cropped.mat"
    if not path.is_file():
        raise FileNotFoundError(path)
    mat = loadmat(path)
    facedat = mat["facedat"]
    images = []
    labels = []
    for person in range(facedat.shape[1]):
        cell = np.asarray(facedat[0, person])
        if cell.ndim != 3 or cell.shape[0] != 112 or cell.shape[1] != 92:
            raise ValueError(f"unexpected figshare cell {cell.shape}")
        for index in range(cell.shape[2]):
            images.append(cell[:, :, index])
            labels.append(person)
    stack = np.stack(images, axis=0)
    if stack.shape != (575, 112, 92) or stack.dtype != np.uint8:
        raise ValueError(f"unexpected figshare stack {stack.shape} {stack.dtype}")
    x = as_float_matrix(stack.astype(np.float64).reshape(575, -1) / 255.0)
    y = as_int_labels(np.asarray(labels), x.shape[0])
    metadata = {
        "dataset_name": "UMIST",
        "version": "figshare575",
        "verification_status": "approximate",
        "source_url": "https://ndownloader.figshare.com/files/67153214",
        "archive_path": str(path),
        "SHA256_checksum": "ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361",
        "n": 575,
        "number_of_classes": 20,
        "original_feature_dimension": 112 * 92,
        "processed_feature_dimension": 112 * 92,
        "original_spatial_size": [112, 92],
        "pixel_range_native_uint8": [int(stack.min()), int(stack.max())],
        "unique_pixel_arrays": int(np.unique(stack.reshape(575, -1), axis=0).shape[0]),
        "preprocessing_operations": [
            "read facedat cell array, each cell (112, 92, n_i)",
            "walk persons 0..19 and the last axis in stored order",
            "divide by 255",
            "vectorize in C order",
            "no resize",
        ],
        "sample_selection_method": (
            "all 575 slices in the Figshare mat. Pixel hashes do not "
            "intersect the 575-image cropped.tar.gz, with or without a transpose. "
            "This is not the 564-image set."
        ),
        "random_seed": "unknown",
        "not_exact_564": True,
        "figshare_article": "https://api.figshare.com/v2/articles/33130868",
    }
    return x, y, metadata
