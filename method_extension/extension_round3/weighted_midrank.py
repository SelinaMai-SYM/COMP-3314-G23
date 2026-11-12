"""Mass-preserving midranks with deterministic, recorded near-tie grouping."""
from __future__ import annotations
import math
import numpy as np


def weighted_midrank(scores, masses):
    scores=np.asarray(scores,dtype=np.float64);masses=np.asarray(masses,dtype=np.float64)
    if scores.shape!=masses.shape or scores.ndim!=1 or not np.isfinite(scores).all() or not np.isfinite(masses).all() or np.any(scores<0) or np.any(masses<=0):
        raise ValueError('finite nonnegative scores and strictly positive masses required')
    positive=scores[scores>0];median=float(np.median(positive)) if len(positive) else 1.
    grouped=np.round(scores/median,10);u=np.empty_like(scores)
    total=math.fsum(masses.tolist());lower=0.;groups=[]
    for value in np.unique(grouped):
        mask=grouped==value;mass=math.fsum(masses[mask].tolist());rank=(lower+.5*mass)/total
        u[mask]=rank;groups.append({'value':float(value),'mass':mass,'count':int(mask.sum()),'rank':rank});lower=math.fsum([lower,mass])
    error=abs(math.fsum((masses*u).tolist())-.5*total)/max(total,np.finfo(float).tiny) if total else 0.
    if error>1e-12:raise ArithmeticError('weighted midrank budget failed')
    return u,{'positive_median':median,'decimals':10,'groups':groups,'mass':total,'relative_budget_error':error}
