"""Conditional design/gate/cache checks without executing a real benchmark."""
import json
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh import ensc_campaign as campaign
from experiments.submission_refresh.core import ArtifactStore,digest


def test_frozen_g4_design_has_declared_budgets_and_fair_sc():
    for dataset in campaign.DATASETS:
        configs=campaign.intended_configurations(dataset)
        assert len(configs)==44
        assert len({c['config_id'] for c in configs})==44
        assert sum(c['family']=='original_ssc' for c in configs)==15
        assert sum(c['family']=='S_tau0.95' for c in configs)==5
        assert {c['anchor'] for c in configs if c['family']=='fair_sc'}=={'F0','U'}
        assert next(c for c in configs if c['family']=='S_tau0.95' and c['gamma']==1.)
    with pytest.raises(ValueError):campaign.intended_configurations('retrospectively_chosen_subset')


def test_g3_failure_blocks_any_real_data_loading(tmp_path,monkeypatch):
    gate=tmp_path/'gate.json';gate.write_text(json.dumps({'promotion_passed':False,'decision':'FAILED'}))
    def never(*args,**kwargs):raise AssertionError('input loading must not run before G3 passes')
    monkeypatch.setattr(campaign,'_inputs',never)
    result=campaign.run_ensc({'dataset':'ORL_att92','gate_file':str(gate),'run_id':'blocked'},tmp_path,tmp_path/'objects')
    assert result['status']=='FAILED'
    assert 'G3 completion gate has not passed' in result['error']


def test_exact_count_random_control_preserves_weights_without_labels():
    weights=np.array([.2,.3,.7,1.1])
    W,meta=campaign._random_graph(7,weights,400)
    V,_=campaign._random_graph(7,weights,400)
    np.testing.assert_array_equal(W.toarray(),V.toarray())
    assert W.nnz//2==len(weights) and not W.diagonal().any()
    np.testing.assert_allclose(np.sort(sparse.triu(W,1).data),np.sort(weights))
    assert meta['label_access']=='NONE'


def test_movement_bisection_uses_certificates_and_six_limit(tmp_path,monkeypatch):
    store=ArtifactStore(tmp_path/'artifacts');F=np.ones((2,1))
    make=lambda gamma,movement:{'gamma':gamma,'solver':{'certified':True},'objects':{'G':store.put(F+movement)}}
    target=make(1.,.4);original=[make(.01,.0),make(100.,1.)]
    calls=[]
    def solve_without_labels(anchor,W,meta,objects,source,*,gamma,fit_cpu_limit):
        calls.append(gamma)
        return make(gamma,(np.log10(gamma)+2)/4)
    monkeypatch.setattr(campaign,'_solution',solve_without_labels)
    result=campaign._matched_movement(target,original,F,sparse.eye(2),{},store,{},1.)
    assert len(calls)<=6 and result['status']=='MATCHED_CERTIFIED'
    assert abs(result['matched_movement']-.4)<=.02


def test_graph_cache_fingerprint_ignores_unrelated_editorial_modules(tmp_path,monkeypatch):
    from experiments.submission_refresh import core,graph_repair
    files=['SSC_method/graph_construction.py','method_extension/next_round/certified_solver/solver.py',
           'experiments/v2_kmeans_protocol/kmeans_trials.py','experiments/v2_kmeans_protocol/metrics.py',
           'experiments/next_round/evaluate.py','experiments/submission_refresh/graph_repair.py',
           'method_extension/submission_refresh/ensc.py']
    for name in files:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('value=1\n')
    monkeypatch.setattr(core,'ROOT',tmp_path)
    monkeypatch.setattr(graph_repair,'source_record',lambda:{'implementation_hash':'project_raw_hash','source_files':{},'environment':{'python':'fixed'}})
    old=graph_repair.scientific_source_record()
    editorial=tmp_path/'experiments/submission_refresh/reporting.py';editorial.write_text('entirely_new_editorial_module=True\n')
    p=tmp_path/'SSC_method/graph_construction.py';p.write_text('"""Revised documentation."""\n# English comment\nvalue=1\n')
    assert graph_repair.scientific_source_record()['implementation_hash']==old['implementation_hash']
    p.write_text('value=2\n')
    assert graph_repair.scientific_source_record()['implementation_hash']!=old['implementation_hash']
    assert old['project_source_fingerprint']=='project_raw_hash'


def test_complete_claim_requires_both_sc_anchors_and_all_required_controls():
    records=[]
    trials=[{'seed':seed,'acc':.5,'nmi':.5} for seed in range(50)]
    for definition in campaign.intended_configurations('ORL_att92'):
        records.append({**definition,'status':'COMPLETED','trials':trials,'summary':{'acc_mean':50.,'nmi_mean':50.,'acc_sd':0.,'nmi_sd':0.},
            'solver':{'certified':True},'mass_matching':{'count_qualified':True}})
    assert campaign._select(records)['qualified_for_four_benchmark_claim']
    for omitted in [('fair_sc','U'),('native_ensc_S_tau0.95','native_spectral'),('Wa','F0')]:
        subset=[r for r in records if not (r['family']==omitted[0] and r['anchor']==omitted[1])]
        result=campaign._select(subset)
        assert not result['qualified_for_four_benchmark_claim'] and result['missing_required_configurations']
    records[2]={**records[2],'solver':{'certified':False}}
    assert not campaign._select(records)['qualified_for_four_benchmark_claim']


def test_saved_g4_record_requires_exact_graph_anchor_source_and_available_objects(tmp_path):
    import copy
    store=ArtifactStore(tmp_path/'store');F=np.array([[0.],[1.],[2.]])
    graph=sparse.csr_matrix([[0.,1.,0.],[1.,0.,1.],[0.,1.,0.]])
    definition=campaign.intended_configurations('ORL_att92')[0]
    context={'schema':'G4-resume-context-v1','definition':definition,'graph':store.put(graph),'graph_shape':[3,3],'graph_nnz':4,
        'anchor':store.put(F),'scientific_source_fingerprint':'exact-fit-source','construction_source_fingerprint':None}
    predictions=store.put(np.zeros((50,3),dtype=int))
    record={**definition,'resume_context':context,'status':'COMPLETED','source':{'implementation_hash':'exact-fit-source'},
        'trials':[{'seed':seed,'acc':.5,'nmi':.5} for seed in range(50)],'objects':{'G':store.put(F),'anchor':store.put(F),'predictions':predictions},
        'graph_objects':{'fitted_W':context['graph']}}
    assert campaign._verify_saved_record(record,definition,context,store,set()) is record
    changed=copy.deepcopy(context);changed['scientific_source_fingerprint']='different-controller'
    with pytest.raises(ValueError,match='context mismatch'):campaign._verify_saved_record(record,definition,changed,store,set())
    changed=copy.deepcopy(record);changed['graph_objects']['fitted_W']=store.put(graph*2)
    with pytest.raises(ValueError,match='actual graph'):campaign._verify_saved_record(changed,definition,context,store,set())
    (store.root/predictions['path']).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='corrupt'):campaign._verify_saved_record(record,definition,context,store,set())
