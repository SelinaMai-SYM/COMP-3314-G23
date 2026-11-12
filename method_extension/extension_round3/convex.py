"""Float64 diagonal PDHG with independent best primal and feasible dual bounds."""
from __future__ import annotations
import time
import numpy as np
from method_extension.next_round.certified_solver import graph_arrays


def lengths(x):return np.linalg.norm(x,axis=1)
def balls(x,r):return x*np.minimum(1.,np.divide(r,lengths(x),out=np.ones(len(x)),where=lengths(x)>0))[:,None]


class FusionProblem:
    def __init__(self,H,W,lam,*,weights=None,tubes=None,alpha=None):
        self.H=np.asarray(H,dtype=np.float64);self.B,self.i,self.j,self.w=graph_arrays(W);self.lam=float(lam)
        if self.H.ndim!=2 or len(H)!=W.shape[0] or not np.isfinite(self.H).all() or not np.isfinite(lam) or lam<0:raise ValueError('invalid anchor/graph/coefficient')
        self.weights=self.w.copy() if weights is None else np.asarray(weights,dtype=float)
        self.a=np.zeros(len(self.w)) if tubes is None else np.asarray(tubes,dtype=float)
        self.alpha=np.zeros(len(self.w)) if alpha is None else np.asarray(alpha,dtype=float)
        if any(x.shape!=self.w.shape or not np.isfinite(x).all() or np.any(x<0) for x in [self.weights,self.a,self.alpha]):raise ValueError('invalid edge coefficients')
        if tubes is not None and alpha is not None:raise ValueError('independent candidates cannot be stacked')
        if (tubes is not None or alpha is not None) and not np.array_equal(self.weights,self.w):raise ValueError('tube/guard keeps W0')
        self.guard=alpha is not None;self.h=self.B@self.H;self.S=float(np.linalg.norm(H-H.mean(axis=0)))
        self.r1=lam*self.weights*(1+self.alpha);self.r2=lam*self.weights*self.alpha
        self.constant=float(self.r2@lengths(self.h));degree=np.bincount(np.r_[self.i,self.j],minlength=len(H));blocks=2 if self.guard else 1
        self.tau=np.divide(.99,blocks*degree,out=np.ones(len(H)),where=degree>0);self.sigma=.495

    def certificate(self,G,q,p=None):
        q=balls(np.asarray(q),self.r1);p=np.zeros_like(q) if p is None else balls(np.asarray(p),self.r2)
        e=self.B@G;delta=G-self.H;A=self.B.T@(q+p);fid=.5*float(np.sum(delta**2))
        if self.guard:
            change=e-self.h;primal=fid+float(self.r1@lengths(e)+self.r2@lengths(change))-self.constant
            dual=float(np.sum(self.h*q))-.5*float(np.sum(A**2))-self.constant
            support=float(np.sum(self.r1*lengths(e)-np.sum(q*e,axis=1)+self.r2*lengths(change)-np.sum(p*change,axis=1)))
        else:
            penalty=self.r1*np.maximum(lengths(e)-self.a,0.);primal=fid+float(penalty.sum())
            dual=float(np.sum(self.h*q))-.5*float(np.sum(A**2))-float(self.a@lengths(q))
            support=float(np.sum(penalty-np.sum(q*e,axis=1)+self.a*lengths(q)))
        stable=.5*float(np.sum((delta+A)**2))+support;signed=primal-dual;scale=max(1.,abs(primal),abs(dual));tol=1e-12*scale
        cap=max(float(np.max(np.maximum(lengths(q)-self.r1,0)/np.maximum(1.,self.r1),initial=0)),float(np.max(np.maximum(lengths(p)-self.r2,0)/np.maximum(1.,self.r2),initial=0)))
        valid=bool(np.isfinite(G).all() and np.isfinite(stable) and signed>=-tol and stable>=-tol and abs(stable-signed)<=1e-9*scale and cap<=1e-8)
        gap=max(0.,stable,signed);error=float(np.sqrt(2*gap)/self.S) if self.S else 0.
        return dict(G=G,q=q,p=p,primal=primal,dual=dual,signed_gap=signed,stable_gap=stable,gap=gap,relative_gap=gap/scale,gap_roundoff_tolerance=tol,capacity_residual=cap,valid_bound=valid,movement=float(np.linalg.norm(delta)/self.S) if self.S else 0.,movement_error=error)


