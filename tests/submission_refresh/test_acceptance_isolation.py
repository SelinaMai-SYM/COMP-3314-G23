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


def test_formal_validation_selection_needs_no_execution_queue_and_uses_fresh_junit(tmp_path,monkeypatch,acceptance_module):
    acceptance=make_acceptance(acceptance_module,tmp_path)
    selection_path=Path(__file__).resolve().parents[2]/'configs/validation.json'
    selection=json.loads(selection_path.read_text())
    config=acceptance.checkout/'configs/validation.json'
    config.parent.mkdir(parents=True)
    config.write_text(selection_path.read_text())
    acceptance.python=acceptance.venv/'bin/python'
    observed={}
    def capture(name,command,junit,expected_integration_skip):
        observed.update(name=name,command=command,junit=junit,expected_skip=expected_integration_skip)
    monkeypatch.setattr(acceptance,'pytest_stage',capture)
    acceptance.focused_regressions()
    original=selection['pytest_argv']
    expected=list(original)
    expected[expected.index('--junitxml')+1]=str(acceptance.products/'focused-regressions.xml')
    assert observed['command']==[acceptance.python,'-m','pytest',*expected]
    assert observed['expected_skip'] is True
    assert '--junitxml' in observed['command'] and '-ra' in observed['command']
    assert 'tests/submission_refresh' in expected and 'tests/next_round' in expected
    assert acceptance.result['focused_selection']['config']=='configs/validation.json'
    assert 'task_run_id' not in acceptance.result['focused_selection']
    assert '{validation_dir}/pytest.xml' in original
    assert not (acceptance.checkout/'configs/submission_refresh').exists()


REPORT_SOURCE=r'''
\section{Conclusion}
Body ends here. \label{main_end}
\clearpage
\label{references_start}
\bibliographystyle{plainnat}\bibliography{references}
\clearpage\appendix
\section{Evidence}
'''


@pytest.mark.parametrize('body_page,references_page,expected_main,passes',[
    (4,6,5,False), # A queued main float occupies page five.
    (3,5,4,True),  # A queued main float occupies page four.
])
def test_main_float_spill_is_counted_before_references(acceptance_module,body_page,references_page,expected_main,passes):
    auxiliary=(r'\newlabel{main_end}{{5}{'+str(body_page)+r'}{Conclusion {nested title}}{section.5}{}}'+'\n'
        +r'\newlabel{references_start}{{5}{'+str(references_page)+r'}{Conclusion}{section.5}{}}')
    boundary=acceptance_module.report_main_boundaries(REPORT_SOURCE,auxiliary)
    assert boundary['body_end_page']==body_page
    assert boundary['main_pages']==expected_main
    assert boundary['within_four_page_limit'] is passes


@pytest.mark.parametrize('source',[
    REPORT_SOURCE.replace('\\clearpage\n\\label{references_start}','\\label{references_start}\n\\clearpage',1),
    REPORT_SOURCE.replace('\\label{references_start}','% \\label{references_start}',1),
    REPORT_SOURCE.replace('\\label{main_end}','\\label{main_end}\\label{main_end}',1),
])
def test_main_reference_markers_require_valid_source_order(acceptance_module,source):
    auxiliary=r'\newlabel{main_end}{{5}{3}}'+'\n'+r'\newlabel{references_start}{{5}{5}}'
    with pytest.raises(ValueError):acceptance_module.report_main_boundaries(source,auxiliary)
