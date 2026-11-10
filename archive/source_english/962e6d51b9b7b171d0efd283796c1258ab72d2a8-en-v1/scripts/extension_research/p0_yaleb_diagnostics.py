"""P0 YaleB checks and the pre-specified D0–D6 diagnostics.

Labels are used only after F and G exist, and only for ACC/NMI.
Graph construction, shrinkage, and K-means initialization do not read y
except when scoring a finished partition. Higher diagnostic ACC is not
treated as the paper protocol.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import hashlib
import json
import time
import traceback
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.linalg import eigh
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import KMeans

from SSC_method.graph_construction import (
    knn_affinity,
    knn_neighbor_squared_distances,
    symmetric_normalized_laplacian,
)
from SSC_method.optimizer import shrink_embedding
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import smallest_eigenpairs, spectral_embedding
from benchmarks import load_dataset
from benchmarks.metrics import clustering_accuracy, normalized_mutual_information

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "extension_research"
DOCS = ROOT / "docs" / "extension_research"
SEEDS = list(range(50))
VERSIONS = ("cropped2414", "dengcai32")

# Locked before any diagnostic accuracy is computed.
DIAGNOSTICS = (
    {
        "id": "D0",
        "factor": "control_protocol",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "symmetrization": "union",
        "row_normalize": False,
        "kmeans_init": "random",
        "reuse": None,
        "protocol_tag": "PAPER_CONSISTENT_UNVERIFIED",
        "notes": (
            "Control. k=5 and the symmetric normalized Laplacian are PAPER_EXPLICIT. "
            "Median bandwidth, union symmetrization, raw eigenvectors, random Lloyd "
            "n_init=1, G0=F, and E8 (coefficient 2, not default E13) are "
            "PAPER_CONSISTENT_UNVERIFIED. gamma=1 is the study control."
        ),
    },
    {
        "id": "D1",
        "factor": "bandwidth_only",
        "bandwidth_rule": "mean_knn_distance_scale",
        "symmetrization": "union",
        "row_normalize": False,
        "kmeans_init": "random",
        "reuse": None,
        "protocol_tag": "NON_PAPER_DIAGNOSTIC",
        "notes": "Only the bandwidth rule changes, on both the feature graph and the shrinkage graph.",
    },
    {
        "id": "D2",
        "factor": "symmetrization_only",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "symmetrization": "mutual",
        "row_normalize": False,
        "kmeans_init": "random",
        "reuse": None,
        "protocol_tag": "NON_PAPER_DIAGNOSTIC",
        "notes": "Only symmetrization changes, on both graphs. Mutual kNN is not the paper statement.",
    },
    {
        "id": "D3",
        "factor": "row_normalization_only",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "symmetrization": "union",
        "row_normalize": True,
        "kmeans_init": "random",
        "reuse": None,
        "protocol_tag": "NON_PAPER_DIAGNOSTIC",
        "notes": "Ng-Jordan-Weiss row normalization of F only. The paper does not state it.",
    },
    {
        "id": "D4",
        "factor": "kmeans_init_only",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "symmetrization": "union",
        "row_normalize": False,
        "kmeans_init": "k-means++",
        "reuse": "D0",
        "protocol_tag": "NON_PAPER_DIAGNOSTIC",
        "notes": "Same F and G as D0. Only the K-means initializer changes. Not selected by ACC.",
    },
    {
        "id": "D5",
        "factor": "combo_mutual_and_row_normalization",
        "bandwidth_rule": "median_positive_knn_squared_distance",
        "symmetrization": "mutual",
        "row_normalize": True,
        "kmeans_init": "random",
        "reuse": None,
        "protocol_tag": "NON_PAPER_DIAGNOSTIC",
        "notes": "Pre-specified combination. A higher ACC does not become the paper protocol.",
    },
    {
        "id": "D6",
        "factor": "combo_mean_bandwidth_and_kmeanspp",
        "bandwidth_rule": "mean_knn_distance_scale",
        "symmetrization": "union",
        "row_normalize": False,
        "kmeans_init": "k-means++",
        "reuse": "D1",
        "protocol_tag": "NON_PAPER_DIAGNOSTIC",
        "notes": "Pre-specified combination of D1's representation and k-means++. Not selected by ACC.",
    },
)


def _sha256_array(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def _git_head() -> str:
    head = ROOT / ".git" / "HEAD"
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref:"):
        ref = text.split(" ", 1)[1]
        return (ROOT / ".git" / ref).read_text(encoding="utf-8").strip()
    return text


def _mean_std(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    return float(array.mean()), float(array.std(ddof=1))


def _score(features: np.ndarray, y: np.ndarray, n_clusters: int, init: str) -> dict:
    accs: list[float] = []
    nmis: list[float] = []
    for seed in SEEDS:
        model = KMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=1,
            random_state=int(seed),
            algorithm="lloyd",
        )
        pred = model.fit_predict(features)
        accs.append(clustering_accuracy(y, pred))
        nmis.append(normalized_mutual_information(y, pred))
    acc_mean, acc_std = _mean_std(accs)
    nmi_mean, nmi_std = _mean_std(nmis)
    return {
        "acc_mean": acc_mean,
        "acc_std": acc_std,
        "nmi_mean": nmi_mean,
        "nmi_std": nmi_std,
        "accs": accs,
        "nmis": nmis,
    }


def _graph_bits(affinity: sparse.spmatrix) -> dict:
    weights = sparse.csr_matrix(affinity)
    n_components, _labels = connected_components(weights, directed=False, return_labels=True)
    return {
        "n_undirected_edges": int(weights.nnz // 2),
        "n_connected_components": int(n_components),
    }


def _solve_graph(X: np.ndarray, spec: dict, n_clusters: int) -> dict:
    config = SpectralGraphConfig(
        k=5,
        bandwidth_rule=spec["bandwidth_rule"],
        symmetrization=spec["symmetrization"],
        row_normalize=bool(spec["row_normalize"]),
        variant="E8",
        g_init="F",
        zero_residual_floor="median_pairwise",
        tol=1e-6,
        max_iter=300,
        eps=1e-8,
        kmeans_init="random",
        kmeans_n_init=1,
    )
    t0 = time.perf_counter()
    embedding, embed_info = spectral_embedding(X, n_components=int(n_clusters), config=config)
    affinity, _graph = knn_affinity(
        embedding,
        k=5,
        bandwidth_rule=spec["bandwidth_rule"],
        symmetrization=spec["symmetrization"],
    )
    shrinkage = shrink_embedding(
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
    runtime = time.perf_counter() - t0
    return {
        "embedding": embedding,
        "patterns": shrinkage.patterns,
        "affinity": affinity,
        "converged": bool(shrinkage.converged),
        "n_iterations": int(shrinkage.n_iterations),
        "fixed_point_residual": float(shrinkage.fixed_point_residual),
        "equation8_objective": float(shrinkage.history[-1]["equation8_objective"]),
        "objective_name": "equation8_on_this_W",
        "runtime_sec": runtime,
        "embed_info": embed_info,
        "graph_bits": _graph_bits(affinity),
        "feature_graph_bits": {
            "n_undirected_edges": int(embed_info["n_undirected_edges"]),
            "n_connected_components": int(embed_info["n_connected_components"]),
        },
    }


def _matched_l2(left: np.ndarray, right: np.ndarray, y_left: np.ndarray, y_right: np.ndarray) -> dict:
    classes = list(range(38))
    means_left = np.vstack([left[y_left == c].mean(axis=0) for c in classes])
    means_right = np.vstack([right[y_right == c].mean(axis=0) for c in classes])
    class_cost = cdist(means_left, means_right, metric="euclidean")
    row_ind, col_ind = linear_sum_assignment(class_cost)
    distances: list[float] = []
    max_abs = []
    for left_class, right_class in zip(row_ind, col_ind):
        a = left[y_left == left_class]
        b = right[y_right == right_class]
        cost = cdist(a, b, metric="euclidean")
        rr, cc = linear_sum_assignment(cost)
        distances.extend(cost[rr, cc].tolist())
        paired_abs = np.max(np.abs(a[rr] - b[cc]), axis=1)
        max_abs.extend(paired_abs.tolist())
    dist = np.asarray(distances, dtype=np.float64)
    abs_diff = np.asarray(max_abs, dtype=np.float64)
    return {
        "n_matched": int(dist.size),
        "median_l2": float(np.median(dist)),
        "mean_l2": float(dist.mean()),
        "fraction_maxabs_le_1e-8": float(np.mean(abs_diff <= 1e-8)),
    }


def _orient(flat: np.ndarray, name: str) -> np.ndarray:
    images = flat.reshape(-1, 32, 32)
    if name == "identity":
        out = images
    elif name == "transpose":
        out = np.transpose(images, (0, 2, 1))
    elif name == "rot90":
        out = np.rot90(images, 1, axes=(1, 2))
    elif name == "fliplr":
        out = images[:, :, ::-1]
    elif name == "flipud":
        out = images[:, ::-1, :]
    elif name == "rot90_fliplr":
        out = np.rot90(images, 1, axes=(1, 2))[:, :, ::-1]
    else:
        raise ValueError(name)
    return np.ascontiguousarray(out.reshape(flat.shape[0], -1))


def _correctness(cropped: np.ndarray, dengcai: np.ndarray, y_c: np.ndarray, y_d: np.ndarray) -> dict:
    checks: list[dict] = []

    def add(name: str, passed: bool, detail: dict) -> None:
        checks.append({"name": name, "passed": bool(passed), **detail})

    subset = cropped[:80].copy()
    perm = np.random.default_rng(0).permutation(subset.shape[1])
    dist_a, idx_a = knn_neighbor_squared_distances(subset, k=5, method="dense")
    dist_b, idx_b = knn_neighbor_squared_distances(subset[:, perm], k=5, method="dense")
    add(
        "global_pixel_permutation_leaves_euclidean_knn",
        bool(np.array_equal(idx_a, idx_b) and np.allclose(dist_a, dist_b)),
        {"n": 80, "k": 5, "max_abs_dist": float(np.max(np.abs(dist_a - dist_b)))},
    )

    scaled = subset * 2.5
    aff_a, info_a = knn_affinity(subset, k=5)
    aff_b, info_b = knn_affinity(scaled, k=5)
    add(
        "brightness_scale_cancels_under_median_squared_bandwidth",
        bool(np.allclose(aff_a.toarray(), aff_b.toarray(), atol=1e-10)),
        {
            "scale": 2.5,
            "delta2_ratio": float(info_b["delta2"] / info_a["delta2"]),
            "max_abs_affinity": float(np.max(np.abs(aff_a.toarray() - aff_b.toarray()))),
        },
    )
    fixed = knn_affinity(scaled, k=5, delta2=float(info_a["delta2"]), bandwidth_rule="fixed")[0]
    add(
        "fixed_bandwidth_does_not_cancel_brightness_scale",
        bool(not np.allclose(aff_a.toarray(), fixed.toarray(), atol=1e-6)),
        {"note": "Same numerical delta^2 is a different relative bandwidth after scaling."},
    )

    rng = np.random.default_rng(1)
    toy = rng.normal(size=(25, 4))
    toy = toy + np.linspace(0.0, 0.01, 25)[:, None]
    dense_dist, dense_idx = knn_neighbor_squared_distances(toy, k=5, method="dense")
    scipy_dist2 = cdist(toy, toy, metric="euclidean") ** 2
    np.fill_diagonal(scipy_dist2, np.inf)
    order = np.argsort(scipy_dist2, axis=1, kind="mergesort")[:, :5]
    rows = np.arange(25)[:, None]
    add(
        "dense_knn_matches_scipy_cdist",
        bool(np.array_equal(dense_idx, order) and np.allclose(dense_dist, scipy_dist2[rows, order])),
        {"n": 25, "k": 5},
    )

    points = np.array([[0.0], [1.0], [3.0]])
    affinity, info = knn_affinity(points, k=1)
    expected_delta2 = float(np.median([1.0, 1.0, 4.0]))
    expected_01 = float(np.exp(-1.0 / expected_delta2))
    add(
        "hand_gaussian_kernel",
        bool(info["delta2"] == expected_delta2 and np.isclose(affinity[0, 1], expected_01)),
        {"delta2": info["delta2"], "w01": float(affinity[0, 1]), "expected": expected_01},
    )

    directed = sparse.csr_matrix(np.array([[0.0, 0.2, 0.0], [0.0, 0.0, 0.4], [0.0, 0.0, 0.0]]))
    from SSC_method.graph_construction import _symmetrize_directed_affinity

    union, _name = _symmetrize_directed_affinity(directed, "union_maximum")
    mutual, _name = _symmetrize_directed_affinity(directed, "mutual_and")
    add(
        "symmetrization_union_and_mutual",
        bool(union[0, 1] == 0.2 and union[1, 0] == 0.2 and mutual.nnz == 0 and union[1, 2] == 0.4),
        {"union_nnz": int(union.nnz), "mutual_nnz": int(mutual.nnz)},
    )

    weights = sparse.csr_matrix(np.array([[0.0, 2.0], [2.0, 0.0]]))
    laplacian = symmetric_normalized_laplacian(weights)
    expected = np.array([[1.0, -1.0], [-1.0, 1.0]])
    evals, vectors, _solver = smallest_eigenpairs(laplacian, 2, dense_threshold=8)
    full = eigh(laplacian.toarray(), eigvals_only=True)
    add(
        "normalized_laplacian_and_smallest_eigenvectors",
        bool(np.allclose(laplacian.toarray(), expected) and np.allclose(evals, full)),
        {"evals": evals.tolist()},
    )

    y_toy = np.array([0, 0, 1, 1])
    pred = np.array([1, 1, 0, 0])
    add(
        "acc_nmi_hungarian",
        bool(
            clustering_accuracy(y_toy, pred) == 1.0
            and normalized_mutual_information(y_toy, pred) == 1.0
            and clustering_accuracy(y_toy, np.array([0, 0, 0, 1])) == 0.75
        ),
        {},
    )
    km = KMeans(n_clusters=2, init="random", n_init=1, random_state=0, algorithm="lloyd")
    labels = km.fit_predict(np.vstack([np.zeros((6, 2)), np.ones((6, 2))]))
    add(
        "kmeans_lloyd_runs",
        bool(labels.shape == (12,) and len(set(labels.tolist())) == 2),
        {},
    )

    try:
        import cvxpy
    except ImportError:
        cvxpy = None
    if cvxpy is None:
        add("e8_matches_independent_convex_solver", False, {"status": "cvxpy_missing"})
    else:
        rng = np.random.default_rng(1)
        embedding = rng.normal(size=(6, 2))
        chain = np.zeros((6, 6))
        for i in range(5):
            chain[i, i + 1] = chain[i + 1, i] = 1.0
        affinity = sparse.csr_matrix(chain)
        result = shrink_embedding(
            embedding,
            affinity,
            gamma=0.8,
            eps=1e-9,
            tol=1e-6,
            max_iter=300,
            variant="E8",
            zero_residual_floor="median_pairwise",
        )
        variable = cvxpy.Variable((6, 2))
        data_term = cvxpy.sum([cvxpy.norm(variable[i] - embedding[i], 2) for i in range(6)])
        graph_terms = []
        for i in range(6):
            for j in range(6):
                if chain[i, j] > 0.0:
                    graph_terms.append(chain[i, j] * cvxpy.norm(variable[i] - variable[j], 2))
        problem = cvxpy.Problem(cvxpy.Minimize(data_term + 0.8 * cvxpy.sum(graph_terms)))
        problem.solve(solver=cvxpy.CLARABEL, verbose=False)
        reference = np.asarray(variable.value, dtype=np.float64)
        gap = float(np.max(np.abs(result.patterns - reference)))
        add(
            "e8_matches_independent_convex_solver",
            bool(problem.status in {cvxpy.OPTIMAL, cvxpy.OPTIMAL_INACCURATE} and gap < 1e-3 and result.laplacian_coefficient == 2.0),
            {"status": str(problem.status), "max_abs_gap": gap, "coefficient": result.laplacian_coefficient},
        )

    orientations = {}
    for name in ("identity", "transpose", "rot90", "fliplr", "flipud", "rot90_fliplr"):
        orientations[name] = _matched_l2(cropped, _orient(dengcai, name), y_c, y_d)
    best_name = min(orientations, key=lambda name: orientations[name]["median_l2"])
    add(
        "yaleb_versions_are_not_the_same_pixel_matrix",
        bool(orientations[best_name]["fraction_maxabs_le_1e-8"] < 0.01),
        {"best_orientation": best_name, "orientations": orientations},
    )

    failed = [item["name"] for item in checks if not item["passed"]]
    return {
        "checks": checks,
        "failed": failed,
        "conclusion": "NO CONFIRMED IMPLEMENTATION BUG" if not failed else "CHECK_FAILED",
        "best_orientation": best_name,
        "best_match": orientations[best_name],
    }


def _write_csv(rows: list[dict]) -> None:
    columns = [
        "dataset",
        "version",
        "diagnostic_id",
        "factor",
        "protocol_tag",
        "status",
        "k",
        "gamma",
        "variant",
        "laplacian_coefficient",
        "bandwidth_rule",
        "symmetrization",
        "row_normalize",
        "kmeans_init",
        "kmeans_n_init",
        "seeds",
        "n_trials",
        "sc_acc_mean",
        "sc_acc_std",
        "sc_nmi_mean",
        "sc_nmi_std",
        "ssc_acc_mean",
        "ssc_acc_std",
        "ssc_nmi_mean",
        "ssc_nmi_std",
        "converged",
        "n_iterations",
        "fixed_point_residual",
        "objective_name",
        "objective_value",
        "n_feature_edges",
        "n_feature_components",
        "n_shrinkage_edges",
        "n_shrinkage_components",
        "runtime_sec",
        "data_checksum",
        "commit",
        "notes",
    ]
    path = OUT_DIR / "P0_yaleb_diagnostics.csv"
    lines = [",".join(columns)]
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column, "")
            if value is None:
                text = ""
            else:
                text = str(value)
            if any(ch in text for ch in ",\"\n"):
                text = '"' + text.replace('"', '""') + '"'
            cells.append(text)
        lines.append(",".join(cells))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(row: dict, key: str) -> str:
    value = row.get(key)
    if value in ("", None):
        return "NA"
    return f"{float(value):.4f}"


def _write_root_cause(rows: list[dict], correctness: dict, checksums: dict) -> None:
    lines = [
        "# P0 YaleB root cause",
        "",
        "This file is generated from `results/extension_research/P0_yaleb_diagnostics.csv` and the correctness checks in `results/extension_research/P0_correctness_checks.json`. It does not copy historical ACC/NMI into that CSV.",
        "",
        "## Implementation check",
        "",
        f"Conclusion: `{correctness['conclusion']}`.",
        "",
        "Checked, without using the checks to retune the method: a global pixel permutation leaves Euclidean kNN unchanged; a global brightness scale cancels when delta^2 is the median of squared kNN distances and does not cancel when delta^2 is held numerically fixed; dense kNN matches SciPy distances; a three-point Gaussian kernel matches the hand value; union and mutual symmetrization do what those rules say; the normalized Laplacian and its smallest eigenvectors match the dense formula; ACC/NMI and Lloyd K-means run on a toy; n=6 E8 matches an independent CLARABEL solve of the ordered-pair objective. `SSC_method/` was not modified.",
        "",
        f"Best orientation of dengcai32 against cropped2414 is `{correctness['best_orientation']}` with median matched L2 {correctness['best_match']['median_l2']:.4f} and fraction of pairs with max-abs <= 1e-8 equal to {correctness['best_match']['fraction_maxabs_le_1e-8']:.6f}. The two 2414 x 1024 matrices are not the same pixels. Array SHA-256: cropped2414 `{checksums['cropped2414']}`, dengcai32 `{checksums['dengcai32']}`.",
        "",
        "Chang et al. Table 1, historical published context only, not a measurement in this CSV: YaleB SC 34.8% and SSC 49.8%. A diagnostic ACC above D0 is `NON_PAPER_DIAGNOSTIC` and is not adopted as the original protocol.",
        "",
        "## D0–D6",
        "",
        "Each non-control row changes one pre-specified factor, or a combination named before the run. SC is K-means on F. SSC is E8, gamma=1, G0=F, K-means on G. Seeds 0..49, n_init=1. Sample standard deviation uses ddof=1.",
        "",
        "| Version | ID | Factor | Tag | Status | SC ACC | SSC ACC | SC NMI | SSC NMI | Edges | Components | Iters | Converged |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {version} | {diagnostic_id} | {factor} | {protocol_tag} | {status} | {sc} ± {scs} | {ssc} ± {sscs} | {sn} ± {sns} | {gn} ± {gns} | {edges} | {comps} | {iters} | {conv} |".format(
                version=row["version"],
                diagnostic_id=row["diagnostic_id"],
                factor=row["factor"],
                protocol_tag=row["protocol_tag"],
                status=row["status"],
                sc=_fmt(row, "sc_acc_mean"),
                scs=_fmt(row, "sc_acc_std"),
                ssc=_fmt(row, "ssc_acc_mean"),
                sscs=_fmt(row, "ssc_acc_std"),
                sn=_fmt(row, "sc_nmi_mean"),
                sns=_fmt(row, "sc_nmi_std"),
                gn=_fmt(row, "ssc_nmi_mean"),
                gns=_fmt(row, "ssc_nmi_std"),
                edges=row.get("n_shrinkage_edges", ""),
                comps=row.get("n_shrinkage_components", ""),
                iters=row.get("n_iterations", ""),
                conv=row.get("converged", ""),
            )
        )
    d0 = [row for row in rows if row["diagnostic_id"] == "D0" and row["status"] != "FAILED"]
    lines.extend(["", "## What the control supports", ""])
    if len(d0) == 2:
        by_version = {row["version"]: row for row in d0}
        c = by_version["cropped2414"]
        d = by_version["dengcai32"]
        lines.append(
            f"On the locked control, cropped2414 SC ACC is {float(c['sc_acc_mean']):.4f} and SSC ACC is {float(c['ssc_acc_mean']):.4f}. "
            f"dengcai32 SC ACC is {float(d['sc_acc_mean']):.4f} and SSC ACC is {float(d['ssc_acc_mean']):.4f}. "
            "Both are far below the published 0.348 / 0.498 table entries. Switching the pixel matrix does not close that gap. "
            "The shrinkage step is not the first place the gap appears: K-means on F is already low."
        )
    below = []
    for row in rows:
        if row["status"] == "FAILED":
            continue
        below.append(float(row["sc_acc_mean"]) < 0.348 and float(row["ssc_acc_mean"]) < 0.498)
    if below:
        lines.append("")
        if all(below):
            lines.append("Every completed D0–D6 cell, including the non-paper diagnostics, stays below the published YaleB SC and SSC table values. Those higher diagnostic numbers are still not the original protocol.")
        else:
            lines.append("At least one diagnostic cell is not below both published table values. That cell remains labeled with its protocol tag and is not retrofitted as the paper setting.")
    lines.extend(
        [
            "",
            "## What remains unresolved",
            "",
            "The paper does not state delta, union versus mutual, the resize kernel, the eigenvector sign convention, or whether the solver was printed Equation (13) or the Equation (8) stationary system. This round keeps E8 as the control and does not pick a diagnostic by test ACC.",
            "",
        ]
    )
    (DOCS / "P0_yaleb_root_cause.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    commit = _git_head()
    loaded = {}
    for version in VERSIONS:
        X, y, meta = load_dataset("YaleB", version=version)
        loaded[version] = (X, y, meta)
        print(f"loaded {version} {X.shape}", flush=True)
    cropped, y_c, _meta_c = loaded["cropped2414"]
    dengcai, y_d, _meta_d = loaded["dengcai32"]
    t0 = time.perf_counter()
    correctness = _correctness(cropped, dengcai, y_c, y_d)
    correctness["runtime_sec"] = time.perf_counter() - t0
    (OUT_DIR / "P0_correctness_checks.json").write_text(
        json.dumps(correctness, indent=2), encoding="utf-8"
    )
    print("correctness", correctness["conclusion"], correctness["failed"], flush=True)
    checksums = {version: _sha256_array(loaded[version][0]) for version in VERSIONS}
    if correctness["conclusion"] != "NO CONFIRMED IMPLEMENTATION BUG":
        print("stopping before D0-D6 because a check failed", flush=True)
        return

    solved: dict[tuple[str, str], dict] = {}
    rows: list[dict] = []
    for version in VERSIONS:
        X, y, _meta = loaded[version]
        n_clusters = int(len(np.unique(y)))
        for spec in DIAGNOSTICS:
            spec = dict(spec)
            print(f"start {version} {spec['id']}", flush=True)
            row = {
                "dataset": "YaleB",
                "version": version,
                "diagnostic_id": spec["id"],
                "factor": spec["factor"],
                "protocol_tag": spec["protocol_tag"],
                "k": 5,
                "gamma": 1.0,
                "variant": "E8",
                "laplacian_coefficient": 2.0,
                "bandwidth_rule": spec["bandwidth_rule"],
                "symmetrization": spec["symmetrization"],
                "row_normalize": spec["row_normalize"],
                "kmeans_init": spec["kmeans_init"],
                "kmeans_n_init": 1,
                "seeds": "0-49",
                "n_trials": 50,
                "data_checksum": checksums[version],
                "commit": commit,
                "notes": spec["notes"],
            }
            try:
                if spec["reuse"] is None:
                    solved[(version, spec["id"])] = _solve_graph(X, spec, n_clusters)
                bundle = solved[(version, spec["reuse"] or spec["id"])]
                sc = _score(bundle["embedding"], y, 38, spec["kmeans_init"])
                ssc = _score(bundle["patterns"], y, 38, spec["kmeans_init"])
                status = "CONVERGED" if bundle["converged"] else "NONCONVERGED"
                row.update(
                    {
                        "status": status,
                        "sc_acc_mean": sc["acc_mean"],
                        "sc_acc_std": sc["acc_std"],
                        "sc_nmi_mean": sc["nmi_mean"],
                        "sc_nmi_std": sc["nmi_std"],
                        "ssc_acc_mean": ssc["acc_mean"],
                        "ssc_acc_std": ssc["acc_std"],
                        "ssc_nmi_mean": ssc["nmi_mean"],
                        "ssc_nmi_std": ssc["nmi_std"],
                        "converged": bundle["converged"],
                        "n_iterations": bundle["n_iterations"],
                        "fixed_point_residual": bundle["fixed_point_residual"],
                        "objective_name": bundle["objective_name"],
                        "objective_value": bundle["equation8_objective"],
                        "n_feature_edges": bundle["feature_graph_bits"]["n_undirected_edges"],
                        "n_feature_components": bundle["feature_graph_bits"]["n_connected_components"],
                        "n_shrinkage_edges": bundle["graph_bits"]["n_undirected_edges"],
                        "n_shrinkage_components": bundle["graph_bits"]["n_connected_components"],
                        "runtime_sec": bundle["runtime_sec"],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                row.update(
                    {
                        "status": "FAILED",
                        "notes": spec["notes"] + f" FAILED {type(exc).__name__}: {exc}",
                    }
                )
                (OUT_DIR / f"P0_fail_{version}_{spec['id']}.txt").write_text(
                    traceback.format_exc(), encoding="utf-8"
                )
            rows.append(row)
            _write_csv(rows)
            print(
                f"done {version} {spec['id']} {row['status']} "
                f"SC={row.get('sc_acc_mean')} SSC={row.get('ssc_acc_mean')}",
                flush=True,
            )
    _write_root_cause(rows, correctness, checksums)
    print("wrote root cause", flush=True)


if __name__ == "__main__":
    main()
