"""No-data current release replay and fail-before-write integrity checks."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil

import pytest
import yaml
from experiments.submission_refresh import current_release as release
from experiments.submission_refresh.core import digest
from experiments.submission_refresh.selection import summarize,distances,rank
from experiments.submission_refresh.csv_transport import pack_large_csvs


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        fields=list(dict.fromkeys(key for row in rows for key in row))
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)


@pytest.fixture
def scalar_fixture(tmp_path,monkeypatch):
    root=tmp_path/'checkout with spaces';root.mkdir()
    output=root/'results/subset_search';output.mkdir(parents=True)
    configs=root/'configs/subset_search';configs.mkdir(parents=True)
    (configs/'protocol.yaml').write_text('version: fixed\n')
    selection=root/'configs/submission_refresh/selection.yaml';selection.parent.mkdir(parents=True);selection.write_text('version: joint\n')
    paper={'acc':{'ssc':{'ORL':{'mean':50.,'sd':1.}}},'nmi':{'ssc':{'ORL':{'mean':50.,'sd':2.}}}}
    pp=root/'configs/v3/paper_reference.yaml';pp.parent.mkdir(parents=True);pp.write_text(yaml.safe_dump(paper))
    rows=[];trials=[];candidates=[];source_root=tmp_path/'external scientific objects'
    for i,(cid,gamma,acc,nmi) in enumerate([('A',1.,.50,.10),('B',1000.,.55,.55)]):
        config_id=f'{cid}|E8|{gamma}|RANDOM'
        base={'candidate_id':cid,'config_id':config_id,'benchmark':'ORL','family':'fixed',
              'pool':'specification_compatible','n_samples':10,'n_classes':2,'prep':'Y0','variant':'E8',
              'gamma_nominal':gamma,'gamma_effective':gamma,'initialization':'RANDOM',
              'solver_status':'ITERATE_CONVERGED_UNCERTIFIED','endpoint':'mean_sample_sd_50',
              'paper_deviations':0,'preparation_assumptions':1,'alias_of':None,
              'record_directory':f'subset/{cid}','record_file':f'E8__{gamma:g}__RANDOM.json'}
        current=[{'seed':seed,'acc':acc,'nmi':nmi,'inertia':float(seed+1)} for seed in range(50)]
        stats=summarize(current)
        row=distances({**base,**{k:v for k,v in stats.items() if k!='native_best'}},{'acc':50.,'nmi':50.})
        row.update(paper_acc=50.,paper_nmi=50.,paper_acc_sd=1.,paper_nmi_sd=2.)
        rows.append(row)
        for t in current:trials.append({**{k:base[k] for k in ['candidate_id','config_id','variant','gamma_nominal','initialization']},**t})
        m=output/'sample_manifests'/f'{cid}.json';m.parent.mkdir(exist_ok=True);m.write_text(json.dumps({'candidate_id':cid,'selected_indices':list(range(10))}))
        candidates.append({'candidate_id':cid,'benchmark':'ORL','pool':'specification_compatible','n':10,'manifest_path':str(m.relative_to(root)),'manifest_sha256':digest(m)})
        source=source_root/f'subset/{cid}/source.json';source.parent.mkdir(parents=True)
        source.write_text(json.dumps({'source_commit':'frozen-source','implementation_hash':'behavior-hash','cache_identity':'cache','environment':{'python':'test'}}))
    # B has the smaller joint discrepancy; ACC-only would choose A.
    native=[]
    for row in rows:
        native.append({**row,**summarize([{'seed':s,'acc':row['acc_mean']/100,'nmi':row['nmi_mean']/100,'inertia':float(s+1)} for s in range(50)])['native_best'],'endpoint':'native_best_of_50','n':1})
    closest=[rank(rows)[0],rank(native)[0]]
    write_csv(output/'joint_search_summary.csv',rows);write_csv(output/'closest_matches.csv',closest)
    buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=list(trials[0]));writer.writeheader();writer.writerows(trials)
    (output/'trials.csv.gz').write_bytes(gzip.compress(buffer.getvalue().encode(),mtime=0))
    (output/'candidate_catalogue.json').write_text(json.dumps({'candidates':candidates}))
    monkeypatch.setattr(release,'ROOT',root)
    manifest=configs/'release_manifest.json'
    release.freeze(output,manifest,source_root)
    return root,output,manifest


def test_current_release_fresh_copy_needs_no_data_artifacts_or_git(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture
    fresh=tmp_path/'fresh shallow checkout with spaces';shutil.copytree(root,fresh)
    rebuilt=tmp_path/'rebuilt current'
    result=release.rebuild(fresh/'configs/subset_search/release_manifest.json',rebuilt)
    assert result['ok'] and result['trials']==100
    assert not result['external_data_read'] and not result['external_artifact_read'] and not result['git_history_read']
    rows=list(csv.DictReader((rebuilt/'closest_matches.csv').open()))
    assert all(r['candidate_id']=='B' for r in rows)
    native=next(r for r in rows if r['endpoint']=='native_best_of_50')
    assert native['acc_sd']==native['nmi_sd']==native['delta_acc_sd_pp']==native['delta_nmi_sd_pp']==''
    assert int(native['n'])==1
    assert result['certified_search_availability_recomputed']
    assert (rebuilt/'certified_search_status.csv').read_bytes()==(output/'certified_search_status.csv').read_bytes()
    statuses=list(csv.DictReader((rebuilt/'certified_search_status.csv').open()))
    assert len(statuses)==2 and all(r['historical_complete_configurations']=='2' and not r['certified_closest_config_id'] for r in statuses)
    # A verified previous output can be replaced without leaving a stale backup.
    assert release.rebuild(fresh/'configs/subset_search/release_manifest.json',rebuilt)['ok']
    assert not rebuilt.with_name(rebuilt.name+'.previous').exists()


def test_gzip_joint_and_inventory_freeze_rebuild_without_external_access(scalar_fixture,tmp_path,monkeypatch):
    root,output,manifest=scalar_fixture
    original_joint=(output/'joint_search_summary.csv').read_bytes()
    original_selected=(output/'closest_matches.csv').read_bytes()
    pack_large_csvs(output,min_bytes=0,names=['joint_search_summary.csv','closest_matches.csv'])
    monkeypatch.setattr(release,'CSV_PACK_MIN_BYTES',0)
    frozen=release.freeze(output,manifest,tmp_path/'external scientific objects')
    inventory=frozen['inputs']['configuration_inventory']
    assert inventory['path'].endswith('configuration_inventory.csv.gz')
    actual=root/inventory['path']
    raw_inventory=gzip.decompress(actual.read_bytes())
    assert inventory['sha256']==digest(actual)
    assert inventory['uncompressed_sha256']==hashlib.sha256(raw_inventory).hexdigest()
    assert not (output/'configuration_inventory.csv').exists()
    assert gzip.decompress((output/'joint_search_summary.csv.gz').read_bytes())==original_joint
    assert gzip.decompress((output/'closest_matches.csv.gz').read_bytes())==original_selected
    # A later freeze may replace only its own already hash-locked gzip inventory.
    assert release.freeze(output,manifest,tmp_path/'external scientific objects')['expected_selections']==frozen['expected_selections']
    fresh=tmp_path/'fresh gzip checkout';shutil.copytree(root,fresh)
    shutil.rmtree(tmp_path/'external scientific objects')
    from experiments.submission_refresh.core import ArtifactStore
    import subprocess
    def denied(*args,**kwargs):raise AssertionError('no-data gzip replay must not access arrays, objects or Git')
    monkeypatch.setattr(ArtifactStore,'get',denied)
    monkeypatch.setattr(release.np,'load',denied)
    monkeypatch.setattr(subprocess,'run',denied)
    monkeypatch.setattr(subprocess,'check_output',denied)
    rebuilt=tmp_path/'plain rebuilt outputs'
    assert release.rebuild(fresh/'configs/subset_search/release_manifest.json',rebuilt)['ok']
    assert (rebuilt/'configuration_inventory.csv').read_bytes()==raw_inventory
    assert not list(rebuilt.glob('*.csv.gz'))
    assert {row['candidate_id'] for row in csv.DictReader((rebuilt/'closest_matches.csv').open())}=={'B'}


@pytest.mark.parametrize('change',['ambiguous','uncompressed_hash'])
def test_gzip_inventory_integrity_fails_before_output(scalar_fixture,tmp_path,monkeypatch,change):
    root,output,manifest=scalar_fixture
    monkeypatch.setattr(release,'CSV_PACK_MIN_BYTES',0)
    frozen=release.freeze(output,manifest,tmp_path/'external scientific objects')
    actual=root/frozen['inputs']['configuration_inventory']['path']
    raw=gzip.decompress(actual.read_bytes())
    if change=='ambiguous':
        actual.with_suffix('').write_bytes(raw)
        expected='ambiguous CSV transport'
    else:
        actual.write_bytes(gzip.compress(raw.replace(b'ITERATE_CONVERGED_UNCERTIFIED',b'CHANGED'),mtime=0))
        frozen['inputs']['configuration_inventory'].update(sha256=digest(actual),bytes=actual.stat().st_size)
        manifest.write_text(json.dumps(frozen))
        expected='uncompressed release input hash mismatch'
    destination=tmp_path/'rebuild must not exist'
    with pytest.raises(ValueError,match=expected):release.rebuild(manifest,destination)
    assert not destination.exists()


def public_archive_receipt(output,manifest,path):
    original=json.loads(manifest.read_text());source=output.parent.parent/original['inputs']['source_records']['path']
    value={'schema':'public-scientific-archive-receipt-v1','verified':True,'archive_id':'fixture-archive',
        'archive_sha256':'a'*64,'bytes':1000,'recovered_objects':3,'recovered_extra_files':4,'recovery_proof_sha256':'b'*64,
        'raw_release_inputs':{'source_records':{'sha256':digest(source),'uncompressed_sha256':hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest()},
            'current_release_manifest':{'sha256':digest(manifest)},'evidence_manifest':{'sha256':'c'*64},
            'artifact_manifests':{'refresh_sha256':'d'*64,'subset_sha256':'e'*64},
            'seed_inventory_proof':{'sha256':'f'*64},'original_namespace':{'sha256':'0'*64}}}
    path.write_text(json.dumps(value));return path


def test_public_current_projection_preserves_ids_measurements_and_failure_coverage(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture;objects=tmp_path/'external scientific objects'
    for source in objects.glob('subset/*/source.json'):
        raw=json.loads(source.read_text());raw.update(working_tree_dirty=True,hostname='private-host',
            thread_libraries=[{'version':'1','num_threads':1,'filepath':'/Users/private/library.dylib'}],
            command=['private-command'],source_files={'experiments/subset_search/runner.py':'a'*64})
        source.write_text(json.dumps(raw))
    write_csv(output/'execution_coverage.csv',[{'candidate_id':'A','variant':'E13','gamma_nominal':'1.0',
        'initialization':'RANDOM','status':'FAILED','original_candidate_status':'FAILED','failed_rounding_seed':'7',
        'source_queue':'private-queue','error':'CG residual 0.004 at /Users/private/workspace'}])
    (output/'resource_usage.json').write_text(json.dumps({'ledger':{'limit_seconds':129600,'max_workers':2,'active':{},
        'entries':[{'run_id':'private-task','phase':'baseline','charged_cpu_seconds':12.5,'status':'FAILED'}]}}))
    (output/'artifact_manifest.json').write_text(json.dumps({'store':'/Users/private/artifacts','records':[{'record':'subset/A/source.json'}]}))
    completion={'schema':'subset-completion-evidence-v1','records':{'subset/A':{
        'original_status':{'status':'FAILED','traceback':'/Users/private/trace','error':'CG residual 0.004'},
        'completion_failures':[{'sha256':'a'*64,'record':{'status':'TIMEOUT','source_error':.004,'objective':2.5,'traceback':'/Users/private/trace'}}],
        'completion_attempts':[]}}}
    (output/'completion_records.json.gz').write_bytes(gzip.compress(json.dumps(completion).encode(),mtime=0))
    raw_manifest=release.freeze(output,manifest,objects)
    raw_before=tmp_path/'raw rebuild';release.rebuild(manifest,raw_before)
    raw_source=output/'source_records.json.gz';raw_bytes=raw_source.read_bytes()
    raw_ids=set(json.loads(gzip.decompress(raw_bytes))['records'])
    proof=public_archive_receipt(output,manifest,tmp_path/'external archive receipt.json')
    projected=release.project_existing_release(output,manifest,archive_receipt=proof)
    assert projected['expected_selections']==raw_manifest['expected_selections']
    for role in ['trials','configuration_inventory','catalogue','protocol','selection','paper']:
        assert projected['inputs'][role]==raw_manifest['inputs'][role]
    registry_path=root/projected['inputs']['source_records']['path'];public=json.loads(gzip.decompress(registry_path.read_bytes()))
    assert set(public['records'])==raw_ids
    assert all(entry['original_record_sha256']==key for key,entry in public['records'].items())
    assert all(entry['public_record_sha256']!=key for key,entry in public['records'].items())
    assert b'/Users/' not in gzip.decompress(registry_path.read_bytes()) and raw_source.read_bytes()==raw_bytes
    assert release.project_existing_release(output,manifest,archive_receipt=proof)==projected
    # Remove original private envelopes: public replay must not dereference them.
    for role in ['source_records','coverage','resource_usage','artifact_manifest','completion_records']:
        (root/raw_manifest['inputs'][role]['path']).unlink()
    rebuilt=tmp_path/'public rebuild';release.rebuild(manifest,rebuilt)
    for name in ['joint_search_summary.csv','native_best_summary.csv','closest_matches.csv']:
        assert (rebuilt/name).read_bytes()==(raw_before/name).read_bytes()
    rows=list(csv.DictReader((rebuilt/'execution_coverage.csv').open()))
    assert len(rows)==1 and rows[0]['status']=='FAILED' and rows[0]['failed_rounding_seed']=='7'
    assert 'source_queue' not in rows[0] and '/Users/' not in (rebuilt/'execution_coverage.csv').read_text()
    cleaned=json.loads(gzip.decompress((rebuilt/'completion_records.json.gz').read_bytes()))
    failure=cleaned['records']['subset/A']['completion_failures'][0]
    assert failure['record']['status']=='TIMEOUT' and failure['record']['source_error']==.004 and failure['record']['objective']==2.5
    assert 'traceback' not in failure['record'] and failure['original_file_sha256']=='a'*64
    assert failure['original_record_sha256']!=failure['public_record_sha256']


def test_public_source_payload_hash_is_checked_even_if_transport_hash_is_updated(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture
    proof=public_archive_receipt(output,manifest,tmp_path/'archive receipt.json')
    projected=release.project_existing_release(output,manifest,archive_receipt=proof)
    path=root/projected['inputs']['source_records']['path'];registry=json.loads(gzip.decompress(path.read_bytes()))
    next(iter(registry['records'].values()))['record']['cache_identity']='different-actual-source'
    payload=(json.dumps(registry)+'\n').encode();path.write_bytes(gzip.compress(payload,mtime=0))
    projected['inputs']['source_records'].update(sha256=digest(path),bytes=path.stat().st_size,uncompressed_sha256=hashlib.sha256(payload).hexdigest())
    manifest.write_text(json.dumps(projected));target=tmp_path/'not authored'
    with pytest.raises(ValueError,match='public source registry payload hash mismatch'):release.rebuild(manifest,target)
    assert not target.exists()


def test_public_projection_requires_matching_verified_archive_before_writes(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture;before=manifest.read_bytes()
    proof=public_archive_receipt(output,manifest,tmp_path/'unverified receipt.json')
    value=json.loads(proof.read_text());value['verified']=False;proof.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='verified scientific archive'):release.project_existing_release(output,manifest,archive_receipt=proof)
    assert manifest.read_bytes()==before and not (output/'source_records.public.v1.json.gz').exists()


def test_public_current_release_replays_archived_namespace_after_raw_history_removal(scalar_fixture,tmp_path,monkeypatch):
    from experiments.subset_search import aggregate,confirmation_public
    from experiments.submission_refresh.core import atomic_json
    root,output,manifest=scalar_fixture;store=tmp_path/'external scientific objects'
    monkeypatch.setattr(aggregate,'ROOT',root);monkeypatch.setattr(confirmation_public,'ROOT',root)
    old=root/'results/historical/rounding.csv';write_csv(old,[{'seed':0,'acc':.5,'nmi':.6}])
    atomic_json(output/'winner_lock.json',{'winners':[{'config_id':'B|E8|1000.0|RANDOM'}]})
    ns=aggregate.confirmation_namespace(store,output,historical_paths=[old])
    confirmation_public.prepare_seed_inventory_proof(store,output)
    release.freeze(output,manifest,store)
    proof=public_archive_receipt(output,manifest,tmp_path/'archive receipt.json')
    value=json.loads(proof.read_text())
    value['raw_release_inputs']['original_namespace']['sha256']=digest(output/'confirmation_seed_namespace.json')
    value['raw_release_inputs']['seed_inventory_proof']['sha256']=digest(store/'confirmation'/confirmation_public.PREPARED)
    proof.write_text(json.dumps(value))
    confirmation_public.project_confirmation_namespace(store,output,archive_receipt=proof,root=root)
    projected=release.project_existing_release(output,manifest,archive_receipt=proof)
    assert {'confirmation_seed_proof','confirmation_namespace_projection','confirmation_winner_lock'}<=projected['inputs'].keys()
    old.unlink();shutil.rmtree(store)
    fresh=tmp_path/'public clone';shutil.copytree(root,fresh)
    rebuilt=tmp_path/'public namespace replay'
    assert release.rebuild(fresh/'configs/subset_search/release_manifest.json',rebuilt)['ok']
    public=json.loads((rebuilt/'confirmation_seed_namespace.json').read_text())
    assert public['version']==3 and public['first']==ns['first'] and public['winner_lock_sha256']==ns['winner_lock_sha256']


def test_hash_mismatch_fails_before_output_write(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture
    (output/'trials.csv.gz').write_bytes(b'not the frozen input')
    destination=tmp_path/'must remain absent'
    with pytest.raises(ValueError,match='hash mismatch'):
        release.rebuild(manifest,destination)
    assert not destination.exists()


def test_certified_search_status_cannot_gain_a_winner_even_with_updated_file_hash(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture
    path=output/'certified_search_status.csv';rows=list(csv.DictReader(path.open()))
    rows[0]['certified_closest_config_id']='a-different-certified-G'
    write_csv(path,rows)
    data=json.loads(manifest.read_text());data['inputs']['certified_search_status'].update(sha256=digest(path),bytes=path.stat().st_size)
    manifest.write_text(json.dumps(data));destination=tmp_path/'must not be authored'
    with pytest.raises(ValueError,match='certified-search availability scope/status mismatch'):
        release.rebuild(manifest,destination)
    assert not destination.exists()


@pytest.mark.parametrize('change',['missing','duplicate','empty'])
def test_invalid_raw_trial_set_fails_before_output_write(scalar_fixture,tmp_path,change):
    root,output,manifest=scalar_fixture
    p=output/'trials.csv.gz'
    with gzip.open(p,'rt',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    if change=='missing':rows=rows[:-1]
    elif change=='duplicate':rows.append(rows[0])
    else:rows=[]
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    raw=stream.getvalue().encode();p.write_bytes(gzip.compress(raw,mtime=0))
    data=json.loads(manifest.read_text());data['inputs']['trials'].update(sha256=digest(p),bytes=p.stat().st_size,uncompressed_sha256=hashlib.sha256(raw).hexdigest());manifest.write_text(json.dumps(data))
    destination=tmp_path/'must remain absent'
    with pytest.raises(ValueError,match='missing trials|duplicate trial|empty trial'):
        release.rebuild(manifest,destination)
    assert not destination.exists()
