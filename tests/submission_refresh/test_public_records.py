"""Public metadata preserves scientific evidence without raw runtime records."""
import copy
import csv
import gzip
import json
from pathlib import Path
import shutil
import pytest
from experiments.submission_refresh import public_records as public,scalar_evidence as evidence
from experiments.submission_refresh.core import atomic_json,digest,identity


def receipt(path,evidence_hash):
    value={'schema':public.ARCHIVE_SCHEMA,'verified':True,'archive_id':'scientific-archive-fixture-v1',
        'archive_sha256':'a'*64,'bytes':123,'recovered_objects':4,'recovered_extra_files':0,
        'recovery_proof_sha256':'b'*64,'raw_release_inputs':{
            'source_records':{'sha256':'c'*64,'uncompressed_sha256':'d'*64},
            'current_release_manifest':{'sha256':'e'*64},'evidence_manifest':{'sha256':evidence_hash},
            'artifact_manifests':{'refresh_sha256':'f'*64,'subset_sha256':'1'*64},
            'seed_inventory_proof':{'sha256':'2'*64},'original_namespace':{'sha256':'3'*64}}}
    atomic_json(path,value);return value


def source():
    return {'source_commit':'original-commit','implementation_hash':'original-scientific-fingerprint',
        'cache_identity':'original-cache','source_files':{'SSC_method/optimizer.py':'a'*64},
        'working_tree_dirty':True,'cwd':'/Users/private/worktree','command':['internal','watcher'],
        'source_archive':{'path':'objects/raw-source.json','sha256':'b'*64,'kind':'json'},
        'environment':{'python':'3.13.3','packages':{'numpy':'2.4.2'},'platform':'Darwin-arm64','hostname':'private-host'},
        'thread_libraries':[{'internal_api':'openblas','version':'1','num_threads':1,'filepath':'/Users/private/libblas.dylib'}]}


def test_source_projection_keeps_original_identity_as_reference_with_distinct_payload_hash():
    raw=source();before=copy.deepcopy(raw);projected=public.public_source_payload(raw)
    assert projected['source_commit']==raw['source_commit'] and projected['implementation_hash']==raw['implementation_hash']
    assert projected['source_files']==raw['source_files'] and projected['cache_identity']==raw['cache_identity']
    assert projected['environment']['packages']=={'numpy':'2.4.2'} and projected['thread_libraries'][0]['num_threads']==1
    assert not {'cwd','command','source_archive','working_tree_dirty'}&projected.keys()
    assert 'hostname' not in projected['environment'] and 'filepath' not in projected['thread_libraries'][0]
    assert raw==before and identity(raw)!=identity(projected)
    value,proof=public.project_record({'source':raw,'config_id':'scientific-id','status':'FAILED'},'baseline')
    assert value['original_source_record_sha256']==identity(raw)
    assert value['public_source_record_sha256']==identity(projected)
    assert proof['original_record_sha256']!=proof['public_record_sha256']


def test_numeric_objectives_failures_kkt_and_costs_survive_without_tracebacks():
    raw={'status':'FAILED','error':.125,'source_error':.25,'kkt_residual':1.2e-7,'cpu_seconds':12.5,
        'diagnostics':[{'seed':4,'error':.5,'inertia':8.,'lda_update_failures':2}],
        'seed_failures':[{'seed':7,'error':'CG failed info=17 in /Users/private/2026/source.py','traceback':'private stack'}],
        'traceback':'private stack','cwd':'/Users/private/worktree','task':{'dataset':'JAFFE','run_id':'scientific-fit','command':['watcher'],'queue':'private'}}
    result=public.public_metadata_payload(raw)
    assert result['error']==.125 and result['source_error']==.25 and result['kkt_residual']==1.2e-7
    assert result['cpu_seconds']==12.5 and result['diagnostics']==raw['diagnostics']
    failure=result['seed_failures'][0]
    assert failure['seed']==7 and failure['error']=='CG_NONCONVERGENCE' and '17' in failure['reported_failure_values']
    assert '2026' not in failure['reported_failure_values']
    assert not {'traceback','cwd'}&result.keys() and 'traceback' not in failure
    assert result['task']=={'dataset':'JAFFE'}
    assert '/Users/' not in json.dumps(result)
    projected,_=public.project_record({'rounding_signature':'a'*64,'status':'COMPLETED'},'usps')
    assert projected['rounding_signature']=='a'*64


