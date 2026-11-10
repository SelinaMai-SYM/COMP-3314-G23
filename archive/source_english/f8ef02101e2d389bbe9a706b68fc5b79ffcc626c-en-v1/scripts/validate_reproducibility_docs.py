#!/usr/bin/env python3
"""Check reproducibility README cross-references. Not a math-correctness audit."""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATASETS = ("ar", "jaffe", "orl", "umist", "binalpha", "msra50", "yaleb", "usps")
BASELINES = (
    "kmeans",
    "spectral_clustering",
    "pca_kmeans",
    "pca_spectral",
    "lda_kmeans",
    "lda_spectral",
    "llc",
    "spls",
)

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SHA256 = re.compile(r"\b[0-9a-f]{64}\b")
RUN_ID = re.compile(r"\b(?:\d{8}_\d{6}__[A-Za-z0-9_]+|D10_[A-Z0-9_]+)\b")
BACKTICK_PATH = re.compile(
    r"`((?:baselines|benchmarks|docs|SSC_method|results|runs|scripts|tests|report|configs|method_extension)/[A-Za-z0-9_./-]+)`"
)
SKIP_LINK_PREFIXES = ("http://", "https://", "mailto:", "#")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest_hashes() -> dict[str, set[str]]:
    """Map lowercase SHA-256 -> relative yaml paths that mention it."""
    found: dict[str, set[str]] = {}
    for yaml_path in ROOT.joinpath("benchmarks").rglob("*.yaml"):
        text = yaml_path.read_text(encoding="utf-8", errors="replace")
        rel = str(yaml_path.relative_to(ROOT))
        for match in SHA256.findall(text.lower()):
            found.setdefault(match, set()).add(rel)
    return found


def resolve_link(readme: Path, target: str) -> Path | None:
    raw = target.strip()
    if not raw or raw.startswith(SKIP_LINK_PREFIXES):
        return None
    raw = raw.split("#", 1)[0].strip()
    if not raw:
        return None
    return (readme.parent / raw).resolve()


def run_dirs() -> set[str]:
    names: set[str] = set()
    for parent in (ROOT / "runs", ROOT / "runs" / "repair_round1", ROOT / "runs" / "round2"):
        if not parent.is_dir():
            continue
        for child in parent.iterdir():
            if child.is_dir():
                names.add(child.name)
    return names


def registry_rows() -> dict[str, dict[str, str]]:
    path = ROOT / "results" / "round2" / "experiment_registry.csv"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["run_id"]: row for row in csv.DictReader(handle) if row.get("run_id")}


def collect_failures() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    dataset_readmes = []
    for name in DATASETS:
        path = ROOT / "benchmarks" / name / "README.md"
        if path.is_file():
            dataset_readmes.append(path)
        else:
            failures.append(f"missing dataset README: {path.relative_to(ROOT)}")

    baseline_readmes = []
    for name in BASELINES:
        path = ROOT / "baselines" / name / "README.md"
        if path.is_file():
            baseline_readmes.append(path)
        else:
            failures.append(f"missing baseline README: {path.relative_to(ROOT)}")

    extra_readmes = [
        ROOT / "README.md",
        ROOT / "baselines" / "README.md",
        ROOT / "benchmarks" / "README.md",
        ROOT / "SSC_method" / "README.md",
        ROOT / "results" / "README.md",
        ROOT / "method_extension" / "README.md",
    ]
    readmes = dataset_readmes + baseline_readmes + [p for p in extra_readmes if p.is_file()]

    manifest_hashes = load_manifest_hashes()
    known_runs = run_dirs()
    registry = registry_rows()
    seen_paths: set[str] = set()

    for readme in readmes:
        rel_readme = str(readme.relative_to(ROOT))
        text = readme.read_text(encoding="utf-8", errors="replace")

        for target in MD_LINK.findall(text):
            resolved = resolve_link(readme, target)
            if resolved is None:
                continue
            key = str(resolved)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                continue
            if not resolved.exists():
                failures.append(f"{rel_readme}: broken link {target!r}")

        for raw_path in BACKTICK_PATH.findall(text):
            candidate = ROOT / raw_path
            if candidate.exists() or candidate.is_symlink():
                continue
            # Directory prefixes in docs are fine if the leaf is a run id checked separately.
            if RUN_ID.search(raw_path):
                continue
            failures.append(f"{rel_readme}: missing path `{raw_path}`")

        for run_id in RUN_ID.findall(text):
            if run_id in known_runs:
                continue
            # Registry may list diagnostic JSON-only rows without a run directory.
            if run_id in registry:
                warnings.append(f"{rel_readme}: run_id {run_id} is in the registry but has no runs/ directory")
                continue
            failures.append(f"{rel_readme}: run_id not found on disk: {run_id}")

        for digest in SHA256.findall(text.lower()):
            if digest in manifest_hashes:
                continue
            warnings.append(
                f"{rel_readme}: SHA-256 {digest} is not in any benchmarks/*.yaml manifest"
            )

    # Recompute hashes for local files named by manifests when the file exists.
    for yaml_path in ROOT.joinpath("benchmarks").rglob("manifest*.yaml"):
        text = yaml_path.read_text(encoding="utf-8", errors="replace")
        pkg = yaml_path.parent
        recorded = SHA256.findall(text.lower())
        archive = re.search(r"archive_filename:\s*[\"']?([^\n\"']+)", text)
        if not recorded:
            continue
        candidates = list((pkg / "data").rglob("*")) if (pkg / "data").is_dir() else []
        for digest in recorded:
            matched = False
            for file_path in candidates:
                if not file_path.is_file() or file_path.name in {".gitignore"}:
                    continue
                if file_path.stat().st_size > 80 * 1024 * 1024:
                    continue
                try:
                    actual = sha256_file(file_path)
                except OSError:
                    continue
                if actual == digest:
                    matched = True
                    break
            if matched:
                continue
            # File may be absent (gitignored and not downloaded). That is not a doc failure
            # unless the README claims the file is present AND we can see it.
            if archive and any((pkg / "data").rglob(archive.group(1).split()[0])):
                failures.append(
                    f"{yaml_path.relative_to(ROOT)}: recorded SHA-256 {digest} does not match local archive"
                )

    return failures, warnings


def main() -> int:
    failures, warnings = collect_failures()
    print("validate_reproducibility_docs.py")
    print(f"workspace: {ROOT}")
    print(f"failures: {len(failures)}")
    print(f"warnings: {len(warnings)}")
    for item in failures:
        print(f"FAIL  {item}")
    for item in warnings:
        print(f"WARN  {item}")
    if failures:
        print("RESULT: FAIL (see FAIL lines; warnings are disclosed, not fatal)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
