"""Cropped Yale B is opt-in. The default loader stays on Deng Cai's mat."""

from benchmarks import load_dataset


def test_default_yaleb_is_dengcai() -> None:
    x, y, meta = load_dataset("YaleB")
    assert x.shape == (2414, 1024)
    assert len(set(y.tolist())) == 38
    assert meta["version"] == "dengcai32"
    assert meta["archive_path"].endswith("YaleB_32x32.mat")


def test_cropped2414_version() -> None:
    x, y, meta = load_dataset("YaleB", version="cropped2414")
    assert x.shape == (2414, 1024)
    assert len(set(y.tolist())) == 38
    assert meta["version"] == "cropped2414"
    assert meta["original_spatial_size"] == [192, 168]
    assert meta["n"] == 2414
    assert meta["number_of_classes"] == 38
