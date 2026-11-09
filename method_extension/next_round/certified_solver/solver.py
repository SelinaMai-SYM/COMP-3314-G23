from __future__ import annotations
import time
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components


def graph_arrays(W):
    W=sparse.csr_matrix(W,dtype=float);W.sum_duplicates();W.eliminate_zeros()
    if W.shape[0]!=W.shape[1] or not np.isfinite(W.data).all() or np.any(W.data<0):raise ValueError('W must be finite, square, nonnegative')
    if np.any(W.diagonal()!=0) or sparse.linalg.norm(W-W.T)>1e-10*max(1,sparse.linalg.norm(W)):raise ValueError('W must be symmetric and have no self loops')
    upper=sparse.triu(W,k=1).tocoo();i,j,w=upper.row,upper.col,upper.data
    rows=np.repeat(np.arange(len(w)),2);cols=np.column_stack([i,j]).ravel()
    B=sparse.csr_matrix((np.tile([1.,-1.],len(w)),(rows,cols)),shape=(len(w),W.shape[0]))
    return B,i,j,w


def objective(G,F,B,c,*,delta=0.,a=None,fidelity='radial'):
    a=np.ones(len(F)) if a is None else a
    r=np.linalg.norm(G-F,axis=1)
    if fidelity=='squared':loss=r*r/(2*delta)
    elif delta>0:loss=np.where(r<=delta,r*r/(2*delta),r-delta/2)
    else:loss=r
    return float(a@loss+c@np.linalg.norm(B@G,axis=1))


def certificate(q,F,B,c,*,delta=0.,a=None,fidelity='radial'):
    a=np.ones(len(F)) if a is None else np.asarray(a)
    edge=np.linalg.norm(q,axis=1);bt=B.T@q;node=np.linalg.norm(bt,axis=1)
    alpha=1.
    nz=edge>0
    if nz.any():alpha=min(alpha,float(np.min(c[nz]/edge[nz])))
    if fidelity!='squared':
        nz=node>0
        if nz.any():alpha=min(alpha,float(np.min(a[nz]/node[nz])))
    alpha=max(0.,min(1.,alpha))*(1-1e-12)
    feasible=q*alpha;bt=B.T@feasible
    edge=np.linalg.norm(feasible,axis=1);node=np.linalg.norm(bt,axis=1)
    edge_v=float(np.maximum(edge-c,0).max(initial=0))
    node_v=0. if fidelity=='squared' else float(np.maximum(node-a,0).max(initial=0))
    dual=float(np.sum(bt*F)-delta/2*np.sum(node*node/a))
    return {'dual':dual,'q':feasible,'edge_violation':edge_v,'node_violation':node_v,'alpha':alpha}


def threshold(F,W,a=None):
    F=np.asarray(F,dtype=float);a=np.ones(len(F)) if a is None else np.asarray(a,dtype=float)
    B,i,j,w=graph_arrays(W);d=B@F;r=np.linalg.norm(d,axis=1)
    u=np.divide(d,r[:,None],out=np.zeros_like(d),where=r[:,None]>0)
    b=B.T@(2*w[:,None]*u);force=np.linalg.norm(b,axis=1)/a
    tv=float(w@r)
    # Infinity is asserted only for the explicit zero-TV analytic case.
    gamma0=float('inf') if tv==0 else (1/float(force.max()) if force.max()>0 else float('nan'))
    return {'gamma0':gamma0,'tv_F':tv,'coincident_edges':int(np.sum(r==0)),'sufficient_only':bool(np.any(r==0)),'q_unit_gamma':2*w[:,None]*u,'scale':float(np.median(r[r>0])) if np.any(r>0) else 0.}


def _consensus(F,W,a,fidelity,delta):
    _,labels=connected_components(W,directed=False);G=F.copy()
    for label in np.unique(labels):
        ids=np.flatnonzero(labels==label);x=F[ids];weights=a[ids];z=np.average(x,axis=0,weights=weights)
        if fidelity!='squared':
            for _ in range(100):
                r=np.linalg.norm(x-z,axis=1)
                denom=np.maximum(r,delta if delta>0 else np.finfo(float).eps*max(1,np.linalg.norm(x)))
                h=weights/denom;new=np.average(x,axis=0,weights=h)
                if np.linalg.norm(new-z)<=1e-12*max(1,np.linalg.norm(z)):z=new;break
                z=new
        G[ids]=z
    return G


