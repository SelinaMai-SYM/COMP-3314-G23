"""A bounded candidate construction, not a general dual feasibility oracle."""
from __future__ import annotations
import time
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import LinearOperator, cg
from .solver import _consensus, certificate, graph_arrays, objective


def component_dual_flow(F,W,gamma,*,cpu_time_limit=300.,max_iter=12000,rtol=1e-10):
    """Pair a component-consensus primal with an independently solved edge flow.

    The weighted Laplacian solves B.T @ diag(w) @ B z = target. Targets are
    balanced within components, since a graph divergence must sum to zero.
    Geometric-median residuals need not balance exactly; this construction
    does not assume they do. Only the measured feasible dual gap is accepted.
    Failure or a large gap does not establish that another certificate cannot
    exist. No labels are accepted.
    """
    started=time.perf_counter();cpu=time.process_time();F=np.asarray(F,dtype=float)
    if F.ndim!=2 or not np.isfinite(F).all():raise ValueError('invalid F')
    if not np.isfinite(gamma) or gamma<0:raise ValueError('invalid gamma')
    if cpu_time_limit<=0 or cpu_time_limit>300:raise ValueError('flow CPU limit must be in (0,300] seconds')
    B,i,j,w=graph_arrays(W)
    if W.shape!=(len(F),len(F)):raise ValueError('W/F mismatch')
    G=_consensus(F,W,np.ones(len(F)),'radial',0.)
    residual=F-G;norm=np.linalg.norm(residual,axis=1)
    target=np.divide(residual,norm[:,None],out=np.zeros_like(residual),where=norm[:,None]>1e-14)
    n_components,membership=connected_components(W,directed=False)
    potential=np.zeros_like(F);history=[];status='RETURNED_CANDIDATE'
    laplacian=(B.T@sparse.diags(w)@B).tocsr()
    def check_cpu(_=None):
        if time.process_time()-cpu>=cpu_time_limit:raise TimeoutError('component dual flow CPU allocation')
    try:
        for label in range(n_components):
            check_cpu();ids=np.flatnonzero(membership==label)
            raw=target[ids].copy();imbalance=raw.sum(axis=0)
            coincident=norm[ids]<=1e-14
            # At a coincident observation, any vector in its fidelity ball
            # is a valid subgradient. Use that freedom before mean balancing.
            if np.any(coincident) and np.linalg.norm(imbalance)<=coincident.sum():
                raw[coincident]=-imbalance/coincident.sum()
            raw-=raw.mean(axis=0)
            target[ids]=raw
            if len(ids)<=1:continue
            free=ids[1:];matrix=laplacian[free][:,free].tocsr()
            diag=matrix.diagonal()
            if np.any(diag<=0):raise ArithmeticError('nonpositive reduced Laplacian diagonal')
            M=LinearOperator(matrix.shape,matvec=lambda x,d=diag:x/d)
            for column in range(F.shape[1]):
                check_cpu();rhs=raw[1:,column];count=[0]
                def callback(_):
                    count[0]+=1;check_cpu()
                value,info=cg(matrix,rhs,rtol=rtol,atol=0,maxiter=max_iter,M=M,callback=callback)
                potential[free,column]=value
                relative=float(np.linalg.norm(matrix@value-rhs)/max(np.linalg.norm(rhs),np.finfo(float).tiny))
                history.append({'component':label,'column':column,'iterations':count[0],'cg_info':int(info),'relative_residual':relative,'target_imbalance_before':float(np.linalg.norm(imbalance))})
                if info!=0:status='INCOMPLETE_LINEAR_SOLVE'
    except TimeoutError as exc:
        status='CPU_LIMIT_CANDIDATE';history.append({'error':str(exc)})
    except Exception as exc:
        status='FAILED_CANDIDATE';history.append({'error':repr(exc)})
    q=w[:,None]*(B@potential)
    cert=certificate(q,F,B,2*gamma*w)
    # q=0 is always feasible and has lower bound zero.
    if cert['dual']<0:cert=certificate(np.zeros_like(q),F,B,2*gamma*w)
    P=objective(G,F,B,2*gamma*w);D=cert['dual'];gap=(P-D)/max(1.,abs(P),abs(D))
    return {'G':G,'q':cert['q'],'primal':P,'dual':D,'gap':float(gap),
        'edge_violation':cert['edge_violation'],'node_violation':cert['node_violation'],
        'certified':bool(gap<=1e-5 and max(cert['edge_violation'],cert['node_violation'])<=1e-8),
        'status':status,'history':history,'cpu_seconds':time.process_time()-cpu,
        'wall_seconds':time.perf_counter()-started,'cpu_time_limit':cpu_time_limit,
        'interpretation':'Failure of this particular flow is not proof that no feasible certificate exists.'}
