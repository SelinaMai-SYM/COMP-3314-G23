"""Default BinAlpha stays unavailable. Explicit versions are not the paper set."""

import pytest

from benchmarks.binalpha import load_dataset
from benchmarks.exceptions import DatasetUnavailable


def test_binalpha_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="BinAlpha is unavailable"):
        load_dataset()


def test_binaryalphadigs36_is_not_paper_binalpha() -> None:
    x, y, meta = load_dataset(version="binaryalphadigs36")
    assert x.shape == (1404, 320)
    assert sorted(set(y.tolist())) == list(range(36))
    assert meta["not_paper_binalpha"] is True
    assert meta["n"] == 1404
    assert meta["number_of_classes"] == 36
    assert x.min() == 0.0 and x.max() == 1.0


def test_letters26x30_seed0_is_reconstruction() -> None:
    x, y, meta = load_dataset(version="letters26x30_seed0")
    assert x.shape == (780, 320)
    assert list(y[:30]) == [0] * 30
    assert int(y.max()) == 25
    assert meta["identity"] == "CANDIDATE_BIN_ALPHA"
    assert meta["not_paper_binalpha"] is True
    assert meta["not_exact"] is True
    assert meta["random_seed"] == 0
    assert meta["n"] == 780


def test_candidate_bin_alpha_is_not_exact() -> None:
    x, y, meta = load_dataset(version="CANDIDATE_BIN_ALPHA")
    assert x.shape == (780, 320)
    assert meta["identity"] == "CANDIDATE_BIN_ALPHA"
    assert meta["version"] == "CANDIDATE_BIN_ALPHA"
    assert meta["not_paper_binalpha"] is True
    assert meta["not_historical_identity"] is True
    assert meta["random_seed"] == 0
