"""Redraw the v3 figures by aggregating the raw records again."""

from __future__ import annotations

from experiments.v3_reproduction.aggregate import aggregate


def redraw(config_path: str) -> None:
    aggregate(config_path)
