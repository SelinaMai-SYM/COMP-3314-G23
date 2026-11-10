#!/usr/bin/env python3
"""Record real validation outcomes. Do not invent passed checks."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORT_MD = ROOT / "docs" / "validation_report.md"
REPORT_JSON = ROOT / "docs" / "validation_report.json"

DOWNLOADS = [
    (
        ROOT / "benchmarks" / "orl" / "data" / "olivettifaces.mat",
        "b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794",
    ),
    (
        ROOT / "benchmarks" / "usps" / "data" / "usps.bz2",
        "3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f",
    ),
    (
        ROOT / "benchmarks" / "usps" / "data" / "usps.t.bz2",
        "a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e",
    ),
    (
        ROOT / "benchmarks" / "yaleb" / "data" / "YaleB_32x32.mat",
        "3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99",
    ),
    (
        ROOT / "benchmarks" / "jaffe" / "data" / "jaffe.zip",
        "6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b",
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(args: list[str], cwd: Path | None = None, timeout: int = 300) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "cmd": args,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        }
    except FileNotFoundError as exc:
        return {"cmd": args, "returncode": None, "error": f"FileNotFoundError: {exc}"}
    except subprocess.TimeoutExpired:
        return {"cmd": args, "returncode": None, "error": f"timeout after {timeout}s"}


def check_syntax() -> dict[str, Any]:
    roots = [
        ROOT / "SSC_method",
        ROOT / "baselines",
        ROOT / "benchmarks",
        ROOT / "method_extension",
        ROOT / "experiments",
        ROOT / "scripts",
        ROOT / "tests",
    ]
    files: list[Path] = []
    for folder in roots:
        if folder.is_dir():
            files.extend(sorted(folder.rglob("*.py")))
    failed = []
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (py_compile.PyCompileError, SyntaxError, ValueError) as exc:
            failed.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
    return {
        "name": "syntax",
        "status": "PASS" if not failed else "FAIL",
        "n_files": len(files),
        "failures": failed,
    }


def check_tests() -> dict[str, Any]:
    result = run_cmd([sys.executable, "-m", "pytest", "-q"], timeout=300)
    status = "PASS" if result.get("returncode") == 0 else "FAIL"
    if result.get("returncode") is None:
        status = "FAIL"
    return {"name": "pytest", "status": status, **result}


def check_manifests() -> dict[str, Any]:
    names = ["orl", "jaffe", "yaleb", "usps", "ar", "umist", "binalpha", "msra50"]
    missing = []
    present = []
    for name in names:
        path = ROOT / "benchmarks" / name / "manifest.yaml"
        if path.is_file():
            present.append(name)
        else:
            missing.append(name)
    return {
        "name": "manifests",
        "status": "PASS" if not missing else "FAIL",
        "present": present,
        "missing": missing,
    }


def check_checksums() -> dict[str, Any]:
    rows = []
    for path, expected in DOWNLOADS:
        rel = str(path.relative_to(ROOT))
        if not path.is_file():
            rows.append({"file": rel, "status": "SKIPPED", "reason": "file not present (gitignored raw data)"})
            continue
        got = sha256(path)
        rows.append(
            {
                "file": rel,
                "status": "PASS" if got == expected else "FAIL",
                "expected": expected,
                "got": got,
            }
        )
    statuses = {row["status"] for row in rows}
    if "FAIL" in statuses:
        overall = "FAIL"
    elif statuses == {"SKIPPED"}:
        overall = "SKIPPED"
    elif "SKIPPED" in statuses:
        overall = "PASS_WITH_SKIP"
    else:
        overall = "PASS"
    return {"name": "checksums", "status": overall, "files": rows}


def check_runs() -> dict[str, Any]:
    runs = ROOT / "runs"
    if not runs.is_dir():
        return {"name": "runs", "status": "FAIL", "error": "runs/ missing"}
    dirs = [p for p in runs.iterdir() if p.is_dir()]
    counts = {"COMPLETED": 0, "SKIPPED": 0, "FAILED": 0, "OTHER": 0, "missing_status": 0}
    missing_metrics = []
    for path in dirs:
        status_path = path / "status.json"
        if not status_path.is_file():
            counts["missing_status"] += 1
            continue
        try:
            payload = json.loads(status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            counts["OTHER"] += 1
            continue
        status = str(payload.get("status") or "OTHER").upper()
        counts[status] = counts.get(status, 0) + 1
        if status == "COMPLETED" and not (path / "metrics.json").is_file():
            missing_metrics.append(path.name)
    ok = counts["missing_status"] == 0 and not missing_metrics
    return {
        "name": "runs",
        "status": "PASS" if ok else "FAIL",
        "n_directories": len(dirs),
        "counts": counts,
        "completed_missing_metrics": missing_metrics,
    }


def check_traceability() -> dict[str, Any]:
    index = ROOT / "results" / "run_index.csv"
    if not index.is_file():
        return {"name": "traceability", "status": "FAIL", "error": "results/run_index.csv missing"}
    with index.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    missing_dirs = []
    completed_without_metrics = []
    for row in rows:
        run_id = row.get("run_id") or ""
        run_dir = ROOT / "runs" / run_id
        if not run_dir.is_dir():
            missing_dirs.append(run_id)
            continue
        if (row.get("status") or "").upper() == "COMPLETED" and not (run_dir / "metrics.json").is_file():
            completed_without_metrics.append(run_id)
    status = "PASS" if not missing_dirs and not completed_without_metrics else "FAIL"
    return {
        "name": "traceability",
        "status": status,
        "n_index_rows": len(rows),
        "missing_run_dirs": missing_dirs[:20],
        "completed_without_metrics": completed_without_metrics[:20],
    }


def check_tables_figures() -> dict[str, Any]:
    required_tables = [
        ROOT / "results" / "tables" / "table1_datasets.md",
        ROOT / "results" / "tables" / "table2_track_a_acc.md",
        ROOT / "results" / "tables" / "table3_track_a_nmi.md",
        ROOT / "results" / "tables" / "table4_track_b.md",
        ROOT / "results" / "tables" / "table5_ex1_ssc_vs_rssc.md",
        ROOT / "results" / "tables" / "table6_robustness.md",
        ROOT / "results" / "tables" / "table7_k_ablation.md",
        ROOT / "results" / "tables" / "table8_runtime_convergence.md",
        ROOT / "report" / "tables" / "track_a_acc.tex",
        ROOT / "report" / "tables" / "track_a_nmi.tex",
        ROOT / "report" / "tables" / "track_b_acc.tex",
        ROOT / "report" / "tables" / "extension_comparison.tex",
        ROOT / "report" / "tables" / "ablation.tex",
        ROOT / "report" / "tables" / "robustness.tex",
    ]
    required_figs = [
        ROOT / "report" / "figures" / "fig1_track_a_acc.pdf",
        ROOT / "report" / "figures" / "fig2_gamma_sensitivity.pdf",
        ROOT / "report" / "figures" / "fig4_ex1_ssc_vs_rssc.pdf",
        ROOT / "report" / "figures" / "fig8_k_sensitivity.pdf",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required_tables + required_figs if not p.is_file()]
    tex = (ROOT / "report" / "main.tex").read_text(encoding="utf-8")
    fillers = [token for token in ("TODO", "TBD", "Lorem", "Currently unpopulated") if token in tex]
    return {
        "name": "tables_figures_tex",
        "status": "PASS" if not missing and not fillers else "FAIL",
        "missing": missing,
        "main_tex_filler_tokens": fillers,
    }


def check_pdf() -> dict[str, Any]:
    pdf = ROOT / "report" / "main.pdf"
    if not pdf.is_file():
        return {"name": "pdf", "status": "FAIL", "error": "report/main.pdf does not exist"}
    info = run_cmd(["pdfinfo", str(pdf)], timeout=30)
    pages = None
    if info.get("returncode") == 0:
        for line in (info.get("stdout_tail") or "").splitlines():
            if line.lower().startswith("pages:"):
                try:
                    pages = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pages = None
    readable = info.get("returncode") == 0 and pages is not None and pages >= 1
    return {
        "name": "pdf",
        "status": "PASS" if readable else "FAIL",
        "path": str(pdf.relative_to(ROOT)),
        "bytes": pdf.stat().st_size,
        "pages": pages,
        "pdfinfo": info,
    }


def check_git() -> dict[str, Any]:
    inside = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], timeout=20)
    if inside.get("returncode") != 0:
        return {"name": "git", "status": "FAIL", "error": "not a git work tree", "detail": inside}
    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=20)
    sha = run_cmd(["git", "rev-parse", "HEAD"], timeout=20)
    jaffe = run_cmd(["git", "ls-files", "benchmarks/jaffe/data"], timeout=20)
    jaffe_files = [ln for ln in (jaffe.get("stdout_tail") or "").splitlines() if ln.strip()]
    jaffe_ok = all(
        Path(name).name == ".gitignore" or name.endswith(".gitignore") for name in jaffe_files
    )
    head = (sha.get("stdout_tail") or "").strip()
    if sha.get("returncode") != 0:
        status = "SKIPPED"
        head = "no commits yet"
    elif not jaffe_ok:
        status = "FAIL"
    else:
        status = "PASS"
    return {
        "name": "git",
        "status": status,
        "branch": (branch.get("stdout_tail") or "").strip(),
        "head": head,
        "jaffe_tracked": jaffe_files,
        "jaffe_images_absent": jaffe_ok,
        "note": "Full remote verification is recorded after push; this check is local.",
    }


def write_reports(checks: list[dict[str, Any]]) -> None:
    when = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {"when": when, "root": str(ROOT), "checks": checks}
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Validation report",
        "",
        f"Generated by `scripts/validate_project.py` at {when}.",
        "Outcomes below are from this run. Failed and skipped checks are kept.",
        "",
        "| Check | Status | Notes |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        name = check.get("name", "")
        status = check.get("status", "UNKNOWN")
        note_bits = []
        if name == "syntax":
            note_bits.append(f"{check.get('n_files', 0)} files")
            if check.get("failures"):
                note_bits.append(f"failures={check['failures']}")
        elif name == "pytest":
            note_bits.append(f"returncode={check.get('returncode')}")
            if check.get("error"):
                note_bits.append(str(check["error"]))
        elif name == "manifests":
            note_bits.append(f"present={check.get('present')}")
            if check.get("missing"):
                note_bits.append(f"missing={check['missing']}")
        elif name == "checksums":
            note_bits.append(", ".join(f"{row['file']}:{row['status']}" for row in check.get("files", [])))
        elif name == "runs":
            note_bits.append(f"dirs={check.get('n_directories')}; {check.get('counts')}")
        elif name == "traceability":
            note_bits.append(f"index_rows={check.get('n_index_rows')}")
            if check.get("missing_run_dirs"):
                note_bits.append(f"missing_dirs={check['missing_run_dirs']}")
        elif name == "tables_figures_tex":
            if check.get("missing"):
                note_bits.append(f"missing={check['missing']}")
            if check.get("main_tex_filler_tokens"):
                note_bits.append(f"filler={check['main_tex_filler_tokens']}")
            if not note_bits:
                note_bits.append("required tables/figures present; no TODO/TBD/Lorem in main.tex")
        elif name == "pdf":
            note_bits.append(f"pages={check.get('pages')}; bytes={check.get('bytes')}")
            if check.get("error"):
                note_bits.append(str(check["error"]))
        elif name == "git":
            note_bits.append(f"branch={check.get('branch')}; head={check.get('head')}; jaffe_ok={check.get('jaffe_images_absent')}")
            if check.get("error"):
                note_bits.append(str(check["error"]))
        note = "; ".join(note_bits) if note_bits else ""
        lines.append(f"| {name} | {status} | {note} |")
    lines.extend(
        [
            "",
            "Pytest stdout (tail):",
            "",
            "```",
            next((c.get("stdout_tail") or "") for c in checks if c.get("name") == "pytest"),
            "```",
            "",
            "pdfinfo stdout (tail):",
            "",
            "```",
            next((c.get("pdfinfo", {}).get("stdout_tail") or c.get("error") or "") for c in checks if c.get("name") == "pdf"),
            "```",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    checks = [
        check_syntax(),
        check_tests(),
        check_manifests(),
        check_checksums(),
        check_runs(),
        check_traceability(),
        check_tables_figures(),
        check_pdf(),
        check_git(),
    ]
    write_reports(checks)
    print(json.dumps({c["name"]: c["status"] for c in checks}, indent=2))
    print(f"wrote {REPORT_MD}")
    return 0 if all(c["status"] in {"PASS", "PASS_WITH_SKIP", "SKIPPED"} for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
