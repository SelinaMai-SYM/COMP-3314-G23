"""Pinned EnSC objective with a true elastic-net coordinate-descent backend.

The active-support loop and affinity convention adapt Chong You's MIT-licensed
implementation at 55e330e38415951f140e74739c869306acdb7a98. See the retained
third_party/ensc/LICENSE and docs/submission_refresh/ensc_source_audit.md.
This module implements no labels, tuning rule, G3 gate or new experiment grid.
"""
from __future__ import annotations
import warnings
import numpy as np
from scipy import sparse
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet

SOURCE_REVISION='55e330e38415951f140e74739c869306acdb7a98'


def elastic_net_objective(c, dictionary, target, alpha, tau):
    residual=np.asarray(target).reshape(-1)-np.asarray(c)@dictionary
    return float(.5*(residual@residual)+alpha*(tau*np.abs(c).sum()+.5*(1-tau)*(c@c)))


def elastic_net_kkt(c, dictionary, target, alpha, tau):
    """Maximum absolute coordinate subgradient residual in original units."""
    c=np.asarray(c)
    gradient=dictionary@(c@dictionary-np.asarray(target).reshape(-1))+alpha*(1-tau)*c
    active=c!=0
    error=np.maximum(np.abs(gradient)-alpha*tau,0)
    error[active]=np.abs(gradient[active]+alpha*tau*np.sign(c[active]))
    return float(error.max(initial=0))


def _solve_working_set(dictionary, target, alpha, tau, *, max_iter=10000, tol=1e-10):
    """sklearn divides squared error by d, so alpha must be alpha_i/d."""
    d=dictionary.shape[1]
    if d<1:
        raise ValueError('empty feature dimension')
    estimator=ElasticNet(alpha=alpha/d,l1_ratio=tau,fit_intercept=False,
                         max_iter=max_iter,tol=tol,selection='cyclic')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        estimator.fit(dictionary.T,np.asarray(target).reshape(-1))
    return estimator.coef_.copy(),{'inner_iterations':int(estimator.n_iter_),
        'sklearn_dual_gap':float(estimator.dual_gap_),
        'convergence_warnings':[str(w.message) for w in caught]}


def elastic_net_code(dictionary, target, alpha, tau=.95, *, active_support=True,
                     support_size=100, max_outer=40, max_inner=10000, tol=1e-10):
    """Solve .5||y-cD||² + alpha[tau||c||1 +(1-tau)||c||²/2].

    The source uses the same residual/alpha screening condition. Changes are a
    true sklearn elastic-net backend, stable index ties and explicit statuses.
    At an iteration cap, diagnostics retain the actual measured KKT residual;
    an active-support stop is not asserted to be an exact optimum.
    """
    D=np.asarray(dictionary,dtype=np.float64);y=np.asarray(target,dtype=np.float64).reshape(-1)
    if D.ndim!=2 or D.shape[1]!=len(y) or not np.isfinite(D).all() or not np.isfinite(y).all():
        raise ValueError('invalid dictionary/target')
    if not np.isfinite(alpha) or alpha<0 or not 0<tau<=1:
        raise ValueError('alpha must be nonnegative and tau in (0,1]')
    if support_size<1 or max_outer<1:
        raise ValueError('invalid active-support limits')
    n=len(D);c=np.zeros(n);history=[];all_indices=np.arange(n)
    if n==0:
        return c,{'status':'EMPTY_DICTIONARY','kkt_residual':0.,'history':[],'outer_iterations':0}
    if alpha==0:
        if np.max(np.abs(D@y),initial=0)>1e-12:
            raise ValueError('zero alpha with nonorthogonal dictionary is not a declared EnSC case')
        return c,{'status':'ORTHOGONAL_ZERO_CODE','kkt_residual':elastic_net_kkt(c,D,y,alpha,tau),'history':[],'outer_iterations':0}
    size=min(int(support_size),n)
    support=(np.lexsort((all_indices,-np.abs(D@y)))[:size] if active_support else all_indices)
    previous=float('inf');reason='ACTIVE_SUPPORT_MAX_ITER'
    for outer in range(int(max_outer) if active_support else 1):
        values,diagnostics=_solve_working_set(D[support],y,alpha,tau,max_iter=max_inner,tol=tol)
        c[:]=0;c[support]=values
        objective=elastic_net_objective(c,D,y,alpha,tau)
        kkt=elastic_net_kkt(c,D,y,alpha,tau)
        history.append({'outer_iteration':outer+1,'support_size':len(support),'objective':objective,'kkt_residual':kkt,**diagnostics})
        if not active_support:
            reason='FULL_DICTIONARY_SOLVED';break
        # This reproduces the source's scaled-objective stopping criterion.
        if np.isfinite(previous) and previous-objective<1e-10*previous:
            reason='SOURCE_OBJECTIVE_STOP';break
        previous=objective
        residual=(y-c@D)/alpha
        coherence=np.abs(D@residual);coherence[support]=0
        additions=np.flatnonzero(coherence>tau+1e-10)
        if len(additions)==0:
            reason='SCREENING_CONVERGED';break
        retained=support[np.abs(values)>1e-10]
        if len(retained)>.8*size:
            size=min(round(max(len(retained),size)*1.1),n)
        slots=max(0,size-len(retained))
        if len(additions)>slots:
            additions=additions[np.lexsort((additions,-coherence[additions]))[:slots]]
        support=np.r_[retained,additions]
    measured=elastic_net_kkt(c,D,y,alpha,tau)
    return c,{'status':reason,'kkt_residual':measured,'kkt_qualified':measured<=1e-7,
              'outer_iterations':len(history),'history':history,
              'objective':elastic_net_objective(c,D,y,alpha,tau),
              'backend':'sklearn.ElasticNet(alpha=alpha_i/d,l1_ratio=tau,fit_intercept=False)',
              'tau_used':float(tau),'alpha_original':float(alpha)}


