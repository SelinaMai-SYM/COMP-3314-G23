from pathlib import Path
import gzip,hashlib,json,shutil
import pytest
from experiments.v3_reproduction.release import rebuild

ROOT=Path(__file__).resolve().parents[2]
@pytest.fixture
def release_copy(tmp_path):
    manifest=json.loads((ROOT/'configs/final/release_manifest.json').read_text())
    for name in manifest['files']:
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    p=tmp_path/'configs/final/release_manifest.json';p.write_text(json.dumps(manifest));return tmp_path,p,manifest


def test_hash_failure_preserves_existing_output(release_copy):
    root,path,m=release_copy;out=root/'existing';out.mkdir();(out/'keep').write_text('user-content')
    target=root/m['metadata_file'];target.write_bytes(target.read_bytes()+b'tamper')
    with pytest.raises(ValueError,match='hash mismatch'):rebuild(path,out)
    assert (out/'keep').read_text()=='user-content'
    assert list(out.iterdir())==[out/'keep']


def test_duplicate_primary_key_fails_even_with_consistent_hashes(release_copy):
    root,path,m=release_copy;p=root/m['trial_file']
    with gzip.open(p,'rb') as f:lines=[f.readline() for _ in range(51)]
    content=b''.join(lines+[lines[1]])
    with gzip.open(p,'wb') as f:f.write(content)
    m['files'][m['trial_file']]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();m['trial_sha256_uncompressed']=hashlib.sha256(content).hexdigest();path.write_text(json.dumps(m))
    out=root/'new-output'
    with pytest.raises(ValueError,match='duplicate trial primary key'):rebuild(path,out)
    assert not out.exists()


def test_unhashed_required_input_is_rejected_before_output(release_copy):
    root,path,m=release_copy;m['files'].pop(m['metadata_file']);path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='not covered by hashes'):rebuild(path,root/'output')
    assert not (root/'output').exists()


def test_empty_release_fails_before_output(release_copy):
    root,path,m=release_copy;p=root/m['trial_file']
    with gzip.open(p,'rb') as f:header=f.readline()
    with gzip.open(p,'wb') as f:f.write(header)
    m['files'][m['trial_file']]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();m['trial_sha256_uncompressed']=hashlib.sha256(header).hexdigest();path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='empty/missing'):rebuild(path,root/'output')
    assert not (root/'output').exists()
