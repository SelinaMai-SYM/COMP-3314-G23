import numpy as np

from method_extension.common.fitting import ExtensionConfig
from method_extension.e01.method import EdgeRecurrenceSSC


def test_e01_class_runs_and_is_deterministic():
    rng = np.random.default_rng(0)
    features = rng.normal(size=(16, 3))
    model = EdgeRecurrenceSSC(2, gamma=1.0, max_iter=8, solver="original")
    model.fit(features, y=np.zeros(16, dtype=int))
    again = EdgeRecurrenceSSC(2, gamma=1.0, max_iter=8, solver="original").fit(features, y=np.ones(16, dtype=int))
    assert model.shrunk_.shape == (16, 2)
    assert np.allclose(model.shrunk_, again.shrunk_)
    assert model.config == ExtensionConfig(max_iter=8, solver="original") or model.config.max_iter == 8
