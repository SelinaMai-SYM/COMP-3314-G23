"""Objective-specific primal-dual refinement in original edge coordinates.

The primal iterate and the actual rounding matrix are separate objects. This
module never normalizes its returned representation and never accepts labels.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import time
import numpy as np
from method_extension.next_round.certified_solver import graph_arrays


def row_norm(x):
    x=np.asarray(x,dtype=np.float64)
    scale=np.max(np.abs(x),axis=1,initial=0.)
    unit=np.divide(x,scale[:,None],out=np.zeros_like(x),where=scale[:,None]>0)
    return scale*np.sqrt(np.sum(unit*unit,axis=1))


def rowunit(x):
    x=np.asarray(x,dtype=np.float64);r=row_norm(x)
    return np.divide(x,r[:,None],out=np.zeros_like(x),where=r[:,None]>0)


@dataclass
class Hinges:
    anchors: np.ndarray
    normals: np.ndarray
    beta: np.ndarray

    @classmethod
    def empty(cls,d):return cls(np.empty(0,dtype=np.int64),np.empty((0,d)),np.empty(0))
    def apply(self,G):return np.sum(G[self.anchors]*self.normals,axis=1)
    def adjoint(self,p,shape):
        result=np.zeros(shape,dtype=np.float64)
        np.add.at(result,self.anchors,p[:,None]*self.normals)
        return result
    def validate(self,n,d):
        self.anchors=np.asarray(self.anchors,dtype=np.int64);self.normals=np.asarray(self.normals,dtype=np.float64);self.beta=np.asarray(self.beta,dtype=np.float64)
        if self.normals.shape!=(len(self.anchors),d) or self.beta.shape!=(len(self.anchors),):raise ValueError('hinge dimensions differ')
        if len(np.unique(self.anchors))!=len(self.anchors) or np.any(self.anchors<0) or np.any(self.anchors>=n):raise ValueError('at most one hinge per valid anchor is required')
        if not np.isfinite(self.normals).all() or not np.isfinite(self.beta).all() or np.any(np.abs(row_norm(self.normals)-1)>1e-10):raise ValueError('hinge gradients must be finite unit vectors')


class Problem:
    def __init__(self,H,W,gamma,*,kind='ssc',eta=.25,radius=None,hinges=None,mu=2.):
        self.H=np.asarray(H,dtype=np.float64)
        if self.H.ndim!=2 or not len(self.H) or not np.isfinite(self.H).all():raise ValueError('anchor must be a finite nonempty matrix')
        if kind not in ['ssc','relative','tangent','ball','relative_neighbor']:raise ValueError('unknown objective')
        if not np.isfinite(gamma) or gamma<0 or not 0<=eta<=1 or not np.isfinite(mu) or mu<0:raise ValueError('invalid objective parameters')
        self.B,self.i,self.j,self.w=graph_arrays(W)
        if self.B.shape[1]!=len(self.H):raise ValueError('graph/anchor dimensions differ')
        self.kind=kind;self.gamma=float(gamma);self.eta=float(eta);self.c=2*self.gamma*self.w;self.mu=float(mu)
        if not np.isfinite(self.c).all():raise ValueError('nonfinite edge capacity')
        self.anchor_edges=self.B@self.H;self.anchor_lengths=row_norm(self.anchor_edges)
        self.a=self.eta*self.anchor_lengths if kind=='relative' else np.zeros(len(self.w))
        self.active=np.any(self.H!=0,axis=1)
        self.radius=float(radius) if radius is not None else None
        if kind in ['tangent','ball'] and (self.radius is None or not np.isfinite(self.radius) or self.radius<0):raise ValueError('a finite nonnegative radius is required')
        if kind=='tangent' and np.any(np.abs(row_norm(self.H[self.active])-1)>1e-10):raise ValueError('tangent anchors must be unit rows or exact zeros')
        self.hinges=hinges if hinges is not None else Hinges.empty(self.H.shape[1]);self.hinges.validate(*self.H.shape)
        if kind!='relative_neighbor' and len(self.hinges.anchors):raise ValueError('hinges belong only to their independent objective')
        self.rootw=np.sqrt(self.w)
        degree=np.bincount(np.r_[self.i,self.j],weights=np.r_[self.rootw,self.rootw],minlength=len(self.H))
        if kind=='relative_neighbor':degree+=np.bincount(self.hinges.anchors,minlength=len(self.H))
        self.tau=np.divide(.99,degree,out=np.ones(len(self.H)),where=degree>0)
        # K=sqrt(w)B. In q=sqrt(w)y coordinates, w*Sigma=.99*sqrt(w)/2.
        self.q_step=.99*self.rootw/2
        self.p_step=.99
        h=hashlib.sha256()
        for array in [self.H,self.i,self.j,self.w,self.hinges.anchors,self.hinges.normals,self.hinges.beta]:
            array=np.ascontiguousarray(array);h.update(str((array.dtype.str,array.shape)).encode());h.update(array.tobytes())
        h.update(json.dumps({'kind':kind,'gamma':self.gamma,'eta':self.eta,'radius':self.radius,'mu':self.mu},sort_keys=True).encode());self.signature=h.hexdigest()

    def project_tangent(self,v):
        result=v-self.H*np.sum(self.H*v,axis=1)[:,None];result[~self.active]=0
        return result

    def feasibility(self,G):
        delta=G-self.H
        if self.kind=='tangent':
            return {'tangency_violation':float(np.max(np.abs(np.sum(self.H*delta,axis=1)),initial=0)),
                    'radius_violation':float(np.max(np.maximum(row_norm(delta)-self.radius,0),initial=0)),
                    'zero_row_violation':float(np.max(row_norm(delta[~self.active]),initial=0))}
        if self.kind=='ball':return {'radius_violation':float(np.max(np.maximum(row_norm(delta)-self.radius,0),initial=0))}
        return {}

    def primal(self,G):
        if not np.isfinite(G).all():return float('inf')
        if max(self.feasibility(G).values(),default=0)>1e-8:return float('inf')
        residual=row_norm(G-self.H);edges=row_norm(self.B@G)
        value=float(np.sum(residual)+self.c@np.maximum(edges-self.a,0))
        if self.kind=='relative_neighbor':value+=self.mu*float(np.maximum(self.hinges.apply(G)+self.hinges.beta,0).sum())
        return value

    def dual(self,q,p=None,*,repair=True):
        q=np.asarray(q,dtype=float).copy();p=np.zeros(len(self.hinges.anchors)) if p is None else np.asarray(p,dtype=float).copy()
        edge=row_norm(q);ratios=np.divide(self.c,edge,out=np.ones_like(edge),where=edge>0);scale=min(1.,float(np.min(ratios,initial=1.)))
        if len(p) and repair:
            if np.min(p)<-1e-12:raise ValueError('negative hinge dual')
            p=np.clip(p,0,self.mu)
        adj=self.B.T@q+self.hinges.adjoint(p,self.H.shape)
        if self.kind not in ['tangent','ball']:
            scale=min(scale,1/max(1.,float(np.max(row_norm(adj),initial=0))))
        if repair:
            scale=max(0.,scale)*(1-1e-12);q*=scale;p*=scale
        adj=self.B.T@q+self.hinges.adjoint(p,self.H.shape)
        value=float(np.sum(self.H*adj))
        if self.kind=='relative':value-=float(self.a@row_norm(q))
        if self.kind=='relative_neighbor':value+=float(self.hinges.beta@p)
        if self.kind=='tangent':value-=self.radius*float(np.maximum(row_norm(self.project_tangent(adj))[self.active]-1,0).sum())
        if self.kind=='ball':value-=self.radius*float(np.maximum(row_norm(adj)-1,0).sum())
        violations={'edge_capacity_violation':float(np.max(np.maximum(row_norm(q)-self.c,0),initial=0))}
        if self.kind not in ['tangent','ball']:violations['node_capacity_violation']=float(np.max(np.maximum(row_norm(adj)-1,0),initial=0))
        if len(p):violations['hinge_capacity_violation']=max(float(np.max(np.maximum(p-self.mu,0),initial=0)),float(np.max(np.maximum(-p,0),initial=0)))
        return {'dual':value,'q':q,'p':p,**violations}

    def prox(self,z):
        v=z-self.H
        if self.kind=='tangent':v=self.project_tangent(v)
        norms=row_norm(v);length=np.maximum(norms-self.tau,0)
        if self.kind in ['tangent','ball']:length=np.minimum(length,self.radius)
        return self.H+np.divide(length,norms,out=np.zeros_like(norms),where=norms>0)[:,None]*v

    def reference(self):
        directions=np.divide(self.anchor_edges,self.anchor_lengths[:,None],out=np.zeros_like(self.anchor_edges),where=self.anchor_lengths[:,None]>0)
        b=self.B.T@(2*self.w[:,None]*directions);M=float(np.max(row_norm(b),initial=0));ref=1/M if M>0 else None
        projected=float(np.max(row_norm(self.project_tangent(b))[self.active],initial=0)) if self.kind=='tangent' else None
        return {'M':M,'gamma_ref':ref,'primary_gamma':2*ref if ref is not None else 1.,
                'reference_status':'REGULAR' if M>0 else 'DEGENERATE_FORCE_REFERENCE','coincident_positive_edges':int(np.sum(self.anchor_lengths==0)),
                'exact_threshold_claim':bool(M>0 and np.all(self.anchor_lengths>0)),
                'gamma_tan_ref':1/projected if projected is not None and projected>0 else None,
                'projected_force_max':projected,'q_unit_gamma':2*self.w[:,None]*directions}


def solve(problem,*,max_iter=30000,cpu_limit=1800.,checkpoint=None,check_every=50,checkpoint_callback=None):
    """Continue one fixed convex problem; retain separate feasible best points."""
    started=time.process_time();wall=time.perf_counter();H=problem.H;n,d=H.shape;m=len(problem.w);t=len(problem.hinges.anchors)
    G=H.copy();Gbar=G.copy();average=G.copy();q=np.zeros((m,d));p=np.zeros(t);bestG=G.copy();best=problem.dual(q,p);P=problem.primal(G);D=best['dual'];iteration=0;history=[]
    if checkpoint is not None:
        if checkpoint['problem_signature']!=problem.signature:raise ValueError('checkpoint objective/input identity differs')
        G=np.array(checkpoint['G_last']);Gbar=np.array(checkpoint['G_bar']);average=np.array(checkpoint['average']);q=np.array(checkpoint['q_last']);p=np.array(checkpoint['p_last']);bestG=np.array(checkpoint['G_best']);iteration=int(checkpoint['iterations_total']);history=list(checkpoint.get('history',[]));best=problem.dual(checkpoint['q_best'],checkpoint['p_best']);P=problem.primal(bestG);D=best['dual']
    else:
        reference=problem.reference();candidate=problem.dual(problem.gamma*reference['q_unit_gamma']) if not (problem.kind=='relative' and problem.eta==1) else best
        if candidate['dual']>D:best=candidate;D=candidate['dual']
        if problem.kind=='relative_neighbor' and problem.gamma==0:
            values=np.maximum(problem.hinges.apply(H)+problem.hinges.beta,0);p=np.where(values>0,min(problem.mu,1.),0.)
            if problem.mu>1:G[problem.hinges.anchors]-=values[:,None]*problem.hinges.normals
            bestG=G.copy();P=problem.primal(G);best=problem.dual(q,p);D=best['dual']
    def summary(reason):
        nonlocal P,D
        independent=problem.dual(best['q'],best['p']);D=independent['dual'];P=problem.primal(bestG);absolute=P-D;gap=absolute/max(1.,abs(P),abs(D));feasibility=problem.feasibility(bestG);capacity={k:v for k,v in independent.items() if k.endswith('violation')}
        certified=bool(np.isfinite(P+D) and absolute>=0 and gap<=1e-5 and max([*feasibility.values(),*capacity.values()],default=0)<=1e-8)
        if absolute<0:reason='NEGATIVE_GAP_INCONSISTENCY'
        movement=float(row_norm(bestG-H).sum()/max(float(row_norm(H).sum()),1e-12))
        state={'problem_signature':problem.signature,'algorithm_version':'block-PDHG-v1','G_last':G,'G_bar':Gbar,'average':average,'q_last':q,'p_last':p,'G_best':bestG,'q_best':independent['q'],'p_best':independent['p'],'iterations_total':iteration,'history':history}
        return {'G':bestG,'q':independent['q'],'p':independent['p'],'primal':P,'dual':D,'absolute_gap':absolute,'relative_gap':gap,'certified':certified,'status':'COMPLETED_CERTIFIED' if certified else 'COMPLETED_UNCERTIFIED','stopping_reason':reason,'normalized_L21_movement':movement,'numerically_active':movement>1e-6,'iterations_total':iteration,'cpu_seconds_this_call':time.process_time()-started,'wall_seconds_this_call':time.perf_counter()-wall,'feasibility':feasibility,'dual_feasibility':capacity,'history':history,'checkpoint':state}
    def qualify():return np.isfinite(P+D) and 0<=P-D<=1e-5*max(1.,abs(P),abs(D))
    if qualify():return summary('INITIAL_FEASIBLE_CERTIFICATE')
    reason='ITERATION_LIMIT'
    while iteration<max_iter:
        if time.process_time()-started>=max(.01,cpu_limit-5):reason='CPU_LIMIT';break
        q+=problem.q_step[:,None]*(problem.B@Gbar)
        norms=row_norm(q)
        if problem.kind=='relative':q*=np.divide(np.maximum(norms-problem.q_step*problem.a,0),norms,out=np.zeros_like(norms),where=norms>0)[:,None];norms=row_norm(q)
        q*=np.minimum(1,np.divide(problem.c,norms,out=np.ones_like(norms),where=norms>0))[:,None]
        if t:p=np.clip(p+problem.p_step*(problem.hinges.apply(Gbar)+problem.hinges.beta),0,problem.mu)
        new=problem.prox(G-problem.tau[:,None]*(problem.B.T@q+problem.hinges.adjoint(p,H.shape)))
        Gbar=2*new-G;G=new;iteration+=1;average+=(G-average)/iteration
        if iteration%check_every==0 or iteration==max_iter:
            for point in [G,average]:
                value=problem.primal(point)
                if value<P:P=value;bestG=point.copy()
            candidate=problem.dual(q,p)
            if candidate['dual']>D:D=candidate['dual'];best=candidate
            gap=(P-D)/max(1.,abs(P),abs(D))
            history.append({'iteration':iteration,'primal':P,'dual':D,'relative_gap':gap,'CPU_this_call':time.process_time()-started})
            if P<D:reason='NEGATIVE_GAP_INCONSISTENCY';break
            if qualify():reason='GAP_TOLERANCE';break
            if checkpoint_callback is not None and iteration%500==0:checkpoint_callback(summary('CHECKPOINT'))
    return summary(reason)
