"""Unsupported CLI settings must fail before data, artifacts or workers."""
import importlib
import json
import sys
import pytest

from experiments.submission_refresh import config_contract as contract


@pytest.fixture
def frozen_checkout(tmp_path):
    root = tmp_path / 'checkout'
    for relative, expected in contract.CONTRACTS.values():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((contract.ROOT / relative).read_bytes())
    return root


@pytest.mark.parametrize('name', ['subset', 'refresh'])
def test_frozen_contract_accepts_identical_copy_and_rejects_changed_canonical(frozen_checkout, tmp_path, name):
    relative, expected = contract.CONTRACTS[name]
    canonical = frozen_checkout / relative
    copied = tmp_path / ('copy-' + name + '.yaml')
    copied.write_bytes(canonical.read_bytes())
    assert contract.require_frozen_config(copied, name, root=frozen_checkout)['sha256'] == expected
    canonical.write_bytes(canonical.read_bytes() + b'\n# changed canonical bytes\n')
    with pytest.raises(ValueError, match='canonical configuration does not match'):
        contract.require_frozen_config(copied, name, root=frozen_checkout)


@pytest.mark.parametrize('module,name,change', [
    ('experiments.subset_search.__main__', 'subset', ('k: 5', 'k: 7')),
    ('experiments.submission_refresh.__main__', 'refresh', ('rss_target_gib: 8', 'rss_target_gib: 1')),
])
def test_changed_cli_config_fails_before_any_campaign_path_access(tmp_path, monkeypatch, module, name, change):
    frontend = importlib.import_module(module)
    relative, _ = contract.CONTRACTS[name]
    original = (contract.ROOT / relative).read_text()
    assert change[0] in original
    supplied = tmp_path / 'unsupported.yaml'
    supplied.write_text(original.replace(*change))
    artifact = tmp_path / 'untouched scientific artifacts'
    output = tmp_path / 'untouched output'
    def forbidden_path(*args, **kwargs):
        raise AssertionError('campaign path accessed before rejecting unsupported configuration')
    monkeypatch.setattr(frontend, 'Path', forbidden_path)
    monkeypatch.setattr(sys, 'argv', ['campaign', 'run', '--config', str(supplied),
        '--artifact-root', str(artifact), '--data-root', str(tmp_path / 'missing data'), '--output', str(output)])
    with pytest.raises(ValueError, match='supplied configuration does not match'):
        frontend.main()
    assert not artifact.exists() and not output.exists()


@pytest.fixture
def tiny_catalogue(tmp_path):
    path = tmp_path / 'candidate_catalogue.json'
    catalogue = {'candidates': [{'candidate_id': 'A', 'alias_of': None},
        {'candidate_id': 'B', 'alias_of': None}, {'candidate_id': 'alias', 'alias_of': 'A'}]}
    path.write_text(json.dumps(catalogue))
    return path, catalogue, {'catalogue_sha256': contract._sha(path), 'candidate_ids': ['A', 'B']}


def test_cohort_accepts_only_unique_known_canonical_members(tiny_catalogue):
    path, catalogue, cohort = tiny_catalogue
    assert contract.require_cohort(cohort, catalogue, path) == ['A', 'B']
    assert contract.require_cohort({**cohort, 'candidate_ids': []}, catalogue, path, allow_empty=True) == []


@pytest.mark.parametrize('patch,message', [
    ({'catalogue_sha256': 'wrong'}, 'catalogue SHA mismatch'),
    ({'candidate_ids': []}, 'must be nonempty'),
    ({'candidate_ids': ['A', 'A']}, 'duplicate candidate IDs'),
    ({'candidate_ids': ['unknown']}, 'unknown candidate IDs'),
    ({'candidate_ids': ['alias']}, 'canonical candidate IDs'),
])
def test_bad_cohort_is_rejected(tiny_catalogue, patch, message):
    path, catalogue, cohort = tiny_catalogue
    with pytest.raises(ValueError, match=message):
        contract.require_cohort({**cohort, **patch}, catalogue, path)


@pytest.mark.parametrize('phase', ['run', 'complete-failed'])
def test_cli_bad_cohort_fails_before_artifact_or_worker_access(tmp_path, monkeypatch, tiny_catalogue, phase):
    from experiments.subset_search import __main__ as frontend
    from experiments.submission_refresh import core, scheduler
    path, catalogue, cohort = tiny_catalogue
    out = tmp_path / 'existing committed catalogue'
    out.mkdir()
    (out / 'candidate_catalogue.json').write_bytes(path.read_bytes())
    cohort_path = tmp_path / 'bad cohort.json'
    cohort_path.write_text(json.dumps({**cohort, 'candidate_ids': ['unknown']}))
    artifact = tmp_path / 'untouched artifacts'
    def forbidden(*args, **kwargs):
        raise AssertionError('artifact/worker accessed before validating frozen cohort')
    monkeypatch.setattr(core, 'ArtifactStore', forbidden)
    monkeypatch.setattr(scheduler, 'run', forbidden)
    monkeypatch.setattr(sys, 'argv', ['subset', phase, '--config', str(contract.ROOT / contract.CONTRACTS['subset'][0]),
        '--output', str(out), '--cohort', str(cohort_path), '--artifact-root', str(artifact)])
    with pytest.raises(ValueError, match='unknown candidate IDs'):
        frontend.main()
    assert not artifact.exists()
    assert not (out / 'completion_queue.json').exists()


def test_cli_unknown_profile_ids_do_not_silently_start_empty_work(tmp_path, monkeypatch, tiny_catalogue):
    from experiments.subset_search import __main__ as frontend
    from experiments.submission_refresh import scheduler
    path, catalogue, cohort = tiny_catalogue
    out = tmp_path / 'catalogue'
    out.mkdir()
    (out / 'candidate_catalogue.json').write_bytes(path.read_bytes())
    artifact = tmp_path / 'untouched artifacts'
    def forbidden(*args, **kwargs):
        raise AssertionError('worker accessed with unknown profile IDs')
    monkeypatch.setattr(scheduler, 'run', forbidden)
    monkeypatch.setattr(sys, 'argv', ['subset', 'profile', '--config', str(contract.ROOT / contract.CONTRACTS['subset'][0]),
        '--output', str(out), '--artifact-root', str(artifact), '--candidates', 'unknown'])
    with pytest.raises(ValueError, match='unknown profile candidate IDs'):
        frontend.main()
    assert not artifact.exists()
