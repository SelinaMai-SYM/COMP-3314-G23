"""UMIST is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.exceptions import DatasetUnavailable
from benchmarks.umist import load_dataset


def test_umist_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="UMIST is unavailable"):
        load_dataset()
