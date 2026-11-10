> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Repair round 1: independent derivation of Equations (8) and (13)

Date: 2026-10-20. This stage covered mathematical variants and an independent convex check with \(n=6\). It did not run ORL/YaleB diagnostics or edit the report.

Source: Chang, Nie, Ma, Yang, and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015, `9736-45063-1-PB.pdf`, Equations (8)-(13), Algorithm 1, and Equations (14)-(18) in the convergence proof. The coefficients below were rederived from the printed equations; the earlier audit was not used as evidence. Its factor 2 agrees with this derivation, but the numerical checks here refer to the recorded CVXPY runs.

Notation: samples are rows. \(G,F\in\mathbb{R}^{n\times c}\), and \(g_i,f_i\in\mathbb{R}^c\) denote row i. W is symmetric with zero diagonal and both directed edges stored. The combinatorial Laplacian is \(\widetilde L=\widetilde D-\widetilde W\), where \(\widetilde D_{ii}=\sum_j\widetilde W_{ij}\).

## Printed objectives

Equation (8) is

\[
\min_G \lVert G-F\rVert_{2,1}+\gamma\sum_{i,j}W_{ij}\lVert g_i-g_j\rVert_2,
\qquad
\lVert H\rVert_{2,1}=\sum_i\lVert h_i\rVert_2,
\]

Here \(h_i\) is row i of \(H=G-F\). The ordered sum \(\sum_{i,j}\) counts both directions of symmetric W. `equation8_objective` implements this sum.

Equation (10) gives S a diagonal of embedding-dimensional length and writes \(H=[h_1,\ldots,h_d]\). Equation (11) defines \(\widetilde W_{ij}=W_{ij}/(2\lVert g_i-g_j\rVert_2)\). Equation (12) is

\[
\operatorname{Tr}((G-F)^\top S(G-F))+\gamma\operatorname{Tr}(G^\top\widetilde L G),
\]

Its stationary point is Equation (13), \(G=(S+\gamma\widetilde L)^{-1}SF\). Algorithm 1 line 10 instead prints \((S_t+\gamma\widetilde W)^{-1}S_t X\). Equation (15) in the proof minimizes

\[
f(G)+\gamma\sum_{i,j}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2,
\qquad
f(G)=\operatorname{Tr}((G-F)^\top S(G-F)).
\]

## The coefficient is 2

When \(h_k\neq0\) and all relevant edge lengths are nonzero, the row-k fidelity derivative in Equation (8) is

\[
\frac{\partial}{\partial g_k}\lVert h_k\rVert_2
=\frac{h_k}{\lVert h_k\rVert_2}
=2S_{kk}h_k,
\qquad
S_{kk}=\frac{1}{2\lVert h_k\rVert_2}.
\]

The graph term \(\phi(G)=\sum_{i,j}W_{ij}\lVert g_i-g_j\rVert_2\) has two contributions to its derivative in \(g_k\): i=k and j=k. Symmetry makes them equal, hence

\[
\frac{\partial\phi}{\partial g_k}
=2\sum_j W_{kj}\frac{g_k-g_j}{\lVert g_k-g_j\rVert_2}.
\]

Substitute Equation (11): \(W_{kj}(g_k-g_j)/\lVert g_k-g_j\rVert_2=2\widetilde W_{kj}(g_k-g_j)\), while \((\widetilde LG)_k=\sum_j\widetilde W_{kj}(g_k-g_j)\). Therefore

\[
\frac{\partial\phi}{\partial g_k}=4(\widetilde LG)_k.
\]

The Equation (8) gradient is \(2S(G-F)+4\gamma\widetilde LG\). Setting it to zero and dividing by 2 gives

\[
(S+2\gamma\widetilde L)G=SF.
\]

The same factor follows independently from Equation (15). For symmetric weights,

\[
\sum_{i,j}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2
=2\operatorname{Tr}(G^\top\widetilde L G).
\]

