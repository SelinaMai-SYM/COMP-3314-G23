"""Reconstruction rules and integrity checks that do not depend on scores."""
from pathlib import Path
import json
import numpy as np
import pytest

from benchmarks import DatasetUnavailable, load_dataset
from experiments.subset_search.catalogue import exact_deduplicate, proportional_quotas, draw_by_class, materialize


def test_first_occurrence_dedup_and_conflict():
    x=np.array([[2,1],[1,2],[2,1],[3,0]])
    keep, mapping=exact_deduplicate(x,np.array([0,1,0,1]))
    np.testing.assert_array_equal(keep,[0,1,3])
    np.testing.assert_array_equal(mapping,[0,1,0,2])
    with pytest.raises(ValueError,match="conflicting"):
        exact_deduplicate(x,np.array([0,1,1,1]))


def test_largest_remainder_quotas_and_one_rng():
    y=np.repeat(np.arange(3),[8,7,5])
    quotas=proportional_quotas(y,13)
    assert quotas == {0:5,1:5,2:3}
    a=draw_by_class(y,quotas,7)
    b=draw_by_class(y,quotas,7)
    np.testing.assert_array_equal(a,b)
    assert len(a)==len(np.unique(a))==13
    assert np.bincount(y[a]).tolist()==[5,5,3]
    assert all(np.all(np.diff(a[y[a]==k])>0) for k in quotas)


def test_strict_originals_remain_unavailable(tmp_path):
    for dataset in ["AR","UMIST","BinAlpha","MSRA50"]:
        with pytest.raises(DatasetUnavailable):
            load_dataset(dataset,root=tmp_path)


def test_parent_loaders_honor_explicit_root(tmp_path):
    for dataset,version in [("AR","lzuf_superset1680"),("UMIST","lzuf574"),("UMIST","roweis575"),("UMIST","zenodo3634017"),("MSRA50","ebsa16")]:
        with pytest.raises((DatasetUnavailable,FileNotFoundError)) as e:
            load_dataset(dataset,root=tmp_path,version=version)
        assert str(tmp_path) in str(e.value)


def test_available_catalogue_replay_and_seed0(monkeypatch):
    import os
    from experiments.subset_search.catalogue import REPO
    root=os.environ.get("COMP3314_DATA_ROOT")
    if not root:
        pytest.skip("integration check requires COMP3314_DATA_ROOT")
    catalogue=json.loads((REPO/"results/subset_search/candidate_catalogue.json").read_text())
    by_id={c["candidate_id"]:c for c in catalogue["candidates"]}
    for cid,n,k in [("AR_first7",840,120),("UMIST_LZUFE574_exact_dedup564",564,20),("BinAlpha_random_seed000",780,26),("MSRA25_EBSA_16x16",1799,12)]:
        X,y,meta=materialize(by_id[cid],root)
        assert len(X)==n and len(np.unique(y))==k
        assert np.isfinite(X).all()
    X,y,_=materialize(by_id["BinAlpha_random_seed000"],root)
    old_X,old_y,_=load_dataset("BinAlpha",root=Path(root)/"binalpha/data",version="letters26x30_seed0")
    np.testing.assert_array_equal(X,old_X)
    np.testing.assert_array_equal(y,old_y)
    assert X.min()==0 and X.max()==1
    X,y,meta=materialize(by_id["MSRA25_EBSA_16x16"],root)
    assert X.shape==(1799,256) and meta["original_spatial_size"]==[16,16]
    assert meta["duplicate_extra_rows"]==13
    assert np.bincount(y).tolist()==[175,154,113,178,186,159,179,128,133,131,128,135]


def test_subset_cache_identity_covers_behavior_environment_and_source(tmp_path,monkeypatch):
    import hashlib
    import experiments.subset_search.runner as runner
    import experiments.subset_search.catalogue as catalogue
    files=['SSC_method/optimizer.py','benchmarks/example.py',
           'experiments/subset_search/catalogue.py','experiments/subset_search/runner.py',
           'experiments/v2_kmeans_protocol/kmeans_trials.py','experiments/v2_kmeans_protocol/metrics.py',
           'experiments/submission_refresh/selection.py','configs/subset_search/protocol.yaml']
    for name in files:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('value=1\n')
    raw=tmp_path/'raw.bin';raw.write_bytes(b'raw source')
    manifest={'source_files':[{'path_relative_to_data_root':'raw.bin','sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}]}
    c={'candidate_id':'sample','manifest_sha256':'manifest','fingerprint':{'x_sha256':'features','y_sha256':'labels'}}
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(catalogue,'_manifest',lambda _:manifest)
    monkeypatch.setattr(runner,'environment_record',lambda:{'python':'test','packages':{'numpy':'fixed'}})
    initial=runner.scientific_cache_identity(c,tmp_path)
    (tmp_path/'SSC_method/optimizer.py').write_text('"""English editorial replacement."""\n# revised comment\nvalue=1\n')
    assert runner.scientific_cache_identity(c,tmp_path)==initial
    (tmp_path/'SSC_method/optimizer.py').write_text('value=2\n')
    assert runner.scientific_cache_identity(c,tmp_path)!=initial
    raw.write_bytes(b'changed source')
    with pytest.raises(ValueError,match='source hash mismatch'):
        runner.scientific_cache_identity(c,tmp_path)
