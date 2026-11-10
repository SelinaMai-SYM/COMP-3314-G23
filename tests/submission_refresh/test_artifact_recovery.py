import json,tarfile,io
from pathlib import Path
import numpy as np
import pytest
from experiments.submission_refresh import export_artifacts
from experiments.submission_refresh.core import ArtifactStore,atomic_json

def test_full_array_and_logical_metadata_recover(tmp_path,monkeypatch):
    root=tmp_path/'checkout';monkeypatch.setattr(export_artifacts,'ROOT',root)
    store=ArtifactStore(tmp_path/'durable');array=np.arange(12.).reshape(6,2);ref=store.put(array)
    record={'objects':{'G':ref},'status':'COMPLETED_TEST_FIXTURE'};rr=store.put(record)
    atomic_json(root/'results/subset_search/artifact_manifest.json',{'records':[{'record':'subset/example/representation.json','object':rr}]})
    archive=tmp_path/'archive.tar.gz';result=export_artifacts.export(store.root,archive)
    assert result['verified']
    recovered=tmp_path/'recovered store';export_artifacts.recover(archive,recovered)
    np.testing.assert_array_equal(ArtifactStore(recovered).get(ref),array)
    assert json.loads((recovered/'subset/example/representation.json').read_text())==record
    with pytest.raises(ValueError,match='already exist'):export_artifacts.recover(archive,recovered)

def test_corruption_fails_before_recovery_target_exists(tmp_path,monkeypatch):
    root=tmp_path/'checkout';monkeypatch.setattr(export_artifacts,'ROOT',root)
    store=ArtifactStore(tmp_path/'durable');ref=store.put(np.arange(4.))
    atomic_json(root/'results/subset_search/artifact_manifest.json',{'records':[{'record':'test.json','object':store.put({'objects':{'F':ref}})}]})
    original=tmp_path/'original.tar.gz';export_artifacts.export(store.root,original)
    broken=tmp_path/'broken.tar.gz'
    with tarfile.open(original) as source,tarfile.open(broken,'w:gz') as target:
        for info in source.getmembers():
            data=source.extractfile(info).read()
            if info.name==ref['path']:data=b'corruption';info.size=len(data)
            target.addfile(info,io.BytesIO(data))
    dest=tmp_path/'new'
    with pytest.raises(ValueError,match='corrupt archive'):export_artifacts.recover(broken,dest)
    assert not dest.exists()


def test_manifest_object_is_available_after_recovery(tmp_path,monkeypatch):
    root=tmp_path/'checkout';monkeypatch.setattr(export_artifacts,'ROOT',root);store=ArtifactStore(tmp_path/'durable')
    rr=store.put({'status':'fixture'});atomic_json(root/'results/subset_search/artifact_manifest.json',{'records':[{'record':'one.json','object':rr}]})
    archive=tmp_path/'archive.tar.gz';result=export_artifacts.export(store.root,archive);dest=tmp_path/'recovered'
    export_artifacts.recover(archive,dest)
    assert ArtifactStore(dest).get(result['export_manifest_object'])['schema']=='recoverable-scientific-export-v1'


def test_logical_conflict_cannot_replace_existing_archive(tmp_path,monkeypatch):
    root=tmp_path/'checkout';monkeypatch.setattr(export_artifacts,'ROOT',root);store=ArtifactStore(tmp_path/'durable')
    one=store.put({'n':1});two=store.put({'n':2});archive=tmp_path/'archive.tar.gz';archive.write_bytes(b'prior archive')
    atomic_json(root/'results/subset_search/artifact_manifest.json',{'records':[{'record':'same.json','object':one},{'record':'same.json','object':two}]})
    with pytest.raises(ValueError,match='conflicting logical'):export_artifacts.export(store.root,archive)
    assert archive.read_bytes()==b'prior archive'
