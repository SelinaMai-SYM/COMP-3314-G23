"""Current numerical/conditional views rebuild from committed scalars alone."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import pytest
from experiments.submission_refresh import scalar_evidence as evidence
from experiments.submission_refresh import ensc_campaign
from experiments.submission_refresh.core import atomic_json
from experiments.submission_refresh.inventory import AUDIT,INITIAL


def ref(name):
    sha=hashlib.sha256(name.encode()).hexdigest()
    return {'sha256':sha,'path':'objects/'+sha[:2]+'/'+sha+'.npz','kind':'compressed_array','bytes':1}


def trials(acc=.5,nmi=.6):
    return [{'seed':seed,'acc':acc,'nmi':nmi,'inertia':float(seed+1),'iterations':1,'warning':''} for seed in range(50)]


def baseline(tmp_path,monkeypatch):
    root=tmp_path/'checkout with spaces';art=tmp_path/'external records';project=Path(__file__).resolve().parents[2]
    for relative in ['configs/v3/paper_reference.yaml','configs/submission_refresh/selection.yaml']:
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(project/relative,path)
    atomic_json(art/'baseline/unit/result.json',{'dataset':'JAFFE','method':'lda_existing','config_id':'unit|limit30','status':'COMPLETED','trials':trials()})
    monkeypatch.setattr(evidence,'ROOT',root)
    return root,art,root/'results/submission_refresh'


def add_ensc_and_gate(art,locked_failure=False):
    for dataset in ensc_campaign.DATASETS:
        inputs={name:ref(dataset+name) for name in ['X','y','F0','U']}
        job=art/'ensc_jobs'/dataset
        atomic_json(job/'status.json',{'task':{'dataset':dataset},'status':'COMPLETED','source':{'implementation_hash':'construction'}})
        for i,definition in enumerate(ensc_campaign.intended_configurations(dataset)):
            graph=definition['graph'];native=definition['anchor']=='native_spectral';uses_ensc=graph.startswith('S_tau')
            context={'schema':'G4-resume-context-v1','definition':definition,'input_objects':inputs,
                'anchor':None if native else inputs[definition['anchor']],'graph':ref(dataset+graph),'graph_shape':[10,10],'graph_nnz':20,
                'graph_metadata_fingerprint':graph,'scientific_source_fingerprint':'science',
                'construction_source_fingerprint':'construction' if uses_ensc else None,'backend_source_sha256':'backend' if uses_ensc else None,
                'environment':{'python':'fixture'},'rounding':{'initialization':'GREEDY','n_init':1,'seeds':list(range(50))}}
            acc,nmi=(.7,.8) if definition['family']=='S_tau0.95' else (.65,.75) if definition['family']=='original_ssc' else (.61,.71) if definition['family']=='fair_sc' else (.64,.74)
            if locked_failure and definition['family']=='S_tau0.95' and definition['gamma']==1.:acc,nmi=.6,.7
            atomic_json(job/'records'/f'{i:02}.json',{**definition,'resume_context':context,'status':'COMPLETED',
                'trials':trials(acc,nmi),'summary':{'acc_mean':0.,'nmi_mean':0.},'solver':{'certified':True},
                'mass_matching':{'count_qualified':True},'objects':{'G':inputs['F0']},
                'source':{'implementation_hash':'construction' if native else 'science','source_commit':'fixture'}})
    dataset='ORL_att92';objects={key:ref(dataset+key) for key in ['X','y','F0','U','A','W0']}
    atomic_json(art/f'graph_inputs/{dataset}/fixed/representation.json',{'dataset':dataset,'source':{'implementation_hash':'science'},'objects':objects})
    for arm,acc,fragments in [('delete',.5,10),('both',.52,7),('blind_400',.51,9),('blind_401',.51,9),('blind_402',.51,9)]:
        atomic_json(art/f'graph_records/{dataset}/fixed/{arm}.json',{'dataset':dataset,'config_id':dataset+'|G3|'+arm,'phase':'G3',
            'arm':arm,'anchor':'F0','gamma':1000.,'addition_fraction':.15,'status':'COMPLETED','trials':trials(acc,.6),
            'source':{'implementation_hash':'science'},'objects':{'anchor':objects['F0']},
            'solver':{'certified':True,'gap':1e-7,'edge_violation':0.,'node_violation':0.,'normalized_L21_movement':.01},
            'graph_diagnostics':{'within_class_excess_fragments':fragments}})


def add_usps(art):
    record={'dataset':'USPS','config_id':'USPS|original','name':'original','status':'COMPLETED','n_trials':50,
        'n_samples':9298,'n_classes':10,'trials':trials(.4,.5),'summary':{'acc_mean':0.},'pair_identity':{'F':'same','W':'same'},
        'audit_metadata':{'cpu_seconds':7.,'linear_checks':{'cg_calls':3,'cg_failures':1}}}
    atomic_json(art/'usps_audit/evaluation/job/generation/original.json',record)
    atomic_json(art/'usps_continuations/extra/result.json',{'task':{'run_id':'extra','gamma':1.},'status':'COMPLETED',
        'solver':{'status':'PRIMAL_DUAL_GAP_CERTIFIED','certified':True,'gap':1e-6,'primal':2.,'dual':1.999999},'cpu_seconds':30.})
    atomic_json(art/'usps_continuation_evaluation/job/generation/extra.json',{**record,'config_id':'USPS|extra','name':'extra','trials':trials(.45,.55)})


def test_full_scalar_views_rebuild_without_arrays_objects_data_or_git(tmp_path,monkeypatch):
    root,art,out=baseline(tmp_path,monkeypatch);add_ensc_and_gate(art);add_usps(art)
    from experiments.submission_refresh.usps_continuation import numerical_reference_input_identity
    identity_view=numerical_reference_input_identity(art)
    atomic_json(out/'usps_numerical_reference_input_identity.json',identity_view)
    # Other tests cover bootstrap numerics; this fixture tests shared derivation.
    import experiments.next_round.evaluate as evaluate
    monkeypatch.setattr(evaluate,'paired',lambda a,b,metric:{'delta_pp':100*(a[0][metric]-b[0][metric]),'ci_lower_pp':0.,'ci_upper_pp':1.})
    evidence.freeze(art,out);manifest=root/'configs/submission_refresh/evidence_manifest.json'
    shutil.rmtree(art)
    from experiments.submission_refresh.core import ArtifactStore
    monkeypatch.setattr(ArtifactStore,'__init__',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('no object store in scalar rebuild')))
    monkeypatch.setattr(__import__('subprocess'),'check_output',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('no Git in scalar rebuild')))
    destination=root/'independent rebuild';gate=evidence.rebuild(manifest,destination)
    assert gate['G4_G5_status']=='COMPLETE_CERTIFIED_FOUR_BENCHMARKS'
    assert gate['four_benchmark_ACC_gain_pp']==pytest.approx(5.)
    assert gate['four_benchmark_NMI_gain_vs_SC_pp']==pytest.approx(9.)
    assert gate['four_benchmark_NMI_gain_vs_SSC_pp']==pytest.approx(5.)
    assert gate['four_benchmark_NMI_gain_pp'] is None
    original=next(csv.DictReader((destination/'usps_solver_evaluation.csv').open()))
    extra=next(csv.DictReader((destination/'usps_continuation_evaluation.csv').open()))
    assert float(original['acc_mean'])==pytest.approx(40.) and float(extra['acc_mean'])==pytest.approx(45.)
    assert json.loads(original['native_best'])['acc_sd'] is None
    assert len(list(csv.DictReader((destination/'ensc_execution_coverage.csv').open())))==176
    assert json.loads((destination/'evidence_validation.json').read_text())['external_artifact_read'] is False
    assert json.loads((destination/'usps_numerical_reference_input_identity.json').read_text())==identity_view


def test_incomplete_USPS_seeds_fail_before_freeze_replaces_existing_release(tmp_path,monkeypatch):
    root,art,out=baseline(tmp_path,monkeypatch);evidence.freeze(art,out)
    manifest=root/'configs/submission_refresh/evidence_manifest.json';before=manifest.read_bytes();add_usps(art)
    path=art/'usps_audit/evaluation/job/generation/original.json';record=json.loads(path.read_text());record['trials'].pop();atomic_json(path,record)
    with pytest.raises(ValueError,match='incomplete'):evidence.freeze(art,out)
    assert manifest.read_bytes()==before


def test_empty_ensc_requires_explicit_NOT_RUN():
    with pytest.raises(ValueError,match='NOT_RUN'):
        ensc_campaign.derive_ensc_metadata({'schema':'ensc-scalar-metadata-v1','conditional_status':'COMPLETED','jobs':[],'records':[]})
    derived=ensc_campaign.derive_ensc_metadata({'schema':'ensc-scalar-metadata-v1','conditional_status':'NOT_RUN','jobs':[],'records':[]})
    assert derived['macro']['status']=='NOT_RUN' and derived['macro']['four_benchmark_ACC_gain_pp'] is None


def test_inventory_inputs_are_hash_locked_and_rebuilt_from_committed_maps(tmp_path,monkeypatch):
    # Reuse the independent source-inventory fixture without loading raw data.
    import runpy
    audited_inventory=runpy.run_path(str(Path(__file__).with_name('test_inventory.py')))['audited_inventory']
    fixture_root,initial,duplicate=audited_inventory.__wrapped__(tmp_path)
    root,art,out=baseline(tmp_path/'release',monkeypatch)
    for source in [initial,fixture_root/AUDIT,duplicate]:
        target=root/source.relative_to(fixture_root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    evidence.freeze(art,out);manifest=root/'configs/submission_refresh/evidence_manifest.json'
    destination=root/'rebuilt';evidence.rebuild(manifest,destination)
    assert (destination/'dataset_inventory.csv').read_bytes()==(destination/'dataset_inventory.v2.csv').read_bytes()
    info=json.loads(manifest.read_text());relative=str((root/duplicate.relative_to(fixture_root)).relative_to(root))
    assert relative in info['inventory_inputs'] and relative in info['files']
    (root/relative).write_text('{}')
    prior=(destination/'dataset_inventory.csv').read_bytes()
    with pytest.raises(ValueError,match='hash mismatch'):evidence.rebuild(manifest,destination)
    assert (destination/'dataset_inventory.csv').read_bytes()==prior


def test_live_USPS_exports_and_pure_views_are_byte_identical(tmp_path):
    from experiments.submission_refresh.scalar_views import collect_usps_metadata,derive_usps_views,write_usps_views
    from experiments.submission_refresh.usps_evaluate import export_evaluation
    from experiments.submission_refresh.usps_continuation import export_results
    art=tmp_path/'records';add_usps(art)
    pure=tmp_path/'pure';write_usps_views(derive_usps_views(collect_usps_metadata(art)),pure)
    live=tmp_path/'live';export_evaluation(art,live);export_results(art,live)
    for name in ['usps_solver_evaluation.csv','usps_solver_evaluation_trials.csv.gz',
                 'usps_continuation_audit.csv','usps_continuation_evaluation.csv','usps_continuation_trials.csv.gz']:
        assert (pure/name).read_bytes()==(live/name).read_bytes()


def test_oracle_pass_locked_fail_keeps_fixed_point_and_live_frozen_parity(tmp_path,monkeypatch):
    root,art,out=baseline(tmp_path,monkeypatch);add_ensc_and_gate(art,locked_failure=True)
    import experiments.next_round.evaluate as evaluate
    monkeypatch.setattr(evaluate,'paired',lambda a,b,metric:{'delta_pp':100*(a[0][metric]-b[0][metric]),'ci_lower_pp':0.,'ci_upper_pp':1.})
    live=tmp_path/'live';macro=ensc_campaign.aggregate_ensc(art,live)
    locked=macro['locked_label_free_operating_point']
    assert macro['practical_target_met'] is True and locked['practical_target_met'] is False
    assert macro['parameter_selection_gap'] is True
    assert locked['fixed_parameters']=={'tau':.95,'source_gamma':50,'SSC_gamma':1}
    assert locked['four_benchmark_ACC_gain_pp']==pytest.approx(-5.)
    assert locked['four_benchmark_NMI_gain_vs_SC_pp']==pytest.approx(-1.)
    assert locked['four_benchmark_NMI_gain_vs_SSC_pp']==pytest.approx(-5.)
    for oracle,point in zip(macro['dataset_status'],locked['dataset_status']):
        assert point['qualified'] and point['ACC_loss_exceeds_1pp']
        assert oracle['fair_SC_config_id']==point['fair_SC_config_id']
        assert oracle['fair_SSC_config_id']==point['fair_SSC_config_id']
        assert point['proposed_config_id'].endswith('|F0|1.0')
        assert point['proposed_config_id']!=oracle['proposed_config_id']
    incomplete=ensc_campaign.collect_ensc_metadata(art)
    incomplete['records']=[entry for entry in incomplete['records'] if not (entry['record']['dataset']=='USPS' and entry['record']['family']=='fair_sc' and entry['record']['anchor']=='U')]
    partial=ensc_campaign.derive_ensc_metadata(incomplete)['macro']
    assert partial['parameter_selection_gap'] is None
    partial_locked=partial['locked_label_free_operating_point']
    assert partial_locked['practical_target_met'] is None and partial_locked['four_benchmark_ACC_gain_pp'] is None
    assert all(row['ACC_gain_vs_stronger_fair_baseline_pp'] is None and row['NMI_gain_vs_SC_pp'] is None and row['NMI_gain_vs_SSC_pp'] is None and row['ACC_loss_exceeds_1pp'] is None for row in partial_locked['dataset_status'])
    evidence.freeze(art,out);shutil.rmtree(art)
    rebuilt=tmp_path/'frozen';gate=evidence.rebuild(root/'configs/submission_refresh/evidence_manifest.json',rebuilt)
    assert (live/'ensc_four_benchmark_conclusion.json').read_bytes()==(rebuilt/'ensc_four_benchmark_conclusion.json').read_bytes()
    assert gate['parameter_selection_gap'] is True
    assert gate['locked_label_free_operating_point']==locked


def test_full_graph_coverage_is_hash_locked_copied_and_semantically_validated(tmp_path,monkeypatch):
    import runpy
    from experiments.submission_refresh.graph_coverage import build_graph_coverage
    from experiments.submission_refresh.core import digest
    fixture=runpy.run_path(str(Path(__file__).with_name('test_inventory.py')))['audited_inventory']
    inventory_root,initial,duplicate=fixture.__wrapped__(tmp_path)
    root,art,out=baseline(tmp_path/'release',monkeypatch)
    for source in [initial,inventory_root/AUDIT,duplicate]:
        target=root/source.relative_to(inventory_root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    project=Path(__file__).resolve().parents[2]
    queue=root/'configs/submission_refresh/graph_queue.json';shutil.copy2(project/'configs/submission_refresh/graph_queue.json',queue)
    build_graph_coverage(art,out,root=root)
    evidence.freeze(art,out);manifest=root/'configs/submission_refresh/evidence_manifest.json'
    frozen=json.loads(manifest.read_text())
    for name in ['graph_execution_coverage.csv','graph_coverage_manifest.json']:
        relative=str((out/name).relative_to(root))
        assert relative in frozen['files'] and relative in frozen['supplementary_files']
    assert str(queue.relative_to(root)) in frozen['files']
    shutil.rmtree(art);rebuilt=root/'rebuilt';evidence.rebuild(manifest,rebuilt)
    assert len(list(csv.DictReader((rebuilt/'graph_execution_coverage.csv').open())))==362
    for name in ['graph_execution_coverage.csv','graph_coverage_manifest.json']:
        assert (out/name).read_bytes()==(rebuilt/name).read_bytes()
    # Correct hashes alone cannot legitimize a truncated intended design.
    path=out/'graph_execution_coverage.csv';lines=path.read_bytes().splitlines(keepends=True);path.write_bytes(b''.join(lines[:-1]))
    coverage_path=out/'graph_coverage_manifest.json';coverage=json.loads(coverage_path.read_text());coverage['coverage_sha256']=digest(path);atomic_json(coverage_path,coverage)
    for changed in [path,coverage_path]:frozen['files'][str(changed.relative_to(root))].update(sha256=digest(changed),bytes=changed.stat().st_size)
    atomic_json(manifest,frozen);prior=(rebuilt/'graph_execution_coverage.csv').read_bytes()
    with pytest.raises(ValueError,match='all 362 tasks'):evidence.rebuild(manifest,rebuilt)
    assert (rebuilt/'graph_execution_coverage.csv').read_bytes()==prior


def test_USPS_metadata_key_order_does_not_change_scalar_CSVs(tmp_path):
    import copy
    from experiments.submission_refresh.scalar_views import collect_usps_metadata,derive_usps_views,write_usps_views
    art=tmp_path/'records';add_usps(art);metadata=collect_usps_metadata(art)
    shuffled=copy.deepcopy(metadata)
    for track in ['original_evaluations','continuation_evaluations']:
        for entry in shuffled[track]:entry['record']=dict(reversed(list(entry['record'].items())))
    first=tmp_path/'first';second=tmp_path/'second'
    write_usps_views(derive_usps_views(metadata),first);write_usps_views(derive_usps_views(shuffled),second)
    assert {path.name:path.read_bytes() for path in first.iterdir()}=={path.name:path.read_bytes() for path in second.iterdir()}


def test_rebuilt_diagnostics_expose_shared_flattened_counts_without_unknown_as_zero(tmp_path,monkeypatch):
    root,art,out=baseline(tmp_path,monkeypatch)
    path=art/'baseline/unit/result.json';record=json.loads(path.read_text())
    record['diagnostics']=[{'termination_reason':'stable','lda_update_successes':0,'lda_update_failures':2},
        {'status':'failed_without_update_counter','error':'preserved failure'},
        {'termination_reason':'cap','lda_update_successes':3,'lda_update_failures':1,'returned_state_consistent':False}]
    atomic_json(path,record);evidence.freeze(art,out);rebuilt=root/'rebuilt';evidence.rebuild(root/'configs/submission_refresh/evidence_manifest.json',rebuilt)
    row=next(csv.DictReader((rebuilt/'baseline_diagnostics.csv').open()))
    expected=evidence.diagnostic_view(evidence._diagnostic_summary(record['diagnostics']))
    assert json.loads(row['termination_counts'])==expected['termination_counts']
    assert int(row['update_failures_total'])==expected['update_failures_total']==3
    assert int(row['no_successful_lda_update_runs'])==expected['no_successful_lda_update_runs']==1
    assert int(row['returned_state_inconsistent_runs'])==1
