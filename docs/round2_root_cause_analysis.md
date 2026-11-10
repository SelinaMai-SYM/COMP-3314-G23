> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Round 2 root-cause analysis

Date: 2026-10-21. Conclusions use only `runs/round2/` and verified Round 1 runs. Labels are CONFIRMED, SUPPORTED, PLAUSIBLE, or UNRESOLVED. Items without controlled comparisons remain UNRESOLVED. Paper table numbers are not our measurements.

Git HEAD was `f9c381487d8a4915f35c2eadb638b5f28d830b11`, with a dirty worktree. SC and SSC shared the same F under identical settings (`results/round2/d2_shared_f.json`, maximum difference zero).

## 1. Earliest observed stage of the ORL gap to paper SC 72.7

CONFIRMED: the gap appeared in K-means on Equation (4) F, before IRLS.

Evidence:

- On att92, SC/K-means(F) gave 56.2±4.2 (n=50, `…D01_ATT92_SC__4fe80e2e`); E8 clustering G gave 57.3±3.8 (`…D08_E8_ATT92__d3809fd0`), and E13 56.7±4.1. Shrinkage gained less than 2 pp.
- Random K-means on the same saved F again gave 56.2 (D10).
- The paper SC target was 72.7; 76.0 was SSC. The SC stage already had a 16.5 pp gap, which these shrinkage results did not recover.

An IRLS implementation error cannot explain poor SC itself because SC does not run IRLS.

## 2. Effect of sharing F relative to Round 1

CONFIRMED: Olivetti changed little, so this did not explain the gap to 72.7.

Verified historical v1 ORL SC runs `20261020_015207__TRACKA__SC__ORL__a86c9d70` and `20261020_015621__TRACKB__SC__ORL__263aa38a` had acc_mean=0.54215, or 54.2±3.1 (n=50), using baselines.spectral and sklearn NearestNeighbors on Olivetti 64 to 32.

Round 2 used the same Olivetti data and 50-seed protocol with shared knn_affinity: 53.9±3.0 (`…D01_OLIVETTI_SC__9118018b`), a 0.3 pp difference within the reported SD.

JAFFE SC was 68.5±11.2 versus Round 1 67.7±11.3. Deng Cai YaleB SC was unchanged at 20.1±1.2. USPS now used the shared path without the n>1500 switch; SC was 63.8±1.7 (n=3).

D2 confirmed elementwise SC/SSC F equality for Olivetti and att92. A shrinkage comparison using independently computed F would have been invalid and was not used.

## 3. att92 vs Olivetti

SUPPORTED: original-source att92 improved ACC by about 2.3 pp, insufficient to close the gap.

Under the same SC configuration and n=50, Olivetti gave 53.9±3.0 and att92 56.2±4.2. Graph statistics differed: 1329 edges/2 components/delta squared 7.09 versus 1273/3/9.34. Olivetti was not the original-source reconstruction.

att92 remained 16.5 pp below paper SC 72.7. Nearest interpolation gave 57.7±4.5 and bicubic 54.8±5.0 (n=5 each); neither advanced to 50 trials. Against the first-five att92 baseline 54.6, the interpolation effect remained UNRESOLVED due to insufficient trials.

## 4. A, bandwidth, symmetrization, and Laplacian

SUPPORTED: with union support and median directed bandwidth, two alternative global bandwidths changed ACC and edges little.

On att92 n=5, mean bandwidth gave 54.6±4.1 (delta squared 9.17), and undirected median 55.6±3.8 (10.50). Both had 1273 edges and three components; the default first-five mean was 54.6.

SUPPORTED: mutual symmetrization was worse (C): 49.6±3.8, 727 edges, 46 components (`…D04_MUTUAL_SC__64f5f71e`), without 50 trials.

CONFIRMED: the representation used the Equation (4) symmetric normalized Laplacian. Recorded normalized and combinatorial att92 spectra each had three near-zero eigenvalues, consistent with three components.

PLAUSIBLE but limited by D10: three components for 40 classes suggests coarse graph structure. Disconnection guarantees only three trivial directions and cannot by itself explain the gap: k-means++ reached 78.3 on the same F, demonstrating available class structure.

## 5. Row normalization

SUPPORTED: ACC rose substantially, but the change remained C.

att92 row-normalized SC gave 67.7±3.1 ACC and 87.1±0.8 NMI (n=5), about +11 pp versus the first-five baseline. It did not advance to 50 trials and remained a diagnostic change even if it had. Its mean was still about 5 pp below 72.7.

## 6. Was W built on F?

CONFIRMED: att92 E8 recorded w_built_on=F, graph Jaccard with X of 0.525, 1217 versus 1273 edges, and identical_to_x_graph=false. W was frozen before IRLS.

## 7. E8 vs E13

SUPPORTED: E8 lowered the objective and moved farther from F, but clustering remained similar and well below 76.0.

