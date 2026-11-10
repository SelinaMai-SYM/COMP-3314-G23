import numpy as np

from method_extension.e08.method import CombinedRecurrenceReliabilitySSC


def test_e08_freezes_both_weights_and_names_the_ablation():
    rng = np.random.default_rng(7)
    features = rng.normal(size=(16, 3))
    model = CombinedRecurrenceReliabilitySSC(2, max_iter=6, solver="original").fit(features)
    assert model.state_.info["weights_fixed_during_optimization"] is True
    assert model.state_.info["ablation"] == ["SSC_E8", "E01", "E02"]
    assert np.isfinite(model.shrunk_).all()
