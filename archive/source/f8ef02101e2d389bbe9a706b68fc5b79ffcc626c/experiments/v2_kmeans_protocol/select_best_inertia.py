"""Select the minimum-inertia trial inside one saved batch.

Selection reads inertia and seed only. ACC and NMI are attributes of
the already chosen trial; they are not inputs to the choice.
"""

from __future__ import annotations

from typing import Mapping, Sequence


def select_min_inertia(trials: Sequence[Mapping]) -> Mapping:
    """Return the trial with smallest inertia.

    Ties break toward the smaller seed. That rule is predetermined and
    does not look at labels or ACC.
    """
    if not trials:
        raise ValueError("cannot select from an empty trial batch")
    for trial in trials:
        if "inertia" not in trial or "seed" not in trial:
            raise ValueError("each trial needs inertia and seed")
        inertia = float(trial["inertia"])
        if inertia != inertia:  # NaN
            raise ValueError("inertia must be finite")
    return min(trials, key=lambda trial: (float(trial["inertia"]), int(trial["seed"])))


def acc_rank_of_selected(trials: Sequence[Mapping], selected: Mapping) -> int:
    """1-based rank of the selected trial's ACC. Rank 1 is the highest ACC.

    Ties keep the best rank: a trial tied with two better scores is rank 3
    only when those two are strictly larger. Equal ACC values share a rank.
    """
    selected_acc = float(selected["acc"])
    better = sum(1 for trial in trials if float(trial["acc"]) > selected_acc)
    return int(better + 1)


__all__ = ["acc_rank_of_selected", "select_min_inertia"]
