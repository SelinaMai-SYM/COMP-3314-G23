> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Repair round 1: closest reconstructions ordered by fidelity

Date: 2026-10-20. Hardware: 8 CPUs, 16 GB. All measurements came from actual runs and report completed n. Paper ACC/NMI are references, not our results. Category C is not the paper method. Track B fixed gamma=1 without label-based gamma selection.

Ranking at this historical stage prioritized fidelity, then numerical proximity to the paper.

| Category | Meaning | Paper-method claim |
| --- | --- | --- |
| A A_PAPER_FAITHFUL | Equation (8) stationary system, S+2 gamma L, k=5, union kNN, median bandwidth, raw eigenvectors, G0=F, random K-means | Faithful variant under the derived printing corrections |
| B B_AMBIGUITY | Printed Equation (13), unspecified bandwidth, k-means++ and related choices | Reconstruction, not the derived Equation (8) target |
| C C_DIAGNOSTIC | K-means(F), row-normalized eigenvectors, mutual-kNN extension | No |

The 31-run ORL one-factor matrix was not rerun. Phase 1 runs were retained. Six FAILED YaleB ARPACK diagnostics remained in `runs/repair_round1/` and the registry; clustering was subsequently rerun successfully.

# Comparison: paper, old v1, and repaired execution

Explicit columns are in `results/repair_round1/reproduction_comparison.csv` and `.tex`; results below are grouped by dataset.

### JAFFE (verified Zenodo 213x676, \(n=50\))

Identity: `verified_zenodo_213_not_paper_unpublished_copy`; no sample-level identity with the unreleased paper-preprocessed copy is claimed.

Paper: ACC 81.2±1.6, NMI 84.3±1.6. Old v1 gamma=1: 68.6±11.3 (n=50), `20261020_015452__TRACKA__SSC__JAFFE__536c9eb1`.

| Fidelity | Setting | ACC | NMI | \(n\) | run_id |
| --- | --- | --- | --- | --- | --- |
| A faithful | E8, cluster \(G\) | 68.4±11.1 | 83.0±5.7 | 50 | `20261020_033024__REPAIR1__JAFFE__D12_KMEANS_G_E8__ee463086` |
| B default reconstruction | E13, cluster \(G\) | 68.6±11.3 | 83.0±5.8 | 50 | `20261020_033023__REPAIR1__JAFFE__D12_KMEANS_G_E13__c943774b` |
| B ambiguity | E13 + k-means++ | 95.3±0.0 | 94.1±0.0 | 50 | `20261020_033025__REPAIR1__JAFFE__D09_KM_PLUSPLUS__585e102e` |
| C diagnostic | K-means(\(F\)) | 68.5±11.2 | 83.0±5.7 | 50 | `20261020_033021__REPAIR1__JAFFE__D12_KMEANS_F__e8036aab` |
| C diagnostic | row-normalized eigenvectors | 85.0±9.4 | 91.8±4.1 | 50 | `20261020_033027__REPAIR1__JAFFE__D05_ROW_NORM__b613c07e` |
| C extension | mutual kNN RSSC | 68.7±11.3 | 83.0±5.9 | 50 | `20261020_034223__REPAIR1__JAFFE__EXT_MUTUAL_KNN__c13071f7` |

- Faithful A E8 gave 68.4, or -12.8 pp from the paper. IRLS did not converge in 300 steps; movement was 0.093, with nine graph components and 655 undirected edges.
- The closest A/B reconstruction was E13 68.6 (B). k-means++ reached 95.3, above the paper, but was an ambiguity reconstruction. Zero ACC SD across 50 seeds described nearly deterministic rounding on that embedding, not reproduction of 81.2.
- The closest C result was row normalization at 85.0. Its approximate +6 pp ORL effect grew to +16.4 pp on JAFFE, supporting transfer of that diagnostic change; it remained C.
- Shrinkage supplied little benefit: K-means(F) 68.5 versus E13 68.6.

