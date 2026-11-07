# Repair round 1: baseline provenance audit

Date of this audit: 2026-10-20 (UTC+8). Workspace: `v1/`. No clustering benchmarks were run. Historical `runs/` were not deleted. `SSC_method/` optimizer variants were not modified. The course report was not rewritten.

Status vocabulary is unchanged: `EXACT_VERIFIED`, `FAITHFUL_REIMPLEMENTATION`, `APPROXIMATE`, `UNVERIFIED`, `NOT_IMPLEMENTED`. Nothing here is `EXACT_VERIFIED` (no author binaries). Repair-round categories from the plan are recorded separately:

- **A_PAPER_FAITHFUL:** written in Chang et al. or in the named source paper, and implemented that way.
- **B_AMBIGUITY:** the source does not specify the setting; the current choice is an explicit reconstruction, not a silent switch.
- **C_NONFAITHFUL:** a diagnostic or invented loop. Numerical improvement does not promote it into a faithful main table.

Phase 1 numbers below are copied from `results/tables/table2_track_a_acc.md`, `table3_track_a_nmi.md`, and `table4_track_b.md`. They are Our Reproduction, not Chang et al. cells. SPLS has no Our Reproduction numbers.

Folder layout is unchanged: `baselines/kmeans/`, `baselines/spectral_clustering/`, `baselines/pca_kmeans/`, `baselines/pca_spectral/`, `baselines/lda_kmeans/`, `baselines/lda_spectral/`, `baselines/llc/`, `baselines/spls/`.

## Summary table

| Method | Status | Repair-round category | Main-table eligible? | Phase 1 ACC vs Chang (JAFFE / ORL) |
| --- | --- | --- | --- | --- |
| K-means | `FAITHFUL_REIMPLEMENTATION` | A (Lloyd + random init); k-means++ is B, not the default | Yes | 73.2 vs 75.6 (n=50) / 51.8 vs 60.5 (n=50) |
| Spectral clustering | `FAITHFUL_REIMPLEMENTATION` | A for Eq. (4), k=5, Gaussian kNN; B for δ and union kNN | Yes | 67.7 vs 76.1 (n=50) / 54.2 vs 72.7 (n=50) |
| PCA-KM | `FAITHFUL_REIMPLEMENTATION` | A for “PCA then K-means”; B for dim step 10 | Yes | 74.8 vs 75.8 (n=50, dim=10) / 53.0 vs 64.5 (n=50, dim=30) |
| PCA-SC | `FAITHFUL_REIMPLEMENTATION` | A for “PCA then Eq. (4)”; B for dim step 10 | Yes | 69.8 vs 76.9 (n=10, dim=70) / 54.9 vs 67.8 (n=10, dim=100) |
| LDA-KM | `FAITHFUL_REIMPLEMENTATION` | A for Ding–Li Algorithm 1; B for ridge and `max_iter` | Yes | 64.8 vs 76.5 (n=10, dim=9) / 48.5 vs 65.6 (n=10, dim=20) |
| LDA-SC | `APPROXIMATE` | C (alternation is not written) | **No** | No Phase 1 jobs. Do not put in a faithful main table. |
| LLC | `FAITHFUL_REIMPLEMENTATION` | A for Wu–Schölkopf Eqs. (9)–(15), (17)–(19); B for k=5 / λ=1 / γ=σ₀² | Yes | 88.4 vs 78.6 (n=50) / 62.1 vs 71.5 (n=50). Higher JAFFE ACC is **not** evidence of greater faithfulness. |
| SPLS / SLPS | `NOT_IMPLEMENTED` | n/a | No (N/A — not reproduced) | No numbers. Full Section 3 still inaccessible. |

## Chang et al. experimental protocol (shared, verified)

Read from Chang, Nie, Ma, Yang, and Zhou, AAAI 2015, “Setup” (AAAI PDF / Monash OA copy). Not inferred from our ACC:

