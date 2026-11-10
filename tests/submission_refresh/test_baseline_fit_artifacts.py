"""Regression checks for recoverable baseline state and declared paired controls."""
import json
from pathlib import Path
import numpy as np
from baselines.spls.spls import oneshot_shrunk_patterns
from baselines.llc import llc_normalized_embedding,yu_shi_discretize_state
from experiments.submission_refresh.baselines import slps_configurations


def test_slps_fit_state_observes_same_solution_and_exact_system():
    X=np.random.default_rng(41).normal(size=(14,5))
    ordinary,info=oneshot_shrunk_patterns(X,.5,5)
    recorded,observed=oneshot_shrunk_patterns(X,.5,5,return_state=True)
    np.testing.assert_array_equal(ordinary,recorded)
    state=observed.pop('fit_state')
    assert observed==info
    np.testing.assert_allclose(state['coefficient']@recorded,.5*X,rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(state['affinity'].toarray(),state['affinity'].toarray().T)


def test_llc_raw_normalized_and_rotation_state_are_consistent():
    X=np.random.default_rng(14).normal(size=(20,5))
    F,info=llc_normalized_embedding(X,3,5,1.,'gaussian',1.,return_state=True)
    state=info['fit_state']
    np.testing.assert_allclose(F,state['raw_embedding']/np.maximum(state['row_norms'],1e-12))
    assert state['regression_matrix'].shape==(20,20)
    fitted=yu_shi_discretize_state(F,7,300,1e-7)
    np.testing.assert_array_equal(fitted['labels'],np.argmax(F@fitted['rotation'],axis=1))
    target=np.eye(3)[fitted['labels']]
    np.testing.assert_allclose(fitted['objective'],np.sum((target-F@fitted['rotation'])**2))


def test_declared_slps_extras_preserve_reported_alpha_dimension_and_rounding():
    root=Path(__file__).resolve().parents[2]
    queue=json.loads((root/'configs/submission_refresh/execution_queue.json').read_text())
    expected={'JAFFE':(.95,70),'ORL_att92':(.85,40),'YaleB_dengcai32':(.2,70),'YaleB_cropped2414':(.2,70)}
    for task in queue['tasks']:
        if task.get('block')!='slps':continue
        configs=slps_configurations(task)
        assert len([c for c in configs if c['role']=='primary_paired_grid'])==18
        if task['dataset'] in expected:
            alpha,dimension=expected[task['dataset']]
            extras=[c for c in configs if c['role']=='paired_existing_reported_setting']
            assert {(c['n_neighbors'],c['alpha'],c['dimension'],c['initialization']) for c in extras}=={
                (k,alpha,dimension,'SKLEARN_GREEDY_KMEANSPP') for k in [5,7]}
        else:assert task['dataset']=='MSRA25_EBSA_16x16' and not task['extra_configs']
