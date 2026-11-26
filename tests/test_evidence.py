"""Archived evidence keeps exact identities and never replaces conflicting files."""
import gzip
import hashlib
import io
import json
import tarfile

import pytest

from experiments.evidence import INDEX, _process, prepare


def fixture(root, payloads=None):
    payloads = payloads or {"results/source.json": b'{"id": 7}\n', "results/trials.csv": b"seed,acc\n0,0.5\n"}
    archive = root / "results/evidence/scalars_and_metadata.tar.gz"
    archive.parent.mkdir(parents=True)
    with tarfile.open(archive, "w:gz") as tar:
        for name, data in payloads.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    spec = {"schema": "ssc-evidence-archive-v1", "archive": {
        "path": str(archive.relative_to(root)), "bytes": archive.stat().st_size,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "uncompressed_sha256": hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest()},
        "members": [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                    for name, data in payloads.items()]}
    index = root / INDEX
    index.parent.mkdir(parents=True)
    index.write_text(json.dumps(spec))
    return payloads, archive, index, spec


def test_lossless_restore_verification_and_idempotence(tmp_path):
    payloads, _, _, _ = fixture(tmp_path)
    assert _process(tmp_path, False) == {"members": 2, "restored": 0}
    assert not (tmp_path / "results/source.json").exists()
    assert prepare(tmp_path) == {"members": 2, "restored": 2}
    assert all((tmp_path / name).read_bytes() == data for name, data in payloads.items())
    assert prepare(tmp_path) == {"members": 2, "restored": 0}


def test_conflicting_local_file_is_preserved(tmp_path):
    _, _, _, _ = fixture(tmp_path)
    target = tmp_path / "results/source.json"
    target.write_text("user changes")
    with pytest.raises(ValueError, match="file preserved"):
        prepare(tmp_path)
    assert target.read_text() == "user changes"
    assert not (tmp_path / "results/trials.csv").exists()


def test_member_validation_precedes_any_restoration(tmp_path):
    _, _, index, spec = fixture(tmp_path)
    spec["members"][-1]["sha256"] = "0" * 64
    index.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="member hash mismatch"):
        prepare(tmp_path)
    assert not (tmp_path / "results/source.json").exists()


def test_corrupt_transport_is_rejected(tmp_path):
    _, archive, _, _ = fixture(tmp_path)
    archive.write_bytes(archive.read_bytes()[:-1] + b"x")
    with pytest.raises(ValueError, match="archive hash mismatch"):
        prepare(tmp_path)


def test_unsafe_member_path_is_rejected(tmp_path):
    fixture(tmp_path, {"../outside.json": b"{}"})
    with pytest.raises(ValueError, match="Invalid evidence path"):
        prepare(tmp_path)
    assert not (tmp_path.parent / "outside.json").exists()
