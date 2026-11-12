"""Exact sparse edge-deletion pilot; never constructs a full dense inverse."""
from __future__ import annotations
import time
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from method_extension.next_round.certified_solver import graph_arrays


def edge_deletion_evidence(H,W,*,tau_multiplier=1.,batch_size=32,cpu_limit=3590.,checkpoint=None,callback=None):
    start=time.process_time();H=np.asarray(H,dtype=np.float64);B,i,j,w=graph_arrays(W);n=len(H)
    degree=np.asarray(W.sum(axis=1)).ravel();positive=degree[degree>0]
    tau=float(tau_multiplier/np.median(positive)) if len(positive) else 0.
    M=(sparse.eye(n,format='csc')+tau*(B.T@sparse.diags(w)@B)).tocsc();factor=splu(M)
    Z=factor.solve(H);residual=float(np.linalg.norm(M@Z-H)/max(np.linalg.norm(H),np.finfo(float).tiny))
    diag=np.zeros(n);ij=np.zeros(len(w));ji=np.zeros(len(w));completed=0
    if checkpoint:
        if checkpoint['tau']!=tau:raise ValueError('evidence checkpoint tau changed')
        diag=checkpoint['diagonal'].copy();ij=checkpoint['inverse_ij'].copy();ji=checkpoint['inverse_ji'].copy();completed=checkpoint['completed'];residual=max(residual,checkpoint['max_residual'])
    for begin in range(completed,n,batch_size):
        end=min(n,begin+batch_size);cols=np.arange(begin,end);rhs=np.zeros((n,len(cols)));rhs[cols,np.arange(len(cols))]=1.
        solution=factor.solve(rhs);residual=max(residual,float(np.max(np.linalg.norm(M@solution-rhs,axis=0))))
        diag[cols]=solution[cols,np.arange(len(cols))]
        mask=(j>=begin)&(j<end);ij[mask]=solution[i[mask],j[mask]-begin]
        mask=(i>=begin)&(i<end);ji[mask]=solution[j[mask],i[mask]-begin]
        state={'tau':tau,'diagonal':diag,'inverse_ij':ij,'inverse_ji':ji,'completed':end,'max_residual':residual}
        if callback:callback(state)
        if residual>1e-9:raise ArithmeticError('pilot/inverse linear system residual exceeds 1e-9')
        if time.process_time()-start>cpu_limit and end<n:raise TimeoutError('exact evidence CPU cap; recoverable coordinate checkpoint retained')
    symmetry=float(np.max(np.abs(ij-ji),initial=0))
    r=diag[i]+diag[j]-ij-ji;raw=tau*w*r
    if symmetry>1e-9 or np.min(raw,initial=0)<-1e-12 or np.max(raw,initial=0)>=1:raise ArithmeticError('invalid retained inverse symmetry or leverage')
    leverage=np.maximum(raw,0.);denom=1-leverage;bound=1/(1+2*tau*w)
    if np.min(denom-bound,initial=0)<-1e-10:raise ArithmeticError('edge-deletion denominator bound violated')
    pilot=np.sum((B@Z)**2,axis=1);cavity=pilot/denom**2;anchor=np.sum((B@H)**2,axis=1)
    scores={'cavity':cavity,'pilot':pilot,'anchor':anchor,'leverage':leverage}
    for seed in [400,401,402]:scores['shuffle'+str(seed)]=np.random.Generator(np.random.PCG64(seed)).permutation(cavity)
    return dict(i=i,j=j,w=w,tau=tau,Z=Z,diagonal=diag,inverse_ij=ij,inverse_ji=ji,r=r,raw_leverage=raw,leverage=leverage,denominator=denom,denominator_bound=bound,scores=scores,max_residual=residual,inverse_symmetry=symmetry,CPU_seconds=time.process_time()-start,degenerate=not len(w))
