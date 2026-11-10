"""Build a corrected, versioned inventory from committed audit evidence only."""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import shutil
import tempfile

from .core import ROOT, atomic_json, digest

SCHEMA = 'corrected-source-inventory-v2'
INITIAL = 'results/subset_search/source_inventory.csv'
AUDIT = 'results/submission_refresh/source_audit/source_version_audit.json'


def _inside(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    path = (root / relative).resolve()
    if relative.is_absolute() or root not in path.parents:
        raise ValueError('source-audit path escapes its evidence directory')
    return path


def _resolution(value):
    return 'UNVERIFIED' if value is None else 'x'.join(str(int(v)) for v in value)


def _validate_map(parent, mapping):
    n = int(parent['shape'][0])
    if mapping.get('input_rows') != n or mapping.get('official_input_modified') is not False:
        raise ValueError('duplicate-map input identity or modification flag mismatch')
    for key in ['unique_rows', 'duplicate_extra_rows', 'duplicate_group_count', 'duplicate_pair_count', 'cross_class_duplicate_groups']:
        if mapping.get(key) != parent.get(key):
            raise ValueError('duplicate-map/audit count mismatch: ' + key)
    first = mapping['first_occurrence_indices']
    assigned = mapping['original_to_first_occurrence_row']
    if len(first) != parent['unique_rows'] or len(set(first)) != len(first) or len(assigned) != n:
        raise ValueError('duplicate-map row cardinality mismatch')
    if any(not isinstance(v, int) or v < 0 or v >= n for v in first):
        raise ValueError('duplicate-map row index outside input')
    # The inverse maps each original row to a compact row in the sorted
    # first-occurrence matrix, rather than directly to an original row ID.
    if any(not isinstance(v, int) or v < 0 or v >= len(first) for v in assigned):
        raise ValueError('duplicate-map retained-row index outside input')
    if any(first[value] > i for i, value in enumerate(assigned)) or any(assigned[original] != j for j, original in enumerate(first)):
        raise ValueError('duplicate-map first occurrence mapping invalid')
    groups = mapping['duplicate_groups']
    if len(groups) != parent['duplicate_group_count']:
        raise ValueError('duplicate-map group count mismatch')
    extra = sum(len(g['original_indices']) - 1 for g in groups)
    pairs = sum(len(g['original_indices']) * (len(g['original_indices']) - 1) // 2 for g in groups)
    conflicts = sum(bool(g['cross_class_conflict']) for g in groups)
    if (extra, pairs, conflicts) != (parent['duplicate_extra_rows'], parent['duplicate_pair_count'], parent['cross_class_duplicate_groups']):
        raise ValueError('duplicate-map group statistics mismatch')
    if n - len(first) != extra:
        raise ValueError('duplicate-map unique-row accounting mismatch')


def build_inventory(output, root=ROOT):
    """Validate all inputs before writing; leave the frozen catalogue untouched.

    Returns the manifest and writes dataset_inventory.csv, an identical explicitly
    versioned dataset_inventory.v2.csv, and dataset_inventory_manifest.json.
    No data-root, external artifact, fitting or Git-history access is used.
    """
    root = Path(root).resolve()
    initial_path = root / INITIAL
    audit_path = root / AUDIT
    hashes = {INITIAL: digest(initial_path), AUDIT: digest(audit_path)}
    with initial_path.open(newline='') as handle:
        frozen = list(csv.DictReader(handle))
    initial = {row['parent_id']: row for row in frozen}
    if not initial or len(initial) != len(frozen):
        raise ValueError('empty or duplicate frozen source inventory')
    audit = json.loads(audit_path.read_text())
    parents = audit['parents']
    if audit.get('schema') != 'parent-source-audit-v1' or audit.get('parent_count') != len(parents) or audit.get('available_audited_parents') != len(parents):
        raise ValueError('incomplete or unsupported source audit')
    if len({p['parent_id'] for p in parents}) != len(parents) or {p['parent_id'] for p in parents} != set(initial):
        raise ValueError('audited source parents do not match the frozen inventory')
    if audit.get('no_official_data_deduplicated') is not True:
        raise ValueError('source audit does not preserve official input rows')
    rows = []
    for parent in parents:
        original = initial[parent['parent_id']]
        if parent['status'] not in ['AUDITED', 'AUDITED_WITH_DUPLICATE_LABEL_CONFLICTS'] or parent.get('official_input_modified') is not False:
            raise ValueError('unavailable or modified source in final inventory')
        n, p = parent['shape']
        if (n, p, parent['classes']) != tuple(int(original[k]) for k in ['n', 'p', 'classes']):
            raise ValueError('source dimensions changed since catalogue freeze')
        sources = parent['source_files']
        if not sources or any(source.get('frozen_catalogue_hash_verified') is not True for source in sources):
            raise ValueError('raw source identity was not verified by the audit')
        if {source['sha256'] for source in sources} != set(original['source_sha256'].split(';')):
            raise ValueError('audited raw source hashes differ from the frozen catalogue')
        duplicate = parent['duplicate_map']
        duplicate_path = _inside(audit_path.parent, duplicate['path'])
        if not duplicate_path.is_file() or digest(duplicate_path) != duplicate['sha256'] or duplicate_path.stat().st_size != duplicate['bytes']:
            raise ValueError('source duplicate map missing/hash mismatch')
        hashes[str(duplicate_path.relative_to(root))] = duplicate['sha256']
        _validate_map(parent, json.loads(duplicate_path.read_text()))
        benchmark = 'MSRA50' if parent['parent_id'] == 'MSRA25_EBSA_16x16' else parent['benchmark']
        row = {'schema': SCHEMA, 'parent_id': parent['parent_id'], 'benchmark': benchmark,
            'loader_benchmark': parent['benchmark'], 'dataset_version': parent['version'],
            'audit_status': parent['status'], 'historical_identity': parent['historical_identity'],
            'n': n, 'p': p, 'classes': parent['classes'], 'class_counts': parent['class_counts'],
            'dtype': parent['dtype'], 'labels_dtype': parent['labels_dtype'],
            'native_resolution': _resolution(parent['native_resolution']),
            'processed_resolution': _resolution(parent['processed_resolution']),
            'native_resolution_unverified': parent['native_resolution_unverified'],
            'resolution_evidence': parent['resolution_evidence'],
            'processed_pixel_range': parent['processed_pixel_range'], 'nonfinite_values': parent['nonfinite_values'],
            'processed_x_sha256': parent['fingerprint']['x_sha256'], 'labels_sha256': parent['fingerprint']['y_sha256'],
            'source_url': parent['source_url'], 'source_sha256': ';'.join(s['sha256'] for s in sources),
            'source_files': sources, 'source_alias_of': original['source_alias_of'],
            'physical_matrix_alias_of': parent['physical_matrix_alias_of'],
            'duplicate_map_path': str(duplicate_path.relative_to(root)), 'duplicate_map_sha256': duplicate['sha256'],
            'source_order': parent['source_order'], 'row_id_pattern': parent['row_id_pattern'],
            'source_selection': parent['source_selection'], 'construction': parent['construction'],
            'preprocessing_operations': parent['preprocessing_operations'],
            'original_parent_id': parent['original_parent_id'],
            'original_row_indices_source': AUDIT + '#parents/' + parent['parent_id'] + '/original_row_indices',
            'official_input_modified': False,
            'duplicate_policy': 'Audit only; all declared input rows retained. Previously declared derived sources retain their explicit construction.'}
        for key in ['unique_rows', 'duplicate_extra_rows', 'duplicate_pair_count', 'duplicate_group_count', 'cross_class_duplicate_groups']:
            row[key] = parent[key]
        row['duplicate_conflict_interpretation'] = parent.get('conflict_interpretation')
        rows.append(row)
    if any(digest(root / name) != sha for name, sha in hashes.items()):
        raise ValueError('source inventory input changed during validation')
    output = Path(output).resolve()
    if any(path == output or output in path.parents for path in [root / name for name in hashes]):
        raise ValueError('inventory output would replace source evidence')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.inventory-', dir=output.parent))
    try:
        path = temporary / 'dataset_inventory.v2.csv'
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in row.items()})
        shutil.copy2(path, temporary / 'dataset_inventory.csv')
        manifest = {'schema': SCHEMA, 'input_hashes': hashes, 'parent_count': len(rows),
            'frozen_initial_inventory_preserved': INITIAL, 'frozen_candidate_catalogue_modified': False,
            'transformation': 'Replace initial unaudited fields with committed source-audit evidence; distinguish paper benchmark, loader source, and native/processed geometry. No sample membership change.',
            'outputs': {name: digest(temporary / name) for name in ['dataset_inventory.csv', 'dataset_inventory.v2.csv']},
            'external_data_read': False, 'external_artifacts_read': False, 'git_history_read': False}
        atomic_json(temporary / 'dataset_inventory_manifest.json', manifest)
        output.mkdir(parents=True, exist_ok=True)
        for path in temporary.iterdir(): os.replace(path, output / path.name)
        return manifest
    finally:
        shutil.rmtree(temporary)