def test_coverage_projection_cleans_nested_csv_json_but_keeps_scientific_keys():
    rows=[{'configuration_id':'fixed-config','dataset':'JAFFE','seed':'7','status':'FAILED','source_queue':'private.json',
        'controller_evidence':json.dumps([{'path':'/Users/private/status.json'}]),
        'solver_certificates':json.dumps([{'gap':1e-5,'certified':False,'run_id':'internal','source_record':'/Users/private/baseline/fixed/record.json'}]),
        'evidence_record':'/Users/private/baseline/fixed/state7.json'}]
    projected=public.public_coverage_rows(rows)[0]
    assert projected['configuration_id']=='fixed-config' and projected['seed']=='7' and projected['status']=='FAILED'
    assert 'source_queue' not in projected and 'controller_evidence' not in projected
    assert projected['solver_certificates'][0]['gap']==1e-5 and 'run_id' not in projected['solver_certificates'][0]
    assert projected['evidence_record']=='baseline/fixed/state7.json'
    assert '/Users/' not in json.dumps(projected)


@pytest.mark.parametrize('change',['unverified','extra','path','count','proof','missing_seed_proof'])
def test_archive_receipt_is_strict_and_cannot_be_an_unverified_reference(tmp_path,change):
    path=tmp_path/'receipt.json';value=receipt(path,'0'*64)
    if change=='unverified':value['verified']=False
    elif change=='extra':value['cwd']='/Users/private'
    elif change=='path':value['archive_id']='../private/archive'
    elif change=='count':value['bytes']=True
    elif change=='proof':value['recovery_proof_sha256']='not-a-hash'
    else:value['raw_release_inputs'].pop('seed_inventory_proof')
    atomic_json(path,value)
    with pytest.raises(ValueError):public.read_archive_receipt(path)


def raw_release(tmp_path,monkeypatch,with_graph=False):
    root=tmp_path/'raw checkout';art=tmp_path/'raw external metadata';out=root/'results/submission_refresh'
    project=Path(__file__).resolve().parents[2]
    for name in ['configs/v3/paper_reference.yaml','configs/submission_refresh/selection.yaml']:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(project/name,path)
    record={'dataset':'JAFFE','method':'lda_existing','config_id':'locked|limit30','status':'COMPLETED','source':source(),
        'trials':[{'seed':seed,'acc':.7,'nmi':.8} for seed in range(50)],'max_iter':30,
        'diagnostics':[{'seed':seed,'source_error':float(50-seed),'error':float(seed),'lda_update_failures':1,'lda_update_successes':2} for seed in range(50)]}
    atomic_json(art/'baseline/fixed/record.json',record)
    atomic_json(art/'baseline/fixed/input.json',{'metadata':{'archive_path':'/Users/private/data.mat','native_resolution':[16,16]}})
    atomic_json(out/'resource_usage.json',{'limit_seconds':129600,'max_workers':2,'active':{},'entries':[
        {'run_id':'private-internal-id','phase':'baseline','status':'COMPLETED','charged_cpu_seconds':12.5}]})
    if with_graph:
        from experiments.submission_refresh.graph_coverage import build_graph_coverage
        target=root/'configs/submission_refresh/graph_queue.json';shutil.copy2(project/'configs/submission_refresh/graph_queue.json',target)
        build_graph_coverage(art,out,root=root)
    monkeypatch.setattr(evidence,'ROOT',root);evidence.freeze(art,out)
    manifest=root/'configs/submission_refresh/evidence_manifest.json'
    proof=tmp_path/'verified-private-archive-receipt.json';receipt(proof,digest(manifest))
    return root,art,out,manifest,proof


