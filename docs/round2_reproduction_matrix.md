> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Round 2 reproduction matrix (D1-D12)

Date: 2026-10-21; worktree `v1/`; hardware target 8 CPUs/16 GB. ACC/NMI are percent values from actual `runs/round2/` jobs, not paper-table copies. Historical `runs/` and `runs/repair_round1/` were not overwritten; no Git commit was made at this stage.

Git HEAD: `f9c381487d8a4915f35c2eadb638b5f28d830b11` (v1), with uncommitted changes. Measurements came from that dirty tree. Registry: `results/round2/experiment_registry.csv`.

Fidelity labels: A_PAPER_FAITHFUL / B_AMBIGUITY / C_DIAGNOSTIC. The faithful table used E8 (S+2 gamma L); E13 (S+gamma L) was separate. K-means defaulted to random, n_init=1, with 50 external seeds. Seeds were not selected by ACC. Mean/SD covered all completed trials, with minimum inertia recorded separately. Invalid/C variants were not advanced to 50 trials.

SC and SSC shared F under the same SpectralGraphConfig, with largest-magnitude eigenvector entries positive. prepare_spectral no longer switched backend for n>1500.

## Identities of versions used

| Dataset | Version | Identity | Original-source status |
| --- | --- | --- | --- |
| ORL | `olivetti` | `approximate_olivetti_64_to_32_not_att92_native` | **No** |
| ORL | `att92` | `original_source_att92_92x112_bilinear_32x32` | Yes (interpolation unspecified; not PAPER_PROTOCOL_MATCHED) |
| ORL | `att92_nearest` / `att92_bicubic` | Same archive; interpolation B | AT&T source; interpolation B |
| JAFFE | `zenodo` | `verified_zenodo_213_not_paper_unpublished_copy` | Verified archive; not unreleased paper preparation |
| YaleB | `dengcai32` | `approximate_dengcai32_not_claimed_sample_identity_with_paper` | No |
| YaleB | `cropped2414` | `obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai` | Official cropped archive; no Deng Cai pixel-identity claim |
| USPS | `libsvm` | `verified_libsvm_9298` | Verified; pilot \(n=3\), not 50-trial protocol |

## D1: Data sources under the same SC settings

Configuration: Equation (4), k=5, union kNN, median positive directed k-neighbor squared-distance bandwidth, raw eigenvectors, random K-means. Olivetti was not labelled original-source.

Verified historical v1 ORL SC: ACC 54.2±3.1 (n=50), NMI 76.5±1.6, baselines.spectral backend, Olivetti 64 to 32. Track A `20261020_015207__TRACKA__SC__ORL__a86c9d70` and Track B `20261020_015621__TRACKB__SC__ORL__263aa38a` both had acc_mean=0.54215.

| Factor | version | Fidelity | \(n\) | ACC | NMI | Edges / components | \(\delta^2\) | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D01_OLIVETTI_SC | olivetti | A | 50 | 53.9±3.0 | 76.5±1.7 | 1329 / 2 | 7.093 | `20261021_161536__ROUND2__ORL__D01_OLIVETTI_SC__9118018b` |
| D01_ATT92_SC | att92 | A | 50 | 56.2±4.2 | 80.5±2.3 | 1273 / 3 | 9.337 | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |
| D01_ATT92_NEAREST_SC | att92_nearest | B | 5 | 57.7±4.5 | 81.0±3.0 | 1286 / 2 | — | `20261021_161538__ROUND2__ORL__D01_ATT92_NEAREST_SC__e6bb4f6e` |
| D01_ATT92_BICUBIC_SC | att92_bicubic | B | 5 | 54.8±5.0 | 79.8±3.1 | 1278 / 3 | — | `20261021_161539__ROUND2__ORL__D01_ATT92_BICUBIC_SC__5d93088d` |

