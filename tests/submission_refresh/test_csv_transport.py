"""CSV transport preserves exact logical bytes and fails before publication."""
import csv
import gzip
import hashlib
import importlib.util
from pathlib import Path
import pytest
from experiments.submission_refresh import csv_transport as transport

PAYLOAD=b'key,value\r\n0,"line one\r\nline two"\r\n1,caf\xc3\xa9\r\n'


def sha(value):return hashlib.sha256(value).hexdigest()


def test_plain_and_gzip_readers_preserve_utf8_multiline_and_crlf_bytes(tmp_path):
    plain=tmp_path/'plain.csv';compressed=tmp_path/'compressed.csv.gz'
    plain.write_bytes(PAYLOAD);compressed.write_bytes(gzip.compress(PAYLOAD,mtime=0))
    assert transport.resolve_csv(plain)==plain
    assert transport.resolve_csv(compressed.with_suffix(''))==compressed
    assert transport.resolve_csv(compressed)==compressed
    for source in [plain,compressed.with_suffix(''),compressed]:
        with transport.open_csv(source) as stream:assert stream.read()==PAYLOAD.decode('utf-8')
        with transport.open_csv(source,'r') as stream:
            assert list(csv.reader(stream))==[['key','value'],['0','line one\r\nline two'],['1','caf\u00e9']]
    for source in [plain,compressed]:
        destination=tmp_path/(source.stem.replace('.csv','')+'-materialized.csv')
        assert transport.copy_plain_csv(source,destination)==destination
        assert destination.read_bytes()==PAYLOAD
    with pytest.raises(ValueError,match='read-only'):
        with transport.open_csv(plain,'w'):pass
    assert plain.read_bytes()==PAYLOAD


def test_optional_missing_and_required_missing_are_distinct(tmp_path):
    for path in [tmp_path/'absent.csv',tmp_path/'absent.csv.gz']:
        assert transport.resolve_csv(path) is None
        with pytest.raises(FileNotFoundError):transport.resolve_csv(path,required=True)


def test_both_forms_are_ambiguous_even_when_actual_gzip_is_requested(tmp_path):
    plain=tmp_path/'records.csv';compressed=tmp_path/'records.csv.gz'
    plain.write_bytes(PAYLOAD);compressed.write_bytes(gzip.compress(PAYLOAD,mtime=0));before=compressed.read_bytes()
    for source in [plain,compressed]:
        with pytest.raises(ValueError,match='ambiguous'):transport.resolve_csv(source)
        with pytest.raises(ValueError,match='ambiguous'):
            with transport.open_csv(source):pass
    assert plain.read_bytes()==PAYLOAD and compressed.read_bytes()==before


@pytest.mark.parametrize('invalid',['directory','dangling_symlink'])
def test_invalid_existing_plain_path_never_falls_back_to_valid_gzip(tmp_path,invalid):
    plain=tmp_path/'records.csv';compressed=tmp_path/'records.csv.gz'
    if invalid=='directory':plain.mkdir()
    else:plain.symlink_to('missing-plain-source')
    compressed.write_bytes(gzip.compress(PAYLOAD,mtime=0));before=compressed.read_bytes()
    for source in [plain,compressed]:
        with pytest.raises(ValueError,match='ambiguous'):transport.resolve_csv(source)
    assert compressed.read_bytes()==before
    compressed.unlink()
    with pytest.raises(ValueError,match='not a readable file'):transport.resolve_csv(plain)
    assert plain.is_dir() if invalid=='directory' else plain.is_symlink()


def test_packing_is_deterministic_and_records_both_logical_and_transport_hashes(tmp_path):
    one=tmp_path/'one';two=tmp_path/'two';one.mkdir();two.mkdir()
    (one/'first.csv').write_bytes(PAYLOAD);(two/'different-name.csv').write_bytes(PAYLOAD)
    a=transport.pack_large_csvs(one,min_bytes=0)[0];b=transport.pack_large_csvs(two,min_bytes=0)[0]
    first=one/a['transport_path'];second=two/b['transport_path']
    assert first.read_bytes()==second.read_bytes()
    assert a['status']==b['status']=='PACKED_GZIP'
    assert a['uncompressed_sha256']==b['uncompressed_sha256']==sha(PAYLOAD)
    assert a['uncompressed_bytes']==b['uncompressed_bytes']==len(PAYLOAD)
    assert a['compressed_sha256']==b['compressed_sha256']==sha(first.read_bytes())
    assert a['compressed_bytes']==first.stat().st_size and a['row_count']==2 and a['column_count']==2
    assert gzip.decompress(first.read_bytes())==PAYLOAD
    assert not (one/'first.csv').exists() and not (two/'different-name.csv').exists()
    assert first.read_bytes()[4:8]==b'\0\0\0\0'  # Fixed gzip modification time.


def test_existing_gzip_is_inventoried_without_rewriting_it(tmp_path):
    compressed=tmp_path/'records.csv.gz';compressed.write_bytes(gzip.compress(PAYLOAD,mtime=123));before=compressed.read_bytes()
    record=transport.pack_large_csvs(tmp_path,min_bytes=0)[0]
    assert record['status']=='EXISTING_GZIP'
    assert record['csv_path']=='records.csv' and record['transport_path']=='records.csv.gz'
    assert record['compressed_sha256']==sha(before) and record['uncompressed_sha256']==sha(PAYLOAD)
    assert record['compressed_bytes']==len(before) and record['row_count']==2
    assert compressed.read_bytes()==before and not (tmp_path/'records.csv').exists()


