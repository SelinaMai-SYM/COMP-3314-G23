"""Bounded, same-F/W USPS solver audit; fitting never receives true labels.

The caller owns the shared resource ledger and must reserve this block before
calling it. This module enforces an additional local six-core-hour ceiling.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import argparse
import hashlib
import json
import signal
import resource
import subprocess
import time
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from method_extension.next_round.certified_solver import solve,graph_arrays,objective,component_dual_flow
from experiments.v3_reproduction.provenance import json_ready,environment_record,source_fingerprint


def _array_hash(array):
    a=np.ascontiguousarray(array)
    return hashlib.sha256(str(a.dtype).encode()+repr(a.shape).encode()+a.tobytes()).hexdigest()


def pair_identity(F,W):
    W=sparse.csr_matrix(W);W.sort_indices()
    return {'F':_array_hash(F),'W_data':_array_hash(W.data),'W_indices':_array_hash(W.indices),'W_indptr':_array_hash(W.indptr),'shape':list(W.shape)}


@contextmanager
def _cpu_guard(seconds):
    """ITIMER_PROF counts user and system CPU; it is separate from wall time."""
    previous=signal.getsignal(signal.SIGPROF);timer=signal.getitimer(signal.ITIMER_PROF)
    def timeout(_signum,_frame):raise TimeoutError('solver audit CPU allocation')
    signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,max(.001,seconds))
    try:yield
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,previous)
        if timer[0]>0:signal.setitimer(signal.ITIMER_PROF,*timer)


def historical_irls_audit(F,W,gamma,*,cpu_limit=1800.,max_iter=300):
    """Observe the existing IRLS/CG code without changing its accepted steps."""
    import SSC_method.optimizer as optimizer
    started=time.perf_counter();cpu=time.process_time();cg_records=[];linear_steps=[];last={}
    B,_,_,w=graph_arrays(W)
    original_solve=optimizer.solve_spd_system;original_cg=optimizer.cg
    def observe_cg(A,b,**kwargs):
        count=[0];callback=kwargs.pop('callback',None)
        def observer(x):
            count[0]+=1
            if callback is not None:callback(x)
        x,info=original_cg(A,b,callback=observer,**kwargs)
        cg_records.append({'info':int(info),'iterations':count[0],
            'relative_residual':float(np.linalg.norm(A@x-b)/max(np.linalg.norm(b),np.finfo(float).tiny)),
            'rtol':kwargs.get('rtol'),'maxiter':kwargs.get('maxiter')})
        return x,info
    def observe_solve(A,rhs):
        x=original_solve(A,rhs)
        last.update(coefficient=sparse.csr_matrix(A),rhs=np.asarray(rhs).copy(),G=np.asarray(x).copy())
        linear_steps.append({'linear_step':len(linear_steps)+1,'primal':objective(x,F,B,2*gamma*w),'relative_linear_residual':float(np.linalg.norm(A@x-rhs)/max(np.linalg.norm(rhs),np.finfo(float).tiny)),'cpu_seconds':time.process_time()-cpu})
        return x
    optimizer.cg=observe_cg;optimizer.solve_spd_system=observe_solve
    try:
        with _cpu_guard(min(1800.,cpu_limit)):
            fitted=optimizer.shrink_embedding(F,W,gamma,eps=1e-8,tol=1e-6,max_iter=max_iter,variant='E8')
        record={'status':'ITERATE_CONVERGED' if fitted.converged else 'MAX_ITER_REACHED',
            'iterations':fitted.n_iterations,'history':fitted.history,
            'fixed_point_residual':fitted.fixed_point_residual,
            'initial_zero_residual_floor':fitted.initial_zero_residual_floor,
            'G':fitted.patterns,'complete_historical_execution':True}
    except Exception as exc:
        record={'status':'CPU_LIMIT' if isinstance(exc,TimeoutError) else 'FAILED',
            'error':repr(exc),'complete_historical_execution':False,
            'G':last.get('G',F.copy()),'history':linear_steps,'iterations_completed_linear_steps':len(linear_steps)}
    finally:
        optimizer.cg=original_cg;optimizer.solve_spd_system=original_solve
    checks={'linear_steps':linear_steps,'cg_records':cg_records,'cg_calls':len(cg_records),
        'cg_failures':sum(r['info']!=0 for r in cg_records),
        'cg_max_relative_residual':max((r['relative_residual'] for r in cg_records),default=None)}
    if 'coefficient' in last:
        A=last['coefficient'];rhs=last['rhs'];G=last['G']
        diagonal=A.diagonal();offsum=np.asarray(np.abs(A).sum(axis=1)).ravel()-np.abs(diagonal)
        checks.update(symmetry_relative=float(sparse.linalg.norm(A-A.T)/max(1.,sparse.linalg.norm(A))),
            diagonal_min=float(diagonal.min()),diagonal_max=float(diagonal.max()),
            gershgorin_lower=float(np.min(diagonal-offsum)),
            gershgorin_upper=float(np.max(diagonal+offsum)),
            relative_linear_residual=float(np.linalg.norm(A@G-rhs)/max(np.linalg.norm(rhs),np.finfo(float).tiny)),
            positive_definiteness_argument='Positive diagonal S plus 2*gamma times a nonnegative-weight graph Laplacian is SPD; a negative rounded Gershgorin bound alone is not an SPD failure.')
    B,_,_,w=graph_arrays(W)
    record.update(primal=objective(record['G'],F,B,2*gamma*w),linear_checks=checks,
        gamma=float(gamma),gamma_effective=float(gamma),variant='E8',certified=False,
        cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started,
        protocol={'eps':1e-8,'tol':1e-6,'max_iter':max_iter,'zero_residual_floor':'median_pairwise','observation_only_instrumentation':True})
    return record,last


def _save_result(output,name,record,extra=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    arrays={};metadata={}
    for key,value in record.items():
        if isinstance(value,np.ndarray):arrays[key]=value
        elif key=='checkpoint':
            metadata[key]={}
            for k,v in value.items():
                if isinstance(v,np.ndarray):arrays['checkpoint_'+k]=v
                else:metadata[key][k]=v
        else:metadata[key]=value
    if extra:
        for key,value in extra.items():
            if sparse.issparse(value):
                value=sparse.csr_matrix(value)
                for part in ['data','indices','indptr']:arrays[key+'_'+part]=getattr(value,part)
                arrays[key+'_shape']=np.array(value.shape)
            else:arrays[key]=value
    np.savez_compressed(output/(name+'.npz'),**arrays)
    metadata['arrays_file']=name+'.npz'
    metadata['arrays_sha256']=hashlib.file_digest(open(output/(name+'.npz'),'rb'),'sha256').hexdigest()
    (output/(name+'.json')).write_text(json.dumps(json_ready(metadata),indent=2)+'\n')
    return metadata


@threadpool_limits.wrap(limits=1)
def audit_pair(F,W,*,output_dir,gammas=(1.,1000.),attempt_cpu_limit=1800.,flow_cpu_limit=300.,block_cpu_limit=21600.,pdhg_max_iter=30000):
    """Run the locked audit sequence on exactly one frozen current F/W pair.

    CPU limits may be reduced before evaluation by the orchestrator. Reduced
    runs retain their limits and cannot be described as exhaustive attempts.
    Per gamma: IRLS300, uniform PDHG, diagonal PDHG, componentwise flow, then
    a diagonal same-objective restart from the best label-free primal/dual.
    The restart is not claimed to reproduce an uninterrupted trajectory.
    """
    if not 0<attempt_cpu_limit<=1800:raise ValueError('full-attempt CPU limit must be in (0,1800]')
    if not 0<flow_cpu_limit<=300:raise ValueError('flow CPU limit must be in (0,300]')
    if not 0<block_cpu_limit<=21600:raise ValueError('USPS block CPU limit must be in (0,21600]')
    started=time.perf_counter();cpu=time.process_time();output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    F=np.asarray(F,dtype=float);W=sparse.csr_matrix(W,dtype=float);B,i,j,w=graph_arrays(W)
    identity=pair_identity(F,W)
    frozen={'F':F,'W_data':W.data,'W_indices':W.indices,'W_indptr':W.indptr,'W_shape':np.array(W.shape)}
    np.savez_compressed(output/'frozen_pair.npz',**frozen)
    def remaining():return max(0.,block_cpu_limit-(time.process_time()-cpu))
    manifest={'schema':1,'same_frozen_pair':identity,'records':[],
        'source_fingerprint':source_fingerprint(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=Path(__file__).resolve().parents[2]).strip(),
        'environment':environment_record(),
        'limits':{'attempt_cpu_seconds':attempt_cpu_limit,'flow_cpu_seconds':flow_cpu_limit,'block_cpu_seconds':block_cpu_limit},
        'graph':{'nodes':len(F),'undirected_edges':len(w),'undirected_mass':float(w.sum()),
            'components':int(sparse.csgraph.connected_components(W,directed=False,return_labels=False)),
            'weights_min':float(w.min()) if len(w) else None,'weights_max':float(w.max()) if len(w) else None,
            'finite':bool(np.isfinite(F).all() and np.isfinite(w).all()),'E8_capacities':'2*gamma*w','E13_mapping':'effective gamma = nominal gamma/2'},
        'historical_identity':'Current regenerated arrays; not identified with unavailable historical F/W artifacts.'}
    for gamma in gammas:
        prefix='gamma_'+format(gamma,'.8g');results=[]
        stages=['IRLS300','uniform_PDHG','diagonal_PDHG','component_dual_flow','diagonal_warm_restart']
        for stage in stages:
            name=prefix+'_'+stage
            if remaining()<.05:
                manifest['records'].append({'name':name,'status':'NOT_RUN_BLOCK_CPU_LIMIT'});continue
            limit=min(flow_cpu_limit if stage=='component_dual_flow' else attempt_cpu_limit,remaining())
            extra=None
            try:
                if stage=='IRLS300':
                    record,extra=historical_irls_audit(F,W,gamma,cpu_limit=limit)
                elif stage=='component_dual_flow':record=component_dual_flow(F,W,gamma,cpu_time_limit=limit)
                else:
                    kwargs={}
                    if stage=='diagonal_warm_restart':
                        eligible=[r for r in results if np.isfinite(r.get('primal',np.inf)) and 'G' in r]
                        best=min(eligible,key=lambda r:r['primal']) if eligible else {'G':F}
                        duals=[r for r in results if 'q' in r and np.isfinite(r.get('dual',-np.inf))]
                        best_dual=max(duals,key=lambda r:r['dual']) if duals else None
                        kwargs={'G_init':best['G'],'q_init':None if best_dual is None else best_dual['q']}
                    with _cpu_guard(limit):
                        record=solve(F,W,gamma,max_iter=pdhg_max_iter,time_limit=max(60.,limit*4),cpu_time_limit=max(.001,limit-.05),
                            preconditioned=stage!='uniform_PDHG',return_checkpoint=True,**kwargs)
                record['stage']=stage;record['same_frozen_pair']=identity
            except Exception as exc:
                record={'stage':stage,'status':'CPU_LIMIT' if isinstance(exc,TimeoutError) else 'FAILED','error':repr(exc),'same_frozen_pair':identity}
            results.append(record)
            metadata=_save_result(output,name,record,extra=extra)
            manifest['records'].append({'name':name,**metadata})
            manifest.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started,peak_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            (output/'audit_manifest.json').write_text(json.dumps(json_ready(manifest),indent=2)+'\n')
    manifest.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started,peak_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (output/'audit_manifest.json').write_text(json.dumps(json_ready(manifest),indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,help='NPZ containing F and W_data/W_indices/W_indptr/W_shape')
    parser.add_argument('--output',required=True)
    parser.add_argument('--attempt-cpu-limit',type=float,default=1800.)
    parser.add_argument('--flow-cpu-limit',type=float,default=300.)
    parser.add_argument('--block-cpu-limit',type=float,default=21600.)
    args=parser.parse_args();data=np.load(args.input)
    W=sparse.csr_matrix((data['W_data'],data['W_indices'],data['W_indptr']),shape=tuple(data['W_shape']))
    audit_pair(data['F'],W,output_dir=args.output,attempt_cpu_limit=args.attempt_cpu_limit,flow_cpu_limit=args.flow_cpu_limit,block_cpu_limit=args.block_cpu_limit)


if __name__=='__main__':main()
