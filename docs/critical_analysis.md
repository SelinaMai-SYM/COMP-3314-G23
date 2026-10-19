# Critical analysis

This note separates **confirmed** implementation facts, **plausible** experimental discrepancies, and **unresolved** questions. Experimental numbers below are filled only from completed run directories under `runs/`. They are not copied from Chang et al. (2015).

## Confirmed: the convex subproblem is not the clustering pipeline

Equation (8) is convex in `G` for nonnegative frozen `W`. The IRLS linear step implemented here is Equation (13),

\[
G=(S+\gamma\widetilde L)^{-1}SF.
\]

Two facts follow and are locked:

1. **A stationary point of Equation (13) is not a stationary point of the printed Equation (8).** Differentiating Equation (8) with symmetric `W` gives `(S+2\gamma\widetilde L)G=SF`. The printed Equation (13) therefore solves the convex problem whose graph term has coefficient `\gamma/2`, not `\gamma`. A small CVXPY check (`n=6`, `c=2`, `\gamma=0.8`) is in `docs/ssc_mathematical_audit.md`. `\gamma` was **not** silently doubled to hide this.
2. **Even a globally optimal `G` does not uniquely determine a clustering.** K-means on the rows of `G` is a nonconvex assignment step. Different random initializations produce different labels and different ACC/NMI. Convexity of the shrinkage subproblem is not uniqueness of the reported clustering metrics. This is why every trial is stored.

Related confirmed corrections, also in the audit:

- `S` is `n\times n` and row-wise, not an embedding-dimension diagonal as written in Equation (10).
- Algorithm 1 line 10 is not used (`\widetilde W` vs `\widetilde L`, `X` vs `F`).
- `G_0=F`. The first all-zero residual uses a median pairwise row-distance floor, otherwise IRLS stays at `F`.
- Bandwidth is the median of positive kNN squared distances. `k=5` unless an EX6 job says otherwise.

## Confirmed: Track A selection is label-informed

The paper says to report the best results and also prints mean±std after 50 random initializations. Those sentences are not the same protocol. This reproduction:

- saves every completed trial;
- for Track A, selects the setting (e.g. `\gamma` or subspace dimension) with the highest mean ACC, using labels;
- then reports mean±std over **all** completed trials of that setting;
- never claims 50 trials when fewer finished.

Track B freezes `\gamma=1` and a prespecified DR dimension `min(50, n_clusters, n-1, d)` (LDA: `K-1`) without labels. Tables for the two tracks are separate.

## Confirmed: what was not implemented

- SPLS / SLPS: `NOT_IMPLEMENTED`. Tables say `N/A — not reproduced`.
- LDA-SC: `APPROXIMATE` (Ding–Li alternation with spectral clustering in the subspace). It is kept off the main faithful table.
- AR, UMIST, BinAlpha, MSRA50: unavailable. Loaders raise `DatasetUnavailable`. No synthetic stand-ins.

## Confirmed: the extension is an adaptation

Mutual kNN on the shrinkage weights of SSC was not found as that combination (`docs/literature_review.md`). Chi and Lange (2015) freeze **union** kNN Gaussian weights for convex clustering. The extension deletes edges of `W` on `F` and keeps the original IRLS. Convexity of Equation (8) is unchanged because `W` stays nonnegative and frozen. No new theorem is claimed. Ablation A0 = original SSC, A1 = mutual kNN only.

## Plausible sources of gap versus Tables 1–2 of the paper

These can move ACC/NMI even when Equation (13) is solved correctly:

- ORL is the Olivetti 64×64 matrix resized to 32×32, not a confirmed 92×112 identity.
- YaleB is Deng Cai’s 32×32 matrix, not a from-scratch resize of the UCSD cropped PGMs.
- JAFFE and USPS match the paper’s counts.
- The paper does not specify `\delta`, K-means `n_init` inside one “run”, or the DR grid step.
- K-means here uses `init="random"` and one seed per trial, matching the paper’s “random initialization” more closely than `k-means++`.
- Equation (13) vs Equation (8) changes the effective `\gamma`. A paper implementation that followed line 10, or that used `2\gamma`, would not match this code.
- Track A “best results” may have meant best-of-50 objective rather than mean±std over 50 seeds.

## Unresolved

- Whether any official SSC code used Algorithm 1 line 10 as written.
- How the paper chose `\delta`.
- How UMIST was resized (dataset unavailable here).
- Whether 50 repetitions were 50 full SSC solves or 50 K-means on one `G`. This reproduction does the latter, which is what convexity of `G` suggests.
- Whether YaleB IRLS with `max_iter=300` reaches the paper’s implicit stopping point. The paper’s Figure 2 is not a numeric tolerance.

## Experimental discrepancies (from actual runs)

All percentages below are **Our Reproduction**, mean±std over the stated trial count, 100×ACC/NMI in `[0,1]`. Paper cells are labeled separately and were not copied into our metrics.

### Confirmed gaps versus Chang et al. (2015) Tables 1–2

