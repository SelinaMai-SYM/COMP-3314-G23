"""Dispatcher tests. Synthetic names are not stored as paper datasets."""

from __future__ import annotations

import pytest

from benchmarks import DatasetUnavailable, load_dataset


def test_unknown_name_is_rejected() -> None:
    with pytest.raises(KeyError, match="unknown dataset"):
        load_dataset("SYNTHETIC")


def test_unavailable_datasets_raise_through_dispatcher() -> None:
    for name in ("AR", "UMIST", "BinAlpha", "MSRA50"):
        with pytest.raises(DatasetUnavailable):
            load_dataset(name)
