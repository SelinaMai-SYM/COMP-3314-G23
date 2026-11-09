"""Frozen v3 protocol constants loaded from configs/v3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

HISTORICAL_METHODS = (
    "kmeans",
    "sc",
    "pca_kmeans",
    "pca_sc",
    "lda_kmeans",
    "lda_sc",
    "llc",
    "spls",
    "ssc",
)
HISTORICAL_BENCHMARKS = (
    "AR",
    "JAFFE",
    "ORL",
    "UMIST",
    "BinAlpha",
    "MSRA50",
    "YaleB",
    "USPS",
)

RANDOM = "RANDOM"
GREEDY = "SKLEARN_GREEDY_KMEANSPP"
VANILLA = "VANILLA_KMEANSPP"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a mapping")
    return data


def load_campaign(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    path = path.expanduser().resolve()
    campaign = load_yaml(path)
    repo = Path(__file__).resolve().parents[2]
    raw_workspace = campaign.get("workspace")
    campaign["workspace"] = str(repo if not raw_workspace else (repo / raw_workspace).resolve())
    root = path.parent
    campaign["_path"] = str(path)
    campaign["_dir"] = str(root)
    for key in ("datasets", "methods", "protocols", "paper_reference", "yaleb_diagnostics"):
        pointer = campaign.get(key)
        if pointer:
            campaign[f"_{key}"] = load_yaml(root / pointer if not str(pointer).startswith("/") else Path(pointer))
    return campaign


def gamma_grid(campaign: dict[str, Any]) -> list[float]:
    return [float(value) for value in campaign["_protocols"]["ssc_gamma"]]


def pca_dimensions(campaign: dict[str, Any]) -> list[int]:
    return [int(value) for value in campaign["_protocols"]["pca_dimensions"]]


def workspace(campaign: dict[str, Any]) -> Path:
    return Path(campaign["workspace"])