- Neighborhood size **k = 5** for all spectral clustering algorithms.
- Comparison-algorithm parameters searched in \(\{10^{-6},10^{-3},1,10^{3},10^{6}\}\); “report the best results”.
- “Repeat each clustering 50 times with **random initialization** and report the results corresponding to the **best objective function values**.” Mean±std is also printed. Those two sentences remain unresolved; Phase 1 Track A reports mean±std over all completed trials of a label-informed selected setting, and does not drop trials by an invented best-objective filter.
- Dimensionality-reduction K-means and spectral clustering: “project the original data into a low dimensional subspace of **10 to 150** and report the best results.” The **step is unspecified**. Phase 1 used `{10,20,…,150}` (`experiments/protocol.py`: `DIM_GRID_FULL = tuple(range(10, 160, 10))`). That step is a B assumption and is kept.

---

## 1. K-means

**Original reference (verified).** Classical Lloyd K-means. Chang et al. treat it as the standard baseline and cite no single algorithm paper. Experimental Setup says “random initialization”.

**Implementation equation.** \(\min \sum_k \sum_{i\in C_k}\|x_i-m_k\|_2^2\).

**Verified algorithm.** `baselines/kmeans/kmeans.py` calls `sklearn.cluster.KMeans` with every control explicit: `init="random"`, `n_init=1`, `algorithm="lloyd"`, `tol=1e-4`, `max_iter=300`. The function does not search 50 restarts internally. Track A/B jobs loop seeds outside.

**Original hyperparameters.** Chang et al.: random initialization, 50 repetitions, best objective. No `tol`, `max_iter`, or Elkan vs Lloyd.

**Unknown settings.** Whether “random initialization” meant uniform random centers (Lloyd / sklearn `random`) or another draw; whether one “run” used inner `n_init>1`.

**Variants that SHOULD be tested later (not run now).**

- `init="k-means++"` as **B_AMBIGUITY**. Do **not** silently switch the default. Random remains the historical protocol default.
- Inner `n_init>1` derived from the same seed (protocol, not algorithm).
- `algorithm="elkan"` (accepted by the fitter, not default).

**Tests already passing.** `baselines/kmeans/test_kmeans.py`: determinism, blob separation, rejection of `random_state=None` and unknown kwargs.

**Fidelity category.** `FAITHFUL_REIMPLEMENTATION`. Init default is A relative to Chang’s “random initialization”; k-means++ is B and unused.

**Numerical differences vs Chang et al.** Track A ACC%: JAFFE 73.2±5.7 (n=50) vs 75.6±1.8; ORL 51.8±3.3 (n=50) vs 60.5±1.8; YaleB 9.3±0.6 (n=10) vs 14.4±1.5; USPS 66.3±1.7 (n=10) vs 65.4±1.7. NMI%: JAFFE 83.1±3.5 vs 79.4±0.8; ORL 74.4±1.5 vs 80.3±1.8. Track B K-means matches Track A on ORL/JAFFE/YaleB (no label-informed setting to select).

**Unresolved.** Best-objective vs mean±std; ORL/YaleB image identity; whether sklearn Lloyd equals the 2015 MATLAB/C stack.

---

## 2. Spectral clustering

**Original reference (verified).** Chang et al., Eq. (4), symmetric normalized Laplacian \(L_n=I-D^{-1/2}AD^{-1/2}\); Shi and Malik, TPAMI 2000, for normalized cut. k=5 in Setup. Affinity is Gaussian on a kNN graph.

**Implementation equation.** \(\min \operatorname{Tr}(F^\top L_n F)\) then K-means on the rows of \(F\). Gaussian \(A_{ij}=\exp(-\|x_i-x_j\|_2^2/\delta^2)\) on retained edges, no self-loops.

**Verified algorithm.** `baselines/spectral_clustering/spectral_clustering.py`. Does **not** call `sklearn.cluster.SpectralClustering` (test asserts the import is absent). Pipeline: brute-force kNN → union or mutual mask → Gaussian weights → Eq. (4) → `n_clusters` smallest eigenvectors of `eigh` → `baselines.kmeans` with `init="random"`. Eigenvectors are **not** row-normalized (Ng–Jordan–Weiss would be C).

