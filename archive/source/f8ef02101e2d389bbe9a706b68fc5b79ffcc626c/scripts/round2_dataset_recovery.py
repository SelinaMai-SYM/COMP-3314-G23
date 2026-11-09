#!/usr/bin/env python3
"""Round 2 dataset recovery: probe candidate URLs, fetch Binary Alphadigits.

Does not overwrite existing archives. Does not download ARDB_Full.zip after
the Zenodo record was identified as a third-party dump. Does not treat TUNA
PyPI as a dataset source. Does not invent checksums.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "COMP3314-SSC-dataset-recovery/2.0"
LOG = ROOT / "docs" / "round2_http_log.json"

BINALPHA_DEST = ROOT / "benchmarks" / "binalpha" / "data" / "binaryalphadigs.mat"
BINALPHA_URLS = [
    "https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat",
    "http://www.cs.nyu.edu/~roweis/data/binaryalphadigs.mat",
    "https://web.archive.org/web/20240616024002id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat",
    "https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat",
]

PROBE_ONLY = [
    "https://cs.nyu.edu/~roweis/data.html",
    "https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html",
    "http://www.cad.zju.edu.cn/home/dengcai/Data/data.html",
    "http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html",
    "http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat",
    "https://zenodo.org/records/19683234",
    "https://zenodo.org/api/records/19683234",
    "https://zenodo.org/records/19683234/files/ARDB_Full.zip?download=1",
    "https://zenodo.org/api/records/19683234/files/ARDB_Full.zip/content",
    "http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html",
    "https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html",
    "https://engineering.purdue.edu/~aleix/ARdatabase.html",
    "https://engineering.purdue.edu/~aleix/aleix_face_DB.html",
    "https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip",
    "https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html",
    "https://zenodo.org/records/14974867",
    "https://zenodo.org/records/14974867/files/jaffe.zip?download=1",
    "https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.bz2",
    "https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.t.bz2",
    "https://ndownloader.figshare.com/files/5976027",
    "http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip",
    "https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip",
    "https://lear.inrialpes.fr/people/triggs/events/iccv03/cdrom/iccv03/0385_he.pdf",
    "https://people.engr.tamu.edu/rgutierrez/web_courses/cpsc689_s07/he2005laplacianfaces.pdf",
    "https://people.engr.tamu.edu/rgutier/web_courses/cpsc689_s07/he2005laplacianfaces.pdf",
    "https://arxiv.org/abs/1411.6241",
    "https://arxiv.org/pdf/1411.6241.pdf",
    "http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz",
    "https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz",
    "http://images.ee.umist.ac.uk/danny/database.html",
    "https://www.sheffield.ac.uk/eee/research/iel/research/face",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def curl_head(url: str) -> dict:
    command = [
        "curl",
        "-sI",
        "-L",
        "-A",
        UA,
        "--max-time",
        "45",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code}\t%{url_effective}\t%{content_type}\t%{size_download}\t%{ssl_verify_result}",
        url,
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return {"tool": "curl", "url": url, "error": str(exc)}
    parts = completed.stdout.strip().split("\t")
    status = parts[0] if parts else "000"
    return {
        "tool": "curl",
        "method": "HEAD",
        "url": url,
        "http_status": int(status) if status.isdigit() else status,
        "effective_url": parts[1] if len(parts) > 1 else "",
        "content_type": parts[2] if len(parts) > 2 else "",
        "size_download": parts[3] if len(parts) > 3 else "",
        "ssl_verify_result": parts[4] if len(parts) > 4 else "",
        "curl_exit": completed.returncode,
        "stderr": completed.stderr.strip()[:400],
    }


def curl_get(url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(dest.suffix + ".partial")
    command = [
        "curl",
        "-L",
        "-A",
        UA,
        "--max-time",
        "180",
        "-o",
        str(temporary),
        "-w",
        "%{http_code}\t%{url_effective}\t%{content_type}\t%{size_download}",
        url,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    parts = completed.stdout.strip().split("\t")
    status = parts[0] if parts else "000"
    record = {
        "tool": "curl",
        "method": "GET",
        "url": url,
        "http_status": int(status) if status.isdigit() else status,
        "effective_url": parts[1] if len(parts) > 1 else "",
        "content_type": parts[2] if len(parts) > 2 else "",
        "size_download": parts[3] if len(parts) > 3 else "",
        "curl_exit": completed.returncode,
        "stderr": completed.stderr.strip()[:400],
        "saved": False,
    }
    if completed.returncode != 0 or not temporary.is_file() or temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        return record
    # Reject HTML error pages saved as .mat
    header = temporary.read_bytes()[:16]
    if header.startswith(b"<") or header.lower().startswith(b"<!do"):
        record["rejected"] = "response body looks like HTML, not a MATLAB file"
        temporary.unlink(missing_ok=True)
        return record
    temporary.replace(dest)
    record["saved"] = True
    record["path"] = str(dest)
    record["bytes"] = dest.stat().st_size
    record["sha256"] = sha256_file(dest)
    return record


def urllib_head(url: str) -> dict:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=45, context=context) as response:
            return {
                "tool": "urllib",
                "method": "HEAD",
                "url": url,
                "http_status": getattr(response, "status", None),
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
                "effective_url": response.geturl(),
            }
    except urllib.error.HTTPError as exc:
        return {
            "tool": "urllib",
            "method": "HEAD",
            "url": url,
            "http_status": exc.code,
            "error": str(exc.reason),
        }
    except Exception as exc:  # noqa: BLE001 - log the real probe error
        return {
            "tool": "urllib",
            "method": "HEAD",
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    records = []
    stamp = datetime.now(timezone.utc).isoformat()
    print(f"round2 probe start {stamp}")

    for url in PROBE_ONLY + BINALPHA_URLS:
        curl_record = curl_head(url)
        urllib_record = urllib_head(url)
        records.append({"url": url, "curl": curl_record, "urllib": urllib_record})
        print(
            f"HEAD {url} curl={curl_record.get('http_status')} "
            f"urllib={urllib_record.get('http_status', urllib_record.get('error'))}"
        )

    download_log = None
    if BINALPHA_DEST.is_file():
        print(f"SKIP existing {BINALPHA_DEST} sha256={sha256_file(BINALPHA_DEST)}")
    else:
        for url in BINALPHA_URLS:
            print(f"GET {url}")
            download_log = curl_get(url, BINALPHA_DEST)
            records.append({"url": url, "download": download_log})
            if download_log.get("saved"):
                print(
                    f"SAVED {BINALPHA_DEST} bytes={download_log['bytes']} "
                    f"sha256={download_log['sha256']}"
                )
                break
            print(f"not saved: {download_log}")

    payload = {
        "date_utc": stamp,
        "user_agent": UA,
        "note": (
            "ARDB_Full.zip was HEAD-probed only. After reading the Zenodo "
            "record, the zip was not downloaded."
        ),
        "records": records,
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {LOG}")
    return 0 if BINALPHA_DEST.is_file() else 2


if __name__ == "__main__":
    sys.exit(main())
