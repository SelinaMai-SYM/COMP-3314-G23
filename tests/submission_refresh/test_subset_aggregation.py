"""Pure scalar and tiny-artifact checks; no dataset fit or score search."""
import csv
import json
from pathlib import Path
import numpy as np
import pytest
import yaml

from experiments.submission_refresh.core import ArtifactStore,digest
from experiments.subset_search import aggregate as aggregation
from experiments.submission_refresh import current_release
from experiments.subset_search.markdown import benchmark_markdown


def test_current_projected_release_uses_the_published_benchmark_view():
    from experiments.subset_search.markdown import _public_mode
    assert _public_mode()


def test_family_distributions_keep_benchmarks_pools_and_alias_weights_separate():
    base={'family':'fixed_membership','pool':'specification_compatible','alias_of':None}
    rows=[{**base,'benchmark':'ORL','candidate_id':'A','acc_mean':10.,'nmi_mean':20.},
          {**base,'benchmark':'ORL','candidate_id':'alias','alias_of':'A','acc_mean':10.,'nmi_mean':20.},
          {**base,'benchmark':'ORL','candidate_id':'B','acc_mean':40.,'nmi_mean':50.},
          {**base,'benchmark':'USPS','candidate_id':'C','acc_mean':99.,'nmi_mean':98.}]
    result=aggregation.family_distributions(rows)
    declared=next(r for r in result if r['benchmark']=='ORL' and r['metric']=='acc_mean' and r['weighting']=='declared_candidates_with_aliases')
    unique=next(r for r in result if r['benchmark']=='ORL' and r['metric']=='acc_mean' and r['weighting']=='unique_physical_inputs')
    assert declared['median']==10. and declared['observations']==3
    assert unique['median']==25. and unique['observations']==2
    assert all(r['median']>=98 for r in result if r['benchmark']=='USPS')


def test_missing_reference_still_has_four_explicit_contrasts():
    rows=aggregation.reference_contrasts([],[],{'MSRA50':'reference'},{'MSRA50':{'adapted'}})
    assert len(rows)==4
    assert all(r['status']=='UNAVAILABLE_INCOMPLETE_REFERENCE' for r in rows)


@pytest.mark.parametrize('public',[False,True])
def test_markdown_reports_native_sd_as_unavailable_and_keeps_empty_pools_explicit(monkeypatch,public):
    from experiments.subset_search import markdown
    monkeypatch.setattr(markdown,'_public_mode',lambda:public)
    paper={'acc':{'ssc':{'ORL':{'mean':50.,'sd':1.}}},'nmi':{'ssc':{'ORL':{'mean':60.,'sd':2.}}}}
    row={'benchmark':'ORL','pool':'adapted','endpoint':'native_best_of_50','candidate_id':'candidate',
         'config_id':'candidate|E8|1|RANDOM','acc_mean':55.,'nmi_mean':65.,'acc_sd':99.,'nmi_sd':99.,
         'paper_acc':50.,'paper_nmi':60.,'paper_acc_sd':1.,'paper_nmi_sd':2.,'seed':3,
         'delta_acc_pp':5.,'delta_nmi_pp':5.,'delta_acc_sd_pp':98.,'delta_nmi_sd_pp':97.,
         'source_specification_deviations':['declared alternative'],'n_samples':400,'n_classes':40,'n':1}
    text=benchmark_markdown('ORL',[row],paper)
    assert '55.000 (single assignment; SD NA)' in text
    assert '99.000' not in text and '+98.000' not in text
    if public:
        assert text.count('No complete eligible configuration')==3
        assert '50.000 ± 1.000' in text and '+5.000 / +5.000' in text
        assert 'Source, resolution or method adaptation' in text
    else:
        assert text.count('UNAVAILABLE: no complete eligible configuration')==3
        assert 'candidate\\|E8\\|1\\|RANDOM' in text
        assert '50.000 +/- 1.000' in text and '+5.000 / +5.000' in text


