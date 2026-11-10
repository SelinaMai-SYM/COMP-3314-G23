"""Locked confirmations enforce their allocation and preserve failed attempts."""
from contextlib import nullcontext
import copy
import hashlib
import json
from types import SimpleNamespace
import pytest
from experiments.subset_search import aggregate
from experiments.submission_refresh import core


@pytest.fixture
def locked_confirmation(tmp_path,monkeypatch):
    out=tmp_path/'published';out.mkdir();root=tmp_path/'external artifacts';folder=root/'subset/fixed';folder.mkdir(parents=True)
    references={name:{'fixture_key':name,'sha256':name*64} for name in ['F','G','y']}
    core.atomic_json(folder/'record.json',{'objects':{'G':references['G']}})
    core.atomic_json(folder/'representation.json',{'objects':{'F':references['F'],'y':references['y']}})
    winner={'config_id':'fixed|E8|1|RANDOM','candidate_id':'fixed','benchmark':'ORL','pool':'specification_compatible',
        'endpoint':'mean_sample_sd_50','record_directory':'subset/fixed','record_file':'record.json',
        'initialization':'RANDOM','G_sha256':references['G']['sha256'],'F_sha256':references['F']['sha256'],
        'acc_mean':50.,'nmi_mean':60.,'paper_acc':50.,'paper_nmi':60.}
    core.atomic_json(out/'winner_lock.json',{'version':1,'winners':[winner]})
    namespace={'version':2,'first':1000000,'count':50,'seeds':list(range(1000000,1000050)),
        'winner_lock_sha256':core.digest(out/'winner_lock.json'),'historical_inventory':{'sources':[]},
        'overlap':False,'no_reselection':True}
    core.atomic_json(root/'confirmation/seed_namespace.json',namespace)
    core.atomic_json(out/'confirmation_seed_namespace.json',namespace)
    events=[];objects={};entries=[];active={}
    def put(value):
        sha=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest();objects[sha]=copy.deepcopy(value)
        return {'sha256':sha,'path':'fixture/'+sha+'.json','kind':'json'}
    store=SimpleNamespace(root=root,get=lambda ref:{'F':'saved-F','G':'saved-G','y':[0,1]}[ref['fixture_key']],put=put)
    class Ledger:
        def __init__(self,*args):pass
        def reserve(self,rid,seconds,phase):
            assert rid not in active;active[rid]=(seconds,phase);events.append(('reserve',seconds));return True
        def finish(self,rid,cpu,status):
            seconds,phase=active.pop(rid);entries.append({'run_id':rid,'cpu_seconds':cpu,'status':status,'reservation':seconds})
    monkeypatch.setattr(aggregate,'ArtifactStore',lambda *args:store)
    monkeypatch.setattr(aggregate,'ResourceLedger',Ledger)
    monkeypatch.setattr(core,'install_cpu_limit',lambda value:events.append(('install',value)))
    import signal,threadpoolctl
    monkeypatch.setattr(signal,'setitimer',lambda which,value:events.append(('clear',which,value)))
    monkeypatch.setattr(threadpoolctl,'threadpool_limits',lambda **kwargs:nullcontext())
    return SimpleNamespace(out=out,root=root,winner=winner,namespace=namespace,objects=objects,entries=entries,events=events,active=active)


def complete_rounding(seeds):
    return ([{'seed':seed,'acc':.75,'nmi':.85,'inertia':float(index+1)} for index,seed in enumerate(seeds)],
        [[0,1] for _ in seeds],[])


