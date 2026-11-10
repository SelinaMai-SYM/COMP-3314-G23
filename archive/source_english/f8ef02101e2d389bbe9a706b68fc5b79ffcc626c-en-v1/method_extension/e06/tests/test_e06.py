import numpy as np

from method_extension.e06.method import AlternatingGraphSSC


def test_e06_records_outer_steps_without_a_global_claim():
    rng = np.random.default_rng(5)
    features = rng.normal(size=(16, 3))
    model = AlternatingGraphSSC(2, max_iter=5, n_outer=2, solver="original").fit(features)
    assert model.state_.info["global_convergence_claimed"] is False
    assert model.state_.info["each_frozen_W_subproblem_convex"] is True
    assert len(model.state_.info["outers"]) == 2
