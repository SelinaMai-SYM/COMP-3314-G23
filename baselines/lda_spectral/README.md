# Approximate LDA–spectral constructions

[Chang et al.](https://doi.org/10.1609/aaai.v29i1.9606) name an LDA–SC
baseline without specifying its algorithm. [Ding and Li](https://doi.org/10.1145/1273496.1273562)
describe LDA-Kmeans, which does not uniquely determine an LDA–SC pipeline.
This package therefore exposes two explicitly approximate interpretations.

| API | Construction |
|---|---|
| `fit_predict` | PCA initialization, then alternating spectral partitions and LDA updates based on those partitions |
| `fit_predict_oneshot` | PCA initialization, one spectral partition, one LDA update, then one spectral partition in the learned subspace |

```python
from baselines.lda_spectral import fit_predict, fit_predict_oneshot

labels = fit_predict(X, n_clusters=3, random_state=0, n_components=2)
oneshot = fit_predict_oneshot(X, n_clusters=3, random_state=0, n_components=2)
```

Both APIs require `n_components`, with at most \(K-1\) LDA directions and
valid feature dimensions. Singular scatter and limited numerical rank remain
explicit limitations. Ground-truth `y` is rejected.
The LDA scatter matrices use current predicted cluster labels. The alternating
variant defaults to at most 30 updates; `fit_predict_oneshot` rejects
`max_iter` because it has only one LDA update. The spectral stage inherits
the explicit graph and rounding conventions of the
[spectral baseline](../spectral_clustering/README.md).

These constructions optimize their stated alternations; they are not
recovered historical LDA–SC algorithms. A closer ACC/NMI match cannot promote
them into an exact reproduction. Singular scatter, rank limitations and
unpublished subspace choices remain substantive limitations.

The separately named PCA-preconditioned ridge LDA-Kmeans → SC adaptation is
documented in [lda_kmeans](../lda_kmeans/README.md) and is distinct from both
interpretations here. See [methods](../../docs/methods.md),
[results](../../docs/results.md) and
[reproducibility](../../docs/reproducibility.md).
