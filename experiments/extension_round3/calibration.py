"""Finite label-free paths; eligibility is recomputed for each requested target."""
import time
import numpy as np
from method_extension.extension_round3.convex import FusionProblem,solve,eligible,matched,lengths
from method_extension.extension_round3.e7_cavity_graph import graph_weights
from method_extension.extension_round3.e1_v3_selective_tube import tube_distances
from method_extension.extension_round3.e5_v2_selective_guard import guard_coefficients
from .common import *


def parameters(H,W,evidence,method):
    from method_extension.next_round.certified_solver import graph_arrays
    B,i,j,w=graph_arrays(W);kind=method['family'];score=np.ones(len(w)) if method['score'] in ['uniform','none'] else evidence['scores'][method['score']]
    kw={};meta={}
    if kind=='graph':kw['weights'],meta=graph_weights(w,score)
    if kind=='tube':kw['tubes'],meta=tube_distances(w,lengths(B@H),score,uniform_eta=method.get('eta') if method['score']=='uniform' else None)
    if kind=='guard':kw['alpha'],meta=guard_coefficients(w,score,uniform=method['score']=='uniform')
    return kw,meta


def calibrate(H,W,kw,rho,folder,*,cpu_limit=1770.,max_lambdas=32,warm=None,max_iter=200000000):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);start=time.process_time();path=read(folder/'path.json') if (folder/'path.json').exists() else {'points':[],'CPU_seconds':0.,'targets':{}}
    points=path['points'];prior_cpu=path['CPU_seconds'];nearest=None;reason='SEARCH_LIMIT'
    proto=FusionProblem(H,W,1.,**kw);unit=np.divide(proto.h,lengths(proto.h)[:,None],out=np.zeros_like(proto.h),where=lengths(proto.h)[:,None]>0)
    force=float(np.linalg.norm(proto.B.T@(proto.weights[:,None]*unit)))*(2 if proto.guard else 1)
    initial=max(1e-12,rho*max(proto.S,1e-12)/max(force,1e-12))
    seen={p['lambda'] for p in points};new_checkpoint=warm
    def restore(p):return get_arrays(ArtifactStore(folder.parent.parent),p['result'])
    def select():
        valid=[]
        for p in points:
            cert=p['certificate']
            if eligible(cert,rho):valid.append(p)
        if valid:return min(valid,key=lambda p:(abs(p['certificate']['movement']-rho)+p['certificate']['movement_error'],p['lambda']))
        return min(points,key=lambda p:(abs(p['certificate']['movement']-rho),p['lambda'])) if points else None
    while True:
        nearest=select()
        if nearest and matched(nearest['certificate'],rho):reason='MATCHED';break
        elapsed=time.process_time()-start
        if prior_cpu+elapsed>=cpu_limit:reason='PATH_CPU_LIMIT';break
        retry=None
        if points:
            closest=min(points,key=lambda p:abs(p['certificate']['movement']-rho))
            used=closest.get('fit_CPU_seconds',closest['certificate'].get('CPU_seconds',0.))
            if closest['certificate']['valid_bound'] and not eligible(closest['certificate'],rho) and used<550.:retry=closest
        if retry is None and len(seen)>=max_lambdas:reason='SEARCH_LIMIT';break
        valid=[p for p in points if eligible(p['certificate'],rho)]
        lower=[p for p in valid if p['certificate']['movement']+p['certificate']['movement_error']<rho]
        upper=[p for p in valid if p['certificate']['movement']-p['certificate']['movement_error']>rho]
        lo=max(lower,key=lambda p:p['lambda']) if lower else None;hi=min(upper,key=lambda p:p['lambda']) if upper else None
        if retry is not None:lam=retry['lambda']
        elif lo and hi and lo['lambda']<hi['lambda']:
            fraction=np.clip((rho-lo['certificate']['movement'])/(hi['certificate']['movement']-lo['certificate']['movement']),.2,.8)
            lam=float(np.exp((1-fraction)*np.log(lo['lambda'])+fraction*np.log(hi['lambda'])))
        elif lo:lam=lo['lambda']*2
        elif hi:lam=hi['lambda']/2
        elif not points:lam=initial
        else:
            # An unresolved point receives no second 600-second attempt at the
            # same lambda. Retain its finite endpoint and exact numerical limit.
            reason='UNCERTIFIED_PATH_POINT';break
        if lam in seen and retry is None:reason='REPEATED_BRACKET_POINT';break
        seen.add(lam);P=FusionProblem(H,W,lam,**kw)
        if retry is not None:
            previous=restore(retry);new_checkpoint=previous['checkpoint'];new_checkpoint['same_lambda']=True
        elif nearest:
            previous=restore(nearest);new_checkpoint=previous['checkpoint'];new_checkpoint['same_lambda']=False
        point_index=points.index(retry) if retry is not None else len(points)
        segment=len(retry.get('segments',[]))+1 if retry is not None else 0
        history=folder/f'lambda-{point_index:02d}-segment-{segment:02d}.jsonl'
        def callback(state,cert,save):
            with history.open('a') as f:f.write(json.dumps({'iteration':state['iteration'],'CPU_seconds':state['CPU_seconds'],**scalar(cert)},allow_nan=False)+'\n')
            if save:save_continuation(folder/'continuation',dict(lambda_value=lam,state=state,best=cert))
        remaining=cpu_limit-prior_cpu-(time.process_time()-start)
        if remaining<15:reason='PATH_CPU_LIMIT';break
        used_fit=retry.get('fit_CPU_seconds',retry['certificate'].get('CPU_seconds',0.)) if retry is not None else 0.
        result=solve(P,rho=rho,cpu_limit=min(570.-used_fit,remaining-5),max_iter=max_iter,checkpoint=new_checkpoint,callback=callback)
        store=ArtifactStore(folder.parent.parent);ref=put_arrays(store,result);p={'lambda':lam,'rho_requested':rho,'certificate':scalar(result),'result':ref,'history_file':str(history.relative_to(store.root))}
        p['fit_CPU_seconds']=used_fit+result['CPU_seconds']
        if retry is not None:
            p['segments']=retry.get('segments',[])+[{k:v for k,v in retry.items() if k!='segments'}];points[point_index]=p
        else:points.append(p)
        path['CPU_seconds']=prior_cpu+time.process_time()-start;atomic_json(folder/'path.json',path)
        if result['stopping_reason']=='NUMERICAL_FAILURE':reason='NUMERICAL_FAILURE';break
        if not eligible(result,rho):reason='FIT_CPU_LIMIT' if result['stopping_reason']=='CPU_LIMIT' else result['stopping_reason'];break
    nearest=select();path['CPU_seconds']=prior_cpu+time.process_time()-start
    path['targets'][str(rho)]={'reason':reason,'point_index':points.index(nearest) if nearest else None};atomic_json(folder/'path.json',path)
    if nearest:return nearest,{'status':'QUALIFIED_MATCHED' if matched(nearest['certificate'],rho) else reason,'qualified':matched(nearest['certificate'],rho),'certified':eligible(nearest['certificate'],rho),'path_CPU_seconds':path['CPU_seconds'],'distinct_lambdas':len(points)}
    return None,{'status':reason,'qualified':False,'certified':False,'path_CPU_seconds':path['CPU_seconds'],'distinct_lambdas':len(points)}
