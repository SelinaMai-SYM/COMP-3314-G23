# One-shot SLPS: subspace learning by pattern shrinking

This package implements the one-shot procedure of Hou, Nie, Jiao, Zhang and
Wu, [*Learning a Subspace for Clustering via Pattern Shrinking*](https://doi.org/10.1016/j.ipm.2013.01.004),
Information Processing & Management 49(4):871–883, 2013. The package identifier
`spls` is retained for compatibility with the SSC comparison; the method is
called SLPS in the source publication.

## Objective and algorithm

The one-shot \(\beta\to0\) procedure constructs a union nearest-neighbor
graph with Zelnik-Manor local scaling,

\[
W_{ij}=\exp(-\|x_i-x_j\|^2/(\sigma_i\sigma_j)),
\]

then solves Equation 18. With row-oriented data, the code computes

\[
[(1-\alpha)L+\alpha I]Y=\alpha X.
\]

PCA of centered \(Y\) gives the requested embedding, followed by K-means
(the source's PsKm variant). PsNcut is a different pipeline.

| Component | API |
|---|---|
| Local-scale affinity | `local_scaling_affinity` |
| Pattern shrinkage | `oneshot_shrunk_patterns` |
| PCA coordinates | `pca_embedding` |
| Complete PsKm partition | `fit_predict` |

```python
from baselines.spls import fit_predict

labels = fit_predict(X, n_clusters=3, random_state=0,
                     n_components=10, alpha=0.5, n_neighbors=7)
```

`n_components` is required. `alpha` lies in `(0,1]`, and the default
neighbor count is seven. PCA is unwhitened and rejects dimensions above its
declared numerical-rank threshold. Rounding defaults to one RANDOM Lloyd
start, 300 iterations and tolerance `1e-4`. Ground-truth labels are rejected.

## Comparison limits

The source searches alpha and dimension without specifying a label-blind
selection rule. Library calls fit one supplied pair; the current experimental
design reports paired k=5/k=7 controls and explicit parameter grids. Its
50-seed mean/SD endpoint differs from the source's best-of-100 K-means
reporting, and those endpoints are not merged.

The implementation is an independent formula-based reconstruction. It is
available from the code and does not require a local publisher PDF to run.
This does not establish exact numerical reproduction of the SSC paper's
SLPS cells. See [methods](../../docs/methods.md),
[results](../../docs/results.md), [theory](../../docs/theory.md) and
[reproducibility](../../docs/reproducibility.md).
