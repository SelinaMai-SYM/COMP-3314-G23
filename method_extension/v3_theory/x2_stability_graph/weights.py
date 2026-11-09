"""Image and feature perturbations used only to build a stability graph."""

from __future__ import annotations

import numpy as np


# Brightness is a fraction of the full scale when the matrix looks like [0, 1],
# and the same numeric fraction of 255 when the matrix looks like 8-bit pixels.
# Contrast multiplies the deviation from each row mean. The list is fixed.
IMAGE_PERTURBATIONS: tuple[tuple[str, float, float], ...] = (
    ("brightness", 6.0, 1.0),
    ("brightness", -6.0, 1.0),
    ("contrast", 0.0, 0.92),
    ("contrast", 0.0, 1.08),
    ("both", 3.0, 0.96),
    ("both", -3.0, 1.04),
    ("brightness", 10.0, 1.0),
    ("brightness", -10.0, 1.0),
    ("contrast", 0.0, 0.85),
    ("contrast", 0.0, 1.15),
)

HELD_OUT_PERTURBATIONS: tuple[tuple[str, float, float], ...] = (
    ("brightness", 2.0, 1.0),
    ("contrast", 0.0, 1.05),
    ("both", -2.0, 0.98),
    ("both", 5.0, 1.02),
)


def _full_scale(features: np.ndarray) -> float:
    peak = float(np.nanmax(features))
    return 1.0 if peak <= 1.5 else 255.0


def perturb_images(features: np.ndarray, brightness_steps: float, contrast: float, *, domain: tuple[float,float] | None = None) -> np.ndarray:
    """Domain-aware perturbation. Historical pre-fix tables are not rerun in place.

    brightness_steps is in 1/255 units of the full declared dynamic range.
    Current runners pass domain explicitly; inference preserves older callers.
    """
    matrix = np.asarray(features, dtype=np.float64)
    if brightness_steps == 0 and contrast == 1:
        return matrix.copy()
    if domain is None:
        domain = (-1.,1.) if matrix.min() < 0 and matrix.max() <= 1.5 else (0.,_full_scale(matrix))
    lo,hi = map(float,domain)
    if hi <= lo or not np.isfinite([lo,hi]).all():
        raise ValueError("invalid pixel domain")
    updated = matrix + float(brightness_steps)/255*(hi-lo)
    if contrast != 1.:
        center=updated.mean(axis=1,keepdims=True)
        updated=center+float(contrast)*(updated-center)
    return np.clip(updated,lo,hi)


def perturb_features(features: np.ndarray, seed: int, relative: float = 0.05) -> np.ndarray:
    matrix = np.asarray(features, dtype=np.float64)
    center = np.median(matrix, axis=0)
    deviation = np.median(np.abs(matrix - center), axis=0)
    scale = np.maximum(deviation, 1e-8)
    noise = np.random.default_rng(seed).normal(0.0, relative, size=matrix.shape)
    return matrix + noise * scale


def perturbation_list(which: str) -> tuple[tuple[str, float, float], ...]:
    if which == "fit":
        return IMAGE_PERTURBATIONS
    if which == "heldout":
        return HELD_OUT_PERTURBATIONS
    raise ValueError("which must be 'fit' or 'heldout'")
