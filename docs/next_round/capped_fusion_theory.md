# Capped fusion: an SSC adaptation of an existing penalty

The group-truncated penalty is prior work (PRclust); robust treatment of spurious graph edges is also central to Shah-Koltun RCC. The contribution studied here is an SSC-specific failure mechanism and controlled adaptation, not a new penalty family.

## Two group-constant representatives

Assume fixed graph/weights, m<n anchors at a,b, d=||a-b||, and total cross-group attraction lambda. Within each group the representative is constrained to be common. For r=||u-v||, triangle inequality gives fidelity >=m max(d-r,0). For 0<=r<=d the bound is attained by v=b and u on the segment from a to b at distance r from b. Distances r>d cannot improve an endpoint solution.

The original reduced cost is m(d-r)+lambda*r, so its minimum is d*min(m,lambda). For d>tau, capped cost is m(d-r)+lambda*min(r,tau). Its minimum is min(md,lambda*tau): the intermediate kink at r=tau cannot improve these endpoints. Thus m<lambda<md/tau makes the original prefer fusion while capping preserves the separated anchors. Equality can yield multiple optima and is not a strict separation guarantee.

The distance-independent original fusion threshold is a statement about this fixed-weight reduced model. If W is rebuilt as separation d changes, lambda may also change. This is not a theorem about every data-dependent SSC graph or ACC.

## Five-point check and initialization

The actual five-point check uses F=(0,0,4,4,4), within-group edge weights 10 and six cross edges of weight .25 at gamma=1. Total cross attraction is 3; tau=1. There are 1024 edge states. A known feasible capped upper bound of 3 prunes states whose nonnegative inactive-edge constant already exceeds it; 64 remaining convex states are solved and independently checked using feasible-dual bounds. This gives capped primal=dual=3, while original primal/dual are approximately 8.

The local active-edge method starts at F or the original SSC output. The latter is fused and remains at the local value approximately 8 (ACC 60%, NMI 0); the F start remains separated at value 3 (ACC/NMI 100%). Selecting the lower same-objective value uses no labels. The global certificate here comes from exhaustive finite-state reference calculations, not the local algorithm, and applies only to this tiny graph.

Full numeric evidence is `results/next_round/five_point_global_check.json`. Synthetic class/bridge design is an Oracle-designed intervention, not an admissible real-data fitting step. Since SC already separates these anchors perfectly, this check establishes damage avoidance, not net gain beyond SC.

## Optimization contract

min(r,tau)=min_{z in {0,1}} z*r+(1-z)*tau. Thresholding edges at each current r fixes z; optimizing G is then a convex SSC subproblem plus a constant. The original point is an admissible primal upper bound for that subproblem, so retaining the best actual primal and rejecting increases protects monotonicity. A fixed active set plus an inner certificate is a local block fixed point, not a general global or label-quality certificate. All inner failures, truncations and initialization differences remain visible.

## Squared fidelity coefficient mapping

The crossed squared control is sum_i ||g_i-f_i||²/(2*s_F) + 2*gamma*sum_e w_e*r_e, with each undirected edge once. Multiplying by 2*s_F gives sum_i ||g_i-f_i||² + 4*s_F*gamma*sum_e w_e*r_e. Thus under Equation 7's ordered-pair graph sum, gamma_E7 = 2*s_F*gamma. Multiplication does not change minimizers. This mapping does not make equal numerical gamma values across squared and non-squared fidelity comparable; the formal design allocates separate searches. For the N1 curvature control whose quadratic scale is delta, the corresponding mapping uses 2*delta*gamma instead. The capped version retains the same scaling with r replaced by min(r,tau).
