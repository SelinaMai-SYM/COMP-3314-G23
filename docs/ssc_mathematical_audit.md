> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# SSC mathematical audit

Source: Chang, Nie, Ma, Yang, and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015, `9736-45063-1-PB.pdf`, extracted with `pdftotext -layout`. This audit covers Equations (3)-(13), Algorithm 1, and coefficient checks in Equations (14)-(18). Implementation decisions are corrections and reproduction assumptions, not a new method.

Samples are rows in arrays of shape `(n,d)`. Algorithm 1 writes \(X\in\mathbb{R}^{d\times n}\). Equation (13) has F on the right; the optimization does not multiply by X.

## Equations (3)-(4): spectral representation

Equation (3) minimizes \(\operatorname{Tr}(F^\top L F)\) with \(F=Y(Y^\top Y)^{-1/2}\). Equation (4) defines the symmetric normalized Laplacian

\[
L_n = I - D^{-1/2} A D^{-1/2}.
\]

For k-neighbors, \(A_{ij}=\exp(-\lVert x_i-x_j\rVert^2/\delta^2)\), otherwise zero; \(D_{ii}=\sum_j A_{ij}\). The paper sets k=5 for all spectral methods.

The implementation uses the c eigenvectors associated with the smallest eigenvalues of Ln, in ascending order, as F of shape n by c. This is spectral embedding, not PCA. Neighbor counts and bandwidths are passed explicitly rather than inherited from sklearn defaults.

An isolated vertex uses \(D^{-1/2}_{ii}=0\), so its Ln row is a unit coordinate vector. The paper does not specify this boundary case.

## Equations (5)-(8): shrinkage objective

A second k-neighbor graph is built on the spectral rows, with \(W_{ij}=\exp(-\lVert f_i-f_j\rVert^2/\delta^2)\). Equations (5)-(7) use squared losses; Equation (8) replaces them with row-wise \(\ell_{2,1}\):

\[
\min_G \lVert G-F\rVert_{2,1} + \gamma\sum_{ij} W_{ij}\lVert g_i-g_j\rVert_2,
\quad G,F\in\mathbb{R}^{n\times c}.
\]

Here \(\lVert H\rVert_{2,1}=\sum_i\lVert h_i\rVert_2\), with hi denoting row i of H=G-F. The ordered sum counts both directions of symmetric W.

## Equations (9)-(10): S must be n by n and row-wise

The trace \(\operatorname{Tr}((G-F)^\top S(G-F))\) in Equation (9) requires n by n S. Equation (10) prints

\[
S=\operatorname{diag}\Big(\frac{1}{2\lVert h_1\rVert_2},\ldots,\frac{1}{2\lVert h_d\rVert_2}\Big),
\]

It also writes \(H=[h_1,\ldots,h_d]\), where d denotes embedding dimension. If hj is a column, S is c by c; the paper mixes original and embedding dimensions. This conflicts with Equation (9) and with sample-wise row \(\ell_{2,1}\) robustness in Nie et al. (2010).

**Correction:** use an n by n diagonal S,

\[
S_{ii}=\frac{1}{2\max(\lVert h_i\rVert_2,\varepsilon)},
\]

where hi is row i of G-F. Epsilon prevents division by zero and does not introduce a new regularizer.

## Equations (11)-(13) and Algorithm 1 line 10

Equation (11) defines \(\widetilde W_{ij}=W_{ij}/(2\lVert g_i-g_j\rVert_2)\), \(\widetilde L=\widetilde D-\widetilde W\), and \(\widetilde D_{ii}=\sum_j\widetilde W_{ij}\). This is a combinatorial Laplacian, distinct from the normalized Laplacian in Equation (4).

Equation (12) is

\[
\min_G \operatorname{Tr}((G-F)^\top S(G-F))+\gamma\operatorname{Tr}(G^\top\widetilde L G).
\]

Differentiation in G and stationarity yield Equation (13):

\[
G=(S+\gamma\widetilde L)^{-1}SF.
\]

Algorithm 1 line 10 instead gives \(G_{t+1}=(S_t+\gamma\widetilde W)^{-1}S_t X\), substituting W for L and X for F. Line 4 also places the G-dependent reweighted W outside the loop.

**This implementation follows Equation (13), not line 10.** Reweighted W and L are rebuilt from current G each iteration. scipy.sparse.linalg.spsolve solves the linear system without an explicit inverse. Positive Sii and nonnegative gamma make S+gamma L symmetric positive definite; `(A+A.T)/2` removes numerical asymmetry before solving.

G0=F is an assumption: the paper specifies only its dimensions. At that start H0=0 and Equation (10) divides by zero. Using epsilon as the initial denominator yields S of order 1/epsilon and an initial O(epsilon) movement, often leaving the iteration near F even when F is not stationary. Only the first all-zero residual uses the median positive pairwise row distance as a finite scale. Subsequent zeros use epsilon. Reusing the large scale whenever G approaches F can repeatedly restart the initial step and cause cycles, as unit tests demonstrate. The one-time scale is recorded as `initial_zero_residual_floor`; `zero_residual_floor="eps"` retains the older near-F behavior.

