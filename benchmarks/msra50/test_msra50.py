"""MSRA50 is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.exceptions import DatasetUnavailable
from benchmarks.msra50 import load_dataset


def test_msra50_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="MSRA50 is unavailable"):
        load_dataset()
