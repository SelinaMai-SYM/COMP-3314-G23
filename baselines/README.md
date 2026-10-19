# Baselines for Chang et al., AAAI 2015

Each method lives in its own package under this directory. Implemented methods expose

```text
fit_predict(X, n_clusters, random_state, **params) -> labels
```

`X` has shape `(n_samples, n_features)`. `random_state` is an integer. The same seed and parameters return the same labels. No function reads ground-truth labels, searches the paper's dimension range, or repeats the paper's 50 restarts on its own.

Canonical imports:

```python
from baselines.kmeans import fit_predict
from baselines.spectral_clustering import fit_predict
```

Run the tests from the `v1` directory:

```text
python -m pytest baselines
```

The tests use tiny synthetic samples. They are not the paper's benchmark. No extra packages beyond NumPy, SciPy, and scikit-learn are required.

## Provenance

Status values are only `EXACT_VERIFIED`, `FAITHFUL_REIMPLEMENTATION`, `APPROXIMATE`, `UNVERIFIED`, and `NOT_IMPLEMENTED`. Nothing here is `EXACT_VERIFIED`: the authors' experimental code was not available to compare numerically. Repair-round 1 re-audit (2026-10-20): `docs/repair_round1_baseline_audit.md`. Folder layout is unchanged (`baselines/kmeans/`, `spectral_clustering/`, `pca_kmeans/`, `pca_spectral/`, `lda_kmeans/`, `lda_spectral/`, `llc/`, `spls/`).

Repair-round categories used in that audit: **A** = written in the source and implemented that way; **B_AMBIGUITY** = unspecified, reconstructed explicitly, not a silent switch; **C** = diagnostic / not written. LDA-SC stays off any faithful main table. k-means++ is B_AMBIGUITY and is **not** the default.