Thus Equation (15) has quadratic term \(f(G)+2\gamma\operatorname{Tr}(G^\top\widetilde L G)\), again yielding \((S+2\gamma\widetilde L)G=SF\). Equation (12) omits this factor 2. Equation (13), with coefficient gamma, instead corresponds to replacing the graph term of Equation (8) by \((\gamma/2)\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\).

A two-point calculation confirms the identity. Let \(g=(0.2,0.8)\), \(W_{01}=W_{10}=1\), and distance 0.6:

| Quantity | Value |
| --- | --- |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.72\) |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) | \(1.2\) |
| \(\widetilde W_{01}=1/(2\cdot 0.6)\) | \(5/6\) |
| \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.6\) |
| \(\operatorname{Tr}(G^\top\widetilde L G)\) | \(0.3\) |

Here \(0.6=2\times0.3\). At the expansion point, the quadratic majorization term contributes half the graph norm; the lemma supplies the accompanying constant. The quadratic surrogate and Equation (8) do not have equal function values.

The gradient was checked by finite differences independently of the old documents. For n=5, c=2, a chain W, gamma=0.8, and seed 7, the maximum absolute difference between \(2S(G-F)+4\gamma\widetilde LG\) and centered finite differences of step \(10^{-6}\) was \(2.45\times10^{-9}\). The gradient is twice the E8 residual matrix.

## Equation (10) and Algorithm 1 line 10

Since \(\widetilde L\) is n by n, Equation (13) requires S to be n by n. The embedding-length diagonal printed in Equation (10) cannot be added to that system or used in the trace of Equation (9). The row-wise definition

\[
S_{ii}=\frac{1}{2\max(\lVert h_i\rVert_2,\varepsilon)}
\]

is compatible with the sample-wise \(\ell_{2,1}\) norm and the dimensions of Equations (11) and (13). This round retained it and did not implement the incompatible embedding-dimensional diagonal.

Algorithm 1 line 10 replaces \(\widetilde L\) by \(\widetilde W\), and F by X. The paper defines \(X\in\mathbb{R}^{d\times n}\), which has a different shape from F. This stage did not execute that line. Reweighted W and L were rebuilt from current G every iteration because Equation (11) depends on G.

## Implemented variants

In `SSC_method/optimizer.py`, `variant` sets \(A=S+c\gamma\widetilde L\):

| Variant | c | Linear system | Default |
| --- | --- | --- | --- |
| E13 | 1 | Printed Equation (13) | Yes; used when `variant` is omitted |
| E8 | 2 | Derived Equation (8) stationarity | No |

S remains row-wise and n by n, with \(G_0=F\). `zero_residual_floor` defaults to `median_pairwise`; `"eps"` remains available. `SpectralShrunkClustering` forwards the same parameter, and default calls retain `info_["linear_update"]="equation_13"`.

History records four distinct quantities:

- `equation8_objective`: the original Equation (8) norm with the caller's gamma; E13 does not minimize it.
- `sqrt_smoothed_equation8_objective`: replaces each norm by \(\sqrt{\lVert v\rVert_2^2+\varepsilon^2}\). A small epsilon can make values close to Equation (8), without equality.
- `irls_quadratic_surrogate`: the quadratic actually minimized with frozen S and L; E13 uses gamma times the trace and E8 uses 2 gamma times the trace.
- `fixed_point_residual`: \(\lVert AG-SF\rVert_F\) after rebuilding S and L at returned G. An inner `linear_residual` only measures one frozen system.

## Small convex references

The example used n=6, c=2, standard-normal F from NumPy seed 1, and gamma=0.8. Both graphs were symmetric with both edge directions stored:

- Chain: unit weights on adjacent vertices.
- Block: two unit-weight triangles connected by a bridge of weight 0.15.

