# Research gap and the nine extensions

Source tree at the start of this round: `8e215ab859dfcf30d2ca9599f25c2abddc49ff8d`. Implementation, tests, and the P0 audit are commit `7459c9e1ab4654079be3244c3769d1b285149524`. This file describes the question. Measured cells are in `experimental_analysis.md`.

## Gap

The reconstructed control is SSC Equation (8) with Laplacian coefficient 2 (`variant="E8"`), `gamma=1`, `k=5`, `G0=F`, union kNN, median positive kNN squared distance, symmetric normalized Laplacian, random Lloyd, `n_init=1`, seeds 0..49. The class default `E13` (printed Equation 13, coefficient 1) is not this control.

On that control, prior `runs/strict_paper` records and the fresh `results/extension_research/extension_matrix.csv` agree on the direction: shrinkage at `gamma=1` is a small ACC change. ORL moves up by about one point. JAFFE and USPS stay at the spectral-clustering value. YaleB cropped2414 moves down (SC 0.1834, SSC 0.1763). Published Table 1, used only as historical context, lists YaleB SC 34.8% and SSC 49.8%. The gap is already present in K-means on F. D0–D6 in `P0_yaleb_root_cause.md` stay below both published figures. Conclusion of the implementation check: `NO CONFIRMED IMPLEMENTATION BUG`. `SSC_method/` and `baselines/` were not edited.

The extensions ask whether a pre-specified change to the weight, the data term, the embedding graph, or the K-means protocol changes that picture. Labels are used only for final ACC/NMI and for the separated diagnostics. They do not enter graph construction, initialization, weights, stopping, or the choice of gamma.

## Methods

Shared code is `method_extension/common/`. Each extension has `method.py`, `config.yaml`, `README.md`, and `tests/`. Existing `method_extension/mutual_knn.py` and `rssc.py` are unchanged. The fresh mutual-kNN row is an auxiliary E8 run, not one of the nine.

| ID | Directory | What is changed | Reduction check |
| --- | --- | --- | --- |
| E01 | `method_extension/e01` | T=10 isotropic perturbations of F, edge recurrence `p_ij`, `W' = W ⊙ p` with `beta=1`. `noise_rel=0.02`, `noise_seed=20260311`. | `noise_rel=0` matches the control W and G within 1e-5. |
| E02 | `method_extension/e02` | Data term `sum_i alpha_i ||g_i - f_i||_2`, `alpha_i = 0.5 + 1.5 * (mutual neighbors)/k`, fixed from F. Objective name `alpha_weighted_equation8`. | `alpha=1` matches E8 within 1e-5. |
| E03 | `method_extension/e03` | Zelnik–Manor local scale on A only (`E03-A`), on W only (`E03-W`), or both (`E03-AW`). Local scale is not a new method name. | Three placements are separate internal variants. |
| E04 | `method_extension/e04` | `E04-degree`: `W_ij / sqrt((d_i+eps)(d_j+eps))`, `eps=1e-12`. `E04-total`: divide by the total edge weight. | Total-edge normalization is a global rescaling of gamma. Config label `control_not_a_new_mechanism`. |
| E05 | `method_extension/e05` | `E05-fuse`: `lambda=0.5` mix of `W_F` and `W_X`. `E05-bilateral`: keep `W_F` only where `W_X` is nonzero. | Lambda is fixed. Pixel-space support is not assumed to be reliable on YaleB. |
| E06 | `method_extension/e06` | `n_outer=3`. F stays the anchor. W is rebuilt on the latest G and frozen inside each E8 solve. | Each frozen-W subproblem is the E8 objective. No global-convergence claim. |
| E07 | `method_extension/e07` | Same F and same G as the control. Protocols: random Lloyd seeds 0..49, k-means++, one inertia-best assignment, one consensus assignment. | Inertia-best minimizes inertia, not ACC. |
| E08 | `method_extension/e08` | E01 recurrence and E02 alpha, both frozen during the solve. | Ablation against SSC, E01, and E02. |
| E09 | `method_extension/e09` | E01 recurrence applied to the E03-W local-scale affinity. Initial F is the control F. | Ablation against SSC, E01, and E03-W. |

When an extension weight is exactly the original weight, G matches `shrink_embedding(..., variant="E8")` at `MATCH_ATOL = MATCH_RTOL = 1e-5`. Raw objective values are recorded under the objective's own name. They are not compared across different weights.

## What is eligible

From `configs/extension_dataset_registry.yaml`, locked before extension ACC was used for any choice:

| Dataset | Version | Status |
| --- | --- | --- |
| ORL | att92 | `PAPER_RECONSTRUCTION` |
| JAFFE | zenodo | `VERIFIED_SOURCE` |
| YaleB | cropped2414 | `PRIMARY_YALEB_VERSION` |
| YaleB | dengcai32 | `ALTERNATE_MATRIX_NOT_AN_INDEPENDENT_BENCHMARK` |
| USPS | libsvm | `VERIFIED_SOURCE` |
| BinAlpha | `CANDIDATE_BIN_ALPHA` | `NON_EXACT_DATASET` |
| UMIST | precropped575 | `NON_EXACT_DATASET` |
| MSRA50 | — | `BLOCKED_DATA` |
| AR | — | `BLOCKED`. Not called paper AR and not named `AR100_ZENODO`. |

Gamma grid `{1e-6, 1e-3, 1, 1e3, 1e6}` is stored in full. The comparison point remains `gamma=1`. The highest ACC in a block is written only to `results/extension_research/oracle_upper_bound.csv` with label `ORACLE_UPPER_BOUND`.
