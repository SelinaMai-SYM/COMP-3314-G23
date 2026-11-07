# X5 adaptive robust fidelity

On the fixed shrinkage graph,

    u_i = median_{j in N(i)} ||f_i - f_j||_2
    u_tilde_i = u_i / max(median_i u_i, epsilon)
    a_i = clip( 1 / (epsilon + u_tilde_i)^alpha , 0.25, 4 )
    epsilon = 0.05
    alpha in {0, 0.5, 1, 2}

`a` is then rescaled so its mean is 1. `alpha = 0` makes every unclipped weight 1, so `a = 1` and the objective is original SSC.

    J(G) = sum_i a_i ||g_i - f_i||_2 + gamma * sum_ij W_ij ||g_i - g_j||_2

`a` and `W` are fixed before `G` moves, so `J` is convex in `G`. The IRLS weight is re-derived as `S_ii = a_i / (2 max(||g_i - f_i||, floor))` with the ordered-pair factor `c = 2`. The original unit-fidelity update is not reused for `alpha > 0`.

Controls: `alpha = 0`, a uniform fidelity of 2 (a global scale, not renormalized to mean 1), a permutation of `a`, and the inverse weight proportional to `(epsilon + u_tilde)^alpha` with the same clip and mean-1 rescaling. Correlation between movement and label error is post-hoc and does not choose `alpha`.
