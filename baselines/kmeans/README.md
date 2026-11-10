# K-means

This package wraps sklearn's Lloyd algorithm for the K-means objective

\[
\min_{z,\mu}\sum_i\|x_i-\mu_{z_i}\|_2^2.
\]

`X` stores samples as rows. One call returns a partition:

```python
from baselines.kmeans import fit_predict

labels = fit_predict(X, n_clusters=3, random_state=0)
```

Defaults are `init="random"`, `n_init=1`, `max_iter=300`,
`tol=1e-4` and `algorithm="lloyd"`. The integer seed controls the declared
random initialization. Increasing `n_init` changes the protocol; this
function does not independently reproduce 50 external trials.

The comparison in [Chang et al.](https://doi.org/10.1609/aaai.v29i1.9606)
states random initialization. Greedy/vanilla K-means++ and native
minimum-inertia selection are separately named settings. Minimum inertia
selects one assignment in the same representation, whereas a mean and sample
SD summarize a complete declared seed set. A single selected assignment has
no across-run SD.

The implementation uses third-party sklearn numerical code; it is not
recovered SSC-author software. Current numerical results and their source
restrictions appear in [results](../../docs/results.md), rather than a
hand-maintained package table. See the [baseline index](../README.md),
[methods](../../docs/methods.md) and
[reproducibility](../../docs/reproducibility.md).
