"""Quadratic graph fusion with independently recomputable numerical certificates."""
from __future__ import annotations
import time
import numpy as np
from scipy import linalg
from method_extension.next_round.certified_solver import graph_arrays


def norms(x):return np.linalg.norm(x,axis=1)
def center(x):return x-x.mean(axis=0,keepdims=True)
def sym(x):return (x+x.T)*.5
def balls(x,c):
    lengths=norms(x)
    return x*np.minimum(1.,np.divide(c,lengths,out=np.ones_like(lengths),where=lengths>0))[:,None]
def psd(x):
    values,vectors=linalg.eigh(sym(x),check_finite=False)
    return (vectors*np.maximum(values,0.))@vectors.T


class QuadraticProblem:
    def __init__(self,H,W,lam,method='QSSC',*,eta=.25,alpha=1.,eta_dir=.5):
        self.H=np.asarray(H,dtype=float)
        if self.H.ndim!=2 or not np.isfinite(self.H).all():raise ValueError('finite n-by-K H required')
        if method not in ['QSSC','E1_v2','E4','E5','E6'] or not np.isfinite(lam) or lam<0:raise ValueError('invalid model')
        if not 0<=eta<=1 or not 0<=eta_dir<1 or alpha<0:raise ValueError('invalid fixed parameter')
        self.B,self.i,self.j,self.w=graph_arrays(W);self.method=method;self.lam=float(lam);self.eta=float(eta);self.alpha=float(alpha);self.eta_dir=float(eta_dir)
        if len(H)!=W.shape[0]:raise ValueError('graph and anchor differ')
        self.mean=H.mean(axis=0,keepdims=True);Hc=center(H);self.scale=float(linalg.norm(Hc));self.h=self.B@H;self.tv_H=float(self.w@norms(self.h));self.rank_info={}
        degree=np.bincount(np.r_[self.i,self.j],minlength=len(H));self.normB2=max(1.,2*float(degree.max(initial=0)))
        if method=='E6':
            u,s,vt=linalg.svd(Hc,full_matrices=False,check_finite=False);tol=max(H.shape)*np.finfo(float).eps*(s[0] if len(s) else 0);keep=s>tol
            self.U=u[:,keep];self.s=s[keep];self.V=vt[keep].T;self.Y=self.U*self.s
            residual=Hc-self.Y@self.V.T;condition=float(self.s[0]/self.s[-1]) if len(self.s) else 1.
            self.rank_info={'rank':int(sum(keep)),'svd_tolerance':float(tol),'singular_values':s.tolist(),'smallest_retained':float(self.s[-1]) if len(self.s) else None,'condition_number':condition,'discarded_energy':float(np.sum(residual**2)),'whitened_roundoff_indicator':float(50*np.finfo(float).eps*max(H.shape)*condition)}
            self.anchor=self.Y;self.edge_H=self.B@self.Y;self.sigma2=np.diag(self.s**2)
            self.tau=np.full(len(H),.99);self.qstep=.4/self.normB2;self.sstep=.4/max(float(self.s[0]**2) if len(self.s) else 0.,np.finfo(float).tiny)
        else:
            self.anchor=H;self.edge_H=self.h
            blocks=2 if method=='E5' and alpha>0 else 1
            self.tau=np.divide(.99,blocks*degree,out=np.ones(len(H)),where=degree>0);self.qstep=.495;self.sstep=0.
        self.a=eta*norms(self.edge_H) if method=='E1_v2' else np.zeros(len(self.w));self.r1=lam*self.w*(1+alpha if method=='E5' else 1);self.r2=lam*alpha*self.w if method=='E5' else np.zeros(len(self.w))

    def reconstruct(self,Z):return self.mean+Z@self.V.T if self.method=='E6' else Z

    def whitened(self,Z):
        if not len(self.s):return np.empty((0,0))
        return sym((self.U.T@Z)/self.s[None,:])

    def repair(self,Z):
        if self.method!='E6':return Z,{'fraction':0.,'whitened_min_eigenvalue':None,'centering_residual':0.,'conditioning_reliable':True}
        Z=center(Z);T=self.whitened(Z);minimum=float(linalg.eigvalsh(T,check_finite=False)[0]) if len(T) else 1.
        target=self.eta_dir+1e-10;fraction=(target-minimum)/(1-minimum) if minimum<target else 0.
        fixed=center((1-fraction)*Z+fraction*self.Y);values=linalg.eigvalsh(self.whitened(fixed),check_finite=False) if len(T) else np.array([1.]);lower=float(values[0])
        if lower<self.eta_dir-1e-8:
            fixed=self.Y.copy();fraction=1.;lower=float(linalg.eigvalsh(self.whitened(fixed),check_finite=False)[0]) if len(T) else 1.
        return fixed,{'fraction':float(fraction),'raw_whitened_min_eigenvalue':minimum,'whitened_min_eigenvalue':lower,'centering_residual':float(np.max(np.abs(fixed.mean(axis=0)),initial=0)),'conditioning_reliable':self.rank_info['whitened_roundoff_indicator']<=1e-8}

    def certificate(self,Z,q,p=None,S=None):
        q=balls(q,self.r1);p=np.zeros_like(q) if p is None else balls(p,self.r2)
        Zf,repair=self.repair(Z);edges=self.B@Zf;residual=Zf-self.anchor
        fidelity=.5*float(np.sum(residual**2))
        if self.method=='E5':
            change=edges-self.edge_H;constant=self.lam*self.alpha*self.tv_H
            primal=fidelity+float(self.r1@norms(edges)+self.r2@norms(change))-constant
            A=self.B.T@(q+p);dual=float(np.sum(self.H*(self.B.T@q)))-.5*float(np.sum(A*A))-constant
            terms=self.r1*norms(edges)-np.sum(q*edges,axis=1)+self.r2*norms(change)-np.sum(p*change,axis=1)
            gap=.5*float(np.sum((residual+A)**2))+float(terms.sum())
        elif self.method=='E6':
            S=psd(np.zeros((len(self.s),len(self.s))) if S is None else S);A=center(self.B.T@q-self.Y@S)
            primal=fidelity+float(self.r1@norms(edges));dual=float(np.sum(self.Y*A))-.5*float(np.sum(A*A))+self.eta_dir*float(np.sum(self.sigma2*S))
            slack=sym(self.Y.T@Zf)-self.eta_dir*self.sigma2
            gap=.5*float(np.sum((residual+A)**2))+float(self.r1@norms(edges)-np.sum(q*edges))+float(np.sum(S*slack))
        else:
            A=self.B.T@q;penalty=self.r1*np.maximum(norms(edges)-self.a,0.)
            primal=fidelity+float(penalty.sum());dual=float(np.sum(self.H*A))-.5*float(np.sum(A*A))-float(self.a@norms(q))
            gap=.5*float(np.sum((residual+A)**2))+float(np.sum(penalty-np.sum(q*edges,axis=1)+self.a*norms(q)))
        signed=primal-dual;roundoff=1e-12*max(1.,abs(primal),abs(dual));negative=gap < -roundoff
        discrepancy=abs(signed-gap);consistent=discrepancy<=1e-9*max(1.,abs(primal),abs(dual))
        gap_for_error=max(0.,gap);uncertainty=(np.sqrt(2*gap_for_error)/self.scale if self.scale>0 else 0.) if not negative else None
        cap=float(np.max(np.maximum(norms(q)-self.r1,0)/np.maximum(1.,self.r1),initial=0))
        if self.method=='E5':cap=max(cap,float(np.max(np.maximum(norms(p)-self.r2,0)/np.maximum(1.,self.r2),initial=0)))
        psd_res=max(0.,-float(linalg.eigvalsh(S,check_finite=False)[0]))/max(1.,float(linalg.norm(S))) if self.method=='E6' and len(self.s) else 0.
        feasible=cap<=1e-8 and psd_res<=1e-8 and repair['conditioning_reliable'] and (self.method!='E6' or repair['whitened_min_eigenvalue']>=self.eta_dir-1e-8 and repair['centering_residual']<=1e-8)
        G=self.reconstruct(Zf);movement=float(linalg.norm(G-self.H)/self.scale) if self.scale>0 else 0.
        relative_gap=max(0.,signed)/max(1.,abs(primal),abs(dual));stable_relative=gap_for_error/max(1.,abs(primal),abs(dual))
        return {'G':G,'Zf':Zf,'q':q,'p':p,'S':S,'primal':primal,'raw_primal':self.raw_primal(Z),'dual':dual,'signed_subtracted_gap':signed,'stable_gap':gap,'gap_roundoff_tolerance':roundoff,'gap_consistent':consistent,'relative_gap':relative_gap,'stable_relative_gap':stable_relative,'movement_error':float(uncertainty) if uncertainty is not None else None,'movement':movement,'capacity_residual':cap,'PSD_residual':psd_res,'repair':repair,'feasible':bool(feasible),'valid_bound':bool(feasible and not negative and consistent),'rank_info':self.rank_info}

    def raw_primal(self,Z):
        d=self.B@Z;f=.5*float(np.sum((Z-self.anchor)**2))
        if self.method=='E5':return f+float(self.r1@norms(d)+self.r2@norms(d-self.edge_H))-self.lam*self.alpha*self.tv_H
        return f+float(self.r1@np.maximum(norms(d)-self.a,0))


