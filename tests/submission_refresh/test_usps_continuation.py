"""Same-target initialization, budget and immutable-history continuation checks."""
import inspect,json
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest,ResourceLedger,ROOT
from experiments.submission_refresh.usps_continuation import (
    warm_initialization,new_attempt_folder,assert_originals_unchanged,remaining_capacity,load_problem)
from experiments.submission_refresh.usps_continuation import numerical_reference_input_identity,export_results
from experiments.submission_refresh.usps_evaluate import pair_identity


def test_warm_selection_uses_exact_objective_and_feasible_dual_without_labels():
    F=np.array([[0.],[0.],[4.],[4.]])
    W=sparse.csr_matrix(np.array([[0,1,0,0],[1,0,.1,0],[0,.1,0,1],[0,0,1,0.]]))
    candidates=[{'name':'inferior_primal','arrays':{'G':np.full_like(F,50.),'q':np.array([[0.],[-.05],[0.]])}},
                {'name':'better_dual','arrays':{'G':F.copy(),'q':np.array([[0.],[-.1],[0.]])}}]
    G,q,proof=warm_initialization(F,W,1.,candidates)
    np.testing.assert_array_equal(G,F)
    assert proof['primal_source']['record']=='frozen_F'
    assert proof['dual_source']['record']=='better_dual'
    assert proof['initial_dual']>0 and proof['initial_primal']>=proof['initial_dual']
    assert 'y' not in inspect.signature(warm_initialization).parameters


def test_original_history_and_existing_attempt_are_never_overwritten(tmp_path):
    store=ArtifactStore(tmp_path);original=tmp_path/'usps_audit/gamma_1_original.npz';original.parent.mkdir()
    original.write_bytes(b'original-audit-state');sha=digest(original)
    folder=new_attempt_folder(store,'new-numerical-attempt')
    (folder/'result.json').write_text('{"status":"COMPLETED"}')
    with pytest.raises(ValueError,match='immutable'):
        new_attempt_folder(store,'new-numerical-attempt')
    with pytest.raises(ValueError):new_attempt_folder(store,'../usps_audit')
    assert digest(original)==sha and not folder.is_relative_to(original.parent)
    provenance={'original_files_sha256':{'usps_audit/gamma_1_original.npz':sha}}
    assert_originals_unchanged(store,provenance)
    original.write_bytes(b'changed')
    with pytest.raises(ValueError,match='original audit changed'):
        assert_originals_unchanged(store,provenance)


def test_continuation_respects_shared_six_hour_cap_and_other_reservations(tmp_path):
    ledger=ResourceLedger(tmp_path)
    with ledger.locked() as state:
        state['entries']=[{'run_id':'usps-numerical-audit-v1','phase':'mandatory_usps','charged_cpu_seconds':20000,'status':'COMPLETED'}]
    assert ledger.reserve('usps-continuation-test',1800,'mandatory_usps')
    assert ledger.reserve('usps-continuation-other',1000,'mandatory_usps')
    allowed,spent=remaining_capacity({'run_id':'usps-continuation-test','cpu_limit':1800},tmp_path)
    assert spent==20000 and allowed==600
    with ledger.locked() as state:state['active']['usps-numerical-audit-v1']={'seconds':1,'phase':'mandatory_usps'}
    with pytest.raises(ValueError,match='remains active'):
        remaining_capacity({'run_id':'usps-continuation-test','cpu_limit':1800},tmp_path)


