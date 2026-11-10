"""Gate provenance and full scientific recovery need no benchmark fits."""
import json
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh import aggregate as refresh
from experiments.submission_refresh import export_artifacts
from experiments.submission_refresh.core import ArtifactStore,atomic_json


def test_gate_cannot_mix_fixed_input_versions_or_anchor_objects(tmp_path):
    store=ArtifactStore(tmp_path/'store');dataset='ORL_att92';version='frozen-input'
    F=np.arange(6.).reshape(3,2);y=np.array([0,1,1]);W=sparse.csr_matrix(np.ones((3,3))-np.eye(3))
    objects={key:store.put(value) for key,value in [('X',F),('y',y),('F0',F),('U',F),('A',W),('W0',W)]}
    meta={'dataset':dataset,'source':{'implementation_hash':'frozen-fit-source'},'objects':objects}
    atomic_json(store.root/'graph_inputs'/dataset/version/'representation.json',meta)
    path=store.root/'graph_records'/dataset/version/'G3.json'
    row={'source':meta['source'],'status':'COMPLETED','anchor':'F0','objects':{'anchor':objects['F0']}}
    provenance=refresh._gate_input_identity(store,dataset,[(path,row)])
    assert provenance['input_version']==version and provenance['fixed_input_objects']['F0']==objects['F0']
    different=path.parent.parent/'other-input'/'G3.json'
    with pytest.raises(ValueError,match='multiple graph input versions'):refresh._gate_input_identity(store,dataset,[(path,row),(different,row)])
    wrong={**row,'objects':{'anchor':store.put(F+1)}}
    with pytest.raises(ValueError,match='exact fixed anchor'):refresh._gate_input_identity(store,dataset,[(path,wrong)])
    wrong={**row,'source':{'implementation_hash':'different-fit-source'}}
    with pytest.raises(ValueError,match='mix scientific source'):refresh._gate_input_identity(store,dataset,[(path,wrong)])


def test_graph_pool_ensc_rows_movement_and_raw_cases_survive_full_export(tmp_path,monkeypatch):
    store=ArtifactStore(tmp_path/'durable');root=tmp_path/'checkout';monkeypatch.setattr(export_artifacts,'ROOT',root)
    matrix=np.arange(12.).reshape(4,3);ref=store.put(matrix)
    pool=np.array([[0,1],[2,3]]);pool_ref=store.put(pool)
    atomic_json(store.root/'graph_inputs/ORL/frozen/representation.json',{'objects':{'X':ref}})
    atomic_json(store.root/'graph_inputs/ORL/frozen/frozen_label_blind_pool.json',{'objects':{'edges':pool_ref}})
    atomic_json(store.root/'ensc_coefficients/frozen/rows/0.json',{'row':0,'values':store.put(np.array([.1,.2]))})
    atomic_json(store.root/'ensc_jobs/frozen/status.json',{'matched_movement':{'attempts':[{'objects':{'G':ref}}]}})
    cases=store.root/'graph_jobs/frozen/input/error_cases.csv';cases.parent.mkdir(parents=True);cases.write_bytes(b'sample_id,case\n0,full-record\n')
    records,extras=refresh._register_scientific_tree(store,[])
    atomic_json(root/'results/submission_refresh/artifact_manifest.json',{'records':records,'extra_files':extras})
    archive=tmp_path/'scientific.tar.gz';export_artifacts.export(store.root,archive);output=tmp_path/'recovered'
    export_artifacts.recover(archive,output)
    np.testing.assert_array_equal(ArtifactStore(output).get(ref),matrix)
    np.testing.assert_array_equal(ArtifactStore(output).get(pool_ref),pool)
    assert (output/'graph_jobs/frozen/input/error_cases.csv').read_bytes()==cases.read_bytes()
    assert json.loads((output/'ensc_jobs/frozen/status.json').read_text())['matched_movement']['attempts'][0]['objects']['G']==ref
    assert (output/'ensc_coefficients/frozen/rows/0.json').exists()
    archive_bytes=archive.read_bytes();cases.write_bytes(b'changed after registration')
    with pytest.raises(ValueError,match='raw scientific file missing or changed'):export_artifacts.export(store.root,archive)
    assert archive.read_bytes()==archive_bytes


def test_extension_gate_reports_actual_ensc_status_and_separate_qualified_NMI(tmp_path,monkeypatch):
    from experiments.submission_refresh import ensc_campaign
    store=ArtifactStore(tmp_path/'store');calls=[]
    macro={'status':'COMPLETE_CERTIFIED_FOUR_BENCHMARKS','four_benchmark_ACC_gain_pp':2.3,
        'four_benchmark_NMI_gain_vs_SC_pp':.4,'four_benchmark_NMI_gain_vs_SSC_pp':.2,'practical_target_met':True,
        'dataset_status':[{'dataset':name,'qualified':True} for name in ensc_campaign.DATASETS]}
    def collect(artifact_root,output):calls.append(str(artifact_root));return macro
    monkeypatch.setattr(ensc_campaign,'aggregate_ensc',collect)
    gate={'promotion_passed':True,'decision':'PASSED'}
    before=refresh._ensc_extension_metadata(gate,store,tmp_path/'out')
    assert before['G4_G5_status']=='TRIGGERED_NOT_RUN' and not calls
    atomic_json(store.root/'ensc_jobs/formal/status.json',{'task':{'dataset':'ORL_att92'},'status':'COMPLETED'})
    complete=refresh._ensc_extension_metadata(gate,store,tmp_path/'out')
    assert complete['G4_G5_status']==macro['status'] and len(calls)==1
    assert complete['four_benchmark_ACC_gain_pp']==2.3
    assert complete['four_benchmark_NMI_gain_vs_SC_pp']==.4 and complete['four_benchmark_NMI_gain_vs_SSC_pp']==.2
    assert complete['four_benchmark_NMI_gain_pp'] is None
    macro.update(status='INCOMPLETE_FOUR_BENCHMARK_COMPARISON')
    partial=refresh._ensc_extension_metadata(gate,store,tmp_path/'out')
    assert partial['four_benchmark_ACC_gain_pp'] is None and partial['four_benchmark_NMI_gain_vs_SC_pp'] is None
    macro['status']='COMPLETE_CERTIFIED_FOUR_BENCHMARKS'
    blocked=refresh._ensc_extension_metadata({'promotion_passed':False,'decision':'FAILED'},store,tmp_path/'out')
    assert blocked['G4_G5_status']=='NOT_RUN_GATE_NOT_PASSED'
    assert blocked['four_benchmark_ACC_gain_pp'] is None and blocked['ensc_records_not_qualified_by_current_G3_gate']
