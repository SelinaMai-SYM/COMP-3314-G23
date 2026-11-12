"""One frozen, degree-preserving finite-band graph intervention."""
from __future__ import annotations
import time
import numpy as np
from scipy import sparse,linalg
from scipy.sparse.linalg import LinearOperator,eigsh
from scipy.sparse.csgraph import connected_components
import osqp
from SSC_method.spectral_embedding import orient_eigenvector_signs
from method_extension.next_round.certified_solver import graph_arrays


def candidate_edges(H,W,k=20,block_size=128):
    n=len(H);squared=np.sum(H*H,axis=1);pairs=set(zip(*sparse.triu(W,k=1).nonzero()))
    for start in range(0,n,block_size):
        stop=min(n,start+block_size);d=squared[start:stop,None]+squared[None,:]-2*H[start:stop]@H.T;np.maximum(d,0,out=d)
        for local,i in enumerate(range(start,stop)):
            d[local,i]=np.inf;order=np.lexsort((np.arange(n),d[local]))[:min(k,n-1)]
            pairs.update((min(i,int(j)),max(i,int(j))) for j in order)
    degree=np.asarray(W.sum(axis=1)).ravel();pairs=sorted((i,j) for i,j in pairs if degree[i]>0 and degree[j]>0)
    return np.asarray(pairs,dtype=np.int64).reshape(-1,2)


def auxiliary_band(L,U0,K,seed=20261108):
    n=len(U0);gram=float(linalg.norm(U0.T@U0-np.eye(K)));LU=L@U0;ritz=sym(U0.T@LU);residual=float(linalg.norm(LU-U0@ritz))
    shifted=LinearOperator((n,n),matvec=lambda x:L@x+4*U0@(U0.T@x),matmat=lambda x:L@x+4*U0@(U0.T@x),dtype=float)
    # One extra omitted eigenpair exposes the upper finite-band cutoff gap.
    count=min(K+1,n-K-1)
    values,Z=eigsh(shifted,k=count,which='SA',v0=np.random.default_rng(seed).standard_normal(n),tol=0.,maxiter=max(10000,10*n))
    order=np.argsort(values);values=values[order];Z=orient_eigenvector_signs(Z[:,order]);aux=Z[:,:K]
    eigenvalues=np.sum(aux*(L@aux),axis=0);eigen_res=normcolumns(L@aux-aux*eigenvalues)
    original_top=float(linalg.eigvalsh(ritz)[-1]);lower=float(eigenvalues.min()-original_top);upper=float(values[K]-values[K-1]) if len(values)>K else None
    diagnostics={'U0_orthogonality_residual':gram,'U0_invariant_subspace_residual':residual,'cross_orthogonality_residual':float(linalg.norm(U0.T@aux)),'aux_orthogonality_residual':float(linalg.norm(aux.T@aux-np.eye(K))),'original_L_eigenvalues':eigenvalues.tolist(),'eigen_residuals':eigen_res.tolist(),'lower_cutoff_gap':lower,'upper_cutoff_gap':upper,'cutoff_ambiguity':bool(lower<1e-8 or upper is not None and upper<1e-8),'which':'SA','shift':4,'seed':seed,'qualified':bool(gram<=1e-7 and residual<=1e-7 and linalg.norm(U0.T@aux)<=1e-7 and linalg.norm(aux.T@aux-np.eye(K))<=1e-7 and eigen_res.max(initial=0)<=1e-7)}
    return aux,diagnostics


def sym(x):return (x+x.T)*.5
def normcolumns(x):return np.linalg.norm(x,axis=0)


def costs(Z,edges):
    raw=np.sum((Z[edges[:,0]]-Z[edges[:,1]])**2,axis=1);positive=raw[raw>0]
    median=float(np.median(positive)) if len(positive) else None
    return (raw/median if median is not None else np.zeros_like(raw)),{'positive_median':median,'degenerate':median is None}


