# Numerical foundations

The fixed-graph SSC objective and selected quadratic refinements are different
optimization problems. Their certificates qualify saved numerical outputs;
clustering quality is measured separately.

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


## A feasible SSC dual

For $c_e=2\gamma w_e$ and unsquared fidelity, a feasible graph dual satisfies
$\|q_e\|_2\le c_e$ and $\|(C^\top q)_i\|_2\le1$. Its lower bound is

$$D(q)=\langle C^\top q,F\rangle\le\min_G P(G)\le P(\widehat G).$$

The zero dual gives a valid initial bound. The solver retains the best feasible
lower bound and best actual primal upper bound separately, even if they arise
at different iterations. A small iterate step or agreement with another solver
is not a gap certificate. A materially negative raw gap is an inconsistency.
Historical SSC certification requires relative gap ≤1e-5 and edge/node capacity
violations ≤1e-8. Each bound belongs to its exact saved F/W/G and objective.

The diagonal formulation uses $K=\operatorname{diag}(\sqrt w)C$ and maps its
dual back through $q=\operatorname{diag}(\sqrt w)p$, recovering capacities
$2\gamma w_e$. The [certified solver](../method_extension/next_round/certified_solver/solver.py)
retains the initial feasible bound before updating PDHG.

## Staying at the anchor

At $G=F$, the graph subgradient can be balanced by the unit node fidelity balls.
The sufficient incident-mass condition $2\gamma\max_i\sum_jw_{ij}\le1$ is
valid for any edge directions. It is not a necessary condition: cancellation
can certify additional cases. Deleting an edge can destroy that cancellation;
the eight-node cycle example at gamma0.6 is retained in the
[certificate tests](../tests/next_round/test_certificates.py).

## Selected quadratic objectives

For QSSC, $J_Q(G)=\frac12\|G-F\|_F^2+\lambda\sum_e w_e\|(CG)_e\|_2$.
Its dual lower bound is

$$D_Q(q)=\langle C^\top q,F\rangle-\tfrac12\|C^\top q\|_F^2,
\qquad \|q_e\|_2\le\lambda w_e.$$

There are no node-ball constraints for quadratic fidelity. Strong convexity
bounds primal distance by the primal–dual gap, allowing uncertainty-aware
movement matching. The selected comparisons require relative gap ≤1e-6,
capacity residual ≤1e-8 and the locked movement interval.

[Edge-deletion formulation](extension_round3/method_design.md) supplies the
exact pilot rank-one identity, weighted allocations, tube and triangle-slack
duals. A finite certified optimizer may still miss the required movement
operating point. Qualification is distinct from both the measured ACC/NMI and
whether a method improves over QSSC or its plain-pilot control.

The [development evidence](development_summary.md) links the earlier objectives
and gates used in presentation slide6.1. The selected methods are three
independent convex refinements, with their complete numerical definitions in
that formulation guide.

## Printed-inequality qualification

The final report also checks the original paper's printed Lemma 1 (Eq. 14):
with row-norm magnitudes 1/2 and 1, its two sides are 0 and −1/2, so it is
invalid as written. The reweighting argument uses the standard touching
majorizer with both quadratic terms divided by the same nonzero reference
norm. This typographical issue is separate from the E8/E13 coefficient mapping
and from numerical certification of saved benchmark outputs.
