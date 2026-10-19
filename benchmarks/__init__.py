"""Benchmark data, metrics, and the original-paper protocol.

Canonical loading:

    from benchmarks import DatasetUnavailable, load_dataset
    from benchmarks.orl import load_dataset as load_orl

``load_dataset(name)`` routes to the per-dataset package. Unavailable sets
raise ``DatasetUnavailable`` and do not return arrays.
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import DatasetUnavailable, as_float_matrix, as_int_labels

_ALIASES = {
    "ar": "AR",
    "jaffe": "JAFFE",
    "orl": "ORL",
    "olivetti": "ORL",
    "umist": "UMIST",
    "sheffield": "UMIST",
    "binalpha": "BinAlpha",
    "bin_alpha": "BinAlpha",
    "msra50": "MSRA50",
    "msra": "MSRA50",
    "yaleb": "YaleB",
    "yale_b": "YaleB",
    "extendedyaleb": "YaleB",
    "usps": "USPS",
}

_PACKAGES = {
    "AR": "benchmarks.ar",
    "JAFFE": "benchmarks.jaffe",
    "ORL": "benchmarks.orl",
    "UMIST": "benchmarks.umist",
    "BinAlpha": "benchmarks.binalpha",
    "MSRA50": "benchmarks.msra50",
    "YaleB": "benchmarks.yaleb",
    "USPS": "benchmarks.usps",
}


def load_dataset(name: str, root: Path | None = None):
    """Return ``X`` of shape ``(n, d)``, integer ``y``, and a metadata dict.

    ``root`` overrides that dataset package's ``data/`` directory.
    """
    key = _ALIASES.get(name.strip().lower())
    if key is None:
        known = ", ".join(sorted(set(_ALIASES.values())))
        raise KeyError(f"unknown dataset {name!r}; known datasets: {known}")
    module_name = _PACKAGES[key]
    module = __import__(module_name, fromlist=["load_dataset"])
    return module.load_dataset(root)


__all__ = [
    "DatasetUnavailable",
    "as_float_matrix",
    "as_int_labels",
    "load_dataset",
]
