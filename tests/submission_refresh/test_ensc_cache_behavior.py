"""EnSC effective-code cache checks using source metadata and dummy builders."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse

from experiments.submission_refresh import ensc_campaign as campaign
from experiments.submission_refresh.core import ArtifactStore, atomic_json, digest

MODULE = 'experiments/submission_refresh/ensc_campaign.py'
LOADER = 'experiments/submission_refresh/baselines.py'


@pytest.fixture
def source_text():
    return Path(campaign.__file__).read_text()


def changed_input(text):
    old = 'F0,info=spectral_embedding(X,K_VALUES[dataset],k=5)'
    assert old in text
    return text.replace(old, old.replace('k=5', 'k=7'), 1)


def changed_native(text):
    old = 'generator=np.random.default_rng(20261108)'
    assert old in text
    return text.replace(old, 'generator=np.random.default_rng(20261109)', 1)


def test_input_native_and_constants_are_effective_code_but_reporting_is_not(source_text):
    initial = campaign._adapter_behavior('construction', source_text)['fingerprint']
    input_initial = campaign._adapter_behavior('input', source_text)['fingerprint']
    editorial = source_text.replace('Reuse a matching full G3 input, never a retrospectively chosen subset.',
        'Reworded input-helper documentation.') + '\n# A reporting-only editorial comment.\n'
    editorial = editorial.replace("'four_benchmark_ACC_gain_pp':None", "'editorial_label_only':None")
    # The replacement above is in scalar views, outside the fitting-helper set.
    assert campaign._adapter_behavior('construction', editorial)['fingerprint'] == initial
    assert campaign._adapter_behavior('input', editorial)['fingerprint'] == input_initial
    assert campaign._adapter_behavior('construction', changed_input(source_text))['fingerprint'] != initial
    assert campaign._adapter_behavior('input', changed_input(source_text))['fingerprint'] != input_initial
    assert campaign._adapter_behavior('construction', changed_native(source_text))['fingerprint'] != initial
    assert campaign._adapter_behavior('input', changed_native(source_text))['fingerprint'] == input_initial
    constants = source_text.replace("'ORL_att92':40", "'ORL_att92':41", 1)
    assert campaign._adapter_behavior('input', constants)['fingerprint'] != input_initial


def test_rebinding_imports_invalidates_unchanged_input_native_and_rounding_helpers(source_text):
    baseline = campaign._adapter_behavior('construction', source_text)['fingerprint']
    input_baseline = campaign._adapter_behavior('input', source_text)['fingerprint']
    input_import = 'from SSC_method.spectral_embedding import spectral_embedding,orient_eigenvector_signs'
    assert input_import in source_text
    rebound_input = source_text.replace(input_import,
        'from another_implementation import spectral_embedding,orient_eigenvector_signs', 1)
    assert campaign._adapter_behavior('input', rebound_input)['fingerprint'] != input_baseline
    rebound_native = source_text.replace('from scipy.sparse.csgraph import laplacian',
        'from another_implementation import laplacian', 1)
    assert campaign._adapter_behavior('construction', rebound_native)['fingerprint'] != baseline
    external = {LOADER: (campaign.ROOT / LOADER).read_text(),
        'experiments/subset_search/runner.py': (campaign.ROOT / 'experiments/subset_search/runner.py').read_text()}
    external['experiments/subset_search/runner.py'] = external['experiments/subset_search/runner.py'].replace(
        'from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,RANDOM,VANILLA,GREEDY',
        'from another_implementation import fit_lloyd,RANDOM,VANILLA,GREEDY', 1)
    assert campaign._adapter_behavior('construction', source_text, external_sources=external)['fingerprint'] != baseline


def test_construction_fingerprint_rejects_stale_native_resume_without_fitting(tmp_path, monkeypatch, source_text):
    def base_source(**kwargs):
        return {'implementation_hash': 'fixed-graph-backend', 'environment': {'python': 'fixed'}, 'source_files': {}}
    monkeypatch.setattr(campaign, 'scientific_source_record', base_source)
    original = campaign._construction_source()
    modified = tmp_path / 'new adapter.py'
    modified.write_text(changed_native(source_text))
    monkeypatch.setattr(campaign, '__file__', str(modified))
    updated = campaign._construction_source()
    assert original['implementation_hash'] != updated['implementation_hash']
    store = ArtifactStore(tmp_path / 'objects')
    ref = store.put(np.eye(3))
    meta = {'objects': {key: ref for key in ['X', 'y', 'F0', 'U']},
        'ensc_input_adapter_fingerprint': campaign._adapter_behavior('input')['fingerprint']}
    definition = next(row for row in campaign.intended_configurations('ORL_att92') if row['anchor'] == 'native_spectral')
    old = campaign._resume_context(definition, sparse.eye(3), None, meta, store, base_source(), original, {})
    new = campaign._resume_context(definition, sparse.eye(3), None, meta, store, base_source(), updated, {})
    with pytest.raises(ValueError, match='context mismatch'):
        campaign._verify_saved_record({**definition, 'resume_context': old}, definition, new, store, set())


def test_archived_g3_input_behavior_accepts_editorial_changes_and_rejects_changed_constructor(tmp_path, monkeypatch, source_text):
    store = ArtifactStore(tmp_path / 'metadata')
    archive = {MODULE: source_text, LOADER: (campaign.ROOT / LOADER).read_text()}
    source = {'source_files': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in archive.items()},
        'source_archive': store.put(archive)}
    meta = {'source': source}
    modified = tmp_path / 'adapter source.py'
    modified.write_text(source_text + '\n# Harmless editorial change.\n')
    monkeypatch.setattr(campaign, '__file__', str(modified))
    proof = campaign._g3_input_compatibility(meta, store, campaign._adapter_behavior('input'))
    assert proof['mode'] == 'VERIFIED_ARCHIVED_FITTING_AST'
    modified.write_text(changed_input(source_text))
    with pytest.raises(ValueError, match='incompatible EnSC input-adapter fitting behavior'):
        campaign._g3_input_compatibility(meta, store, campaign._adapter_behavior('input'))
    modified.write_text(source_text + '\n# Harmless editorial change.\n')
    broken = copy.deepcopy(meta)
    broken['source']['source_files'][MODULE] = 'not-the-archived-file-hash'
    with pytest.raises(ValueError, match='does not match its recorded source bytes'):
        campaign._g3_input_compatibility(broken, store, campaign._adapter_behavior('input'))


def test_matching_g3_reuses_exact_saved_f0_without_rewriting_or_calling_builder(tmp_path, monkeypatch):
    from experiments.submission_refresh import baselines
    store = ArtifactStore(tmp_path / 'scientific objects')
    X = np.arange(80., dtype=float).reshape(40, 2)
    y = np.arange(40)
    F0 = np.eye(40)
    zero = sparse.csr_matrix((40, 40))
    source = {'implementation_hash': 'same-graph-source', 'environment': {'python': 'fixed'},
        'source_files': {MODULE: digest(campaign.__file__), LOADER: digest(campaign.ROOT / LOADER)}}
    arrays = {'X': X, 'y': y, 'F0': F0, 'U': F0, 'A': zero, 'W0': zero, 'Wa_raw': zero}
    meta = {'dataset': 'ORL_att92', 'K': 40, 'input_preparation': 'Y0', 'source': source,
        'objects': {name: store.put(value) for name, value in arrays.items()}}
    path = store.root / 'graph_inputs/ORL_att92/frozen/representation.json'
    atomic_json(path, meta)
    before = path.read_bytes()
    monkeypatch.setattr(baselines, 'load', lambda *args: (X, y, {}))
    def never(*args, **kwargs): raise AssertionError('matching saved G3 F0 must not be refitted')
    monkeypatch.setattr(campaign, 'spectral_embedding', never)
    folder, reused, values = campaign._inputs('ORL_att92', tmp_path, store, source)
    assert folder == path.parent
    assert path.read_bytes() == before
    assert reused['objects']['F0'] == meta['objects']['F0']
    np.testing.assert_array_equal(values['F0'], F0)


def test_own_f0_cache_changes_with_input_helper_but_not_editorial_bytes(tmp_path, monkeypatch, source_text):
    from experiments.submission_refresh import baselines
    store = ArtifactStore(tmp_path / 'scientific objects')
    X = np.arange(80., dtype=float).reshape(40, 2)
    y = np.arange(40)
    source = {'implementation_hash': 'same-graph-source', 'environment': {'python': 'fixed'}}
    monkeypatch.setattr(baselines, 'load', lambda *args: (X, y, {}))
    calls = []
    def dummy_builder(*args, **kwargs):
        calls.append(True)
        return np.eye(40), {}
    monkeypatch.setattr(campaign, 'spectral_embedding', dummy_builder)
    monkeypatch.setattr(campaign, 'knn_affinity', lambda array, **kwargs: (sparse.csr_matrix((len(array), len(array))), {}))
    monkeypatch.setattr(campaign, 'angular_graph', lambda array: sparse.csr_matrix((len(array), len(array))))
    original, _, _ = campaign._inputs('ORL_att92', tmp_path, store, source)
    modified = tmp_path / 'adapter source.py'
    modified.write_text(source_text + '\n# Harmless editorial change.\n')
    monkeypatch.setattr(campaign, '__file__', str(modified))
    editorial, _, _ = campaign._inputs('ORL_att92', tmp_path, store, source)
    assert editorial == original and len(calls) == 1
    modified.write_text(changed_input(source_text))
    changed, _, _ = campaign._inputs('ORL_att92', tmp_path, store, source)
    assert changed != original and len(calls) == 2