def test_small_plain_and_unselected_invalid_csv_are_left_untouched(tmp_path):
    selected=tmp_path/'selected.csv';other=tmp_path/'unselected.csv'
    selected.write_bytes(PAYLOAD);other.write_bytes(b'not a valid CSV body\xff')
    records=transport.pack_large_csvs(tmp_path,min_bytes=len(PAYLOAD)+1,names=['selected.csv'])
    assert records[0]['status']=='UNCHANGED_PLAIN' and records[0]['compressed_sha256'] is None
    assert selected.read_bytes()==PAYLOAD and other.read_bytes()==b'not a valid CSV body\xff'
    transport.pack_large_csvs(tmp_path,min_bytes=0,names=['selected.csv'])
    assert not selected.exists() and (tmp_path/'selected.csv.gz').is_file()
    assert other.read_bytes()==b'not a valid CSV body\xff' and not (tmp_path/'unselected.csv.gz').exists()


@pytest.mark.parametrize('invalid',[
    b'',b'key,value\n',b'key,key\n1,2\n',b'key,value\n1\n',
    b'key,value\n1,"unterminated\n',b'key,value\n1,nu\0l\n',b'key,value\n1,\xff\n'])
def test_invalid_selected_csv_prevents_publication_of_every_staged_file(tmp_path,invalid):
    valid=tmp_path/'a-valid.csv';bad=tmp_path/'z-invalid.csv'
    valid.write_bytes(PAYLOAD);bad.write_bytes(invalid)
    with pytest.raises(ValueError):transport.pack_large_csvs(tmp_path,min_bytes=0)
    assert valid.read_bytes()==PAYLOAD and bad.read_bytes()==invalid
    assert not list(tmp_path.glob('*.csv.gz'))
    assert not list(tmp_path.glob('.csv-transport-*'))


def test_corrupt_gzip_never_replaces_an_existing_plain_destination(tmp_path):
    source=tmp_path/'broken.csv.gz';source.write_bytes(gzip.compress(PAYLOAD,mtime=0)[:-5])
    destination=tmp_path/'materialized.csv';destination.write_bytes(b'keep,original\n1,2\n');before=destination.read_bytes()
    with pytest.raises(ValueError,match='invalid or corrupt'):transport.copy_plain_csv(source,destination)
    assert destination.read_bytes()==before and not list(tmp_path.glob('.csv-copy-*'))
    with pytest.raises(ValueError,match='invalid or corrupt'):transport.pack_large_csvs(tmp_path,min_bytes=0,names=['broken.csv'])
    assert source.exists()


def test_unknown_existing_transport_is_never_overwritten(tmp_path):
    plain=tmp_path/'records.csv';compressed=tmp_path/'records.csv.gz'
    plain.write_bytes(PAYLOAD);compressed.write_bytes(b'unknown existing transport')
    with pytest.raises(ValueError,match='ambiguous'):transport.pack_large_csvs(tmp_path,min_bytes=0)
    assert plain.read_bytes()==PAYLOAD and compressed.read_bytes()==b'unknown existing transport'
    source=tmp_path/'source.csv';source.write_bytes(PAYLOAD)
    with pytest.raises(ValueError,match='ambiguous'):transport.copy_plain_csv(source,plain)
    assert plain.read_bytes()==PAYLOAD and compressed.read_bytes()==b'unknown existing transport'


def test_concurrent_unknown_target_is_not_replaced_or_followed_by_plain_deletion(tmp_path,monkeypatch):
    plain=tmp_path/'records.csv';plain.write_bytes(PAYLOAD);original_link=transport.os.link
    def another_publisher(source,target):
        Path(target).write_bytes(b'concurrent unknown transport')
        return original_link(source,target)
    monkeypatch.setattr(transport.os,'link',another_publisher)
    with pytest.raises(FileExistsError):transport.pack_large_csvs(tmp_path,min_bytes=0)
    assert plain.read_bytes()==PAYLOAD
    assert (tmp_path/'records.csv.gz').read_bytes()==b'concurrent unknown transport'


@pytest.mark.parametrize('name',['../escape.csv','/tmp/escape.csv','sub/escape.csv','','.','..','records.txt','records.csv.gzip'])
def test_pack_names_must_be_csv_basenames(tmp_path,name):
    plain=tmp_path/'valid.csv';plain.write_bytes(PAYLOAD)
    with pytest.raises(ValueError):transport.pack_large_csvs(tmp_path,min_bytes=0,names=[name])
    assert plain.read_bytes()==PAYLOAD and not list(tmp_path.glob('*.gz'))


def test_duplicate_logical_names_and_invalid_thresholds_are_rejected(tmp_path):
    plain=tmp_path/'records.csv';plain.write_bytes(PAYLOAD)
    with pytest.raises(ValueError,match='duplicate logical'):transport.pack_large_csvs(tmp_path,min_bytes=0,names=['records.csv','records.csv.gz'])
    for threshold in [-1,True,1.5]:
        with pytest.raises(ValueError,match='nonnegative integer'):transport.pack_large_csvs(tmp_path,min_bytes=threshold)
    assert plain.read_bytes()==PAYLOAD


def test_transport_module_can_load_standalone_before_project_dependencies():
    spec=importlib.util.spec_from_file_location('standalone_csv_transport',transport.__file__)
    standalone=importlib.util.module_from_spec(spec);spec.loader.exec_module(standalone)
    assert standalone.DEFAULT_MIN_BYTES==90*1024**2
    assert callable(standalone.resolve_csv) and callable(standalone.copy_plain_csv)
