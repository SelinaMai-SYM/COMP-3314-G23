# PCA + spectral clustering

**Package status:** `PAPER_FAITHFUL_REIMPLEMENTATION` of “PCA, then the Eq. (4) spectral baseline”. Same dimension-step `AMBIGUITY_RECONSTRUCTION` as PCA-KM. Spectral \(\delta\) / union graph inherit SC’s reconstructions.

Master index: [`baselines/README.md`](../README.md).

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| Named baseline | Chang et al., AAAI 2015, “PCA spectral clustering (PCA SC)”. No separate source paper. Spectral step is their Eq. (4). Setup: 10…150, `k=5`. | `VERIFIED ORIGINAL PUBLICATION` |
| Author code | None located. | not `VERIFIED AUTHOR CODE` |
| This package | PCA then `baselines.spectral_clustering.fit_predict` | `INDEPENDENT REIMPLEMENTATION` of the named pipeline |

## Original math (original equation numbers)

1. PCA variance objective in `n_components` dimensions (no equation number in Chang et al.).
2. Then Chang et al. Eq. (3)–(4) in the projected coordinates, with Setup `k=5`.

## Original algorithm mapped to paper sections

| Paper step | Where | This package |
| --- | --- | --- |
| PCA | Setup 10…150 | `PCA(svd_solver="full")` (`pca_spectral.py` 60–61) |
| SC Eq. (4) | Eq. (4), Setup k=5 | `baselines.spectral_clustering.fit_predict` (line 62) |
| Dimension search | Setup; step unspecified | not inside this function |

## Our implementation mapped to real files

Import: `from baselines.pca_spectral import fit_predict`

| Piece | File | Function | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Defaults (spectral + K-means) | `baselines/pca_spectral/pca_spectral.py` | `_DEFAULTS` | 13–22 |
| Public fitter | same | `fit_predict` | 25–62 |
| Required `n_components` | same | `TypeError` if missing | 48–49 |
| PCA | same | `PCA(..., svd_solver="full")` | 60–61 |
| Spectral step | `baselines/spectral_clustering/spectral_clustering.py` | `fit_predict` | via line 62 |

## Fidelity audit

| Item | Status | Notes |
| --- | --- | --- |
| PCA then Eq. (4) SC | `PAPER_FAITHFUL_REIMPLEMENTATION` | |
| `k=5` default | `PAPER_FAITHFUL_REIMPLEMENTATION` | |
| dim grid step 10 | `AMBIGUITY_RECONSTRUCTION` | protocol |
| \(\delta\), union kNN | `AMBIGUITY_RECONSTRUCTION` | inherited from SC |

## SSC comparison protocol vs this baseline’s own paper settings

Same 10…150 sentence as PCA-KM. Spectral settings follow the SC baseline (`k=5`, union, median \(\delta^2\) unless overridden). Chang et al. give no extra PCA-SC hyperparameters.

## Tests actually run

`baselines/pca_spectral/test_pca_spectral.py`: `test_pca_spectral_dimension_is_required_and_used` (line 32). Tiny blobs only.

## Experimental results

Track A used **10 trials per dimension** (cost triage), not 50.

| Dataset | Paper ACC% | Our Track A | Track A run_id | Track B | Track B run_id |
| --- | --- | --- | --- | --- | --- |
| JAFFE | 76.9 ± 1.8 | 69.8 ± 8.3 (n=10, dim=70) | `20261020_015528__TRACKA__PCASC__JAFFE__954f8128` | 60.0 ± 7.4 (n=50) | `20261020_015805__TRACKB__PCASC__JAFFE__ebef5506` |
| ORL | 67.8 ± 2.1 | 54.9 ± 2.7 (n=10, dim=100) | `20261020_015325__TRACKA__PCASC__ORL__cf34bead` | 53.0 ± 3.1 (n=50) | `20261020_015630__TRACKB__PCASC__ORL__afa6d100` |
| YaleB / USPS / missing sets | see paper | N/A — not reproduced | — | N/A — not reproduced | — |

## Limitations

- Track A n=10 per dim is a cost choice, not the paper’s 50.
- Selected dims unpublished.

## Reproduction commands

```text
python -m pytest baselines/pca_spectral -q
```

## Task 1（2026-10-21）

无新文件。作者代码 `CODE_NOT_FOUND`。矩阵状态：`COMPLETE_WITH_UNSPECIFIED_SETTINGS`。