For n>1500, `experiments/methods.py` `prepare_spectral` switches to `SSC_method.spectral_embedding` (sparse `eigsh`) and records `spectral_backend="ssc_method_sparse"`. That is YaleB/USPS only, not a sklearn default.

**Original hyperparameters.** k=5. Random initialization of the final K-means, 50 times. δ unspecified.

**Unknown settings.** δ; union vs mutual kNN (the paper does not say “mutual”); isolated-vertex convention; eigenvector sign.

**Current B defaults (kept).** `knn_mode="union"`; `delta=None` sets \(\delta^2\) to the median squared length of retained edges; isolated vertices have \(D^{-1/2}=0\) so \(L_n\) diagonal 1.

**Variants that SHOULD be tested later (not run now).**

- B: mean (not median) bandwidth; a fixed global δ; `knn_mode="mutual"` as an SSC extension, not as faithful SC.
- C: Zelnik–Manor self-tuning; Ng–Jordan–Weiss row normalization; sklearn `SpectralClustering` defaults (k-means++, RBF on a full graph, etc.).

**Tests already passing.** `test_spectral_laplacian_matches_equation_4`, `test_gaussian_weights_and_mutual_knn_rule`, `test_spectral_clustering_does_not_use_sklearn_estimator`.

**Fidelity category.** `FAITHFUL_REIMPLEMENTATION` of Eq. (4)+k=5+Gaussian kNN. Bandwidth and union graph are B.

**Numerical differences vs Chang et al.** Track A ACC%: JAFFE 67.7±11.3 (n=50) vs 76.1±1.6; ORL 54.2±3.1 (n=50) vs 72.7±2.3; YaleB 20.1±1.2 (n=10) vs 34.8±1.4; USPS not reproduced. NMI%: JAFFE 82.8±5.7 vs 80.2±0.9; ORL 76.5±1.6 vs 85.8±1.9; YaleB 29.9±0.9 vs 55.6±1.6. ORL SC is statistically indistinguishable from our SSC (53.9±3.0), which contradicts the paper ranking.

**Unresolved.** δ in the 2015 code; whether F was row-normalized; YaleB sparse-vs-dense eigensolver.

---

## 3. PCA-KM

**Original reference (verified).** Named “PCA Kmeans” by Chang et al.; they cite Xu and Wunsch, IEEE TNN 2005. That survey does not define a new estimator. The method is PCA, then K-means.

**Implementation equation.** Maximize captured variance in an `n_components`-dimensional linear subspace, then the K-means objective there.

**Verified algorithm.** `baselines/pca_kmeans/pca_kmeans.py`: sklearn PCA `svd_solver="full"` (centers X), then `baselines.kmeans` with the same explicit Lloyd controls. `n_components` is required; the fitter does not search 10…150.

**Original hyperparameters.** Subspace “10 to 150”, best result. Step unspecified. K-means random init, 50 times.

**Unknown settings.** Dimension step; whether PCA whitened; whether data were pre-normalized before PCA.

**Current B default (kept).** Track A grid `{10,20,…,150}` clipped by `min(n-1,d)`. Track B uses `min(50, n_clusters, n-1, d)` with no labels (protocol example, not a paper value).

**Variants that SHOULD be tested later (not run now).** Other steps (e.g. 5, 20) only as B grids; whitening; sklearn randomized SVD. Do not run a 50-trial grid in this round.

**Tests already passing.** `test_pca_kmeans_dimension_is_required_and_used`.

**Fidelity category.** `FAITHFUL_REIMPLEMENTATION` of “PCA then K-means”. Grid step is B.

**Numerical differences vs Chang et al.** Track A selected dim=10 on JAFFE (74.8±7.7, n=50 vs paper 75.8±1.5) and dim=30 on ORL (53.0±3.1, n=50 vs 64.5±2.3). YaleB/USPS Track A PCA-KM were not run. Track B: ORL 52.6±2.9 (n=50), JAFFE 74.8±7.7 (n=50), YaleB 9.1±0.6 (n=10).