IRLS used epsilon=1e-10, `tol=1e-12`, `max_iter=1000`, `zero_residual_floor="median_pairwise"`, and G0=F. The independent reference used CVXPY 1.9.3 / CLARABEL 0.11.1 with `tol_gap_abs=tol_gap_rel=tol_feas=1e-10`, `max_iter=500`. Both reference problems returned `optimal`.

| Graph | Solver | Equation (8) or corresponding target | Maximum reference difference | Fixed-point residual | Iterations |
| --- | --- | --- | --- | --- | --- |
| Chain | CLARABEL, graph coefficient \(\gamma\) | \(4.021064576768\)(12 steps) |  |  |  |
| Chain | E8 | \(4.021064576828\) | \(1.07\times 10^{-6}\) | \(1.12\times 10^{-6}\) | 103, step convergence |
| Chain | CLARABEL, graph coefficient \(\gamma/2\) | \(3.843869772520\)(10 steps) |  |  |  |
| Chain | E13 evaluated in \(\gamma/2\)  target | \(3.843869772479\) | \(4.08\times 10^{-6}\) | \(8.66\times 10^{-7}\) | 1000, step criterion unmet |
| Chain | E13 evaluated inprinted Eq. (8) | \(4.536864561036\) |  |  |  |
| Block | CLARABEL, graph coefficient \(\gamma\) | \(3.652064947785\)(10 steps) |  |  |  |
| Block | E8 | \(3.652064947951\) | \(9.94\times 10^{-7}\) | \(3.03\times 10^{-6}\) | 1000, step criterion unmet |
| Block | CLARABEL, graph coefficient \(\gamma/2\) | \(3.573381366945\)(13 steps) |  |  |  |
| Block | E13 evaluated in \(\gamma/2\)  target | \(3.573381366967\) | \(2.70\times 10^{-6}\) | \(1.41\times 10^{-6}\) | 1000, step criterion unmet |
| Block | E13 evaluated inprinted Eq. (8) | \(3.655950751916\) |  |  |  |

E8 agreed with printed Equation (8), while E13 agreed with its half-gamma graph version. The Equation (8) optimum was about 0.516 below the Equation (8) value at E13 on the chain, and about 0.0039 below on the block. The smaller block difference still exceeded solver tolerance; the targets are distinct.

At the chain E8 point, Equation (8) was 4.021064576828; the epsilon=1e-10 smoothed value was 4.021064577355, and the epsilon=1e-2 smoothed value was 4.101876705618. The IRLS surrogate was 2.010532438591 and fixed-point residual 1.12e-6. The surrogate is approximately half the original objective at the expansion point. A matrix residual is not an objective value.

With S and L frozen, both c=1 and c=2 quadratics were independently minimized from random starts using scipy.optimize L-BFGS-B and agreed with spsolve. This checks the quadratic surrogate, not Equation (8).

Step convergence is distinct from a fixed-point residual. On the block graph, E13 with tol=1e-8 and max_iter=80 stopped at iteration 57: Frobenius step 2.18e-8, frozen linear residual 1.06e-6, but rebuilt fixed-point residual 0.361. With tol=1e-12 and 1000 iterations, the rebuilt residual fell to 1.41e-6 and the objective agreed with CLARABEL. A step flag cannot replace this residual.

With `zero_residual_floor="eps"`, E13 remained near F. For a linearly spaced 6 by 2 embedding, chain W, gamma=1, epsilon=1e-8, two E13 steps gave movement 1.41e-8. E8 accepted the same option and moved 2.83e-8 in its first step; later row residuals grew. At 30 steps its movement was 0.390, Equation (8) fell from 2.828 to 2.277, and fixed-point residual was 0.987; it had not converged. The default and convex checks used `median_pairwise`.

## Scope limits

ORL 53.9 versus 76.0 and YaleB 19.7 versus 49.8 were not rerun with E8 or E13 in this mathematical stage. Objective differences in tiny examples do not imply clustering-accuracy changes. Equation (8), smoothing, the IRLS surrogate, and the fixed-point residual remain separate records.