class GraphRepair:
    def __init__(self,H,W,Z,*,edges=None,fixed=None,warm=None):
        self.H=H;self.W=sparse.csr_matrix(W);self.edges=candidate_edges(H,W) if edges is None else np.asarray(edges,dtype=np.int64);self.n=len(H)
        self.w0=np.asarray(self.W[self.edges[:,0],self.edges[:,1]]).ravel();self.mass=float(self.w0.sum())
        if fixed is None:
            self.a,self.a_info=costs(H,self.edges);self.r=np.maximum(np.exp(-self.a),1e-6);self.r*=self.mass/self.r.sum() if self.mass else 0.
        else:self.a=fixed['a'];self.a_info=fixed['a_info'];self.r=fixed['r']
        m=len(self.edges);self.M=sparse.csc_matrix((np.ones(2*m),(self.edges.T.ravel(),np.tile(np.arange(m),2))),shape=(self.n,m));self.d=np.asarray(self.M@self.w0);self.C=1.05*float(self.a@self.w0);self.Z=Z;self.engine=None;self.last=None;self.initial_warm=warm
        if fixed is not None and (not np.array_equal(self.d,fixed['d']) or self.C!=fixed['C']):raise ValueError('fixed constraints differ')

    def fit(self,*,beta=1.,mix=.25,permutation_seed=None,cpu_limit=570.):
        started=time.process_time();Z=self.Z if permutation_seed is None else self.Z[np.random.RandomState(permutation_seed).permutation(self.n)]
        b,b_info=costs(Z,self.edges)
        if self.mass==0 or beta==0:
            return self.W.copy(),{'status':'DEGENERATE_ZERO_GRAPH' if self.mass==0 else 'EXACT_BETA_ZERO_IDENTITY','eligible':True,'beta':beta,'permutation_seed':permutation_seed,'CPU_seconds':time.process_time()-started}, {'t':self.w0.copy(),'b':b}
        q=beta*b-self.w0/self.r
        if self.engine is None:
            self.engine=osqp.OSQP();matrix=sparse.vstack([self.M,sparse.csc_matrix(self.a[None,:]),sparse.eye(len(q),format='csc')],format='csc')
            self.engine.setup(P=sparse.diags(1/self.r,format='csc'),q=q,A=matrix,l=np.r_[self.d,-np.inf,np.zeros(len(q))],u=np.r_[self.d,self.C,np.full(len(q),np.inf)],eps_abs=1e-9,eps_rel=1e-9,max_iter=200000,polishing=True,verbose=False,time_limit=max(1.,cpu_limit))
            if self.initial_warm is not None:self.engine.warm_start(x=self.initial_warm['raw_t'],y=self.initial_warm['QP_y'])
        else:self.engine.update(q=q);self.engine.update_settings(time_limit=max(1.,cpu_limit))
        result=self.engine.solve(raise_error=False);raw=np.asarray(result.x) if result.x is not None else self.w0.copy()
        # Tiny negative roundoff is explicitly projected and all constraints
        # are rechecked. No degree/row normalization or hidden mass restoration.
        candidate=np.maximum(raw,0.);clip=float(np.max(np.abs(candidate-raw),initial=0));v=result.y[:self.n] if result.y is not None else np.zeros(self.n);theta=max(0.,float(result.y[self.n])) if result.y is not None else 0.
        c=beta*b+self.M.T@v+theta*self.a;s=np.maximum(self.w0-self.r*c,0.);active=self.w0-self.r*c>0
        terms=np.where(active,c*self.w0-.5*self.r*c*c,self.w0*self.w0/(2*self.r));dual=float(-v@self.d-theta*self.C+terms.sum())
        primal=.5*float(np.sum((candidate-self.w0)**2/self.r))+beta*float(b@candidate);safe=beta*float(b@self.w0)
        degree=float(np.max(np.abs(self.M@candidate-self.d),initial=0)/max(1.,self.d.max(initial=0)));budget=max(0.,float(self.a@candidate-self.C))/max(1.,self.C);gap=primal-dual;relative=max(0.,gap)/max(1.,abs(primal),abs(dual));tolerance=1e-10*max(1.,abs(primal),abs(dual))
        eligible=bool(result.info.status_val==1 and degree<=1e-8 and budget<=1e-8 and relative<=1e-6 and gap>=-tolerance and np.isfinite(primal+dual))
        t=candidate if eligible else self.w0.copy();weights=.75*self.w0+.25*t
        W=sparse.csr_matrix((np.r_[weights,weights],(np.r_[self.edges[:,0],self.edges[:,1]],np.r_[self.edges[:,1],self.edges[:,0]])),shape=self.W.shape);W.eliminate_zeros()
        _,old_i,old_j,oldw=graph_arrays(self.W);new_old=np.asarray(W[old_i,old_j]).ravel()
        diagnostics={'status':'NUMERICALLY_CERTIFIED' if eligible else 'QP_FAILED_W0_FALLBACK','eligible':eligible,'solver_status':result.info.status,'iterations':int(result.info.iter),'polish_status':int(result.info.status_polish),'beta':float(beta),'mix':mix,'permutation_seed':permutation_seed,'primal':primal,'dual':dual,'signed_gap':gap,'relative_gap':relative,'safe_W0_upper_bound':safe,'primal_qualification':'Numerically feasible under recorded residual tolerances; not an interval-arithmetic exact upper bound','solver_objective_without_constant':float(result.info.obj_val),'QP_constant':.5*float(np.sum(self.w0**2/self.r)),'degree_residual':degree,'budget_residual':budget,'nonnegative_projection_max_change':clip,'negative_weight_count_after_projection':int(np.sum(candidate<0)),'a_info':self.a_info,'b_info':b_info,'conditioning_ratio':float(self.r.max()/self.r.min()),'exchange_mass':float(np.maximum(t-self.w0,0).sum()/self.mass),'graph_L1_relative_change':float(np.sum(np.abs(weights-self.w0))/self.mass),'old_edge_floor_min':float(np.min(new_old/oldw,initial=1.)),'old_a_cost':float(self.a@self.w0),'new_a_cost':float(self.a@weights),'a_cost_bound':1.0125*float(self.a@self.w0),'old_b_cost':float(b@self.w0),'new_b_cost':float(b@weights),'new_degree_error':float(np.max(np.abs(np.asarray(W.sum(axis=1)).ravel()-self.d),initial=0)),'old_components':int(connected_components(self.W,directed=False,return_labels=False)),'new_components':int(connected_components(W,directed=False,return_labels=False)),'CPU_seconds':time.process_time()-started}
        return W,diagnostics,{'t':t,'raw_t':raw,'QP_y':result.y,'w0':self.w0,'a':self.a,'b':b,'r':self.r,'v':v,'theta':theta,'edges':self.edges}
