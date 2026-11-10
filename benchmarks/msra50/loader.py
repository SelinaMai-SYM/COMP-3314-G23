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
    if version in ("ebsa16", "MSRA25_EBSA_16x16"):
        return _load_ebsa16(root)
    raise DatasetUnavailable(
        "MSRA50",
        "MSRA50 is BLOCKED_NO_VERIFIED_DATA_URL. Chang et al. state 1799 "
        "images and 12 classes resized to 32x32, with no URL. Round 2 "
        "was given a null direct download URL. The page "
        "https://arxiv.org/html/2311.15214v1 is reference material only "
        "and was not saved as data. No MSRA-B, MSRA10K, TD500, or MSRC "
        "file was substituted. See benchmarks/msra50/README.md.",
    )


EBSA_SHA256 = "3c8681c40ebbed2f6dc2d2f30e7c5195e947467e8cf6797faa44753a190cd659"
EBSA_URL = "https://raw.githubusercontent.com/LZUFE-Machine-Learning/EBSA/c72bfbf13ac0e67db1a756eb26d56b7b996b64cb/dataset/MSRA25.mat"


def _load_ebsa16(root=None):
    """Native EBSA 16x16 source, without deduplication or resizing.

    The explicit version does not change the unavailable original MSRA50
    endpoint. MATLAB's declared double dtype is read with mat_dtype=True.
    """
    import hashlib
    import numpy as np
    from scipy.io import loadmat
    from benchmarks.exceptions import as_float_matrix, as_int_labels
    path = data_dir(root) / "EBSA_c72bfbf_MSRA25.mat"
    if not path.is_file():
        raise FileNotFoundError(f"missing {path}; retrieve the pinned EBSA source")
    if hashlib.file_digest(path.open("rb"), "sha256").hexdigest() != EBSA_SHA256:
        raise ValueError("EBSA MSRA25 source hash mismatch")
    mat = loadmat(path, mat_dtype=True)
    x = np.asarray(mat["X"], dtype=np.float64)
    raw_y = np.asarray(mat["Y"]).reshape(-1)
    shape = [int(np.asarray(mat[k]).item()) for k in ["im_height", "im_width"]]
    if x.shape != (1799, 256) or shape != [16, 16]:
        raise ValueError("EBSA MSRA25 shape/resolution mismatch")
    if not np.isfinite(x).all() or np.any(x != np.floor(x)) or (x.min(), x.max()) != (0, 255):
        raise ValueError("EBSA MSRA25 unexpected pixel scale")
    y = as_int_labels(raw_y.astype(np.int64)-1, len(x))
    counts = np.bincount(y)
    if counts.tolist() != [175,154,113,178,186,159,179,128,133,131,128,135]:
        raise ValueError("EBSA MSRA25 labels changed")
    _, inv, multiplicities = np.unique(x, axis=0, return_inverse=True, return_counts=True)
    for group in np.flatnonzero(multiplicities > 1):
        if len(np.unique(y[inv == group])) != 1:
            raise ValueError("EBSA MSRA25 duplicate label conflict")
    if int(np.sum(multiplicities-1)) != 13:
        raise ValueError("EBSA MSRA25 duplicate count changed")
    return as_float_matrix(x/255.), y, {
        "dataset_name": "MSRA25_EBSA_16x16", "version": "ebsa16",
        "verification_status": "ADAPTED_RESOLUTION_HISTORICAL_IDENTITY_UNVERIFIED",
        "counts_as_historical": False, "source_url": EBSA_URL,
        "archive_path": str(path), "SHA256_checksum": EBSA_SHA256,
        "n": 1799, "number_of_classes": 12, "processed_feature_dimension": 256,
        "original_spatial_size": [16,16], "processed_spatial_size": [16,16],
        "declared_matlab_dtype": "double", "reader": "scipy.io.loadmat(mat_dtype=True)",
        "pixel_range_native": [0,255], "duplicate_extra_rows": 13,
        "preprocessing_operations": ["divide native integer pixels by 255", "preserve all source rows and source order", "no resize; no deduplication"],
        "sample_selection_method": "all 1799 rows in pinned MSRA25.mat",
        "historical_identity": "unverified; native 16x16 differs from the paper's stated 32x32"}
