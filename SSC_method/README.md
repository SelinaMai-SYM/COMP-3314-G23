# Spectral shrunk clustering

Chang, Nie, Ma, Yang, and Zhou, AAAI 2015, *A Convex Formulation for Spectral Shrunk Clustering*. This package is the original method only. Extensions, baselines, and experiment protocols live elsewhere.

Samples are rows, shape `(n_samples, n_features)`. Algorithm 1 writes \(X\in\mathbb{R}^{d\times n}\). Equation (13) does not multiply by \(X\).

## Paper-to-code map

Shared knobs live in `SSC_method/spectral_config.py` (`SpectralGraphConfig`). Spectral clustering and SSC use that config for the **same** Equation (4) embedding \(F\). LLC and LDA keep the graphs defined in their own papers.

| Paper object | Code | Default / note |
| --- | --- | --- |
| Eq. (3) \(\min_F \operatorname{Tr}(F^\top L F)\) with \(F=Y(Y^\top Y)^{-1/2}\) | `spectral_embedding.spectral_embedding` takes the \(c\) smallest eigenvectors of \(L_n\) | Not PCA. `eigenvector_selection="smallest"` |
| Eq. (4) \(L_n=I-D^{-1/2}AD^{-1/2}\) | `graph_construction.symmetric_normalized_laplacian` | Isolated vertices use \(D^{-1/2}=0\), so that row of \(L_n\) is \(e_i\) |
| Graph \(A\) on raw features \(X\) | `graph_construction.knn_affinity` | Gaussian \(k\)-NN, \(k=5\), union symmetrization |
| \(A_{ij}=\exp(-\lVert x_i-x_j\rVert^2/\delta^2)\) if \(k\)-NN else 0 | same | \(\delta^2\): median of positive directed \(k\)-NN squared distances when omitted |
| Embedding \(F\in\mathbb{R}^{n\times c}\) | `spectral_embedding_` / `model.embedding_` | Column signs: largest-magnitude entry positive. Row-normalization **off** (Category C) |
| Graph \(W\) on the embedding \(F\) | second `knn_affinity` call, now on rows of \(F\) | Same \(k=5\) union Gaussian rule; **not** the same matrix as \(A\) unless the \(k\)-NN edges happen to coincide. Each graph has its own \(\delta\) |
| Eq. (5)–(7) squared losses | not used as the objective | Replaced in the paper by Eq. (8) |
| Eq. (8) \(\lVert G-F\rVert_{2,1}+\gamma\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) | `objective.equation8_objective` | Ordered-pair sum; both directions of symmetric \(W\) count |
| Eq. (9) \(\operatorname{Tr}((G-F)^\top S(G-F))\) | implied by the IRLS quadratic | Requires \(S\) to be \(n\times n\) |
| Eq. (10) printed as a length-\(c\) diagonal | **not implemented** | Incompatible with Eq. (9). Corrected \(S_{ii}=1/(2\max(\lVert h_i\rVert_2,\varepsilon))\) in `objective.row_l21_diagonal` |
| Eq. (11) \(\widetilde W_{ij}=W_{ij}/(2\lVert g_i-g_j\rVert_2)\) | `objective.reweighted_affinity` / `shrinkage_laplacian` | Combinatorial \(\widetilde L=\widetilde D-\widetilde W\), not Eq. (4) |
| Eq. (12) printed quadratic | `objective.trace_surrogate` | Missing a factor 2 relative to the ordered-pair expansion of Eq. (8); see E8 vs E13 |
| Eq. (13) \(G=(S+\gamma\widetilde L)^{-1}SF\) | `optimizer.shrink_embedding(..., variant="E13")` | Sparse `spsolve`, no explicit inverse. **Default.** Historical call sites stay on E13 |
| Algorithm 1 line 10 \((S_t+\gamma\widetilde W)^{-1}S_t X\) | **not implemented** | \(\widetilde W\) is not \(\widetilde L\); \(X\) is not \(F\) |
| Algorithm 1 line 4 \(\widetilde W\) outside the loop | **not followed** | \(\widetilde W,\widetilde L\) are rebuilt from the current \(G\) every iteration because Eq. (11) depends on \(G\) |
| \(G_0\) | `G_init=F` | Paper writes \(G_0\in\mathbb{R}^{n\times c}\) and does not specify the start |
| K-means on \(G\) | `sklearn.cluster.KMeans` in `ssc.py`; experiment runner uses `init="random"`, `n_init=1` | Labels are evaluation-only. They do not build \(A\), \(W\), \(F\), or \(G\) |

Two graphs are easy to mix up:

- **\(A\)** is built on **\(X\)** and is used only to form \(L_n\) and then \(F\).
- **\(W\)** is built on **\(F\)** and is the frozen shrinkage graph in Eq. (8)/(13).

Evaluating shrinkage against a second, independently computed embedding is invalid. Round 1 already showed K-means(\(F\)) \(\approx\) SSC; \(F\) must be identical before that comparison.

## E8 vs E13

Both linear systems live in `optimizer.py`. Neither is removed.

| Variant | Linear system | What it is | Default |
| --- | --- | --- | --- |
| **E13** | \(A=S+\gamma\widetilde L\) | Printed Equation (13) | Yes. Old call sites that omit `variant` stay here |
| **E8** | \(A=S+2\gamma\widetilde L\) | Ordered-pair stationary point of printed Equation (8) | No. Derived in this reproduction; **not** claimed to be the authors' unreleased code |

E13 is the IRLS fixed point of Equation (8) with the graph term halved. E8 matches the printed Equation (8). They are different problems. History records four separate numbers: the nonsmooth Eq. (8) value, the square-root smoothing, the frozen IRLS quadratic, and the rebuilt fixed-point residual.

