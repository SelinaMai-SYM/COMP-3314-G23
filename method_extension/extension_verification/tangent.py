"""Fixed tangent-plane and isotropic-ball controls with distinct valid duals."""
import numpy as np
from .convex import Problem,solve

def solve_tangent(U,W,gamma,*,angle_degrees=15.,**options):
    return solve(Problem(U,W,gamma,kind='tangent',radius=np.tan(np.deg2rad(angle_degrees))),**options)

def solve_isotropic(U,W,gamma,*,angle_degrees=15.,**options):
    return solve(Problem(U,W,gamma,kind='ball',radius=np.sin(np.deg2rad(angle_degrees))),**options)
