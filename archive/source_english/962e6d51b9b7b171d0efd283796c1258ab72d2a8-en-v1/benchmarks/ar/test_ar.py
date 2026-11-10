"""AR is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.ar import load_dataset
from benchmarks.exceptions import DatasetUnavailable


def test_ar_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="AR is unavailable"):
        load_dataset()