def test_input_verification_never_dereferences_label_objects(tmp_path):
    store=ArtifactStore(tmp_path);folder=tmp_path/'usps_audit';folder.mkdir()
    F=np.zeros((9298,10));W=sparse.csr_matrix((9298,9298));pair=pair_identity(F,W)
    refs={'F':store.put(F),'W':store.put(W),'y':{'sha256':'0'*64,'path':'objects/not-a-label-object.npy','kind':'array'}}
    atomic_json(folder/'frozen_pair.json',{'objects':refs})
    np.savez_compressed(folder/'frozen_pair.npz',F=F,W_data=W.data,W_indices=W.indices,W_indptr=W.indptr,W_shape=np.array(W.shape))
    name='gamma_1_IRLS300';np.savez_compressed(folder/(name+'.npz'),G=F,q=np.empty((0,10)))
    meta={'same_frozen_pair':pair,'arrays_file':name+'.npz','arrays_sha256':digest(folder/(name+'.npz')),'variant':'E8','gamma':1.}
    atomic_json(folder/(name+'.json'),meta)
    manifest={'same_frozen_pair':pair,'graph':{'E8_capacities':'2*gamma*w'},'records':[{'name':name,**meta}]}
    atomic_json(folder/'audit_manifest.json',manifest)
    atomic_json(tmp_path/'task_status/usps-numerical-audit-v1.json',{'status':'COMPLETED','manifest':manifest})
    before={p.name:digest(p) for p in folder.iterdir()}
    loaded_F,loaded_W,G,q,initial,provenance=load_problem({'gamma':1.},store)
    assert not provenance['labels_loaded_for_fitting'] and G.shape==F.shape
    assert initial['initial_relative_gap']==0 and q.shape==(0,10)
    assert before=={p.name:digest(p) for p in folder.iterdir()}


def test_fixed_two_attempts_and_separate_rounding_queues():
    fits=json.loads((ROOT/'configs/submission_refresh/usps_continuation_queue.json').read_text())['tasks']
    rounding=json.loads((ROOT/'configs/submission_refresh/usps_continuation_evaluation_queue.json').read_text())['tasks'][0]
    assert [task['gamma'] for task in fits]==[1.,1000.]
    assert all(task['cpu_limit']<=1800 and task['max_iter']==300000 and task['phase']=='mandatory_usps' for task in fits)
    assert rounding['continuation_run_ids']==[task['run_id'] for task in fits]
    assert rounding['cpu_limit']<=900 and rounding['kind']=='usps_continuation_evaluate'


def _input_metadata(root,*,different=False):
    def ref(letter,kind):
        sha=letter*64
        return {'sha256':sha,'path':'objects/'+sha[:2]+'/'+sha+'.npz','kind':kind,'bytes':17}
    audit={'objects':{'F':ref('a','compressed_array'),'W':ref('b','sparse'),
                      'y':{'path':'must-never-be-read'}}}
    subset={'objects':dict(audit['objects'])}
    if different:subset['objects']['W']=ref('c','sparse')
    atomic_json(root/'usps_audit/frozen_pair.json',audit)
    atomic_json(root/'subset/USPS/representation.json',subset)
    return audit,subset


@pytest.mark.parametrize('different',[False,True])
def test_reference_identity_compares_current_input_refs_only_without_loading_arrays(tmp_path,monkeypatch,different):
    audit,subset=_input_metadata(tmp_path,different=different)
    monkeypatch.setattr(np,'load',lambda *a,**k:pytest.fail('metadata view loaded arrays'))
    result=numerical_reference_input_identity(tmp_path)
    assert result['same_current_F_W_content_addresses'] is (not different)
    assert result['sources']['numerical_audit']['objects']=={k:audit['objects'][k] for k in ['F','W']}
    assert result['sources']['subset_search']['sha256']==digest(tmp_path/'subset/USPS/representation.json')
    assert not result['arrays_loaded_for_this_view'] and not result['certificate_transferred_to_locked_IRLS_G']
    assert not result['historical_missing_F_G_identity_established']
    assert 'not certify a different historical-style IRLS G' in result['scope']


def test_reference_identity_missing_is_unknown_and_malformed_refs_fail_before_export(tmp_path):
    result=numerical_reference_input_identity(tmp_path)
    assert result['same_current_F_W_content_addresses'] is None
    assert result['status']=='UNAVAILABLE_CURRENT_INPUT_REFERENCE_COMPARISON'
    audit,_=_input_metadata(tmp_path);audit['objects']['F']['sha256']='not-a-hash'
    atomic_json(tmp_path/'usps_audit/frozen_pair.json',audit)
    output=tmp_path/'exports';output.mkdir();(output/'sentinel').write_text('preserve')
    with pytest.raises(ValueError,match='invalid USPS F/W content-addressed reference'):
        export_results(tmp_path,output)
    assert sorted(p.name for p in output.iterdir())==['sentinel']
