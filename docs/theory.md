# Mathematical foundations and scope

This document develops the fixed-graph SSC objective, its numerical certificates,
and the candidate mechanisms studied in this project. The main scientific
question is whether shrinkage improves ACC and NMI beyond matched spectral
clustering. Convexity, representation movement and numerical optimality are
properties of intermediate computations; none implies better class labels.
The [methods](methods.md), [experimental protocol](experimental_protocol.md)
and [results](results.md) define the corresponding empirical comparisons.

## 1. Two graphs and the SSC target

Input samples are rows of \(X\). An upstream affinity \(A\) produces a spectral
representation \(F\). A separate affinity \(W\), constructed in that spectral
space, controls refinement to \(G\). SC rounds \(F\); matched SSC rounds \(G\)
with the same clustering protocol. Contamination of \(A\) and contamination of
\(W\) therefore describe different mechanisms.

Store each undirected positive edge once and orient it arbitrarily. Let \(B\)
have one \(+1\) and one \(-1\) per edge row, so \((BG)_e=g_i-g_j\). With
\(a_i>0\), \(w_e>0\), \(\gamma\geq0\) and \(c_e=2\gamma w_e\), write

\[
P_0(G)=\sum_i a_i\|g_i-f_i\|_2+\sum_e c_e\|(BG)_e\|_2.
\]

The project uses \(a_i=1\) for original SSC. The coefficient two reproduces
Equation 8's ordered-pair graph sum in [Chang et al.](https://doi.org/10.1609/aaai.v29i1.9606).
The E8 IRLS system has \(S+2\gamma\widetilde L\), whereas the printed E13 system
has \(S+\gamma\widetilde L\). Consequently, E13 at nominal
\(\gamma_{13}\) targets E8 at effective \(\gamma_{13}/2\), for the same fixed
graph and other conventions.

Each term in \(P_0\) is convex. The unsquared fidelity need not be strictly
convex, so a minimizer need not be unique. K-means rounding is a separate
nonconvex operation, and class labels do not occur in this objective.

## 2. A feasible dual gives an objective certificate

For the radial Huber function, define

\[
\phi_\delta(r)=
\begin{cases}
r^2/(2\delta),&0\leq r\leq\delta,\\
r-\delta/2,&r>\delta,
\end{cases}
\qquad \phi_0(r)=r.
\]

The common family is

\[
P_\delta(G)=\sum_i a_i\phi_\delta(\|g_i-f_i\|_2)
             +\sum_e c_e\|(BG)_e\|_2.
\]

The graph norm has the support-function representation
\(c_e\|z\|_2=\sup_{\|q_e\|_2\leq c_e}\langle q_e,z\rangle\).
For \(h_i(z)=a_i\phi_\delta(\|z\|_2)\), its conjugate is

\[
h_i^*(s)=
\begin{cases}
\dfrac{\delta}{2a_i}\|s\|_2^2,&\|s\|_2\leq a_i,\\
+\infty,&\text{otherwise}.
\end{cases}
\]

After shifting the fidelity by \(F\), minimization over \(G\) yields

\[
D_\delta(q)=\langle B^Tq,F\rangle
 -\frac{\delta}{2}\sum_i\frac{\|(B^Tq)_i\|_2^2}{a_i},
\qquad
\|q_e\|_2\leq c_e,\quad \|(B^Tq)_i\|_2\leq a_i.
\]

The sign agrees with a primal update in the direction \(-B^Tq\). At
\(\delta=0\), the quadratic term vanishes. For squared fidelity
\(a_i\|g_i-f_i\|_2^2/(2s)\), the dual has the same quadratic term with
\(s\) in place of \(\delta\), but has **no node-ball constraints**.

Weak duality gives \(D(q)\leq\min_G P(G)\leq P(\widehat G)\) for every feasible
\(q\) and actual primal point \(\widehat G\). Thus a small objective value or
agreement between solvers is insufficient: a lower bound is also needed.
The reported certificate requires

\[
\frac{P(\widehat G)-D(q)}{\max(1,|P(\widehat G)|,|D(q)|)}\leq10^{-5}
\]

and edge/node capacity violations at most \(10^{-8}\). A materially negative
primal–dual gap is an inconsistency, not a stronger certificate.

The zero dual supplies the valid lower bound zero. A supplied initial dual is
checked before any update, and its feasible bound is retained if it is better.
Candidate duals are scaled inward by the minimum applicable capacity ratio and
checked again. Best primal and best feasible dual may originate at different
iterations: this is valid for an objective bound. Clustering metrics remain
attached to the actual saved primal point, rather than to an objective value
from another iterate. A certificate for one output does not certify a different
output merely because its input \(F,W\) is the same.

