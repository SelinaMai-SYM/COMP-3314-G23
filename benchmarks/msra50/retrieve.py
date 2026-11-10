"""Retrieve the pinned native EBSA MSRA25 source into an independent data root."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import ssl
import urllib.request
from benchmarks.data_paths import resolve_data_root
from .loader import EBSA_SHA256, EBSA_URL


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    args=parser.parse_args()
    root=resolve_data_root(args.data_root)
    target=root/"msra50/data/EBSA_c72bfbf_MSRA25.mat"
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if hashlib.file_digest(target.open("rb"),"sha256").hexdigest()!=EBSA_SHA256:
            raise ValueError("existing MSRA25 file does not match the pinned source; refusing to overwrite")
        print(target)
        return
    try:
        import certifi
    except ImportError:
        context=ssl.create_default_context()
    else:
        context=ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(EBSA_URL,context=context,timeout=60) as response:
        content=response.read()
    if len(content)!=387675 or hashlib.sha256(content).hexdigest()!=EBSA_SHA256:
        raise ValueError("downloaded MSRA25 length/hash mismatch; no dataset file was written")
    temporary=target.with_suffix(".download")
    temporary.write_bytes(content)
    temporary.replace(target)
    print(target)

if __name__=="__main__":
    main()
