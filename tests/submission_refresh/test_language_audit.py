"""Language inventory fixtures use fake Git/PDF tools, never external jobs."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import pytest


@pytest.fixture
def audit_module():
    path=Path(__file__).resolve().parents[2]/'scripts/submission_refresh/language_audit.py'
    spec=importlib.util.spec_from_file_location('language_audit_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.fixture
def publication(tmp_path,monkeypatch,audit_module):
    root=tmp_path/'publication';root.mkdir()
    def inventory(_root):
        return {'tracked':{str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()},
            'pending':set(),'head':'a'*40,'status':''}
    monkeypatch.setattr(audit_module,'_git_inventory',inventory)
    return root,root/'audit.json',audit_module


def result(output):return json.loads(output.read_text())


def test_decodes_json_jsonl_gzip_and_notebook_values_once(publication):
    root,output,audit=publication
    foreign=chr(0x4e2d)+chr(0x6587)
    (root/'record.json').write_text(json.dumps({'message':foreign},ensure_ascii=True))
    serialized=(json.dumps({'note':foreign},ensure_ascii=True)+'\n').encode()
    compressed=gzip.compress(serialized,mtime=0)
    (root/'records.jsonl.gz').write_bytes(compressed)
    (root/'notebook.ipynb').write_text(json.dumps({'cells':[{'cell_type':'markdown','source':[foreign]}]},ensure_ascii=True))
    assert not audit.audit(root,output)
    data=result(output)
    decoded=[flag for flag in data['remaining_flags'] if flag['kind']=='DECODED_STRUCTURED_VALUES']
    assert {flag['path'] for flag in decoded}=={'record.json','records.jsonl.gz','notebook.ipynb'}
    assert all(flag['count']==2 for flag in decoded)
    assert any('cells' in context['value_path'] for flag in decoded for context in flag['contexts'])
    row=next(row for row in data['compressed_records'] if row['path']=='records.jsonl.gz')
    assert row['compressed_sha256']==hashlib.sha256(compressed).hexdigest()
    assert row['uncompressed_sha256']==hashlib.sha256(serialized).hexdigest()


def test_preserves_literal_backslash_escapes_and_original_files(publication):
    root,output,audit=publication
    path=root/'literal.json'
    raw=json.dumps({'raw_string':r'\u4e2d\u6587'}).encode()
    path.write_bytes(raw)
    assert audit.audit(root,output)
    assert path.read_bytes()==raw
    assert not result(output)['remaining_flags']


@pytest.mark.parametrize('suffix',['.txt','.bib','.sty','.jsonl','.tsv','.rst','.sh','.unknown'])
def test_undecodable_text_is_never_silently_dropped(publication,suffix):
    root,output,audit=publication
    name='undecodable'+suffix
    (root/name).write_bytes(b'\xff')
    assert not audit.audit(root,output)
    data=result(output)
    assert any(error.get('path')==name for error in data['errors'])
    row=next(row for row in data['file_inventory'] if row['path']==name)
    assert row['classification']=='UNDECODABLE_OR_INVALID_TEXT'
    assert row['sha256']==hashlib.sha256(b'\xff').hexdigest()


def test_textless_pdf_requires_manual_review(publication,monkeypatch):
    root,output,audit=publication
    (root/'image-only.pdf').write_bytes(b'%PDF-fixture')
    monkeypatch.setattr(audit.subprocess,'run',lambda argv,**kwargs:subprocess.CompletedProcess(argv,0,b'',b''))
    assert not audit.audit(root,output)
    data=result(output)
    assert data['pdf_extraction'][0]['extraction_status']=='NO_TEXT_MANUAL_REVIEW_REQUIRED'
    assert data['manual_review_required'][0]['reason']=='PDF_NO_EXTRACTABLE_TEXT'
    assert data['language_certified'] is False


def test_pdf_timeout_is_recorded_without_claiming_success(publication,monkeypatch):
    root,output,audit=publication
    (root/'timeout.pdf').write_bytes(b'%PDF-fixture')
    def timeout(argv,**kwargs):raise subprocess.TimeoutExpired(argv,kwargs['timeout'])
    monkeypatch.setattr(audit.subprocess,'run',timeout)
    assert not audit.audit(root,output,pdf_timeout=2)
    assert result(output)['errors'][0]['kind']=='PDF_EXTRACTION_FAILED'


def test_plain_file_hashes_dirty_state_and_change_detection_are_retained(publication,monkeypatch):
    root,output,audit=publication
    text=root/'a.txt';original=b'English prose.\r\n';text.write_bytes(original)
    (root/'z.pdf').write_bytes(b'%PDF-fixture')
    before_inventory=audit._git_inventory
    def dirty(path):return {**before_inventory(path),'status':' M a.txt\0'}
    monkeypatch.setattr(audit,'_git_inventory',dirty)
    def extract(argv,**kwargs):
        text.write_text('Changed English prose.\n')
        return subprocess.CompletedProcess(argv,0,b'English extracted text.',b'')
    monkeypatch.setattr(audit.subprocess,'run',extract)
    assert not audit.audit(root,output)
    data=result(output)
    row=next(row for row in data['file_inventory'] if row['path']=='a.txt')
    assert row['sha256']==hashlib.sha256(original).hexdigest()
    assert row['uncompressed_sha256']==row['sha256']
    assert row['unchanged_during_audit'] is False
    assert data['working_tree_dirty'] is True and data['inputs_unchanged'] is False
    assert any(error['kind']=='INPUTS_CHANGED_DURING_AUDIT' for error in data['errors'])