### PDHG and diagonal scaling

The numerical method is an application of
[Chambolle–Pock primal–dual optimization](https://doi.org/10.1007/s10851-010-0251-1),
rather than a new optimizer. In the unweighted incidence formulation, edge
duals are projected onto balls of radius \(2\gamma w_e\). With maximum
unweighted degree \(d_{\max}\), the bound \(\|B\|_2^2\leq2d_{\max}\) permits
uniform steps \(\tau=\sigma=0.99/\sqrt{2d_{\max}}\).

The diagonal formulation instead uses

\[
K=\operatorname{diag}(\sqrt w)B,\qquad
q=\operatorname{diag}(\sqrt w)p,\qquad
\|p_e\|_2\leq2\gamma\sqrt{w_e}.
\]

Set

\[
T_i=\frac{0.99}{\sum_e|K_{ei}|},\qquad
\Sigma_e=\frac{0.99}{\sum_i|K_{ei}|};
\]

an isolated node uses \(T_i=1\). A Schur bound gives
\(\|\Sigma^{1/2}KT^{1/2}\|_2\leq0.99\). For a two-endpoint edge,
\(\Sigma_e=0.99/(2\sqrt{w_e})\), so its dual increment in original coordinates
is \(q_e\leftarrow q_e+(0.99\sqrt{w_e}/2)(B\overline G)_e\), followed by the
appropriate projection. Both formulations evaluate the same original objective
and map back to capacities \(2\gamma w_e\) for certification.

A componentwise dual-flow candidate solves
\(B^T\operatorname{diag}(w)Bz=t\) and forms
\(q=\operatorname{diag}(w)Bz\). The target must sum to zero in each connected
component. The resulting flow still needs capacity and gap checks. Failure of
this particular construction does not prove that no feasible certificate
exists. A component-consensus primal is an upper bound, not a lower bound.
Same-objective primal/dual warm restarts are valid initializations; they do not
claim to reproduce an uninterrupted solver trajectory.

## 3. When can the unsquared objective remain at F?

For a noncoincident edge, let
\(u_e=(BF)_e/\|(BF)_e\|_2\). Set \(u_e=0\) on exactly coincident edges and
define

\[
b=B^T(2wu),\qquad
\gamma_0=\left[\max_i\frac{\|b_i\|_2}{a_i}\right]^{-1}.
\]

For \(0\leq\gamma\leq\gamma_0\), the dual \(q_e=2\gamma w_eu_e\) is feasible,
and \(P_0(F)=D_0(q)\). Therefore \(G=F\) is an optimum. When every positive
edge is noncoincident, its graph-norm subgradient is fixed, and the node-ball
condition is also necessary for \(F\) to be optimal. Coincident edges admit
other subgradients, so choosing zero there gives a sufficient region that need
not be maximal. An infinite threshold is asserted only for an explicit
zero-total-variation case.

This result concerns unsquared fidelity. It is not an activation threshold for
radial Huber or squared fidelity. An analytic \(G=F\) certificate establishes
that shrinkage can be omitted at that setting; it does not establish a useful
choice of \(\gamma\).

### Incident mass is sufficient; arbitrary deletion is not

Write \(r_i=\|g_i-f_i\|_2\). The reverse triangle inequality gives

\[
P_0(G)-P_0(F)\geq
\sum_i\left(a_i-2\gamma\sum_{j:\{i,j\}\in E}w_{ij}\right)r_i.
\]

Hence \(2\gamma\sum_jw_{ij}\leq a_i\) at every node is a sufficient
\(G=F\) condition. Deletion preserves this particular sufficient bound if it
held before deletion and retained weights are unchanged. Rescaling the edited
graph's mass requires checking the bound again. The bound discards directional
cancellation and need not hold whenever \(F\) is optimal.

The distinction matters on an eight-cycle with unit edge weights and anchors
\(f_i=(\cos(2\pi i/8),\sin(2\pi i/8))\). At each node, the two unit-edge
directions have resultant norm \(2\sin(\pi/8)\). Thus

\[
\gamma_0=\frac1{4\sin(\pi/8)}\approx0.65328148.
\]

After deleting one edge, each former endpoint has only one unit-edge direction,
so the threshold becomes \(1/2\). At \(\gamma=0.6\), \(F\) is optimal on the
cycle and is not optimal after deletion. All positive edges are noncoincident,
so the subgradient condition is decisive. Edge deletion can remove force
cancellation; there is no universal deletion-preserves-optimality theorem.

## 4. Two representatives explain one fusion failure

Consider two group-constant representatives, with \(m<n\) anchors at \(a,b\),
\(d=\|a-b\|_2>0\), and fixed total cross-group attraction
\(\lambda=2\gamma\sum_{e\text{ cross}}w_e\). The reduced objective is

\[
J(u,v)=m\|u-a\|_2+n\|v-b\|_2+\lambda\|u-v\|_2.
\]

For \(r=\|u-v\|_2\), triangle inequality gives fidelity at least
\(m\max(d-r,0)\). For \(0\leq r\leq d\), equality is attained by \(v=b\)
and \(u\) on the segment from \(a\) to \(b\), at distance \(r\) from \(b\).
Larger \(r\) cannot improve an endpoint. The reduced cost is consequently

\[
J(r)=m(d-r)+\lambda r,\qquad
\min J=d\min(m,\lambda).
\]

If \(\lambda<m\), the separated anchors minimize it; if \(\lambda>m\), both
representatives fuse at \(b\). At \(\lambda=m\), every point on the described
segment is optimal: separation and fusion coexist with intermediate optima.
The distance-independent fusion threshold concerns this fixed-weight,
group-constant model. A data-dependent graph can change \(\lambda\) as \(d\)
changes, and unrestricted within-group representations are a different problem.

### Capped fusion and equality cases

Replace the graph norm by \(\rho_\tau(r)=\min(r,\tau)\), with \(0<\tau<d\).
Then

\[
J_{\mathrm{cap}}(r)=m(d-r)+\lambda\min(r,\tau),\qquad
\min J_{\mathrm{cap}}=\min(md,\lambda\tau).
\]

The two linear pieces attain their overall minimum at \(r=0\) or \(r=d\);
the kink \(r=\tau\) cannot improve those endpoints. Separation is preferred
when \(\lambda\tau<md\), and fusion when \(\lambda\tau>md\). At
\(\lambda\tau=md\), both endpoint states are global optima; with \(d>\tau\),
intermediate states are not additional minimizers. If \(\tau\geq d\), capping
does not change the reduced objective on \([0,d]\), including the continuum at
\(\lambda=m\). Thus strict inequalities are essential to a strict conclusion.
The range

\[
m<\lambda<md/\tau
\]

shows original fusion versus capped separation. It demonstrates preserved
information in this model, not a guarantee of improved benchmark ACC.

### The five-point reference is a specific graph

The verified example has anchors \(F=(0,0,4,4,4)\), weight 10 on each
within-group edge, weight 0.25 on all six cross-group edges, \(\gamma=1\), and
\(\tau=1\). Its total cross attraction is three. The corresponding
two-representative formulas give eight for linear fusion and three for capped
fusion. Exhaustive active-state reference bounds on the unrestricted, specific
ten-edge graph agree with those values at the recorded numerical precision. A feasible capped
upper bound of three excludes states with a larger inactive-edge constant,
leaving 64 of the 1,024 states for convex primal–dual checks.

The local capped method can stay at objective eight from the fused SSC start,
while the \(F\) start attains three. Selecting the lower value of the same
objective requires no labels. The global conclusion comes from the exhaustive
tiny-graph calculation, not from local convergence. It is not a theorem about
arbitrary five-point graphs. SC already separates these anchors perfectly, so
the example establishes damage avoidance rather than extra benefit over SC.

### Optimization and fidelity controls

The identity
\(\min(r,\tau)=\min_{z\in\{0,1\}}zr+(1-z)\tau\) produces an active-edge
alternation: choose edge states at the current distances, then solve a convex
SSC subproblem plus a constant. Retaining an actual previous primal candidate
and rejecting any increase in the full capped objective protects monotonicity.
A fixed active set and a certified inner solve are a block fixed-point
condition, not a global certificate for the nonconvex capped objective.

The squared-fidelity control is

\[
\sum_i\frac{\|g_i-f_i\|_2^2}{2s_F}
 +2\gamma\sum_e w_e\rho_\tau(\|(BG)_e\|_2).
\]

Multiplying by \(2s_F\) maps its linear-fusion coefficient to Equation 7's
ordered-pair convention as \(\gamma_{E7}=2s_F\gamma\). For an N1 quadratic
scale \(\delta\), the corresponding mapping is \(2\delta\gamma\). This
algebraic mapping does not make equal numerical gamma values equally strong
across different fidelities; separate parameter searches are needed.

Group-truncated fusion is prior work in
[PRclust](https://jmlr.csail.mit.edu/papers/volume14/pan13a/pan13a.pdf).
[Shah–Koltun Robust Continuous Clustering](https://vladlen.info/publications/robust-continuous-clustering/)
also addresses unreliable graph relations. Neither penalty family is claimed
as a new invention here. The earlier real-data capped-fusion mechanism gate
supported zero of four benchmarks; its synthetic damage-avoidance examples do
not replace that negative finding. The later connectivity intervention uses a
different, explicitly defined criterion.

## 5. Secondary candidates: radial fidelity and heat geometry

### Radial Huber fidelity

Because \(\phi_\delta\) is convex and nondecreasing on nonnegative arguments,
its composition with an Euclidean norm is convex. Together with fixed
nonnegative graph total variation, it gives a convex target.

If the graph total variation at \(F\) is positive, take any common location
\(h\) and consider \(G(t)=(1-t)F+t\mathbf1h^T\). For sufficiently small positive \(t\), fidelity
increases quadratically, while graph total variation decreases linearly:

\[
P_\delta(G(t))-P_\delta(F)
=\frac{t^2}{2\delta}\sum_i a_i\|f_i-h\|_2^2
 -t\sum_e c_e\|(BF)_e\|_2<0.
\]

Thus \(F\) is not optimal when \(\delta>0\) and the weighted graph variation
is positive. This proves activation, not useful movement. Original SSC also
moves at many evaluated settings without a stable clustering improvement.

For square orthogonal \(Q\), all residual and edge norms are unchanged by
\((G,F)\mapsto(GQ,FQ)\), so the solution set is equivariant; uniqueness is not
implied. Coordinatewise Huber does not share this general rotational property.
Moreover,

\[
0\leq r-\phi_\delta(r)\leq\delta/2
\quad\Longrightarrow\quad
P_0(G_\delta)-\min P_0\leq\frac\delta2\sum_i a_i
\]

for an exact Huber minimizer. A computed point adds its certified **absolute**
optimality gap. This is an objective-approximation bound, not a
classification-error bound. Each radial fidelity gradient has norm at most
\(a_i\); that bounded influence does not transfer a breakdown theorem from
another graph or estimator. In particular,
[Sun et al.'s resistant convex clustering](https://doi.org/10.1214/25-EJS2359)
uses a different, coordinatewise Huber construction and is distinct from
Shah–Koltun RCC.

### Heat geometry

For the same upstream affinity and a symmetric positive-semidefinite normalized
Laplacian \(L\), define

\[
K_t=e^{-tL},\qquad H_t=e^{-tL/2},\qquad H_tH_t^T=K_t.
\]

The exact squared feature distance is
\(d_t^2(i,j)=K_{t,ii}+K_{t,jj}-2K_{t,ij}\). Distances between rows of \(K_t\)
instead use \(K_{2t}\), so these are different constructions.
For another symmetric positive-semidefinite \(L'\), Duhamel's formula and
semigroup contraction give

\[
\|e^{-tL}-e^{-tL'}\|_2\leq t\|L-L'\|_2.
\]

Using \(v=e_i-e_j\), with \(\|v\|_2^2=2\), each squared distance changes by
at most \(2t\|L-L'\|_2\). A squared-distance k-nearest-neighbor boundary gap
strictly greater than \(4t\|L-L'\|_2\) therefore cannot reverse under that
perturbation. This bound assumes a bound on the Laplacian change; it does not
automatically turn a small pixel perturbation into a small change of a
discontinuously constructed nearest-neighbor graph.

Scalable features \(Z=e^{-tL/2}R\), with independent Gaussian
\(R_{ij}\sim N(0,1/r)\), approximate the full-spectrum geometry. They are not
the exact \(H_t\), and do not automatically inherit its exact-distance bound.
The earlier primary setting was \(t=4,r=128\), seed 20261108; its projection
is held fixed within a perturbation comparison. No final truncation to the
class count is substituted. Principal-angle comparisons use raw eigenvectors,
not row-normalized embeddings. Sign and orthogonal basis changes preserve
geometry and are not themselves eigenspace failures.

Hard-dimension, heat-only, heat-plus-SSC and W-only controls distinguish feature
dimension, filtering and shrinkage. Stable geometry can still cluster poorly,
and large diffusion times can erase distinctions. The earlier heat results are
secondary evidence; no new Huber, capped-fusion or heat grid forms the main
submission comparison.

## Independent refinement theory

The current E1, E2 and E3 studies have distinct convex objectives, dual feasible
sets and proximal maps. Their complete derivations and limiting cases are in
[independent convex refinement objectives](extension_verification_theory.md).
The geometric-median dispersion bound applies to E1's optimized G; it does not
imply class preservation or ACC/NMI gains. E2's tangent/radius support function
and E3's combined incidence/hinge node capacities are checked separately.
