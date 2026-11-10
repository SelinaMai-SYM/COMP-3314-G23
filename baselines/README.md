# Clustering baselines

The baseline packages provide explicit reconstructions and named adaptations
for the comparison in [Chang et al., AAAI 2015](https://doi.org/10.1609/aaai.v29i1.9606).
They operate on finite arrays with samples as rows. Library calls fit one
specified configuration; parameter search, repeated seeds and statistical
selection belong to the [experimental protocol](../docs/experimental_protocol.md).

Most packages expose:

```python
labels = fit_predict(X, n_clusters, random_state, **params)
```

`X` has shape `(n_samples, n_features)`, `random_state` is an integer, and
returned labels have shape `(n_samples,)`. True class labels are not fitting
arguments. Dimension choices are explicit; fitters do not search the paper's
reported dimension range internally.

| Method | Package | Implementation and scope |
|---|---|---|
| K-means | [kmeans](kmeans/README.md) | sklearn Lloyd with explicit initialization and restart settings |
| Spectral clustering | [spectral_clustering](spectral_clustering/README.md) | Shared Equation 4 graph, Laplacian and embedding with SSC |
| PCA–K-means | [pca_kmeans](pca_kmeans/README.md) | Centered full-SVD PCA followed by K-means |
| PCA–SC | [pca_spectral](pca_spectral/README.md) | PCA followed by the explicit spectral baseline |
| LDA-Kmeans | [lda_kmeans](lda_kmeans/README.md) | Existing reconstruction, pinned ClustPy reference, and separately named ridge adaptation |
| LDA–SC interpretations | [lda_spectral](lda_spectral/README.md) | Two approximate constructions; the paper does not specify an exact historical LDA–SC algorithm |
| Locally linear clustering | [llc](llc/README.md) | Wu–Schölkopf local regression and Yu–Shi discretization |
| One-shot SLPS | [spls](spls/README.md) | Hou et al.'s pattern shrinkage, PCA and K-means; package name `spls` is retained |

## Parameters and interpretation

The standard K-means wrapper defaults to RANDOM initialization, one Lloyd
start, 300 iterations and tolerance `1e-4`. Greedy K-means++, vanilla
K-means++, best-objective selection and means over 50 seeds are distinct
experimental settings, not interchangeable library defaults.

PCA methods require `n_components`. LDA directions are limited by the class
count, with additional rank constraints; the ridge adaptation declares its
own dimension rule. The spectral Gaussian bandwidth, symmetrization and row
normalization are explicit reconstruction choices. LLC uses its own
local-regression operator, rather than SSC's affinity Laplacian.

An implemented formula does not establish that the unpublished settings,
source samples or original software were recovered. In particular, the
approximate LDA–SC constructions and ridge LDA-to-SC adaptation do not fill
an exact historical LDA–SC identity. Failed fits and incomplete seed sets
remain visible, and inertia across different learned subspaces is not a
common best-of-50 objective.

See [methods](../docs/methods.md), [theory](../docs/theory.md),
[results](../docs/results.md) and [reproducibility](../docs/reproducibility.md)
for derivations, qualified measurements and validation commands. Third-party
ClustPy source retains its [BSD-3-Clause license](lda_kmeans/vendor/clustpy/LICENSE).
