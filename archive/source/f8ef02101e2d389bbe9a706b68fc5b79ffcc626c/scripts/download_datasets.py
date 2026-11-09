#!/usr/bin/env python3
"""Download the traceable SSC archives into each dataset package's data/.

Files that are already present and match the recorded SHA-256 are left in
place. AR, UMIST, BinAlpha, and MSRA50 are not fabricated. JAFFE's official
Zenodo URL returned HTTP 403 to curl on 2026-10-20; a browser download of
that same URL succeeded and is recognized by checksum.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"

# SHA-256 values computed from the files saved on 2026-10-20.
DOWNLOADS = [
    (
        BENCHMARKS / "orl" / "data" / "olivettifaces.mat",
        "https://ndownloader.figshare.com/files/5976027",
        "b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794",
    ),
    (
        BENCHMARKS / "usps" / "data" / "usps.bz2",
        "https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.bz2",
        "3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f",
    ),
    (
        BENCHMARKS / "usps" / "data" / "usps.t.bz2",
        "https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.t.bz2",
        "a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e",
    ),
    (
        BENCHMARKS / "yaleb" / "data" / "YaleB_32x32.mat",
        "http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat",
        "3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99",
    ),
    (
        BENCHMARKS / "jaffe" / "data" / "jaffe.zip",
        "https://zenodo.org/records/14974867/files/jaffe.zip?download=1",
        "6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b",
    ),
]

UNAVAILABLE = {
    "AR": "official request/password required; Zenodo 19683234 was not used",
    "UMIST": "564-image file not obtained; extra 1012/575 archives are not that set",
    "BinAlpha": "paper 26x30 identity unverified; Binary Alphadigits is an explicit extra version",
    "MSRA50": "no 1799-image, 12-class archive; other MSRA sets were not substituted",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, dest: Path, expected: str) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(dest.suffix + ".partial")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "COMP3314-SSC-dataset-download/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            status = getattr(response, "status", 200)
            with temporary.open("wb") as handle:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    handle.write(chunk)
    except urllib.error.HTTPError as exc:
        temporary.unlink(missing_ok=True)
        print(f"FAIL {url} HTTP {exc.code}")
        return exc.code
    except Exception as exc:  # noqa: BLE001 - report the real download error
        temporary.unlink(missing_ok=True)
        print(f"FAIL {url} {type(exc).__name__}: {exc}")
        return 1
    temporary.replace(dest)
    digest = sha256(dest)
    relative = dest.relative_to(BENCHMARKS)
    print(f"OK {relative} bytes={dest.stat().st_size} sha256={digest} http={status}")
    if digest != expected:
        print(f"CHECKSUM MISMATCH expected {expected}")
        return 2
    return 0


def main() -> int:
    exit_code = 0
    for dest, url, expected in DOWNLOADS:
        relative = dest.relative_to(BENCHMARKS)
        if dest.is_file():
            digest = sha256(dest)
            if digest == expected:
                print(f"SKIP {relative} sha256 matches")
                continue
            print(f"REPLACE {relative} sha256 {digest} != expected")
        status = fetch(url, dest, expected)
        if status != 0:
            exit_code = status if exit_code == 0 else exit_code
            if dest.name == "jaffe.zip":
                print(
                    "JAFFE note: Zenodo blocked curl/urllib with HTTP 403 on "
                    "2026-10-20. The official record is "
                    "https://zenodo.org/records/14974867. Do not use a reposted copy."
                )
    for name, reason in UNAVAILABLE.items():
        print(f"UNAVAILABLE {name}: {reason}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
