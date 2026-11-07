"""K-means summaries. The selected min-inertia score has no SD attached."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import adjusted_rand_score

from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY, RANDOM, fit_lloyd
from experiments.v2_kmeans_protocol.metrics import evaluate_partition, mean_and_sample_sd


def run_family(
    features: np.ndarray,
    labels: np.ndarray,
    initialization: str,
    *,
    seeds: range | list[int] = range(50),
) -> list[dict[str, Any]]:
    n_clusters = int(np.unique(labels).size)
    rows = []
    for seed in seeds:
        fit = fit_lloyd(features, n_clusters, int(seed), initialization)
        scores = evaluate_partition(labels, fit["labels"])
        rows.append(
            {
                "seed": int(seed),
                "initialization": initialization,
                "inertia": float(fit["inertia"]),
                "acc": float(scores["acc"]),
                "nmi": float(scores["nmi"]),
                "labels": fit["labels"],
            }
        )
    return rows


def summarize_family(rows: list[dict[str, Any]]) -> dict[str, Any]:
    acc_mean, acc_sd = mean_and_sample_sd([row["acc"] for row in rows])
    nmi_mean, nmi_sd = mean_and_sample_sd([row["nmi"] for row in rows])
    selected = min(rows, key=lambda row: (row["inertia"], row["seed"]))
    reference = rows[0]["labels"]
    stability = float(np.mean([adjusted_rand_score(reference, row["labels"]) for row in rows[1:]])) if len(rows) > 1 else 1.0
    return {
        "n_runs": len(rows),
        "acc_mean": acc_mean,
        "acc_sd": acc_sd,
        "nmi_mean": nmi_mean,
        "nmi_sd": nmi_sd,
        "min_inertia": float(selected["inertia"]),
        "min_inertia_acc": float(selected["acc"]),
        "min_inertia_nmi": float(selected["nmi"]),
        "min_inertia_seed": int(selected["seed"]),
        "seed_ari_vs_seed0": stability,
        "per_seed_acc": [row["acc"] for row in rows],
        "per_seed_nmi": [row["nmi"] for row in rows],
        "per_seed_inertia": [row["inertia"] for row in rows],
        "labels_seed0": rows[0]["labels"],
    }


def paired_bootstrap(differences: np.ndarray, *, seed: int = 0, n_boot: int = 2000) -> dict[str, float]:
    """95% bootstrap CI for a mean paired difference. Conditional on fixed inputs."""
    values = np.asarray(differences, dtype=np.float64)
    rng = np.random.default_rng(seed)
    if values.size == 0:
        return {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan")}
    draws = rng.integers(0, values.size, size=(n_boot, values.size))
    means = values[draws].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return {"mean": float(values.mean()), "ci_low": float(low), "ci_high": float(high)}


PRIMARY_INIT = GREEDY
SENSITIVITY_INIT = RANDOM
