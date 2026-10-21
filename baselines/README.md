# Baselines for Chang et al., AAAI 2015

Each method lives in its own package. Implemented methods expose

```text
fit_predict(X, n_clusters, random_state, **params) -> labels
```

`X` has shape `(n_samples, n_features)`. `random_state` is an integer. No function reads ground-truth labels, searches 10…150, or repeats the paper’s 50 restarts on its own.

Canonical imports:

```python
from baselines.kmeans import fit_predict
from baselines.spectral_clustering import fit_predict
```

Run tests from `v1/`:

```text
python -m pytest baselines
```

Tests use tiny synthetic samples. They are not the paper’s benchmark.

Round 2 paper-faithfulness details live in **each package README**, not in this file. Short index: [`docs/round2_baseline_audit.md`](../docs/round2_baseline_audit.md). Round 1 historical audit: [`docs/repair_round1_baseline_audit.md`](../docs/repair_round1_baseline_audit.md).

## Status vocabulary

Use only: `EXACT_VERIFIED` / `PAPER_FAITHFUL_REIMPLEMENTATION` / `AMBIGUITY_RECONSTRUCTION` / `APPROXIMATE` / `NOT_IMPLEMENTED` / `UNVERIFIED`.

Publication/code types in the package READMEs: `VERIFIED ORIGINAL PUBLICATION` / `VERIFIED AUTHOR CODE` / `THIRD-PARTY` / `INDEPENDENT REIMPLEMENTATION` / `UNVERIFIED`. Never invent GitHub URLs.

Nothing here is `EXACT_VERIFIED`: no 2015 author binaries. `experiments/protocol.py` still stores the Round 1 string `FAITHFUL_REIMPLEMENTATION` for several methods; that is the same claim as `PAPER_FAITHFUL_REIMPLEMENTATION` below.

## Master provenance index

LDA-SC stays **off** any faithful main table. SPLS cells stay **N/A — not reproduced**. k-means++ is `AMBIGUITY_RECONSTRUCTION` and is **not** the default.

| Method | Package README | Original paper | Implementation source | Faithful main table? | Status |
| --- | --- | --- | --- | --- | --- |
| K-means | [`kmeans/README.md`](kmeans/README.md) | Classical Lloyd; Chang et al. Setup: random initialization | `THIRD-PARTY` sklearn Lloyd wrapped in `baselines/kmeans/kmeans.py` `fit_predict` | Yes | `PAPER_FAITHFUL_REIMPLEMENTATION` |
| Spectral clustering | [`spectral_clustering/README.md`](spectral_clustering/README.md) | Chang et al. Eq. (4); Shi and Malik 2000 | `INDEPENDENT REIMPLEMENTATION`; currently shares `SSC_method.graph_construction.knn_affinity` | Yes | `PAPER_FAITHFUL_REIMPLEMENTATION` (δ, union graph: `AMBIGUITY_RECONSTRUCTION`) |
| PCA-KM | [`pca_kmeans/README.md`](pca_kmeans/README.md) | Named by Chang et al.; Xu and Wunsch 2005 is a survey | sklearn PCA then `baselines.kmeans` | Yes | `PAPER_FAITHFUL_REIMPLEMENTATION` (dim step: `AMBIGUITY_RECONSTRUCTION`) |
| PCA-SC | [`pca_spectral/README.md`](pca_spectral/README.md) | Named by Chang et al.; spectral step Eq. (4) | PCA then `baselines.spectral_clustering` | Yes | `PAPER_FAITHFUL_REIMPLEMENTATION` |
| LDA-KM | [`lda_kmeans/README.md`](lda_kmeans/README.md) | Ding and Li, ICML 2007, Algorithm 1 | `INDEPENDENT REIMPLEMENTATION` in `lda_kmeans.py` | Yes | `PAPER_FAITHFUL_REIMPLEMENTATION` |
| LDA-SC | [`lda_spectral/README.md`](lda_spectral/README.md) | **Name only** in Chang et al. Ding–Li is K-means only | Two named approximations: `fit_predict` (A_ALTERNATE), `fit_predict_oneshot` (B_ONESHOT) | **No** | `APPROXIMATE` |
| LLC | [`llc/README.md`](llc/README.md) | Wu and Schölkopf, NIPS 2006 (spec). SSC `k=5` is comparison protocol. Yang 2010 is **not** mixed in | `INDEPENDENT REIMPLEMENTATION` in `llc.py` | Yes | `PAPER_FAITHFUL_REIMPLEMENTATION` |
| SPLS / SLPS | [`spls/README.md`](spls/README.md) | Hou et al., IPM 2013, DOI `10.1016/j.ipm.2013.01.004`. Paper name SLPS | `fit_predict` raises `NotImplementedError`. Section 3 not obtained 2026-10-21 | No (N/A) | `NOT_IMPLEMENTED` |

## Parameters the caller must choose

- Subspace methods take `n_components`. They do not loop over 10..150.
- LDA methods reject `n_components > n_clusters - 1`. USPS (10 classes) has at most 9 LDA directions. The fitter does not silently clip or pad.
- Spectral methods take `n_neighbors` (default 5), `delta`, and `knn_mode` (`"union"` or `"mutual"`). Default is `"union"`.
- K-means restarts and best-objective selection are evaluation protocol. Default `init` is `"random"`.

## Ground truth

`lda_kmeans` and `lda_spectral` compute scatter matrices from the labels just produced by K-means or spectral clustering. Their signatures have no label argument. Passing `y=...` raises `TypeError`.