@pytest.fixture
def tiny_aggregate(tmp_path,monkeypatch):
    root=tmp_path/'checkout';root.mkdir();out=root/'results/subset_search';out.mkdir(parents=True)
    store=ArtifactStore(tmp_path/'scientific store')
    candidates=[]
    policy={'version':'frozen','family_preparation_assumptions':{'YaleB_source_preparation':0},
            'additional_assumptions':{'declared_resize_interpolation_for_cropped_yaleb':1,'input_row_L2':1,'embedding_row_L2':1},
            'paper_deviation_flags':{'native_MSRA16_instead_of32':1,'deterministic_BinAlpha_membership_instead_of_stated_random_sampling':1,'input_row_L2_changes_pixel_vectors':1,'embedding_row_L2_changes_raw_eigenvector_representation':1}}
    for prep in ['Y0','Y2']:
        cid='candidate_'+prep;F=np.array([[1.,0.],[0.,1.],[.5,.5]])+(0 if prep=='Y0' else .1);Fref=store.put(F)
        m=out/'sample_manifests'/f'{cid}.json';m.parent.mkdir(exist_ok=True);m.write_text(json.dumps({'selected_indices':[0,1,2],'candidate_id':cid}))
        candidate={'candidate_id':cid,'benchmark':'YaleB','family':'YaleB_source_preparation','pool':'specification_compatible',
                   'prep':prep,'n':3,'p':2,'classes':2,'fingerprint':{'x_sha256':'input','y_sha256':'labels'},'alias_of':None,
                   'manifest_path':str(m.relative_to(root)),'manifest_sha256':digest(m)}
        candidates.append(candidate)
        folder=store.root/'subset'/cid;folder.mkdir(parents=True)
        (folder/'representation.json').write_text(json.dumps({'fingerprint':candidate['fingerprint'],'objects':{'F':Fref}}))
        trials=[{'seed':i,'acc':.5,'nmi':.5,'inertia':float(i+1),'iterations':2,'warning':''} for i in range(50)]
        (folder/'SC__RANDOM.json').write_text(json.dumps({'status':'COMPLETED','method':'sc','initialization':'RANDOM','trials':trials,'objects':{'G':Fref}}))
        (folder/'E8__1__RANDOM.json').write_text(json.dumps({'candidate_id':cid,'config_id':cid+'|E8__1|RANDOM','status':'COMPLETED','method':'ssc','initialization':'RANDOM','variant':'E8','gamma_nominal':1.,'gamma_effective':1.,'trials':trials,'solver':{'status':'MAX_ITER_REACHED'},'objects':{'G':store.put(F*.9)}}))
        (folder/'source.json').write_text(json.dumps({'source_commit':'fixture','implementation_hash':'source','cache_identity':'cache','environment':{'python':'fixed'}}))
    (out/'candidate_catalogue.json').write_text(json.dumps({'candidates':candidates}))
    configs=root/'configs/subset_search';configs.mkdir(parents=True)
    (configs/'compatibility.yaml').write_text(yaml.safe_dump(policy))
    (configs/'protocol.yaml').write_text(yaml.safe_dump({'version':'frozen','reference_candidates':{'YaleB':'candidate_Y0'}}))
    paperfile=root/'configs/v3/paper_reference.yaml';paperfile.parent.mkdir(parents=True)
    paper={'datasets':['YaleB'],'acc':{'ssc':{'YaleB':{'mean':50.,'sd':1.}}},'nmi':{'ssc':{'YaleB':{'mean':50.,'sd':2.}}}}
    paperfile.write_text(yaml.safe_dump(paper))
    selection=root/'configs/submission_refresh/selection.yaml';selection.parent.mkdir(parents=True);selection.write_text('version: frozen\n')
    monkeypatch.setattr(aggregation,'ROOT',root);monkeypatch.setattr(current_release,'ROOT',root)
    return root,out,store


