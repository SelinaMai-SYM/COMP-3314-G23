# Locally linear clustering

This implementation follows Wu and Schölkopf's
[*A Local Learning Approach for Clustering*, NeurIPS 2006](https://proceedings.neurips.cc/paper_files/paper/2006/file/366f0bc7bd1d4bf414073cabbadfdfcd-Paper.pdf).
It constructs a local-regression operator and uses Yu–Shi discretization.
It is distinct from SSC's affinity Laplacian and from the different
Yang et al. local-learning construction also cited by Chang et al.

## Mathematical procedure

Local kernel-ridge coefficients satisfy
\(\alpha_i^T=k_i^T(K_i+\lambda I)^{-1}\). Assemble them into the neighbor
regression matrix \(A_{\mathrm{loc}}\), then form

\[
T=(I-A_{\mathrm{loc}})^T(I-A_{\mathrm{loc}}).
\]

Take its \(K\) smallest eigenvectors, row-normalize, and discretize by
orthogonal Procrustes. Gaussian weights use
\(\exp(-\|x_i-x_j\|^2/\gamma)\), with denominator \(\gamma\), not
\(\gamma^2\); a cosine-kernel alternative is explicit.

For target indicator matrix \(Y\) and embedding \(P\), the rotation minimizes
\(\|Y-PR\|_F\), subject to \(R^TR=I\). If
\(Y^TP=U\Sigma V^T\), the update is \(R=VU^T\). In NumPy notation this is
`Vt.T @ U.T`. `yu_shi_discretize_state` exposes the actual rotation,
partition, objective and convergence information.

## API and conventions

```python
from baselines.llc import fit_predict

labels = fit_predict(X, n_clusters=3, random_state=0)
```

Defaults are `n_neighbors=5`, `reg=1.0` and `kernel="gaussian"`.
When `gamma=None`, the bandwidth is the squared mean row Euclidean norm,
with gamma one used if that scale is zero. Five neighbors follow the SSC
comparison convention; they do not reproduce Wu–Schölkopf's own
neighbor/regularization/bandwidth search. Its published neighbor grid is
`{5,10,20,40,80}` and ridge grid is `{0.1,1,1.5}`.

The embedding has a dense eigensolver branch and a sparse matrix-free
ARPACK branch for the same \(T\). This is not a landmark approximation.
The selected backend and any unsuccessful attempt remain explicit in the
results. The MSRA dense result is distinguished from its failed sparse
attempt. The random seed controls the discretizer's rotation initialization.

## Limits of reconstruction

The exact LLC parameters and local-learning variant used in the SSC paper
are unpublished. This package does not silently substitute the Yang et al.
operator. Higher ACC alone cannot resolve that method identity. Historical
measurements preceding the corrected Procrustes orientation remain separately
identified rather than being treated as current outputs.

See [methods](../../docs/methods.md), [results](../../docs/results.md),
[theory](../../docs/theory.md) and
[reproducibility](../../docs/reproducibility.md).
