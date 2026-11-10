"""Ground-truth labels are not an input to the fits."""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from baselines.kmeans import fit_predict as kmeans_fit
from baselines.lda_kmeans import fit_predict as lda_fit
from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd


def test_lloyd_signature_has_no_labels() -> None:
    assert "y" not in inspect.signature(fit_lloyd).parameters
    assert "y_true" not in inspect.signature(fit_lloyd).parameters


def test_lda_and_kmeans_reject_a_label_argument() -> None:
    features = np.array([[0.0, 0.0], [0.1, 0.0], [4.0, 0.0], [4.1, 0.2]], dtype=np.float64)
    with pytest.raises(TypeError):
        kmeans_fit(features, 2, 0, y=np.array([0, 0, 1, 1]))
    with pytest.raises(TypeError):
        lda_fit(features, 2, 0, n_components=1, y=np.array([0, 0, 1, 1]))
