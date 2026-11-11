"""Fit one immutable convex problem without reading evaluation labels."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import numpy as np
from experiments.submission_refresh.core import atomic_json,digest,identity,ROOT
from method_extension.extension_verification.convex import Problem,Hinges,solve,rowunit
from .inputs import load_locked,datasets_lock_path
from .identity import fit_key

ARRAY_KEYS=['G_last','G_bar','average','q_last','p_last','G_best','q_best','p_best','node_step','edge_step']


def _pack_checkpoint(store,state):
    return {key:store.put(value) if key in ARRAY_KEYS else value for key,value in state.items()}


def _unpack_checkpoint(store,state):
    return {key:store.get(value) if key in ARRAY_KEYS else value for key,value in state.items()}


def recover_checkpoint(artifact_root,task):
    """Verify and import the latest complete generation; never use partial files."""
    from experiments.submission_refresh.core import ArtifactStore
    store=ArtifactStore(artifact_root);current=store.root/'fits'/task['fit_id']/'attempts'/task['attempt_id']/'latest'
    pointer=json.loads((current/'CURRENT.json').read_text());generation=(current/pointer['directory']).resolve()
    if current.resolve() not in generation.parents:raise ValueError('unsafe checkpoint generation')
    metadata=generation/'state.json'
    if digest(metadata)!=pointer['state_sha256']:raise ValueError('checkpoint metadata hash mismatch')
    state=json.loads(metadata.read_text());archive=generation/'arrays.npz'
    if digest(archive)!=state.pop('arrays_sha256'):raise ValueError('checkpoint array hash mismatch')
    expected={key:task[key] for key in ['fit_id','source_fingerprint','protocol_sha256','input_registration_sha256','environment_fingerprint']}
    if state.get('source_context')!=expected:raise ValueError('checkpoint identity differs from continuation task')
    with np.load(archive,allow_pickle=False) as arrays:
        if set(arrays.files)!=set(ARRAY_KEYS):raise ValueError('checkpoint array state incomplete')
        state.update({key:arrays[key].copy() for key in ARRAY_KEYS})
    return store.put(_pack_checkpoint(store,state))


def fit(task,config,artifact_root):
    specification,lock,store=load_locked(config,artifact_root);entry=lock['datasets'][task['benchmark']]
    if task['source_fingerprint']!=lock['source_fingerprint'] or task['protocol_sha256']!=lock['protocol_sha256']:raise ValueError('fit task identity differs from freeze')
    if task['input_registration_sha256']!=digest(datasets_lock_path(store.root)) or task['environment_fingerprint']!=identity(lock['environment']):raise ValueError('fit registration/environment namespace differs')
    if task['fit_id']!=fit_key(task) or task['anchor_sha256']!=entry['objects']['F0' if task['panel']=='original' else 'U']['sha256'] or task['W0_sha256']!=entry['objects']['W0']['sha256']:raise ValueError('fit objective/input identity mismatch')
    context={key:task[key] for key in ['fit_id','source_fingerprint','protocol_sha256','input_registration_sha256','environment_fingerprint']}
    H=store.get(entry['objects']['F0' if task['panel']=='original' else 'U']);W=store.get(entry['objects']['W0']);parameters=task['parameters'];kind=task['kind'];hinges=None
    if kind=='relative_neighbor':
        system=entry['random_hinges'][str(parameters['random_seed'])] if parameters.get('random_seed') is not None else {name:entry['objects']['hinge_'+name] for name in ['anchors','normals','beta']}
        hinges=Hinges(store.get(system['anchors']),store.get(system['normals']),store.get(system['beta']))
    angle=parameters.get('angle_degrees',15.)
    radius=np.tan(np.deg2rad(angle)) if kind=='tangent' else np.sin(np.deg2rad(angle)) if kind=='ball' else None
    problem=Problem(H,W,task['gamma'],kind=kind,eta=parameters.get('eta',.25),radius=radius,hinges=hinges,mu=parameters.get('mu',2.))
    folder=store.root/'fits'/task['fit_id'];attempt=folder/'attempts'/task['attempt_id'];attempt.mkdir(parents=True,exist_ok=False)
    previous=None
    if task.get('checkpoint'):
        previous=_unpack_checkpoint(store,store.get(task['checkpoint']))
        if previous.get('source_context')!=context or not np.array_equal(previous['node_step'],problem.tau) or not np.array_equal(previous['edge_step'],problem.q_step) or previous['hinge_step']!=problem.p_step:raise ValueError('checkpoint source, environment, objective or steps differ')
    current=attempt/'latest';current.mkdir();generation=None
    def checkpoint(result):
        nonlocal generation
        state=dict(result['checkpoint']);state.update(source_context=context,node_step=problem.tau,edge_step=problem.q_step,hinge_step=problem.p_step,prior_charged_CPU_seconds=task.get('prior_charged_CPU_seconds',0.),worker_CPU_seconds=time.process_time());new=Path(tempfile.mkdtemp(prefix='state-',dir=current));arrays={k:state[k] for k in ARRAY_KEYS};np.savez_compressed(new/'arrays.npz',**arrays)
        meta={k:v for k,v in state.items() if k not in ARRAY_KEYS};meta.update(arrays_sha256=digest(new/'arrays.npz'),source_fingerprint=lock['source_fingerprint']);atomic_json(new/'state.json',meta)
        atomic_json(current/'CURRENT.json',{'directory':new.name,'state_sha256':digest(new/'state.json')})
        if generation is not None:shutil.rmtree(generation)
        generation=new
    result=solve(problem,max_iter=task['iteration_ceiling'],cpu_limit=max(1.,task['cpu_allowance']-20-time.process_time()),checkpoint=previous,checkpoint_callback=checkpoint)
    G=result['G'];Q=G.copy() if task['panel']=='original' else rowunit(G)
    objects={name:store.put(value) for name,value in [('G',G),('Q',Q),('q',result['q']),('p',result['p'])]}
    savedG=store.get(objects['G']);savedq=store.get(objects['q']);savedp=store.get(objects['p']);independent=problem.dual(savedq,savedp,repair=False);primal=problem.primal(savedG);absolute=primal-independent['dual'];relative=absolute/max(1.,abs(primal),abs(independent['dual']));feasibility=problem.feasibility(savedG);dual_feasibility={k:v for k,v in independent.items() if k.endswith('violation')}
    certified=bool(np.isfinite(primal+independent['dual']) and absolute>=0 and relative<=1e-5 and max([*feasibility.values(),*dual_feasibility.values()],default=0)<=1e-8)
    solver={key:value for key,value in result.items() if key not in ['G','q','p','checkpoint','history']};solver.update(primal=primal,dual=independent['dual'],absolute_gap=absolute,relative_gap=relative,certified=certified,feasibility=feasibility,dual_feasibility=dual_feasibility)
    final_state=dict(result['checkpoint']);final_state.update(source_context=context,node_step=problem.tau,edge_step=problem.q_step,hinge_step=problem.p_step,prior_charged_CPU_seconds=task.get('prior_charged_CPU_seconds',0.),worker_CPU_seconds=time.process_time())
    checkpoint_ref=store.put(_pack_checkpoint(store,final_state));history_ref=store.put(result['history'])
    record={**task,'schema':'ssc-refinement-fit-v1','candidate_id':entry['candidate_id'],'n':entry['n'],'K':entry['K'],'role':entry['role'],'qualification':entry['qualification'],'historical_identity':'UNVERIFIED','anchor_object':entry['objects']['F0' if task['panel']=='original' else 'U'],'graph_object':entry['objects']['W0'],'objects':objects,'solver':solver,'checkpoint':checkpoint_ref,'history':history_ref,'source_snapshot':lock['source_snapshot'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'labels_loaded_for_fitting':False,'output_normalization':'none' if task['panel']=='original' else 'rowunit','independent_saved_array_certificate':True,'worker_CPU_seconds':time.process_time()}
    atomic_json(attempt/'result.json',record);atomic_json(folder/'result.json',record)
    shutil.rmtree(current)
    return record


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--config',required=True);p.add_argument('--artifact-root',required=True);args=p.parse_args();task=json.loads(Path(args.task).read_text());result=fit(task,args.config,args.artifact_root);print(json.dumps({'fit_id':result['fit_id'],'benchmark':result['benchmark'],'kind':result['kind'],'certified':result['solver']['certified'],'gap':result['solver']['relative_gap'],'iterations':result['solver']['iterations_total']}),flush=True)

if __name__=='__main__':main()