Paper ORL SC: 72.7±2.3; SSC: 76.0±1.6. Sharing F changed Olivetti SC by -0.3 pp versus historical 54.2. att92 gained 2.3 pp over Olivetti but remained -16.5 pp below paper SC. Nearest/bicubic were not advanced to 50 trials.

## D2: Graph A, shared F, and spectrum

Reference: `results/round2/d2_shared_f.json`; same SpectralGraphConfig with k=5, union, median directed bandwidth, Equation (4):

| version | SC \(F\) = SSC \(F\) | max‖Δ‖ | Undirected edges | Components | \(\delta^2\) | Near-zero eigenvalues of Eq.(4) |
| --- | --- | --- | --- | --- | --- | --- |
| olivetti | Yes | 0 | 1329 | 2 | 7.093 | 2 |
| att92 | Yes | 0 | 1273 | 3 | 9.337 | 3 |

The first eight combinatorial att92 eigenvalues included three numerical zeros (`combinatorial_laplacian_eigenvalues_A`), consistent with three components. Solver: scipy.linalg.eigh. This was a spectral diagnostic, not a clustering trial.

## D3-D6: One-factor diagnostics (ORL att92 SC; C uses n=5)

The first five default att92 seeds gave mean ACC 54.6: seeds 0-4 were 53.00, 48.75, 54.75, 59.75, 56.75. The complete n=50 default was 56.2±4.2.

| Factor | Change | Fidelity | \(n\) | ACC | Edges / CC | \(\delta^2\) | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D03_BW_MEAN_SC | Squared mean directed kNN Euclidean distance | B | 5 | 54.6±4.1 | 1273 / 3 | 9.171 | `20261021_161548__ROUND2__ORL__D03_BW_MEAN_SC__8f25437b` |
| D03_BW_UNDIRECTED_MEDIAN_SC | Median undirected squared edge distance | B | 5 | 55.6±3.8 | 1273 / 3 | 10.499 | `20261021_161549__ROUND2__ORL__D03_BW_UNDIRECTED_MEDIAN_SC__96ae6849` |
| D04_MUTUAL_SC | Mutual symmetrization (AND) | C | 5 | 49.6±3.8 | 727 / 46 | Same default scale | `20261021_161550__ROUND2__ORL__D04_MUTUAL_SC__64f5f71e` |
| D06_ROW_NORM_SC | Row-normalized eigenvectors | C | 5 | 67.7±3.1 | 1273 / 3 | 9.337 | `20261021_161551__ROUND2__ORL__D06_ROW_NORM_SC__c17f11c3` |

Bandwidth changes barely affected support. Mutual support was worse and more fragmented and did not advance to 50 trials. Row normalization gained about 11 pp but remained C and was not advanced because of favorable ACC.

## D7: W is built on F, separately from X

Source: w_vs_x_overlap in att92 E8 run `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0`.

- w_built_on: F
- X graph: 1273 undirected edges; F graph: 1217; overlap: 857; Jaccard 0.525.
- identical_to_x_graph: false.
- Weights were frozen before IRLS.

E13 had the same overlap because W used the same F: `20261021_161552__ROUND2__ORL__D08_E13_ATT92__a9ac25d0`.

## D8: E8 versus E13 (ORL att92, gamma=1, clustering G, n=50)

| Variant | Linear system | Fidelity | ACC | NMI | \(\lVert G-F\rVert_F\) | Equation (8) objective | IRLS | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E8 | \(A=S+2\gamma\widetilde L\) | A | 57.3±3.8 | 81.1±2.2 | 0.727 | 14.583 | Unconverged after 300 steps | `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` |
| E13 | \(A=S+\gamma\widetilde L\) | B | 56.7±4.1 | 80.8±2.2 | 0.443 | 16.969 | Unconverged after 300 steps | `20261021_161552__ROUND2__ORL__D08_E13_ATT92__a9ac25d0` |
| SC / K-means(\(F\)) | No shrinkage | A | 56.2±4.2 | 80.5±2.3 | — | — | — | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |

