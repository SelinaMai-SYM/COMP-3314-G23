import numpy as np

from method_extension.e07.method import cluster_fixed_representation


def test_e07_protocols_do_not_read_accuracy():
    rng = np.random.default_rng(6)
    features = rng.normal(size=(24, 2))
    result = cluster_fixed_representation(features, 3, [0, 1, 2])
    assert result["uses_accuracy"] is False
    assert result["inertia_best_labels"].shape == (24,)
    assert result["consensus_labels"].shape == (24,)
    assert len(result["random"]) == 3
    assert len(result["kmeanspp"]) == 3