### ORL (Olivetti 64 to 32; 31-run matrix not rerun; shortlist n=50)

Identity: `approximate_olivetti_64_to_32_not_att92_native`.

Paper: ACC 76.0±1.6, NMI 88.6±1.5. Old v1: 53.9±3.0 (n=50); gamma=1 E13: 53.7±2.8.

| Fidelity | Setting | ACC | NMI | \(n\) | run_id |
| --- | --- | --- | --- | --- | --- |
| A faithful | E8 | 53.3±3.2 | 76.2±1.8 | 50 | `20261020_032508__REPAIR1__ORL__D12_KMEANS_G_E8__d484f3c9` |
| B default | E13 | 53.7±2.8 | 76.7±1.5 | 50 | `20261020_032506__REPAIR1__ORL__D12_KMEANS_G_E13__3cdaa69b` |
| B closest A/B | E13 + k-means++ | 62.1±1.6 | 80.3±0.7 | 50 | `20261020_032509__REPAIR1__ORL__D09_KM_PLUSPLUS__2fa139a6` |
| C diagnostic | K-means(\(F\)) | 53.9±3.0 | 76.5±1.7 | 50 | `20261020_032504__REPAIR1__ORL__D12_KMEANS_F__3c9cd874` |
| C diagnostic | row normalization | 60.2±2.9 | 80.1±1.2 | 50 | `20261020_032512__REPAIR1__ORL__D05_ROW_NORM__b7fe4814` |
| C extension | mutual kNN | 54.0±2.8 | 76.6±1.5 | 50 | `20261020_034225__REPAIR1__ORL__EXT_MUTUAL_KNN__91b78dec` |

- Shrinkage did not help: F 53.9 versus E13 53.7. E8 lowered the objective but clustering was slightly worse. No A/B setting approached 76%.
- Closest A/B was k-means++ 62.1 (n=50, distinct from the n=5 value 62.5), still about 14 pp below.

### YaleB (Deng Cai 32x32; n=10, not 50)

Identity: `approximate_dengcai32_not_claimed_sample_identity_with_paper`. No sample identity with the paper or other YaleB versions is claimed.

Paper: ACC 49.8±1.6, NMI 46.8±1.3. Old v1 gamma=1: 19.7±1.1 (n=10).

| Fidelity | Setting | ACC | NMI | \(n\) | run_id |
| --- | --- | --- | --- | --- | --- |
| A faithful | E8 | 19.5±1.5 | 29.3±1.2 | 10 | `20261020_033639__REPAIR1__YALEB__D12_KMEANS_G_E8__3ab7c3f0` |
| B default | E13 | 19.7±1.1 | 29.5±1.0 | 10 | `20261020_033606__REPAIR1__YALEB__D12_KMEANS_G_E13__537ad7be` |
| B closest A/B | E13 + k-means++ | 25.2±0.6 | 30.9±0.8 | 10 | `20261020_033710__REPAIR1__YALEB__D09_KM_PLUSPLUS__72eaaecc` |
| C diagnostic | K-means(\(F\)) | 20.1±1.2 | 29.9±0.9 | 10 | `20261020_033532__REPAIR1__YALEB__D12_KMEANS_F__20297104` |
| C diagnostic | row normalization | 26.7±1.8 | 37.4±0.7 | 10 | `20261020_033741__REPAIR1__YALEB__D05_ROW_NORM__fe5fbdd4` |
| C extension | mutual kNN | 20.0±1.3 | 29.8±1.2 | 10 | `20261020_034227__REPAIR1__YALEB__EXT_MUTUAL_KNN__4869bdff` |

- Shrinkage did not help: F 20.1 versus E13 19.7. All IRLS runs reached 300 iterations without convergence; the graph had 13 components and 8060 edges.
- k-means++ transferred to YaleB (+5.5 pp). The JAFFE row-normalization improvement of at least 5 pp triggered its YaleB diagnostic; YaleB gained 7.0 pp, still category C and far below 49.8.
- Bilinear cropped2414 E13 gave 18.0±0.7 (n=10), NMI 26.4±0.7, `20261020_033811__REPAIR1__YALEB__D01_CROPPED2414_E13__cbd4d1ff`. Identity: `obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai`. ACC did not improve; pixel identity with Deng Cai was not claimed.

