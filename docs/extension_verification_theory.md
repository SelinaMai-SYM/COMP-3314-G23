# Independent convex refinement objectives

Each study optimizes its own representation. They are alternatives; none uses
another extension's fitted output. See the [registered protocol](extension_verification_plan.md)
for fixed operating points and gates, and the [results](extension_verification_results.md)
for empirical qualification.

Let H be the fixed anchor and B the incidence matrix with one row per positive
undirected edge. Set c_e = 2 gamma w_e. The common fidelity is the unsquared sum
of row distances to H. W0 is constructed from F0 and stays fixed when H changes
to U = rowunit(F0). Original geometry rounds G; the common angular panel rounds
rowunit(G) for every method. Exact zero rows remain zero.

## E1: relative stopping distance

\[
J_\eta(G)=\sum_i\|g_i-h_i\|_2+
\sum_e c_e\bigl(\|(BG)_e\|_2-\eta\|(BH)_e\|_2\bigr)_+.
\]

The frozen edge tolerance stops that edge's own attraction inside the tube.
Other edges may still decrease its endpoint distance. This loss is convex and
is neither a capped penalty nor a minimum-distance constraint. Eta = 0 gives
ordinary SSC, eta = 1 makes H optimal with zero objective, and gamma = 0 gives H.

For a_e = eta ||(BH)_e||, the dual is

\[
D_\eta(q)=\langle H,B^Tq\rangle-\sum_e a_e\|q_e\|_2,
\quad \|q_e\|_2\le c_e,\quad\|(B^Tq)_i\|_2\le1.
\]

In original-edge coordinates the dual prox soft-thresholds the norm by
sigma_e a_e, then projects onto the radius c_e ball. With weighted incidence
K = diag(sqrt(w)) B, the original-edge step is w_e Sigma_e.

Write D(H) = min_z sum_i ||h_i-z||. A geometric-median-centered contraction
eta H + (1-eta)z has zero edge penalty and fidelity (1-eta)D(H). Thus the optimum
is at most (1-eta)D(H). The triangle inequality gives
D(H) <= sum_i ||g_i-h_i|| + D(G). Combining the inequalities proves

\[
D(G)\ge\eta D(H)-\epsilon,
\qquad\epsilon=J_\eta(G)-D_\eta(q).
\]

Epsilon is the absolute certified gap. Numerical checks use lower and upper
geometric-median bounds, including their own absolute gap. The statement concerns
G before normalization. It does not protect every edge, class separation or
ACC/NMI. For eta < 1, the anchor's leaving threshold is unchanged.

Two tied groups of sizes 2 and 3 at distance 4 have optima 6.4/4.8/3.2 at
lambda = 1.6 and eta = 0/.25/.5, and 8/6/4 at lambda = 2.4. At lambda = 2,
a continuum of separations may minimize the objective. Comparisons therefore
check objective values and feasibility without requiring identical optimizers.

A supplementary explanation follows directly from the objective. Let
C = sum_e c_e a_e. Since (r-a)_+ >= r-a, J_eta(G) >= J_0(G)-C.
If an exact ordinary-SSC minimizer has every edge distance at least its frozen
tolerance, equality holds there, so that same representation minimizes E1.
The saved-output tube and cross-objective-certificate diagnostics examine this
condition without adding a fit or selecting a parameter. Finite certificates
remain attached to their own targets and do not repair an uncertified control.

## E2: fixed tangent planes

At nonzero unit anchors set P_i = I-u_i u_i^T. E2 minimizes ordinary SSC subject
to u_i^T(g_i-u_i) = 0 and ||g_i-u_i|| <= tan(theta), with displacement frozen to
zero at exact zero anchors. Its dual, for v = B^T q, is

\[
D_T(q)=\langle U,v\rangle-\tan(\theta)
\sum_{i:u_i\ne0}(\|P_i v_i\|_2-1)_+,
\qquad\|q_e\|_2\le c_e.
\]

The primal proximal displacement projects onto the fixed tangent plane, shrinks
radially by the node step, then clips to the radius. The isotropic control omits
the tangent projection, uses sin(theta), and includes every row in its support
function. An unconstrained consensus is not a feasible primal bound here.

The radial-neutralization gate is a development intervention, not an optimized
method. Energy is measured only on nonzero unit anchors. Angles additionally
require G and the neutralized R to have norms above 1e-12. These masks never
remove samples from ACC/NMI. The two locked contrasts, their adjusted lower
quantile and the isotropic control are specified in the protocol.

## E3: frozen relative-neighbor comparisons

Construct triplets without labels from two independently centered/normalized
feature views. Verified image geometry supplies checkerboards; otherwise the
fixed PCG64 feature split is used. All i, j and k come from the common valid pool,
with immutable row IDs resolving ties. Frozen reference rows u_j, u_k define

\[
s=\|u_j-u_k\|_2,\quad m=.1s^2,\quad
n=(u_k-u_j)/s,\quad
\beta=(m+\|u_j\|_2^2-\|u_k\|_2^2)/(2s),
\quad h(g_i)=[n^Tg_i+\beta]_+.
\]

The gradient is unit length. With at most one hinge per anchor, E3 minimizes
J_R = J_0 + mu sum h(g_i), without coverage rescaling. Let T contain those
unit-gradient rows. Its dual is

\[
D_R(q,p)=\langle U,B^Tq+T^Tp\rangle+\beta^Tp,
\quad\|q_e\|_2\le c_e,\quad0\le p\le\mu,
\quad\|(B^Tq+T^Tp)_i\|_2\le1.
\]

The combined operator determines steps. Repair scales q and p together.
At gamma = 0 and mu > 1, g_i = u_i-h(u_i)n_i; at mu < 1, U is optimal;
mu = 1 allows the intervening segment. Empty triplets reduce the objective to
ordinary SSC and do not remove that benchmark. Hinge satisfaction is checked
separately on optimized G and rounded-input Q.

## Numerical qualification

Separate best feasible primal and dual points are retained, including the
initial dual. Saved arrays independently reproduce objectives, dual values and
violations. A relative gap at most 1e-5 and violations at most 1e-8 qualify an
output; signed negative gaps are preserved and rejected. Certificate validity
concerns the exact saved G, not its normalized Q. Independent small-graph
CLARABEL references validate objectives, proximal mappings, limiting cases and
nonunique solutions. Complete state supports cumulative bounded continuation.
