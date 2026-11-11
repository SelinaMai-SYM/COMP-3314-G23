"""Frozen relative edge tolerances; an edge's own attraction stops inside its tube."""
from .convex import Problem,solve

def solve_relative(H,W,gamma,*,eta=.25,**options):
    return solve(Problem(H,W,gamma,kind='relative',eta=eta),**options)
