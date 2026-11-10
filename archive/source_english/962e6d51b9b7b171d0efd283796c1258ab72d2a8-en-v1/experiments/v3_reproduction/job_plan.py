"""72 historical cells. Extra versions are not extra cells."""

from __future__ import annotations

from typing import Any

from experiments.v3_reproduction.protocol_registry import (
    HISTORICAL_BENCHMARKS,
    HISTORICAL_METHODS,
)


def historical_cells(dataset_records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    by_benchmark: dict[str, list[dict[str, Any]]] = {}
    for record in dataset_records or []:
        by_benchmark.setdefault(record["historical_benchmark"], []).append(record)
    cells = []
    for benchmark in HISTORICAL_BENCHMARKS:
        records = by_benchmark.get(benchmark, [])
        historical_hits = [item for item in records if item.get("counts_as_historical")]
        for method in HISTORICAL_METHODS:
            cells.append(
                _cell(benchmark, method, historical_hits, records)
            )
    if len(cells) != 72:
        raise RuntimeError(f"expected 72 historical cells, found {len(cells)}")
    return cells


def _cell(
    benchmark: str,
    method: str,
    historical_hits: list[dict[str, Any]],
    all_records: list[dict[str, Any]],
) -> dict[str, Any]:
    available = [item for item in historical_hits if item.get("available")]
    supplemental = [
        item["dataset_id"]
        for item in all_records
        if item.get("available") and not item.get("counts_as_historical")
    ]
    if method == "lda_sc":
        blocker = "BLOCKED_METHOD"
        reason = (
            "Chang et al. name LDA-SC and cite no algorithm. "
            "Ding and Li define LDA-Kmeans only. "
            "An alternating spectral substitute is not reported under this name."
        )
        resource = "PAPER_NAME_ONLY"
    elif benchmark == "AR":
        blocker = "BLOCKED_DATA"
        reason = (
            "The on-disk archive has 100 identities. "
            "It is not the 840-image, 120-identity AR subset, and no subset was manufactured."
        )
        resource = "BLOCKED_DATA"
    elif benchmark == "MSRA50":
        blocker = "BLOCKED_DATA"
        reason = "No 1799 x 12 MSRA50 matrix was found. Other MSRA collections were not substituted."
        resource = "BLOCKED_DATA"
    elif benchmark == "UMIST":
        blocker = "BLOCKED_DATA"
        reason = (
            "The historical target is 564 images. "
            "The 575-image cropped release is a separate version and is not relabeled as 564."
        )
        resource = "BLOCKED_DATA"
    elif benchmark == "BinAlpha":
        blocker = "SUBSET_UNVERIFIED"
        reason = (
            "Binary Alphadigits is the parent set. "
            "letters26x30 with seed 0 is a reconstructable candidate, not Chang et al.'s subset."
        )
        resource = "SUBSET_UNVERIFIED"
    elif not available and not historical_hits:
        blocker = "BLOCKED_DATA"
        reason = "No historical matrix was loaded."
        resource = "BLOCKED_DATA"
    else:
        blocker = None
        reason = None
        resource = "DATA_AVAILABLE"
    executable = blocker is None
    return {
        "benchmark": benchmark,
        "method": method,
        "cell_id": f"{benchmark}__{method}",
        "resource_status": resource,
        "blocker": blocker,
        "reason": reason,
        "executable": executable,
        "dataset_ids": [item["dataset_id"] for item in available],
        "supplemental_dataset_ids": supplemental,
        "execution_status": "PLANNED" if executable else blocker,
        "algorithm_fidelity": _fidelity(method),
        "counts_toward_72": True,
    }


def _fidelity(method: str) -> str:
    if method == "lda_sc":
        return "BLOCKED_METHOD"
    if method == "spls":
        return "PAPER_BASED_REIMPLEMENTATION"
    if method in {"ssc", "sc", "pca_sc"}:
        return "PAPER_BASED_REIMPLEMENTATION"
    if method == "llc":
        return "PAPER_BASED_REIMPLEMENTATION"
    if method == "lda_kmeans":
        return "PAPER_BASED_REIMPLEMENTATION"
    return "STANDARD_BASELINE"
