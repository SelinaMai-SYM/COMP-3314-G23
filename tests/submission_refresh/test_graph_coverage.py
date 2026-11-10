"""Metadata-only coverage fixtures: no graph construction, matrices or fits."""
import csv
import json
from pathlib import Path
import pytest

from experiments.submission_refresh import graph_coverage as coverage


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def graph_metadata(tmp_path):
    root = tmp_path / 'checkout'
    queue = root / coverage.QUEUE
    queue.parent.mkdir(parents=True)
    queue.write_bytes((coverage.ROOT / coverage.QUEUE).read_bytes())
    inventory = root / 'results/subset_search/source_inventory.csv'
    inventory.parent.mkdir(parents=True)
    inventory.write_bytes((coverage.ROOT / inventory.relative_to(root)).read_bytes())
    store = tmp_path / 'scientific metadata'
    store.mkdir()
    return root, store, tmp_path / 'coverage', json.loads(queue.read_text())['tasks']


def rows(path):
    return list(csv.DictReader((path / 'graph_execution_coverage.csv').open()))


def point(store, task, *, trials=None, solver=None):
    problem = {'F': 'same-anchor', 'W': 'same-objective-graph', 'gamma': task['gamma'], 'source': 'science'}
    config_id = (f'{task["dataset"]}|G2|{task["anchor"]}|{task["graph"]}|{task["gamma"]:g}'
        if task['phase'] == 'G2' else f'{task["dataset"]}|G3|{task["addition_fraction"]:g}|{task["arm"]}|{task["gamma"]:g}')
    record = {key: task[key] for key in coverage.SELECTORS[task['phase']]}
    record.update(config_id=config_id, status='COMPLETED', problem=problem,
        SC_graph_arm_alias=task['gamma'] == 0,
        trials=trials if trials is not None else [{'seed': seed, 'acc': .4, 'nmi': .3} for seed in range(50)],
        solver=solver if solver is not None else {'status': 'PRIMAL_DUAL_GAP_CERTIFIED', 'certified': True,
            'gap': 1e-9, 'edge_violation': 0., 'node_violation': 0.})
    write_json(store / 'graph_records' / task['dataset'] / 'input-version' / coverage._point_name(task), record)


def test_every_frozen_graph_task_is_visible_even_when_nothing_launched(graph_metadata):
    root, store, output, tasks = graph_metadata
    manifest = coverage.build_graph_coverage(store, output, root=root)
    result = rows(output)
    assert len(result) == manifest['intended_tasks'] == 362
    assert manifest['phase_counts'] == {'G1': 2, 'G2': 48, 'G3': 312}
    assert all(row['controller_status'] == 'NOT_RUN' for row in result)
    assert all(row['point_file_status'] == 'NOT_APPLICABLE_G1_CASEBOOK' for row in result if row['phase'] == 'G1')
    assert manifest['array_objects_read'] is manifest['fits_run'] is manifest['score_based_scope_selection'] is False
    assert not (store / 'objects').exists()


def test_saved_points_survive_failed_controller_and_do_not_complete_g1(graph_metadata):
    root, store, output, tasks = graph_metadata
    aliases = [task for task in tasks if task['phase'] == 'G2' and task['dataset'] == 'ORL_att92'
        and task['anchor'] == 'F0' and task['gamma'] == 0]
    for task in aliases: point(store, task)
    write_json(store / 'task_status' / (aliases[0]['run_id'] + '.json'), {'task': aliases[0], 'status': 'TIMEOUT'})
    g1 = next(task for task in tasks if task['phase'] == 'G1' and task['dataset'] == 'ORL_att92')
    write_json(store / 'task_status' / (g1['run_id'] + '.json'), {'task': g1, 'status': 'COMPLETED'})
    coverage.build_graph_coverage(store, output, root=root)
    result = {row['run_id']: row for row in rows(output)}
    saved = result[aliases[0]['run_id']]
    assert saved['controller_status'] == 'TIMEOUT' and saved['point_complete'] == 'True'
    assert saved['coverage_state'] == 'POINT_COMPLETE'
    assert aliases[1]['run_id'] in json.loads(saved['saved_problem_alias_run_ids'])
    assert json.loads(saved['solver_certificates'])[0]['certificate_status'] == 'RECORDED_GAP_CERTIFIED'
    assert result[g1['run_id']]['coverage_state'] == 'CONTROLLER_COMPLETED_MISSING_CASEBOOK'
    assert result[g1['run_id']]['casebook_complete'] == 'False'


def test_duplicate_seeds_and_missing_certificate_fields_are_not_promoted(graph_metadata):
    root, store, output, tasks = graph_metadata
    task = next(task for task in tasks if task['phase'] == 'G3')
    point(store, task, trials=[{'seed': 0, 'acc': .4, 'nmi': .3}] * 50,
        solver={'certified': True, 'gap': 0., 'edge_violation': 0.})
    coverage.build_graph_coverage(store, output, root=root)
    row = next(row for row in rows(output) if row['run_id'] == task['run_id'])
    assert row['point_complete'] == 'False'
    assert json.loads(row['saved_evidence'])[0]['duplicate_seeds'] == 49
    assert json.loads(row['solver_certificates'])[0]['certificate_status'] == 'CERTIFICATE_CLAIM_UNVERIFIABLE'


def test_pending_and_budget_states_use_ledger_evidence_not_scores(graph_metadata):
    root, store, output, tasks = graph_metadata
    write_json(store / 'resource_ledger.json', {'entries': [{'run_id': 'prior', 'charged_cpu_seconds': 90}],
        'active': {}, 'limit_seconds': 100, 'reserve_seconds': 0})
    coverage.build_graph_coverage(store, output, root=root)
    assert all(row['controller_status'] == 'NOT_RUN_BUDGET' for row in rows(output))
    write_json(store / 'resource_ledger.json', {'entries': [], 'active': {'other-job': {'seconds': 1}},
        'limit_seconds': 100, 'reserve_seconds': 0})
    write_json(store / 'queues' / 'pending.json', {'pending': [tasks[0]['run_id']]})
    coverage.build_graph_coverage(store, output, root=root)
    result = rows(output)
    assert result[0]['controller_status'] == 'PENDING'
    assert all(row['controller_status'] == 'NOT_RUN' for row in result[1:])


def test_bad_intended_queue_fails_before_output_replacement(graph_metadata):
    root, store, output, tasks = graph_metadata
    output.mkdir()
    previous = output / 'graph_execution_coverage.csv'
    previous.write_text('prior coverage preserved\n')
    write_json(root / coverage.QUEUE, {'tasks': tasks[:-1]})
    with pytest.raises(ValueError, match='complete frozen 362-task'):
        coverage.build_graph_coverage(store, output, root=root)
    assert previous.read_text() == 'prior coverage preserved\n'
