"""One original-solver USPS E8, gamma=1 trajectory.

This is the spsolve implementation in SSC_method.optimizer.shrink_embedding.
It is a verification artifact for the extension CG solver, not a historical
copy. The array is written under runs/extension_research/cache and is not
committed.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np

from SSC_method.graph_construction import knn_affinity
from SSC_method.optimizer import shrink_embedding
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import spectral_embedding
from benchmarks import load_dataset

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "runs" / "extension_research" / "cache"


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    X, _y, meta = load_dataset("USPS", version="libsvm")
    config = SpectralGraphConfig(
        k=5,
        bandwidth_rule="median_positive_knn_squared_distance",
        symmetrization="union",
        row_normalize=False,
        variant="E8",
        g_init="F",
        zero_residual_floor="median_pairwise",
        tol=1e-6,
        max_iter=300,
        eps=1e-8,
    )
    t0 = time.perf_counter()
    embedding, embed_info = spectral_embedding(X, n_components=10, config=config)
    t_embed = time.perf_counter() - t0
    affinity, graph_info = knn_affinity(
        embedding,
        k=5,
        bandwidth_rule="median_positive_knn_squared_distance",
        symmetrization="union",
    )
    print(
        f"embed_sec={t_embed:.2f} edges={int(affinity.nnz // 2)} "
        f"solver={embed_info['eigen_solver']}",
        flush=True,
    )
    t1 = time.perf_counter()
    result = shrink_embedding(
        embedding,
        affinity,
        gamma=1.0,
        eps=1e-8,
        tol=1e-6,
        max_iter=300,
        G_init=embedding,
        zero_residual_floor="median_pairwise",
        variant="E8",
    )
    t_shrink = time.perf_counter() - t1
    np.savez_compressed(
        CACHE / "usps_libsvm_e8_gamma1_original.npz",
        embedding=embedding,
        patterns=result.patterns,
        affinity_data=affinity.data,
        affinity_indices=affinity.indices,
        affinity_indptr=affinity.indptr,
        affinity_shape=np.array(affinity.shape, dtype=np.int64),
    )
    payload = {
        "dataset": "USPS",
        "version": "libsvm",
        "variant": "E8",
        "laplacian_coefficient": 2.0,
        "gamma": 1.0,
        "solver": "SSC_method.optimizer.shrink_embedding",
        "n_iterations": result.n_iterations,
        "converged": bool(result.converged),
        "fixed_point_residual": result.fixed_point_residual,
        "embed_sec": t_embed,
        "shrink_sec": t_shrink,
        "n_edges": int(affinity.nnz // 2),
        "graph": graph_info,
        "equation8_objective": result.history[-1]["equation8_objective"] if result.history else None,
        "data_checksum_field": meta.get("SHA256_checksum"),
    }
    (CACHE / "usps_libsvm_e8_gamma1_original.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    print(
        f"shrink_sec={t_shrink:.2f} iters={result.n_iterations} "
        f"converged={result.converged}",
        flush=True,
    )


if __name__ == "__main__":
    main()