E8 lowered the objective without a material clustering improvement over E13/SC. E8 remained -18.7 pp from paper SSC 76.0. The optimizer was not changed to pursue ACC.

## D9: IRLS optimality and convergence

| Setting | \(n\) | Converged | Steps | Equation (8) | ACC | run_id |
| --- | --- | --- | --- | --- | --- | --- |
| E8 max_iter=300 | 50 | No | 300 | 14.58275 | 57.3±3.8 | E8 above |
| E8 max_iter=1000 | 5 | Yes | 825 | 14.58272 | 55.9±4.5 | `20261021_161555__ROUND2__ORL__D09_E8_ITER1000_ATT92__b959d78e` |

At 300 steps, fixed-point residual was 0.013. Extending the budget to 1000 barely changed the objective and did not improve ACC. The longer setting was not advanced to 50 trials.

JAFFE E13 converged at 263 steps, while E8 did not converge within 300. USPS E8 converged at 298. Both YaleB E8 versions reached 300 without convergence.

## D10/D11: K-means on saved F

F was computed once and saved as embedding_F.npy. Fifty random and fifty k-means++ trials used n_init=1. Mean/SD included every trial; minimum-inertia endpoints were separate and not chosen by ACC. Details: `results/round2/d10_d11_kmeans_on_saved_f.json`.

| Saved \(F\) | Source run | random ACC | Random minimum-inertia ACC | k-means++ ACC (B) | ++ minimum-inertia ACC |
| --- | --- | --- | --- | --- | --- |
| ORL olivetti SC | `…D01_OLIVETTI_SC__9118018b` | 53.9±3.0 | 62.75(seed 21, inertia 9.382) | 62.7±1.4 | 62.5(seed 37, inertia 5.469) |
| ORL att92 SC | `…D01_ATT92_SC__4fe80e2e` | 56.2±4.2 | 62.25(seed 21, inertia 9.935) | **78.3±1.3** | 79.0(seed 13, inertia 3.699) |
| ORL att92 E8 \(F\) | `…D08_E8_ATT92__d3809fd0` | 56.2±4.2 | Same as SC (same \(F\)) | 78.3±1.3 | Same as SC |
| JAFFE SC | `…D12_JAFFE_SC__2983a645` | 68.5±11.2 | 95.3(seed 23, inertia 0.623) | 95.3±0.0 | 95.3(seed 0, inertia 0.614) |

Saved att92 SC/E8 F produced identical random/++ measurements, consistent with D2 elementwise equality. k-means++ 78.3 exceeded paper SC 72.7 and SSC 76.0, but remained B_AMBIGUITY rather than faithful reproduction.

## D12: Fifty-trial shortlist (ORL att92 and JAFFE only)

| Dataset | Method | Fidelity | ACC | NMI | run_id |
| --- | --- | --- | --- | --- | --- |
| ORL att92 | SC | A | 56.2±4.2 | 80.5±2.3 | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |
| ORL att92 | SSC E8 | A | 57.3±3.8 | 81.1±2.2 | `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` |
| ORL att92 | SSC E13 | B | 56.7±4.1 | 80.8±2.2 | `20261021_161552__ROUND2__ORL__D08_E13_ATT92__a9ac25d0` |
| JAFFE zenodo | SC | A | 68.5±11.2 | 83.0±5.7 | `20261021_161557__ROUND2__JAFFE__D12_JAFFE_SC__2983a645` |
| JAFFE zenodo | SSC E8 | A | 68.4±11.1 | 83.0±5.7 | `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` |
| JAFFE zenodo | SSC E13 | B | 68.6±11.3 | 83.0±5.8 | `20261021_161559__ROUND2__JAFFE__D12_JAFFE_E13__50a3c90d` |

Paper references: ORL SC 72.7/SSC 76.0; JAFFE SC 76.1/SSC 81.2. Shrinkage gained less than 2 pp over K-means(F).

