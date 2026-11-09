"""Download and inspect the round-2 resource list. Raw files stay private."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from experiments.v3_reproduction.protocol_registry import load_campaign


CSV_FIELDS = (
    "resource",
    "role",
    "source_url_or_local_path",
    "download_status",
    "local_file",
    "file_size",
    "sha256",
    "external_checksum_match",
    "native_variables",
    "sample_count",
    "class_count",
    "feature_dimension",
    "expected_paper_specification",
    "source_identity_status",
    "license_status",
    "loader_status",
    "experiment_eligibility",
    "remaining_gap",
)

ATTEMPTS = 3
TIMEOUT_SECONDS = 240


def classify_payload(body: bytes, expected: str, content_type: str | None) -> str:
    """Return a download status from the body prefix. Do not treat HTML as a PDF."""
    head = body.lstrip()[:800]
    lowered = head.lower()
    type_text = (content_type or "").lower()
    looks_html = lowered.startswith(b"<") or b"<html" in lowered or "html" in type_text
    if expected == "pdf":
        if looks_html and not head.startswith(b"%PDF"):
            return "ACCESS_DENIED_HTML"
        if not head.startswith(b"%PDF"):
            return "INVALID_FILE"
        return "DOWNLOADED_VALID_FORMAT"
    if expected == "zip":
        if looks_html and not head.startswith(b"PK"):
            return "ACCESS_DENIED_HTML"
        if not head.startswith(b"PK"):
            return "INVALID_FILE"
        return "DOWNLOADED_VALID_FORMAT"
    if expected == "json":
        try:
            json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return "INVALID_FILE"
        return "DOWNLOADED_VALID_FORMAT"
    if expected == "html":
        if looks_html or b"<!doctype" in lowered:
            return "DOWNLOADED_VALID_FORMAT"
        return "INVALID_FILE"
    if expected == "mat":
        if looks_html and not head.startswith(b"MATLAB") and not head.startswith(b"\x89HDF"):
            return "ACCESS_DENIED_HTML"
        if head.startswith(b"MATLAB") or head.startswith(b"\x89HDF"):
            return "DOWNLOADED_VALID_FORMAT"
        return "INVALID_FILE"
    return "INVALID_FILE"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checksum_match(path: Path, algorithm: str | None, expected: str | None) -> str:
    if not algorithm or not expected:
        return "not_supplied"
    actual = _md5(path) if algorithm.lower() == "md5" else _sha256(path)
    return "true" if actual.lower() == expected.lower() else "false"


def _curl_once(url: str, part: Path) -> dict[str, Any]:
    part.parent.mkdir(parents=True, exist_ok=True)
    if part.exists():
        part.unlink()
    header_path = part.with_suffix(part.suffix + ".headers")
    command = [
        "curl",
        "-L",
        "--max-time",
        str(TIMEOUT_SECONDS),
        "-o",
        str(part),
        "-D",
        str(header_path),
        "-w",
        "\n__HTTP__%{http_code}\n__URL__%{url_effective}\n__TYPE__%{content_type}\n",
        url,
    ]
    stamp = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 20,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "timestamp_utc": stamp,
            "status": "TIMEOUT",
            "error": str(exc),
            "final_url": url,
        }
    except OSError as exc:
        return {
            "timestamp_utc": stamp,
            "status": "NETWORK_DNS_FAILURE",
            "error": str(exc),
            "final_url": url,
        }
    def _marked(name: str) -> str:
        token = f"__{name}__"
        text = completed.stdout or ""
        index = text.rfind(token)
        if index < 0:
            return ""
        return text[index + len(token):].splitlines()[0].strip()

    http_code = _marked("HTTP")
    final_url = _marked("URL") or url
    content_type = _marked("TYPE")
    record: dict[str, Any] = {
        "timestamp_utc": stamp,
        "curl_exit": completed.returncode,
        "http_code": http_code,
        "final_url": final_url,
        "content_type": content_type,
        "stderr_tail": (completed.stderr or "")[-300:],
    }
    if completed.returncode == 6:
        record["status"] = "NETWORK_DNS_FAILURE"
        return record
    if completed.returncode == 28:
        record["status"] = "TIMEOUT"
        return record
    if http_code == "404":
        record["status"] = "HTTP_404"
        return record
    if http_code == "403":
        record["status"] = "HTTP_403"
        return record
    if not part.is_file() or part.stat().st_size == 0:
        record["status"] = "INVALID_FILE"
        record["error"] = f"curl exit {completed.returncode} produced no body"
        return record
    body = part.read_bytes()[:800]
    status = classify_payload(body, "pdf", content_type) if False else None
    record["status"] = status or "BODY_PRESENT"
    record["body_prefix_hex"] = body[:16].hex()
    return record


def _download_url(url: str, destination: Path, expected: str) -> dict[str, Any]:
    part = destination.with_suffix(destination.suffix + ".part")
    last: dict[str, Any] = {}
    for attempt in range(1, ATTEMPTS + 1):
        last = _curl_once(url, part)
        last["attempt"] = attempt
        if last.get("status") in {"NETWORK_DNS_FAILURE", "TIMEOUT", "HTTP_404", "HTTP_403"}:
            continue
        if last.get("status") != "BODY_PRESENT":
            continue
        raw = part.read_bytes()
        probe_body = raw if expected == "json" else raw[:800]
        status = classify_payload(probe_body, expected, last.get("content_type"))
        last["status"] = status
        if status == "ACCESS_DENIED_HTML":
            part.unlink(missing_ok=True)
            return last
        if status != "DOWNLOADED_VALID_FORMAT":
            continue
        last["bytes"] = part.stat().st_size
        return last
    if part.exists() and last.get("status") not in {"DOWNLOADED_VALID_FORMAT", "ACCESS_DENIED_HTML"}:
        part.unlink(missing_ok=True)
    return last


def _validate_pdf(path: Path) -> dict[str, Any]:
    info = subprocess.run(
        ["pdfinfo", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if info.returncode != 0:
        return {"pdf_valid": False, "pdf_error": (info.stderr or "")[-200:]}
    pages = None
    title = None
    for line in info.stdout.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split(":", 1)[1].strip())
        if line.startswith("Title:"):
            title = line.split(":", 1)[1].strip()
    text = subprocess.run(
        ["pdftotext", "-f", "1", "-l", "2", "-layout", str(path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    excerpt = (text.stdout or "")[:1500].replace("\n", " ")
    return {"pdf_valid": True, "pages": pages, "pdf_title": title, "first_pages_excerpt": excerpt[:500]}


def _validate_zip(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            names = archive.namelist()
    except zipfile.BadZipFile as exc:
        return {"zip_valid": False, "error": str(exc)}
    unsafe = [name for name in names if name.startswith("/") or ".." in Path(name).parts]
    return {
        "zip_valid": bad is None and not unsafe,
        "zip_bad_member": bad,
        "zip_unsafe_members": unsafe,
        "zip_members": names[:80],
        "zip_member_count": len(names),
    }


def _mat_variables(path: Path) -> dict[str, Any]:
    from scipy.io import loadmat, whosmat

    try:
        listed = whosmat(str(path))
    except (NotImplementedError, ValueError, OSError):
        listed = None
    if listed is None:
        return _h5_variables(path)
    try:
        payload = loadmat(str(path), squeeze_me=False, struct_as_record=True)
    except (NotImplementedError, ValueError) as exc:
        h5 = _h5_variables(path)
        h5["loadmat_error"] = str(exc)
        return h5
    variables = []
    arrays: dict[str, np.ndarray] = {}
    for name, value in payload.items():
        if name.startswith("__"):
            continue
        array = np.asarray(value)
        variables.append(
            {
                "name": name,
                "shape": list(array.shape),
                "dtype": str(array.dtype),
            }
        )
        if array.dtype != object:
            arrays[name] = array
    summary = _summarize_numeric(arrays)
    if summary.get("sample_count") is None:
        summary.update(_object_cells(payload))
    summary["native_variables"] = variables
    summary["whosmat"] = [
        {"name": name, "shape": list(shape), "matlab_class": matlab_class}
        for name, shape, matlab_class in listed
    ]
    return summary


def _h5_variables(path: Path) -> dict[str, Any]:
    import h5py

    variables = []
    arrays: dict[str, np.ndarray] = {}
    with h5py.File(path, "r") as handle:
        def _visit(name: str, item: Any) -> None:
            if not hasattr(item, "shape"):
                return
            variables.append({"name": name, "shape": list(item.shape), "dtype": str(item.dtype)})
            if item.size <= 8_000_000 and item.dtype.kind in "fiu":
                arrays[name] = np.asarray(item)

        handle.visititems(_visit)
    summary = _summarize_numeric(arrays)
    summary["native_variables"] = variables
    summary["format"] = "matlab_v7.3_hdf5"
    return summary


def _summarize_numeric(arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    """Use a 1-d label vector when one exists. Do not pick orientation by length alone."""
    labels = None
    label_name = None
    for name, array in arrays.items():
        flat = np.asarray(array).reshape(-1)
        if array.ndim <= 2 and flat.size == array.size and min(array.shape) == 1 and flat.size >= 2:
            numeric = flat.astype(np.float64)
            if np.all(np.isfinite(numeric)) and np.all(numeric == np.floor(numeric)):
                if labels is None or flat.size > labels.size:
                    labels = numeric.astype(np.int64)
                    label_name = name
    features = None
    feature_name = None
    if labels is not None:
        for name, array in arrays.items():
            if name == label_name:
                continue
            if array.ndim == 2 and labels.size in array.shape and array.dtype != object:
                features = array
                feature_name = name
                break
    sample_count = None
    feature_dimension = None
    class_count = None
    value_min = None
    value_max = None
    duplicate_rows = None
    orientation = None
    if features is not None and labels is not None:
        if features.shape[0] == labels.size:
            sample_count = int(features.shape[0])
            feature_dimension = int(features.shape[1])
            orientation = "rows_are_samples"
            matrix = features
        elif features.shape[1] == labels.size:
            sample_count = int(features.shape[1])
            feature_dimension = int(features.shape[0])
            orientation = "columns_are_samples"
            matrix = features.T
        else:
            matrix = None
        if matrix is not None:
            finite = np.asarray(matrix, dtype=np.float64)
            value_min = float(np.min(finite))
            value_max = float(np.max(finite))
            class_count = int(np.unique(labels).size)
            if matrix.shape[0] <= 4000 and matrix.shape[1] <= 20000:
                duplicate_rows = _duplicate_row_count(matrix)
    return {
        "label_variable": label_name,
        "feature_variable": feature_name,
        "sample_count": sample_count,
        "class_count": class_count,
        "feature_dimension": feature_dimension,
        "orientation": orientation,
        "value_min": value_min,
        "value_max": value_max,
        "exact_duplicate_rows": duplicate_rows,
    }


def _duplicate_row_count(matrix: np.ndarray) -> int:
    seen: set[bytes] = set()
    duplicates = 0
    for row in np.ascontiguousarray(matrix):
        key = row.tobytes()
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def _cell_text(item: Any) -> str | None:
    array = np.asarray(item)
    if array.dtype.kind in {"U", "S"}:
        return "".join(array.astype(str).reshape(-1).tolist()) or None
    if array.size == 1 and array.dtype == object:
        value = array.reshape(-1)[0]
        return value if isinstance(value, str) else None
    if array.size == 1:
        value = array.item()
        return value if isinstance(value, str) else None
    return None


def _object_cells(payload: dict[str, Any]) -> dict[str, Any]:
    """Describe MATLAB cell arrays without assuming the longer axis is the sample axis."""
    notes = []
    for name, value in payload.items():
        if str(name).startswith("__"):
            continue
        array = np.asarray(value)
        if array.dtype != object:
            continue
        cells = []
        for cell in array.reshape(-1):
            item = np.asarray(cell)
            cells.append(item)
        shapes = [list(item.shape) for item in cells[:8]]
        note: dict[str, Any] = {
            "name": str(name),
            "cell_grid": list(array.shape),
            "n_cells": int(array.size),
            "example_shapes": shapes,
        }
        if cells and all(item.ndim == 2 and item.shape == cells[0].shape for item in cells):
            height, width = cells[0].shape
            note.update(
                {
                    "layout": "image_cells",
                    "sample_count": int(array.size),
                    "class_count": int(array.shape[0]) if array.ndim == 2 else int(array.size),
                    "feature_dimension": int(height * width),
                    "spatial": [int(height), int(width)],
                    "value_min": int(min(item.min() for item in cells)),
                    "value_max": int(max(item.max() for item in cells)),
                }
            )
        elif cells and all(item.ndim == 3 for item in cells):
            spatial = [list(item.shape[:2]) for item in cells]
            slices = [int(item.shape[2]) for item in cells]
            note.update(
                {
                    "layout": "per_class_stack",
                    "sample_count": int(sum(slices)),
                    "class_count": int(len(cells)),
                    "spatial_per_class": spatial[:8],
                    "slices_per_class": slices,
                    "feature_dimension": int(cells[0].shape[0] * cells[0].shape[1])
                    if len(set(map(tuple, spatial))) == 1
                    else None,
                }
            )
        string_values = []
        if array.size <= 64:
            for item in array.reshape(-1):
                text = _cell_text(item)
                if text:
                    string_values.append(text)
        if string_values:
            note["strings"] = string_values
        notes.append(note)
    chosen = next((note for note in notes if note.get("sample_count")), None)
    summary: dict[str, Any] = {"cell_variables": notes}
    if chosen:
        summary.update(
            {
                "sample_count": chosen.get("sample_count"),
                "class_count": chosen.get("class_count"),
                "feature_dimension": chosen.get("feature_dimension"),
                "orientation": chosen.get("layout"),
                "value_min": chosen.get("value_min"),
                "value_max": chosen.get("value_max"),
            }
        )
    return summary


def _identity_for_counts(resource_id: str, summary: dict[str, Any]) -> tuple[str, str, str]:
    """Return identity status, experiment eligibility, and the remaining gap."""
    n = summary.get("sample_count")
    k = summary.get("class_count")
    d = summary.get("feature_dimension")
    if resource_id == "ar_lzuf_AR_mat":
        if n == 840 and k == 120:
            return (
                "COUNTS_MATCHED_CANDIDATE",
                "supplemental_only",
                "Counts match 840/120. Historical identity is not verified. Do not replace the blocked AR cell.",
            )
        if k == 100:
            return (
                "NON_TARGET_AR100",
                "not_eligible",
                "100 identities are not the 120-person AR target. Do not cluster this file as paper AR.",
            )
        if n is not None and n > 840 and (k or 0) >= 120:
            return (
                "DOCUMENTED_SUPERSET_ONLY",
                "not_eligible",
                f"{n} images, {k} identities, {d} features, "
                f"{summary.get('exact_duplicate_rows')} exact duplicate rows. "
                "No documented 840-image rule was found, so no subset was taken.",
            )
        return (
            "INSUFFICIENT_FOR_TARGET_REPRODUCTION",
            "not_eligible",
            f"Observed n={n}, classes={k}, features={d}. This is not a verified 840/120 AR matrix.",
        )
    if resource_id.startswith("umist_"):
        if resource_id == "umist_roweis_cropped_mat" and n == 575 and k == 20:
            return (
                "NON_EXACT_UMIST575",
                "diagnostic_not_scheduled",
                "Roweis facedat is 575 images of 20 people at 112x92, directory names 1a-1t. "
                "The NYU page states 575, not the SSC 564 set. "
                "SHA-256 ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361 matches the figshare575 file. "
                "Its pixels do not intersect the wayback cropped 575 already executing. No samples were dropped.",
            )
        if n == 564 and k == 20:
            return (
                "COUNTS_MATCHED_RECONSTRUCTION",
                "supplemental_only",
                "564/20 matches the stated count. Identity against the SSC file is still unverified.",
            )
        if n == 575:
            return (
                "NON_EXACT_UMIST575",
                "diagnostic_not_scheduled",
                f"575 images, {k} classes, {d} features, "
                f"{summary.get('exact_duplicate_rows')} exact duplicate rows. "
                "Not the SSC 564-image set. Samples were not dropped.",
            )
        if n == 574 and k == 20:
            return (
                "INSUFFICIENT_FOR_TARGET_REPRODUCTION",
                "not_eligible",
                "574 x 10304 with 20 classes and 10 exact duplicate rows "
                "(564 unique rows). The duplicates were not removed and the file was not relabeled as the 564-image set.",
            )
        return (
            "INSUFFICIENT_FOR_TARGET_REPRODUCTION",
            "not_eligible",
            f"Observed n={n}, classes={k}, features={d}. Not the 564-image target.",
        )
    if resource_id == "binalpha_roweis_parent_mat":
        if n == 1404 and k == 36 and d == 320:
            return (
                "PARENT_DATA_VERIFIED",
                "parent_not_historical_subset",
                "36x39 parent is verified. The 26x30 letter draw remains HISTORICAL_INDICES_UNKNOWN.",
            )
        return (
            "PARENT_CONTENTS_DIFFER",
            "not_eligible",
            f"Observed n={n}, classes={k}, features={d}. Expected 1404/36/320.",
        )
    return ("INSPECTED", "see_round2_note", "")


def _copy_local(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_file():
        return {"status": "INVALID_FILE", "error": f"missing local source {source}"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_hash = _sha256(source)
    if destination.is_file() and _sha256(destination) == source_hash:
        return {
            "status": "DOWNLOADED_VALID_FORMAT",
            "reused_existing": True,
            "bytes": destination.stat().st_size,
            "sha256": source_hash,
            "final_url": str(source),
        }
    part = destination.with_suffix(destination.suffix + ".part")
    shutil.copyfile(source, part)
    if _sha256(part) != source_hash:
        part.unlink(missing_ok=True)
        return {"status": "CHECKSUM_MISMATCH", "error": "copy changed bytes"}
    part.replace(destination)
    return {
        "status": "DOWNLOADED_VALID_FORMAT",
        "reused_existing": False,
        "bytes": destination.stat().st_size,
        "sha256": source_hash,
        "final_url": str(source),
    }


def _load_sources(campaign: dict[str, Any]) -> list[dict[str, Any]]:
    pointer = campaign.get("resource_sources", "resource_sources.yaml")
    path = Path(campaign["_dir"]) / pointer
    payload = yaml.safe_load(path.read_text())
    sources = payload.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("resource_sources.yaml has no sources list")
    return sources


def _workspace(campaign: dict[str, Any]) -> Path:
    return Path(campaign["workspace"])


def recover(config_path: str | Path) -> dict[str, Any]:
    campaign = load_campaign(config_path)
    root = _workspace(campaign)
    docs = root / "docs" / "v3"
    docs.mkdir(parents=True, exist_ok=True)
    log_path = docs / "resource_download_log.jsonl"
    rows = []
    log_records = []
    for source in sorted(_load_sources(campaign), key=lambda item: int(item.get("priority", 9))):
        row, log_record = _one_source(root, source)
        rows.append(row)
        log_records.append(log_record)
    rows.extend(_stage_rows())
    with log_path.open("w") as handle:
        for record in log_records:
            handle.write(json.dumps(record) + "\n")
    csv_path = docs / "resource_recovery_round2.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in CSV_FIELDS})
    _write_markdown(docs / "resource_recovery_round2.md", rows)
    return {"n_sources": len(rows), "csv": str(csv_path), "log": str(log_path)}


def _one_source(root: Path, source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    stamp = datetime.now(timezone.utc).isoformat()
    destination = source.get("destination")
    dest_path = root / destination if destination else None
    blocked = source.get("blocked_status")
    log_record: dict[str, Any] = {
        "timestamp_utc": stamp,
        "resource": source["id"],
        "url": source.get("url"),
        "local_source": source.get("local_source"),
    }
    if blocked:
        row = _empty_row(source, blocked)
        log_record["download_status"] = blocked
        if source["id"] == "msra50_data":
            row["loader_status"] = "BLOCKED_NO_VERIFIED_DATA_URL"
        if source["id"] == "lda_sc_definition":
            row["loader_status"] = "not_a_dataset"
            row["remaining_gap"] = "No standalone definition in SSC, SLPS, or Ding and Li."
        return row, log_record
    if source.get("local_source"):
        outcome = _copy_local(Path(source["local_source"]), dest_path)
    elif source.get("url") and dest_path is not None:
        if dest_path.is_file():
            outcome = {
                "status": "DOWNLOADED_VALID_FORMAT",
                "reused_existing": True,
                "bytes": dest_path.stat().st_size,
                "sha256": _sha256(dest_path),
                "final_url": source["url"],
            }
            prefix = dest_path.read_bytes()[:800]
            checked = classify_payload(prefix, source["content_type"], None)
            if checked != "DOWNLOADED_VALID_FORMAT":
                outcome = _download_url(source["url"], dest_path, source["content_type"])
        else:
            outcome = _download_url(source["url"], dest_path, source["content_type"])
    else:
        outcome = {"status": "INVALID_FILE", "error": "no url and no local source"}
    log_record.update(outcome)
    status = outcome.get("status", "INVALID_FILE")
    if status == "DOWNLOADED_VALID_FORMAT" and dest_path is not None and not dest_path.is_file():
        part = dest_path.with_suffix(dest_path.suffix + ".part")
        if part.is_file():
            match = _checksum_match(
                part,
                source.get("external_checksum_algorithm"),
                source.get("external_checksum"),
            )
            if match == "false":
                rejected = dest_path.with_suffix(dest_path.suffix + ".checksum_mismatch")
                part.replace(rejected)
                status = "CHECKSUM_MISMATCH"
                log_record["status"] = status
                log_record["rejected_file"] = str(rejected)
            else:
                extra = _content_checks(part, source["content_type"])
                if extra.get("invalid"):
                    status = "INVALID_FILE"
                    log_record["status"] = status
                    log_record["validation"] = extra
                    part.unlink(missing_ok=True)
                elif extra.get("keep_file"):
                    part.replace(dest_path)
                    log_record["validation_error"] = extra.get("error")
                else:
                    part.replace(dest_path)
                    log_record["validation"] = extra
    inspection: dict[str, Any] = {}
    checksum = "not_supplied"
    file_size = ""
    digest = ""
    if dest_path is not None and dest_path.is_file() and status == "DOWNLOADED_VALID_FORMAT":
        checksum = _checksum_match(
            dest_path,
            source.get("external_checksum_algorithm"),
            source.get("external_checksum"),
        )
        if checksum == "false":
            status = "CHECKSUM_MISMATCH"
        file_size = dest_path.stat().st_size
        digest = _sha256(dest_path)
        log_record["sha256"] = digest
        log_record["external_checksum_match"] = checksum
        if source["content_type"] == "pdf":
            inspection = _validate_pdf(dest_path)
        elif source["content_type"] == "zip":
            inspection = _validate_zip(dest_path)
        elif source["content_type"] == "mat":
            try:
                inspection = _mat_variables(dest_path)
            except Exception as exc:
                inspection = {"inspection_error": f"{type(exc).__name__}: {exc}"}
        log_record["inspection"] = {
            key: value
            for key, value in inspection.items()
            if key not in {"first_pages_excerpt"}
        }
    identity, eligibility, gap = ("", "", "")
    if source["content_type"] == "mat" and inspection:
        identity, eligibility, gap = _identity_for_counts(source["id"], inspection)
    elif source["id"] == "slps_hou2013_pdf" and inspection.get("pdf_valid"):
        identity = "FULL_TEXT_VERIFIED_LOCAL"
        eligibility = "method_text_only"
        gap = "Full text is verified locally. That status is not an implementation claim."
    row = _empty_row(source, status)
    row.update(
        {
            "local_file": "" if dest_path is None else str(dest_path),
            "file_size": file_size,
            "sha256": digest,
            "external_checksum_match": checksum,
            "native_variables": json.dumps(inspection.get("native_variables", inspection.get("whosmat", "")))[:500],
            "sample_count": inspection.get("sample_count", ""),
            "class_count": inspection.get("class_count", ""),
            "feature_dimension": inspection.get("feature_dimension", ""),
            "source_identity_status": identity,
            "experiment_eligibility": eligibility,
            "remaining_gap": gap,
        }
    )
    if source["content_type"] == "pdf":
        row["native_variables"] = json.dumps(
            {"pages": inspection.get("pages"), "pdf_title": inspection.get("pdf_title")}
        )
    if source["content_type"] == "zip":
        row["native_variables"] = json.dumps(
            {
                "member_count": inspection.get("zip_member_count"),
                "members": (inspection.get("zip_members") or [])[:20],
            }
        )
    loader_status = {
        "ar_lzuf_AR_mat": "diagnostic_version_lzuf_superset1680_not_scheduled",
        "umist_lzuf_mat": "diagnostic_version_lzuf574_not_scheduled",
        "umist_zenodo_3634017_mat": "diagnostic_version_zenodo3634017_not_scheduled",
        "umist_roweis_cropped_mat": "pending_native_inspection",
        "binalpha_roweis_parent_mat": "existing_parent_loader_binaryalphadigs36",
        "msra50_data": "BLOCKED_NO_VERIFIED_DATA_URL",
    }.get(source["id"])
    if loader_status:
        row["loader_status"] = loader_status
    if source["id"] == "umist_roweis_cropped_mat" and inspection.get("sample_count"):
        row["loader_status"] = "inspected_nonexact_not_scheduled"
    if source["id"] == "binalpha_roweis_parent_mat" and row.get("sha256") == "3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7":
        row["remaining_gap"] = (
            "SHA-256 matches the parent already used by v1/v2 and by letters26x30_seed0. "
            "The 780-image subset remains HISTORICAL_INDICES_UNKNOWN."
        )
    return row, log_record


def _content_checks(path: Path, content_type: str) -> dict[str, Any]:
    if content_type == "pdf":
        info = _validate_pdf(path)
        info["invalid"] = not info.get("pdf_valid")
        return info
    if content_type == "zip":
        info = _validate_zip(path)
        info["invalid"] = not info.get("zip_valid")
        return info
    if content_type == "mat":
        head = path.read_bytes()[:16]
        ok = head.startswith(b"MATLAB") or head.startswith(b"\x89HDF")
        return {"invalid": not ok}
    return {"invalid": False}


def _empty_row(source: dict[str, Any], status: str) -> dict[str, Any]:
    locator = source.get("url") or source.get("local_source") or ""
    return {
        "resource": source["id"],
        "role": source["role"],
        "source_url_or_local_path": locator,
        "download_status": status,
        "local_file": "",
        "file_size": "",
        "sha256": "",
        "external_checksum_match": "not_supplied",
        "native_variables": "",
        "sample_count": "",
        "class_count": "",
        "feature_dimension": "",
        "expected_paper_specification": source.get("expected_paper_specification", ""),
        "source_identity_status": source.get("blocked_status", ""),
        "license_status": source.get("license", ""),
        "loader_status": "not_a_dataset" if source["role"] != "dataset" else "pending_inspection",
        "experiment_eligibility": "blocked" if source.get("blocked_status") else "",
        "remaining_gap": source.get("reference_url", ""),
    }


def _stage_rows() -> list[dict[str, Any]]:
    return [
        {
            "resource": "slps_stage_full_text",
            "role": "paper",
            "source_url_or_local_path": "local Hou et al. PDF",
            "download_status": "FULL_TEXT_VERIFIED_LOCAL",
            "local_file": "baselines/spls/resources/private/hou2013_slps.pdf",
            "file_size": "",
            "sha256": "",
            "external_checksum_match": "not_supplied",
            "native_variables": "",
            "sample_count": "",
            "class_count": "",
            "feature_dimension": "",
            "expected_paper_specification": "13-page IP&M article, Section 3 included",
            "source_identity_status": "FULL_TEXT_VERIFIED_LOCAL",
            "license_status": "publisher PDF not committed",
            "loader_status": "not_a_dataset",
            "experiment_eligibility": "method_text_only",
            "remaining_gap": "Verified text does not by itself mean the code matches.",
        },
        {
            "resource": "slps_stage_specification",
            "role": "paper",
            "source_url_or_local_path": "docs/v3/slps_method_specification.md",
            "download_status": "METHOD_SPECIFICATION_COMPLETE",
            "local_file": "docs/v3/slps_method_specification.md",
            "file_size": "",
            "sha256": "",
            "external_checksum_match": "not_supplied",
            "native_variables": "",
            "sample_count": "",
            "class_count": "",
            "feature_dimension": "",
            "expected_paper_specification": "Eqs. (7)-(19), Table 2, Section 4 one-shot protocol",
            "source_identity_status": "METHOD_SPECIFICATION_COMPLETE",
            "license_status": "independently written notes",
            "loader_status": "not_a_dataset",
            "experiment_eligibility": "specification_only",
            "remaining_gap": "Author code was not found. Alpha/d selection criterion is not stated.",
        },
        {
            "resource": "slps_stage_implementation",
            "role": "code",
            "source_url_or_local_path": "baselines/spls/spls.py",
            "download_status": "IMPLEMENTED",
            "local_file": "baselines/spls/spls.py",
            "file_size": "",
            "sha256": "",
            "external_checksum_match": "not_supplied",
            "native_variables": "",
            "sample_count": "",
            "class_count": "",
            "feature_dimension": "",
            "expected_paper_specification": "One-shot Eqs. (18)-(19), local scaling, k=7, then K-means",
            "source_identity_status": "IMPLEMENTED",
            "license_status": "independent reimplementation",
            "loader_status": "not_a_dataset",
            "experiment_eligibility": "executable_where_data_exists",
            "remaining_gap": "SSC protocol replaces the paper's 100-run K-means selection. Ncut variant is not the SSC SPLS cell.",
        },
        {
            "resource": "slps_stage_numerical",
            "role": "code",
            "source_url_or_local_path": "baselines/spls/test_spls.py",
            "download_status": "NUMERICALLY_VALIDATED",
            "local_file": "baselines/spls/test_spls.py",
            "file_size": "",
            "sha256": "",
            "external_checksum_match": "not_supplied",
            "native_variables": "",
            "sample_count": "",
            "class_count": "",
            "feature_dimension": "",
            "expected_paper_specification": "Dense Eq. (18) solve and Zelnik-Manor weights",
            "source_identity_status": "NUMERICALLY_VALIDATED",
            "license_status": "tests",
            "loader_status": "not_a_dataset",
            "experiment_eligibility": "executable_where_data_exists",
            "remaining_gap": "Validation is algebraic. It is not a claim that SSC table numbers were reproduced.",
        },
        {
            "resource": "binalpha_letters26x30_seed0",
            "role": "dataset",
            "source_url_or_local_path": "benchmarks/binalpha/reconstructions/letters26x30_seed0.json",
            "download_status": "SUBSET_RECONSTRUCTED",
            "local_file": "benchmarks/binalpha/reconstructions/letters26x30_seed0.json",
            "file_size": "",
            "sha256": "",
            "external_checksum_match": "not_supplied",
            "native_variables": "parent indices stored per letter",
            "sample_count": 780,
            "class_count": 26,
            "feature_dimension": 320,
            "expected_paper_specification": "26 alphabets x 30 images. Author indices were not published.",
            "source_identity_status": "HISTORICAL_INDICES_UNKNOWN",
            "license_status": "index file only; images stay with the parent mat",
            "loader_status": "CANDIDATE_BIN_ALPHA",
            "experiment_eligibility": "supplemental_not_historical",
            "remaining_gap": "Seed 0 is a prespecified reconstruction, not Chang et al.'s draw.",
        },
    ]


def _write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# v3 resource recovery round 2",
        "",
        "Raw matrices and publisher PDFs stay in gitignored `resources/private/` directories.",
        "A download failure is not evidence that the resource does not exist.",
        "Count agreement is not historical identity.",
        "",
        "| Resource | Status | Identity | Eligibility |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['resource']}` | {row['download_status']} | {row['source_identity_status']} | {row['experiment_eligibility']} |"
        )
    lines.extend(
        [
            "",
            "LDA-SC has no verified definition in the SSC paper, the SLPS paper, or Ding and Li.",
            "Ding and Li define LDA-Kmeans. SLPS calls that method LdaKm.",
            "MSRA50 has no direct data URL. The arXiv HTML page was not saved as a dataset.",
            "LDA-SC remains METHOD_DEFINITION_UNRESOLVED after reading SSC, SLPS, and Ding and Li.",
            "",
            "## Procrustes cross-check",
            "",
            "Ncut_9/discretisation.m computes `[U,S,V] = svd(Discrete' * EigenVectors)` and, on non-terminal iterations, sets `R = V*U'`.",
            "`baselines/llc/llc.py` uses `R = Vt.T @ U.T` after `svd(discrete.T @ embedding)`, which is the same factor.",
            "The archive is Jianbo Shi's Normalized Cuts package. It was not executed, and it is not LLC or SSC author code.",
            "",
        ]
    )
    path.write_text("\n".join(lines))
