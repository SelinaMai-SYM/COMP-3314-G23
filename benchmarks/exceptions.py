"""Errors and array checks shared by per-dataset loaders."""

from __future__ import annotations

import numpy as np


class DatasetUnavailable(RuntimeError):
    """Raised when a paper dataset was not legally or actually obtained."""

    def __init__(self, dataset_name: str, reason: str):
        self.dataset_name = dataset_name
        self.reason = reason
        super().__init__(f"{dataset_name} is unavailable: {reason}")


def as_float_matrix(x: np.ndarray) -> np.ndarray:
    matrix = np.asarray(x, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError(f"X must have shape (n, d), got {matrix.shape}")
    if not np.isfinite(matrix).all():
        raise ValueError("X contains non-finite values")
    return matrix


def as_int_labels(y: np.ndarray, n_rows: int) -> np.ndarray:
    labels = np.asarray(y).reshape(-1)
    if labels.shape != (n_rows,):
        raise ValueError(f"y length {labels.shape[0]} does not match X rows {n_rows}")
    if not np.issubdtype(labels.dtype, np.integer):
        if not np.all(labels == np.floor(labels)):
            raise ValueError("labels are not integers")
    return labels.astype(np.int64, copy=False)
