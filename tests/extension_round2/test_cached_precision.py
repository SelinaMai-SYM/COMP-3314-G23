"""Target-specific cache qualification and immutable-fit audit compatibility."""
import json
from pathlib import Path
import pytest
from experiments.extension_round2.calibration import MovementPath
from experiments.extension_round2.common import ROOT,source_files
from experiments.extension_round2.report import registered_derivation_difference


def test_cache_certification_is_recomputed_for_the_requested_target():
    result={'certified':True,'valid_bound':True,'relative_gap':8.302878796197233e-7,'stable_relative_gap':8.302878796197233e-7,'movement_error':0.00042715095768294743,'movement':.0201}
    assert MovementPath.certified(result,.05)
    assert not MovementPath.certified(result,.02)
    assert not MovementPath.matched(result,.02)
    # A flag from a stricter target cannot veto a valid looser-target reuse.
    result.update(certified=False,movement=.1,movement_error=.0015)
    assert MovementPath.certified(result,.1) and MovementPath.matched(result,.1)
    result['relative_gap']=2e-6
    assert not MovementPath.certified(result,.1)


def test_report_compatibility_rejects_objective_or_operator_changes():
    amendment=json.loads((ROOT/'configs/extension_round2/derivation_compatibility.json').read_text())
    current=source_files();original=dict(current);name=amendment['source_change']['path'];original[name]=amendment['source_change']['before_sha256']
    assert registered_derivation_difference(original,current,amendment['original_fitting_source_fingerprint']).startswith('derivation_compatibility.json')
    changed=dict(current);changed['method_extension/extension_round2/models.py']='0'*64
    with pytest.raises(ValueError,match='Unregistered source difference'):
        registered_derivation_difference(original,changed,amendment['original_fitting_source_fingerprint'])
    assert registered_derivation_difference(current,current,'new-independent-study') is None