**Unresolved.** The paper’s selected dimensions are unpublished, so a gap can be the grid, the images, or K-means init as well as PCA.

---

## 4. PCA-SC

**Original reference (verified).** Named “PCA spectral clustering / PCA SC” by Chang et al. Spectral step is their Eq. (4). No separate source paper.

**Implementation equation.** PCA variance objective, then the spectral baseline in the projected coordinates.

**Verified algorithm.** `baselines/pca_spectral/pca_spectral.py`: full SVD PCA, then `baselines.spectral_clustering.fit_predict` with default k=5, union kNN, median δ.

**Original hyperparameters.** Same 10…150 sentence; k=5; random K-means on the embedding.

**Unknown settings.** Same as PCA-KM plus the spectral B items (δ, union).

**Variants that SHOULD be tested later (not run now).** Same B list as PCA-KM and SC. Not run now.

**Tests already passing.** `test_pca_spectral_dimension_is_required_and_used`.

**Fidelity category.** `FAITHFUL_REIMPLEMENTATION` of “PCA then the spectral baseline”.

**Numerical differences vs Chang et al.** Track A used **10 trials per dimension** (cost triage, not 50): JAFFE dim=70, 69.8±8.3 vs 76.9±1.8; ORL dim=100, 54.9±2.7 vs 67.8±2.1. Track B (prespecified dim, n=50): ORL 53.0±3.1, JAFFE 60.0±7.4. YaleB/USPS not reproduced.

**Unresolved.** 10 vs 50 trials on Track A; selected dimensions unpublished.

---

## 5. LDA-KM

**Original reference (verified).** Ding and Li, ICML 2007, “Adaptive Dimension Reduction Using Discriminant Analysis and K-means Clustering”. Chang et al. cite this for LDA Kmeans.

**Implementation equation.** Ding and Li Eq. (7): \(\max_{U,H} \operatorname{Tr}(U^\top S_b U)/\operatorname{Tr}(U^\top S_w U)\). Algorithm 1: PCA init, K-means in the subspace, LDA from those labels, repeat. Labels are cluster indicators, never ground truth.

**Verified algorithm.** `baselines/lda_kmeans/lda_kmeans.py`. `n_components` required and **cannot exceed `n_clusters-1`**. No PCA padding. Data centered. `S_w` ridged only when numerically singular (`sw_reg=1e-8`). Loop stops on unchanged labels or `max_iter=30`. Inner K-means `init="random"`, `n_init=1`. Passing `y=...` raises `TypeError`.

Chang’s “10 to 150 for every DR baseline” is **not feasible** for classical LDA on a 10-class set (USPS: at most 9). The fitter raises rather than clipping silently. Track A LDA grid is `{10,20,…}` clipped to `K-1`, or `[K-1]` if that cap is below 10 (JAFFE: 9).

**Original hyperparameters.** Ding and Li set the subspace dimension to `K-1`. Chang et al. still write 10…150. Alternation cap and singular-`S_w` rule are unspecified.

**Unknown settings.** Numeric `max_iter`; ridge; whether Ding–Li centered in code; whether Chang et al. padded LDA with PCA to reach dimension 10+.

**Variants that SHOULD be tested later (not run now).**

- B: `n_components=K-1` only (Ding–Li), vs the Chang 10…150 sentence.
- B: `sw_reg=0` (refuse singular `S_w`).
- C: pad leftover axes with PCA so USPS can use dim≥10. That would **not** be classical LDA and must not enter a faithful table.

**Tests already passing.** `test_lda_kmeans_uses_cluster_labels_and_respects_rank`.

**Fidelity category.** `FAITHFUL_REIMPLEMENTATION` of Ding–Li Algorithm 1, with B numerical safeguards.

**Numerical differences vs Chang et al.** Track A: JAFFE dim=9, 64.8±11.7 (n=10) vs 76.5±1.7; ORL dim=20, 48.5±3.7 (n=10) vs 65.6±2.6. One ORL dim=20 job failed (`NameError`, `20261020_015425__TRACKA__LDAKM__ORL__fb14ac44`) and was rerun to completion (`20261020_020157__…`); FAILED directory kept. Track B: ORL 48.5±3.0 (n=50), JAFFE 64.4±9.2 (n=50). YaleB/USPS not reproduced.