## Entrypoints

- **Library / single fit:** `SSC_method/ssc.py` → `SpectralShrunkClustering`. Constructor defaults: `variant="E13"`, `G_0=F`, `kmeans_init="k-means++"`, `kmeans_n_init=10`, `max_iter=100`. Use this to fit one model on an array you already loaded.
- **Experiment runner:** `experiments/methods.py` → `prepare_ssc_family` / `prepare_spectral`. Same Equation (4) path for SC and SSC (`SpectralGraphConfig`). Protocol defaults: `variant="E13"`, `kmeans_init="random"`, `n_init=1`, `max_iter=300`. There is no `n>1500` backend switch.
- **Shared graph / embedding:** `graph_construction.knn_affinity` and `spectral_embedding.spectral_embedding`. `baselines.spectral_clustering` calls these when the math is Eq. (4), \(k=5\), union \(k\)-NN Gaussian.
- **Not this path:** LLC (`baselines/llc`, Wu & Schölkopf local regression) and the LDA step of LDA-SC. Mutual \(k\)-NN as an SSC *method* stays in `method_extension/`.

## Remaining hidden defaults

These are explicit in `SpectralGraphConfig` but are still reproduction assumptions, not paper values:

- \(\delta^2\): median of **positive directed** \(k\)-NN squared distances (`median_positive_knn_squared_distance`). The older dense SC median over remaining undirected edges is the named alternative `median_undirected_edge_squared_distance`, not the default.
- Union vs mutual: default `union`. The paper does not name the rule.
- \(k\)-NN ties: smaller index. `knn_method="auto"` is dense mergesort for \(n\le 1500\), otherwise block `argpartition` (boundary ties can differ).
- Eigen-solver: `scipy.linalg.eigh` for \(n\le 512\) (or nearly full spectra), else `eigsh`.
- Eigenvector signs: `largest_magnitude_positive`.
- Row-normalization: **off**. Turning it on is Category C, not the paper method.
- \(G_0=F\). The first all-zero residual uses `zero_residual_floor="median_pairwise"`; later zeros use `eps=1e-8`. `"eps"` throughout stays at \(F\).
- IRLS `tol=1e-6`. `ssc.py` uses `max_iter=100`; the experiment runner uses `300`.
- K-means: `ssc.py` still defaults to `k-means++` / 10 restarts; experiments use `random` / 1 restart. sklearn `tol=1e-4` in the SC baseline is the K-means tolerance, not the IRLS tolerance.
- `gamma=1` is an API default, not a claim that every dataset should use it.

## How to run SSC

From the `v1` directory:

```python
from SSC_method import SpectralShrunkClustering

model = SpectralShrunkClustering(n_clusters=3, gamma=1.0, k=5, kmeans_random_state=0)
labels = model.fit_predict(X)  # X has one sample per row
# model.embedding_ is F, model.shrunk_ is G, model.affinity_ is W
# model.objective_history_ records Equation (8) and the smoothed objective
# model.info_["variant"] is E13 unless you pass variant="E8"
```

Same \(F\) as spectral clustering (after the documented sign convention):

```python
from baselines.spectral_clustering import spectral_embedding as sc_embed
from SSC_method.spectral_config import SpectralGraphConfig
from SSC_method.spectral_embedding import embeddings_match, spectral_embedding

config = SpectralGraphConfig(k=5, symmetrization="union", row_normalize=False)
F_ssc, _ = spectral_embedding(X, n_components=c, config=config)
F_sc = sc_embed(X, n_clusters=c, n_neighbors=5, knn_mode="union")
assert embeddings_match(F_sc, F_ssc)
```

The library does not read data files, so it has no filesystem paths. Experiment orchestration is `experiments/methods.py` and `scripts/run_experiment.py`.

## What the solver does

1. Build a symmetric \(k\)-NN Gaussian graph \(A\) on the features and take the \(c\) eigenvectors for the smallest eigenvalues of the symmetric normalized Laplacian, Equation (4). Default \(k=5\). This is not PCA.
2. Build a second \(k\)-NN Gaussian graph \(W\) on that embedding \(F\).
3. Iterate Equation (13) by default, \(G=(S+\gamma\widetilde L)^{-1}SF\), with a sparse symmetric solve (`scipy.sparse.linalg.spsolve`). No explicit inverse. \(\widetilde W\) and \(\widetilde L\) are recomputed from the current \(G\). Algorithm 1 line 10 is not implemented. Pass `variant="E8"` for the printed Equation (8) stationary system.
4. Run K-means on \(G\). Those labels are an output. They are not used to build \(W\), \(F\), or \(G\).

## Task 1（2026-10-21）OA PDFs

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `resources/Chang_et_al_2015_SSC_AAAI.pdf` | 851255 | `970ee4e65fd73aca46b3f983098f87105fb7e45726b767ec7925c9188646dfaf` |
| `resources/Chang_et_al_2014_SSC_arxiv_1411.6308.pdf` | 233802 | `b4bb9f8984db89ee5c17a2c2200a6764085d81d3da5fc26b2c144e2202262e39` |

AAAI GET **200**；哈希与仓库外 `9736-45063-1-PB.pdf` 相同。GitHub 仓库搜索 `spectral shrunk clustering` `total_count=0`。xiaojun.ai HTTP **200**，无 2015 代码。作者代码 `CODE_NOT_FOUND`。实现 `PAPER_BASED_REIMPLEMENTATION`。矩阵状态：`COMPLETE_WITH_UNSPECIFIED_SETTINGS`。