### USPS (LIBSVM 9298; pilot only)

Identity: `verified_libsvm_9298`. This was not a 50-trial reproduction; no smaller subset was substituted for 9298.

Paper: ACC 75.5±1.9, NMI 79.8±1.6. Old v1: 62.1 (n=1).

E13 gamma=1, three K-means seeds and sparse IRLS gave ACC 63.8±1.7, NMI 77.5±4.0 (n=3), convergence at 171 iterations, movement 0.038, and one component. Run: `20261020_033852__REPAIR1__USPS__D12_KMEANS_G_E13__5c5f8321`. Wall time was about 205 seconds, without TIMEOUT. E8, F, k-means++, row normalization, and RSSC were not run. The gap was about -12 pp, and n=3 did not meet the paper protocol.

## Did shrinkage help on any dataset?

No material gain was observed in these comparisons of K-means(F) and E13 clustering of G:

- ORL：53.9 vs 53.7
- JAFFE：68.5 vs 68.6
- YaleB：20.1 vs 19.7

E8 often moved farther from F and lowered Equation (8), without improving clustering.

## Transfer of k-means++ and row normalization

- k-means++ (B) transferred: ORL 62.1 (+8.4 pp), JAFFE 95.3 (+26.7 pp; zero SD over 50 seeds), YaleB 25.2 (+5.5 pp). The precise initializer was unspecified; the historical protocol used random starts. JAFFE 95.3 was not faithful reproduction.
- Row normalization (C) transferred: ORL 60.2, JAFFE 85.0 (+16.4 pp, triggering YaleB), YaleB 26.7. It remained a diagnostic change, not the paper method.

## Extension: mutual-kNN versus original SSC

Comparisons used the same data, preprocessing, representation (raw eigenvectors, k=5, median F bandwidth followed by mutual filtering), gamma=1, and seeds. RSSC was category C.

| Dataset | union SSC ACC | mutual RSSC ACC | \(\lVert G-F\rVert\) SSC / RSSC | Components SSC / RSSC | Edges SSC / RSSC | IRLS s SSC / RSSC | Converged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JAFFE n=50 | 68.6±11.3 | 68.7±11.3 | 0.050 / 0.033 | 9 / 20 | 655 / 410 | 0.20 / 0.40 | Yes / Yes(298 steps) |
| ORL n=50 | 53.7±2.8 | 54.0±2.8 | 0.650 / 0.473 | 13 / 42 | 1242 / 758 | 0.63 / 0.54 | No / No |
| YaleB n=10 | 19.7±1.1 | 20.0±1.3 | 0.292 / 0.182 | 13 / 176 | 8060 / 4010 | 7.19 / 2.66 | No / No |

The negative result was preserved: mutual support had fewer edges and more components, with ACC differences below 1 pp. Phase 1 EX1 gave 53.7 versus 54.0, 68.6 versus 68.7, and 19.7 versus 19.9; paired repair-round results agreed. USPS extension was not run.

## Remaining paper gaps

Faithful A/E8 gaps: JAFFE -12.8 pp, ORL -22.7 pp, YaleB -30.3 pp (n=10). USPS had only B/E13 at n=3, gap -11.7 pp.

Closest A/B results, still excluding C: JAFFE E13 68.6 (-12.6 pp), ORL k-means++ 62.1 (-13.9 pp), YaleB k-means++ 25.2 (-24.6 pp), USPS E13 63.8 (-11.7 pp, n=3).

No faithful or A/B setting closed the gap to ORL 76% or YaleB 49.8%. JAFFE 95.3/85.0 came from B/C changes and cannot be described as the paper SSC result.