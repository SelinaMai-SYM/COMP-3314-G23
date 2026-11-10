"""Complete graph-design coverage from scalar metadata, without arrays or fits.

Controller execution and saved scientific outputs are independent observations.
A completed controller is not evidence of a complete casebook/point, and a
saved point can survive an interrupted controller. No score selects scope.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
import io
import hashlib
import json
import math
from pathlib import Path
import tempfile
import os
import shutil

ROOT = Path(__file__).resolve().parents[2]
QUEUE = 'configs/submission_refresh/graph_queue.json'
SCHEMA = 'graph-intended-coverage-v1'
SELECTORS = {'G1': ['dataset', 'phase', 'gamma'],
    'G2': ['dataset', 'phase', 'anchor', 'graph', 'gamma'],
    'G3': ['dataset', 'phase', 'addition_fraction', 'arm', 'gamma']}
EXPECTED_PHASES = {'G1': 2, 'G2': 48, 'G3': 312}


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _seed(value):
    result = int(value)
    if isinstance(value, bool) or float(value) != result:
        raise ValueError('noninteger recorded seed')
    return result


class Metadata:
    def __init__(self, store):
        self.store = Path(store).resolve()
        self.inputs = {}

    def read(self, path):
        path = Path(path)
        if not path.is_file(): return None
        raw = path.read_bytes()
        self.inputs[str(path.relative_to(self.store))] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {'_error': 'metadata is not a JSON object'}
        except (ValueError, UnicodeDecodeError) as exc:
            return {'_error': repr(exc)}

    def reference(self, path):
        relative = str(Path(path).relative_to(self.store))
        return {'path': relative, **self.inputs.get(relative, {})}


def _validate_tasks(queue):
    tasks = queue.get('tasks', [])
    if len(tasks) != 362 or dict(Counter(task.get('phase') for task in tasks)) != EXPECTED_PHASES:
        raise ValueError('graph coverage requires the complete frozen 362-task G1/G2/G3 design')
    for field in ['run_id', 'configuration_id']:
        if len({task.get(field) for task in tasks}) != len(tasks):
            raise ValueError('duplicate intended graph ' + field)
    for task in tasks:
        fields = SELECTORS[task['phase']]
        if task.get('kind') != 'graph' or any(key not in task for key in fields):
            raise ValueError('invalid intended graph task selectors')
        if _identity({key: task[key] for key in fields}) != task['configuration_id']:
            raise ValueError('intended graph configuration identity mismatch')
        if task['run_id'] != 'graph-' + task['configuration_id'][:20]:
            raise ValueError('intended graph run/configuration mapping mismatch')
    return tasks


def _matches(controller, task):
    if controller.get('kind') != 'graph' or controller.get('profile'):
        return False
    phase = controller.get('phase', controller.get('block', 'G2'))
    if phase != task['phase'] or controller.get('dataset') != task['dataset']:
        return False
    return all(key not in controller or controller[key] == task[key] for key in SELECTORS[phase])


def _controllers(metadata):
    records = []
    paths = set((metadata.store / 'task_status').glob('*.json'))
    paths.update((metadata.store / 'graph_jobs').glob('*/status.json'))
    paths.update((metadata.store / 'graph_jobs').glob('*/*/status.json'))
    for path in sorted(paths):
        record = metadata.read(path)
        if not record: continue
        task = record.get('task', {})
        if not isinstance(task, dict): continue
        if task.get('kind') != 'graph' or task.get('profile'): continue
        fallback = (path.stem if path.parent.name == 'task_status' else path.parent.name
            if path.parent.parent.name == 'graph_jobs' else path.parents[1].name)
        run_id = task.get('run_id') or fallback
        records.append({'run_id': run_id, 'task': task, 'status': record.get('status', 'UNKNOWN'),
            'error': record.get('error'), 'source_fingerprint': (record.get('source') or {}).get('implementation_hash'),
            'input_record': record.get('input_record'), 'saved_point_config_ids': [r.get('config_id') for r in (record.get('records') or []) if isinstance(r, dict)],
            'sc_solution': record.get('sc_solution'), 'ssc_solution': record.get('ssc_solution'),
            'evidence': metadata.reference(path)})
    return records


def _trial_state(record):
    trials = record.get('trials', [])
    if not isinstance(trials, list): return {'trial_count': 0, 'complete_50': False, 'trial_error': 'trials is not a list'}
    try:
        seeds = [_seed(trial['seed']) for trial in trials]
        valid = all(all(math.isfinite(float(trial[key])) and 0 <= float(trial[key]) <= 1
            for key in ['acc', 'nmi']) for trial in trials)
    except (ValueError, TypeError, KeyError, OverflowError):
        return {'trial_count': len(trials), 'complete_50': False, 'trial_error': 'invalid seed or scalar metric'}
    return {'trial_count': len(trials), 'complete_50': len(trials) == 50 and set(seeds) == set(range(50))
        and len(set(seeds)) == 50 and valid, 'recorded_seeds': sorted(set(seeds)),
        'duplicate_seeds': len(seeds) - len(set(seeds)), 'valid_metric_values': valid}


def _certificate(solution):
    solver = solution.get('solver') or {}
    if not isinstance(solver, dict): return {'certificate_status': 'INVALID_SOLVER_METADATA'}
    fields = {key: solver.get(key) for key in ['status', 'certified', 'gap', 'edge_violation', 'node_violation']}
    try:
        values = [float(fields[key]) for key in ['gap', 'edge_violation', 'node_violation']]
        valid = all(math.isfinite(value) for value in values) and 0 <= values[0] <= 1e-5
        valid = valid and 0 <= values[1] <= 1e-8 and 0 <= values[2] <= 1e-8
    except (ValueError, TypeError): valid = False
    status = 'RECORDED_GAP_CERTIFIED' if fields['certified'] is True and valid else (
        'CERTIFICATE_CLAIM_UNVERIFIABLE' if fields['certified'] is True else 'UNCERTIFIED' if solver else 'NOT_AVAILABLE')
    return {'certificate_status': status, **fields}


def _problem(solution):
    problem = solution.get('problem')
    return _identity(problem) if isinstance(problem, dict) and problem else None


def _point_name(task):
    if task['phase'] == 'G2':
        return f'G2__{task["anchor"]}__{task["graph"]}__{task["gamma"]:g}.json'
    return f'G3__{task["addition_fraction"]:g}__{task["arm"]}__{task["gamma"]:g}.json'


def _point_evidence(task, metadata):
    evidence = []
    filename = _point_name(task)
    expected_id = (f'{task["dataset"]}|G2|{task["anchor"]}|{task["graph"]}|{task["gamma"]:g}'
        if task['phase'] == 'G2' else f'{task["dataset"]}|G3|{task["addition_fraction"]:g}|{task["arm"]}|{task["gamma"]:g}')
    for path in sorted((metadata.store / 'graph_records' / task['dataset']).glob('*/' + filename)):
        record = metadata.read(path) or {'_error': 'point metadata disappeared during coverage snapshot'}
        errors = [record['_error']] if '_error' in record else []
        errors += [key + ' mismatch' for key in SELECTORS[task['phase']] if record.get(key) != task[key]]
        if record.get('config_id') != expected_id: errors.append('saved config_id mismatch')
        trials = _trial_state(record)
        evidence.append({**metadata.reference(path), 'input_version': path.parent.name,
            'config_id': record.get('config_id'), 'status': record.get('status', 'INVALID_METADATA'),
            'identity_errors': errors, **trials, 'point_complete': not errors
                and record.get('status') == 'COMPLETED' and trials['complete_50'],
            'certificate': _certificate(record), 'problem_id': _problem(record),
            'SC_graph_arm_alias': record.get('SC_graph_arm_alias'),
            'source_fingerprint': (record.get('source') or {}).get('implementation_hash')})
    return evidence, expected_id


def _casebook_evidence(task, controllers, metadata, expected_membership):
    evidence = []
    for controller in controllers:
        run_id = controller['run_id']
        for path in sorted((metadata.store / 'graph_jobs' / run_id).glob('*/casebook.json')):
            record = metadata.read(path) or {'_error': 'casebook metadata disappeared during coverage snapshot'}
            table = path.parent / 'error_cases.csv'
            errors = [record['_error']] if '_error' in record else []
            count = 0
            samples = record.get('samples', 0)
            try:
                if not isinstance(samples, int) or samples <= 0: raise ValueError('invalid casebook sample count')
                raw = table.read_bytes()
                metadata.inputs[str(table.relative_to(metadata.store))] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
                rows = list(csv.DictReader(io.StringIO(raw.decode())))
                ids = [int(row['sample_id']) for row in rows]
                count = len(rows)
                if len(ids) != samples or set(ids) != set(range(samples)) or len(set(ids)) != len(ids):
                    errors.append('casebook table must retain every sample exactly once')
            except (OSError, ValueError, KeyError, UnicodeDecodeError) as exc: errors.append(repr(exc))
            if record.get('status') != 'COMPLETED' or record.get('seed_count') != 50:
                errors.append('casebook is not marked complete for 50 paired seeds')
            expected = expected_membership.get(task['dataset'])
            if expected is None or samples != expected['n']:
                errors.append('casebook sample count does not match frozen full-benchmark membership')
            per_class = defaultdict(list)
            try:
                for item in record.get('per_class', []): per_class[str(item['class'])].append(_seed(item['seed']))
                if expected is None or len(per_class) != expected['classes'] or any(
                    len(seeds) != 50 or set(seeds) != set(range(50)) for seeds in per_class.values()):
                    errors.append('casebook per-class paired-seed coverage incomplete')
            except (KeyError, TypeError, ValueError, OverflowError): errors.append('invalid casebook per-class diagnostics')
            if any(not isinstance(record.get(key), list) or len(record[key]) != 50
                for key in ['sc_pair_errors', 'ssc_pair_errors']):
                errors.append('casebook paired-seed diagnostics incomplete')
            objects = record.get('objects', {})
            if not all(isinstance(objects.get(key), dict) and {'sha256', 'path', 'kind'}.issubset(objects[key])
                for key in ['sc_correct', 'ssc_correct', 'raw_neighbors', 'angular_neighbors', 'confusions']):
                errors.append('casebook object references incomplete')
            evidence.append({**metadata.reference(path), 'controller_run_id': run_id,
                'input_version': path.parent.name, 'samples': samples, 'case_table_rows': count,
                'case_table': metadata.reference(table), 'seed_count': record.get('seed_count'),
                'casebook_complete': not errors, 'errors': errors})
    # Top-level and graph_jobs status copies must not duplicate one casebook.
    return list({row['path']: row for row in evidence}.values())


def _controller_state(task, controllers, ledger, pending):
    matching = [record for record in controllers if _matches(record['task'], task)]
    direct = [record for record in matching if record['run_id'] == task['run_id']]
    primary = [record for record in direct if record['evidence']['path'].startswith('task_status/')]
    selected = primary or direct or matching
    statuses = sorted({record['status'] for record in selected})
    ids = sorted({task['run_id']} | {record['run_id'] for record in matching})
    entries = [entry for entry in ledger.get('entries', []) if entry.get('run_id') in ids]
    active = [run_id for run_id in ids if run_id in ledger.get('active', {})]
    charged = sum(float(entry.get('charged_cpu_seconds', 0)) for entry in ledger.get('entries', []))
    limit = float(ledger.get('limit_seconds', 129600)) - float(ledger.get('reserve_seconds', 7200))
    remaining = limit - charged
    if statuses: status = statuses[0] if len(statuses) == 1 else 'MULTIPLE_CONTROLLER_STATES'
    elif active: status = 'RUNNING'
    elif entries: status = entries[-1].get('status', 'UNKNOWN_LEDGER_STATUS')
    elif ledger and not ledger.get('active') and remaining < float(task.get('cpu_limit', 0)): status = 'NOT_RUN_BUDGET'
    elif any(run_id in pending for run_id in ids): status = 'PENDING'
    else: status = 'NOT_RUN'
    return matching, {'controller_status': status,
        'controller_identity': 'EXACT_RUN_ID' if direct else 'SEMANTIC_CONTROLLER_ALIAS' if matching else 'NO_CONTROLLER_RECORD',
        'controller_run_ids': sorted({record['run_id'] for record in matching}),
        'controller_evidence': [{key: record[key] for key in ['run_id', 'status', 'error', 'source_fingerprint', 'input_record', 'saved_point_config_ids', 'evidence']} for record in matching],
        'ledger_statuses': [entry.get('status') for entry in entries], 'active_controller_run_ids': active,
        'scheduler_pending': any(run_id in pending for run_id in ids),
        'shared_unreserved_budget_seconds_before_active_reservations': remaining,
        'unrun_reason': 'Frozen task reservation exceeds remaining non-finalization allowance; no active jobs remain.'
            if status == 'NOT_RUN_BUDGET' else 'No launched controller record or reservation.' if status == 'NOT_RUN' else None}


def build_graph_coverage(artifact_root, output, *, root=ROOT):
    """Write one row per intended task; read JSON/CSV metadata, never arrays."""
    root = Path(root).resolve()
    queue_path = root / QUEUE
    queue_bytes = queue_path.read_bytes()
    tasks = _validate_tasks(json.loads(queue_bytes))
    membership_path = root / 'results/subset_search/source_inventory.csv'
    membership_bytes = membership_path.read_bytes() if membership_path.is_file() else None
    expected_membership = ({row['parent_id']: {'n': int(row['n']), 'classes': int(row['classes'])}
        for row in csv.DictReader(io.StringIO(membership_bytes.decode()))} if membership_bytes is not None else {})
    metadata = Metadata(artifact_root)
    ledger = metadata.read(metadata.store / 'resource_ledger.json') or {}
    if '_error' in ledger: raise ValueError('cannot read shared resource ledger for graph coverage')
    pending = set()
    for path in sorted((metadata.store / 'queues').glob('*.json')):
        queue = metadata.read(path) or {}
        pending.update(value for value in queue.get('pending', []) if isinstance(value, str))
    controllers = _controllers(metadata)
    rows = []
    for index, task in enumerate(tasks):
        matching, state = _controller_state(task, controllers, ledger, pending)
        row = {'schema': SCHEMA, 'declaration_index': index, 'run_id': task['run_id'],
            'configuration_id': task['configuration_id'], **{key: task.get(key) for key in
                ['phase', 'dataset', 'anchor', 'graph', 'arm', 'addition_fraction', 'gamma', 'cpu_limit', 'fit_cpu_limit']}, **state}
        if task['phase'] == 'G1':
            evidence = _casebook_evidence(task, matching, metadata, expected_membership)
            certificates = []
            problems = []
            for controller in matching:
                for name in ['sc_solution', 'ssc_solution']:
                    solution = controller.get(name)
                    if not isinstance(solution, dict): continue
                    certificates.append({'role': name, 'controller_run_id': controller['run_id'],
                        'problem_id': _problem(solution), **_certificate(solution)})
                    if _problem(solution): problems.append(_problem(solution))
            certificates = list({_identity(item): item for item in certificates}.values())
            complete = len(evidence) == 1 and evidence[0]['casebook_complete']
            output_state = 'CASEBOOK_COMPLETE' if complete else 'MISSING_CASEBOOK' if not evidence else 'INCOMPLETE_OR_MULTIPLE_CASEBOOKS'
            row.update(saved_output_type='G1_CASEBOOK', casebook_complete=complete, point_complete=None,
                point_file_status='NOT_APPLICABLE_G1_CASEBOOK', expected_config_id=None,
                saved_output_state=output_state, saved_evidence=evidence, solver_certificates=certificates,
                problem_ids=sorted(set(problems)), input_versions=sorted({item['input_version'] for item in evidence}))
        else:
            evidence, config_id = _point_evidence(task, metadata)
            complete = len(evidence) == 1 and evidence[0]['point_complete']
            output_state = ('POINT_COMPLETE' if complete else 'MISSING_POINT_FILE' if not evidence else
                'AMBIGUOUS_INPUT_VERSIONS' if len(evidence) > 1 else 'INCOMPLETE_OR_INVALID_POINT')
            row.update(saved_output_type='G2_G3_POINT', casebook_complete=None, point_complete=complete,
                point_file_status=evidence[0]['status'] if len(evidence) == 1 else output_state,
                expected_config_id=config_id, expected_point_filename=_point_name(task), saved_output_state=output_state,
                saved_evidence=evidence, solver_certificates=[item['certificate'] for item in evidence],
                problem_ids=sorted({item['problem_id'] for item in evidence if item['problem_id']}),
                input_versions=sorted({item['input_version'] for item in evidence}))
        row['saved_output_count'] = len(row['saved_evidence'])
        row['declared_SC_graph_arm_alias'] = task['phase'] != 'G1' and task['gamma'] == 0
        row['declared_SC_alias_key'] = (task['dataset'] + '|SC|' + task.get('anchor', 'F0')) if row['declared_SC_graph_arm_alias'] else None
        row['coverage_state'] = row['saved_output_state'] if row['saved_output_count'] else row['controller_status']
        if row['controller_status'] == 'COMPLETED' and not complete:
            row['coverage_state'] = 'CONTROLLER_COMPLETED_' + row['saved_output_state']
        row['object_availability_scope'] = 'Metadata references only; object/archive verification is separate.'
        rows.append(row)
    aliases = defaultdict(set)
    for row in rows:
        for problem in row['problem_ids']: aliases[problem].add(row['run_id'])
    for row in rows:
        row['saved_problem_alias_run_ids'] = sorted(set().union(*(aliases[problem] for problem in row['problem_ids'])) - {row['run_id']}) if row['problem_ids'] else []
    output = Path(output).resolve()
    if output == metadata.store or output in metadata.store.parents:
        raise ValueError('coverage output would replace the scientific artifact root')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.graph-coverage-', dir=output.parent))
    try:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        csv_path = stage / 'graph_execution_coverage.csv'
        with csv_path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})
        manifest = {'schema': SCHEMA, 'queue_path': QUEUE,
            'queue_sha256': hashlib.sha256(queue_bytes).hexdigest(), 'intended_tasks': len(rows),
            'frozen_membership_inventory': {'path': 'results/subset_search/source_inventory.csv',
                'sha256': hashlib.sha256(membership_bytes).hexdigest() if membership_bytes is not None else None},
            'phase_counts': dict(Counter(row['phase'] for row in rows)),
            'controller_status_counts': dict(Counter(row['controller_status'] for row in rows)),
            'saved_output_state_counts': dict(Counter(row['saved_output_state'] for row in rows)),
            'coverage_state_counts': dict(Counter(row['coverage_state'] for row in rows)),
            'source_metadata': metadata.inputs, 'array_objects_read': False, 'fits_run': False,
            'labels_evaluated': False, 'score_based_scope_selection': False,
            'coverage_sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            'qualification': 'One row per frozen intended task. Controller state, G1 casebook completeness and G2/G3 saved-point/certificate evidence stay separate. Shared problem IDs are aliases, not independent reruns. Budget states use ledger reservations, never scores.'}
        (stage / 'graph_coverage_manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
        output.mkdir(parents=True, exist_ok=True)
        for path in stage.iterdir(): os.replace(path, output / path.name)
        return manifest
    finally:
        shutil.rmtree(stage)
