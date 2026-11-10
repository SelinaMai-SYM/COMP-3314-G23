import numpy as np

from method_extension.e03.method import LocalScaleSSC


def test_e03_three_placements_do_not_share_one_call():
    rng = np.random.default_rng(2)
    features = rng.normal(size=(16, 3))
    sources = {}
    for placement in ("A", "W", "AW"):
        model = LocalScaleSSC(2, placement=placement, max_iter=6, solver="original").fit(features)
        sources[placement] = model.state_.f_source
        assert model.state_.variant == placement
    assert sources["W"] == "control_eq4"
    assert sources["A"] == "local_scale_on_A"
    assert sources["AW"] == "local_scale_on_A"
