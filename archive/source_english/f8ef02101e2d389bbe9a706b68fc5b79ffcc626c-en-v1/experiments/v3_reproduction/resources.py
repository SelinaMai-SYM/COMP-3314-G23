"""Resource probe and round-2 recovery. Raw archives stay outside git."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from experiments.v3_reproduction.dataset_registry import load_spec
from experiments.v3_reproduction.resource_recovery import recover
from experiments.v3_reproduction.job_plan import historical_cells
from experiments.v3_reproduction.protocol_registry import load_campaign
from experiments.v3_reproduction.provenance import json_ready


ATTEMPTS = (
    {
        "asset": "SSC_AAAI_PDF",
        "url": "https://ojs.aaai.org/index.php/AAAI/article/download/9606/9465",
    },
    {
        "asset": "BinaryAlphadigits_live",
        "url": "https://cs.nyu.edu/home/people/in_memoriam/roweis/data/binaryalphadigs.mat",
    },
    {
        "asset": "BinaryAlphadigits_page",
        "url": "https://cs.nyu.edu/home/people/in_memoriam/roweis/data.html",
    },
    {
        "asset": "DengCai_FaceData",
        "url": "http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html",
    },
    {
        "asset": "SLPS_DOI",
        "url": "https://doi.org/10.1016/j.ipm.2013.01.004",
    },
    {
        "asset": "ATT_ORL_zip",
        "url": "https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip",
    },
)


def _curl(url: str) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).isoformat()
    command = [
        "curl",
        "-I",
        "-L",
        "--max-time",
        "20",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code} %{content_type} %{size_download}",
        url,
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError as exc:
        return {
            "url": url,
            "timestamp_utc": stamp,
            "http_status": None,
            "error": str(exc),
        }
    text = (completed.stdout or "").strip()
    parts = text.split()
    status = parts[0] if parts else None
    return {
        "url": url,
        "timestamp_utc": stamp,
        "http_status": status,
        "curl_exit": completed.returncode,
        "content_type": parts[1] if len(parts) > 1 else None,
        "stderr_tail": (completed.stderr or "")[-400:],
    }


def _file_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            size += len(chunk)
            digest.update(chunk)
    return {
        "path": str(path),
        "exists": True,
        "bytes": size,
        "sha256": digest.hexdigest(),
    }


def probe(config_path: str | Path) -> dict[str, Any]:
    campaign = load_campaign(config_path)
    data_root = Path(campaign["data_root"])
    records = []
    for spec in campaign["_datasets"]["specs"]:
        loaded = load_spec(data_root, spec)
        loaded.pop("X", None)
        loaded.pop("y", None)
        records.append(json_ready(loaded))
    attempts = []
    for item in ATTEMPTS:
        outcome = _curl(item["url"])
        outcome["asset"] = item["asset"]
        attempts.append(outcome)
    slps_pdf = Path(campaign.get("slps_pdf", ""))
    pdf_record = _file_record(slps_pdf) if campaign.get("slps_pdf") else {"exists": False}
    cells = historical_cells(records)
    summary = {
        "data_root": str(data_root),
        "n_historical_cells": len(cells),
        "n_executable_cells": sum(1 for cell in cells if cell["executable"]),
        "datasets": records,
        "acquisition_attempts": attempts,
        "slps_pdf": pdf_record,
        "cells": cells,
    }
    out_dir = Path(campaign["workspace"]) / "docs" / "v3"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "resource_manifest.csv"
    with manifest.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset_id",
                "historical_benchmark",
                "available",
                "blocker",
                "n_samples",
                "n_features",
                "n_classes",
                "version",
                "counts_as_historical",
                "reason",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "dataset_id": record.get("dataset_id"),
                    "historical_benchmark": record.get("historical_benchmark"),
                    "available": record.get("available"),
                    "blocker": record.get("blocker"),
                    "n_samples": record.get("n_samples"),
                    "n_features": record.get("n_features"),
                    "n_classes": record.get("n_classes"),
                    "version": record.get("version"),
                    "counts_as_historical": record.get("counts_as_historical"),
                    "reason": record.get("reason"),
                }
            )
    gaps = out_dir / "resource_gaps.md"
    lines = [
        "# v3 resource gaps",
        "",
        "Raw images stay outside git. This file records availability, not a claim that a loaded matrix is the author's file.",
        "",
    ]
    for record in records:
        state = "AVAILABLE" if record.get("available") else record.get("blocker")
        lines.append(
            f"- `{record.get('dataset_id')}` ({record.get('historical_benchmark')}): {state}. {record.get('reason') or ''}"
        )
    lines.extend(["", "## Acquisition attempts", ""])
    for attempt in attempts:
        lines.append(
            f"- {attempt['asset']}: HTTP {attempt.get('http_status')} `{attempt['url']}`"
        )
    lines.extend(
        [
            "",
            "## Still missing for a historical cell",
            "",
            "- AR 840/120. The 100-identity zip is not that subset.",
            "- UMIST 564. The 575-image release keeps its own version id.",
            "- BinAlpha author's 26 by 30 draw. Seed 0 is only a candidate.",
            "- MSRA50 1799/12. No file was substituted.",
            "- LDA-SC has a name in Chang et al. and no algorithm.",
            "",
        ]
    )
    gaps.write_text("\n".join(lines))
    (out_dir / "resource_probe.json").write_text(json.dumps(json_ready(summary), indent=2))
    return summary
