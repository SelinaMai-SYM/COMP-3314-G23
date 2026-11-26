"""Verify and restore losslessly archived scalar evidence at its original paths."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INDEX = "configs/final/evidence_archive.json"


def _sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _path(root, name):
    relative = PurePosixPath(name)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in name
            or not relative.parts or relative.parts[0] != "results"):
        raise ValueError("Invalid evidence path: " + name)
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError("Evidence path leaves checkout: " + name)
    if any(p.is_symlink() for p in [target, *target.parents] if p != root):
        raise ValueError("Evidence paths cannot use symlinks: " + name)
    return target


def _process(root, restore):
    root = Path(root).resolve()
    index = root / INDEX
    if not index.exists():
        if (root / "results/evidence/scalars_and_metadata.tar.gz").exists():
            raise ValueError("Evidence archive index is missing")
        return {"members": 0, "restored": 0}
    spec = json.loads(index.read_text())
    if spec.get("schema") != "ssc-evidence-archive-v1":
        raise ValueError("Unsupported evidence archive schema")
    entries = spec["members"]
    expected = {entry["path"]: entry for entry in entries}
    if not expected or len(expected) != len(entries):
        raise ValueError("Empty or duplicate evidence members")
    targets = {name: _path(root, name) for name in expected}
    archive = _path(root, spec["archive"]["path"])
    if archive.stat().st_size != spec["archive"]["bytes"] or _sha(archive) != spec["archive"]["sha256"]:
        raise ValueError("Evidence archive hash mismatch")
    with gzip.open(archive, "rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != spec["archive"]["uncompressed_sha256"]:
            raise ValueError("Evidence archive uncompressed hash mismatch")

    def check_existing():
        for name, target in targets.items():
            if target.exists() and (not target.is_file() or target.stat().st_size != expected[name]["bytes"]
                                    or _sha(target) != expected[name]["sha256"]):
                raise ValueError("Existing evidence differs; file preserved: " + name)

    check_existing()
    restored = 0
    with tempfile.TemporaryDirectory(prefix=".evidence-", dir=root) as staging:
        staged = {}
        seen = set()
        with tarfile.open(archive, "r|gz") as stream:
            for member in stream:
                name = member.name
                if name not in expected or name in seen or not member.isfile():
                    raise ValueError("Unexpected, duplicate or non-file evidence member: " + name)
                seen.add(name)
                entry = expected[name]
                if member.size != entry["bytes"]:
                    raise ValueError("Evidence member size mismatch: " + name)
                payload = stream.extractfile(member)
                if payload is None:
                    raise ValueError("Unreadable evidence member: " + name)
                digest = hashlib.sha256()
                missing = restore and not targets[name].exists()
                path = Path(staging) / str(len(seen))
                with payload:
                    if missing:
                        with path.open("wb") as output:
                            for block in iter(lambda: payload.read(1024 * 1024), b""):
                                digest.update(block)
                                output.write(block)
                    else:
                        for block in iter(lambda: payload.read(1024 * 1024), b""):
                            digest.update(block)
                if digest.hexdigest() != entry["sha256"]:
                    raise ValueError("Evidence member hash mismatch: " + name)
                if missing:
                    staged[name] = path
        if seen != set(expected):
            raise ValueError("Evidence archive members are missing")
        check_existing()
        for name, path in staged.items():
            target = targets[name]
            target.parent.mkdir(parents=True, exist_ok=True)
            # Never overwrite a file created or edited during verification.
            os.link(path, target)
            restored += 1
    return {"members": len(expected), "restored": restored}


def prepare(root=ROOT):
    """Restore original bytes without changing scientific IDs or frozen hashes."""
    return _process(root, restore=True)


def archived_paths(root=ROOT):
    """Logical original paths included in tracked-history inventories."""
    index = Path(root) / INDEX
    return [entry["path"] for entry in json.loads(index.read_text())["members"]] if index.exists() else []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify", "prepare"])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(_process(args.root, restore=args.command == "prepare"), indent=2))


if __name__ == "__main__":
    main()
