"""AR Face Database loader. No image archive was saved."""

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
        "The AR Face Database is distributed by request with a password and "
        "forbids redistribution. Official Ohio State HTTP returned 503 on "
        "2026-10-21; HTTPS had an untrusted certificate. "
        "Zenodo record 19683234 (ARDB_Full.zip, HTTP 200, 120587997 bytes, "
        "uploader Manu shree, claimed CC-BY-4.0) is a third-party dump, not "
        "the Martinez–Benavente distributor. It was not downloaded and is "
        "not used. The paper 840/120 subset was not invented. "
        "See benchmarks/ar/README.md.",
    )
