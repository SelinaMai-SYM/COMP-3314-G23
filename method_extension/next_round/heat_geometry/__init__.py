"""Full-spectrum heat action, not a truncated eigenvector embedding."""
import numpy as np
from scipy.sparse.linalg import expm_multiply


def project_heat(L,t=4.,r=128,seed=20261108,R=None):
    if t<0 or r<1:raise ValueError('invalid heat parameters')
    R=np.random.default_rng(seed).normal(0,1/np.sqrt(r),(L.shape[0],r)) if R is None else R
    return expm_multiply(-t/2*L,R),R
