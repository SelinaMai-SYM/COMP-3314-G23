# LDA-Kmeans and the ridge LDA-to-SC adaptation

The underlying method is [Ding and Li, ICML 2007](https://doi.org/10.1145/1273496.1273562),
*Adaptive Dimension Reduction Using Discriminant Analysis and K-means
Clustering*. It alternates a partition with a discriminative subspace learned
from that partition. Cluster indicators used by LDA are predictions, not
ground-truth labels.

## Existing reconstruction

```python
from baselines.lda_kmeans import fit_predict, fit_state

labels = fit_predict(X, n_clusters=3, random_state=0, n_components=2)
state = fit_state(X, n_clusters=3, random_state=0, n_components=2)
```

The fit centers the input, initializes a PCA subspace and alternates K-means
with the generalized LDA eigenproblem \(S_bu=\lambda S_wu\). Scatter matrices
are computed from current cluster membership. The Euclidean scaling of the
generalized eigenvectors is retained.

`n_components` is required, with at most \(K-1\) directions and the declared
sample/feature limits. Defaults include `max_iter=30`, `sw_reg=1e-8`,
one RANDOM Lloyd start per inner fit, and 300 K-means iterations. The
`sw_reg` safeguard adds a scale-dependent ridge when the within-cluster
scatter is singular or insufficiently positive definite. It is an explicit
numerical reconstruction choice, not a recovered unpublished paper setting.

`fit_state` exposes the projection actually clustered, centering, labels,
centers, objective diagnostics, termination reason and optional trajectory.
Its default literal-label stopping rule preserves the existing behavior;
`permutation_invariant_stop=True` is a named behavioral option.
The default failure policy raises on a failed LDA update. Diagnostic state
collection can retain the failure without representing it as an update.

## Pinned ClustPy reference

`fit_reference_state` observes the
[pinned ClustPy LDAKmeans implementation](https://github.com/collinleiber/ClustPy/blob/4ac9d00685efc7432800684f5bfac0f01af59172/clustpy/centroid/ldakmeans.py),
revision `4ac9d00685efc7432800684f5bfac0f01af59172`. Original source and the
[BSD-3-Clause notice](vendor/clustpy/LICENSE) are retained under `vendor/clustpy`.

The adapter preserves source failures, its mutable inner RNG and any
difference between the source-returned projection and the projection actually
used for labels. It records `projection_used` and `projection_returned`
separately. The source clusters `X @ R` rather than centered `X @ R`.
A scoped NumPy seed makes its otherwise unseeded PCA repeatable, restores the
previous global state and is disclosed as a determinism modification.
Default observation uses one outer fit and ten inner K-means starts.

Observed benchmark failures include fits with no successful LDA update,
identified as PCA–K-means degeneracies. These are implementation observations,
not a theorem that LDA-Kmeans cannot work.

## Separately named ridge adaptation

`prepare_pca` and `fit_adapted_state` implement the
**PCA-preconditioned ridge LDA-Kmeans → SC adaptation**. Centered float64 input
uses the standard rank tolerance
\(\epsilon\max(n,p)\sigma_{\max}\), followed by

\[
p_0=\min(100,p,n-K,\operatorname{rank}(X_c)),\qquad r=\min(K-1,p_0).
\]

Scatter covariance is divided by \(n-1\), and the ridge is
\(\eta=10^{-6}\operatorname{tr}(S_t)/p_0\). The fit uses ten greedy
K-means++ starts per inner partition, a 300-update default and
partition-equivalence stopping. Its state returns the last projection
actually clustered. The downstream SC stage and raw/PCA controls are separate
experiment adapters.

This adaptation is not the paper's unspecified historical LDA–SC baseline.
Inertia across independently learned subspaces is not a common best-of-50
objective; source-native choices are retained only as separately qualified
diagnostics. All mean/SD results require the complete declared external seed
set, including failures rather than successful-seed filtering.

See [methods](../../docs/methods.md),
[results](../../docs/results.md), [limitations](../../docs/limitations.md)
and [reproducibility](../../docs/reproducibility.md).
