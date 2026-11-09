# N1 radial Huber candidate: properties and limits

N1 is subordinate to the performance diagnosis, as agreed on 2026-11-09. The shared solver implements it; it is not presumed to improve ACC.

For delta>0, phi_delta(r)=r^2/(2delta) for r<=delta and r-delta/2 otherwise. It is convex and nondecreasing on r>=0, so composition with row Euclidean norms is convex. Fixed nonnegative graph TV remains convex.

If TV(F)>0, let G(t)=(1-t)F+t 1m^T. The graph term decreases linearly in t while the fidelity near zero increases quadratically. Thus F cannot minimize a positive-gamma Huber objective. This proves activation, not label improvement; existing gamma=1 SSC already moves.

For Q^TQ=I, all radial residual and edge norms are unchanged by (G,F)->(GQ,FQ). The solution set is equivariant; uniqueness is not implied. Coordinatewise Huber lacks this general invariance.

Since 0<=r-phi_delta(r)<=delta/2, an exact Huber minimizer satisfies P0(G_delta)-min P0<=n delta/2 when a_i=1. A computed point adds its certified absolute optimality gap. This is not a classification-error bound.

The radial fidelity gradient has norm<=1. This bounded influence statement does not transfer a 50% breakdown theorem from another estimator/graph to sparse spectral SSC. Sun et al. (EJS 2025) use coordinatewise Huber; our radial adaptation differs.

Parameters and sensitivities remain as locked in configs/next_round/protocol.yaml and the original user specification. A squared control uses its own node-unconstrained dual. Real-data method claims require certified paired outputs, and all-quadratic residuals cannot demonstrate a robust-tail benefit.
