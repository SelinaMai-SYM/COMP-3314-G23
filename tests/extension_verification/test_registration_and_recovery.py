"""Context changes invalidate caches; complete checkpoints survive interruption."""
import copy,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest,identity,ROOT
from experiments.extension_verification.inputs import source_files,runtime_environment,source_context,load_locked
from experiments.extension_verification.identity import fit_key
from experiments.extension_verification.worker import fit,recover_checkpoint


def test_environment_and_registration_namespace_are_not_reused(tmp_path):
    config=ROOT/'configs/extension_verification/protocol.yaml';store=ArtifactStore(tmp_path)
    from experiments.extension_verification.inputs import protocol
    _,sha=protocol(config);env=runtime_environment();files=source_files()
    lock={'source_files':files,'environment':env,'source_fingerprint':source_context(files,env),'protocol_sha256':sha,'datasets':{}}
    path=tmp_path/'registration/datasets.lock.json';atomic_json(path,lock);atomic_json(tmp_path/'freeze.json',{'datasets_lock_sha256':digest(path)})
    assert load_locked(config,tmp_path)[1]==lock
    changed=copy.deepcopy(env);changed['packages']['numpy']='different'
    with patch('experiments.extension_verification.inputs.runtime_environment',return_value=changed):
        with pytest.raises(ValueError,match='environment'):load_locked(config,tmp_path)
    base={key:'fixture' for key in ['benchmark','panel','kind','source_fingerprint','protocol_sha256','anchor_sha256','W0_sha256','input_registration_sha256','environment_fingerprint']};base.update(gamma=.5,parameters={})
    a=fit_key(base);base['environment_fingerprint']='new';assert fit_key(base)!=a
    a=fit_key(base);base['input_registration_sha256']='new';assert fit_key(base)!=a


def test_full_checkpoint_context_and_saved_steps_survive_interruption(tmp_path):
    store=ArtifactStore(tmp_path);H=np.array([[0.,0.],[4.,0.]]);entry={'objects':{'F0':store.put(H),'W0':store.put(sparse.csr_matrix([[0.,1.],[1.,0.]]))},'candidate_id':'synthetic','n':2,'K':2,'role':'synthetic','qualification':'synthetic'}
    lock={'datasets':{'synthetic':entry},'source_fingerprint':'fixture','protocol_sha256':'fixture','source_snapshot':store.put({}),'environment':{'synthetic':True}}
    path=tmp_path/'registration/datasets.lock.json';atomic_json(path,lock)
    task={'benchmark':'synthetic','panel':'original','kind':'relative','gamma':.8,'parameters':{'eta':.25},'source_fingerprint':'fixture','protocol_sha256':'fixture','anchor_sha256':entry['objects']['F0']['sha256'],'W0_sha256':entry['objects']['W0']['sha256'],'input_registration_sha256':digest(path),'environment_fingerprint':identity(lock['environment']),'attempt_id':'interrupted','iteration_ceiling':30000,'cpu_allowance':60}
    task['fit_id']=fit_key(task)
    from method_extension.extension_verification.convex import solve
    def interrupted(problem,**options):
        result=solve(problem,max_iter=100,cpu_limit=5);options['checkpoint_callback'](result);raise InterruptedError('synthetic interruption after a complete generation')
    with patch('experiments.extension_verification.worker.load_locked',return_value=({},lock,store)):
        with patch('experiments.extension_verification.worker.solve',side_effect=interrupted):
            with pytest.raises(InterruptedError):fit(task,'unused',tmp_path)
        ref=recover_checkpoint(tmp_path,task);state=store.get(ref)
        assert {'node_step','edge_step','hinge_step','source_context','G_best','q_best'}<=set(state)
        resumed={**task,'attempt_id':'resumed','checkpoint':ref};result=fit(resumed,'unused',tmp_path);assert result['solver']['certified']
        assert np.array_equal(store.get(result['objects']['G']),store.get(state['G_best']))
        wrong={**task,'environment_fingerprint':'wrong'}
        with pytest.raises(ValueError,match='identity'):recover_checkpoint(tmp_path,wrong)
        pointer=tmp_path/'fits'/task['fit_id']/'attempts/interrupted/latest/CURRENT.json';generation=pointer.parent/json.loads(pointer.read_text())['directory'];arrays=generation/'arrays.npz';arrays.write_bytes(arrays.read_bytes()+b'corrupt')
        with pytest.raises(ValueError,match='array hash'):recover_checkpoint(tmp_path,task)
