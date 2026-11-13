"""Metadata-only plain/gzip report transport fixtures."""
import csv
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from experiments.submission_refresh import reporting


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    return path


def packed(path):
    destination=path.with_suffix(path.suffix+'.gz')
    destination.write_bytes(gzip.compress(path.read_bytes(),mtime=0));path.unlink()
    return destination


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def report_fixture(root,compress=False):
    historical={'benchmark':'ORL','method':'ssc','endpoint':'mean_sample_sd_50','acc_mean':42.,'acc_sd':1.2,
        'nmi_mean':81.,'nmi_sd':2.3,'paper_ACC':76.,'paper_ACC_SD':1.6,'paper_NMI':88.6,'paper_NMI_SD':1.5,
        'D_max':34.,'D_mean':20.8,'solver_status_current_audit':'ITERATE_CONVERGED_UNCERTIFIED'}
    sources={
        'historical':('results/submission_refresh/joint_metric_selection.csv',[historical]),
        'historical_endpoints':('results/submission_refresh/endpoint_comparison.csv',[
            {**historical,'endpoint':'native_best_of_50','acc_mean':91.,'nmi_mean':92.,'acc_sd':None,'nmi_sd':None,'selected_seed':3}]),
        'historical_all_joint':('results/submission_refresh/all_joint_configurations.csv',[{'config_id':'historical-joint','endpoint':'mean_sample_sd_50'}]),
        'historical_all_native':('results/submission_refresh/all_native_endpoints.csv',[{'config_id':'historical-native','endpoint':'native_best_of_50'}]),
        'joint':('results/subset_search/joint_search_summary.csv',[{'benchmark':'ORL','candidate_id':'fixed','endpoint':'mean_sample_sd_50','acc_mean':42.,'nmi_mean':81.}]),
        'native':('results/subset_search/native_best_summary.csv',[{'benchmark':'ORL','candidate_id':'fixed','endpoint':'native_best_of_50','acc_mean':91.,'nmi_mean':92.}])}
    paths={}
    for role,(name,rows) in sources.items():
        path=write_csv(root/name,rows);paths[role]=packed(path) if compress else path
    return paths


def test_report_plain_and_gzip_inputs_generate_identical_tables_and_hash_actual_transport(tmp_path,monkeypatch):
    monkeypatch.setattr(reporting,'figure',lambda *args:False)
    plain=tmp_path/'plain inputs';compressed=tmp_path/'gzip inputs'
    original=report_fixture(plain);transport=report_fixture(compressed,compress=True)
    plain_manifest=reporting.generate(plain);gzip_manifest=reporting.generate(compressed)
    left={p.name:p.read_bytes() for p in (plain/'report/tables').glob('refresh_*.tex')}
    right={p.name:p.read_bytes() for p in (compressed/'report/tables').glob('refresh_*.tex')}
    assert left==right and len(left)==4
    for role,path in transport.items():
        record=gzip_manifest['inputs'][role]
        assert record['available'] and record['transport']=='gzip'
        assert record['path']==str(path.relative_to(compressed)) and record['path'].endswith('.csv.gz')
        assert record['logical_path'].endswith('.csv') and record['sha256']==digest(path)
        assert plain_manifest['inputs'][role]['sha256']==digest(original[role])
        assert record['sha256']!=plain_manifest['inputs'][role]['sha256']
    assert reporting.read_csv(compressed/'results/subset_search/joint_search_summary.csv')==reporting.read_csv(original['joint'])


def test_report_missing_is_explicit_and_ambiguous_inputs_do_not_replace_existing_tables(tmp_path,monkeypatch):
    monkeypatch.setattr(reporting,'figure',lambda *args:False)
    assert reporting.read_csv(tmp_path/'absent.csv')==[]
    path=write_csv(tmp_path/'results/subset_search/joint_search_summary.csv',[{'benchmark':'ORL'}])
    path.with_suffix('.csv.gz').write_bytes(gzip.compress(path.read_bytes(),mtime=0))
    sentinel=tmp_path/'report/tables/refresh_main.tex';sentinel.parent.mkdir(parents=True);sentinel.write_text('previous verified table')
    with pytest.raises(ValueError):reporting.read_csv(path)
    with pytest.raises(ValueError):reporting.generate(tmp_path)
    assert sentinel.read_text()=='previous verified table'
    assert not (tmp_path/'results/submission_refresh/report_input_manifest.json').exists()


def test_large_metadata_cells_work_without_changing_global_limit(tmp_path):
    previous=csv.field_size_limit();payload='metadata '*18000
    committed=write_csv(tmp_path/'large.csv',[{'id':'a','metadata':payload}]);archive=packed(committed)
    rebuilt=write_csv(tmp_path/'rebuilt.csv',[{'id':'a','metadata':payload}])
    assert reporting.read_csv(committed)[0]['metadata']==payload
    assert csv.field_size_limit()==previous


def test_direct_report_script_uses_own_sibling_helper_under_isolated_python(tmp_path):
    checkout=tmp_path/'uninstalled checkout with spaces';package=checkout/'experiments/submission_refresh'
    package.mkdir(parents=True);report=checkout/'report';report.mkdir()
    project=Path(__file__).resolve().parents[2]
    for filename in ['reporting.py','csv_transport.py']:
        shutil.copyfile(project/'experiments/submission_refresh'/filename,package/filename)
    # Deliberately omit package __init__ files and an editable installation.
    # No joint-search input is supplied, so figure() exits before scientific or
    # plotting imports. A plain global/cwd fallback must never be consulted.
    (report/'csv_transport.py').write_text("raise AssertionError('wrong helper imported')\n")
    historical={'benchmark':'ORL','method':'ssc','endpoint':'mean_sample_sd_50',
        'acc_mean':42.,'acc_sd':1.2,'nmi_mean':81.,'nmi_sd':2.3,
        'solver_status_current_audit':'ITERATE_CONVERGED_UNCERTIFIED'}
    logical=write_csv(checkout/'results/submission_refresh/joint_metric_selection.csv',[historical])
    archive=packed(logical)
    environment={key:value for key,value in os.environ.items() if key not in ['PYTHONPATH','PYTHONHOME','COMP3314_DATA_ROOT','COMP3314_ARTIFACT_ROOT']}
    completed=subprocess.run([sys.executable,'-I',str(package/'reporting.py'),'--root','..','--date','2026-11-10'],
        cwd=report,env=environment,text=True,capture_output=True,timeout=30)
    assert completed.returncode==0,completed.stdout+'\n'+completed.stderr
    assert r'42.00 $\pm$ 1.20' in (report/'tables/refresh_main.tex').read_text()
    manifest=json.loads((checkout/'results/submission_refresh/report_input_manifest.json').read_text())
    assert manifest['inputs']['historical']['path']=='results/submission_refresh/joint_metric_selection.csv.gz'
    assert manifest['inputs']['historical']['sha256']==digest(archive)
    assert not (report/'figures').exists()
