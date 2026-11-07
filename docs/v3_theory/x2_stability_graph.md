# X2 stability-weighted graph

Ten label-free perturbations are fixed in advance. Images use small brightness and contrast changes. A non-image matrix, if used, gets feature noise scaled by a coordinate-wise median absolute deviation.

`s_ij` is the fraction of those ten graphs that contain undirected edge `(i, j)`. The original shrinkage weight is reweighted and then put back on its original total mass:

    W_stable,ij = W_ij * (epsilon + s_ij)^beta
    epsilon = 0.05
    beta in {0, 0.5, 1, 2}

`beta = 0` leaves every multiplier at 1, so `W_stable = W`. The objective is the original ordered-pair objective on this fixed nonnegative matrix, so it stays convex for the same reason SSC does. No new convexity claim is made.

Controls, also fixed: uniform scale 2 (a global gamma rescaling), stability scores permuted on the same support, and a degree-matched random graph with the same total mass. Held-out perturbations are a separate list and are not used to choose `beta`. A stable edge is not a same-class edge.
