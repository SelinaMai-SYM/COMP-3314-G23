import json
from experiments.submission_refresh.scheduler import _execute
from experiments.subset_search import complete_failed

def test_preflight_failure_keeps_an_actual_cpu_record(monkeypatch,tmp_path):
    monkeypatch.setenv('COMP3314_ARTIFACT_ROOT','before-test')
    def reject(*args):raise ValueError('invalid saved representation')
    monkeypatch.setattr(complete_failed,'run_completion',reject)
    task={'kind':'subset_completion','run_id':'failure-fixture','cpu_limit':100}
    _execute(task,tmp_path,tmp_path/'artifacts')
    record=json.loads((tmp_path/'artifacts/task_status/failure-fixture.json').read_text())
    assert record['status']=='FAILED_CONTROLLER'
    assert 'invalid saved representation'in record['error']
    assert 0<=record['cpu_seconds']<=record['process_cpu_seconds']
