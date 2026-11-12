"""Redistribute guard coefficient mass; graph and anchor remain frozen."""
import numpy as np
from .weighted_midrank import weighted_midrank


def guard_coefficients(w,scores,*,uniform=False):
    u,meta=weighted_midrank(scores,w) if len(w) else (np.empty(0),{'groups':[]})
    alpha=np.ones(len(w)) if uniform else 2*u
    if abs(float(w@alpha)-float(w.sum()))>1e-12*max(1.,float(w.sum())):raise ArithmeticError('guard coefficient budget failed')
    return alpha,{'ranks':u,'grouping':meta,'coefficient_mass':float(w@alpha),'original_mass':float(w.sum())}
