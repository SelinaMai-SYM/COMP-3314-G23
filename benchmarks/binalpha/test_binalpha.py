"""BinAlpha is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.binalpha import load_dataset
from benchmarks.exceptions import DatasetUnavailable


def test_binalpha_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="BinAlpha is unavailable"):
        load_dataset()
