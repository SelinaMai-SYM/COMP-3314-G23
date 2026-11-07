# X4 multi-scale consensus

Neighborhood sizes are fixed at `{3, 5, 10, 15}`. Each graph is normalized to the same total mass. The combination is

    W_multi = sum_l alpha_l W^(k_l)
    alpha_l = 1/4

The alphas are not fit to labels. `F` stays the frozen `k = 5` embedding. The ordered-pair objective is then the usual one on this fixed nonnegative `W_multi`. Convexity is the same fact as for any fixed nonnegative affinity. No new convexity theorem is claimed.

Controls are each single `k` after the same mass normalization, a mass-matched random graph, and an edge-budget-matched random graph. Rebuilding `F` with a different `k` is stored as `X4_refit_F` and is not mixed into the primary contrast.

Prespecified failure hypothesis: larger neighborhoods add edges that need not respect identity. That hypothesis is not tested by maximizing accuracy.
