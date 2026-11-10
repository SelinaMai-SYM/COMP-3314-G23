"""Parse LIBSVM USPS files. The release is already 16x16 in [-1, 1]."""

from __future__ import annotations

import bz2
from pathlib import Path

import numpy as np

# Published by Hastie, zip.info: digit counts for the 7291/2007 USPS split.
TRAIN_COUNTS = (1194, 1005, 731, 658, 652, 556, 664, 645, 542, 644)
TEST_COUNTS = (359, 264, 198, 166, 200, 160, 170, 147, 166, 177)


def parse_libsvm(
    path: Path, expected_n: int, expected_counts: tuple[int, ...]
) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    labels = []
    with bz2.open(path, "rt") as handle:
        for line in handle:
            parts = line.split()
            file_label = int(float(parts[0]))
            if file_label < 1 or file_label > 10:
                raise ValueError(f"unexpected USPS file label {file_label} in {path}")
            vector = np.zeros(256, dtype=np.float64)
            for item in parts[1:]:
                index, value = item.split(":")
                index = int(index)
                if index < 1 or index > 256:
                    raise ValueError(f"feature index {index} outside 1..256")
                vector[index - 1] = float(value)
            rows.append(vector)
            labels.append(file_label - 1)
    x = np.vstack(rows)
    y = np.asarray(labels, dtype=np.int64)
    if x.shape != (expected_n, 256):
        raise ValueError(f"{path.name} shape {x.shape}, expected {(expected_n, 256)}")
    counts = tuple(int(np.sum(y == digit)) for digit in range(10))
    if counts != expected_counts:
        raise ValueError(f"{path.name} class counts {counts} != {expected_counts}")
    return x, y


def preprocess(
    path: Path, expected_n: int, expected_counts: tuple[int, ...]
) -> tuple[np.ndarray, np.ndarray]:
    """No resize and no further scaling; stored values are already in [-1, 1]."""
    return parse_libsvm(path, expected_n, expected_counts)
