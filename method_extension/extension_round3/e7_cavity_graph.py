"""Redistribute ten percent of edge mass without changing graph support."""
import numpy as np
from .weighted_midrank import weighted_midrank


def graph_weights(w,scores):
    u,metadata=weighted_midrank(scores,w) if len(w) else (np.empty(0),{'groups':[]})
    result=w*(1-.2*u)
    if len(w) and abs(result.sum()/.9/w.sum()-1)>1e-12:raise ArithmeticError('graph mass identity failed')
    return result,{'ranks':u,'grouping':metadata,'retained_mass_fraction':float(result.sum()/w.sum()) if len(w) else 1.,'minimum_weight_fraction':float(np.min(result/w)) if len(w) else 1.}
