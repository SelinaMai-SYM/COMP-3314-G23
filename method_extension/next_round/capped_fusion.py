"""Existing truncated group penalty adapted to SSC; no global certificate claimed.

Penalty: Pan, Shen & Liu (JMLR 2013); related robust-edge motivation:
Shah & Koltun (PNAS 2017). From-scratch active-edge block minimization.
"""
import time
import numpy as np
from scipy import sparse
from .certified_solver import graph_arrays, solve


def capped_objective(G,F,W,gamma,tau,*,fidelity='radial',scale=1.):
    B,_,_,w=graph_arrays(W);r=np.linalg.norm(G-F,axis=1)
    data=np.sum(r) if fidelity=='radial' else np.sum(r*r)/(2*scale)
    return float(data+2*gamma*w@np.minimum(np.linalg.norm(B@G,axis=1),tau))


def fit(F,W,gamma,tau,*,fidelity='radial',scale=1.,G_init=None,max_outer=20,max_iter=30000,time_limit=600.):
    if tau<=0 or not np.isfinite(tau):raise ValueError('tau must be positive finite')
    G=np.array(F if G_init is None else G_init,copy=True);B,i,j,w=graph_arrays(W);start=time.perf_counter();cpu=time.process_time();steps=0;history=[];inners=[];status='OUTER_MAX_ITER';value=capped_objective(G,F,W,gamma,tau,fidelity=fidelity,scale=scale)
    for outer in range(max_outer):
        active=np.linalg.norm(B@G,axis=1)<=tau
        Wsub=sparse.coo_matrix((np.r_[w[active],w[active]],(np.r_[i[active],j[active]],np.r_[j[active],i[active]])),shape=W.shape).tocsr()
        remaining=time_limit-(time.perf_counter()-start)
        if remaining<=0 or steps>=max_iter:status='BUDGET_UNCERTIFIED';break
        inner=solve(F,Wsub,gamma,delta=scale if fidelity=='squared' else 0.,fidelity=fidelity,G_init=G,max_iter=max_iter-steps,time_limit=remaining)
        steps+=inner['iterations'];new=inner['G'];newvalue=capped_objective(new,F,W,gamma,tau,fidelity=fidelity,scale=scale)
        inners.append({k:v for k,v in inner.items() if k not in ['G','q','history']})
        if newvalue>value+1e-10*max(1,abs(value)):status='MONOTONICITY_REJECTED';break
        history.append({'outer':outer,'objective':newvalue,'active_edges':int(active.sum()),'inner_gap':inner['gap'],'inner_certified':inner['certified']})
        G=new;value=newvalue
        if not inner['certified']:status='INNER_UNCERTIFIED';break
        if np.array_equal(active,np.linalg.norm(B@G,axis=1)<=tau):status='ACTIVE_SET_FIXED_POINT';break
    return {'G':G,'objective':value,'status':status,'local_qualified':status=='ACTIVE_SET_FIXED_POINT','globally_certified':False,'iterations':steps,'history':history,'inners':inners,'wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu}
