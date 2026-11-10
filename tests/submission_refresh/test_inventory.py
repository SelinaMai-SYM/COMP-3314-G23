"""Corrected metadata must preserve frozen sources and verify its evidence."""
import csv
import json
import pytest

from experiments.submission_refresh.core import digest
from experiments.submission_refresh.inventory import AUDIT, INITIAL, OUTPUT_NAMES, build_inventory


@pytest.fixture
def audited_inventory(tmp_path):
    root = tmp_path / 'checkout'
    initial = root / INITIAL
    initial.parent.mkdir(parents=True)
    initial.write_text('parent_id,benchmark,n,p,classes,native_resolution,source_url,source_sha256,historical_identity,unique_rows,source_alias_of\n' + 'source,BinAlpha,3,2,2,,url,' + 'a' * 64 + ',unverified,not audited,\n')
    audit_path = root / AUDIT
    audit_path.parent.mkdir(parents=True)
    duplicate_path = audit_path.parent / 'source_duplicate_maps/source.json'
    duplicate_path.parent.mkdir()
    counts = {'unique_rows': 2, 'duplicate_extra_rows': 1, 'duplicate_group_count': 1, 'duplicate_pair_count': 1, 'cross_class_duplicate_groups': 1}
    duplicate_path.write_text(json.dumps({**counts, 'input_rows': 3, 'official_input_modified': False,
        'first_occurrence_indices': [0, 1], 'original_to_first_occurrence_row': [0, 1, 0],
        'duplicate_groups': [{'original_indices': [0, 2], 'first_original_index': 0, 'cross_class_conflict': True}]}))
    parent = {**counts, 'parent_id': 'source', 'benchmark': 'BinAlpha', 'version': 'native',
        'shape': [3, 2], 'classes': 2, 'class_counts': {'0': 1, '1': 2}, 'status': 'AUDITED_WITH_DUPLICATE_LABEL_CONFLICTS',
        'official_input_modified': False, 'historical_identity': 'unverified', 'dtype': 'float64', 'labels_dtype': 'int64',
        'native_resolution': None, 'processed_resolution': None, 'native_resolution_unverified': True,
        'resolution_evidence': 'unverified', 'processed_pixel_range': [0, 1], 'nonfinite_values': 0,
        'fingerprint': {'x_sha256': 'features', 'y_sha256': 'labels'}, 'source_url': 'url',
        'source_files': [{'sha256': 'a' * 64, 'frozen_catalogue_hash_verified': True}],
        'physical_matrix_alias_of': None, 'duplicate_map': {'path': 'source_duplicate_maps/source.json', 'sha256': digest(duplicate_path), 'bytes': duplicate_path.stat().st_size},
        'source_order': 'canonical', 'row_id_pattern': 'source:row:index', 'source_selection': 'all rows',
        'construction': None, 'preprocessing_operations': [], 'original_parent_id': 'source', 'original_row_indices': [0, 1, 2],
        'conflict_interpretation': 'Exact cross-class duplicates retained, not relabelled.'}
    audit_path.write_text(json.dumps({'schema': 'parent-source-audit-v1', 'parents': [parent], 'parent_count': 1,
        'available_audited_parents': 1, 'no_official_data_deduplicated': True}))
    return root, initial, duplicate_path


def test_inventory_preserves_frozen_inputs_and_cross_class_duplicate_diagnostics(audited_inventory, tmp_path):
    root, initial, duplicate = audited_inventory
    initial_hash = digest(initial)
    out = tmp_path / 'inventory'
    manifest = build_inventory(out, root)
    row = next(csv.DictReader((out / 'dataset_inventory.csv').open()))
    assert digest(initial) == initial_hash
    assert row['native_resolution'] == row['processed_resolution'] == 'UNVERIFIED'
    assert row['cross_class_duplicate_groups'] == '1'
    assert row['official_input_modified'] == 'False'
    assert row['duplicate_conflict_interpretation'].endswith('not relabelled.')
    assert (out / 'dataset_inventory.csv').read_bytes() == (out / 'dataset_inventory.v2.csv').read_bytes()
    assert manifest['external_data_read'] is False


def test_corrupt_duplicate_evidence_fails_before_replacing_output(audited_inventory, tmp_path):
    root, initial, duplicate = audited_inventory
    out = tmp_path / 'inventory'
    out.mkdir()
    previous = out / 'dataset_inventory.csv'
    previous.write_text('preserved prior inventory\n')
    duplicate.write_text('{}')
    with pytest.raises(ValueError, match='duplicate map missing/hash mismatch'):
        build_inventory(out, root)
    assert previous.read_text() == 'preserved prior inventory\n'


def test_canonical_output_parent_preserves_all_nested_source_audit_inputs(audited_inventory):
    root, initial, duplicate = audited_inventory
    evidence = [initial, root / AUDIT, duplicate]
    before = {path: digest(path) for path in evidence}
    output = root / 'results/submission_refresh'
    manifest = build_inventory(output, root)
    assert all((output / name).is_file() for name in OUTPUT_NAMES)
    assert {path: digest(path) for path in evidence} == before
    assert (output / 'source_audit/source_duplicate_maps').is_dir()
    assert manifest['input_hashes'] == {str(path.relative_to(root)): sha for path, sha in before.items()}


@pytest.mark.parametrize('target_name', OUTPUT_NAMES)
def test_any_output_symlink_to_source_is_rejected_before_other_replacements(audited_inventory, target_name):
    root, initial, duplicate = audited_inventory
    output = root / 'results/submission_refresh'
    evidence = [initial, root / AUDIT, duplicate]
    before = {path: digest(path) for path in evidence}
    originals = {}
    for name in OUTPUT_NAMES:
        target = output / name
        if name == target_name:
            target.symlink_to(root / AUDIT)
        else:
            originals[name] = ('prior output: ' + name + '\n').encode()
            target.write_bytes(originals[name])
    with pytest.raises(ValueError, match='target would replace source evidence'):
        build_inventory(output, root)
    assert (output / target_name).is_symlink()
    assert {path: digest(path) for path in evidence} == before
    assert all((output / name).read_bytes() == raw for name, raw in originals.items())


def test_file_as_output_directory_is_rejected_without_replacement(audited_inventory, tmp_path):
    root, initial, duplicate = audited_inventory
    output = tmp_path / 'file instead of directory'
    output.write_text('preserve existing file\n')
    before = {path: digest(path) for path in [initial, root / AUDIT, duplicate]}
    with pytest.raises(ValueError, match='output must be a directory'):
        build_inventory(output, root)
    assert output.read_text() == 'preserve existing file\n'
    assert {path: digest(path) for path in before} == before
