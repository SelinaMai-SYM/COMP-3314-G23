# PCA + K-means

**Package status:** `PAPER_FAITHFUL_REIMPLEMENTATION` of “PCA, then K-means”. The 10…150 dimension **step** is `AMBIGUITY_RECONSTRUCTION` and is **not** searched inside this fitter.

Master index: [`baselines/README.md`](../README.md).

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| Named baseline | Chang et al., AAAI 2015, “PCA Kmeans (Xu and Wunsch 2005)”. Setup: project to “a low dimensional subspace of 10 to 150 and report the best results.” | `VERIFIED ORIGINAL PUBLICATION` |
| Cited survey | Xu and Wunsch, IEEE TNN 2005. That survey does not define a new estimator. | `VERIFIED ORIGINAL PUBLICATION` (survey); the method is ordinary PCA then K-means |
| Author code | None located. | not `VERIFIED AUTHOR CODE` |
| PCA / K-means libraries | sklearn `PCA` + `baselines.kmeans` | `THIRD-PARTY` PCA; K-means as in `baselines/kmeans/` |

No GitHub URL is invented.

## Original math (original equation numbers)

Chang et al. do not reprint a PCA objective. sklearn `PCA(svd_solver="full")` centers \(X\) and maximizes captured variance in `n_components` coordinates (no whitening unless requested; this call does not whiten). Then Lloyd K-means in that subspace (Ding–Li Eq. (1) / this repo’s K-means objective).

## Original algorithm mapped to paper sections

| Paper step | Where | This package |
| --- | --- | --- |
| PCA projection | Chang et al. comparison list + Setup 10…150 | `PCA(...).fit_transform` (`pca_kmeans.py` 60–61) |
| K-means | Setup, random init | `baselines.kmeans.fit_predict` (line 62) |
| Dimension search 10…150 | Setup; **step unspecified** | **not inside this function**; Track A used `{10,20,…,150}` in `experiments/protocol.py` |

## Our implementation mapped to real files

Import: `from baselines.pca_kmeans import fit_predict`

| Piece | File | Function | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Defaults (K-means controls only) | `baselines/pca_kmeans/pca_kmeans.py` | `_DEFAULTS` | 13–19 |
| Public fitter | same | `fit_predict` | 22–62 |
| Required `n_components` | same | raises `TypeError` if missing | 47–48 |
| Full SVD PCA, centered, not whitened | same | `PCA(..., svd_solver="full")` | 60–61 |
| K-means | `baselines/kmeans/kmeans.py` | `fit_predict` | via line 62 |

`n_components` must be \(\le\min(n,d)\). The fitter does not clip silently.

## Fidelity audit

| Item | Status | Notes |
| --- | --- | --- |
| PCA then K-means | `PAPER_FAITHFUL_REIMPLEMENTATION` | |
| Center, no default whitening | `PAPER_FAITHFUL_REIMPLEMENTATION` of ordinary PCA | whitening not written in Chang et al. |
| Full SVD | `AMBIGUITY_RECONSTRUCTION` vs possible randomized SVD | explicit `svd_solver="full"` |
| Dimension grid step 10 | `AMBIGUITY_RECONSTRUCTION` | protocol, not this fitter |
| Inner K-means random init | `PAPER_FAITHFUL_REIMPLEMENTATION` | |

## SSC comparison protocol vs this baseline’s own paper settings

| Setting | Chang et al. 2015 | Xu–Wunsch 2005 | This fitter |
| --- | --- | --- | --- |
| Subspace dim | “10 to 150”, best result | not a new grid | required `n_components` |
| Step | unspecified | — | not searched here |
| K-means init | random | — | default `random` |

## Tests actually run

`baselines/pca_kmeans/test_pca_kmeans.py`: `test_pca_kmeans_dimension_is_required_and_used` (line 32). Tiny blobs only.

## Experimental results

| Dataset | Paper ACC% | Our Track A | Track A run_id | Track B | Track B run_id |
| --- | --- | --- | --- | --- | --- |
| JAFFE | 75.8 ± 1.5 | 74.8 ± 7.7 (n=50, dim=10) | `20261020_015501__TRACKA__PCAKM__JAFFE__6ca78d09` | 74.8 ± 7.7 (n=50) | `20261020_015803__TRACKB__PCAKM__JAFFE__e2b28f48` |
| ORL | 64.5 ± 2.3 | 53.0 ± 3.1 (n=50, dim=30) | `20261020_015234__TRACKA__PCAKM__ORL__8aaa1028` | 52.6 ± 2.9 (n=50) | `20261020_015626__TRACKB__PCAKM__ORL__3aa11ff9` |
| YaleB | 24.9 ± 1.8 | N/A — not reproduced (Track A) | — | 9.1 ± 0.6 (n=10) | `20261020_015840__TRACKB__PCAKM__YALEB__c60160aa` |
| others | see paper | N/A — not reproduced | — | N/A — not reproduced | — |

Selected Track A dimensions are label-informed (`experiments/protocol.py` `SELECTION_RULE`). That is disclosed protocol, not a claim that Chang used those dims.

## Limitations

- Unpublished selected dimensions in 2015.
- Grid step is an assumption.
- ORL/YaleB image identity is a dataset issue, not this fitter.

## Reproduction commands

```text
python -m pytest baselines/pca_kmeans -q
```