def test_aggregate_and_no_data_rebuild_preserve_native_and_fixed_endpoints(tiny_aggregate,tmp_path):
    root,out,store=tiny_aggregate
    aggregation.aggregate(store.root,out)
    read=lambda name:list(csv.DictReader((out/name).open()))
    fixed=read('fixed_protocol_summary.csv')
    assert len(fixed)==1 and fixed[0]['prep']=='Y0'
    for row in read('native_best_summary.csv'):
        assert row['n']=='1'
        assert row['acc_sd']==row['nmi_sd']==row['delta_acc_sd_pp']==row['delta_nmi_sd_pp']==''
    contrasts=read('matched_sc_contrasts.csv')
    native=next(r for r in contrasts if r['endpoint']=='native_best_of_50')
    assert native['ssc_selected_seed']==native['sc_selected_seed']=='0'
    assert native['n']=='1' and native['ssc_acc_sd']==native['sc_acc_sd']==''
    manifest=root/'configs/subset_search/release_manifest.json'
    current_release.freeze(out,manifest,store.root)
    rebuilt=tmp_path/'no data rebuild';validation=current_release.rebuild(manifest,rebuilt)
    assert validation['ok'] and validation['trials']==100
    assert (rebuilt/'reference_contrasts.csv').exists()
    assert (rebuilt/'fixed_protocol_family_distributions.csv').exists()
    assert (rebuilt/'matched_sc_contrasts.csv').exists()
    assert (rebuilt/'certified_search_status.csv').read_bytes()==(out/'certified_search_status.csv').read_bytes()
    statuses=read('certified_search_status.csv')
    assert len(statuses)==2 and all(r['historical_complete_configurations']=='2' for r in statuses)
    assert all(r['status']=='UNAVAILABLE_NO_COMPARABLE_CERTIFIED_SEARCH_COVERAGE' and r['certified_closest_config_id']=='' for r in statuses)
    assert (rebuilt/'YaleB.md').read_bytes()==(out/'YaleB.md').read_bytes()


def test_aggregate_rejects_sc_using_different_f(tiny_aggregate):
    root,out,store=tiny_aggregate
    path=store.root/'subset/candidate_Y0/SC__RANDOM.json';row=json.loads(path.read_text())
    row['objects']['G']=store.put(np.zeros((3,2)));path.write_text(json.dumps(row))
    with pytest.raises(ValueError,match='exact saved candidate F'):
        aggregation.aggregate(store.root,out)


def test_confirmation_namespace_scans_historical_sources_and_reuses_lock(tmp_path,monkeypatch):
    import gzip
    root=tmp_path/'checkout';out=root/'results/subset_search';out.mkdir(parents=True)
    (out/'winner_lock.json').write_text(json.dumps({'version':1,'winners':[{'config_id':'locked'}]}))
    old_v2=root/'results/v2_kmeans_protocol/trials.csv';old_v2.parent.mkdir(parents=True)
    old_v2.write_text('rounding_seed,acc,nmi\n1000000,0.5,0.6\n')
    old_v3=root/'results/v3_reproduction/all_trials.csv.gz';old_v3.parent.mkdir(parents=True)
    old_v3.write_bytes(gzip.compress(b'seed,acc,nmi\n0,0.5,0.5\n',mtime=0))
    old_next=root/'results/next_round/records.jsonl';old_next.parent.mkdir(parents=True)
    old_next.write_text(json.dumps({'trials':[{'kmeans_seed':49,'acc':.4,'nmi':.3}]})+'\n')
    own=out/'rounding_confirmation.csv';own.write_text('seed,acc,nmi\n1000050,0.6,0.6\n')
    paths=[old_v2,old_v3,old_next,own];monkeypatch.setattr(aggregation,'ROOT',root)
    used,inventory=aggregation.scan_historical_rounding_seeds(root,paths)
    assert used=={0,49,1000000}
    assert all('rounding_confirmation' not in source['path'] for source in inventory['sources'])
    assert {column for source in inventory['sources'] for column in source['seed_columns']}=={'seed','rounding_seed','kmeans_seed'}
    artifacts=tmp_path/'durable'
    namespace=aggregation.confirmation_namespace(artifacts,out,historical_paths=paths)
    assert namespace['first']==1000050 and namespace['count']==50
    assert namespace['winner_lock_sha256']==digest(out/'winner_lock.json')
    assert len(namespace['historical_inventory']['sources'])==3
    # Own new confirmations must never advance an already frozen namespace.
    own.write_text('seed,acc,nmi\n1000050,0.9,0.9\n1000099,0.8,0.8\n')
    (artifacts/'confirmation/confirm-own.json').write_text(json.dumps({'first_seed':1000050}))
    resumed=aggregation.confirmation_namespace(artifacts,out,historical_paths=paths)
    assert resumed==namespace
    assert json.loads((out/'confirmation_seed_namespace.json').read_text())==namespace
    (out/'winner_lock.json').write_text(json.dumps({'version':1,'winners':[{'config_id':'different'}]}))
    with pytest.raises(ValueError,match='winner lock changed'):
        aggregation.confirmation_namespace(artifacts,out,historical_paths=paths)


