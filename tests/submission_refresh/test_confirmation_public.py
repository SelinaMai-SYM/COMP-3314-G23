"""Archival seed evidence preserves the original block after raw-path removal."""
import csv
import json
from pathlib import Path
import pytest
from experiments.subset_search import aggregate,confirmation_public as public
from experiments.submission_refresh.core import atomic_json,digest,identity


@pytest.fixture
def frozen(tmp_path,monkeypatch):
    root=tmp_path/'checkout';out=root/'results/subset_search';out.mkdir(parents=True)
    store=tmp_path/'external objects';store.mkdir()
    old=root/'results/old/trials.csv';old.parent.mkdir()
    with old.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['seed','acc','nmi']);writer.writeheader()
        writer.writerows([{'seed':seed,'acc':.5,'nmi':.6} for seed in [0,17,1000000]])
    atomic_json(out/'winner_lock.json',{'winners':[{'config_id':'fixed-winner'}]})
    monkeypatch.setattr(aggregate,'ROOT',root);monkeypatch.setattr(public,'ROOT',root)
    ns=aggregate.confirmation_namespace(store,out,historical_paths=[old])
    return root,out,store,old,ns


def receipt(tmp_path,out,store):
    value={'schema':'public-scientific-archive-receipt-v1','verified':True,'archive_id':'seed-fixture',
        'archive_sha256':'a'*64,'bytes':123,'recovered_objects':1,'recovered_extra_files':3,'recovery_proof_sha256':'b'*64,
        'raw_release_inputs':{'source_records':{'sha256':'c'*64,'uncompressed_sha256':'d'*64},
            'current_release_manifest':{'sha256':'e'*64},'evidence_manifest':{'sha256':'f'*64},
            'artifact_manifests':{'refresh_sha256':'0'*64,'subset_sha256':'1'*64},
            'seed_inventory_proof':{'sha256':digest(store/'confirmation'/public.PREPARED)},
            'original_namespace':{'sha256':digest(out/'confirmation_seed_namespace.json')}}}
    path=tmp_path/'receipt.json';path.write_text(json.dumps(value));return path


def test_explicit_preparation_and_public_resume_preserve_frozen_block(frozen,tmp_path,monkeypatch):
    root,out,store,old,original=frozen
    raw=(out/'confirmation_seed_namespace.json').read_bytes();lock=(out/'winner_lock.json').read_bytes()
    prepared=public.prepare_seed_inventory_proof(store,out)
    assert prepared['observed_historical_rounding_seeds']==[0,17,1000000]
    assert prepared['seed_block']['first']==1000050
    ref=prepared['archived_seed_sources'][0]
    assert ref['original_format']=='.csv' and ref['relative_path'].endswith('.bin')
    assert (store/ref['relative_path']).read_bytes()==old.read_bytes()
    assert 'path' not in ref and 'kind' not in ref
    proof=receipt(tmp_path,out,store);old.unlink()
    # Resume preparation uses the already sealed private record, not new paths.
    assert public.prepare_seed_inventory_proof(store,out)==prepared
    projected=public.project_confirmation_namespace(store,out,archive_receipt=proof,root=root)
    assert projected['version']==3 and projected['first']==original['first']
    assert projected['seeds']==original['seeds'] and projected['winner_lock_sha256']==original['winner_lock_sha256']
    backup=store/'confirmation'/('seed_namespace.original.'+projected['original_namespace_sha256']+'.v2.json')
    assert backup.read_bytes()==raw and (out/'winner_lock.json').read_bytes()==lock
    payload=(out/public.PROOF).read_text()
    assert 'results/old/trials.csv' not in payload and 'historical_inventory' not in projected
    def denied(*args,**kwargs):raise AssertionError('public resume must not scan raw history')
    monkeypatch.setattr(aggregate,'scan_historical_rounding_seeds',denied)
    assert aggregate.confirmation_namespace(store,out)==projected
    assert public.project_confirmation_namespace(store,out,archive_receipt=proof,root=root)==projected


def test_changed_original_history_blocks_preparation(frozen):
    root,out,store,old,namespace=frozen
    old.write_text('seed,acc,nmi\n99,.5,.6\n')
    with pytest.raises(ValueError,match='historical seed source changed'):public.prepare_seed_inventory_proof(store,out)
    assert not (store/'confirmation'/public.PREPARED).exists()
    assert json.loads((out/'confirmation_seed_namespace.json').read_text())==namespace


def test_archive_mismatch_blocks_public_namespace_publication(frozen,tmp_path):
    root,out,store,old,namespace=frozen
    public.prepare_seed_inventory_proof(store,out);path=receipt(tmp_path,out,store)
    value=json.loads(path.read_text());value['raw_release_inputs']['seed_inventory_proof']['sha256']='0'*64;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='does not cover exact seed'):public.project_confirmation_namespace(store,out,archive_receipt=path,root=root)
    assert not (out/public.PROOF).exists() and json.loads((out/'confirmation_seed_namespace.json').read_text())==namespace


def test_missing_exact_archived_source_bytes_block_projection(frozen,tmp_path):
    root,out,store,old,namespace=frozen
    prepared=public.prepare_seed_inventory_proof(store,out);path=receipt(tmp_path,out,store)
    (store/prepared['archived_seed_sources'][0]['relative_path']).unlink();old.unlink()
    with pytest.raises(ValueError,match='source bytes are missing or corrupt'):
        public.project_confirmation_namespace(store,out,archive_receipt=path,root=root)
    assert not (out/public.PROOF).exists()


def test_public_proof_tampering_fails_without_reselecting(frozen,tmp_path):
    root,out,store,old,namespace=frozen
    public.prepare_seed_inventory_proof(store,out);path=receipt(tmp_path,out,store)
    public.project_confirmation_namespace(store,out,archive_receipt=path,root=root)
    with (out/public.PROOF).open('a') as stream:stream.write(' ')
    with pytest.raises(ValueError,match='seed proof hash mismatch'):aggregate.confirmation_namespace(store,out)
    assert json.loads((out/'confirmation_seed_namespace.json').read_text())['first']==namespace['first']
