# X1 certified shrinkage path

Ordered-pair objective with unit fidelity:

    J(G) = sum_i ||g_i - f_i||_2 + gamma * sum_{ij} W_ij ||g_i - g_j||_2

`W` is symmetric and stores both triangles. For a noncoincident edge the contribution to the graph subgradient at `i` is `2 W_ij u_ij`, with `u_ij = (f_i - f_j) / ||f_i - f_j||`. Define

    q_i = sum_j W_ij (f_i - f_j) / ||f_i - f_j||

over those noncoincident pairs, counting each undirected edge once. `G = F` is optimal when

    2 * gamma * max_i ||q_i||_2 <= 1.

Hence `gamma_0 = 1 / (2 max_i ||q_i||)` when the maximum is positive. Coincident edges are not divided by zero. Their subgradient is a Euclidean ball, and the largest feasible gamma is found by a second-order-cone bisection when the graph is small.

The factor `2` is the ordered-pair count. It was checked on a synthetic path against CVXPY before any real clustering was trusted. ADMM is the standard convex-clustering splitting (Chi and Lange). It is an independent solver here, not a new algorithm.

Above `gamma_0`, IRLS uses the frozen E8 linear system. A small step of `G` is not marked `OPTIMALITY_VERIFIED`. That label requires the exact objectives of IRLS and the independent solver to agree closely, or the certified `G = F` region to be confirmed by the IRLS objective staying at `J(F)`.
