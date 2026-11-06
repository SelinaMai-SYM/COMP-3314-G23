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
            "The SLPS paper defines LdaKm, and Ding and Li define LDA-Kmeans. "
            "Neither document defines LDA-SC. Status METHOD_DEFINITION_UNRESOLVED."
        )
        resource = "PAPER_NAME_ONLY"
    elif benchmark == "AR":
        blocker = "BLOCKED_DATA"
        reason = (
            "No verified 840/120 file. The Zenodo zip has 100 identities. "
            "LZUFE AR.mat is 1680x1024 with 120 identities and 14 images each. "
            "It has no documented 840-image rule, so no subset was taken."
        )
        resource = "BLOCKED_DATA"
    elif benchmark == "MSRA50":
        blocker = "BLOCKED_DATA"
        reason = "BLOCKED_NO_VERIFIED_DATA_URL. No 1799 x 12 file was found. MSRA-B, MSRA10K, TD500, and MSRC were not substituted."
        resource = "BLOCKED_DATA"
    elif benchmark == "UMIST":
        blocker = "BLOCKED_DATA"
        reason = (
            "No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, "
            "which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. "
            "Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. "
            "None of these is the SSC 564-image set."
        )
        resource = "BLOCKED_DATA"
    elif benchmark == "BinAlpha":
        blocker = "SUBSET_UNVERIFIED"
        reason = (
            "The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 "
            "3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. "
            "letters26x30 seed 0 stores every parent index and is not the author's draw."
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
