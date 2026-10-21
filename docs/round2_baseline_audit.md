# Round 2 baseline paper-faithfulness audit (index)

Date: 2026-10-21. Workspace: `v1/baselines/`. This file is a **short index**. Independently verifiable details (original equations, line-mapped functions, run IDs, URL logs) are in each package README. Do not treat this page as the source of truth for a single method.

Round 1 historical write-up (old label `FAITHFUL_REIMPLEMENTATION`): [`docs/repair_round1_baseline_audit.md`](repair_round1_baseline_audit.md). Master table: [`baselines/README.md`](../baselines/README.md).

Status vocabulary only: `EXACT_VERIFIED` / `PAPER_FAITHFUL_REIMPLEMENTATION` / `AMBIGUITY_RECONSTRUCTION` / `APPROXIMATE` / `NOT_IMPLEMENTED` / `UNVERIFIED`. Nothing is `EXACT_VERIFIED`.

This round did **not** unify the SC/SSC graph (other agent). It did **not** download the eight face datasets, rewrite the 4-page report, or git commit.

## Provenance table

| Method | README | Status | Faithful main table? | SPLS / notes |
| --- | --- | --- | --- | --- |
| K-means | [`baselines/kmeans/README.md`](../baselines/kmeans/README.md) | `PAPER_FAITHFUL_REIMPLEMENTATION` | Yes | Default `init="random"`. `k-means++` is `AMBIGUITY_RECONSTRUCTION`, not the silent default. |
| SC | [`baselines/spectral_clustering/README.md`](../baselines/spectral_clustering/README.md) | `PAPER_FAITHFUL_REIMPLEMENTATION` | Yes | Eq. (4), `k=5`. δ and union kNN are `AMBIGUITY_RECONSTRUCTION`. |
| PCA-KM | [`baselines/pca_kmeans/README.md`](../baselines/pca_kmeans/README.md) | `PAPER_FAITHFUL_REIMPLEMENTATION` | Yes | Dim step 10 is protocol `AMBIGUITY_RECONSTRUCTION`. |
| PCA-SC | [`baselines/pca_spectral/README.md`](../baselines/pca_spectral/README.md) | `PAPER_FAITHFUL_REIMPLEMENTATION` | Yes | PCA then Eq. (4). |
| LDA-KM | [`baselines/lda_kmeans/README.md`](../baselines/lda_kmeans/README.md) | `PAPER_FAITHFUL_REIMPLEMENTATION` | Yes | Ding–Li Algorithm 1; never GT. |
| LDA-SC | [`baselines/lda_spectral/README.md`](../baselines/lda_spectral/README.md) | `APPROXIMATE` | **No** | Chang et al. still give **no** construction. Two named interpretations: `fit_predict` (A_ALTERNATE), `fit_predict_oneshot` (B_ONESHOT). Never GT. |
| LLC | [`baselines/llc/README.md`](../baselines/llc/README.md) | `PAPER_FAITHFUL_REIMPLEMENTATION` | Yes | Wu–Schölkopf NIPS 2006 is the spec. SSC `k=5` is comparison protocol. Yang 2010 not mixed in. |
| SPLS / SLPS | [`baselines/spls/README.md`](../baselines/spls/README.md) | `NOT_IMPLEMENTED` | No | **Section 3 not obtained.** `NotImplementedError`. URL/status log in that README. |

## SPLS yes/no

**No.** Hou et al., IPM 2013, DOI `10.1016/j.ipm.2013.01.004`. Unpaywall/OpenAlex/Semantic Scholar closed; arXiv `totalResults=0`; author `[PDF]` is the Elsevier DOI; HKU Find@HKUL is a JS catalog with no authenticated PDF in this session; Scholars Hub 403. Paywalls were not bypassed. LSDA arXiv:1705.01206 is a different parameterization and was not implemented. Full table: [`baselines/spls/README.md`](../baselines/spls/README.md).

## LDA-SC

Still `APPROXIMATE`. Off the faithful main table. `experiments/protocol.py` `APPROXIMATE_METHODS = ("lda_spectral",)`. Phase 1: no LDA-SC jobs. Our Reproduction: none.

## Tests (this round)

Touched this round: K-means default-init test; LDA-SC `fit_predict_oneshot`; SPLS error text. Command from `v1/` with `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`:

```text
python -m pytest baselines -q
```

Result, 2026-10-21: **13 passed in 0.89s**. Import check: `imports-ok`. SPLS still raises `NotImplementedError`. Tiny synthetic tests only; not the paper’s benchmark.
