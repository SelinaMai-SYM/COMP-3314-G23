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
from .inputs import load_locked

ARRAY_KEYS=['G_last','G_bar','average','q_last','p_last','G_best','q_best','p_best']


def _pack_checkpoint(store,state):
    return {key:store.put(value) if key in ARRAY_KEYS else value for key,value in state.items()}


def _unpack_checkpoint(store,state):
    return {key:store.get(value) if key in ARRAY_KEYS else value for key,value in state.items()}


def fit(task,config,artifact_root):
    specification,lock,store=load_locked(config,artifact_root);entry=lock['datasets'][task['benchmark']]
    if task['source_fingerprint']!=lock['source_fingerprint'] or task['protocol_sha256']!=lock['protocol_sha256']:raise ValueError('fit task identity differs from freeze')
    H=store.get(entry['objects']['F0' if task['panel']=='original' else 'U']);W=store.get(entry['objects']['W0']);parameters=task['parameters'];kind=task['kind'];hinges=None
    if kind=='relative_neighbor':
        system=entry['random_hinges'][str(parameters['random_seed'])] if parameters.get('random_seed') is not None else {name:entry['objects']['hinge_'+name] for name in ['anchors','normals','beta']}
        hinges=Hinges(store.get(system['anchors']),store.get(system['normals']),store.get(system['beta']))
    angle=parameters.get('angle_degrees',15.)
    radius=np.tan(np.deg2rad(angle)) if kind=='tangent' else np.sin(np.deg2rad(angle)) if kind=='ball' else None
    problem=Problem(H,W,task['gamma'],kind=kind,eta=parameters.get('eta',.25),radius=radius,hinges=hinges,mu=parameters.get('mu',2.))
    folder=store.root/'fits'/task['fit_id'];attempt=folder/'attempts'/task['attempt_id'];attempt.mkdir(parents=True,exist_ok=False)
    previous=None
    if task.get('checkpoint'):previous=_unpack_checkpoint(store,store.get(task['checkpoint']))
    current=attempt/'latest';current.mkdir();generation=None
    def checkpoint(result):
        nonlocal generation
        state=result['checkpoint'];new=Path(tempfile.mkdtemp(prefix='state-',dir=current));arrays={k:state[k] for k in ARRAY_KEYS};np.savez_compressed(new/'arrays.npz',**arrays)
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
    checkpoint_ref=store.put(_pack_checkpoint(store,result['checkpoint']));history_ref=store.put(result['history'])
    record={**task,'schema':'ssc-refinement-fit-v1','candidate_id':entry['candidate_id'],'n':entry['n'],'K':entry['K'],'role':entry['role'],'qualification':entry['qualification'],'historical_identity':'UNVERIFIED','anchor_object':entry['objects']['F0' if task['panel']=='original' else 'U'],'graph_object':entry['objects']['W0'],'objects':objects,'solver':solver,'checkpoint':checkpoint_ref,'history':history_ref,'source_snapshot':lock['source_snapshot'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'labels_loaded_for_fitting':False,'output_normalization':'none' if task['panel']=='original' else 'rowunit','independent_saved_array_certificate':True,'worker_CPU_seconds':time.process_time()}
    atomic_json(attempt/'result.json',record);atomic_json(folder/'result.json',record)
    shutil.rmtree(current)
    return record


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--config',required=True);p.add_argument('--artifact-root',required=True);args=p.parse_args();task=json.loads(Path(args.task).read_text());result=fit(task,args.config,args.artifact_root);print(json.dumps({'fit_id':result['fit_id'],'benchmark':result['benchmark'],'kind':result['kind'],'certified':result['solver']['certified'],'gap':result['solver']['relative_gap'],'iterations':result['solver']['iterations_total']}),flush=True)

if __name__=='__main__':main()
