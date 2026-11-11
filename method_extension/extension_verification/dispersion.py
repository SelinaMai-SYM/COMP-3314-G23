"""Geometric-median upper/lower bounds, including nonsmooth data coincidences."""
import numpy as np
from .convex import row_norm

def geometric_median_bounds(X,*,relative_tolerance=1e-9,max_iter=5000):
    X=np.asarray(X,dtype=float)
    if X.ndim!=2 or len(X)==0 or not np.isfinite(X).all():raise ValueError('finite nonempty rows required')
    center=X.mean(axis=0);radius=float(np.max(row_norm(X-center),initial=0));z=center.copy();best_upper=float('inf');best_lower=0.;best_z=z.copy()
    for iteration in range(max_iter+1):
        displacement=X-z;r=row_norm(displacement);positive=r>0;zero=int(np.sum(~positive));unit=np.divide(displacement,r[:,None],out=np.zeros_like(X),where=positive[:,None]);force=unit.sum(axis=0);length=float(row_norm(force[None])[0])
        if zero and length<=zero:unit[~positive]=-force/zero
        # For any row-ball feasible v and an optimal median in conv(X),
        # sum v_i.(x_i-c) - R*||sum v_i|| is a valid lower bound. The
        # residual penalty accounts for an inexact zero-sum condition.
        unit*=min(1.,1/max(1.,float(np.max(row_norm(unit),initial=0))))*(1-1e-13)
        support=np.sum(unit.astype(np.longdouble)*(X-center).astype(np.longdouble),dtype=np.longdouble)
        residual=float(row_norm(unit.sum(axis=0)[None])[0]);lower=float(support)-radius*residual
        upper=float(r.sum());roundoff=32*np.finfo(float).eps*max(1.,upper,len(X)*radius)
        best_lower=max(best_lower,lower-roundoff)
        if upper<best_upper:best_upper=upper;best_z=z.copy()
        if best_upper-best_lower<=relative_tolerance*max(1.,best_upper):break
        if not np.any(positive):break
        weights=1/r[positive];target=np.sum(weights[:,None]*X[positive],axis=0)/weights.sum()
        if zero:
            fraction=min(1.,zero/max(length,np.finfo(float).tiny));target=(1-fraction)*target+fraction*z
        z=target
    return {'lower':best_lower,'upper':best_upper,'center':best_z,'iterations':iteration,'certified_interval':bool(best_upper-best_lower<=relative_tolerance*max(1.,best_upper)),'bound_method':'convex-hull ball support lower bound with zero-sum residual penalty'}

def dispersion_check(H,G,eta,absolute_gap):
    anchor=geometric_median_bounds(H);output=geometric_median_bounds(G)
    lower_margin=output['lower']-eta*anchor['upper']+absolute_gap
    upper_margin=output['upper']-eta*anchor['lower']+absolute_gap
    return {'anchor':anchor,'output':output,'absolute_optimality_gap':absolute_gap,'verified_lower_margin':lower_margin,'possible_upper_margin':upper_margin,'status':'VERIFIED_BOUND' if lower_margin>=0 else 'INCONSISTENT_BOUND' if upper_margin<0 else 'INTERVAL_UNRESOLVED','scope':'Global dispersion of optimized G, not edge/class separation or normalized Q'}
