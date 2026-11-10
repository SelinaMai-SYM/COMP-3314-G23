"""ORL version selection. The default name stays on the Olivetti pipeline."""

from benchmarks import load_dataset


def test_default_orl_is_olivetti() -> None:
    x, y, meta = load_dataset("ORL")
    assert x.shape == (400, 1024)
    assert y.shape == (400,)
    assert meta["version"] == "olivetti64"
    assert meta["original_spatial_size"] == [64, 64]
    assert "olivettifaces.mat" in meta["archive_path"]


def test_att92_is_separate_from_olivetti() -> None:
    x, y, meta = load_dataset("ORL", version="att92")
    assert x.shape == (400, 1024)
    assert int(y.max()) == 39
    assert meta["version"] == "att92"
    assert meta["original_spatial_size"] == [112, 92]
    assert meta["interpolation"] == "bilinear"
    assert meta["n"] == 400
    assert meta["number_of_classes"] == 40
    nearest, _, nearest_meta = load_dataset("ORL", version="att92_nearest")
    bicubic, _, _ = load_dataset("ORL", version="att92_bicubic")
    assert nearest_meta["interpolation"] == "nearest"
    assert nearest.shape == x.shape == bicubic.shape
    assert not (nearest == x).all()
    assert not (bicubic == x).all()
