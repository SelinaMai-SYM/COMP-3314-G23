"""Adopt whole external LDA fits under byte-verified compatibility conditions.

This helper does not inspect ACC/NMI, choose favorable seeds, reuse within-fit
trajectory prefixes, or change an LDA fitting function. Timed-out fits restart
from their declared external seed and the same iteration cap.
"""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import re
from experiments.v3_reproduction.provenance import fingerprint_matrix
from .core import ROOT,atomic_json,digest

SEEDS=tuple(range(50))


def _limits(task):
    return tuple(map(int,task.get('limits',[30,100,300]))) if task['block']=='lda_existing' else (300,)


def _fit_files(block):
    files=[p for p in (ROOT/'baselines/lda_kmeans').rglob('*.py') if not p.name.startswith('test') and '__pycache__' not in p.parts]
    if not files:raise ValueError('LDA fit-library source inventory is incomplete')
    files.append(ROOT/'baselines/common.py')
    if block=='lda_adapted':
        files += list((ROOT/'SSC_method').glob('*.py'))
        files += [ROOT/'experiments/v2_kmeans_protocol'/name for name in ['kmeans_trials.py','vanilla_kmeanspp.py']]
    if not files or any(not p.is_file() for p in files):raise ValueError('LDA fit-library source inventory is incomplete')
    return sorted(set(files))


def _verify_objects(value,store,verified):
    if isinstance(value,dict):
        if {'sha256','path','kind'}<=set(value):
            key=(value['sha256'],value['path'])
            if key in verified:return
            item=store.get(value);verified.add(key)
            if isinstance(item,(dict,list)): _verify_objects(item,store,verified)
        else:
            for child in value.values():_verify_objects(child,store,verified)
    elif isinstance(value,list):
        for child in value:_verify_objects(child,store,verified)