def test_completion_keeps_actual_controller_original_failure_and_no_data_evidence(tiny_aggregate,tmp_path):
    root,out,store=tiny_aggregate;folder=store.root/'subset/candidate_Y0'
    original_source=json.loads((folder/'source.json').read_text());controller='experiments/subset_search/complete_failed.py';controller_sha='a'*64
    actual={**original_source,'source_commit':'completion-commit','implementation_hash':'completion-byte-map','source_files':{controller:controller_sha}}
    config=folder/'E8__1__RANDOM.json';record=json.loads(config.read_text())
    record.update(source=actual,completion_provenance={'controller':controller,'controller_sha256':controller_sha,'source':store.put(actual),'implementation_hash':actual['implementation_hash']})
    config.write_text(json.dumps(record))
    active={'method':'ssc','variant':'E8','gamma_nominal':1000.,'stage':'solver'}
    status={'status':'FAILED','source':original_source,'active_configuration':active,'error':'original numerical failure'}
    (folder/'status.json').write_text(json.dumps(status))
    failed=folder/'completion_failures/original.json';failed.parent.mkdir()
    failed.write_text(json.dumps({'original_failure':True,'status':'FAILED_PRESERVED','blocked_points':['E8__1000__'+init for init in aggregation.INITS],'active_configuration':active,'error':'original numerical failure'}))
    attempt=folder/'completion_attempts/independent.json';attempt.parent.mkdir()
    attempt.write_text(json.dumps({'status':'COMPLETED_WITH_PRESERVED_FAILURES','source':actual}))
    (folder/'completion_status.json').write_text(json.dumps({'latest_status':'COMPLETED_WITH_PRESERVED_FAILURES'}))
    aggregation.aggregate(store.root,out)
    rows=list(csv.DictReader((out/'joint_search_summary.csv').open()));row=next(r for r in rows if r['candidate_id']=='candidate_Y0')
    assert row['scientific_source_fingerprint']=='completion-byte-map' and row['controller_sha256']==controller_sha
    coverage=list(csv.DictReader((out/'execution_coverage.csv').open()))
    preserved=[r for r in coverage if r['candidate_id']=='candidate_Y0' and r['gamma_nominal']=='1000.0' and r['variant']=='E8']
    assert len(preserved)==3 and all(r['status']=='FAILED_ORIGINAL_PRESERVED' for r in preserved)
    assert any(r['status']=='MISSING_AFTER_COMPLETION' for r in coverage)
    artifact=json.loads((out/'artifact_manifest.json').read_text())
    assert any(r['record'].endswith('/completion_attempts/independent.json') for r in artifact['records'])
    assert any(r['record']=='subset/candidate_Y0/status.json' for r in artifact['records'])
    manifest=root/'configs/subset_search/release_manifest.json';current_release.freeze(out,manifest,store.root)
    import gzip
    with gzip.open(out/'source_records.json.gz','rt') as stream:registry=json.load(stream)['records']
    assert actual in registry.values() and original_source in registry.values()
    rebuilt=tmp_path/'rebuilt without scientific objects';current_release.rebuild(manifest,rebuilt)
    assert (rebuilt/'completion_records.json.gz').read_bytes()==(out/'completion_records.json.gz').read_bytes()
    assert (rebuilt/'source_records.json.gz').read_bytes()==(out/'source_records.json.gz').read_bytes()
    inventory=list(csv.DictReader((rebuilt/'configuration_inventory.csv').open()))
    assert next(r for r in inventory if r['candidate_id']=='candidate_Y0')['scientific_source_fingerprint']=='completion-byte-map'