def solve(problem,*,rho=.05,cpu_limit=580.,max_iter=200000,checkpoint=None,callback=None,check_every=50):
    """PDHG; objective-specific duals, feasible repaired E6 primal and stable gaps."""
    start=time.process_time();P=problem;Z=P.anchor.copy();q=np.zeros_like(P.edge_H);p=np.zeros_like(q);S=np.zeros((len(P.s),len(P.s))) if P.method=='E6' else None
    if checkpoint:
        Z=np.asarray(checkpoint['Z']).copy();q=balls(np.asarray(checkpoint['q']),P.r1);p=balls(np.asarray(checkpoint['p']),P.r2)
        if P.method=='E6':S=psd(np.asarray(checkpoint.get('S',S)))
    bar=Z.copy();best=P.certificate(Z,q,p,S);history=[];reason='ITERATION_LIMIT';iteration=0
    for iteration in range(max_iter+1):
        if iteration%check_every==0:
            cert=P.certificate(Z,q,p,S)
            # The gap is evaluated for an actual feasible primal/dual pair.
            if cert['valid_bound'] and (not best['valid_bound'] or cert['stable_gap']<best['stable_gap']):best=cert
            history.append({k:cert[k] for k in ['primal','dual','stable_gap','relative_gap','movement','movement_error']})
            qualified=best['valid_bound'] and best['relative_gap']<=1e-6 and best['stable_relative_gap']<=1e-6 and best['movement_error']<=.02*rho
            if callback and (iteration%1000==0 or qualified):callback({'Z':Z,'bar':bar,'q':q,'p':p,'S':S,'best':best,'iteration':iteration,'CPU_seconds':time.process_time()-start})
            if qualified:reason='CERTIFIED';break
            if not cert['gap_consistent'] or cert['stable_gap'] < -cert['gap_roundoff_tolerance']:reason='NUMERICAL_FAILURE';break
            if not cert['repair']['conditioning_reliable']:reason='NUMERICAL_CONDITIONING';break
            if time.process_time()-start>=cpu_limit:reason='CPU_LIMIT';break
        edges=P.B@bar;q=q+P.qstep*edges
        if P.method=='E1_v2':
            lengths=norms(q);q*=np.maximum(0,1-np.divide(P.qstep*P.a,lengths,out=np.zeros_like(lengths),where=lengths>0))[:,None]
        q=balls(q,P.r1)
        if P.method=='E5':p=balls(p+P.qstep*(edges-P.edge_H),P.r2)
        if P.method=='E6':S=psd(S+P.sstep*(P.eta_dir*P.sigma2-sym(P.Y.T@bar)))
        adj=P.B.T@(q+p)
        if P.method=='E6':adj-=P.Y@S
        next_Z=(Z-P.tau[:,None]*adj+P.tau[:,None]*P.anchor)/(1+P.tau[:,None])
        if P.method=='E6':next_Z=center(next_Z)
        bar=2*next_Z-Z;Z=next_Z
    state={'Z':Z,'bar':bar,'q':q,'p':p,'S':S,'iteration':iteration,'CPU_seconds':time.process_time()-start}
    best.update(certified=bool(best['valid_bound'] and best['relative_gap']<=1e-6 and best['stable_relative_gap']<=1e-6 and best['movement_error']<=.02*rho),stopping_reason=reason,iterations=iteration,CPU_seconds=time.process_time()-start,checkpoint=state,history=history)
    return best