def adopt_fit_checkpoints(task,X,y,K,store,folder,source):
    """Validate every proposed adoption before publishing any new checkpoint."""
    if not task.get('continue_from'):return None
    if task.get('profile'):raise ValueError('profiling runs cannot adopt reportable LDA fits')
    folder=Path(folder).resolve();base=(store.root/'baseline').resolve();prior=Path(task['continue_from'])
    if not prior.is_absolute():prior=store.root/prior if prior.parts and prior.parts[0]=='baseline' else base/prior
    prior=prior.resolve()
    if base not in prior.parents or prior==folder:raise ValueError('continuation source must be a distinct baseline folder in the same artifact store')
    old_status_path=prior/'status.json';old_input_path=prior/'input.json'
    if not old_status_path.is_file() or not old_input_path.is_file():raise ValueError('continuation task/input provenance unavailable')
    old_status=json.loads(old_status_path.read_text());old_input=json.loads(old_input_path.read_text());old_task=old_status.get('task',{})
    if old_status.get('status') in ['RUNNING','STARTED']:raise ValueError('prior LDA block is still active')
    if any(old_task.get(key)!=task.get(key) for key in ['dataset','block']):raise ValueError('continuation dataset/block mismatch')
    if old_input.get('dataset')!=task['dataset']:raise ValueError('continuation input dataset mismatch')
    if old_task.get('profile'):raise ValueError('profile checkpoints are ineligible for adoption')
    for item in [old_task,task]:
        declared=item.get('seeds',item.get('seed_list',SEEDS))
        if not isinstance(declared,(list,tuple)) or tuple(map(int,declared))!=SEEDS:raise ValueError('continuation requires the full fixed external seeds0..49')
    limits=_limits(task)
    if not set(limits)<=set(_limits(old_task)):raise ValueError('continuation iteration-cap mismatch')
    for key in ['parameters','lda_params','initialization','n_init','n_components','permutation_invariant_stop']:
        if old_task.get(key)!=task.get(key):raise ValueError('continuation fitting parameter mismatch: '+key)
    old_source=old_input.get('source',old_status.get('source'))
    if not isinstance(old_source,dict) or not old_source.get('environment') or old_source['environment']!=source.get('environment'):
        raise ValueError('continuation environment mismatch or unavailable environment record')
    fit_files=_fit_files(task['block']);file_hashes={};verified_bodies={}
    for path in fit_files:
        relative=str(path.relative_to(ROOT));body=path.read_bytes();sha=hashlib.sha256(body).hexdigest()
        if old_source.get('source_files',{}).get(relative)!=sha or source.get('source_files',{}).get(relative)!=sha:
            raise ValueError('continuation fit-library source mismatch: '+relative)
        file_hashes[relative]=sha;verified_bodies[relative]=body
    objects=old_input.get('objects',{})
    if not {'X','y'}<=objects.keys():raise ValueError('continuation exact input objects unavailable')
    old_X=store.get(objects['X']);old_y=store.get(objects['y'])
    if fingerprint_matrix(old_X,old_y)!=fingerprint_matrix(X,y):raise ValueError('continuation input fingerprint mismatch')
    if len(set(map(int,old_y)))!=int(K):raise ValueError('continuation class-count mismatch')
    for path in prior.glob('state__*__*.json'):
        match=re.fullmatch(r'state__(\d+)__(\d+)\.json',path.name)
        if match and (int(match[1]) not in _limits(old_task) or int(match[2]) not in SEEDS):raise ValueError('prior checkpoint outside declared cap/seed namespace')
    planned=[];retry=[];missing=[];verified=set()
    for limit in limits:
        for seed in SEEDS:
            path=prior/f'state__{limit}__{seed}.json'
            if not path.is_file():missing.append({'limit':limit,'seed':seed});continue
            saved=json.loads(path.read_text())
            if saved.get('seed')!=seed:raise ValueError('continuation checkpoint seed identity mismatch')
            original=saved.get('implementation_hash');previous_adoption=saved.get('adoption',{})
            if original!=old_source.get('implementation_hash') and previous_adoption.get('accepted_current_implementation_hash')!=old_source.get('implementation_hash'):
                raise ValueError('continuation checkpoint/source identity mismatch')
            status=saved.get('status');diagnostics=saved.get('diagnostics',{})
            if status in ['COMPLETED','FAILED_LDA_UPDATE']:
                if diagnostics.get('seed')!=seed:raise ValueError('completed fit RNG seed is not recorded consistently')
                if 'parameters'in diagnostics and diagnostics['parameters'].get('max_iter')!=limit:
                    raise ValueError('continuation checkpoint actual iteration-cap mismatch')
                if not saved.get('objects',{}).get('labels'):raise ValueError('completed fit labels object unavailable')
            elif status=='TIMEOUT':
                error=str(saved.get('error','')).lower()
                if not any(phrase in error for phrase in ['cpu allocation','cpu limit','cpu budget','cpu deadline','timer allocation']):
                    raise ValueError('timeout does not explicitly establish an allocation failure')
                retry.append({'limit':limit,'seed':seed,'path':path,'saved':saved,
                    'reason':'Explicit prior CPU-allocation timeout; restart this fixed external seed at the identical cap, without within-fit prefix reuse.'})
                continue
            elif status!='FAILED':raise ValueError('unknown prior checkpoint status: '+str(status))
            _verify_objects(saved.get('objects',{}),store,verified);_verify_objects(diagnostics,store,verified)
            target=folder/path.name
            if target.exists():
                current=json.loads(target.read_text())
                adoption=current.get('adoption',{})
                if adoption.get('prior_checkpoint_sha256')!=digest(path) or adoption.get('accepted_current_implementation_hash')!=source['implementation_hash']:
                    raise ValueError('new checkpoint already exists with incompatible adoption provenance')
                continue
            planned.append({'path':path,'target':target,'saved':saved,'limit':limit,'seed':seed})
    # No score fields, fit calls, or output checkpoint writes occurred above.
    bodies=[]
    for path in fit_files:
        relative=str(path.relative_to(ROOT));bodies.append({'path':relative,'sha256':file_hashes[relative],
            'object':store.put({'encoding':'base64','bytes_base64':base64.b64encode(verified_bodies[relative]).decode('ascii')})})
    proof={'schema':'whole-lda-fit-adoption-v1','prior_run_id':old_task['run_id'],'new_run_id':task['run_id'],
        'prior_input_record_sha256':digest(old_input_path),'prior_status_record_sha256':digest(old_status_path),
        'prior_input_record_object':store.put(old_input),'prior_status_record_object':store.put(old_status),
        'original_source_record_object':store.put(old_source),'current_source_record_object':store.put(source),
        'fit_library_files':bodies,'environment':source['environment'],'input_fingerprint':fingerprint_matrix(X,y),
        'limits':list(limits),'expected_external_seeds':list(SEEDS),
        'RNG_verification':'Each adopted checkpoint is one complete externally seeded fit; checkpoint and diagnostic seed IDs agree and all fit-library bytes/defaults match.',
        'no_within_fit_trajectory_prefix_reuse':True,'no_ACC_NMI_inspected_for_adoption':True,
        'all_completed_and_genuine_failed_states_retained':True,'verified_scientific_objects':len(verified),
        'retry_timeouts':[{'limit':item['limit'],'seed':item['seed'],'reason':item['reason'],'original_checkpoint_sha256':digest(item['path']),'original_checkpoint_object':store.put(item['saved'])} for item in retry],
        'missing_fixed_seeds':missing,
        'adopted':[{'limit':item['limit'],'seed':item['seed'],'status':item['saved']['status'],'prior_checkpoint_sha256':digest(item['path'])} for item in planned]}
    proof_ref=store.put(proof);folder.mkdir(parents=True,exist_ok=True)
    for item in planned:
        saved=dict(item['saved']);saved['adoption']={'prior_record_path':str(item['path'].relative_to(store.root)),
            'prior_checkpoint_sha256':digest(item['path']),'prior_checkpoint_object':store.put(item['saved']),
            'original_implementation_hash':item['saved']['implementation_hash'],
            'accepted_current_implementation_hash':source['implementation_hash'],'compatibility_proof':proof_ref,
            'same_iteration_cap':item['limit'],'same_external_seed':item['seed']}
        atomic_json(item['target'],saved)
    atomic_json(folder/'continuation_adoption.json',{'proof':proof_ref,'adopted_records':len(planned),
        'retry_timeout_records':len(retry),'missing_fixed_seed_records':len(missing),
        'prior_run_id':old_task['run_id'],'no_successful_seed_filtering':True})
    return proof_ref
