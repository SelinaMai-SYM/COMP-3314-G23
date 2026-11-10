"""PDHG and feasible-dual certificates for fixed-graph SSC.

From-scratch implementation based on Chambolle & Pock (2011).
The certificate bounds the specified convex objective, not clustering error.
"""
from .solver import solve, graph_arrays, objective, certificate, threshold
__all__ = ['solve','graph_arrays','objective','certificate','threshold','component_dual_flow']

from .flow import component_dual_flow
