"""UMIST is unavailable; the loader must not return arrays."""

import pytest

from benchmarks.exceptions import DatasetUnavailable
from benchmarks.umist import load_dataset


def test_umist_raises_unavailable() -> None:
    with pytest.raises(DatasetUnavailable, match="UMIST is unavailable"):
        load_dataset()


def test_precropped_is_not_564() -> None:
    from pathlib import Path

    archive = (
        Path(__file__).resolve().parent
        / "data"
        / "wayback_sheffield"
        / "processed"
        / "umist_precropped575_uint8.npy"
    )
    if not archive.is_file():
        pytest.skip("precropped UMIST array stays in the read-only data root, not this checkout")
    x, y, meta = load_dataset(version="precropped575")
    assert x.shape == (575, 112 * 92)
    assert len(set(y.tolist())) == 20
    assert meta["n"] == 575
    assert meta["not_exact_564"] is True


def test_round2_umist_candidates_keep_their_counts() -> None:
    from pathlib import Path

    private = Path(__file__).resolve().parent / "resources" / "private"
    if (private / "lzuf_umist.mat").is_file():
        features, labels, metadata = load_dataset(version="lzuf574")
        assert features.shape == (574, 10304)
        assert len(set(labels.tolist())) == 20
        assert metadata["not_exact_564"] is True
    if (private / "zenodo3634017_umist.mat").is_file():
        features, labels, metadata = load_dataset(version="zenodo3634017")
        assert features.shape == (575, 644)
        assert metadata["im_height"] == 28
        assert metadata["im_width"] == 23
        assert metadata["not_exact_564"] is True
    if (private / "roweis_umist_cropped.mat").is_file():
        features, labels, metadata = load_dataset(version="roweis575")
        assert features.shape == (575, 112 * 92)
        assert len(set(labels.tolist())) == 20
        assert metadata["directory_names"][0] == "1a"
        assert metadata["not_exact_564"] is True