def test_public_scalar_package_rebuilds_after_raw_checkout_and_store_are_removed(tmp_path,monkeypatch):
    root,art,out,manifest,proof=raw_release(tmp_path,monkeypatch)
    original_manifest=manifest.read_bytes();original_packet=(out/'baseline_records.public.v2.jsonl.gz').read_bytes()
    public_root=tmp_path/'public package';result=evidence.project_existing_release(manifest,public_root,archive_receipt=proof)
    assert manifest.read_bytes()==original_manifest and (out/'baseline_records.public.v2.jsonl.gz').read_bytes()==original_packet
    public_manifest=Path(result['manifest_path']);definition=json.loads(public_manifest.read_text())
    assert definition['schema']==evidence.PUBLIC_SCHEMA
    with gzip.open(public_root/definition['baseline_file'],'rt') as stream:row=json.loads(next(stream))
    assert row['trials'][0]=={'seed':0,'acc':.7,'nmi':.8} and len(row['source_native_values'])==50
    assert row['source_native_values'][0]['value']==50. and row['source']['implementation_hash']=='original-scientific-fingerprint'
    assert '/Users/' not in json.dumps(row) and 'traceback' not in json.dumps(row)
    resources=json.loads((public_root/'results/submission_refresh/resource_usage.json').read_text())
    assert resources['total_cpu_seconds']==12.5 and 'private-internal-id' not in json.dumps(resources)
    shutil.rmtree(art);shutil.rmtree(root)
    from experiments.submission_refresh.core import ArtifactStore
    monkeypatch.setattr(ArtifactStore,'__init__',lambda *args:(_ for _ in ()).throw(AssertionError('no store during public rebuild')))
    rebuilt=tmp_path/'rebuilt only public metadata';evidence.rebuild(public_manifest,rebuilt)
    actual=list(csv.DictReader((rebuilt/'baseline_diagnostics.csv').open()))[0]
    assert float(actual['acc_mean'])==pytest.approx(70.) and float(actual['nmi_mean'])==pytest.approx(80.)
    native=list(csv.DictReader((rebuilt/'baseline_source_native_diagnostics.csv').open()))[0]
    assert native['selected_seed']=='49' and native['pool']=='diagnostic_only'


def test_public_graph_coverage_keeps_all_362_scientific_configs_without_a_queue(tmp_path,monkeypatch):
    root,art,out,manifest,proof=raw_release(tmp_path,monkeypatch,with_graph=True)
    public_root=tmp_path/'public';result=evidence.project_existing_release(manifest,public_root,archive_receipt=proof)
    public_manifest=Path(result['manifest_path']);definition=json.loads(public_manifest.read_text())
    assert 'configs/submission_refresh/graph_queue.json' not in definition['files']
    design=public_root/'configs/submission_refresh/graph_design.public.v1.json'
    assert len(json.loads(design.read_text())['configurations'])==362
    path=public_root/'results/submission_refresh/graph_execution_coverage.csv'
    rows=list(csv.DictReader(path.open()));assert len(rows)==362
    assert 'run_id' not in rows[0] and 'controller_evidence' not in rows[0]
    shutil.rmtree(art);shutil.rmtree(root)
    evidence.rebuild(public_manifest,tmp_path/'rebuilt graph coverage')


def test_wrong_archive_receipt_fails_before_any_publication(tmp_path,monkeypatch):
    root,art,out,manifest,proof=raw_release(tmp_path,monkeypatch)
    value=json.loads(proof.read_text());value['raw_release_inputs']['evidence_manifest']['sha256']='0'*64;atomic_json(proof,value)
    public_root=tmp_path/'not published';before=manifest.read_bytes()
    with pytest.raises(ValueError,match='does not cover'):evidence.project_existing_release(manifest,public_root,archive_receipt=proof)
    assert not public_root.exists() and manifest.read_bytes()==before


