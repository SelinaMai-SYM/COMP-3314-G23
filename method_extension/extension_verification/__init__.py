"""Three independent convex adaptations of Spectral Shrunk Clustering."""
from .relative_stopping import solve_relative
from .tangent import solve_tangent, solve_isotropic
from .relative_neighbor import solve_relative_neighbors
__all__=['solve_relative','solve_tangent','solve_isotropic','solve_relative_neighbors']
