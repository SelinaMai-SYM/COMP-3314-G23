import numpy as np

from method_extension.e02.method import ReliabilityWeightedSSC


def test_e02_alpha_stays_inside_the_declared_interval():
    rng = np.random.default_rng(1)
    features = rng.normal(size=(18, 3))
    model = ReliabilityWeightedSSC(2, max_iter=8, solver="original").fit(features)
    assert 0.5 <= model.state_.info["alpha_min_value"] <= model.state_.info["alpha_max_value"] <= 2.0