## YaleB (E8/SC, n=10 rather than 50)

| version | Method | ACC | NMI | Edges / CC | IRLS | run_id |
| --- | --- | --- | --- | --- | --- | --- |
| dengcai32 | SC | 20.1±1.2 | 29.9±0.9 | 8568 / 1 | — | `20261021_161602__ROUND2__YALEB__D01_DENGCAI32_SC__6411988e` |
| dengcai32 | E8 | 19.5±1.5 | 29.3±1.2 | 8060 / 13 | Unconverged at 300 | `20261021_161603__ROUND2__YALEB__D08_DENGCAI32_E8__27f746d1` |
| cropped2414 | SC | 18.1±1.3 | 26.6±0.6 | 8510 / 1 | — | `20261021_161625__ROUND2__YALEB__D01_CROPPED2414_SC__d1a360fb` |
| cropped2414 | E8 | 17.4±1.1 | 26.0±1.1 | 7957 / 13 | Unconverged at 300 | `20261021_161626__ROUND2__YALEB__D08_CROPPED2414_E8__5fb5af8b` |

Paper YaleB: SC 34.8, SSC 49.8. cropped2414 did not improve results; Deng Cai SC 20.1 was unchanged from Round 1.

## USPS (E8/SC pilot, n=3; timeout permitted)

Both executions completed without TIMEOUT.

| Method | ACC | NMI | IRLS | run_id |
| --- | --- | --- | --- | --- |
| SC | 63.8±1.7 | 77.4±3.9 | — | `20261021_161647__ROUND2__USPS__D12_USPS_SC__6324d037` |
| E8 | 60.7±4.0 | 76.8±3.1 | Converged at 298 steps, \(\lVert G-F\rVert_F=0.071\) | `20261021_161650__ROUND2__USPS__D08_USPS_E8__c638f49b` |

Paper USPS: SC 64.3, SSC 75.5. The n=3 SC estimate was near 64.3, while E8 was about 15 pp lower. Three trials did not meet the 50-trial protocol. The shared path had no n>1500 backend switch.

## Extension: same-F mutual-kNN versus SSC (JAFFE n=50)

This category C diagnostic was executed within the available time.

| Method | ACC | Edges / CC | \(\lVert G-F\rVert_F\) | Converged | run_id |
| --- | --- | --- | --- | --- | --- |
| SSC E8 union | 68.4±11.1 | 655 / 9 | 0.093 | No(300) | `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` |
| RSSC mutual | 68.4±11.2 | 410 / 20 | 0.077 | Yes (241) | `20261021_161924__ROUND2__JAFFE__EXT_JAFFE_MUTUAL_KNN__45fd1c1f` |

Negative finding: fewer edges and more components did not improve ACC.

## Remaining gaps under the faithful protocol

| Dataset | Paper SC | Our SC | Paper SSC | Our E8 | Remaining SC / E8 (pp) |
| --- | --- | --- | --- | --- | --- |
| ORL att92 \(n=50\) | 72.7±2.3 | 56.2±4.2 | 76.0±1.6 | 57.3±3.8 | −16.5 / −18.7 |
| ORL olivetti \(n=50\) | 72.7 | 53.9±3.0 | 76.0 | (Olivetti E8 not rerun in this round) | −18.8 / — |
| JAFFE \(n=50\) | 76.1±1.6 | 68.5±11.2 | 81.2±1.6 | 68.4±11.1 | −7.6 / −12.8 |
| YaleB dengcai \(n=10\) | 34.8±1.4 | 20.1±1.2 | 49.8±1.6 | 19.5±1.5 | −14.7 / −30.3 |
| USPS \(n=3\) | 64.3±1.4 | 63.8±1.7 | 75.5±1.9 | 60.7±4.0 | −0.5 / −14.8(\(n=3\)) |

Higher k-means++ and row-normalized results are in the root-cause analysis; they are excluded from the faithful table.