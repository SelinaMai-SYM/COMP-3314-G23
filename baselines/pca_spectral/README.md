# PCA followed by spectral clustering

This named baseline applies centered, unwhitened full-SVD PCA, then
[spectral clustering](../spectral_clustering/README.md) in the projected
coordinates. The spectral stage uses the shared normalized-Laplacian path.

```python
from baselines.pca_spectral import fit_predict

labels = fit_predict(X, n_clusters=3, random_state=0, n_components=10)
```

`n_components` is required and must not exceed
`min(n_samples, n_features)`. The fitter does not search dimensions or
silently clip the request. Default spectral settings are five neighbors,
Gaussian weighting and union symmetrization. K-means uses one RANDOM Lloyd
start, 300 iterations and tolerance `1e-4`.

The pipeline reconstructs the PCA–SC comparison named by
[Chang et al.](https://doi.org/10.1609/aaai.v29i1.9606).
The paper's unpublished selected dimension and incomplete graph conventions
remain limitations. A dimension search and its label-assisted selection are
experimental procedures, not part of this single-configuration API.

Source membership, preprocessing and graph settings accompany every measured
result. See [methods](../../docs/methods.md),
[theory](../../docs/theory.md), [results](../../docs/results.md) and
[reproducibility](../../docs/reproducibility.md).
