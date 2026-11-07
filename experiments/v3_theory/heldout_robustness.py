"""Held-out perturbation robustness for X2. Not used to choose beta."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score

from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY, fit_lloyd
from method_extension.v3_theory.common.graphs import knn_graph, upper_edges
from method_extension.v3_theory.x2_stability_graph.weights import perturb_features, perturb_images, perturbation_list

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "runs" / "v3_theory" / "cache"
JOBS = ROOT / "results" / "v3_theory" / "jobs"
OUT = ROOT / "results" / "v3_theory" / "heldout_robustness.csv"


def edge_set(matrix) -> set[tuple[int, int]]:
    src, dst, _weight = upper_edges(matrix)
    return set(zip(src.tolist(), dst.tolist(), strict=True))


def main() -> None:
    rows = []
    for meta_path in sorted(CACHE.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text())
        features = np.load(meta_path.parent / "X.npy")
        labels = np.load(meta_path.parent / "y.npy")
        base_job = JOBS / f"X2__{meta['key']}__beta_0.json"
        alt_job = JOBS / f"X2__{meta['key']}__beta_1.json"
        if not base_job.is_file() or not alt_job.is_file():
            continue
        base = json.loads(base_job.read_text())
        alt = json.loads(alt_job.read_text())
        if "labels_seed0" not in base or "labels_seed0" not in alt:
            continue
        base_labels = np.asarray(base["labels_seed0"])
        alt_labels = np.asarray(alt["labels_seed0"])
        aris_base = []
        aris_alt = []
        jaccards = []
        original = knn_graph(np.load(meta_path.parent / "F.npy"), 5)
        original_edges = edge_set(original)
        for index, (_kind, brightness, contrast) in enumerate(perturbation_list("heldout")):
            if meta["benchmark"] == "BinAlpha":
                changed = perturb_features(features, seed=2000 + index)
            else:
                changed = perturb_images(features, brightness, contrast)
            embedding, _info = spectral_embedding(
                changed,
                n_components=int(meta["n_components"]),
                config=SpectralGraphConfig(k=5, delta2=None, row_normalize=False, symmetrization="union"),
            )
            graph = knn_graph(embedding, 5)
            edges = edge_set(graph)
            union = original_edges | edges
            jaccards.append(len(original_edges & edges) / max(len(union), 1))
            fit = fit_lloyd(embedding, int(meta["n_classes"]), 0, GREEDY)
            aris_base.append(float(adjusted_rand_score(base_labels, fit["labels"])))
            aris_alt.append(float(adjusted_rand_score(alt_labels, fit["labels"])))
        rows.append(
            {
                "dataset_id": meta["dataset_id"],
                "prep": meta["prep"],
                "beta0_heldout_ari_mean": float(np.mean(aris_base)),
                "beta1_heldout_ari_mean": float(np.mean(aris_alt)),
                "heldout_edge_jaccard_mean": float(np.mean(jaccards)),
                "note": "ARI is between the unperturbed seed-0 partition and k-means on a held-out perturbed embedding. Not a class-correctness score and not used to choose beta.",
            }
        )
        print(rows[-1]["dataset_id"], rows[-1]["prep"], rows[-1]["beta1_heldout_ari_mean"], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        OUT.write_text("")
        return
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
