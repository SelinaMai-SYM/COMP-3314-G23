"""Frontend-only validation of the frozen campaign configuration contract.

The scientific runners consume their preregistered constants and canonical
configuration identities. This module rejects unsupported overrides before
frontends read campaign inputs or create artifact stores/workers.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = {
    'subset': ('configs/subset_search/protocol.yaml',
        '339bc600672ff04c7fdbb74e49ee596178ffa55b3df518cb8621cc131ed3ea28'),
    'refresh': ('configs/submission_refresh/campaign.yaml',
        '9a4755975e8ca8b8706582fb2a5df1dc5b530727a2bc49af7869a80bf6a9bbdd'),
}


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require_frozen_config(supplied, contract, *, root=None):
    """Accept the canonical file or a byte-identical copy, never overrides."""
    if contract not in CONTRACTS:
        raise ValueError('unknown frozen campaign contract: ' + str(contract))
    relative, expected = CONTRACTS[contract]
    canonical = (Path(root).resolve() if root is not None else ROOT) / relative
    supplied = Path(supplied).expanduser().resolve()
    for role, path in [('canonical', canonical), ('supplied', supplied)]:
        try: observed = _sha(path)
        except OSError as exc:
            raise ValueError(f'{contract} {role} configuration is unavailable: {path}') from exc
        if observed != expected:
            raise ValueError(f'{contract} {role} configuration does not match the frozen campaign contract: {path}. '
                'This command accepts only the canonical configuration or a byte-identical copy; '
                'unsupported settings, additional keys and formatting changes are rejected. '
                'A different protocol requires a separately versioned campaign.')
    return {'contract': contract, 'canonical_path': str(canonical),
        'supplied_path': str(supplied), 'sha256': expected}


def _candidate_lookup(catalogue):
    candidates = catalogue.get('candidates')
    if not isinstance(candidates, list) or not candidates:
        raise ValueError('candidate catalogue must contain a nonempty candidate list')
    if any(not isinstance(candidate, dict) or not isinstance(candidate.get('candidate_id'), str)
        or not candidate['candidate_id'] for candidate in candidates):
        raise ValueError('candidate catalogue has an invalid candidate ID')
    lookup = {candidate['candidate_id']: candidate for candidate in candidates}
    if len(lookup) != len(candidates):
        raise ValueError('candidate catalogue contains duplicate candidate IDs')
    return lookup


def _ids(values, name, *, allow_empty=False):
    if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
        raise ValueError(name + ' must be a list of nonempty candidate IDs')
    if not values and not allow_empty:
        raise ValueError(name + ' must be nonempty; an empty cohort cannot be executed')
    if len(set(values)) != len(values):
        raise ValueError(name + ' contains duplicate candidate IDs')
    return values


def require_cohort(cohort, catalogue, catalogue_path, *, allow_empty=False):
    """Check identity and canonical membership before task/store creation."""
    if not isinstance(cohort, dict):
        raise ValueError('frozen cohort must be a JSON object')
    expected = cohort.get('catalogue_sha256')
    if not isinstance(expected, str) or expected != _sha(catalogue_path):
        raise ValueError('frozen cohort catalogue SHA mismatch')
    lookup = _candidate_lookup(catalogue)
    ids = _ids(cohort.get('candidate_ids'), 'frozen cohort candidate_ids', allow_empty=allow_empty)
    unknown = sorted(set(ids) - lookup.keys())
    if unknown:
        raise ValueError('frozen cohort contains unknown candidate IDs: ' + ', '.join(unknown))
    aliases = [value for value in ids if lookup[value].get('alias_of')]
    if aliases:
        raise ValueError('frozen cohort requires canonical candidate IDs, not aliases: ' + ', '.join(aliases))
    return ids


def require_profile_ids(ids, catalogue):
    """Unknown or duplicated explicit profiles must not silently run nothing."""
    values = _ids(ids, 'profile candidate IDs')
    lookup = _candidate_lookup(catalogue)
    unknown = sorted(set(values) - lookup.keys())
    if unknown:
        raise ValueError('unknown profile candidate IDs: ' + ', '.join(unknown))
    return values
