"""Deterministic ORL image preprocessing. No augmentation and no embeddings."""

from __future__ import annotations

import numpy as np
from PIL import Image


def resize_bilinear(image: np.ndarray, height: int, width: int) -> np.ndarray:
    """Resize a 2-D uint8 image to ``(height, width)`` with PIL bilinear."""
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


def preprocess(images: np.ndarray, height: int = 32, width: int = 32) -> np.ndarray:
    """Resize uint8 images to ``height x width``, scale to ``[0, 1]``, vectorize."""
    resized = np.stack([resize_bilinear(image, height, width) for image in images], axis=0)
    scaled = scale_uint8_to_unit(resized)
    return scaled.reshape(scaled.shape[0], -1)
