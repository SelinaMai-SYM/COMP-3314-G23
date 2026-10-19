"""AR Face Database loader. The archive was not obtained."""

from __future__ import annotations

from pathlib import Path

from benchmarks.exceptions import DatasetUnavailable


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None):
    del root, version
    raise DatasetUnavailable(
        "AR",
        "The AR Face Database is distributed by request with a password. "
        "On 2026-10-20 the Ohio State page returned HTTP 503 over HTTP and "
        "an expired TLS certificate over HTTPS. Purdue URLs returned HTTP 404. "
        "No image archive was downloaded and no 840-image subset was invented. "
        "See docs/repair_round1_dataset_recovery.md.",
    )
