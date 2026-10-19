# Spectral shrunk clustering

Chang, Nie, Ma, Yang, and Zhou, AAAI 2015, *A Convex Formulation for Spectral Shrunk Clustering*. This package is the original method only. Extensions, baselines, and experiment protocols live elsewhere.

Samples are rows, shape `(n_samples, n_features)`. Algorithm 1 writes \(X\in\mathbb{R}^{d\times n}\). Equation (13) does not multiply by \(X\).

## What the solver does

1. Build a symmetric \(k\)-NN Gaussian graph on the features and take the \(c\) eigenvectors for the smallest eigenvalues of the symmetric normalized Laplacian, Equation (4). Default \(k=5\). This is not PCA.
2. Build a second \(k\)-NN Gaussian graph \(W\) on that embedding \(F\).
3. Iterate Equation (13), \(G=(S+\gamma\widetilde L)^{-1}SF\), with a sparse symmetric solve (`scipy.sparse.linalg.spsolve`). No explicit inverse. \(\widetilde W\) and \(\widetilde L\) are recomputed from the current \(G\). Algorithm 1 line 10 is not implemented.
4. Run K-means on \(G\). Those labels are an output. They are not used to build \(W\), \(F\), or \(G\).

\(S\) is the \(n\times n\) diagonal with \(S_{ii}=1/(2\max(\lVert h_i\rVert_2,\varepsilon))\), where \(h_i\) is row \(i\) of \(G-F\). The paper's embedding-dimension diagonal is dimensionally inconsistent with the trace in Equation (9).

## Assumptions recorded as such

- \(G_0=F\). The paper does not specify the start. Equation (10) divides by zero there, so the first all-zero residual uses the median pairwise row distance as its denominator scale. Later iterations use `eps` (default `1e-8`). Passing `zero_residual_floor="eps"` stays at \(F\).
- \(\delta^2\) is the median of the positive directed \(k\)-NN squared distances on that graph. The feature graph and the embedding graph each have their own median.
- Undirected edges are the union of the two directed \(k\)-NN relations.
- Equation (13) is implemented as printed. Its fixed point matches Equation (8) with the graph term multiplied by \(1/2\), not the printed Equation (8). The audit in `docs/ssc_mathematical_audit.md` has the factor check.
- History key `equation8_objective` is the unsmoothed Equation (8). `sqrt_smoothed_equation8_objective` replaces every Euclidean norm by \(\sqrt{\lVert v\rVert_2^2+\varepsilon^2}\). Those two functions and the denominator floor are different.

`gamma=1` is the constructor default, not a claim that every dataset should use it.

## Use

From the `v1` directory:

```python
from SSC_method import SpectralShrunkClustering

model = SpectralShrunkClustering(n_clusters=3, gamma=1.0, k=5, kmeans_random_state=0)
labels = model.fit_predict(X)  # X has one sample per row
# model.embedding_ is F, model.shrunk_ is G, model.affinity_ is W
# model.objective_history_ records Equation (8) and the smoothed objective
```

The library does not read data files, so it has no filesystem paths.
