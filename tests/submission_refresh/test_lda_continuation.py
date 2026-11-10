"""Whole-fit checkpoint adoption verifies identity before any new seed is copied."""
import base64
import copy
import hashlib
import json
import numpy as np
import pytest
import experiments.submission_refresh.lda_continuation as continuation
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest


def fixture(tmp_path,monkeypatch,block='lda_reference'):
    root=tmp_path/'checkout';fit=root/'baselines/lda_kmeans/fit.py';fit.parent.mkdir(parents=True)
    fit.write_text('# fixed externally seeded LDA fit\n');(root/'baselines/common.py').write_text('# checked input defaults\n')
    monkeypatch.setattr(continuation,'ROOT',root)
    hashes={str(path.relative_to(root)):digest(path) for path in [fit,root/'baselines/common.py']}
    source={'implementation_hash':'original-full-map','source_files':hashes,'environment':{'python':'3.13.3','packages':{'numpy':'2.4.2','scipy':'1.17.1','scikit-learn':'1.8.0'}}}
    current={**source,'implementation_hash':'new-orchestration-map'}
    store=ArtifactStore(tmp_path/'objects outside checkout');old=store.root/'baseline/old';old.mkdir(parents=True)
    X=np.arange(12.).reshape(4,3);y=np.array([0,0,1,1]);objects={'X':store.put(X),'y':store.put(y)}
    task={'run_id':'old','dataset':'unit','block':block,'limits':[30,100,300]}
    atomic_json(old/'input.json',{'dataset':'unit','objects':objects,'source':source})
    atomic_json(old/'status.json',{'task':task,'status':'TIMEOUT','source':source})
    for seed,status in [(0,'COMPLETED'),(1,'FAILED_LDA_UPDATE'),(2,'TIMEOUT'),(3,'FAILED')]:
        row={'seed':seed,'status':status,'implementation_hash':source['implementation_hash']}
        if status in ['COMPLETED','FAILED_LDA_UPDATE']:
            row.update(diagnostics={'seed':seed,'parameters':{'max_iter':300},'inertia':999999.-seed},objects={'labels':store.put(y)})
        elif status=='TIMEOUT':row['error']="TimeoutError('process CPU allocation exhausted')"
        else:row['error']='genuine numerical failure'
        atomic_json(old/f'state__300__{seed}.json',row)
    new={**task,'run_id':'new','continue_from':'old'};folder=store.root/'baseline/new'
    return root,store,old,folder,X,y,current,new


def test_all_completed_and_genuine_failed_states_keep_original_identity(tmp_path,monkeypatch):
    root,store,old,folder,X,y,current,task=fixture(tmp_path,monkeypatch)
    original=(old/'state__300__0.json').read_bytes()
    ref=continuation.adopt_fit_checkpoints(task,X,y,2,store,folder,current);proof=store.get(ref)
    assert {entry['seed'] for entry in proof['adopted']}=={0,1,3}
    assert [entry['seed'] for entry in proof['retry_timeouts']]==[2]
    assert len(proof['missing_fixed_seeds'])==46
    copied=json.loads((folder/'state__300__0.json').read_text())
    assert copied['implementation_hash']=='original-full-map'
    assert copied['adoption']['accepted_current_implementation_hash']=='new-orchestration-map'
    assert copied['adoption']['prior_checkpoint_sha256']==hashlib.sha256(original).hexdigest()
    assert json.loads((folder/'state__300__1.json').read_text())['status']=='FAILED_LDA_UPDATE'
    assert json.loads((folder/'state__300__3.json').read_text())['status']=='FAILED'
    assert not (folder/'state__300__2.json').exists()
    assert (old/'state__300__0.json').read_bytes()==original
    for item in proof['fit_library_files']:
        body=base64.b64decode(store.get(item['object'])['bytes_base64'])
        assert hashlib.sha256(body).hexdigest()==item['sha256']
    assert proof['no_within_fit_trajectory_prefix_reuse']


@pytest.mark.parametrize('mismatch',['data','environment','fit_code'])
def test_mismatch_fails_before_checkpoint_adoption(tmp_path,monkeypatch,mismatch):
    root,store,old,folder,X,y,current,task=fixture(tmp_path,monkeypatch)
    if mismatch=='data':X=X+1
    elif mismatch=='environment':
        current=copy.deepcopy(current);current['environment']['packages']['numpy']='different'
    else:(root/'baselines/common.py').write_text('# different fitting helper\n')
    with pytest.raises(ValueError,match='mismatch'):continuation.adopt_fit_checkpoints(task,X,y,2,store,folder,current)
    assert not list(folder.glob('state__*.json'))


def test_no_adoption_across_iteration_caps(tmp_path,monkeypatch):
    root,store,old,folder,X,y,current,task=fixture(tmp_path,monkeypatch,block='lda_existing')
    task['limits']=[100]
    # Even a complete lower-cap trajectory is not an external fit at cap100.
    old_row=json.loads((old/'state__300__0.json').read_text());old_row['diagnostics']['parameters']['max_iter']=30
    atomic_json(old/'state__30__0.json',old_row)
    ref=continuation.adopt_fit_checkpoints(task,X,y,2,store,folder,current)
    assert not list(folder.glob('state__*.json'))
    assert len(store.get(ref)['missing_fixed_seeds'])==50


def test_unexplained_timeout_does_not_get_retried_or_partially_adopted(tmp_path,monkeypatch):
    root,store,old,folder,X,y,current,task=fixture(tmp_path,monkeypatch)
    path=old/'state__300__2.json';row=json.loads(path.read_text());row['error']='unknown wall-time interruption';atomic_json(path,row)
    with pytest.raises(ValueError,match='allocation failure'):continuation.adopt_fit_checkpoints(task,X,y,2,store,folder,current)
    assert not list(folder.glob('state__*.json'))
