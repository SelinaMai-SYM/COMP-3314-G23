# Methods

This project studies Spectral Shrunk Clustering (SSC), its numerical solution,
and the relationship between graph refinement and clustering accuracy. The
implementation follows [Chang et al., AAAI 2015](https://doi.org/10.1609/aaai.v29i1.9606).
SSC denotes **Spectral Shrunk Clustering** here. It is distinct from sparse
subspace clustering.

The [experimental protocol](experimental_protocol.md) defines the evaluated
settings. [Results](results.md) and the [benchmark tables](../results/submission_refresh/per_benchmark/)
report measurements and qualifications.

## Two graphs, two representations

Samples are rows of a matrix \(X\). An input-space affinity \(A\) defines the
normalized Laplacian

\[
L_A=I-D_A^{-1/2}AD_A^{-1/2}.
\]

The eigenvectors associated with its \(K\) smallest eigenvalues form the
spectral representation \(F\), where \(K\) is the benchmark class count. A
second graph \(W\), constructed from \(F\), controls shrinkage. Matched spectral
clustering (SC) clusters \(F\); SSC clusters the refined representation \(G\).
The [editable method diagram](../report/figures/ssc_two_graph_pipeline.tikz)
illustrates these roles.

The standard graph uses five nearest neighbors, zero diagonal and union
symmetrization. Gaussian weights are
\(\exp(-\|x_i-x_j\|^2/\delta^2)\), with \(\delta^2\) equal to the median positive
directed-neighbor squared distance. This convention has no additional factor
of two in the Gaussian denominator. Input and embedding row normalization are
explicit experimental factors.

## SSC objective and parameter convention

For one stored copy of each undirected edge, let \(B\) be the incidence matrix.
The unsquared-fidelity objective corresponding to Equation 8 is

\[
P(G)=\sum_i\|g_i-f_i\|_2+
2\gamma\sum_e w_e\|(BG)_e\|_2.
\]

The coefficient two reproduces the paper's ordered-pair sum. For fixed \(F,W\)
and nonnegative weights this objective is convex. Unsquared fidelity does not
ensure uniqueness, and an optimal representation does not guarantee better
K-means labels.

The E8 IRLS system uses \(S+2\gamma\widetilde L\). The printed Equation 13 system
uses \(S+\gamma\widetilde L\), so E13 at nominal \(\gamma\) corresponds to E8 at
effective \(\gamma/2\). Both nominal and effective values accompany the results.
Finite historical-style IRLS outputs and certified convex solves are separate
statistical tracks.

## Primal–dual certification

For \(c_e=2\gamma w_e\), a dual variable satisfying

\[
\|q_e\|_2\le c_e,\qquad \|(B^Tq)_i\|_2\le1
\]

gives the lower bound \(D(q)=\langle B^Tq,F\rangle\). The reported relative gap is

\[
\frac{P(G)-D(q)}{\max(1,|P(G)|,|D(q)|)}.
\]

Certification requires relative gap at most \(10^{-5}\) and edge/node capacity
violations at most \(10^{-8}\). The solver retains feasible initial dual bounds.
Its diagonal formulation uses \(K=\operatorname{diag}(\sqrt w)B\); transformed
duals are mapped back to original capacities before evaluating the bound.
This is a problem-specific implementation of the primal–dual approach of
[Chambolle and Pock](https://doi.org/10.1007/s10851-010-0251-1).

An iterate stopping condition, agreement between solvers, or a low objective
alone is not a certificate. A certificate applies to the specified saved point,
objective and graph. Matching input representations does not certify a different
output. A failed dual-flow construction is a numerical limitation of that
construction, not proof that no feasible certificate exists.

## Graph diagnostics and interventions

The diagnostics distinguish incorrect relations from missing within-class
connectivity. Edge contamination is reported both by edge count and by weight.
Class fragmentation uses connected components of each true class's induced
subgraph, including isolates, excess components and largest-component fractions.
Whole-graph connectivity is reported separately.

The factorial geometry experiment crosses the original anchor \(F_0\) and its
row-normalized form \(U\) with the original graph \(W_0\) and an angular-neighbor
graph \(W_a\). Graphs are matched to the original undirected weight mass.
Consequently, normalization gains can be distinguished from additional
shrinkage gains under the declared settings.

Oracle deletion and completion use true labels solely as diagnostic
interventions. Candidate additions are drawn from a pool constructed without
labels. The controls distinguish selective deletion, additional within-class
paths, blind additions and fully randomized edits. Oracle performance measures
information available in that pool; it is not an unsupervised algorithm result.

## Baseline implementations

The project includes explicitly named reconstructions of K-means, SC, PCA
baselines, LDA-Kmeans, locally linear clustering and one-shot SLPS. SLPS follows
[Hou et al.](https://doi.org/10.1016/j.ipm.2013.01.004); its paired experiments
separate neighbor count, alpha, dimension and rounding initialization.

The LDA reference is an observed port of the
[pinned ClustPy implementation](https://github.com/collinleiber/ClustPy/blob/4ac9d00685efc7432800684f5bfac0f01af59172/clustpy/centroid/ldakmeans.py)
of [Ding–Li LDA-Kmeans](https://doi.org/10.1145/1273496.1273562). It preserves
failed-update behavior and distinguishes the projection actually clustered
from the source-returned projection. Scoped seeding makes the source PCA
deterministic. The original source and
[BSD-3-Clause notice](../baselines/lda_kmeans/vendor/clustpy/LICENSE) are retained.

The separately named PCA-preconditioned ridge LDA-Kmeans → SC adaptation uses
centered float64 input, SVD rank tolerance
\(\epsilon\max(n,p)\sigma_{\max}\),
\(p_0=\min(100,p,n-K,\operatorname{rank}(X_c))\), and
\(r=\min(K-1,p_0)\). Covariance scatter is divided by \(n-1\), and
\(\eta=10^{-6}\operatorname{tr}(S_t)/p_0\). Inner K-means uses ten starts; the outer
limit is 300, with partition-equivalence stopping. Downstream SC and raw/PCA
controls use one RANDOM Lloyd start per matched external seed. This adaptation
does not establish the identity of the paper's historical LDA-SC method.

## Independent convex refinements

The [three registered refinements](extension_verification_plan.md) preserve the
unsquared fidelity and frozen W0. E1 replaces edge fusion with a relative stopping
tube. E2 restricts motion to fixed tangent planes around unit anchors. E3 adds
frozen unit-gradient relative-neighbor hinges. Their modules are independent and
their fit interfaces accept no labels. Their [objectives, duals and bounds](extension_verification_theory.md)
state exactly what numerical certification establishes.

For example, E1 accepts an anchor matrix and its fixed sparse graph:

```python
from method_extension.extension_verification.relative_stopping import solve_relative

fit = solve_relative(H, W0, gamma, eta=0.25, max_iter=30000, cpu_limit=1800)
G = fit["G"]
```

The registered campaign records optimized G and the actual panel-specific Q,
then applies the common rounding protocol. E1 has no performance promotion gate;
E2 and E3 require their separate development mechanisms to pass before formal
eight-input optimization. Inactive, uncertified, failed, gated and unrun endpoints
remain distinct in the [results](extension_verification_results.md).
