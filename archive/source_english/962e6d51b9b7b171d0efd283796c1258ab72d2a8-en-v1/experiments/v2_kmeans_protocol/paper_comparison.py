"""Historical Chang et al. 2015 numbers, kept apart from our measurements."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from experiments.v2_kmeans_protocol.dataset_registry import REPO_ROOT

PAPER_PATH = REPO_ROOT / "configs" / "paper_2015_reference.yaml"


def load_paper(path: Path | None = None) -> dict[str, Any]:
    payload = yaml.safe_load((path or PAPER_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "acc" not in payload or "nmi" not in payload:
        raise ValueError("paper_2015_reference.yaml must contain acc and nmi tables")
    return payload


def paper_stat(table: str, method: str, benchmark: str, path: Path | None = None) -> tuple[float, float]:
    """Return the published mean and SD in percent."""
    paper = load_paper(path)
    try:
        cell = paper[table][method][benchmark]
    except KeyError as exc:
        raise KeyError(f"paper reference missing {table}.{method}.{benchmark}") from exc
    return float(cell["mean"]), float(cell["sd"])


def as_fraction(percent: float) -> float:
    return float(percent) / 100.0


def numeric_gap(our_fraction: float | None, paper_percent: float | None, comparison_class: str) -> float | str:
    """Gap in fraction units, or NOT_COMPARABLE when the cell is not a match."""
    if comparison_class == "NOT_COMPARABLE" or our_fraction is None or paper_percent is None:
        return "NOT_COMPARABLE"
    return float(our_fraction) - as_fraction(paper_percent)


__all__ = ["PAPER_PATH", "as_fraction", "load_paper", "numeric_gap", "paper_stat"]