def test_public_resource_summary_refuses_a_live_ledger():
    with pytest.raises(ValueError,match='finalized'):public.final_resource_summary({'active':{'unfinished':{'seconds':1}},'entries':[]})


def test_public_full_current_packet_keeps_graph_and_USPS_metrics_without_originals(tmp_path,monkeypatch):
    import runpy
    helpers=runpy.run_path(str(Path(__file__).with_name('test_full_scalar_evidence.py')))
    root,art,out,manifest,proof=raw_release(tmp_path,monkeypatch)
    helpers['add_graph_gate'](art);helpers['add_usps'](art)
    import experiments.next_round.evaluate as evaluate
    import experiments.submission_refresh.graph_repair as graph
    monkeypatch.setattr(evaluate,'paired',lambda *args,**kwargs:{'delta_pp':0.,'ci_lower_pp':0.,'ci_upper_pp':0.})
    monkeypatch.setattr(graph,'paired_interval',lambda a,b:{'delta_pp':100*float(a[0]-b[0]),'ci_lower_pp':1.,'ci_upper_pp':3.})
    evidence.freeze(art,out);receipt(proof,digest(manifest))
    raw_output=tmp_path/'raw derived';raw_gate=evidence.rebuild(manifest,raw_output)
    public_root=tmp_path/'public current';result=evidence.project_existing_release(manifest,public_root,archive_receipt=proof)
    shutil.rmtree(art);shutil.rmtree(root)
    from experiments.submission_refresh.core import ArtifactStore
    monkeypatch.setattr(ArtifactStore,'__init__',lambda *args:(_ for _ in ()).throw(AssertionError('public rebuild cannot open scientific arrays')))
    monkeypatch.setattr(__import__('subprocess'),'check_output',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('public rebuild cannot read Git')))
    public_output=tmp_path/'public derived';public_gate=evidence.rebuild(result['manifest_path'],public_output)
    for key in ['decision','promotion_passed','datasets']:
        assert public_gate[key]==raw_gate[key]
    for name in ['usps_solver_evaluation.csv','usps_continuation_evaluation.csv']:
        raw=list(csv.DictReader((raw_output/name).open()));projected=list(csv.DictReader((public_output/name).open()))
        assert [(r['config_id'],r['acc_mean'],r['acc_sd'],r['nmi_mean'],r['nmi_sd']) for r in raw]==[(r['config_id'],r['acc_mean'],r['acc_sd'],r['nmi_mean'],r['nmi_sd']) for r in projected]


def test_public_payload_mapping_cannot_be_bypassed_by_rehashing_the_outer_file(tmp_path,monkeypatch):
    root,art,out,manifest,proof=raw_release(tmp_path,monkeypatch)
    result=evidence.project_existing_release(manifest,tmp_path/'public',archive_receipt=proof)
    path=Path(result['manifest_path']);definition=json.loads(path.read_text());package=path.parents[2]
    packet=package/definition['baseline_file']
    with gzip.open(packet,'rt') as stream:rows=[json.loads(line) for line in stream if line.strip()]
    rows[0]['trials'][0]['acc']=.71
    compressed,uncompressed=evidence._gzip_bytes(rows);packet.write_bytes(compressed)
    definition['files'][definition['baseline_file']].update(sha256=digest(packet),bytes=len(compressed),uncompressed_sha256=uncompressed)
    atomic_json(path,definition)
    output=tmp_path/'preserved user output';output.mkdir();(output/'keep.txt').write_text('keep')
    with pytest.raises(ValueError,match='payload hashes'):evidence.rebuild(path,output)
    assert (output/'keep.txt').read_text()=='keep'
