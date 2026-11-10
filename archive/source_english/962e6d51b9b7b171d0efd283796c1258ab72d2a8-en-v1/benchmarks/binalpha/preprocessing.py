"""Binary Alphadigits cells are already 20x16 and valued in {0, 1}."""

from __future__ import annotations

import numpy as np


def stack_binary_images(images: np.ndarray) -> np.ndarray:
    """Vectorize a ``(n, 20, 16)`` uint8 stack of 0/1 pixels to float64."""
    array = np.asarray(images)
    if array.ndim != 3 or array.shape[1:] != (20, 16):
        raise ValueError(f"expected (n, 20, 16), got {array.shape}")
    if array.dtype != np.uint8:
        raise ValueError(f"expected uint8, got {array.dtype}")
    if array.min() < 0 or array.max() > 1:
        raise ValueError(f"pixels are not binary 0/1: {array.min()}..{array.max()}")
    return array.astype(np.float64).reshape(array.shape[0], -1)
