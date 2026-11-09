"""Radial Huber is supported by the shared convex solver with delta > 0.

Use fidelity='radial'. For the quadratic control use fidelity='squared';
its dual deliberately has no node-ball constraint.
"""
from ..certified_solver import solve