@pytest.mark.parametrize('failed_stage',['locked_candidate_rounding','matched_sc_rounding'])
def test_confirmation_timeout_enforces_cap_clears_timer_and_preserves_partial_attempt(locked_confirmation,monkeypatch,failed_stage):
    f=locked_confirmation;calls=[];lock_bytes=(f.out/'winner_lock.json').read_bytes();namespace_bytes=(f.root/'confirmation/seed_namespace.json').read_bytes()
    partial=[{'seed':1000000,'acc':.5,'nmi':.6,'inertia':1.}];partial_predictions=[[0,1]]
    def timeout(embedding,y,K,initialization,seeds):
        calls.append((embedding,initialization,list(seeds)))
        assert ('install',120) in f.events
        if failed_stage=='matched_sc_rounding' and len(calls)==1:return complete_rounding(list(seeds))
        error=TimeoutError('fixed confirmation CPU allocation exhausted')
        error.partial_trials=partial;error.partial_predictions=partial_predictions;error.failed_rounding_seed=1000001
        raise error
    monkeypatch.setattr(aggregate,'round_embedding',timeout)
    with pytest.raises(TimeoutError,match='CPU allocation'):aggregate.confirm(f.root,f.out)
    failures=list((f.root/'confirmation/failures').rglob('attempt-*.json'));assert len(failures)==1
    saved=json.loads(failures[0].read_text())
    assert saved['status']=='TIMEOUT' and saved['stage']==failed_stage and saved['cpu_limit']==120
    assert saved['config_id']==f.winner['config_id'] and saved['endpoint']==f.winner['endpoint']
    assert saved['first_seed']==1000000 and saved['seeds']==f.namespace['seeds']
    assert saved['failed_rounding_seed']==1000001 and saved['partial_trials']==partial
    assert f.objects[saved['objects']['partial_predictions']['sha256']]==partial_predictions
    if failed_stage=='matched_sc_rounding':
        assert len(saved['completed_candidate_trials'])==50
        assert len(f.objects[saved['objects']['completed_candidate_predictions']['sha256']])==50
    assert not list((f.root/'confirmation').glob('confirm-*.json'))
    assert not (f.out/'rounding_confirmation.csv').exists()
    assert (f.out/'winner_lock.json').read_bytes()==lock_bytes
    assert (f.root/'confirmation/seed_namespace.json').read_bytes()==namespace_bytes
    assert all(call[1:] == ('RANDOM',f.namespace['seeds']) for call in calls)
    assert [event for event in f.events if event[0]=='install']==[('install',120),('install',120)]
    assert f.events[-1][0]=='clear' and f.events[-1][-1]==0
    assert f.entries[-1]['status']=='TIMEOUT' and f.entries[-1]['reservation']==120 and not f.active


def test_successful_confirmation_uses_same_lock_and_clears_its_winner_timer(locked_confirmation,monkeypatch):
    f=locked_confirmation;calls=[];before=(f.out/'winner_lock.json').read_bytes()
    def rounded(embedding,y,K,initialization,seeds):
        calls.append((embedding,initialization,list(seeds)));return complete_rounding(list(seeds))
    monkeypatch.setattr(aggregate,'round_embedding',rounded)
    aggregate.confirm(f.root,f.out)
    completed=list((f.root/'confirmation').glob('confirm-*.json'));assert len(completed)==1
    saved=json.loads(completed[0].read_text())
    assert saved['status']=='COMPLETED' and saved['first_seed']==f.namespace['first']
    assert saved['selection_acc']==f.winner['acc_mean'] and saved['confirmation_all50']['acc_mean']==75.
    assert (f.out/'winner_lock.json').read_bytes()==before
    assert [call[0] for call in calls]==['saved-G','saved-F']
    assert all(call[1:] == ('RANDOM',f.namespace['seeds']) for call in calls)
    assert [event for event in f.events if event[0]=='install']==[('install',120),('install',120)]
    assert f.events[-1][0]=='clear' and f.entries[-1]['status']=='COMPLETED' and not f.active


def test_timeout_after_publication_cannot_leave_a_false_completed_confirmation(locked_confirmation,monkeypatch):
    f=locked_confirmation;original=aggregate.atomic_json
    monkeypatch.setattr(aggregate,'round_embedding',lambda embedding,y,K,initialization,seeds:complete_rounding(list(seeds)))
    def interrupted_publication(path,value):
        original(path,value)
        if path.parent==f.root/'confirmation' and path.name.startswith('confirm-'):
            raise TimeoutError('CPU limit just after confirmation publication')
    monkeypatch.setattr(aggregate,'atomic_json',interrupted_publication)
    with pytest.raises(TimeoutError,match='publication'):aggregate.confirm(f.root,f.out)
    assert not list((f.root/'confirmation').glob('confirm-*.json'))
    failures=list((f.root/'confirmation/failures').rglob('attempt-*.json'));assert len(failures)==1
    failure=json.loads(failures[0].read_text())
    assert failure['status']=='TIMEOUT' and failure['stage']=='summary_and_publication'
    assert len(failure['completed_candidate_trials'])==len(failure['completed_matched_sc_trials'])==50
    assert f.entries[-1]['status']=='TIMEOUT' and not f.active
