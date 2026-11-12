"""Interrupted outputs must preserve the saved best pair, not an extrapolate."""
import numpy as np
import pytest
from scipy import sparse
from method_extension.extension_round2.models import QuadraticProblem
from experiments.extension_round2.common import ArtifactStore,atomic_json,digest,environment,identity,load_record,source_files,save_continuation,get_arrays
from experiments.extension_round2.recovery import _recover_finite


def test_interrupted_best_state_and_unreached_targets(tmp_path):
    store=ArtifactStore(tmp_path/'artifacts');H=np.array([[-1.],[1.]]);W=sparse.csr_matrix([[0.,1.],[1.,0.]])
    config=tmp_path/'protocol.yaml';config.write_text('{}\n');files=source_files();env=environment();fingerprint=identity({'files':files,'environment':env})
    href=store.put(H);wref=store.put(W);context={'benchmark':'toy','method':'QSSC','variant':'default','parameters':{},'source_fingerprint':fingerprint,'protocol_sha256':digest(config),'H_sha256':href['sha256'],'W_sha256':wref['sha256']}
    lock={'source_files':files,'environment':env,'source_fingerprint':fingerprint,'protocol_sha256':digest(config),'cohorts':{'toy':{'n':2,'K':1,'objects':{'H':href,'W0':wref}}}}
    atomic_json(store.root/'cohort_lock.json',lock);lam=.05;definition={**context,'lambda':lam,'attempt':1};fit_id=identity(definition);folder=store.root/'fits'/fit_id
    atomic_json(folder/'definition.json',definition)
    best=QuadraticProblem(H,W,lam).certificate(.95*H,np.array([[-lam]]));raw=H+10
    state={'Z':raw,'bar':raw+1,'q':best['q'],'p':best['p'],'S':None,'best':best,'iteration':1000,'CPU_seconds':.25}
    save_continuation(folder/'continuation',{'state':state,'context':context,'lambda':lam,'parameters':{}})
    atomic_json(store.root/'paths/toy--QSSC--default.json',{'distinct':[lam.hex()],'attempts':{lam.hex():1},'fits':{},'targets':{}})
    atomic_json(store.root/'tasks/toy.json',{'kind':'path','benchmark':'toy','method':'QSSC','targets':[.05,.1,.2]})
    assert len(_recover_finite(store.root,config))==3
    points={p['rho']:p for file in (store.root/'endpoints').glob('*.json') if (p:=load_record(file))}
    recovered=get_arrays(store,store.get(points[.05]['result']))
    assert np.array_equal(recovered['G'],best['G']) and not np.array_equal(recovered['G'],raw)
    assert np.array_equal(recovered['checkpoint']['Z'],raw)
    assert points[.05]['outcome']['status']=='TIMEOUT_RECOVERED_LAST_FINITE' and not points[.05]['outcome']['matched']
    for target in [.1,.2]:
        assert points[target]['outcome']['status']=='UNRUN_PATH_BUDGET' and points[target]['result'] is None
        assert points[target]['outcome']['last_finite_fit']==points[.05]['result']
    assert len(list((store.root/'fits').glob('*/definition.json')))==1
    assert load_record(store.root/'paths/toy--QSSC--default.json')['fits']=={}
    before={p.name:digest(p) for p in (store.root/'endpoints').glob('*.json')}
    assert _recover_finite(store.root,config)==[]
    assert before=={p.name:digest(p) for p in (store.root/'endpoints').glob('*.json')}
    atomic_json(folder/'definition.json',{**definition,'W_sha256':'0'*64})
    with pytest.raises(ValueError,match='shrinkage graph identity'):_recover_finite(store.root,config)
    atomic_json(folder/'definition.json',definition)
    pointer=folder/'continuation/CURRENT.json';value=load_record(pointer);value['state_sha256']='0'*64;atomic_json(pointer,value)
    with pytest.raises(ValueError,match='continuation metadata identity'):_recover_finite(store.root,config)
    assert before=={p.name:digest(p) for p in (store.root/'endpoints').glob('*.json')}
