"""Top-level resume skips retain source, authorization, data and cap guards."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh import scheduler,scheduler_resume,graph_repair,baselines
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest


@pytest.fixture
def fixed_resume(tmp_path,monkeypatch):
    root=tmp_path/'external artifacts';store=ArtifactStore(root)
    monkeypatch.setenv('COMP3314_ARTIFACT_ROOT',str(root))
    X=np.arange(80.,dtype=float).reshape(40,2);y=np.arange(40);F=np.eye(40);W=sparse.eye(40,format='csr')
    shared={'implementation_hash':'current-graph-source','environment':{'python':'fixture'}}
    source_calls=[];data_calls=[]
    def graph_source(*args,**kwargs):source_calls.append(True);return copy.deepcopy(shared)
    def load(*args):data_calls.append(args);return X.copy(),y.copy(),{}
    monkeypatch.setattr(graph_repair,'scientific_source_record',graph_source)
    monkeypatch.setattr(baselines,'load',load)
    def never(*args,**kwargs):raise AssertionError('resume must not invoke a scientific builder or fit')
    for module,names in [(graph_repair,['spectral_embedding','knn_affinity','solve'])]:
        for name in names:monkeypatch.setattr(module,name,never)
    arrays={'X':X,'y':y,'F0':F,'U':F,'A':W,'W0':W,'Wa_raw':W}
    path=root/'graph_inputs/ORL_att92/frozen/representation.json'
    atomic_json(path,{'dataset':'ORL_att92','K':40,'input_preparation':'Y0','source':shared,
        'objects':{name:store.put(value) for name,value in arrays.items()}})
    task={'run_id':'graph-fixture','kind':'graph','phase':'G2','dataset':'ORL_att92','anchor':'F0','graph':'W0','gamma':1.,'cpu_limit':100,'fit_cpu_limit':50}
    result={'task':copy.deepcopy(task),'status':'COMPLETED','source':copy.deepcopy(shared),'input_record':str(path)}
    result['scheduler_resume_identity']=scheduler_resume.capture_execution(task,result,root)
    return {'root':root,'store':store,'X':X,'y':y,'path':path,'task':task,'result':result,
        'shared':shared,'source_calls':source_calls,'data_calls':data_calls}




def test_unchanged_graph_skip_checks_data_once_per_controller_and_never_fits(fixed_resume):
    f=fixed_resume;validator=scheduler_resume.ResumeValidator('unused',f['root']);before=f['path'].read_bytes()
    assert validator.validate(f['task'],f['result'])['validated'] is True
    second=copy.deepcopy(f['task']);second['run_id']='graph-second';second['gamma']=10.
    saved=copy.deepcopy(f['result']);saved['task']=second
    saved['scheduler_resume_identity']=scheduler_resume.capture_execution(second,saved,f['root'])
    validator.validate(second,saved)
    assert len(f['source_calls'])==len(f['data_calls'])==1 and validator.validated==2
    assert validator.cpu_seconds>=0 and f['path'].read_bytes()==before


@pytest.mark.parametrize('change',['source','environment','data','metadata','caps','legacy'])
def test_resume_rejects_changed_scientific_identity_before_skip(fixed_resume,monkeypatch,change):
    f=fixed_resume;task=copy.deepcopy(f['task']);saved=copy.deepcopy(f['result'])
    if change=='source':f['shared']['implementation_hash']='changed-graph-helper'
    elif change=='environment':f['shared']['environment']={'python':'changed'}
    elif change=='data':monkeypatch.setattr(baselines,'load',lambda *args:(f['X']+1,f['y'],{}))
    elif change=='metadata':f['path'].write_text(f['path'].read_text()+'\n')
    elif change=='caps':task['cpu_limit']+=1
    elif change=='legacy':saved.pop('scheduler_resume_identity')
    before=f['path'].read_bytes()
    with pytest.raises(ValueError,match='use a new run ID'):
        scheduler_resume.ResumeValidator('unused',f['root']).validate(task,saved)
    assert f['path'].read_bytes()==before






def test_scheduler_unchanged_skip_invokes_guard_without_launching_a_worker(fixed_resume,monkeypatch):
    f=fixed_resume;atomic_json(f['root']/'task_status/graph-fixture.json',f['result'])
    monkeypatch.setattr(scheduler.mp,'get_context',lambda *args:object())
    result=scheduler.run([f['task']],'unused',f['root'])
    assert result['not_launched']==[] and result['resume_metadata_validation']['tasks']==1
    assert len(f['data_calls'])==1 and not result['ledger']['entries']


def test_scheduler_callback_records_exact_profile_and_formal_input_identities(fixed_resume,monkeypatch):
    f=fixed_resume
    def profile(task,*args):
        return {**f['result'],'task':task,'status':'PROFILE_ONLY_INELIGIBLE'}
    monkeypatch.setattr(graph_repair,'run_graph',profile)
    task={**f['task'],'profile':True,'profile_rows':3}
    scheduler._execute(task,'unused',f['root'])
    saved=json.loads((f['root']/'task_status/graph-fixture.json').read_text())
    assert saved['scheduler_resume_identity']['available'] is True
    assert saved['scheduler_resume_identity']['profile'] is True
    assert saved['scheduler_resume_identity']['input_record_sha256']==digest(f['path'])
    assert saved['task']==task and saved['status']=='PROFILE_ONLY_INELIGIBLE'


def test_failure_before_inputs_has_no_usable_resume_identity(fixed_resume,monkeypatch):
    f=fixed_resume
    def forbidden(*args):raise ValueError('input metadata is unavailable')
    monkeypatch.setattr(scheduler_resume,'_input_path',forbidden)
    result=scheduler_resume.capture_execution(f['task'],{'status':'FAILED'},f['root'])
    assert result['available'] is False and 'input metadata' in result['unavailable_reason']
