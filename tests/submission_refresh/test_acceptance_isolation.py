"""Acceptance environment/monitor guards without clone, install or subprocess."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest


@pytest.fixture
def acceptance_module():
    path=Path(__file__).resolve().parents[2]/'scripts/submission_refresh/acceptance.py'
    spec=importlib.util.spec_from_file_location('acceptance_isolation_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def make_acceptance(module,tmp_path):
    source=tmp_path/'source';source.mkdir()
    data=tmp_path/'independent data';data.mkdir()
    return module.Acceptance(SimpleNamespace(repository=str(source),data_root=str(data),
        output=str(tmp_path/'acceptance evidence'),branch='main',expected_commit='a'*40,
        cpu_limit=900,wall_limit=1800,report_date='2026-11-10',real_candidate_replay=False))


def test_shared_artifact_root_is_removed_and_absence_is_checked_before_commands(tmp_path,monkeypatch,acceptance_module):
    module=acceptance_module
    monkeypatch.setenv('COMP3314_ARTIFACT_ROOT',str(tmp_path/'shared original artifacts'))
    acceptance=make_acceptance(module,tmp_path)
    assert 'COMP3314_ARTIFACT_ROOT' not in acceptance.env
    assert 'COMP3314_ARTIFACT_ROOT' in acceptance.result['cleared_environment_keys']
    assert Path(acceptance.ps_path).is_absolute()
    acceptance.env['COMP3314_ARTIFACT_ROOT']='unexpected inherited pointer'
    def never(*args,**kwargs):raise AssertionError('no-data subprocess must not start with an artifact override')
    monkeypatch.setattr(acceptance,'run',never)
    with pytest.raises(ValueError,match='no-inherited-data-or-artifact-root'):
        acceptance.no_data_rebuilds()


def test_process_monitor_uses_explicit_absolute_binary_and_clean_environment(monkeypatch,acceptance_module):
    observed={};environment={'PATH':'/usr/bin:/bin'}
    def fake(argv,**kwargs):
        observed.update(argv=argv,kwargs=kwargs)
        return '100 1 00:00.01 1000\n101 100 00:00.02 2000\n102 1 00:00.03 3000\n'
    monkeypatch.setattr(acceptance_module.subprocess,'check_output',fake)
    children,cpu,rss=acceptance_module.descendants(100,'/absolute/system/ps',environment)
    assert observed['argv'][0]=='/absolute/system/ps'
    assert observed['kwargs']['env'] is environment
    assert children==[101] and cpu==.02 and rss==3000*1024
