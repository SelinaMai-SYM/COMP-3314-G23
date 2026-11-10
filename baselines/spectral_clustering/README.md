# Spectral clustering

This baseline uses the symmetric normalized Laplacian of
[Chang et al., Equation 4](https://doi.org/10.1609/aaai.v29i1.9606),
with the normalized-cut context of
[Shi and Malik](https://doi.org/10.1109/34.868688).

For affinity \(A\), form \(L=I-D^{-1/2}AD^{-1/2}\), take the \(K\) smallest
eigenvectors as \(F\), and cluster its rows. Graph construction, eigensolve
and sign conventions are shared with [SSC_method](../../SSC_method/README.md).
A shrinkage comparison must use exactly the same saved \(F\), rather than
a separately generated embedding.

```python
from baselines.spectral_clustering import fit_predict, spectral_embedding

F = spectral_embedding(X, n_clusters=3, n_neighbors=5)
labels = fit_predict(X, n_clusters=3, random_state=0)
```

## Explicit conventions

- Default graph: five-neighbor Gaussian affinity, zero diagonal and union
  symmetrization.
- Gaussian weight: \(\exp(-\|x_i-x_j\|^2/\delta^2)\). When unspecified,
  \(\delta^2\) is the median positive directed-neighbor squared distance.
- The shared graph configuration records neighbor construction, bandwidth,
  Laplacian, eigensolver and the largest-magnitude-positive column-sign rule.
- Embedding row normalization is off by default. Passing
  `row_normalize=True` defines the separately evaluated normalized anchor.
- Rounding defaults to one RANDOM Lloyd start, 300 iterations and tolerance
  `1e-4`. It is independent of the eigensolver's numerical stopping criteria.

Bandwidth selection, symmetrization and rounding details are reconstruction
assumptions where the paper is incomplete. Input normalization, source
resolution and sample membership can change \(F\), so numerical agreement
alone does not identify the historical setting. Row normalization gains must
be separated from additional SSC shrinkage gains.

LLC uses a different local-learning operator and is documented in its
[own package](../llc/README.md). See [methods](../../docs/methods.md),
[theory](../../docs/theory.md), [results](../../docs/results.md) and
[reproducibility](../../docs/reproducibility.md).