At att92 gamma=1, n=50, E8 gave 57.3±3.8, Equation (8)=14.583, movement 0.727; E13 gave 56.7±4.1, Equation (8)=16.969, movement 0.443. The 0.6 pp difference did not justify changing the linear system to pursue ACC. The faithful table used E8.

JAFFE E8 68.4 and E13 68.6 were comparable to SC 68.5. Deng Cai YaleB E8 gave 19.5 versus SC 20.1. USPS E8 gave 60.7 versus SC 63.8 (n=3). These measured settings did not show the paper-scale shrinkage gain.

## 8. Did IRLS convergence explain the ACC gap?

CONFIRMED: ORL att92 E8 had not converged at 300 steps. SUPPORTED: continuing to convergence did not increase ACC.

At max_iter=1000, n=5, convergence occurred at 825 steps: objective 14.58272 versus 14.58275 at 300; ACC 55.9±4.5 versus shortlist 57.3. The 300-step fixed-point residual was 0.013. This continued setting was not called faithful or advanced to 50 trials.

## 9. K-means initialization versus best objective

CONFIRMED: random-start mean/SD was substantially below k-means++; lowest inertia was distinct from highest ACC and did not reach 72.7.

On saved att92 F, identical for SC and E8:

- Fifty random trials: 56.2±4.2; minimum-inertia seed 21 had ACC 62.25, selected by inertia rather than ACC.
- Fifty k-means++ trials (B): 78.3±1.3; minimum-inertia seed 13 had ACC 79.0.

Saved Olivetti F gave random ACC 53.9 and k-means++ 62.7±1.4, comparable to Round 1 Olivetti k-means++ 62.1.

Saved JAFFE F gave random 68.5±11.2 and k-means++ 95.3, with zero SD over 50 seeds. The minimum-inertia random trial also had ACC 95.3 (seed 23). This did not faithfully reproduce 81.2.

The paper stated random initialization and reported mean/SD, while its precise best-objective repetition hierarchy remained ambiguous. Switching the default to k-means++ was B_AMBIGUITY. att92 k-means++ 78.3 exceeded both paper SC 72.7 and SSC 76.0, suggesting that random rounding missed an existing partition in F. It did not establish that the authors used k-means++ or justify adding it to a faithful main table.

## 10. Did shrinkage help in any faithful setting?

CONFIRMED: measured gains did not reach the paper scale.

| Dataset | K-means(\(F\))/SC | E8 \(G\) |
| --- | --- | --- |
| ORL att92 \(n=50\) | 56.2 | 57.3 |
| JAFFE \(n=50\) | 68.5 | 68.4 |
| YaleB dengcai \(n=10\) | 20.1 | 19.5 |
| YaleB cropped \(n=10\) | 18.1 | 17.4 |
| USPS \(n=3\) | 63.8 | 60.7 |

## 11. YaleB cropped versus Deng Cai, and USPS

SUPPORTED: cropped2414 did not outperform Deng Cai: SC 18.1 versus 20.1 and E8 17.4 versus 19.5 (n=10). Both remained well below 34.8/49.8; historical sample identity was not claimed.

PLAUSIBLE: shared-path USPS SC approached paper 64.3, but SSC did not. SC was 63.8±1.7 versus 64.3; E8 was 60.7±4.0 versus 75.5 (n=3). Too few trials precluded a complete-protocol claim; the runs did not time out.

## 12. Mutual-kNN extension (JAFFE n=50)

CONFIRMED: same-F, same-E8 mutual support did not improve ACC: 68.4±11.2 versus union 68.4±11.1 (n=50), with 410 versus 655 edges and 20 versus nine components. This was executed, not skipped.

## 13. Unresolved issues

- Whether unreleased preprocessing, delta, and K-means behavior matched att92, median bandwidth, and sklearn Lloyd random.
- Whether paper 72.7 came from row normalization, k-means++, best-objective selection, or another graph rule. These diagnostic changes were B/C; better numbers did not identify the authors' choices.
- Nearest versus bicubic interpolation (n=5 only).
- A complete 50-trial gamma grid: this round's faithful shortlist fixed gamma=1.
- Fifty-trial USPS/YaleB execution.
- Why the paper SSC gain of 3.3 pp (76.0 minus 72.7) became about 1.1 pp here (57.3 minus 56.2).

## 14. Historical handover

1. The earliest verified discrepancy was random K-means on Equation (4) F, before IRLS or the E8/E13 coefficient.
2. Sharing F changed Olivetti SC from 54.2 to 53.9; this was not the main cause.
3. att92 improved about 2.3 pp over Olivetti but remained -16.5 pp from 72.7.
4. E8 versus E13 gave 57.3 versus 56.7; faithful E8 remained -18.7 pp from 76.0.
5. k-means++ gave 78.3±1.3 on att92 F (B); random minimum-inertia ACC was 62.3. Seeds were selected by inertia, not ACC.
6. Under faithful random rounding, remaining att92 gaps were -16.5 pp for SC and -18.7 pp for E8.