**Unresolved.** Why Track A selected ORL dim=20 rather than 39=`K-1`; whether the paper’s LDA-KM used `K-1` only.

---

## 6. LDA-SC

**Original reference (verified).** Named “LDA spectral clustering / LDA SC” by Chang et al. Ding and Li define the **K-means** version only. Neither paper writes an LDA↔spectral loop.

**Implementation equation.** Not written. Code actually optimizes Ding–Li alternation with spectral clustering in place of K-means.

**Verified algorithm.** `baselines/lda_spectral/lda_spectral.py`. Same rank limit and ridge as LDA-KM. Inner partition is Eq. (4) spectral clustering. Current cluster labels only; no `y` argument.

**Original hyperparameters.** None for the missing loop. k=5 if the inner step is spectral. Dimension sentence still 10…150, which classical LDA cannot meet above `K-1`.

**Unknown settings.** One-shot LDA after a single spectral clustering vs alternation; how many LDA directions; whether labels for LDA ever used ground truth (this code does not).

**Variants that SHOULD be tested later (not run now).** One-shot vs alternate vs “spectral clustering in an LDA subspace fit from an initial K-means”. All remain **C / APPROXIMATE**. Do not promote any of them into a faithful main table even if ACC is closer to Chang et al.

**Tests already passing.** `test_lda_spectral_is_deterministic_without_ground_truth`.

**Fidelity category.** `APPROXIMATE`. **Not eligible for a faithful main table.** `experiments/protocol.py` lists it in `APPROXIMATE_METHODS`. Phase 1 `run_all_stages.py` did not schedule LDA-SC jobs.

**Numerical differences vs Chang et al.** Paper ACC% (quoted only): AR 44.5±1.3, JAFFE 77.4±1.9, ORL 68.3±2.4, UMIST 54.7±1.5, BinAlpha 45.1±1.4, MSRA50 55.1±1.7, YaleB 38.2±1.6, USPS 70.4±1.5. Our Reproduction: none. Do not invent numbers.

**Unresolved.** What Chang et al. actually ran.

---

## 7. LLC

**Original reference (verified).** Wu and Schölkopf, NIPS 2006, “A Local Learning Approach for Clustering”. Final discretization: Yu and Shi, ICCV 2003 (Wu–Schölkopf point at Jianbo Shi’s 2006 spectral-clustering code). Chang et al. also cite Yang, Xu, Nie, Yan, and Zhuang, IEEE TIP 2010, for a local-learning Laplacian; **that paper was not used as the specification**.

**Implementation equation.** Wu–Schölkopf Eq. (14): \(\min_F \operatorname{Tr}(F^\top T F)\) s.t. \(F^\top F=I\), \(T=(I-A)^\top(I-A)\), A from local kernel ridge regression Eq. (9)–(10). Gaussian kernel Eq. (23): \(\exp(-\|x_i-x_j\|^2/\gamma)\), divide by \(\gamma\) not \(\gamma^2\). Discrete partition Eqs. (17)–(19) via Yu–Shi.

**Verified algorithm.** `baselines/llc/llc.py`: local ridge on k neighbors, `eigh` of T, row-normalize eigenvectors, Yu–Shi with `random_state` for the first discrete center. Default `n_neighbors=5` (SSC protocol, **not** LLC’s search over k), `reg=1` (one value on their `{0.1, 1, 1.5}`), `gamma=None` → \((\text{mean row Euclidean norm})^2\) (center \(\sigma_0^2\) of their gamma grid, not a selected optimum). Yu–Shi `tol=1e-8` rather than machine epsilon. Phase 1 jobs pass `k=5` and use this default γ.

