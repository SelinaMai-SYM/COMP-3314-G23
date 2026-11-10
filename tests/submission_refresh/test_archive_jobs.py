"""Final archive controllers preserve dependencies, outputs and CPU evidence."""
import json
from pathlib import Path
import subprocess
import pytest
from experiments.submission_refresh import archive_jobs,export_artifacts
from experiments.submission_refresh.core import ArtifactStore,ResourceLedger,atomic_json,digest


@pytest.fixture
def small_archive(tmp_path,monkeypatch):
    root=tmp_path/'checkout with spaces';root.mkdir()
    subprocess.run(['git','init','-q',str(root)],check=True)
    store=ArtifactStore(tmp_path/'external scientific artifacts')
    # Small JSON objects suffice to exercise nested CAS/logical recovery; no
    # data loader, numerical fit, or scientific worker is invoked by the tests.
    nested=store.put({'values':[1,2,3]});record=store.put({'objects':{'small':nested},'status':'FIXTURE'})
    atomic_json(root/archive_jobs.MANIFESTS[0],{'records':[{'record':'fixture/result.json','object':record}]})
    atomic_json(root/archive_jobs.MANIFESTS[1],{'records':[]})
    subprocess.run(['git','add','results'],cwd=root,check=True)
    subprocess.run(['git','-c','user.name=Archive Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Freeze fixture manifests'],cwd=root,check=True)
    monkeypatch.setattr(archive_jobs,'ROOT',root);monkeypatch.setattr(export_artifacts,'ROOT',root)
    guards=[];monkeypatch.setattr(archive_jobs,'install_cpu_limit',guards.append)
    return root,store,guards


def task(operation='export',run_id=None):
    return {'run_id':run_id or 'fixture-'+operation,'kind':'archive','phase':'aggregation','operation':operation,
        'cpu_limit':3600 if operation=='export' else 1800,'archive_name':'fixture-science.tar.gz',
        **({'recovery_name':'fixture-recovered','depends_on':'fixture-export'} if operation=='recover' else {})}


def execute(store,definition):
    ledger=ResourceLedger(store.root)
    assert ledger.reserve(definition['run_id'],definition['cpu_limit'],'aggregation')
    result=archive_jobs.run_archive(definition,'unused-data-root',store.root)
    ledger.finish(definition['run_id'],result['process_cpu_seconds'],result['status'])
    return result


def test_shared_export_then_recovery_uses_verified_dependency_and_original_objects(small_archive):
    root,store,guards=small_archive
    exported=execute(store,task());recovered=execute(store,task('recover'))
    assert exported['status']==recovered['status']=='COMPLETED'
    assert exported['archive']['verified'] is True
    assert recovered['export_dependency']['record_sha256']==digest(store.root/'archive_jobs/fixture-export.json')
    restored=store.root.parent/'fixture-recovered'
    logical=json.loads((restored/'fixture/result.json').read_text())
    assert ArtifactStore(restored).get(logical['objects']['small'])=={'values':[1,2,3]}
    assert recovered['recovery']['summary']['archive_sha256']==exported['archive']['sha256']
    assert guards and all(0<value<3600-archive_jobs.CLEANUP_MARGIN for value in guards)
    assert exported['guarded_remaining_cpu_seconds']<3600-archive_jobs.CLEANUP_MARGIN
    assert recovered['guarded_remaining_cpu_seconds']<1800-archive_jobs.CLEANUP_MARGIN
    for record in [exported,recovered]:
        assert record['cpu_seconds']>=0 and record['process_cpu_seconds']>=record['cpu_seconds']
        assert record['wall_seconds']>=0 and record['peak_rss_bytes']>0
        assert record['source']['files'] and record['tested_commit']
        assert [row['path'] for row in record['input_manifests']]==list(archive_jobs.MANIFESTS)
    assert len(ResourceLedger(store.root).state()['entries'])==2


@pytest.mark.parametrize('target',['archive','sidecar'])
def test_recovery_requires_completed_export_and_rejects_changed_archive(small_archive,target):
    _,store,_=small_archive
    first=execute(store,task('recover','missing-export'))
    assert first['status']=='FAILED' and 'dependency is unavailable' in first['error']
    assert not (store.root.parent/'fixture-recovered').exists()
    exported=execute(store,task());archive=store.root.parent/exported['archive_name']
    changed_path=archive if target=='archive' else archive.with_suffix(archive.suffix+'.json')
    changed_path.write_bytes(changed_path.read_bytes()+b'changed')
    changed=execute(store,task('recover','changed-archive'))
    assert changed['status']=='FAILED'
    assert ('hash or size' if target=='archive' else 'sidecar differs') in changed['error']
    assert not (store.root.parent/'fixture-recovered').exists()


def test_existing_archive_sidecar_and_recovery_outputs_are_preserved(small_archive):
    _,store,_=small_archive
    exported=execute(store,task());archive=store.root.parent/exported['archive_name'];before=archive.read_bytes()
    duplicate=execute(store,task(run_id='duplicate-export'))
    assert duplicate['status']=='FAILED' and archive.read_bytes()==before
    recovered=store.root.parent/'fixture-recovered';recovered.mkdir();marker=recovered/'original.txt';marker.write_text('retain original')
    blocked=execute(store,task('recover'))
    assert blocked['status']=='FAILED' and marker.read_text()=='retain original'
    original_record=(store.root/'archive_jobs/fixture-export.json').read_bytes()
    with pytest.raises(ValueError,match='new run ID'):archive_jobs.run_archive(task(),'unused',store.root)
    assert (store.root/'archive_jobs/fixture-export.json').read_bytes()==original_record


