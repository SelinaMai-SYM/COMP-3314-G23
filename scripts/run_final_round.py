"""Final-round diagnostics E1–E6.

Reuses runs/strict_paper embeddings and trial logs. Does not rerun the
72-cell matrix, does not edit the SSC solver, and does not select a
configuration by maximum ACC.

Run from the v1 directory:
  python scripts/run_final_round.py --stage all
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
import zlib
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import load_dataset  # noqa: E402
from benchmarks.metrics import clustering_accuracy, normalized_mutual_information  # noqa: E402
from experiments.repair_diagnostics import (  # noqa: E402
    edge_jaccard,
    eigenvalue_summary,
    graph_summary,
    undirected_edge_set,
)
from SSC_method.graph_construction import knn_affinity  # noqa: E402
from SSC_method.objective import equation8_objective, graph_l2_term, row_l2_norms  # noqa: E402
from SSC_method.optimizer import shrink_embedding  # noqa: E402
from SSC_method.spectral_config import SpectralGraphConfig  # noqa: E402
from SSC_method.spectral_embedding import spectral_embedding  # noqa: E402

RUNS = ROOT / "runs" / "strict_paper"
OUT_RUNS = ROOT / "runs" / "final_round"
OUT_RESULTS = ROOT / "results" / "final_round"
EXPECTED_HEAD = "cb870acd47f9a62726c0cdab9b3b03395cc5e1cc"

# Explicit Lloyd settings. max_iter and tol match scikit-learn 1.8.0 defaults,
# which strict_paper left implicit inside experiments.methods._kmeans_labels.
# init is never left implicit: sklearn 1.8.0 defaults init to k-means++.
KMEANS = {
    "n_init": 1,
    "max_iter": 300,
    "tol": 1e-4,
    "algorithm": "lloyd",
    "copy_x": True,
    "verbose": 0,
}
SEEDS = list(range(50))
BOOT_DRAWS = 10000
# Absolute Euclidean tolerance for "near-coincident" rows of G.
# 1e-8 is the exact-fusion screen. 1e-3 and 1e-2 are documented loose screens.
# None of them is claimed to be a paper threshold.
COINCIDENT_TOLS = (1e-8, 1e-3, 1e-2)
# A row of G is near the corresponding row of F when
# ||g_i - f_i|| <= NEAR_F_ATOL + NEAR_F_RTOL * ||f_i||.
NEAR_F_ATOL = 1e-8
NEAR_F_RTOL = 1e-4

DATASETS = {
    "ORL": {"loader": "ORL", "version": "att92", "token": "ORL"},
    "JAFFE": {"loader": "JAFFE", "version": "zenodo", "token": "JAFFE"},
    "YaleB": {"loader": "YaleB", "version": "cropped2414", "token": "YALEB"},
    "USPS": {"loader": "USPS", "version": "libsvm", "token": "USPS"},
}
GAMMAS = (1e-6, 1e-3, 1.0, 1e3, 1e6)
GAMMA_TOKEN = {
    1e-6: "G1EM6",
    1e-3: "G1EM3",
    1.0: "G1P0",
    1e3: "G1E3",
    1e6: "G1E6",
}

PRIMARY = {
    "ORL": "20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41",
    "JAFFE": "20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d",
    "YaleB": "20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff",
    "USPS": "20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b",
}
SC_RUNS = {
    "ORL": "20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce",
    "JAFFE": "20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b",
    "YaleB": "20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51",
    "USPS": "20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055",
}
E3_CASES = (
    {"dataset": "ORL", "gamma": 1.0, "token": "G1P0"},
    {"dataset": "YaleB", "gamma": 1.0, "token": "G1P0"},
    {"dataset": "USPS", "gamma": 1000.0, "token": "G1E3"},
)


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return ""
        return format(float(value), ".16g")
    if isinstance(value, (bool, np.bool_)):
        return "true" if bool(value) else "false"
    return value


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key)) for key in fieldnames})


def sha256_array(array: np.ndarray) -> str:
    payload = np.ascontiguousarray(array)
    digest = hashlib.sha256(payload.view(np.uint8)).hexdigest()
    return digest


def git_head() -> str:
    out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True)
    return out.strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def find_run(dataset_token: str, variant: str, gamma_token: str) -> Path:
    needle = f"__{dataset_token}__SSC_{variant}_{gamma_token}__"
    matches = [p for p in RUNS.iterdir() if p.is_dir() and needle in p.name and "SMOKE" not in p.name]
    if len(matches) != 1:
        raise FileNotFoundError(f"{needle}: found {len(matches)} runs")
    return matches[0]


def load_labels(dataset_key: str):
    spec = DATASETS[dataset_key]
    features, labels, meta = load_dataset(spec["loader"], version=spec["version"])
    return np.asarray(features, dtype=np.float64), np.asarray(labels), meta


def fit_kmeans(features: np.ndarray, n_clusters: int, seed: int, init: str):
    if init not in {"random", "k-means++"}:
        raise ValueError(init)
    model = KMeans(
        n_clusters=int(n_clusters),
        init=init,
        n_init=int(KMEANS["n_init"]),
        max_iter=int(KMEANS["max_iter"]),
        tol=float(KMEANS["tol"]),
        random_state=int(seed),
        copy_x=bool(KMEANS["copy_x"]),
        algorithm=str(KMEANS["algorithm"]),
        verbose=int(KMEANS["verbose"]),
    )
    t0 = time.perf_counter()
    pred = np.asarray(model.fit_predict(features), dtype=np.int64)
    elapsed = time.perf_counter() - t0
    return pred, float(model.inertia_), int(model.n_iter_), elapsed


def mean_std(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return float("nan"), float("nan")
    if values.size == 1:
        return float(values[0]), 0.0
    return float(values.mean()), float(values.std(ddof=1))


def bootstrap_mean_ci(deltas: np.ndarray, seed: int) -> tuple[float, float, float]:
    deltas = np.asarray(deltas, dtype=np.float64)
    rng = np.random.default_rng(int(seed))
    draws = rng.integers(0, deltas.size, size=(BOOT_DRAWS, deltas.size))
    means = deltas[draws].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(deltas.mean()), float(low), float(high)


def boot_seed(*parts: str) -> int:
    key = "|".join(parts).encode()
    return 3314 + (zlib.adler32(key) % 100000)


def rebuild_w(embedding: np.ndarray, metrics: dict):
    graph = metrics["shrinkage_graph"]
    affinity, info = knn_affinity(
        embedding,
        k=int(graph["k"]),
        delta2=float(graph["delta2"]),
        knn_method=str(graph["knn_method"]),
        bandwidth_rule="fixed",
        symmetrization=str(graph["symmetrization"]),
    )
    summary = graph_summary(affinity)
    expected = metrics["shrinkage_graph_stats"]
    for key in ("n_undirected_edges", "n_stored_nnz", "n_connected_components"):
        if int(summary[key]) != int(expected[key]):
            raise RuntimeError(
                f"rebuilt W {key}={summary[key]} != saved {expected[key]} "
                f"(delta2={graph.get('delta2')}, knn={graph.get('knn_method')})"
            )
    degree_gap = abs(float(summary["degree_mean"]) - float(expected["degree_mean"]))
    if degree_gap > 1e-6:
        raise RuntimeError(f"rebuilt W degree_mean gap {degree_gap}")
    return affinity, info, summary


def history_rows(run_dir: Path) -> list[dict]:
    with (run_dir / "objective_history.csv").open() as handle:
        return list(csv.DictReader(handle))


def assert_head() -> str:
    head = git_head()
    if head != EXPECTED_HEAD:
        raise SystemExit(f"HEAD is {head}, expected {EXPECTED_HEAD}. Not resetting.")
    return head


def run_e1() -> None:
    print("E1: paired K-means on fixed F and G", flush=True)
    trials: list[dict] = []
    label_store: dict[str, np.ndarray] = {}
    settings_note = {
        "kmeans": KMEANS,
        "init_arms": ["random", "k-means++"],
        "representations": ["F", "G"],
        "seeds": SEEDS,
        "sklearn_1_8_0_default_init_is": "k-means++",
        "note": (
            "max_iter=300 and tol=1e-4 are passed explicitly. They equal "
            "sklearn 1.8.0 defaults that strict_paper did not pass. "
            "init is passed explicitly because that default is k-means++."
        ),
    }
    for dataset, run_id in PRIMARY.items():
        run_dir = RUNS / run_id
        metrics = load_json(run_dir / "metrics.json")
        _x, y, meta = load_labels(dataset)
        f_mat = np.load(run_dir / "embedding_F.npy")
        g_mat = np.load(run_dir / "embedding_G.npy")
        if f_mat.shape[0] != y.shape[0] or g_mat.shape != f_mat.shape:
            raise RuntimeError(f"{dataset} embedding/label shape mismatch")
        n_clusters = int(np.unique(y).size)
        if f_mat.shape[1] != n_clusters:
            raise RuntimeError(f"{dataset} embedding dim {f_mat.shape[1]} != K {n_clusters}")
        stored = {int(t["seed"]): t for t in metrics["trials"]}
        if sorted(stored) != SEEDS:
            raise RuntimeError(f"{dataset} stored seeds are not 0..49")
        f_hash = sha256_array(f_mat)
        g_hash = sha256_array(g_mat)
        cache_id = run_id
        for init in ("random", "k-means++"):
            level = "A_PAPER_RANDOM" if init == "random" else "C_DIAGNOSTIC_KMEANS_PLUS_PLUS"
            for target_name, target in (("F", f_mat), ("G", g_mat)):
                for seed in SEEDS:
                    labels, inertia, n_iter, elapsed = fit_kmeans(target, n_clusters, seed, init)
                    scores = {
                        "acc": float(clustering_accuracy(y, labels)),
                        "nmi": float(normalized_mutual_information(y, labels)),
                    }
                    key = f"{dataset}__{init}__{target_name}__{seed}"
                    label_store[key] = labels
                    if init == "random" and target_name == "G":
                        historical = float(stored[seed]["acc"])
                        if abs(historical - scores["acc"]) > 1e-9:
                            raise RuntimeError(
                                f"{dataset} seed {seed} recomputed ACC {scores['acc']} "
                                f"!= stored {historical}"
                            )
                    trials.append(
                        {
                            "dataset": dataset,
                            "dataset_version": DATASETS[dataset]["version"],
                            "dataset_checksum": meta.get("SHA256_checksum"),
                            "cache_run_id": cache_id,
                            "F_sha256": f_hash,
                            "G_sha256": g_hash,
                            "variant": "E8",
                            "gamma": 1.0,
                            "arm": f"KMeans({target_name})/{init}",
                            "representation": target_name,
                            "init": init,
                            "evidence_level": level,
                            "seed": seed,
                            "n_init": KMEANS["n_init"],
                            "max_iter": KMEANS["max_iter"],
                            "tol": KMEANS["tol"],
                            "algorithm": KMEANS["algorithm"],
                            "copy_x": KMEANS["copy_x"],
                            "acc": scores["acc"],
                            "nmi": scores["nmi"],
                            "inertia": inertia,
                            "kmeans_iterations": n_iter,
                            "runtime_seconds": elapsed,
                            "n_unique_predicted": int(np.unique(labels).size),
                            "assignment_file": f"runs/final_round/E1/{dataset}_labels.npz",
                            "assignment_key": key,
                        }
                    )
        print(f"  {dataset} matched stored random/G ACC on 50 seeds", flush=True)

    OUT_RUNS.joinpath("E1").mkdir(parents=True, exist_ok=True)
    for dataset in PRIMARY:
        payload = {
            key: value
            for key, value in label_store.items()
            if key.startswith(dataset + "__")
        }
        np.savez_compressed(OUT_RUNS / "E1" / f"{dataset}_labels.npz", **payload)
    (OUT_RUNS / "E1" / "kmeans_settings.json").write_text(json.dumps(settings_note, indent=2))

    trial_fields = list(trials[0].keys())
    write_csv(OUT_RESULTS / "E1_trials.csv", trials, trial_fields)

    summary_rows = []
    for dataset in PRIMARY:
        for init in ("random", "k-means++"):
            for target_name in ("F", "G"):
                rows = [
                    r
                    for r in trials
                    if r["dataset"] == dataset and r["init"] == init and r["representation"] == target_name
                ]
                acc = np.array([r["acc"] for r in rows])
                nmi = np.array([r["nmi"] for r in rows])
                inertia = np.array([r["inertia"] for r in rows])
                best = min(rows, key=lambda r: (r["inertia"], r["seed"]))
                acc_mean, acc_std = mean_std(acc)
                nmi_mean, nmi_std = mean_std(nmi)
                summary_rows.append(
                    {
                        "dataset": dataset,
                        "dataset_version": DATASETS[dataset]["version"],
                        "cache_run_id": PRIMARY[dataset],
                        "variant": "E8",
                        "gamma": 1.0,
                        "init": init,
                        "representation": target_name,
                        "evidence_level": rows[0]["evidence_level"],
                        "n_trials": len(rows),
                        "acc_mean": acc_mean,
                        "acc_std_ddof1": acc_std,
                        "nmi_mean": nmi_mean,
                        "nmi_std_ddof1": nmi_std,
                        "inertia_mean": float(inertia.mean()),
                        "inertia_std_ddof1": float(inertia.std(ddof=1)),
                        "inertia_min": float(inertia.min()),
                        "inertia_max": float(inertia.max()),
                        "best_inertia_seed": best["seed"],
                        "best_inertia_acc": best["acc"],
                        "best_inertia_nmi": best["nmi"],
                        "acc_min": float(acc.min()),
                        "acc_p50": float(np.median(acc)),
                        "acc_max": float(acc.max()),
                        "nmi_min": float(nmi.min()),
                        "nmi_p50": float(np.median(nmi)),
                        "nmi_max": float(nmi.max()),
                        "std_convention": "sample standard deviation, ddof=1",
                    }
                )
    write_csv(OUT_RESULTS / "E1_summary.csv", summary_rows, list(summary_rows[0].keys()))

    paired_rows = []
    for dataset in PRIMARY:
        for init in ("random", "k-means++"):
            by_seed_f = {
                r["seed"]: r
                for r in trials
                if r["dataset"] == dataset and r["init"] == init and r["representation"] == "F"
            }
            by_seed_g = {
                r["seed"]: r
                for r in trials
                if r["dataset"] == dataset and r["init"] == init and r["representation"] == "G"
            }
            deltas_acc = []
            deltas_nmi = []
            aris = []
            for seed in SEEDS:
                labels_f = label_store[f"{dataset}__{init}__F__{seed}"]
                labels_g = label_store[f"{dataset}__{init}__G__{seed}"]
                ari = float(adjusted_rand_score(labels_f, labels_g))
                d_acc = by_seed_g[seed]["acc"] - by_seed_f[seed]["acc"]
                d_nmi = by_seed_g[seed]["nmi"] - by_seed_f[seed]["nmi"]
                deltas_acc.append(d_acc)
                deltas_nmi.append(d_nmi)
                aris.append(ari)
                paired_rows.append(
                    {
                        "row_type": "seed",
                        "dataset": dataset,
                        "init": init,
                        "evidence_level": "A_PAPER_RANDOM" if init == "random" else "C_DIAGNOSTIC_KMEANS_PLUS_PLUS",
                        "seed": seed,
                        "acc_F": by_seed_f[seed]["acc"],
                        "acc_G": by_seed_g[seed]["acc"],
                        "nmi_F": by_seed_f[seed]["nmi"],
                        "nmi_G": by_seed_g[seed]["nmi"],
                        "delta_acc": d_acc,
                        "delta_nmi": d_nmi,
                        "ari_F_vs_G": ari,
                        "inertia_F": by_seed_f[seed]["inertia"],
                        "inertia_G": by_seed_g[seed]["inertia"],
                        "cache_run_id": PRIMARY[dataset],
                        "ci_scope": "K-means randomization conditional on this fixed F and G",
                    }
                )
            acc_mean, acc_lo, acc_hi = bootstrap_mean_ci(
                np.array(deltas_acc), boot_seed(dataset, init, "acc")
            )
            nmi_mean, nmi_lo, nmi_hi = bootstrap_mean_ci(
                np.array(deltas_nmi), boot_seed(dataset, init, "nmi")
            )
            ari_mean, ari_std = mean_std(np.array(aris))
            paired_rows.append(
                {
                    "row_type": "aggregate",
                    "dataset": dataset,
                    "init": init,
                    "evidence_level": "A_PAPER_RANDOM" if init == "random" else "C_DIAGNOSTIC_KMEANS_PLUS_PLUS",
                    "seed": "",
                    "n_pairs": 50,
                    "delta_acc_mean": acc_mean,
                    "delta_acc_ci95_low": acc_lo,
                    "delta_acc_ci95_high": acc_hi,
                    "delta_acc_ci_excludes_0": bool(acc_lo > 0.0 or acc_hi < 0.0),
                    "delta_nmi_mean": nmi_mean,
                    "delta_nmi_ci95_low": nmi_lo,
                    "delta_nmi_ci95_high": nmi_hi,
                    "delta_nmi_ci_excludes_0": bool(nmi_lo > 0.0 or nmi_hi < 0.0),
                    "fraction_seeds_acc_G_gt_F": float(np.mean(np.array(deltas_acc) > 0)),
                    "fraction_seeds_acc_G_lt_F": float(np.mean(np.array(deltas_acc) < 0)),
                    "ari_mean": ari_mean,
                    "ari_std_ddof1": ari_std,
                    "bootstrap_draws": BOOT_DRAWS,
                    "bootstrap_seed_acc": boot_seed(dataset, init, "acc"),
                    "bootstrap_seed_nmi": boot_seed(dataset, init, "nmi"),
                    "bootstrap": "percentile, paired resample of the 50 seeds",
                    "cache_run_id": PRIMARY[dataset],
                    "ci_scope": (
                        "95% percentile bootstrap of the mean paired difference. "
                        "Conditional on this fixed F and G. Does not cover dataset, "
                        "graph, or IRLS uncertainty."
                    ),
                }
            )
    # Union of keys so seed rows and aggregate rows share one header.
    fields: list[str] = []
    for row in paired_rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    write_csv(OUT_RESULTS / "E1_paired.csv", paired_rows, fields)
    _figure_e1(summary_rows, paired_rows)
    print("E1 wrote results/final_round/E1_*.csv and E1_figure.pdf", flush=True)


def _figure_e1(summary_rows: list[dict], paired_rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    datasets = list(PRIMARY)
    arms = [
        ("F", "random", "F/random"),
        ("G", "random", "G/random"),
        ("F", "k-means++", "F/++ (C)"),
        ("G", "k-means++", "G/++ (C)"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    ax = axes[0]
    x = np.arange(len(datasets))
    width = 0.18
    for index, (rep, init, label) in enumerate(arms):
        means, stds = [], []
        for dataset in datasets:
            row = next(
                r
                for r in summary_rows
                if r["dataset"] == dataset and r["representation"] == rep and r["init"] == init
            )
            means.append(100.0 * row["acc_mean"])
            stds.append(100.0 * row["acc_std_ddof1"])
        ax.bar(x + (index - 1.5) * width, means, width, yerr=stds, label=label, capsize=2)
    ax.set_xticks(x, datasets)
    ax.set_ylabel("ACC (%)")
    ax.set_title("Mean ACC ± sample SD, fixed F/G")
    ax.legend(fontsize=8)

    ax = axes[1]
    aggregates = [r for r in paired_rows if r["row_type"] == "aggregate"]
    positions = []
    labels = []
    for index, dataset in enumerate(datasets):
        for j, init in enumerate(("random", "k-means++")):
            row = next(r for r in aggregates if r["dataset"] == dataset and r["init"] == init)
            pos = index * 3 + j
            positions.append(pos)
            labels.append(f"{dataset}\n{init if init == 'random' else '++ (C)'}")
            mean = 100.0 * row["delta_acc_mean"]
            low = 100.0 * row["delta_acc_ci95_low"]
            high = 100.0 * row["delta_acc_ci95_high"]
            ax.errorbar(pos, mean, yerr=[[mean - low], [high - mean]], fmt="o", color="C0" if j == 0 else "C1", capsize=3)
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(positions, labels, fontsize=7)
    ax.set_ylabel("ΔACC (G − F), percentage points")
    ax.set_title("Paired mean and 95% bootstrap CI")
    fig.suptitle("E1 reproduction: K-means on one saved E8 γ=1 embedding. Not a published figure.", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "E1_figure.pdf")
    plt.close(fig)


def _pairwise_and_coincident(f_mat: np.ndarray, g_mat: np.ndarray, block: int = 128) -> dict:
    n = f_mat.shape[0]
    counts = {tol: 0 for tol in COINCIDENT_TOLS}
    min_g = np.inf
    sum_abs = 0.0
    sum_rel = 0.0
    n_rel = 0
    n_pairs = 0
    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        dist_g = np.linalg.norm(g_mat[i0:i1, None, :] - g_mat[None, i0:, :], axis=-1)
        dist_f = np.linalg.norm(f_mat[i0:i1, None, :] - f_mat[None, i0:, :], axis=-1)
        mask = np.triu(np.ones(dist_g.shape, dtype=bool), k=1)
        vals_g = dist_g[mask]
        vals_f = dist_f[mask]
        if vals_g.size == 0:
            continue
        min_g = min(min_g, float(vals_g.min()))
        n_pairs += int(vals_g.size)
        for tol in COINCIDENT_TOLS:
            counts[tol] += int(np.sum(vals_g <= tol))
        sum_abs += float(np.sum(np.abs(vals_g - vals_f)))
        usable = vals_f > 1e-12
        n_rel += int(np.sum(usable))
        if np.any(usable):
            sum_rel += float(np.sum(np.abs(vals_g[usable] - vals_f[usable]) / vals_f[usable]))
    row_delta = np.linalg.norm(g_mat - f_mat, axis=1)
    row_f = np.linalg.norm(f_mat, axis=1)
    near_f = row_delta <= (NEAR_F_ATOL + NEAR_F_RTOL * row_f)
    median_row = float(np.median(np.linalg.norm(g_mat, axis=1)))
    rel_tol = 1e-3 * median_row
    # Second pass only if we need the relative-tolerance pair count. Reuse 1e-2
    # when rel_tol is in the stored set; otherwise count it explicitly.
    rel_count = counts.get(rel_tol)
    if rel_count is None:
        rel_count = 0
        for i0 in range(0, n, block):
            i1 = min(n, i0 + block)
            dist_g = np.linalg.norm(g_mat[i0:i1, None, :] - g_mat[None, i0:, :], axis=-1)
            mask = np.triu(np.ones(dist_g.shape, dtype=bool), k=1)
            rel_count += int(np.sum(dist_g[mask] <= rel_tol))
    return {
        "n_pairs": n_pairs,
        "min_pairwise_G_row_distance": float(min_g),
        "n_pairs_G_le_1e-8": counts[1e-8],
        "n_pairs_G_le_1e-3": counts[1e-3],
        "n_pairs_G_le_1e-2": counts[1e-2],
        "coincident_relative_tol": rel_tol,
        "n_pairs_G_le_1e-3_median_row_norm": rel_count,
        "exact_fusion_observed": bool(counts[1e-8] > 0),
        "fraction_rows_near_F": float(np.mean(near_f)),
        "near_F_rule": "||g-f|| <= 1e-8 + 1e-4*||f||",
        "mean_abs_pairwise_distance_change": sum_abs / n_pairs,
        "mean_abs_relative_pairwise_change": sum_rel / n_rel if n_rel else float("nan"),
        "n_pairs_relative": n_rel,
    }


def run_e2() -> None:
    print("E2: shrinkage geometry on saved gamma-grid G", flush=True)
    rows = []
    for dataset in DATASETS:
        token = DATASETS[dataset]["token"]
        _x, y, _meta = load_labels(dataset)
        loaded = []
        for gamma in GAMMAS:
            run_dir = find_run(token, "E8", GAMMA_TOKEN[gamma])
            metrics = load_json(run_dir / "metrics.json")
            f_mat = np.load(run_dir / "embedding_F.npy")
            g_mat = np.load(run_dir / "embedding_G.npy")
            loaded.append((gamma, run_dir, metrics, f_mat, g_mat))
        f_hashes = [sha256_array(item[3]) for item in loaded]
        shared_f = len(set(f_hashes)) == 1
        for gamma, run_dir, metrics, f_mat, g_mat in loaded:
            # Rebuild W for this run's F and this run's recorded bandwidth.
            # A shared F hash is reported, but the objective check uses this W.
            affinity, _info, summary = rebuild_w(f_mat, metrics)
            tv_g = graph_l2_term(g_mat, affinity)
            tv_f = graph_l2_term(f_mat, affinity)
            l21 = float(np.sum(row_l2_norms(g_mat - f_mat)))
            objective = equation8_objective(g_mat, f_mat, affinity, gamma)
            if abs(objective - (l21 + gamma * tv_g)) > 1e-6 * (1.0 + abs(objective)):
                raise RuntimeError(f"{dataset} γ={gamma} objective identity failed")
            hist = history_rows(run_dir)
            recorded = float(hist[-1]["equation8_objective"])
            obj_gap = abs(recorded - objective)
            if obj_gap > 1e-4 * (1.0 + abs(recorded)):
                raise RuntimeError(
                    f"{dataset} γ={gamma} rebuilt objective {objective} != history {recorded}"
                )
            disagreements = [float(t["label_disagreement_F_G"]) for t in metrics["trials"]]
            # Recompute one full paired labeling with the explicit K-means call
            # so the stored fraction can be checked, not replaced.
            n_clusters = int(np.unique(y).size)
            recomputed = []
            for seed in SEEDS:
                labels_f, _, _, _ = fit_kmeans(f_mat, n_clusters, seed, "random")
                labels_g, _, _, _ = fit_kmeans(g_mat, n_clusters, seed, "random")
                recomputed.append(1.0 - clustering_accuracy(labels_f, labels_g))
            pair = _pairwise_and_coincident(f_mat, g_mat)
            fro_f = float(np.linalg.norm(f_mat))
            rows.append(
                {
                    "dataset": dataset,
                    "dataset_version": DATASETS[dataset]["version"],
                    "variant": "E8",
                    "gamma": gamma,
                    "run_id": run_dir.name,
                    "F_sha256": sha256_array(f_mat),
                    "G_sha256": sha256_array(g_mat),
                    "shared_F_across_gamma": shared_f,
                    "W_source": "rebuilt from saved F with recorded delta2, k, knn_method, symmetrization",
                    "W_n_undirected_edges": summary["n_undirected_edges"],
                    "W_n_stored_nnz": summary["n_stored_nnz"],
                    "W_n_connected_components": summary["n_connected_components"],
                    "W_symmetric_both_triangles": summary["symmetric_stored"],
                    "tv_convention": (
                        "sum over stored ordered pairs W_ij ||.||_2 ; "
                        "both triangles are stored, and the sum is not multiplied by 2 again"
                    ),
                    "rel_frobenius": float(np.linalg.norm(g_mat - f_mat) / fro_f),
                    "l21_G_minus_F": l21,
                    "tv_F": tv_f,
                    "tv_G": tv_g,
                    "tv_undirected_half_G": 0.5 * tv_g,
                    "relative_tv_reduction": (tv_f - tv_g) / tv_f if tv_f != 0.0 else float("nan"),
                    "equation8_objective": objective,
                    "equation8_history_gap": obj_gap,
                    "irls_converged": bool(metrics["irls_converged"]),
                    "n_irls_iterations": int(metrics["n_irls_iterations"]),
                    "fixed_point_residual": float(metrics["fixed_point_residual"]),
                    "acc_mean_stored": float(metrics["acc_mean"]),
                    "acc_std_stored_ddof1": float(metrics["acc_std"]),
                    "nmi_mean_stored": float(metrics["nmi_mean"]),
                    "nmi_std_stored_ddof1": float(metrics["nmi_std"]),
                    "n_trials_stored": int(metrics["n_trials_completed"]),
                    "label_change_fraction_stored_mean": float(np.mean(disagreements)),
                    "label_change_fraction_recomputed_mean": float(np.mean(recomputed)),
                    "label_change_abs_gap": abs(float(np.mean(disagreements)) - float(np.mean(recomputed))),
                    **pair,
                }
            )
            print(
                f"  {dataset} γ={gamma:g} relF={rows[-1]['rel_frobenius']:.4g} "
                f"tv_ratio={rows[-1]['tv_G'] / rows[-1]['tv_F']:.4g} "
                f"ACC={rows[-1]['acc_mean_stored']:.4f}",
                flush=True,
            )
    write_csv(OUT_RESULTS / "E2_shrinkage.csv", rows, list(rows[0].keys()))
    _figure_e2(rows)
    print("E2 wrote E2_shrinkage.csv and E2_figure.pdf", flush=True)


def _figure_e2(rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.8))
    for dataset in DATASETS:
        subset = [r for r in rows if r["dataset"] == dataset]
        subset.sort(key=lambda r: r["gamma"])
        gamma = [r["gamma"] for r in subset]
        axes[0].plot(gamma, [r["rel_frobenius"] for r in subset], marker="o", label=dataset)
        axes[1].plot(gamma, [r["tv_G"] / r["tv_F"] for r in subset], marker="o", label=dataset)
        axes[2].plot(gamma, [100.0 * r["acc_mean_stored"] for r in subset], marker="o", label=dataset)
    for ax, title, ylabel in zip(
        axes,
        ["Movement ||G−F||_F / ||F||_F", "TV(G) / TV(F), ordered-pair sum", "Stored K-means ACC on G"],
        ["relative Frobenius", "TV ratio", "ACC (%)"],
    ):
        ax.set_xscale("log")
        ax.set_xlabel("γ")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=9)
    axes[0].legend(fontsize=7)
    fig.suptitle(
        "E2 E8 grid from saved G. Larger movement is not interpreted as higher ACC.",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "E2_figure.pdf")
    plt.close(fig)


def _small_graph_cvxpy() -> list[dict]:
    import cvxpy
    from scipy import sparse

    rng = np.random.default_rng(1)
    n_samples, n_components = 6, 2
    embedding = rng.normal(size=(n_samples, n_components))
    weights = np.zeros((n_samples, n_samples))
    for index in range(n_samples - 1):
        weights[index, index + 1] = 1.0
        weights[index + 1, index] = 1.0
    affinity = sparse.csr_matrix(weights)
    gamma = 0.8

    def solve_exact(graph_coefficient: float):
        variable = cvxpy.Variable((n_samples, n_components))
        data_term = cvxpy.sum([cvxpy.norm(variable[i] - embedding[i], 2) for i in range(n_samples)])
        graph_terms = []
        dense = affinity.toarray()
        for i in range(n_samples):
            for j in range(n_samples):
                if dense[i, j] > 0.0:
                    graph_terms.append(dense[i, j] * cvxpy.norm(variable[i] - variable[j], 2))
        problem = cvxpy.Problem(cvxpy.Minimize(data_term + graph_coefficient * cvxpy.sum(graph_terms)))
        problem.solve(solver=cvxpy.CLARABEL, verbose=False)
        return (
            np.asarray(variable.value, dtype=np.float64),
            float(problem.value),
            str(problem.status),
        )

    rows = []
    for variant, coefficient, note in (
        ("E13", gamma / 2.0, "printed Eq.13 matches Eq.8 with the graph term halved"),
        ("E8", gamma, "E8 linear system versus Eq.8 at the printed gamma; numerical check, not a new proof"),
    ):
        result = shrink_embedding(
            embedding,
            affinity,
            gamma=gamma,
            eps=1e-9,
            tol=1e-6,
            max_iter=300,
            zero_residual_floor="median_pairwise",
            variant=variant,
        )
        reference, value, status = solve_exact(coefficient)
        solved_obj = equation8_objective(result.patterns, embedding, affinity, coefficient)
        rows.append(
            {
                "case_type": "small_graph_cvxpy",
                "dataset": "synthetic_chain_n6",
                "variant": variant,
                "gamma": gamma,
                "graph_coefficient_in_cvxpy": coefficient,
                "max_iter_budget": 300,
                "n_iterations_run": result.n_iterations,
                "converged_step_rule": result.converged,
                "equation8_at_graph_coefficient": solved_obj,
                "cvxpy_objective": value,
                "objective_gap": abs(solved_obj - value),
                "max_abs_G_gap": float(np.max(np.abs(result.patterns - reference))),
                "fixed_point_residual": result.fixed_point_residual,
                "cvxpy_status": status,
                "note": note,
                "source_test": "tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term",
            }
        )
    return rows


def _kmeans_acc_nmi(features: np.ndarray, y: np.ndarray) -> dict:
    n_clusters = int(np.unique(y).size)
    accs, nmis = [], []
    for seed in SEEDS:
        labels, _, _, _ = fit_kmeans(features, n_clusters, seed, "random")
        accs.append(clustering_accuracy(y, labels))
        nmis.append(normalized_mutual_information(y, labels))
    acc_mean, acc_std = mean_std(np.array(accs))
    nmi_mean, nmi_std = mean_std(np.array(nmis))
    return {
        "acc_mean": acc_mean,
        "acc_std_ddof1": acc_std,
        "nmi_mean": nmi_mean,
        "nmi_std_ddof1": nmi_std,
        "n_trials": 50,
        "kmeans_init": "random",
    }


def run_e3() -> None:
    print("E3: budgets 300/1000/2000 and the existing CVXPY test", flush=True)
    rows: list[dict] = []
    histories_for_figure: dict[str, list[dict]] = {}
    try:
        rows.extend(_small_graph_cvxpy())
        print(
            "  small graph "
            + ", ".join(
                f"{r['variant']} max|G|={r['max_abs_G_gap']:.3g} status={r['cvxpy_status']}"
                for r in rows
            ),
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001 - record the failure, do not invent the check
        rows.append({"case_type": "small_graph_cvxpy", "cvxpy_status": f"FAILED {type(exc).__name__}: {exc}"})
        print(f"  small graph failed: {exc}", flush=True)

    pytest_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    (OUT_RESULTS / "E3_pytest_cvxpy.txt").write_text(pytest_proc.stdout + "\n" + pytest_proc.stderr)
    rows.append(
        {
            "case_type": "existing_unit_test",
            "source_test": "tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term",
            "pytest_returncode": pytest_proc.returncode,
            "note": "Re-ran the existing test. A pass is not a new proof.",
        }
    )

    for case in E3_CASES:
        dataset = case["dataset"]
        gamma = case["gamma"]
        run_dir = find_run(DATASETS[dataset]["token"], "E8", case["token"])
        metrics = load_json(run_dir / "metrics.json")
        f_mat = np.load(run_dir / "embedding_F.npy")
        g_saved = np.load(run_dir / "embedding_G.npy")
        affinity, _info, summary = rebuild_w(f_mat, metrics)
        _x, y, _meta = load_labels(dataset)
        saved_hist = history_rows(run_dir)
        print(f"  solving {dataset} γ={gamma:g} from saved F,W", flush=True)
        acc_cache: dict[str, dict] = {}
        for budget in (300, 1000, 2000):
            t0 = time.perf_counter()
            result = shrink_embedding(
                f_mat,
                affinity,
                gamma=float(gamma),
                eps=1e-8,
                tol=1e-6,
                max_iter=budget,
                zero_residual_floor="median_pairwise",
                variant="E8",
                G_init=None,
            )
            elapsed = time.perf_counter() - t0
            g_hash = sha256_array(result.patterns)
            match_saved = float(np.max(np.abs(result.patterns - g_saved))) if budget == 300 else float("nan")
            if budget == 300 and match_saved > 1e-5:
                raise RuntimeError(f"{dataset} fresh 300-step G disagrees with saved G by {match_saved}")
            if g_hash not in acc_cache:
                acc_cache[g_hash] = _kmeans_acc_nmi(result.patterns, y)
            last = result.history[-1]
            objective = equation8_objective(result.patterns, f_mat, affinity, gamma)
            out_dir = OUT_RUNS / "E3" / f"{dataset}_g{gamma:g}_budget{budget}"
            out_dir.mkdir(parents=True, exist_ok=True)
            np.save(out_dir / "embedding_G.npy", result.patterns)
            np.save(out_dir / "embedding_F.npy", f_mat)
            with (out_dir / "objective_history.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(result.history[0].keys()))
                writer.writeheader()
                writer.writerows(result.history)
            (out_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "source_run_id": run_dir.name,
                        "budget": budget,
                        "variant": "E8",
                        "gamma": gamma,
                        "git_head": git_head(),
                        "W_edges": summary["n_undirected_edges"],
                        "max_abs_vs_saved_G_at_300": match_saved,
                    },
                    indent=2,
                )
            )
            if budget == 2000 or (result.converged and budget == 300):
                histories_for_figure[f"{dataset} γ={gamma:g}"] = result.history
            rows.append(
                {
                    "case_type": "real_data_E8",
                    "dataset": dataset,
                    "dataset_version": DATASETS[dataset]["version"],
                    "variant": "E8",
                    "gamma": gamma,
                    "source_run_id_for_F": run_dir.name,
                    "max_iter_budget": budget,
                    "n_iterations_run": result.n_iterations,
                    "converged_step_rule": result.converged,
                    "stopped_before_budget": bool(result.n_iterations < budget),
                    "equation8_objective": objective,
                    "relative_step_last": float(last["step_frobenius"]),
                    "fixed_point_residual": result.fixed_point_residual,
                    "runtime_seconds": elapsed,
                    "G_sha256": g_hash,
                    "max_abs_vs_saved_G": match_saved,
                    "saved_history_last_objective": float(saved_hist[-1]["equation8_objective"]),
                    "W_n_connected_components": summary["n_connected_components"],
                    "optimality_certificate": (
                        "fixed_point_residual of A G = S F with A = S + 2 γ Ltilde. "
                        "A small step is not an optimality certificate. No dual certificate is claimed."
                    ),
                    **acc_cache[g_hash],
                    "objective_vs_acc": "reported separately; a lower objective is not read as higher ACC",
                }
            )
            print(
                f"    budget {budget}: iters={result.n_iterations} conv={result.converged} "
                f"obj={objective:.6g} ACC={acc_cache[g_hash]['acc_mean']:.4f} t={elapsed:.1f}s",
                flush=True,
            )
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    write_csv(OUT_RESULTS / "E3_optimization.csv", rows, fields)
    _figure_e3(histories_for_figure)
    print("E3 wrote E3_optimization.csv and E3_convergence_figure.pdf", flush=True)


def _figure_e3(histories: dict[str, list[dict]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(histories)
    fig, axes = plt.subplots(1, max(len(names), 1), figsize=(4.0 * max(len(names), 1), 3.6), squeeze=False)
    for ax, name in zip(axes[0], names):
        hist = histories[name]
        iteration = [float(r["iteration"]) for r in hist]
        obj = [float(r["equation8_objective"]) for r in hist]
        ax.plot(iteration, obj, color="C0")
        for budget in (300, 1000, 2000):
            if iteration and budget - 1 <= iteration[-1]:
                ax.axvline(budget - 1, color="gray", linewidth=0.6, linestyle="--")
        ax.set_title(name + "\nEq. (8) objective, E8", fontsize=9)
        ax.set_xlabel("iteration index (0-based)")
        ax.set_ylabel("equation8_objective")
    fig.suptitle("E3 reproduction. Vertical lines are budgets, not the published Figure 2.", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "E3_convergence_figure.pdf")
    plt.close(fig)


def _orientations(features: np.ndarray) -> dict[str, np.ndarray]:
    images = features.reshape(-1, 32, 32)
    return {
        "C": images.reshape(features.shape[0], -1),
        "transpose": np.transpose(images, (0, 2, 1)).reshape(features.shape[0], -1),
        "rot90": np.rot90(images, 1, axes=(1, 2)).reshape(features.shape[0], -1),
        "rot180": np.rot90(images, 2, axes=(1, 2)).reshape(features.shape[0], -1),
        "rot270": np.rot90(images, 3, axes=(1, 2)).reshape(features.shape[0], -1),
        "fliplr": np.flip(images, axis=2).reshape(features.shape[0], -1),
        "flipud": np.flip(images, axis=1).reshape(features.shape[0], -1),
    }


def _match_versions(left: np.ndarray, left_y: np.ndarray, right: np.ndarray, right_y: np.ndarray) -> dict:
    """Match Deng Cai rows to a spatially transformed cropped matrix.

    Class ids are aligned by class-mean images, then images are matched
    inside each paired class. A large residual means pixel identity is not claimed.
    """
    n_classes = 38

    def means(matrix, labels):
        out = np.zeros((n_classes, matrix.shape[1]), dtype=np.float64)
        for label in range(n_classes):
            out[label] = matrix[labels == label].mean(axis=0)
        return out

    def pair_l2(a, b):
        aa = np.sum(a * a, axis=1)[:, None]
        bb = np.sum(b * b, axis=1)[None, :]
        return np.sqrt(np.maximum(aa + bb - 2.0 * (a @ b.T), 0.0))

    best = None
    for name, transformed in _orientations(right).items():
        cost = pair_l2(means(left, left_y), means(transformed, right_y))
        r_ind, c_ind = linear_sum_assignment(cost)
        total = float(cost[r_ind, c_ind].sum())
        if best is None or total < best["class_mean_l2_sum"]:
            best = {
                "orientation": name,
                "class_mean_l2_sum": total,
                "class_pairs": list(zip(r_ind.tolist(), c_ind.tolist())),
                "matrix": transformed,
            }
    assert best is not None
    matched_l2 = []
    matched_maxabs = []
    n_exact = 0
    n_matched = 0
    n_unmatched = 0
    for left_label, right_label in best["class_pairs"]:
        a = left[left_y == left_label]
        b = best["matrix"][right_y == right_label]
        if a.shape[0] != b.shape[0]:
            n_unmatched += abs(int(a.shape[0] - b.shape[0]))
        dist = pair_l2(a, b)
        rr, cc = linear_sum_assignment(dist)
        for i, j in zip(rr, cc):
            n_matched += 1
            matched_l2.append(float(dist[i, j]))
            maxabs = float(np.max(np.abs(a[i] - b[j])))
            matched_maxabs.append(maxabs)
            if maxabs <= 1e-8:
                n_exact += 1
    row_exact = float(np.mean(np.max(np.abs(left - right), axis=1) <= 1e-8))
    return {
        "best_orientation": best["orientation"],
        "class_mean_l2_sum": best["class_mean_l2_sum"],
        "n_images_matched": n_matched,
        "n_class_count_unmatched_slots": n_unmatched,
        "median_matched_image_l2": float(np.median(matched_l2)),
        "max_matched_image_maxabs": float(np.max(matched_maxabs)),
        "fraction_matched_maxabs_le_1e-8": n_exact / n_matched,
        "fraction_rows_identical_in_stored_order": row_exact,
        "pixel_identity_claimed": bool(n_exact == n_matched and n_unmatched == 0),
    }


def _spectral_variant(features, labels, config: SpectralGraphConfig) -> dict:
    embedding, info = spectral_embedding(features, n_components=int(np.unique(labels).size), config=config)
    affinity, graph_info = knn_affinity(
        features,
        k=config.k,
        delta2=config.resolved_delta2(),
        knn_method=config.knn_method,
        bandwidth_rule=config.bandwidth_rule,
        symmetrization=config.symmetrization,
    )
    if graph_info.get("delta2") != info["graph"].get("delta2"):
        # Both calls use the same rule; a mismatch means the two graphs differ.
        if abs(float(graph_info["delta2"]) - float(info["graph"]["delta2"])) > 1e-8:
            raise RuntimeError("spectral graph delta2 disagreed with the diagnostic rebuild")
    summary = graph_summary(affinity)
    weights = affinity.data
    degrees = np.asarray(affinity.sum(axis=1)).ravel()
    evals = np.asarray(info["eigenvalues"], dtype=np.float64)
    multiplicity = int(np.sum(evals <= evals[0] + 1e-8))
    scores = _kmeans_acc_nmi(embedding, labels)
    return {
        "embedding": embedding,
        "info": info,
        "summary": summary,
        "edges": undirected_edge_set(affinity),
        "affinity_min": float(weights.min()) if weights.size else float("nan"),
        "affinity_p50": float(np.median(weights)) if weights.size else float("nan"),
        "affinity_max": float(weights.max()) if weights.size else float("nan"),
        "degree_p50": float(np.median(degrees)),
        "eigen_summary": eigenvalue_summary(evals, n_list=6),
        "eigen_multiplicity_atol_1e-8": multiplicity,
        "scores": scores,
        "F_sha256": sha256_array(embedding),
    }


def run_e4() -> None:
    print("E4: YaleB dengcai32 vs cropped2414", flush=True)
    versions = {
        "dengcai32": load_dataset("YaleB", version="dengcai32"),
        "cropped2414": load_dataset("YaleB", version="cropped2414"),
        "cropped2414_nearest": load_dataset("YaleB", version="cropped2414_nearest"),
        "cropped2414_bicubic": load_dataset("YaleB", version="cropped2414_bicubic"),
    }
    data_rows = []
    for name, (features, labels, meta) in versions.items():
        counts = np.bincount(labels, minlength=38)
        _unique, dup_counts = np.unique(np.round(features, decimals=10), axis=0, return_counts=True)
        data_rows.append(
            {
                "record": "version",
                "version": name,
                "n_images": int(features.shape[0]),
                "n_identities": int(np.unique(labels).size),
                "feature_dim": int(features.shape[1]),
                "spatial": "32x32",
                "float_min": float(features.min()),
                "float_max": float(features.max()),
                "float_mean": float(features.mean()),
                "pixel_scale": "uint8/255 into [0,1]",
                "per_identity_counts": ",".join(str(int(c)) for c in counts),
                "counts_min": int(counts.min()),
                "counts_max": int(counts.max()),
                "n_duplicate_rows_atol_1e-10": int(np.sum(dup_counts > 1)),
                "checksum_field": meta.get("SHA256_checksum"),
                "archive_or_array": meta.get("archive_path") or meta.get("processed_array_path"),
                "interpolation": meta.get("interpolation", "none_already_32x32"),
                "label_encoding": meta.get("label_encoding"),
                "array_sha256": sha256_array(features),
            }
        )
    match = _match_versions(versions["dengcai32"][0], versions["dengcai32"][1], versions["cropped2414"][0], versions["cropped2414"][1])
    data_rows.append({"record": "match_dengcai32_vs_cropped2414_bilinear", **match})
    # Same check against nearest and bicubic, identity of pixels still unexpected.
    for other in ("cropped2414_nearest", "cropped2414_bicubic"):
        other_match = _match_versions(
            versions["dengcai32"][0],
            versions["dengcai32"][1],
            versions[other][0],
            versions[other][1],
        )
        data_rows.append({"record": f"match_dengcai32_vs_{other}", **other_match})
    count_equal = data_rows[0]["per_identity_counts"] == data_rows[1]["per_identity_counts"]
    data_rows.append(
        {
            "record": "count_vector_equal_dengcai_vs_bilinear",
            "per_identity_count_vectors_equal": count_equal,
            "note": (
                "Equal histograms do not identify people. Cropped files have subject "
                "folder names and drop yaleB14. The mat file has no subject names."
            ),
        }
    )

    base = dict(
        k=5,
        bandwidth_rule="median_positive_knn_squared_distance",
        symmetrization="union",
        laplacian="symmetric_normalized_eq4",
        row_normalize=False,
        knn_method="auto",
    )
    variants = [
        ("controlled", "cropped2414", base, "PAPER_CONSISTENT", "same graph rule as strict_paper; kernel of 32x32 is unspecified in the paper"),
        ("controlled", "dengcai32", base, "PAPER_CONSISTENT", "Deng Cai matrix, same graph rule; not selected by ACC"),
        ("bandwidth_mean_knn", "cropped2414", {**base, "bandwidth_rule": "mean_knn_distance_scale"}, "PAPER_CONSISTENT", "alternative bandwidth; paper does not state delta"),
        ("bandwidth_mean_knn", "dengcai32", {**base, "bandwidth_rule": "mean_knn_distance_scale"}, "PAPER_CONSISTENT", "alternative bandwidth"),
        ("symmetrization_mutual", "cropped2414", {**base, "symmetrization": "mutual"}, "PAPER_CONSISTENT", "paper does not choose union vs mutual"),
        ("symmetrization_mutual", "dengcai32", {**base, "symmetrization": "mutual"}, "PAPER_CONSISTENT", "paper does not choose union vs mutual"),
        ("row_normalize", "cropped2414", {**base, "row_normalize": True}, "NON_PAPER_DIAGNOSTIC", "Ng-Jordan-Weiss row norm; Level C"),
        ("row_normalize", "dengcai32", {**base, "row_normalize": True}, "NON_PAPER_DIAGNOSTIC", "Ng-Jordan-Weiss row norm; Level C"),
        ("interpolation_nearest", "cropped2414_nearest", base, "PAPER_CONSISTENT", "resize kernel not stated; not selected by ACC"),
        ("interpolation_bicubic", "cropped2414_bicubic", base, "PAPER_CONSISTENT", "resize kernel not stated; not selected by ACC"),
    ]
    graph_rows = []
    embeddings = {}
    saved_sc = np.load(RUNS / SC_RUNS["YaleB"] / "embedding_F.npy")
    for variant_name, version, params, level, note in variants:
        features, labels, _meta = versions[version]
        config = SpectralGraphConfig(**params)
        print(f"  spectral {version} / {variant_name}", flush=True)
        packed = _spectral_variant(features, labels, config)
        embeddings[(variant_name, version)] = packed
        out_dir = OUT_RUNS / "E4" / f"{version}__{variant_name}"
        out_dir.mkdir(parents=True, exist_ok=True)
        np.save(out_dir / "embedding_F.npy", packed["embedding"])
        gap = ""
        if version == "cropped2414" and variant_name == "controlled":
            gap = float(np.max(np.abs(packed["embedding"] - saved_sc)))
        graph_rows.append(
            {
                "variant": variant_name,
                "version": version,
                "evidence_level": level,
                "note": note,
                "selected_as_paper_method": False,
                "k": 5,
                "bandwidth_rule": params["bandwidth_rule"],
                "symmetrization": params["symmetrization"],
                "laplacian": params["laplacian"],
                "row_normalize": params["row_normalize"],
                "n_connected_components": packed["summary"]["n_connected_components"],
                "n_undirected_edges": packed["summary"]["n_undirected_edges"],
                "degree_min": packed["summary"]["degree_min"],
                "degree_p50": packed["degree_p50"],
                "degree_mean": packed["summary"]["degree_mean"],
                "degree_max": packed["summary"]["degree_max"],
                "affinity_min": packed["affinity_min"],
                "affinity_p50": packed["affinity_p50"],
                "affinity_max": packed["affinity_max"],
                "eigen_min": packed["eigen_summary"]["min"],
                "eigen_max": packed["eigen_summary"]["max"],
                "eigen_gap_1_2": packed["eigen_summary"].get("gap_1_2"),
                "eigen_multiplicity_atol_1e-8": packed["eigen_multiplicity_atol_1e-8"],
                "eigenvalues_listed": ",".join(str(v) for v in packed["eigen_summary"]["listed"]),
                "F_sha256": packed["F_sha256"],
                "max_abs_vs_saved_strict_sc_F": gap,
                **packed["scores"],
                "kmeans_settings": "random n_init=1 max_iter=300 tol=1e-4 algorithm=lloyd seeds 0..49",
            }
        )
    left_edges = embeddings[("controlled", "dengcai32")]["edges"]
    right_edges = embeddings[("controlled", "cropped2414")]["edges"]
    graph_rows.append(
        {
            "variant": "controlled_graph_overlap",
            "version": "dengcai32_vs_cropped2414",
            "evidence_level": "comparison",
            "edge_jaccard": edge_jaccard(left_edges, right_edges),
            "note": (
                "Same graph procedure, not the same W. kNN depends on the pixels, "
                "so copying one W onto the other matrix would no longer be spectral clustering of that matrix."
            ),
            "selected_as_paper_method": False,
        }
    )
    data_fields: list[str] = []
    for row in data_rows:
        for key in row:
            if key not in data_fields:
                data_fields.append(key)
    graph_fields: list[str] = []
    for row in graph_rows:
        for key in row:
            if key not in graph_fields:
                graph_fields.append(key)
    write_csv(OUT_RESULTS / "E4_data_comparison.csv", data_rows, data_fields)
    write_csv(OUT_RESULTS / "E4_graph_diagnostics.csv", graph_rows, graph_fields)
    _figure_e4(graph_rows)
    print("E4 wrote E4_data_comparison.csv, E4_graph_diagnostics.csv, E4_figure.pdf", flush=True)


def _figure_e4(graph_rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    controlled = [r for r in graph_rows if r.get("variant") == "controlled"]
    diagnostic = [r for r in graph_rows if r.get("variant") not in {"controlled", "controlled_graph_overlap", None}]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))
    ax = axes[0]
    labels = [r["version"] for r in controlled]
    means = [100.0 * r["acc_mean"] for r in controlled]
    stds = [100.0 * r["acc_std_ddof1"] for r in controlled]
    ax.bar(labels, means, yerr=stds, capsize=3, color=["C0", "C1"])
    ax.set_ylabel("K-means(F) ACC (%)")
    ax.set_title("Controlled: same graph rule, only the matrix changes")
    ax = axes[1]
    names = [f"{r['version'][:8]}\n{r['variant']}" for r in diagnostic]
    ax.bar(range(len(diagnostic)), [100.0 * r["acc_mean"] for r in diagnostic], color="0.65")
    ax.set_xticks(range(len(diagnostic)), names, fontsize=6)
    ax.set_ylabel("K-means(F) ACC (%)")
    ax.set_title("Diagnostics. Highest bar is not the paper method.")
    fig.suptitle("E4 YaleB version audit. Paper Table 1 YaleB SC is 34.8%, not plotted as our curve.", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "E4_figure.pdf")
    plt.close(fig)


def run_e5() -> None:
    print("E5: our gamma and convergence curves from saved histories", flush=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    points = []
    for dataset in DATASETS:
        sc_metrics = load_json((RUNS / SC_RUNS[dataset]) / "metrics.json")
        for gamma in GAMMAS:
            run_dir = find_run(DATASETS[dataset]["token"], "E8", GAMMA_TOKEN[gamma])
            metrics = load_json(run_dir / "metrics.json")
            points.append(
                {
                    "dataset": dataset,
                    "gamma": gamma,
                    "run_id": run_dir.name,
                    "acc_mean": float(metrics["acc_mean"]),
                    "acc_std_ddof1": float(metrics["acc_std"]),
                    "nmi_mean": float(metrics["nmi_mean"]),
                    "irls_converged": bool(metrics["irls_converged"]),
                    "n_irls_iterations": int(metrics["n_irls_iterations"]),
                    "sc_run_id": SC_RUNS[dataset],
                    "sc_acc_mean": float(sc_metrics["acc_mean"]),
                    "curve_label": "our reproduction, not the published Figure 1",
                    "aggregation": "mean over 50 random K-means seeds on one G; not best-of-50 objective",
                }
            )
    write_csv(OUT_RESULTS / "E5_parameter_points.csv", points, list(points[0].keys()))

    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.4))
    for ax, dataset in zip(axes.ravel(), DATASETS):
        subset = [r for r in points if r["dataset"] == dataset]
        gamma = [r["gamma"] for r in subset]
        acc = [100.0 * r["acc_mean"] for r in subset]
        std = [100.0 * r["acc_std_ddof1"] for r in subset]
        ax.errorbar(gamma, acc, yerr=std, marker="o", capsize=3, label="E8 mean ACC")
        ax.axhline(100.0 * subset[0]["sc_acc_mean"], color="C1", linestyle="--", label="our SC mean")
        for r, x, y in zip(subset, gamma, acc):
            if not r["irls_converged"]:
                ax.scatter([x], [y], facecolors="none", edgecolors="black", s=80, zorder=3)
        ax.set_xscale("log")
        ax.set_title(f"{dataset} {DATASETS[dataset]['version']}")
        ax.set_xlabel("γ")
        ax.set_ylabel("ACC (%)")
        ax.legend(fontsize=7)
    fig.suptitle(
        "Our reproduction of a γ–ACC sweep (paper Figure 1). Open circles: IRLS tol not met by step 300.\n"
        "Not the published curve. AR, UMIST, binalpha, MSRA50 are omitted (no paper-identity run).",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "E5_parameter_sensitivity.pdf")
    plt.close(fig)

    curve_rows = []
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.4))
    for ax, dataset in zip(axes.ravel(), DATASETS):
        run_dir = RUNS / PRIMARY[dataset]
        metrics = load_json(run_dir / "metrics.json")
        hist = history_rows(run_dir)
        iteration, objective = [], []
        for row in hist:
            iteration.append(float(row["iteration"]))
            objective.append(float(row["equation8_objective"]))
            curve_rows.append(
                {
                    "dataset": dataset,
                    "run_id": run_dir.name,
                    "variant": "E8",
                    "gamma": 1.0,
                    "iteration": float(row["iteration"]),
                    "equation8_objective": float(row["equation8_objective"]),
                    "sqrt_smoothed_equation8_objective": float(row["sqrt_smoothed_equation8_objective"]),
                    "irls_quadratic_surrogate": float(row["irls_quadratic_surrogate"]),
                    "plotted_quantity": "equation8_objective",
                    "irls_converged": bool(metrics["irls_converged"]),
                }
            )
        ax.plot(iteration, objective, color="C0")
        flag = "step tol met" if metrics["irls_converged"] else "stopped at 300, tol not met"
        ax.set_title(f"{dataset} E8 γ=1\n{flag}", fontsize=9)
        ax.set_xlabel("iteration index (0-based)")
        ax.set_ylabel("Eq. (8) objective")
    fig.suptitle(
        "Our reproduction of a convergence curve (paper Figure 2, γ=1).\n"
        "Plotted quantity is the recorded nonsmooth Eq. (8), not the IRLS surrogate and not the published curve.",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "E5_convergence.pdf")
    plt.close(fig)
    write_csv(OUT_RESULTS / "E5_convergence_curves.csv", curve_rows, list(curve_rows[0].keys()))
    print("E5 wrote both PDFs", flush=True)


def _parse_pm(text: str):
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*±\s*([0-9]+(?:\.[0-9]+)?)", text or "")
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def run_e6() -> None:
    print("E6: metric tests and seed audit", flush=True)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_metrics.py", "tests/test_final_round_e6.py", "tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    (OUT_RESULTS / "E6_pytest.txt").write_text(proc.stdout + "\n" + proc.stderr)

    matrix_path = ROOT / "results" / "strict_reproduction_matrix.csv"
    with matrix_path.open() as handle:
        matrix_rows = list(csv.DictReader(handle))

    cells = []
    problems = []
    seen = {}
    for run_dir in sorted(p for p in RUNS.iterdir() if p.is_dir()):
        name = run_dir.name
        if "SMOKE" in name:
            continue
        if not any(token in name for token in ("SSC_E8", "SSC_E13", "SC_EQ4", "K1_RANDOM", "K3_KMEANSPP")):
            continue
        if not any(token in name for token in ("__ORL__", "__JAFFE__", "__YALEB__", "__USPS__")):
            continue
        metrics = load_json(run_dir / "metrics.json")
        status = load_json(run_dir / "status.json")
        trials = metrics.get("trials") or []
        seeds = [int(t["seed"]) for t in trials]
        accs = np.array([float(t["acc"]) for t in trials], dtype=np.float64)
        nmis = np.array([float(t["nmi"]) for t in trials], dtype=np.float64)
        acc_mean, acc_std = mean_std(accs) if accs.size else (None, None)
        nmi_mean, nmi_std = mean_std(nmis) if nmis.size else (None, None)
        stdout = (run_dir / "stdout.log").read_text(errors="replace") if (run_dir / "stdout.log").exists() else ""
        prepared_lines = sum(1 for line in stdout.splitlines() if "prepared " in line)
        factor = (load_json(run_dir / "metadata.json").get("factor") if (run_dir / "metadata.json").exists() else None)
        dataset = load_json(run_dir / "metadata.json").get("dataset")
        key = (dataset, factor)
        if key in seen:
            problems.append(f"duplicate completed cell {key}: {seen[key]} and {name}")
        seen[key] = name
        cell_problems = []
        if status.get("status") != "COMPLETED":
            cell_problems.append("status not COMPLETED")
        if seeds != list(range(50)):
            cell_problems.append(f"seeds are not 0..49 (n={len(seeds)} unique={len(set(seeds))})")
        if accs.size and abs(acc_mean - float(metrics["acc_mean"])) > 1e-12:
            cell_problems.append("acc_mean disagrees with trials")
        if accs.size > 1 and abs(acc_std - float(metrics["acc_std"])) > 1e-9:
            cell_problems.append("acc_std disagrees with ddof=1")
        if nmis.size and abs(nmi_mean - float(metrics["nmi_mean"])) > 1e-12:
            cell_problems.append("nmi_mean disagrees with trials")
        if "SSC_" in name:
            if prepared_lines != 1:
                cell_problems.append(f"prepared-line count {prepared_lines}, expected 1")
            if not (run_dir / "embedding_F.npy").exists() or not (run_dir / "embedding_G.npy").exists():
                cell_problems.append("missing F or G")
            if metrics.get("kmeans_init") not in (None, "random"):
                cell_problems.append(f"kmeans_init {metrics.get('kmeans_init')}")
        problems.extend(f"{name}: {item}" for item in cell_problems)
        cells.append(
            {
                "run_id": name,
                "dataset": dataset,
                "factor": factor,
                "n_trials": len(trials),
                "seeds_are_0_to_49": seeds == list(range(50)),
                "acc_mean_matches_trials": not any("acc_mean" in item for item in cell_problems),
                "std_matches_ddof1": not any("acc_std" in item for item in cell_problems),
                "prepared_once": prepared_lines == 1 if "SSC_" in name or "SC_EQ4" in name else None,
                "kmeans_init": metrics.get("kmeans_init"),
                "irls_iterations_single_value": metrics.get("n_irls_iterations"),
            }
        )

    matrix_checks = []
    for row in matrix_rows:
        run_field = row.get("run IDs") or ""
        if "STRICT_PAPER" not in run_field or "completed" not in (row.get("status") or ""):
            continue
        if not any(ds in run_field for ds in ("__ORL__", "__JAFFE__", "__YALEB__", "__USPS__")):
            continue
        paper = row.get("Paper ACC") or ""
        reproduced = row.get("Reproduced ACC") or ""
        parsed = _parse_pm(reproduced)
        historical_in_paper = "historical only" in paper
        historical_in_reproduced = "historical only" in reproduced
        metrics = None
        run_id = run_field.split(";")[0].strip()
        metrics_path = RUNS / run_id / "metrics.json"
        compared_to = "acc_mean"
        if metrics_path.exists() and parsed is not None:
            metrics = load_json(metrics_path)
            selection = row.get("selection rule") or ""
            matrix_n = int(float(row.get("trial count") or 0))
            if matrix_n == 1 and "lowest" in selection and "inertia" in selection:
                # K2/K4 report one trial from the parent run, not the 50-trial mean.
                best = min(
                    metrics["trials"],
                    key=lambda trial: (float(trial["kmeans_inertia"]), int(trial["seed"])),
                )
                gap = abs(parsed[0] / 100.0 - float(best["acc"]))
                compared_to = f"lowest_inertia_seed_{best['seed']}"
            else:
                gap = abs(parsed[0] / 100.0 - float(metrics["acc_mean"]))
                if int(metrics["n_trials_completed"]) != matrix_n:
                    problems.append(f"matrix {run_id}: trial count {matrix_n} != metrics {metrics['n_trials_completed']}")
        else:
            gap = None
        ok = bool(historical_in_paper and not historical_in_reproduced and gap is not None and gap < 6e-4)
        if not ok:
            problems.append(f"matrix {run_id}: paper_hist={historical_in_paper} gap={gap}")
        matrix_checks.append(
            {
                "run_id": run_id,
                "paper_marked_historical_only": historical_in_paper,
                "reproduced_marked_historical_only": historical_in_reproduced,
                "abs_gap_fraction": gap,
                "compared_to": compared_to,
                "ok": ok,
            }
        )

    e1_audit = {"present": (OUT_RESULTS / "E1_trials.csv").exists()}
    if e1_audit["present"]:
        with (OUT_RESULTS / "E1_trials.csv").open() as handle:
            e1_rows = list(csv.DictReader(handle))
        e1_audit["n_rows"] = len(e1_rows)
        e1_audit["arms"] = sorted({(r["dataset"], r["init"], r["representation"]) for r in e1_rows})
        e1_audit["each_arm_has_seeds_0_to_49"] = all(
            sorted(int(r["seed"]) for r in e1_rows if (r["dataset"], r["init"], r["representation"]) == arm) == SEEDS
            for arm in e1_audit["arms"]
        )
        e1_audit["explicit_fields"] = sorted({(r["n_init"], r["max_iter"], r["tol"], r["algorithm"]) for r in e1_rows})

    report = {
        "pytest_returncode": proc.returncode,
        "pytest_stdout_tail": proc.stdout[-2000:],
        "std_convention": "sample standard deviation with ddof=1, computed in run_experiment.py and re-checked here from trial lists",
        "n_cells_audited": len(cells),
        "n_problems": len(problems),
        "problems": problems,
        "cells": cells,
        "matrix_checks_n": len(matrix_checks),
        "matrix_checks_failed": [c for c in matrix_checks if not c["ok"]][:20],
        "kmeans_only_randomness": (
            "SSC and SC cells record one prepare step, one F (and one G for SSC), "
            "and 50 distinct K-means seeds. The IRLS iteration count is a single integer, not 50 solves."
        ),
        "e1": e1_audit,
        "acc_definition": "Hungarian one-to-one alignment, benchmarks.metrics.clustering_accuracy",
        "nmi_definition": "geometric-mean entropy normalization, Strehl and Ghosh, matching sklearn average_method='geometric'",
        "empty_cluster_convention": (
            "Labels that do not occur are not inserted. ACC/NMI use the observed partition. "
            "A prediction that uses fewer than K labels is scored as that coarser partition."
        ),
    }
    (OUT_RESULTS / "E6_validation.json").write_text(json.dumps(report, indent=2))
    if proc.returncode != 0 or problems:
        print(f"E6 problems: pytest={proc.returncode} n_problems={len(problems)}", flush=True)
        for item in problems[:12]:
            print(" ", item, flush=True)
    else:
        print(f"E6 clean: {len(cells)} cells, pytest returncode 0", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=["all", "e1", "e2", "e3", "e4", "e5", "e6"])
    args = parser.parse_args()
    head = assert_head()
    print(f"HEAD {head}", flush=True)
    OUT_RESULTS.mkdir(parents=True, exist_ok=True)
    OUT_RUNS.mkdir(parents=True, exist_ok=True)
    stages = {
        "e1": run_e1,
        "e2": run_e2,
        "e3": run_e3,
        "e4": run_e4,
        "e5": run_e5,
        "e6": run_e6,
    }
    order = ["e1", "e2", "e3", "e4", "e5", "e6"] if args.stage == "all" else [args.stage]
    for name in order:
        t0 = time.perf_counter()
        stages[name]()
        print(f"{name} done in {time.perf_counter() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