**Original hyperparameters (Wu–Schölkopf).** Search k; λ in `{0.1, 1, 1.5}`; γ on a grid around \(\sigma_0^2\). Chang et al. force k=5 for spectral methods and search `{1e-6,…,1e6}` for “parameters in all comparison algorithms”, which does not map cleanly onto LLC’s λ/γ.

**Unknown settings.** Which (k, λ, γ) Chang et al. reported; whether they used Yang et al. 2010 instead of Wu–Schölkopf; Yu–Shi stopping rule.

**Variants that SHOULD be tested later (not run now).** LLC’s original (k, λ, γ) grids; cosine kernel Eq. (22); Yang et al. 2010 Laplacian as a **different method**, not a silent LLC swap.

**Tests already passing.** `test_llc_follows_local_learning_and_is_deterministic` (Gaussian + cosine).

**Fidelity category.** `FAITHFUL_REIMPLEMENTATION` of Wu–Schölkopf with SSC k=5 as a B protocol choice.

**Numerical differences vs Chang et al.** Track A ACC%: **JAFFE 88.4±6.9 (n=50) vs paper 78.6±1.5**; ORL 62.1±2.0 (n=50) vs 71.5±2.2. NMI%: JAFFE 91.2±2.7 vs 82.5±1.7; ORL 78.7±1.3 vs 84.9±1.5. Track B JAFFE LLC ACC is the same 88.4±6.9.

**Higher ACC is not evidence of greater faithfulness.** JAFFE LLC beating the paper by ~10 points can come from k=5, the γ=σ₀² center, Yu–Shi vs another discretizer, preprocessing, or a different local-learning Laplacian in 2015. It does **not** imply our LLC is “more correct than the paper”, and it must not be used to replace SSC numbers or to claim the 2015 ranking is reproduced.

**Unresolved.** The JAFFE overshoot; Yang et al. 2010 unread.

---

## 8. SPLS / SLPS

**Original reference (verified at publisher/metadata, not at full text).** Hou, Nie, Jiao, Zhang, and Wu, *Information Processing & Management* 49(4):871–883, 2013, DOI `10.1016/j.ipm.2013.01.004`, PII `S0306457313000095`. The paper’s own name is **SLPS** (Subspace Learning via Pattern Shrinking). Chang et al. write **SPLS**. Corresponding author: Chenping Hou, Department of Mathematics and Systems Science, NUDT.

Open abstract (ScienceDirect, 2026-10-20): linear subspace that incorporates linear and nonlinear structure; replace original points by shrunk patterns, inspired by Zhou, Bousquet, Lal, Weston, and Schölkopf (2003); parameter **α** can move “the small circle … outside of the big circle”; “how to derive the approximated solution in a quick way” is in Section 3, which is **not** in the open abstract. Experiments listed: Orl, Mnist, Coil20, Isolet, Newsgroup — not the SSC eight-dataset table.

**Implementation equation.** Unknown. Section 3 updates were not obtained. A citing recap in Gao et al., “Local Shrunk Discriminant Analysis (LSDA)”, arXiv:1705.01206, Section II-C, writes an SLPS-like model with parameters **δ and β**, not α, and does not reprint Hou et al.’s solver. That recap is **not** treated as a verified transcription. It was **not** implemented.

**Verified algorithm.** None. `baselines/spls/spls.py` `fit_predict` still raises `NotImplementedError`. No substitute shrinking, no SSC IRLS, no LSDA objective, no 2016 “pattern shrinking least square regression” (PSLSR / SLSR; different paper).

**Original hyperparameters.** Unknown (α and the rest live in Section 3 / experiments of Hou et al.). Chang et al. would have searched `{1e-6,…,1e6}` if they treated SPLS as a “comparison algorithm”, but that is not a substitute for Hou et al.’s own grid.

**Unknown settings.** Entire optimizer: variables, constraints, closed form vs iteration, graph weights, subspace dimension, clustering step after the subspace.

**Variants that SHOULD be tested later (not run now).** None until the full text or author code is in hand. After that: implement the printed updates, add small-example tests against those equations, then mark `FAITHFUL_REIMPLEMENTATION` or `APPROXIMATE` honestly.