def test_uncommitted_manifest_fails_before_export(small_archive):
    root,store,_=small_archive;path=root/archive_jobs.MANIFESTS[0]
    path.write_text(path.read_text()+'\n')
    result=execute(store,task())
    assert result['status']=='FAILED' and 'committed bytes' in result['error']
    assert not (store.root.parent/'fixture-science.tar.gz').exists()


def test_export_timeout_records_actual_cpu_and_leaves_existing_store_untouched(small_archive,monkeypatch):
    _,store,_=small_archive;before=sorted(str(p.relative_to(store.root)) for p in (store.root/'objects').rglob('*') if p.is_file())
    def fail(root,path):
        # Simulate interruption between the atomic archive publication and
        # sidecar publication. This attempt owns these previously absent paths.
        path.write_bytes(b'fixture interrupted publication')
        raise TimeoutError('fixture CPU allocation exhausted')
    monkeypatch.setattr(export_artifacts,'export',fail)
    result=execute(store,task())
    assert result['status']=='TIMEOUT' and result['source']['implementation_hash']
    assert result['cpu_seconds']>=0 and result['process_cpu_seconds']>=result['cpu_seconds']
    assert sorted(str(p.relative_to(store.root)) for p in (store.root/'objects').rglob('*') if p.is_file())==before
    assert not (store.root.parent/'fixture-science.tar.gz').exists()
    assert json.loads((store.root/'archive_jobs/fixture-export.json').read_text())['status']=='TIMEOUT'


def test_existing_sidecar_alone_is_preserved(small_archive):
    _,store,_=small_archive;sidecar=store.root.parent/'fixture-science.tar.gz.json'
    sidecar.write_bytes(b'previous sidecar')
    result=execute(store,task())
    assert result['status']=='FAILED' and sidecar.read_bytes()==b'previous sidecar'
    assert not (store.root.parent/'fixture-science.tar.gz').exists()


def test_failed_export_record_cannot_authorize_recovery(small_archive):
    _,store,_=small_archive;exported=execute(store,task())
    record_path=store.root/'archive_jobs/fixture-export.json'
    exported['status']='TIMEOUT';atomic_json(record_path,exported)
    result=execute(store,task('recover'))
    assert result['status']=='FAILED' and 'not a completed verified export' in result['error']
    assert not (store.root.parent/'fixture-recovered').exists()


def test_git_preflight_timeout_is_bounded_and_preserves_failure_accounting(small_archive,monkeypatch):
    _,store,guards=small_archive;calls=[]
    def timeout(command,**kwargs):
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(command,kwargs['timeout'])
    monkeypatch.setattr(archive_jobs.subprocess,'run',timeout)
    result=execute(store,task())
    assert result['status']=='TIMEOUT' and result['source']['files']
    assert guards and calls and 0<calls[0]['timeout']<7215
    assert callable(calls[0]['preexec_fn'])
    assert result['process_cpu_seconds']>=result['cpu_seconds']>=0
    assert json.loads((store.root/'archive_jobs/fixture-export.json').read_text())['status']=='TIMEOUT'
    assert not (store.root.parent/'fixture-science.tar.gz').exists()


@pytest.mark.parametrize('name',['/tmp/escape.tar.gz','../escape.tar.gz','sub/escape.tar.gz','bad\\escape.tar.gz'])
def test_archive_names_cannot_escape_the_artifact_sibling_directory(small_archive,name):
    _,store,_=small_archive;definition=task();definition['archive_name']=name
    result=execute(store,definition)
    assert result['status']=='FAILED' and 'safe relative filename' in result['error']


def test_finalization_refuses_another_active_shared_job(small_archive):
    _,store,_=small_archive;ledger=ResourceLedger(store.root)
    assert ledger.reserve('other-scientific-job',1,'experiment')
    result=execute(store,task())
    assert result['status']=='FAILED' and 'all other shared jobs' in result['error']
    assert not (store.root.parent/'fixture-science.tar.gz').exists()
    ledger.finish('other-scientific-job',0,'FIXTURE')


def test_scheduler_routes_archive_without_a_second_worker_pool(small_archive,monkeypatch):
    from experiments.submission_refresh.scheduler import _execute
    _,store,_=small_archive
    monkeypatch.setattr(archive_jobs,'run_archive',lambda task,data,root:{'task':task,'status':'FIXTURE_ONLY','cpu_seconds':.01})
    definition=task();_execute(definition,'unused',store.root)
    saved=json.loads((store.root/'task_status/fixture-export.json').read_text())
    assert saved['status']=='FIXTURE_ONLY' and saved['task']==definition


def test_archive_specs_are_separate_bounded_and_use_one_shared_reserve(small_archive):
    _,store,_=small_archive
    export=[task('export')]
    recover=[task('recover')]
    assert len(export)==len(recover)==1
    assert export[0]['cpu_limit']==3600 and recover[0]['cpu_limit']==1800
    assert recover[0]['depends_on']==export[0]['run_id']
    assert recover[0]['archive_name']==export[0]['archive_name']
    assert all(row['phase']=='aggregation' and row['kind']=='archive' for row in export+recover)
    ledger=ResourceLedger(store.root)
    for definition in export+recover:
        assert ledger.reserve(definition['run_id'],definition['cpu_limit'],definition['phase'])
    state=ledger.state()
    assert state['max_workers']==2 and sum(item['seconds'] for item in state['active'].values())==5400
    assert not ledger.reserve('third-fixture-task',1,'aggregation')
    for definition in export+recover:ledger.finish(definition['run_id'],0,'FIXTURE_NOT_EXECUTED')
    assert not ledger.state()['active']