def eligible(cert,rho):
    return bool(cert['valid_bound'] and cert['relative_gap']<=1e-6 and cert['capacity_residual']<=1e-8 and cert['movement_error']<=.005*rho)


def matched(cert,rho):return eligible(cert,rho) and abs(cert['movement']-rho)+cert['movement_error']<=.01*rho


def solve(P,*,rho=.1,cpu_limit=570.,max_iter=200000,checkpoint=None,callback=None):
    start=time.process_time();G=P.H.copy();q=np.zeros_like(P.h);p=np.zeros_like(q);iteration0=0;prior_cpu=0.
    if checkpoint:
        G=np.asarray(checkpoint['Z']).copy();q=balls(np.asarray(checkpoint['q']),P.r1);p=balls(np.asarray(checkpoint.get('p',p)),P.r2)
        iteration0=int(checkpoint.get('iteration',0));prior_cpu=float(checkpoint.get('CPU_seconds',0.))
    bar=np.asarray(checkpoint['bar']).copy() if checkpoint and checkpoint.get('same_lambda',False) else G.copy()
    best=P.certificate(G,q,p);bestG=best['G'].copy();bestq=best['q'].copy();bestp=best['p'].copy();best_primal=best['primal'];best_dual=best['dual'];reason='ITERATION_LIMIT'
    if checkpoint and checkpoint.get('same_lambda',False) and 'best_G' in checkpoint:
        retained=P.certificate(checkpoint['best_G'],checkpoint['best_q'],checkpoint['best_p'])
        if retained['valid_bound']:
            best=retained;bestG=retained['G'].copy();bestq=retained['q'].copy();bestp=retained['p'].copy();best_primal=best['primal'];best_dual=best['dual']
    for k in range(max_iter+1):
        if k%50==0:
            cert=P.certificate(G,q,p)
            if cert['valid_bound']:
                if cert['primal']<best_primal:bestG=G.copy();best_primal=cert['primal']
                if cert['dual']>best_dual:bestq=cert['q'].copy();bestp=cert['p'].copy();best_dual=cert['dual']
                best=P.certificate(bestG,bestq,bestp)
            done=eligible(best,rho)
            state=dict(Z=G,bar=bar,q=q,p=p,iteration=iteration0+k,CPU_seconds=prior_cpu+time.process_time()-start,same_lambda=True,best_G=bestG,best_q=bestq,best_p=bestp)
            if callback:callback(state,best,k%1000==0 or done)
            if not cert['valid_bound']:reason='NUMERICAL_FAILURE';break
            if done:reason='CERTIFIED';break
            if time.process_time()-start>=cpu_limit:reason='CPU_LIMIT';break
        edges=P.B@bar;q=q+P.sigma*edges
        if np.any(P.a):
            sizes=lengths(q);q*=np.maximum(0.,1-np.divide(P.sigma*P.a,sizes,out=np.zeros_like(sizes),where=sizes>0))[:,None]
        q=balls(q,P.r1)
        if P.guard:p=balls(p+P.sigma*(edges-P.h),P.r2)
        nextG=(G-P.tau[:,None]*(P.B.T@(q+p))+P.tau[:,None]*P.H)/(1+P.tau[:,None]);bar=2*nextG-G;G=nextG
    best.update(certified=eligible(best,rho),stopping_reason=reason,iterations=iteration0+k,CPU_seconds=time.process_time()-start,checkpoint=state)
    return best