## Coefficients in Equations (14)-(18)

Lemma 1, for nonzero \(g,g^t\in\mathbb{R}^c\), states

\[
\lVert g\rVert_2-\frac{\lVert g\rVert_2^2}{2\lVert g^t\rVert_2}
\le
\lVert g^t\rVert_2-\frac{\lVert g^t\rVert_2^2}{2\lVert g^t\rVert_2}.
\]

Adding Equations (16) and (17) cancels the quadratics and yields Equation (18) monotonicity. This scalar Equation (8) argument is algebraically consistent with \(\widetilde W_{ij}=W_{ij}/(2\lVert g_i^t-g_j^t\rVert_2)\); it does not pass through a trace.

The trace and ordered sum differ by a factor. Take \(G=(0.2,0.8)^\top\), \(W_{01}=W_{10}=1\), and distance 0.6:

| Quantity | Value |
| --- | --- |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.72\) |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) | \(1.2\) |
| \(\widetilde W_{01}=1/(2\cdot 0.6)\) | \(5/6\) |
| \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.6\) |
| \(\operatorname{Tr}(G^\top\widetilde L G)\) | \(0.3\) |

Thus at the expansion point,

\[
\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2
= 2\operatorname{Tr}(G^\top\widetilde L G)
= \tfrac12\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2.
\]

Equation (15) minimizes \(f(G)+\gamma\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2\). Symmetry gives \(\sum_{ij}\widetilde W_{ij}\lVert\cdot\rVert_2^2=2\operatorname{Tr}(G^\top\widetilde L G)\), so its stationary system is

\[
(S+2\gamma\widetilde L)G = SF.
\]

Equation (12) instead has gamma times the trace, producing the gamma L coefficient in Equation (13). That coefficient lacks a factor 2 relative to the Equation (8) majorizer.

Direct differentiation of Equation (8) gives the same factor. For symmetric W,

\[
\frac{\partial}{\partial g_k}\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2
= 4(\widetilde L G)_k,
\qquad
\frac{\partial}{\partial g_k}\lVert h_k\rVert_2
= 2S_{kk}(g_k-f_k).
\]

Setting this gradient to zero gives \((S+2\gamma\widetilde L)G=SF\).

**The implementation locked at this historical stage still solved Equation (13), with gamma rather than 2 gamma.** Its fixed point corresponds to Equation (8) with a half-gamma graph coefficient. On n=6, c=2, chain W, gamma=0.8, and seed 1, independent CVXPY 1.9.3 / CLARABEL solves gave agreement with the half-gamma problem: objective about 3.844 and maximum difference about 2e-5. The same G had printed Equation (8) value about 4.537, versus its optimum about 4.021. These are not equivalent targets.

The frozen-S/L Equation (12) quadratic was independently checked with numpy.linalg.solve and scipy.optimize L-BFGS-B, agreeing with the sparse solve. That checks Equation (12), not Equation (8).

## Monitored quantities

Each iteration records:

- `equation8_objective`: the original norm objective without epsilon.
- `sqrt_smoothed_equation8_objective`: replaces each norm with \(\sqrt{\lVert v\rVert_2^2+\varepsilon^2}\). This smooth objective, the unsmoothed norm, and the floored denominator \(\max(\lVert v\rVert_2,\varepsilon)\) are distinct.

Historical linear residuals use frozen S and L in \(\lVert(S+\gamma\widetilde L)G-SF\rVert_F\). `fixed_point_residual` rebuilds these at final G. When edge lengths reach epsilon, the latter can be much larger because reweighted W is sensitive to distance.

The paper does not state a stopping rule. The implementation uses \(\lVert G_{t+1}-G_t\rVert_F\le\mathrm{tol}(1+\lVert G_t\rVert_F)\), default tol=1e-6 and max_iter=100. Nonsmooth reweighting can jitter at steps of order 1e-8; reducing tolerance to 1e-12 need not yield a convergence flag even when the rebuilt residual is small.

## Bandwidth, symmetrization, and K-means

The paper does not specify delta. The reproduction uses the median positive directed k-neighbor squared distance as delta squared, falling back to 1 when no positive distance exists. The raw-feature and spectral graphs each calculate their own scale.

The paper does not specify symmetrization. The implementation uses union support: either directed neighbor relation creates an edge, with Gaussian weight and zero diagonal. Ties prefer lower indices. n<=1500 uses stable full sorting; larger inputs use blocked argpartition, whose boundary ties may differ.

Final K-means uses G, Lloyd updates, explicit n_init and random_state, and the library default k-means++. Output labels do not modify W, F, or G. The 50 repetitions belong to the experiment protocol; the method default n_init=10 remains caller-adjustable.

Eigenvector signs are fixed by making the largest-magnitude entry in each column positive. This removes sign freedom without changing the subspace; rotations within repeated eigenspaces remain nonunique.