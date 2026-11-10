"""Cache keys include the source commit and the matrix fingerprint."""

from __future__ import annotations

import numpy as np

from experiments.v3_reproduction.provenance import cache_key, fingerprint_matrix


def test_commit_and_row_order_change_the_key() -> None:
    features = np.arange(12, dtype=np.float64).reshape(4, 3)
    labels = np.array([0, 0, 1, 1])
    fingerprint = fingerprint_matrix(features, labels)
    config = {"ssc_gamma": 1.0}
    first = cache_key(fingerprint=fingerprint, config=config, code_commit="aaa")
    second = cache_key(fingerprint=fingerprint, config=config, code_commit="bbb")
    swapped = fingerprint_matrix(features[::-1], labels[::-1])
    third = cache_key(fingerprint=swapped, config=config, code_commit="aaa")
    assert len({first, second, third}) == 3
