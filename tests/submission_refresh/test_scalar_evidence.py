import csv,json,shutil
from pathlib import Path
import pytest
from experiments.submission_refresh import scalar_evidence

def fixture_release(tmp_path,monkeypatch):
    project=Path(__file__).resolve().parents[2];root=tmp_path/'checkout with spaces'
    for path in ['configs/v3/paper_reference.yaml','configs/submission_refresh/selection.yaml']:
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(project/path,target)
    monkeypatch.setattr(scalar_evidence,'ROOT',root)
    folder=tmp_path/'artifacts/baseline/test-only';folder.mkdir(parents=True)
    record={'dataset':'JAFFE','method':'lda_existing','config_id':'test-only|limit30','status':'COMPLETED','trials':[{'seed':i,'acc':.7,'nmi':.8} for i in range(50)],'max_iter':30}
    (folder/'record.json').write_text(json.dumps(record))
    scalar_evidence.freeze(tmp_path/'artifacts',root/'results/submission_refresh')
    return root,root/'configs/submission_refresh/evidence_manifest.json'

def test_new_evidence_rebuild_needs_no_objects_or_data(tmp_path,monkeypatch):
    root,manifest=fixture_release(tmp_path,monkeypatch);shutil.rmtree(tmp_path/'artifacts')
    out=root/'rebuilt';scalar_evidence.rebuild(manifest,out)
    row=list(csv.DictReader((out/'baseline_diagnostics.csv').open()))[0]
    assert float(row['acc_mean'])==pytest.approx(70.)
    assert float(row['nmi_mean'])==pytest.approx(80.)
    assert row['variability_scope'].startswith('50 separately fitted')
    assert json.loads((out/'extension_gate.json').read_text())['decision']=='INCOMPLETE_OR_NUMERICALLY_UNCERTIFIED'
    scalar_evidence.rebuild(manifest,out)

def test_evidence_hash_failure_does_not_touch_unknown_output(tmp_path,monkeypatch):
    root,manifest=fixture_release(tmp_path,monkeypatch)
    source=root/'results/submission_refresh/baseline_records.public.v2.jsonl.gz';source.write_bytes(b'corrupt')
    out=root/'user output';out.mkdir();(out/'keep').write_text('keep')
    with pytest.raises(ValueError,match='hash mismatch'):scalar_evidence.rebuild(manifest,out)
    assert list(out.iterdir())==[out/'keep']


def test_freeze_duplicate_failure_preserves_previous_release(tmp_path,monkeypatch):
    root,manifest=fixture_release(tmp_path,monkeypatch)
    raw=root/'results/submission_refresh/baseline_records.public.v2.jsonl.gz'
    previous=(manifest.read_bytes(),raw.read_bytes())
    record=tmp_path/'artifacts/baseline/test-only/record.json'
    (record.parent/'duplicate.json').write_bytes(record.read_bytes())
    with pytest.raises(ValueError,match='duplicate baseline'):scalar_evidence.freeze(tmp_path/'artifacts',raw.parent)
    assert previous==(manifest.read_bytes(),raw.read_bytes())


def test_source_native_is_diagnostic_and_fixed_space_native_has_no_SD(tmp_path,monkeypatch):
    root,manifest=fixture_release(tmp_path,monkeypatch)
    folder=tmp_path/'artifacts/baseline/test-only';path=folder/'record.json';record=json.loads(path.read_text())
    record['diagnostics']=[{'seed':i,'inertia':float(50-i)} for i in range(50)]
    record['trials']=[{'seed':i,'acc':i/100.,'nmi':.8} for i in range(50)];path.write_text(json.dumps(record))
    fixed={**record,'method':'kmeans','config_id':'fixed-space','trials':[dict(t,inertia=50-t['seed']) for t in record['trials']]}
    (folder/'fixed.json').write_text(json.dumps(fixed))
    scalar_evidence.freeze(tmp_path/'artifacts',root/'results/submission_refresh');out=root/'rebuilt';scalar_evidence.rebuild(manifest,out)
    diagnostic=list(csv.DictReader((out/'baseline_source_native_diagnostics.csv').open()))[0]
    assert diagnostic['pool']=='diagnostic_only' and diagnostic['selected_seed']=='49'
    assert diagnostic['acc_sd']=='' and diagnostic['nmi_sd']==''
    endpoint=list(csv.DictReader((out/'baseline_endpoint_comparison.csv').open()))
    lda_native=next(r for r in endpoint if r['method']=='lda_existing' and r['endpoint']=='native_best_of_50')
    assert lda_native['status']=='UNAVAILABLE_CROSS_SUBSPACE_OBJECTIVE' and lda_native['acc_mean']==''
    fixed_native=next(r for r in endpoint if r['method']=='kmeans' and r['endpoint']=='native_best_of_50')
    assert fixed_native['selected_seed']=='49' and fixed_native['acc_sd']==''


def test_unlocked_evidence_input_is_rejected(tmp_path,monkeypatch):
    root,manifest=fixture_release(tmp_path,monkeypatch);record=json.loads(manifest.read_text())
    record['baseline_file']='results/unlocked.gz';manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='not hash-locked'):scalar_evidence.rebuild(manifest,root/'rebuilt')
