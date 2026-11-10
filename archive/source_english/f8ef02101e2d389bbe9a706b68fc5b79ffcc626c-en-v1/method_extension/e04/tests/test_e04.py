import numpy as np

from method_extension.e04.method import DegreeNormalizedSSC


def test_e04_total_is_labeled_a_gamma_scale_control():
    rng = np.random.default_rng(3)
    features = rng.normal(size=(16, 3))
    model = DegreeNormalizedSSC(2, mode="total", max_iter=6, solver="original").fit(features)
    assert model.state_.info["equivalent_to_global_gamma_scale"] is True
    assert model.state_.info["mechanism"] == "control_not_a_new_mechanism"
