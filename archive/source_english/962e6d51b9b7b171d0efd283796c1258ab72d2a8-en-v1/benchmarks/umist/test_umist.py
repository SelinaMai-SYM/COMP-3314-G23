"""UMIST is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.exceptions import DatasetUnavailable
from benchmarks.umist import load_dataset


def test_umist_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="UMIST is unavailable"):
        load_dataset()


def test_precropped_is_not_564() -> None:
    x, y, meta = load_dataset(version="precropped575")
    assert x.shape == (575, 112 * 92)
    assert len(set(y.tolist())) == 20
    assert meta["n"] == 575
    assert meta["not_exact_564"] is True
