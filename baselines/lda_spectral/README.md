# LDA + spectral clustering (APPROXIMATE)

**Package status:** `APPROXIMATE`

Chang et al. **name** “LDA spectral clustering / LDA SC” in the comparison list and Tables 1–2. They give **no algorithm, equation, or citation** for that construction. Ding and Li (ICML 2007) define the **K-means** version only. This folder therefore keeps two clearly named reconstructions. **Neither uses ground-truth labels. Neither belongs in a faithful main table**, even if a later ACC is closer to Chang et al.

Master index: [`baselines/README.md`](../README.md).

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| Name only | Chang et al., AAAI 2015, Experiment section: “LDA spectral clustering (LDA SC)”. OA PDF read 2026-10-21. No algorithm box. | `VERIFIED ORIGINAL PUBLICATION` for the **name**; construction **unspecified** |
| Closest written algorithm | Ding and Li, ICML 2007, Algorithm 1 (K-means, not spectral) | `VERIFIED ORIGINAL PUBLICATION` of a **different** method |
| Author code | None located. | not `VERIFIED AUTHOR CODE` |
| This package | two named reconstructions | `INDEPENDENT REIMPLEMENTATION` of **invented** loops |

## Original math (original equation numbers)

**There is no original LDA-SC equation in Chang et al.** Eq. (4) is ordinary SC. Ding–Li Eq. (7) and Algorithm 1 are LDA-KM.

What the code actually optimizes is therefore not a printed LDA-SC objective.

## Original algorithm mapped to paper sections

Chang et al.: **no mapping exists.** Setup still says `k=5` for spectral methods and 10…150 for DR methods. That does not specify:

- one-shot LDA after one spectral clustering vs alternation;
- whether LDA labels come from K-means or from SC;
- how many LDA directions.

Two named interpretations in this package:

| Name | Function | Construction | Status |
| --- | --- | --- | --- |
| `INTERPRETATION_A_ALTERNATE` | `fit_predict` | Ding–Li Algorithm 1 with `baselines.spectral_clustering.fit_predict` in place of K-means; loop until labels stabilize or `max_iter` | `APPROXIMATE` |
| `INTERPRETATION_B_ONESHOT` | `fit_predict_oneshot` | PCA init → SC once → LDA from those cluster labels → SC once in the LDA subspace → stop | `APPROXIMATE` |

A third idea mentioned in Round 1 (SC in an LDA subspace fit from initial K-means) is **not** implemented here and would also be `APPROXIMATE`.

## Our implementation mapped to real files

Import:

```python
from baselines.lda_spectral import fit_predict, fit_predict_oneshot
```

| Piece | File | Function | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Defaults | `baselines/lda_spectral/lda_spectral.py` | `_DEFAULTS` | 29–40 |
| Shared loop | same | `_run_lda_spectral` | 56–80 |
| Interpretation A | same | `fit_predict` | 83–118 |
| Interpretation B | same | `fit_predict_oneshot` | 121–153 |
| LDA / PCA helpers | `baselines/lda_kmeans/lda_kmeans.py` | `_pca_basis`, `_prepare_subspace`, `lda_basis` | reused; cluster labels only |
| Inner partition | `baselines/spectral_clustering/spectral_clustering.py` | `fit_predict` | default `k=5` |
| Export | `baselines/lda_spectral/__init__.py` | both names | — |

`fit_predict_oneshot` **rejects** `max_iter` and `y`. `fit_predict` rejects `y`. Rank still \(\le K-1\). No ground truth.

`experiments/methods.py` currently calls `fit_predict` (Interpretation A) if a job is scheduled. Phase 1 scheduled **no** LDA-SC jobs (`APPROXIMATE_METHODS` in `experiments/protocol.py`).

## Fidelity audit

| Item | Status | Notes |
| --- | --- | --- |
| Named in Chang et al. | name only | no construction |
| Interpretation A | `APPROXIMATE` | invented loop |
| Interpretation B | `APPROXIMATE` | invented oneshot |
| Cluster labels, never GT | required constraint, satisfied | does **not** promote status |
| Faithful main table | **No** | `experiments/protocol.py` `APPROXIMATE_METHODS` |

## SSC comparison protocol vs this baseline’s own paper settings

There is no “own paper” for LDA-SC. If the inner step is spectral, Chang’s `k=5` applies. Dimension 10…150 still cannot exceed \(K-1\) for classical LDA.

Do not put either interpretation in a faithful main table.

## Tests actually run

`baselines/lda_spectral/test_lda_spectral.py`:

- `test_lda_spectral_is_deterministic_without_ground_truth` (line 33)
- `test_lda_spectral_oneshot_is_named_and_rejects_iteration_and_y` (line 59)

Tiny blobs only. Not a clustering benchmark.

## Experimental results

**Our Reproduction: none.** Do not invent numbers.

Paper ACC% quoted only from Chang et al. Table 1: AR 44.5±1.3, JAFFE 77.4±1.9, ORL 68.3±2.4, UMIST 54.7±1.5, BinAlpha 45.1±1.4, MSRA50 55.1±1.7, YaleB 38.2±1.6, USPS 70.4±1.5.

Phase 1 `run_all_stages.py` did not schedule LDA-SC. Cells stay **N/A — not reproduced**.

## Limitations

- Unknown what Chang et al. actually ran.
- ACC closer to the paper would still not make either interpretation faithful.

## Reproduction commands

```text
python -m pytest baselines/lda_spectral -q
```