| Method | Original paper | Official code available? | Implementation source | Paper-faithful? | Verified differences | Status |
| --- | --- | --- | --- | --- | --- | --- |
| K-means | Classical Lloyd K-means. Chang et al. treat it as the standard baseline and do not cite a single algorithm paper for it. Setup says "random initialization". | No author repository. scikit-learn is a library implementation. | `baselines/kmeans/`, `sklearn.cluster.KMeans` | Yes, as Lloyd K-means with the controls below written into the call | Default `init="random"` is the historical protocol default (Chang et al. Setup). `init="k-means++"` is accepted as a **B_AMBIGUITY** argument and must not become the silent default. Default `n_init=1`, so the paper's 50 restarts stay outside this function. `algorithm="lloyd"`, `tol=1e-4`, `max_iter=300` are explicit arguments. | `FAITHFUL_REIMPLEMENTATION` |
| Spectral clustering | Chang et al., AAAI 2015, Eq. (4), the symmetric normalized Laplacian; Shi and Malik, TPAMI 2000, for normalized cut | No SSC author code found | `baselines/spectral_clustering/`. Does not call `sklearn.cluster.SpectralClustering` (not sklearn defaults) | Yes, for Eq. (4) followed by K-means on the embedding | `k=5` by default. Affinity is Gaussian on a kNN graph. Default graph is the union (symmetric) kNN graph, because the paper does not say mutual. `delta=None` sets `delta^2` to the median squared length of the retained edges; the paper leaves `delta` unspecified (B). Eigenvectors are not row-normalized. Final K-means uses the explicit K-means controls. | `FAITHFUL_REIMPLEMENTATION` |
| PCA + K-means | Xu and Wunsch, IEEE TNN 2005, is the survey Chang et al. cite. PCA then K-means is not a new estimator in that survey. | scikit-learn PCA and K-means | `baselines/pca_kmeans/` | Yes for "PCA, then K-means" | `n_components` is required. The fitter does not try dimensions 10, 20, ..., 150. The SSC text says "10 to 150" and does not state the step. Phase 1 used step 10 as a kept **B** assumption (`experiments/protocol.py`). PCA uses a full SVD and centers `X`. | `FAITHFUL_REIMPLEMENTATION` |
| PCA + spectral clustering | Named by Chang et al. The spectral step is their Eq. (4). | No | `baselines/pca_spectral/` | Yes for "PCA, then the spectral baseline" | Same dimension rule as PCA + K-means (step 10 is B, kept). Same spectral defaults as the spectral baseline. | `FAITHFUL_REIMPLEMENTATION` |
| LDA + K-means | Ding and Li, ICML 2007, "Adaptive Dimension Reduction Using Discriminant Analysis and K-means Clustering" | No implementation repository found. The algorithm was read from the author PDF. | `baselines/lda_kmeans/` | Yes for Algorithm 1: PCA initialization, K-means in the subspace, LDA from those labels, repeat | `n_components` is an argument. Algorithm 1 sets it to `K-1`. Values above `K-1` raise, because classical LDA has no further discriminant directions and this code does not pad with PCA. Data are centered, as Section 2 assumes. `S_w` is ridged only when it is numerically singular (`sw_reg=1e-8`). The alternation stops on unchanged labels or after `max_iter=30`. Labels passed to LDA are the current K-means labels. | `FAITHFUL_REIMPLEMENTATION` |
| LDA + spectral clustering | Named by Chang et al. Ding and Li define the K-means version only. | No | `baselines/lda_spectral/` | Partially. The label rule is the one requested: current cluster labels, never ground truth. The alternation itself is not written in either paper. | Same rank limit and ridge as LDA + K-means. Inside the subspace, spectral clustering replaces K-means. Chang et al. do not say whether LDA is fit once or alternated. Status is **C / APPROXIMATE**. Do not put LDA-SC in a faithful main table, even if a later ACC is closer to Chang et al. Phase 1 scheduled no LDA-SC jobs. | `APPROXIMATE` |
| LLC | Wu and Schölkopf, NIPS 2006, "A Local Learning Approach for Clustering" | The paper points at Jianbo Shi's 2006 spectral-clustering code for the final discretization only. No maintained LLC package was found. Discretization is reimplemented from Yu and Shi, ICCV 2003. | `baselines/llc/` | Yes for Eqs. (9)--(15) and (17)--(19) | Default `k=5` matches the SSC experimental protocol, not the LLC search grid. Default `reg=1` and, when `gamma` is omitted, `gamma = (mean row norm)^2`, which is the center of their gamma grid rather than a selected value. Gaussian kernel is Eq. (23): divide by `gamma`, not by `gamma^2`. Stopping tolerance of the Yu--Shi loop is `1e-8` rather than machine epsilon. The first discrete center is drawn with `random_state`. SSC also cites Yang et al., IEEE TIP 2010, for a local-learning Laplacian; that paper was not used as the specification. Phase 1 JAFFE LLC ACC was 88.4 vs paper 78.6; **a higher ACC is not evidence of greater faithfulness**. | `FAITHFUL_REIMPLEMENTATION` |
| SPLS | Hou, Nie, Jiao, Zhang, and Wu, Information Processing & Management 49(4):871--883, 2013, DOI `10.1016/j.ipm.2013.01.004`. The paper's own name is SLPS. SSC writes SPLS. | No official code found. Re-search 2026-10-20: Unpaywall/OpenAlex closed, arXiv 0 hits, author `[PDF]` is the Elsevier DOI, Feiping Nie pages have no 2013 IPM PDF, `ranger.uta.edu/~nie/` is 404. | `baselines/spls/` raises `NotImplementedError` | No. A substitute was not implemented. LSDA (arXiv:1705.01206) recap uses δ, β not Hou's α and was not treated as Section 3. | Open abstract confirms authors, title, year, venue, pattern shrinking, and parameter α. It does not give the Section 3 optimization. Do not invent SPLS numbers. Use "N/A — not reproduced". URL log: `docs/repair_round1_baseline_audit.md`. | `NOT_IMPLEMENTED` |

Do not fill a results table for SPLS with numbers from another method. Use "N/A — not reproduced".

## Parameters the caller must choose

- Subspace methods take `n_components`. They do not loop over 10..150.
- LDA methods reject `n_components > n_clusters - 1`. For USPS, 10 classes give at most 9 LDA directions. The SSC sentence that searches dimensions 10 through 150 for every dimensionality-reduction baseline is not feasible for classical LDA on that collection. The fitter does not silently clip or pad.
- Spectral methods take `n_neighbors` (default 5), `delta` (default: median squared retained-edge length), and `knn_mode` (`"union"` or `"mutual"`). The baseline default is `"union"`. Mutual kNN is the planned SSC extension and is not switched on here.
- K-means restarts and the choice of the best objective are an evaluation protocol. Set `n_init` only when one call should keep the best of several seeds derived from `random_state`.

## Ground truth

`lda_kmeans` and `lda_spectral` compute scatter matrices from the labels just produced by K-means or spectral clustering. Their signatures have no label argument. Passing `y=...` raises `TypeError`.