def solve(F,W,gamma,*,delta=0.,a=None,fidelity='radial',max_iter=30000,time_limit=600.,gap_tol=1e-5,check_every=50,G_init=None,q_init=None,consensus_bound=True,warm_start_irls=False):
    start=time.perf_counter();cpu=time.process_time();F=np.asarray(F,dtype=float)
    if F.ndim!=2 or not len(F) or not np.isfinite(F).all():raise ValueError('F must be nonempty finite n by d')
    if not np.isfinite(gamma) or gamma<0 or not np.isfinite(delta) or delta<0:raise ValueError('invalid gamma/delta')
    if fidelity not in ['radial','squared'] or (fidelity=='squared' and delta<=0):raise ValueError('squared fidelity needs positive delta')
    a=np.ones(len(F)) if a is None else np.asarray(a,dtype=float)
    if a.shape!=(len(F),) or not np.isfinite(a).all() or np.any(a<=0):raise ValueError('invalid fidelity weights')
    B,i,j,w=graph_arrays(W)
    if B.shape[1]!=len(F):raise ValueError('W/F mismatch')
    c=2*float(gamma)*w;info=threshold(F,W,a)
    G=F.copy() if G_init is None else np.array(G_init,dtype=float,copy=True)
    if G.shape!=F.shape or not np.isfinite(G).all():raise ValueError('invalid G_init')
    bestG=G.copy();P=objective(G,F,B,c,delta=delta,a=a,fidelity=fidelity);source='initial'
    initialP=objective(F,F,B,c,delta=delta,a=a,fidelity=fidelity)
    if initialP<P:bestG=F.copy();P=initialP;source='F'
    q=np.zeros((len(w),F.shape[1])) if q_init is None else np.array(q_init,dtype=float,copy=True)
    if q.shape!=(len(w),F.shape[1]) or not np.isfinite(q).all():raise ValueError('invalid q_init')
    bestq=np.zeros_like(q);D=0.;violations=(0.,0.);history=[];iterations=0;reason='MAX_ITER_REACHED';status=reason
    analytic=(info['tv_F']==0 or gamma==0 or (delta==0 and fidelity=='radial' and gamma<=info['gamma0']))
    if analytic:
        bestG=F.copy();P=initialP
        cert=certificate(gamma*info['q_unit_gamma'],F,B,c,delta=delta,a=a,fidelity=fidelity)
        D=max(0.,cert['dual']);bestq=cert['q'];violations=(cert['edge_violation'],cert['node_violation']);reason=status='ANALYTIC_G_EQUALS_F'
    else:
        if warm_start_irls and fidelity=='radial' and delta==0:
            # A primal-only initializer cannot certify anything by itself.
            # Its acceptance uses the exact same objective, never labels.
            import signal
            from SSC_method.optimizer import shrink_embedding
            warm_started=time.perf_counter();warm={'requested':True,'max_iter':300 if len(F)<=3000 else 30}
            previous_handler=signal.getsignal(signal.SIGALRM)
            def timeout(_signum,_frame):raise TimeoutError('IRLS warm-start time allocation')
            try:
                signal.signal(signal.SIGALRM,timeout)
                signal.setitimer(signal.ITIMER_REAL,min(60.,max(.01,time_limit/4)))
                initialized=shrink_embedding(F,W,gamma,max_iter=warm['max_iter'],variant='E8')
                value=objective(initialized.patterns,F,B,c,delta=delta,a=a,fidelity=fidelity)
                warm.update(status='RETURNED_POINT',iterations=initialized.n_iterations,primal=value)
                if value<P:
                    G=initialized.patterns.copy();bestG=G.copy();P=value;source='IRLS_primal_upper_bound'
            except Exception as exc:warm.update(status='FALLBACK_TO_COLD',error=repr(exc))
            finally:
                signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous_handler)
            warm['wall_seconds']=time.perf_counter()-warm_started
        else:warm={'requested':False}
        if consensus_bound:
            candidate=_consensus(F,W,a,fidelity,delta);value=objective(candidate,F,B,c,delta=delta,a=a,fidelity=fidelity)
            if value<P:bestG=candidate;P=value;source='component_consensus_upper_bound'
        degree=np.bincount(np.r_[i,j],minlength=len(F));step=.99/np.sqrt(2*max(1,int(degree.max())))
        tau=sigma=float(step);Gbar=G.copy();average=np.zeros_like(G)
        for it in range(1,int(max_iter)+1):
            q+=sigma*(B@Gbar);r=np.linalg.norm(q,axis=1)
            factor=np.minimum(1.,np.divide(c,r,out=np.ones_like(c),where=r>0));q*=factor[:,None]
            Y=G-tau*(B.T@q);v=Y-F;r=np.linalg.norm(v,axis=1)
            if fidelity=='squared':s=delta/(delta+tau*a)
            else:
                s=np.where(r<=delta+tau*a,delta/(delta+tau*a),1-np.divide(tau*a,r,out=np.zeros_like(r),where=r>0))
            new=F+s[:,None]*v;Gbar=2*new-G;G=new;average+=(G-average)/it;iterations=it
            if it%check_every==0 or it==max_iter:
                for name,point in [('last_iterate',G),('ergodic_average',average)]:
                    value=objective(point,F,B,c,delta=delta,a=a,fidelity=fidelity)
                    if value<P:P=value;bestG=point.copy();source=name
                cert=certificate(q,F,B,c,delta=delta,a=a,fidelity=fidelity)
                if cert['dual']>D:D=cert['dual'];bestq=cert['q'];violations=(cert['edge_violation'],cert['node_violation'])
                gap=(P-D)/max(1.,abs(P),abs(D))
                if P<D-1e-9*max(1,abs(P),abs(D)):raise ArithmeticError('primal below feasible dual')
                if not np.isfinite(P+D+gap):raise ArithmeticError('nonfinite objective/gap')
                history.append({'iteration':it,'primal':P,'dual':D,'gap':gap,'wall_seconds':time.perf_counter()-start})
                if gap<=gap_tol and max(violations)<=1e-8:status=reason='PRIMAL_DUAL_GAP_CERTIFIED';break
                if time.perf_counter()-start>=time_limit:status=reason='TIMEOUT_UNCERTIFIED';break
    gap=(P-D)/max(1.,abs(P),abs(D))
    return {'G':bestG,'q':bestq,'primal':P,'dual':D,'absolute_gap':P-D,'gap':gap,'edge_violation':violations[0],'node_violation':violations[1],'iterations':iterations,'status':status,'stopping_reason':reason,'certified':bool(status in ['ANALYTIC_G_EQUALS_F','PRIMAL_DUAL_GAP_CERTIFIED']),'best_primal_source':source,'warm_start':warm if not analytic else {'requested':False,'reason':'analytic'},'history':history,'wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'gamma':float(gamma),'gamma_effective':float(gamma),'delta':float(delta),'fidelity':fidelity,'gamma0':info['gamma0'],'scale':info['scale'],'objective_target':'undirected_E8_c=2*gamma*w','movement':float(np.linalg.norm(bestG-F)/max(np.linalg.norm(F),np.finfo(float).tiny))}
