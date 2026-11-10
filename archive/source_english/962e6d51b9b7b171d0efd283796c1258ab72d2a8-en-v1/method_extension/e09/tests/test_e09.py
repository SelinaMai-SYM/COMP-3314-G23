import numpy as np

from method_extension.e09.method import RecurrenceLocalScaleSSC


def test_e09_starts_from_the_control_embedding():
    rng = np.random.default_rng(8)
    features = rng.normal(size=(16, 3))
    model = RecurrenceLocalScaleSSC(2, max_iter=6, solver="original").fit(features)
    assert model.state_.f_source == "control_eq4"
    assert model.state_.info["ablation"] == ["SSC_E8", "E01", "E03-W"]
    assert np.isfinite(model.shrunk_).all()
