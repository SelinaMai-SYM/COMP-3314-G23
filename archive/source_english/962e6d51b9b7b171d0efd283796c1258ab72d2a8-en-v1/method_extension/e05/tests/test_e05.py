import numpy as np

from method_extension.e05.method import CrossSpaceSSC


def test_e05_does_not_treat_the_pixel_graph_as_reliable():
    rng = np.random.default_rng(4)
    features = rng.normal(size=(16, 3))
    for mode in ("fuse", "bilateral"):
        model = CrossSpaceSSC(2, mode=mode, max_iter=6, solver="original").fit(features)
        assert model.state_.info["pixel_graph_assumed_reliable"] is False
        assert np.isfinite(model.shrunk_).all()