def coefficients_to_affinity(coefficients, n_nonzero=50):
    """Top-|c| truncation, row-L2 normalization, then .5(|Cn|+|Cn|T)."""
    C=sparse.csr_matrix(coefficients,dtype=np.float64).copy();C.setdiag(0);C.eliminate_zeros()
    if C.shape[0]!=C.shape[1] or not np.isfinite(C.data).all() or n_nonzero<1:
        raise ValueError('invalid coefficient matrix/truncation')
    pre=C.copy()
    for i in range(len(C.indptr)-1):
        a,b=C.indptr[i:i+2]
        if b-a>n_nonzero:
            keep=np.lexsort((C.indices[a:b],-np.abs(C.data[a:b])))[:n_nonzero]
            mask=np.ones(b-a,dtype=bool);mask[keep]=False;C.data[a:b][mask]=0
    C.eliminate_zeros()
    norms=np.sqrt(np.asarray(C.multiply(C).sum(axis=1)).ravel())
    scale=np.divide(1.,norms,out=np.zeros_like(norms),where=norms>0)
    Cn=sparse.diags(scale)@C
    S=.5*(abs(Cn)+abs(Cn.T));S.setdiag(0);S.eliminate_zeros()
    return {'C_pre_truncation':pre,'C':C,'Cn':Cn.tocsr(),'S':S.tocsr(),
            'zero_coefficient_rows':np.flatnonzero(norms==0).tolist(),
            'degenerate_affinity':bool(S.nnz==0),
            'n_nonzero':int(n_nonzero),'row_normalization':'L2 with zero rows retained'}


def ensc_affinity(X,tau=.95,source_gamma=50.,n_nonzero=50,*,active_support=True,support_size=100,max_outer=40):
    """Label-free fixed source convention; unit-L2 input rows, self-code zero."""
    X=np.asarray(X,dtype=np.float64)
    if X.ndim!=2 or not np.isfinite(X).all() or len(X)<2 or source_gamma<=0 or not 0<tau<=1:
        raise ValueError('invalid EnSC input/parameters')
    norms=np.linalg.norm(X,axis=1,keepdims=True)
    unit=np.divide(X,norms,out=np.zeros_like(X),where=norms>0)
    rows=[];columns=[];values=[];diagnostics=[];alphas=[]
    for i in range(len(unit)):
        ids=np.delete(np.arange(len(unit)),i);D=unit[ids];target=unit[i]
        alpha=float(np.max(np.abs(D@target),initial=0)/(source_gamma*tau));alphas.append(alpha)
        c,diag=elastic_net_code(D,target,alpha,tau,active_support=active_support,support_size=support_size,max_outer=max_outer)
        nz=np.flatnonzero(c);rows.extend([i]*len(nz));columns.extend(ids[nz]);values.extend(c[nz]);diagnostics.append(diag)
    matrix=sparse.csr_matrix((values,(rows,columns)),shape=(len(unit),len(unit)))
    return {**coefficients_to_affinity(matrix,n_nonzero), 'unit_input':unit,'input_zero_rows':np.flatnonzero(norms.ravel()==0).tolist(),
            'alpha_i':np.asarray(alphas),'diagnostics':diagnostics,'source_revision':SOURCE_REVISION,
            'tau':float(tau),'source_gamma':float(source_gamma),
            'status':'IMPLEMENTATION_OUTPUT_REQUIRES_G3_GATE_AND_BACKEND_VALIDATION'}
