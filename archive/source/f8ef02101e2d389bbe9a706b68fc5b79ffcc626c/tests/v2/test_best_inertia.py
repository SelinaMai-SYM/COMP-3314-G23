"""Minimum inertia is the only selection rule."""

from experiments.v2_kmeans_protocol.select_best_inertia import (
    acc_rank_of_selected,
    select_min_inertia,
)


def test_selects_minimum_inertia_not_maximum_acc() -> None:
    trials = [
        {"seed": 0, "inertia": 3.0, "acc": 0.9},
        {"seed": 1, "inertia": 1.0, "acc": 0.2},
        {"seed": 2, "inertia": 2.0, "acc": 0.95},
    ]
    selected = select_min_inertia(trials)
    assert selected["seed"] == 1
    assert acc_rank_of_selected(trials, selected) == 3


def test_inertia_tie_uses_smaller_seed() -> None:
    trials = [
        {"seed": 4, "inertia": 1.0, "acc": 0.1},
        {"seed": 2, "inertia": 1.0, "acc": 0.9},
    ]
    assert select_min_inertia(trials)["seed"] == 2


def test_changing_acc_does_not_change_the_seed() -> None:
    base = [
        {"seed": 0, "inertia": 5.0, "acc": 0.1},
        {"seed": 1, "inertia": 4.0, "acc": 0.2},
    ]
    flipped = [
        {"seed": 0, "inertia": 5.0, "acc": 0.99},
        {"seed": 1, "inertia": 4.0, "acc": 0.01},
    ]
    assert select_min_inertia(base)["seed"] == select_min_inertia(flipped)["seed"] == 1
