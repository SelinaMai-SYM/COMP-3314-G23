"""Redistribute stopping distances while retaining a one-eighth dispersion floor."""
import numpy as np
from .weighted_midrank import weighted_midrank,weighted_midrank_log


def tube_distances(w,anchor_lengths,scores,*,uniform_eta=None):
    eta=np.full(len(w),.25);active=anchor_lengths>0;meta={'groups':[]};u=np.full(len(w),.5)
    if uniform_eta is not None:eta[:]=uniform_eta
    elif active.any():
        masses=(w*anchor_lengths)[active]
        if np.any(masses==0):u[active],meta=weighted_midrank_log(scores[active],np.log(w[active])+np.log(anchor_lengths[active]))
        else:u[active],meta=weighted_midrank(scores[active],masses)
        eta[active]=.125+.25*u[active]
    a=eta*anchor_lengths;budget=float(w@a);target=float((.25 if uniform_eta is None else uniform_eta)*(w@anchor_lengths))
    if abs(budget-target)>1e-12*max(1.,abs(target)):raise ArithmeticError('tube budget failed')
    return a,{'eta':eta,'ranks':u,'grouping':meta,'budget':budget,'target_budget':target,'zero_anchor_edges':int((~active).sum())}


def dispersion_lower_bound(scale,gap):return max(0.,scale-np.sqrt((7*scale/8)**2+2*max(0.,gap)))
