"""AR is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.ar import load_dataset
from benchmarks.exceptions import DatasetUnavailable


def test_ar_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="AR is unavailable"):
        load_dataset()


def test_lzuf_superset_is_not_the_840_subset() -> None:
    from pathlib import Path

    private = Path(__file__).resolve().parent / "resources" / "private" / "lzuf_candidate_AR.mat"
    if not private.is_file():
        pytest.skip("private LZUFE AR.mat is not in this checkout")
    features, labels, metadata = load_dataset(version="lzuf_superset1680")
    assert features.shape == (1680, 1024)
    assert len(set(labels.tolist())) == 120
    assert metadata["counts_as_historical"] is False
    assert metadata["n"] == 1680
