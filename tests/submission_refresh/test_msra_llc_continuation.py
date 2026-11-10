"""Metadata and independent spectral checks for the disclosed dense LLC repair."""
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh.msra_llc_continuation import configurations,eigen_diagnostics


def test_complete_original_grid_and_seed_protocol_are_fixed():
    task={'dataset':'MSRA25_EBSA_16x16'}
    grid=configurations(task)
    assert len(grid)==15 and len({(r['ridge'],r['bandwidth_factor']) for r in grid})==15
    assert all(row['seeds']==list(range(50)) and row['n_neighbors']==5 for row in grid)
    with pytest.raises(ValueError):configurations({**task,'llc_ridge':[.1,1.]})
    with pytest.raises(ValueError):configurations({**task,'seeds':list(range(49))})


def test_independent_Gram_eigenpairs_pass_operator_checks():
    rng=np.random.default_rng(816);R=sparse.csr_matrix(rng.uniform(0,.02,(18,18)))
    residual=np.eye(18)-R.toarray();Gram=residual.T@residual
    values,vectors=np.linalg.eigh(Gram)
    diagnostics=eigen_diagnostics(R,vectors[:,:4],values[:4])
    assert diagnostics['qualified'] and diagnostics['normalized_eigen_residual']<1e-12
    altered=vectors[:,:4].copy();altered[0,0]+=.1
    assert not eigen_diagnostics(R,altered,values[:4])['qualified']


def test_queue_discloses_repair_and_separates_profile_from_formal():
    import json
    from experiments.submission_refresh.core import ROOT
    profile=json.loads((ROOT/'configs/submission_refresh/msra_llc_profile_queue.json').read_text())['tasks'][0]
    queue=json.loads((ROOT/'configs/submission_refresh/msra_llc_continuation_queue.json').read_text())
    formal=queue['tasks'][0]
    assert profile['profile'] and profile['cpu_limit']==120
    assert formal['required_profile_run_id']==profile['run_id']
    assert formal['backend']=='existing_dense_threshold_n_branch'
    assert queue['original_sparse_failure_retained'] and queue['choice_frozen_before_LLC_scores']
    assert not formal.get('profile')