| Dataset | Method | Paper ACC% | Ours ACC% | n | run_id |
| --- | --- | --- | --- | --- | --- |
| ORL | K-means | 60.5 ± 1.8 | 51.8 ± 3.3 | 50 | `20261020_015205__TRACKA__KMEANS__ORL__9c448e6b` |
| ORL | SC | 72.7 ± 2.3 | 54.2 ± 3.1 | 50 | `20261020_015207__TRACKA__SC__ORL__a86c9d70` |
| ORL | SSC (best γ) | 76.0 ± 1.6 | 53.9 ± 3.0 | 50 | `20261020_015209__TRACKA__SSC__ORL__5f95ad90` (γ=1e-6) |
| JAFFE | K-means | 75.6 ± 1.8 | 73.2 ± 5.7 | 50 | `20261020_015445__TRACKA__KMEANS__JAFFE__c6d76526` |
| JAFFE | SC | 76.1 ± 1.6 | 67.7 ± 11.3 | 50 | `20261020_015447__TRACKA__SC__JAFFE__097601c6` |
| JAFFE | SSC (best γ) | 81.2 ± 1.6 | 74.8 ± 8.4 | 50 | `20261020_015456__TRACKA__SSC__JAFFE__4d8acd1f` (γ=1e6) |
| YaleB | K-means | 14.4 ± 1.5 | 9.3 ± 0.6 | 10 | `20261020_015607__TRACKA__KMEANS__YALEB__e85daf75` |
| YaleB | SC | 34.8 ± 1.4 | 20.1 ± 1.2 | 10 | `20261020_015609__TRACKA__SC__YALEB__5e1920c1` |
| YaleB | SSC γ=1 | 49.8 ± 1.6 | 19.7 ± 1.1 | 10 | `20261020_015611__TRACKA__SSC__YALEB__cff9a04e` |
| USPS | K-means | 65.4 ± 1.7 | 66.3 ± 1.7 | 10 | `20261020_020247__TRACKA__KMEANS__USPS__6af21281` |
| USPS | SSC γ=1 | 75.5 ± 1.9 | 62.1 | 1 | `20261020_020231__TRACKA__SSC__USPS__829559a2` |

On ORL, SSC is statistically indistinguishable from SC under this protocol (53.9 vs 54.2). That contradicts the paper’s ranking. Plausible causes, in order of how well they are supported:

1. **Confirmed.** Equation (13) uses graph coefficient γ, which is the stationary point of Equation (8) with γ/2. If the paper’s binary followed line 10 or used 2γ, the shrinkage strength would differ.
2. **Confirmed.** Track A selection here is label-informed mean ACC over all trials, not an unpublished best-objective filter.
3. **Plausible.** ORL is Olivetti 64×64 resized to 32×32; YaleB is Deng Cai’s 32×32 mat. Neither is sample-level identity with a 92×112 ORL or a from-scratch UCSD YaleB resize.
4. **Plausible.** K-means is `init="random"`, one seed per trial. `k-means++` or inner `n_init>1` is not used.
5. **Unresolved.** Official SSC code was not available.

JAFFE is the closest match (K-means 73.2 vs 75.6; SSC 74.8 vs 81.2). Label-informed γ on JAFFE selected **1e6**, not 1. The paper’s remark that γ=1 is usually good does not hold on this JAFFE run. γ=1 on JAFFE is 68.6 ± 11.3 (`20261020_015452__TRACKA__SSC__JAFFE__536c9eb1`).

LLC on JAFFE **exceeds** the paper (88.4 ± 6.9, n=50, `20261020_015458__TRACKA__LLC__JAFFE__23d153da` vs 78.6 ± 1.5). That is a real run, not a copied cell. It does not imply the SSC numbers should be replaced by LLC.

### Extension (A0 vs A1)

γ=1, k=5, mutual kNN only on the shrinkage graph:

| Dataset | A0 SSC ACC | A1 RSSC ACC | n | Outcome |
| --- | --- | --- | --- | --- |
| ORL | 53.7 ± 2.8 | 54.0 ± 2.8 | 50 | mixed / negligible |
| JAFFE | 68.6 ± 11.3 | 68.7 ± 11.3 | 50 | mixed / negligible |
| YaleB | 19.7 ± 1.1 | 19.9 ± 1.3 | 10 | mixed / negligible |

Run ids: EX1 table in `results/tables/table5_ex1_ssc_vs_rssc.md`. The difference is inside the trial standard deviation. Robustness jobs (EX2–EX4) did not reverse that. Negative result kept.

### Protocol facts that are not paper matches

- YaleB: 10 trials, not 50. USPS SSC: 1 trial, not 50. Do not read those rows as a 50-run reproduction.
- PCA-SC Track A used 10 trials per dimension for selection (computational triage). LDA-KM used 10 trials per feasible dimension.
- Track B DR dimension is `min(50, n_clusters, n-1, d)` (LDA: `K-1`), not a label search.
- IRLS `max_iter=300` is an assumption. YaleB at 100 iterations had not met `tol=1e-6`.
- YaleB/USPS spectral clustering for n>1500 uses `SSC_method.spectral_embedding` (sparse eigsh), recorded in metrics as `ssc_method_sparse`.
- One Track A LDA-KM ORL dim=20 job failed mid-run (`NameError` during a layout migration) as `20261020_015425__TRACKA__LDAKM__ORL__fb14ac44`. It was rerun to completion as `20261020_020157__TRACKA__LDAKM__ORL__fb14ac44`. The FAILED directory was kept.

Full index: `results/run_index.csv`. Tables 1–8: `results/tables/`. Figures: `results/figures/` (PDF and SVG).