**Tests already passing.** `baselines/spls/test_spls.py::test_spls_is_not_implemented`.

**Fidelity category.** `NOT_IMPLEMENTED`. Result cells stay **N/A — not reproduced**. Do not invent SPLS numbers.

**Numerical differences vs Chang et al.** Paper ACC% (quoted only): AR 49.2±1.4, JAFFE 79.5±2.1, ORL 74.2±1.8, UMIST 70.4±1.6, BinAlpha 48.5±1.9, MSRA50 60.3±1.3, YaleB 47.3±1.7, USPS 71.4±1.6. Our Reproduction: none. Six Phase 1 jobs are SKIPPED (`runs/20261020_*__*__SPLS__*`).

**Unresolved.** Full text and official code.

### SPLS URLs tried (2026-10-20)

Access via Cursor `WebFetch` / publisher APIs. Local CPython `urllib` failed TLS (`CERTIFICATE_VERIFY_FAILED`) on this machine; those local failures are **not** used as HTTP status. `escience.cn` returned **502** even on that local client.

| URL | What was asked | Access status | Section 3 / PDF? |
| --- | --- | --- | --- |
| https://doi.org/10.1016/j.ipm.2013.01.004 | Canonical DOI | Resolves to Elsevier / ScienceDirect | No |
| https://www.sciencedirect.com/science/article/abs/pii/S0306457313000095 | Publisher abstract | Open abstract + highlights; “Purchase PDF” | Abstract only |
| https://www.sciencedirect.com/science/article/pii/S0306457313000095 | Full HTML | Paywalled (no full text in fetch) | No |
| https://linkinghub.elsevier.com/retrieve/pii/S0306457313000095 | Elsevier linking hub | Redirects to publisher | No |
| https://api.elsevier.com/content/article/PII:S0306457313000095?httpAccept=text/plain | Crossref text-mining link | Subscription API; not a public manuscript | No |
| https://dl.acm.org/doi/abs/10.1016/j.ipm.2013.01.004 | ACM DL | Abstract landing; no PDF | No |
| https://api.crossref.org/works/10.1016/j.ipm.2013.01.004 | Crossref metadata | 200. Copyright © 2013 Elsevier Ltd. | Metadata only |
| https://api.openalex.org/works/https://doi.org/10.1016/j.ipm.2013.01.004 | OpenAlex | `is_oa=false`, `oa_url=null`, `any_repository_has_fulltext=false`, `pdf_url=null`, `has_fulltext=false` | No |
| https://api.unpaywall.org/v2/10.1016/j.ipm.2013.01.004 | Unpaywall | `is_oa=false`, `oa_status="closed"`, `has_repository_copy=false`, `oa_locations=[]`, `best_oa_location=null` | No |
| https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/j.ipm.2013.01.004 | Semantic Scholar | `isOpenAccess=false`, `openAccessPdf.status="CLOSED"`, abstract elided by publisher | No |
| https://www.semanticscholar.org/paper/29c20db87d1fdd93fa072cdb11deca9307447d06 | S2 HTML | Landing; no OA PDF | No |
| https://export.arxiv.org/api/query?search_query=all:"Learning a subspace for clustering via pattern shrinking" | arXiv title/all search | `totalResults=0` | No preprint |
| https://arxiv.org/search/?query="Learning a subspace for clustering via pattern shrinking" | arXiv UI | 0 hits (via search tool) | No |
| https://dblp.org/rec/journals/ipm/HouNJZW13 | DBLP | Record exists; points at the DOI | No PDF |
| https://ir.webis.de/anthology/publications/rec+journals+ipm+HouNJZW13 | Webis/DBLP mirror | BibTeX + DOI only | No |
| https://chenpinghou.github.io/ | Author homepage | Live. Email `hcpnudt@hotmail.com` | No PDF |
| https://chenpinghou.github.io/publications.html | Author publications | JS loads `years.html` | — |
| https://raw.githubusercontent.com/ChenpingHou/ChenpingHou.github.io/main/years.html | Source of the publications list | 2013 IPM entry is present. The `[PDF]` href is **`https://doi.org/10.1016/j.ipm.2013.01.004`**, not a hosted manuscript. (The next 2013 Cybernetics row copy-pastes the same DOI; ignored.) | DOI only |
| https://chenpinghou.github.io/code.html | Author codes page | “We provide codes in the Github page.” No SLPS entry | No |
| https://github.com/ChenpingHou/ChenpingHou.github.io | Homepage repo | No PDF of the 2013 paper | No |
| https://api.github.com/users/ChenpingHou/repos | Author GitHub repos | No SLPS/SPLS repository | No |
| https://github.com/search?q="Subspace Learning via Pattern Shrinking" OR SLPS Hou Nie | Code search | No matching implementation | No |
| https://orcid.org/0000-0002-9335-0469 | Chenping Hou ORCID | Profile (HTML sparse in fetch) | No PDF |
| https://iopen.nwpu.edu.cn/info/1329/1213.htm | Feiping Nie (NWPU iOPEN) | Representative-paper list; 2013 IPM not among posted PDFs | No |
| http://ranger.uta.edu/~nie/ | Former UTA page | **404** | No |
| http://www.escience.cn/people/houchengping/ | Old Chinese academy homepage (KipHub still lists it) | Local GET **502 Bad Gateway** | No |
| https://faculty.nudt.edu.cn/ | NUDT faculty portal | TLS error / no SLPS PDF obtained | No |
| https://www.researchgate.net/publication/257107889_Learning_a_subspace_for_clustering_via_pattern_shrinking | ResearchGate guess | Login wall in fetch; not used as a manuscript | No |
| https://citeseerx.ist.psu.edu/search?q=Learning+a+subspace+for+clustering+via+pattern+shrinking | CiteSeerX | No OA PDF obtained | No |
| https://core.ac.uk/search?q=Learning%20a%20subspace%20for%20clustering%20via%20pattern%20shrinking%20Hou | CORE | No OA PDF obtained | No |
| https://europepmc.org/search?query=Learning%20a%20subspace%20for%20clustering%20via%20pattern%20shrinking | Europe PMC | No OA PDF obtained | No |
| https://www.ncbi.nlm.nih.gov/pmc/?term=Learning+a+subspace+for+clustering+via+pattern+shrinking | PubMed Central | Not a PMC journal article | No |
| https://github.com/jiaoboleetc/SLSR | MATLAB “SLSR” | **Different method** (2016 PSLSR / pattern-shrinking least squares). Not SLPS | Must not be substituted |
| https://arxiv.org/abs/1705.01206 and https://arxiv.org/pdf/1705.01206v1.pdf | LSDA citing recap | Open. Parameters δ, β, not Hou’s α. Solver not Hou Section 3 | Secondary; **not implemented** |

**Decision.** Keep `NotImplementedError`. Do not substitute generic shrinking.

---

## Tests and import check (this round)

Commands to be run after this document and the README update, from `v1/`, with the course interpreter `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` (Anaconda sklearn is binary-incompatible with the current numpy):

```text
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pytest baselines -q
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -c "from baselines.kmeans import fit_predict as kmeans_fit_predict; from baselines.spectral_clustering import fit_predict as sc_fit_predict; from baselines.pca_kmeans import fit_predict as pca_km; from baselines.pca_spectral import fit_predict as pca_sc; from baselines.lda_kmeans import fit_predict as lda_km; from baselines.lda_spectral import fit_predict as lda_sc; from baselines.llc import fit_predict as llc_fit_predict; from baselines.spls import fit_predict as spls_fit_predict; print('imports-ok')"
```

Tiny synthetic tests only. Not the paper’s benchmark. This round (2026-10-20): `11 passed in 1.18s`; `imports-ok`. SPLS still raises `NotImplementedError`.

## What this audit did not do

- No 50-trial grids, no new clustering numbers, no SPLS invented scores.
- No edits to `SSC_method/` optimizer variants.
- No deletion of historical runs.
- No report rewrite, no git commit/push.
