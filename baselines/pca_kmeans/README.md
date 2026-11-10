# PCA followed by K-means

This package centers the data, computes full-SVD PCA without whitening,
and runs the explicit [K-means wrapper](../kmeans/README.md) on the projected
coordinates. For centered \(X_c\), the representation is \(Z=X_cV_r\), where
\(V_r\) contains the leading right singular vectors.

```python
from baselines.pca_kmeans import fit_predict

labels = fit_predict(X, n_clusters=3, random_state=0, n_components=10)
```

`n_components` is required and must not exceed
`min(n_samples, n_features)`. It is not silently clipped. PCA uses sklearn
`svd_solver="full"`; the seed is forwarded to K-means. Rounding defaults
are RANDOM initialization, one Lloyd start, 300 iterations and tolerance
`1e-4`.

[Chang et al.](https://doi.org/10.1609/aaai.v29i1.9606) name this baseline
and report a dimension search from 10 to 150, without fully specifying its
step or selected dimensions. This library fits one requested dimension.
The experimental grid and any retrospective selection are reported
separately; a best numerical match does not recover the unpublished choice.

The implementation combines sklearn PCA with the project wrapper, rather
than recovered SSC-author code. See the [baseline index](../README.md),
[methods](../../docs/methods.md), [results](../../docs/results.md) and
[reproducibility](../../docs/reproducibility.md).
