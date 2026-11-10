"""AR Face Database loader.

A third-party Zenodo zip was saved and checksum-verified. It is **not**
the official Martinez–Benavente distribution. The paper 840/120 subset
was not recovered, so the default name stays unavailable.
"""

from __future__ import annotations

from pathlib import Path

from benchmarks.exceptions import DatasetUnavailable

_SHA256 = "32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438"
_MD5 = "bb97bd9237680744c0c7268624696263"
_ARCHIVE = "ARDB_Full.zip"

_UNAVAILABLE = (
    "Chang et al. name AR as 840 faces of 120 people and do not say which "
    "840. Official Martinez distribution was not obtained. "
    "A THIRD-PARTY zip ARDB_Full.zip from Zenodo 19683234 (uploader Manu "
    "shree, not Martinez/OSU) was downloaded on 2026-10-21: 120587997 "
    "bytes, MD5 bb97bd9237680744c0c7268624696263 (matches the published "
    "Zenodo checksum), SHA-256 "
    "32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438. "
    "The zip is PKZIP, not HTML. It contains 100 folders s1-s100 with "
    "120x165 BMP files named 1.bmp..26.bmp, not official M-xx-yy.raw / "
    "F-xx-yy.raw names. No archive document states an 840/120 or 7-image "
    "rule, so that subset was not invented. Status: "
    "SOURCE_RECOVERED_SUBSET_UNVERIFIED. Default load_dataset('AR') does "
    "not claim EXACT. See benchmarks/ar/README.md."
)


def data_dir(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent / "data"


def load_dataset(root: Path | None = None, version: str | None = None):
    archive = data_dir(root) / _ARCHIVE
    if version in ("zenodo_third_party_full", "SOURCE_RECOVERED"):
        raise DatasetUnavailable(
            "AR",
            "version="
            + str(version)
            + " is the third-party Zenodo dump, not the paper 840/120 "
            "set. The zip is on disk at "
            + str(archive)
            + " (SHA-256 "
            + _SHA256
            + ", MD5 "
            + _MD5
            + ") with 100 identities. Status "
            "SOURCE_RECOVERED_SUBSET_UNVERIFIED. Arrays are not returned "
            "under a paper-AR name.",
        )
    del version
    raise DatasetUnavailable("AR", _UNAVAILABLE)
