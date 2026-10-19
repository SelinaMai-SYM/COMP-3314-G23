"""Deterministic JAFFE image preprocessing. No augmentation and no embeddings."""

from __future__ import annotations

import numpy as np
from PIL import Image


def to_grayscale_uint8(image: Image.Image) -> np.ndarray:
    if image.mode != "L":
        image = image.convert("L")
    array = np.asarray(image, dtype=np.uint8)
    if array.ndim != 2:
        raise ValueError(f"grayscale image must be 2-D, got shape {array.shape}")
    return array


def resize_bilinear(image: np.ndarray, height: int, width: int) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim != 2:
        raise ValueError(f"resize expects a 2-D image, got shape {array.shape}")
    if array.dtype != np.uint8:
        raise ValueError(f"resize expects uint8, got {array.dtype}")
    if height < 1 or width < 1:
        raise ValueError(f"invalid size {(height, width)}")
    pil = Image.fromarray(array, mode="L")
    resized = pil.resize((width, height), resample=Image.Resampling.BILINEAR)
    return np.asarray(resized, dtype=np.uint8)


def scale_uint8_to_unit(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if array.dtype != np.uint8:
        raise ValueError(f"scale_uint8_to_unit expects uint8, got {array.dtype}")
    return array.astype(np.float64) / 255.0


def vectorize(image: np.ndarray) -> np.ndarray:
    return np.asarray(image, dtype=np.float64).reshape(-1)


def preprocess(image: Image.Image, height: int = 26, width: int = 26) -> np.ndarray:
    """Convert one TIFF to a length-``height*width`` vector in ``[0, 1]``."""
    gray = to_grayscale_uint8(image)
    small = resize_bilinear(gray, height, width)
    return vectorize(scale_uint8_to_unit(small))
