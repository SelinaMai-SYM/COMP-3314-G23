"""Deterministic YaleB scaling. The obtained matrix is already 32x32."""

from __future__ import annotations

import numpy as np


def scale_uint8_to_unit(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if array.dtype != np.uint8:
        raise ValueError(f"scale_uint8_to_unit expects uint8, got {array.dtype}")
    return array.astype(np.float64) / 255.0


def preprocess(features: np.ndarray) -> np.ndarray:
    """No resize; divide uint8 values by 255."""
    return scale_uint8_to_unit(features)
