# E3 — Optimization versus clustering accuracy

Convexity applies to G with F and W fixed and W nonnegative. It does not apply to the spectral embedding or to K-means. This note does not add a proof. It re-runs the existing small-graph check and extends three saved solves.

## What E8 and E13 are

Printed Equation (8) is `||G−F||_{2,1} + γ Σ_{i,j} W_ij ||g_i−g_j||_2`. Printed Equation (13) is `G = (S + γ L̃)^{-1} S F`. Differentiating Equation (8) when both ordered pairs of a symmetric W are stored produces a factor 2 on `γ L̃`. That linear system is variant E8 (`A = S + 2γ L̃`). Variant E13 keeps the printed factor 1. E13 is the stationary system of Equation (8) with the graph coefficient halved, not of Equation (8) at the printed γ.

Algorithm 1 line 10 in the AAAI paper is `G ← (S + γ W̃)^{-1} S X`. It uses X and W̃, not F and L̃. This code does not implement that line. A pass of the CVXPY check is not a proof that line 10 is correct, and it is not a proof that the authors' unreleased code used E8.

The ordered-pair sum is the same convention as E2: both triangles are stored, and the objective adds each stored entry once.

## Small graph

`tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term` was re-run (`results/final_round/E3_pytest_cvxpy.txt`, pytest return code 0).

The same n = 6 chain, γ = 0.8, seed 1, was solved in-process with CLARABEL:

| Variant | CVXPY graph coefficient | CVXPY status | max \|G − G_cvxpy\| | objective gap |
| --- | --- | --- | --- | --- |
| E13 | γ/2 | optimal | 2.33e-5 | 1.6e-8 |
| E8 | γ | optimal | 1.17e-5 | 2.0e-8 |

CONFIRMED as a numerical check on this instance, not as a new theorem: E13 tracks the halved graph term and E8 tracks the printed γ. A small IRLS step is not the certificate. The certificate here is the solver status plus the objective gap.

## Real data

F is the saved embedding. W is rebuilt and checked as in E2. Fresh `shrink_embedding(..., variant="E8", max_iter=budget)` from `G_0 = F`. Budget 300 matches the saved G with max absolute error 0.

| Case | Budget | Iterations actually run | Step rule | Eq. (8) | Fixed-point residual | ACC mean |
| --- | --- | --- | --- | --- | --- | --- |
| ORL γ = 1 | 300 | 300 | not met | 14.58274942 | 0.01310 | 0.57265 |
| ORL γ = 1 | 1000 and 2000 | 825 | met | 14.58272412 | 0.00213 | 0.57135 |
| YaleB γ = 1 | 300 | 300 | not met | 50.67685228 | 0.19422 | 0.17622 |
| YaleB γ = 1 | 1000 and 2000 | 359 | met | 50.67683885 | 0.17098 | 0.17614 |
| USPS γ = 1000 | 300 | 300 | not met | 179.83482261 | 0.11880 | 0.73687 |
| USPS γ = 1000 | 1000 and 2000 | 355 | met | 179.83481634 | 0.05776 | 0.73861 |

Source F runs: ORL `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41`, YaleB `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff`, USPS `20261021_225950__STRICT_PAPER__USPS__SSC_E8_G1E3__e8aad5e1`. New G and histories: `runs/final_round/E3/`. Budgets 1000 and 2000 return the same G (identical SHA-256) because the relative-step rule already fired. No longer saved run existed before this round; these solves are new and were required.

The step rule is `||ΔG|| ≤ 1e-6 (1 + ||G||)`. Meeting it is not a dual certificate. After the rule fires, the rebuilt residual `||(S + 2γ L̃) G − S F||` is still 0.002 (ORL), 0.171 (YaleB), and 0.058 (USPS). Those residuals were not driven to the 1e-5 scale of the n = 6 check. UNRESOLVED: whether these real-data points are global minimizers of Equation (8). What is measured is that extra IRLS iterations past 300 change the recorded objective by 2.5e-5 (ORL), 1.3e-5 (YaleB), and 6e-6 (USPS).

ACC uses the same explicit random Lloyd settings and seeds 0..49, computed separately from the objective.

SUPPORTED: reaching the step rule does not raise ACC in any substantial way on these three cases. ORL ACC moves from 0.57265 to 0.57135 (down). YaleB moves by less than 0.0001. USPS γ = 1000 moves from 0.73687 to 0.73861. The USPS gain from γ = 1000 over γ = 1 (E2: 0.617 to 0.737) is already present at the unconverged 300-step G. It is not produced by the extra 55 iterations.

Figure: `results/final_round/E3_convergence_figure.pdf` plots the Eq. (8) column, not the quadratic surrogate.
