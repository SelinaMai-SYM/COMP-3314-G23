"""BinAlpha loaders.

The default name is still the paper set, which was not identified.
``version="binaryalphadigs36"`` is the 36-class Binary Alphadigits parent.
``version="letters26x30_seed0"`` is a documented reconstruction. Neither
version is the Chang et al. BinAlpha sample set.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from benchmarks.exceptions import DatasetUnavailable, as_float_matrix, as_int_labels

from .preprocessing import stack_binary_images

_ARCHIVE = "binaryalphadigs.mat"
_SHA256 = "3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7"
_SOURCE_URL = (
    "https://web.archive.org/web/20240616024002id_/"
    "https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat"
)
_EXPECTED_LABELS = tuple("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_RECONSTRUCTION = Path(__file__).resolve().parent / "reconstructions" / "letters26x30_seed0.json"

_UNAVAILABLE = (
    "Chang et al. name BinAlpha as 26 binary handwritten alphabets with "
    "30 randomly selected images per alphabet, without a URL, image size, "
    "or seed. Binary Alphadigits (36 classes x 39 images, 20x16) was "
    "downloaded on 2026-10-21 from a Wayback capture of the Roweis page. "
    "No evidence was found that Chang et al. used that file. "
    "The 36-class archive is therefore not called the paper BinAlpha. "
    "Use version='binaryalphadigs36' or version='letters26x30_seed0' for "
    "the parent and the UNVERIFIED reconstruction. "
    "See benchmarks/binalpha/README.md."
)


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None):
    if version in (None, "paper", "chang"):
        raise DatasetUnavailable("BinAlpha", _UNAVAILABLE)
    if version == "binaryalphadigs36":
        return _load_parent(root)
    if version in ("letters26x30_seed0", "letters26x30"):
        return _load_reconstruction(root)
    raise ValueError(
        f"unknown BinAlpha version {version!r}; known versions: "
        "paper, binaryalphadigs36, letters26x30_seed0"
    )


def _read_parent(root: Path | None):
    path = data_dir(root) / _ARCHIVE
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}. See benchmarks/binalpha/README.md."
        )
    mat = loadmat(path)
    dat = mat["dat"]
    if dat.shape != (36, 39):
        raise ValueError(f"unexpected Binary Alphadigits dat {dat.shape}")
    labels = []
    for item in np.asarray(mat["classlabels"]).reshape(-1):
        text = item.item() if hasattr(item, "item") else item
        labels.append(str(text))
    if tuple(labels) != _EXPECTED_LABELS:
        raise ValueError(f"unexpected classlabels {labels}")
    images = []
    for class_index in range(36):
        for example in range(39):
            cell = np.asarray(dat[class_index, example])
            if cell.shape != (20, 16) or cell.dtype != np.uint8:
                raise ValueError(f"unexpected cell {cell.shape} {cell.dtype}")
            images.append(cell)
    stack = np.stack(images, axis=0)
    if stack.min() != 0 or stack.max() != 1:
        raise ValueError(f"Binary Alphadigits pixels are not 0/1: {stack.min()}..{stack.max()}")
    return path, stack, labels


def _load_parent(root: Path | None):
    path, stack, labels = _read_parent(root)
    x = as_float_matrix(stack_binary_images(stack))
    y = as_int_labels(np.repeat(np.arange(36), 39), x.shape[0])
    if x.shape != (1404, 320):
        raise ValueError(f"processed Binary Alphadigits shape {x.shape}")
    metadata = {
        "dataset_name": "BinaryAlphadigits",
        "version": "binaryalphadigs36",
        "verification_status": "obtained_parent_not_paper_binalpha",
        "identity": "UNVERIFIED as Chang et al. BinAlpha",
        "not_paper_binalpha": True,
        "source_url": _SOURCE_URL,
        "archive_path": str(path),
        "SHA256_checksum": _SHA256,
        "n": 1404,
        "number_of_classes": 36,
        "original_feature_dimension": 320,
        "processed_feature_dimension": 320,
        "original_spatial_size": [20, 16],
        "class_labels": labels,
        "preprocessing_operations": [
            "read every 20x16 uint8 cell in dat (36 classes x 39 examples)",
            "keep stored 0/1 values; no divide-by-255",
            "vectorize in C order",
            "no resize",
        ],
        "sample_selection_method": "all 1404 images; this is the 36-class parent, not 26x30",
        "random_seed": "none; the full parent is loaded",
    }
    return x, y, metadata


def _load_reconstruction(root: Path | None):
    path, stack, labels = _read_parent(root)
    spec = json.loads(_RECONSTRUCTION.read_text())
    if spec["n_total"] != 780 or spec["random_seed"] != 0:
        raise ValueError("reconstruction spec is not letters26x30_seed0")
    rows = []
    class_ids = []
    for class_id, item in enumerate(spec["selection"]):
        parent_index = item["class_index_in_parent"]
        if labels[parent_index] != item["letter"]:
            raise ValueError(f"label mismatch at {parent_index}")
        if len(item["example_indices_0based"]) != 30:
            raise ValueError(f"{item['letter']} does not have 30 indices")
        for example in item["example_indices_0based"]:
            rows.append(stack[parent_index * 39 + example])
            class_ids.append(class_id)
    images = np.stack(rows, axis=0)
    x = as_float_matrix(stack_binary_images(images))
    y = as_int_labels(np.asarray(class_ids), x.shape[0])
    if x.shape != (780, 320):
        raise ValueError(f"reconstructed subset shape {x.shape}")
    if not np.all(np.bincount(y) == 30):
        raise ValueError("reconstruction is not 30 images per letter")
    metadata = {
        "dataset_name": "BinaryAlphadigits_letters26x30_seed0",
        "version": "letters26x30_seed0",
        "verification_status": "reconstruction_unverified_identity",
        "identity": "UNVERIFIED",
        "not_paper_binalpha": True,
        "source_url": _SOURCE_URL,
        "archive_path": str(path),
        "index_path": str(_RECONSTRUCTION),
        "SHA256_checksum": _SHA256,
        "n": 780,
        "number_of_classes": 26,
        "original_feature_dimension": 320,
        "processed_feature_dimension": 320,
        "original_spatial_size": [20, 16],
        "preprocessing_operations": [
            "drop digit classes 0-9",
            "for each letter A-Z, take the 30 example indices stored in letters26x30_seed0.json",
            "keep stored 0/1 values; no divide-by-255",
            "vectorize in C order",
            "no resize",
        ],
        "sample_selection_method": spec["rng"],
        "random_seed": 0,
        "reconstruction_note": spec["note"],
    }
    return x, y, metadata
