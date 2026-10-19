"""Shared checks for baseline ``fit_predict`` functions."""

from __future__ import annotations

from typing import Any

import numpy as np


def as_feature_matrix(X: np.ndarray) -> np.ndarray:
    """Return a finite ``(n_samples, n_features)`` array of dtype float64.

    The caller array is not modified.
    """
    features = np.asarray(X, dtype=np.float64)
    if features.ndim != 2:
        raise ValueError("X must have shape (n_samples, n_features)")
    n_samples, n_features = features.shape
    if n_samples < 2 or n_features < 1:
        raise ValueError("X must contain at least 2 samples and 1 feature")
    if not np.isfinite(features).all():
        raise ValueError("X contains non-finite values")
    return features


def as_positive_int(name: str, value: object) -> int:
    """Cast a Boolean-rejected positive integer parameter."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be a positive int")
    number = int(value)
    if number < 1:
        raise ValueError(f"{name} must be a positive int")
    return number


def as_random_state(random_state: object) -> int:
    """Require an integer seed so a call is deterministic."""
    if isinstance(random_state, bool) or not isinstance(random_state, (int, np.integer)):
        raise TypeError("random_state must be an int")
    return int(random_state)


def check_problem(
    X: np.ndarray, n_clusters: object, random_state: object
) -> tuple[np.ndarray, int, int]:
    """Validate the three positional arguments shared by every baseline."""
    features = as_feature_matrix(X)
    clusters = as_positive_int("n_clusters", n_clusters)
    if clusters > features.shape[0]:
        raise ValueError("n_clusters cannot exceed n_samples")
    return features, clusters, as_random_state(random_state)


def resolve_params(params: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    """Override ``defaults`` and reject names that are not in that map."""
    unknown = sorted(set(params) - set(defaults))
    if unknown:
        raise TypeError(f"unexpected parameters: {unknown}")
    resolved = dict(defaults)
    resolved.update(params)
    return resolved
