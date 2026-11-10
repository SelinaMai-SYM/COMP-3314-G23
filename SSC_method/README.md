# Spectral Shrunk Clustering

This package reconstructs Chang, Nie, Ma, Yang and Zhou,
[*A Convex Formulation for Spectral Shrunk Clustering*](https://doi.org/10.1609/aaai.v29i1.9606),
AAAI 2015. SSC means **Spectral Shrunk Clustering** here. It is distinct
from sparse subspace clustering and from the EnSC graph adaptation.

The API stores samples as rows, `X.shape == (n_samples, n_features)`.
It operates on arrays; no local paper PDF or benchmark path is required.
See [methods](../docs/methods.md), [theory](../docs/theory.md) and
[reproducibility](../docs/reproducibility.md) for the complete scientific
conventions and experiment interfaces.

## Two graphs and the paper-to-code map

An affinity \(A\) on input features defines
\(L_n=I-D^{-1/2}AD^{-1/2}\). Its \(K\) smallest eigenvectors form \(F\).
A separate affinity \(W\) on \(F\) controls refinement to \(G\). Matched
spectral clustering clusters exactly that same \(F\); SSC clusters \(G\).

| Paper object | Implementation | Convention |
|---|---|---|
| Input affinity \(A\) | `graph_construction.knn_affinity` | Gaussian five-neighbor graph, union symmetrization |
| Equation 4 Laplacian | `graph_construction.symmetric_normalized_laplacian` | Isolated rows use \(D^{-1/2}=0\), leaving the corresponding identity row |
| Spectral representation \(F\) | `spectral_embedding.spectral_embedding` | Smallest eigenvectors; largest-magnitude-positive column signs; no default row normalization |
| Fusion graph \(W\) | A second `knn_affinity` call on \(F\) | Fixed during the SSC objective; independently computed bandwidth |
| Equation 8 objective | `objective.equation8_objective` | Unsquared row fidelity and ordered-pair graph norm |
| Fidelity reweighting \(S\) | `objective.row_l21_diagonal` | An \(n\times n\) diagonal, consistent with the trace surrogate |
| Graph reweighting | `objective.reweighted_affinity` / `shrinkage_laplacian` | Rebuilt from the current \(G\); combinatorial reweighted Laplacian |
| E8/E13 linear systems | `optimizer.shrink_embedding` | Sparse linear solve, not an explicit inverse |
| Final partition | `SpectralShrunkClustering` | Explicit K-means settings; no true labels used |

The paper's printed length-\(K\) fidelity diagonal is dimensionally
incompatible with its trace expression. The implementation uses one
fidelity weight per sample. Algorithm 1's printed update involving
\(\widetilde W\) and \(X\) is not substituted for the Laplacian update
anchored at \(F\).

## E8 and E13 are different parameter conventions

For a symmetric graph stored once per undirected edge, Equation 8 is

\[
P(G)=\sum_i\|g_i-f_i\|_2+
2\gamma\sum_e w_e\|(BG)_e\|_2.
\]

| Variant | IRLS system | Meaning |
|---|---|---|
| `E13` | \((S+\gamma\widetilde L)G=SF\) | Printed Equation 13; library default |
| `E8` | \((S+2\gamma\widetilde L)G=SF\) | Stationary system for the printed ordered-pair Equation 8 |

E13 at nominal gamma targets E8 at effective gamma/2. E8 is a documented
paper-based derivation, not a claim to recover the authors' unavailable
software. Objective histories distinguish the nonsmooth target,
square-root smoothing, frozen IRLS quadratic and fixed-point residual.

## Single-model API

```python
from SSC_method import SpectralShrunkClustering

model = SpectralShrunkClustering(
    n_clusters=3, gamma=1.0, k=5, variant="E8",
    kmeans_init="random", kmeans_n_init=1, kmeans_random_state=0,
)
labels = model.fit_predict(X)
F = model.embedding_
G = model.shrunk_
W = model.affinity_
```

The constructor defaults preserve `variant="E13"`, `max_iter=100`,
`tol=1e-6`, `eps=1e-8`, initial `G=F`, greedy sklearn
`k-means++` and ten K-means starts. These are library defaults, not
the complete experimental protocol. The reproduction adapters pass their
declared settings explicitly, including the 300-update historical IRLS cap
and separate rounding seeds.

`SpectralGraphConfig` records graph and embedding assumptions. Omitted
bandwidth uses the median **positive directed-neighbor squared distance**;
weights are \(\exp(-\|x_i-x_j\|^2/\delta^2)\), without an extra factor two
in the denominator. Union symmetrization, eigenvector signs and absent row
normalization are explicit choices. Neighbor-boundary ties and eigensolver
backends remain relevant numerical conventions. The initial all-zero
residual uses the declared median-pairwise floor; later denominator floors
use epsilon. Gamma one is an API default, not a universal parameter rule.

## Solver qualification and limitations

IRLS convergence or a small monitored objective is not a primal–dual
certificate. The separate
[certified solver](../method_extension/next_round/README.md) provides
feasible graph duals and objective-specific gaps. Its certificate applies
to the specified saved \(G,F,W\) and target; it cannot be transferred to a
different output.

Convexity holds for fixed nonnegative \(W\), but the unsquared fidelity
does not ensure uniqueness. Neither optimality nor representation
movement guarantees higher ACC/NMI. Source membership, preprocessing,
normalization, parameters and rounding must be matched before attributing
a gain to shrinkage. Qualified measurements are reported in
[results](../docs/results.md) and the
[experimental protocol](../docs/experimental_protocol.md).
