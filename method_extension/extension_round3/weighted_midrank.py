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
    total=math.fsum(masses.tolist());lower=0.;groups=[];values=np.unique(grouped)
    for value in values:
        mask=grouped==value;mass=math.fsum(masses[mask].tolist());rank=.5 if len(values)==1 else (lower+.5*mass)/total
        u[mask]=rank;groups.append({'value':float(value),'mass':mass,'count':int(mask.sum()),'rank':rank});lower=math.fsum([lower,mass])
    error=abs(math.fsum((masses*u).tolist())-.5*total)/max(total,np.finfo(float).tiny) if total else 0.
    if error>1e-12:raise ArithmeticError('weighted midrank budget failed')
    return u,{'positive_median':median,'decimals':10,'groups':groups,'mass':total,'relative_budget_error':error}


def weighted_midrank_log(scores,log_masses):
    """The same midranks for positive products outside float64's mass range.

    Only the representation of sums changes. No edge is removed and objective
    weights are never rescaled. Unrepresentable raw masses retain their logs.
    """
    scores=np.asarray(scores,dtype=np.float64);logs=np.asarray(log_masses,dtype=np.float64)
    if scores.shape!=logs.shape or scores.ndim!=1 or not len(scores) or not np.isfinite(scores).all() or not np.isfinite(logs).all() or np.any(scores<0):raise ValueError('finite scores and finite logs of positive masses required')
    positive=scores[scores>0];median=float(np.median(positive)) if len(positive) else 1.;grouped=np.round(scores/median,10);values=np.unique(grouped);u=np.empty_like(scores)
    def lse(v):
        top=float(np.max(v));return top+math.log(math.fsum(np.exp(v-top).tolist()))
    total_log=lse(logs);lower_log=-np.inf;groups=[];maximum_correction=0.
    for value in values:
        mask=grouped==value;group_log=lse(logs[mask]);rank=.5 if len(values)==1 else float(np.exp(np.logaddexp(lower_log,group_log-math.log(2.))-total_log))
        raw_rank=rank
        if not 0<=raw_rank<=1+1e-12:raise ArithmeticError('material log-rank bound violation')
        rank=min(1.,raw_rank);maximum_correction=max(maximum_correction,abs(raw_rank-rank))
        u[mask]=rank;raw_mass=float(np.exp(group_log));groups.append({'value':float(value),'mass':raw_mass if raw_mass>0 else None,'log_mass':group_log,'count':int(mask.sum()),'rank':rank,'raw_rank':raw_rank});lower_log=float(np.logaddexp(lower_log,group_log))
    normalized=np.exp(logs-total_log);mass=math.fsum(normalized.tolist());error=abs(math.fsum((normalized*u).tolist())-.5*mass)/mass
    if error>1e-12 or np.any(u<0) or np.any(u>1+1e-12):raise ArithmeticError('log-domain weighted midrank identity failed')
    raw_total=float(np.exp(total_log));zeros=int(np.sum(normalized==0))
    return u,{'positive_median':median,'decimals':10,'groups':groups,'mass':raw_total if raw_total>0 else None,'log_mass':total_log,'relative_budget_error':error,'arithmetic':'float64 log-domain sums; original objective weights unchanged','raw_log_masses':logs,'maximum_rank_roundoff_correction':maximum_correction,'normalized_mass_underflows':zeros,'normalized_underflow_mass_upper_bound':float(zeros*np.nextafter(0.,1.))}
