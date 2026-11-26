# Methods

## Original SSC

SSC means **Spectral Shrunk Clustering**. Its two graphs have distinct roles:
`X → A → F → W → G → K-means`. The input graph A defines
$L_A=I-D_A^{-1/2}AD_A^{-1/2}$; its smallest eigenvectors give F. W is rebuilt
on F and stays fixed throughout refinement. Matched SC rounds the same F.

The standard reconstruction uses union k-nearest neighbors, k=5, Gaussian
weights with bandwidth equal to the median positive directed-neighbor squared
distance, no self-edges and the declared Y0–Y3 preparation. The eigensolver
initialization and eigenvector ordering are explicit in
[`spectral_embedding.py`](../SSC_method/spectral_embedding.py).

With each undirected edge stored once in C, the original target is

$$P(G)=\sum_i\|g_i-f_i\|_2+2\gamma\sum_e w_e\|(CG)_e\|_2.$$

[`objective.py`](../SSC_method/objective.py) computes Equation 8 and the IRLS
weights S and reweighted graph. E8 solves
$(S+2\gamma\widetilde L)G=SF$; E13 solves the printed
$(S+\gamma\widetilde L)G=SF$. With identical counting and reweighting, E13's
nominal gamma has E8 effective gamma/2. The original unsquared problem is convex
for fixed F/W, but need not have a unique optimizer or improve clustering.

[`shrink_embedding`](../SSC_method/optimizer.py) uses sparse solves. Denominator
floors regularize zero residuals; `median_pairwise` initializes the all-zero
fidelity residual using an explicit nonzero floor. Iterate stopping, solver
agreement and a feasible primal–dual gap are separate numerical statuses.
The [core estimator](../SSC_method/ssc.py) retains historical defaults (including
E13); experiment configurations explicitly select E8/E13 and rounding.

## Metrics and baselines

[`benchmarks.metrics`](../benchmarks/metrics/) implements Hungarian label-matched
ACC and geometric-entropy NMI. Both use the same predicted partition. Metric
functions return fractions; released tables multiply by 100. K-means uses
Lloyd updates with explicit RANDOM, vanilla++ or greedy++ initialization.

The [baseline package](../baselines/) includes K-means, SC, PCA→K-means,
PCA→SC, LDA-Kmeans, LLC and SPLS. The separately named ridge
LDA-Kmeans→SC adaptation is not a recovered historical LDA-SC implementation.
Its source/projection and failed-update qualifications are retained in the
[baseline measurements](../results/submission_refresh/baseline_diagnostics.csv).

## Selected quadratic refinements

E7, E1_v3 and E5_v2 share one frozen anchor F and graph W. They are independent
alternatives using quadratic fidelity, with QSSC as their base:

$$J_Q(G)=\tfrac12\|G-F\|_F^2+\lambda\sum_e w_e\|(CG)_e\|_2.$$

At fixed pilot strength, a rank-one inverse identity computes the exact
endpoint residual after deleting one pilot edge. Weighted score midranks
allocate edge weights (E7), stopping tubes (E1_v3) or triangle-slack guards
(E5_v2). The [final report figure](figures/extension_pipeline_ppt_6_2.png)
shows these alternatives. A stopping tube is a hinge penalty with zero cost
below its threshold, rather than a hard lower bound on distance.

The [formulation](extension_round3/method_design.md) defines objectives, duals,
proximal updates and qualification. The [protocol](extension_round3/experiment_protocol.md)
defines movement matching, controls and both rounding panels. Plain-pilot
controls keep the intervention while omitting the edge-deletion correction.

The [development summary](development_summary.md) records the earlier E1–E7
comparisons displayed in the presentation, including failed promotion gates.
Their code remains only where it supplies these measurements or shared
numerical infrastructure. See [theory](theory.md) for numerical certificates.
