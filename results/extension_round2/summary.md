# Conditional SSC extension evaluation on locked report cohorts

These cohorts were selected retrospectively against published targets. This is a conditional study, not unseen or unbiased test data. All methods use the same frozen H per cohort and feed optimized G directly to the locked rounding protocol. MSRA50 denotes the adapted native-16 EBSA source (1,799 samples, 12 classes); identity with the paper dataset is unverified.

The primary mechanism comparison is against quadratic QSSC at the prescribed 5% movement target. A fidelity change, nonzero movement, a smaller objective, or a geometric guarantee alone does not establish improved clustering.

| Cohort | SC ACC / NMI | Historical replay | Certified SSC reference | Original E1 reference | QSSC | E1_v2 | E4 | E5 | E6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AR | 68.979 / 84.187 | 51.210 / 72.940 | 57.148 / 80.588 | 69.181 / 84.284 U | 69.024 / 84.086 | 69.131 / 84.094 | 69.098 / 84.146 | 69.119 / 84.173 | 69.002 / 84.076 |
| JAFFE | 68.526 / 83.016 | 74.751 / 85.600 | 79.192 / 87.361 | 65.136 / 81.439 U | 69.700 / 83.404 | 68.883 / 82.969 | 68.648 / 83.007 | 70.854 / 83.946 | 70.432 / 83.727 |
| ORL | 72.725 / 87.492 | 74.630 / 89.714 | 74.540 / 89.689 | 75.700 / 89.997 U | 72.615 / 87.817 | 73.505 / 88.046 | 73.050 / 87.988 | 73.075 / 87.880 | 72.615 / 87.817 |
| UMIST | 63.950 / 81.002 | 69.968 / 85.165 | 70.110 / 85.234 | 70.372 / 85.548 U | 63.865 / 81.138 | 64.766 / 81.246 | 63.865 / 81.138 † | 63.131 / 80.656 | 63.865 / 81.138 |
| BinAlpha | 46.695 / 59.387 | 49.544 / 63.459 | 44.356 / 56.990 | 48.936 / 62.261 U | 46.349 / 59.259 | 46.459 / 59.258 | 46.567 / 59.293 | 46.315 / 59.250 | 46.344 / 59.253 |
| MSRA50 | 48.491 / 60.981 | 49.252 / 61.505 | 48.624 / 60.990 U | 48.334 / 61.141 U | 47.568 / 60.049 † | 48.140 / 60.431 † | 47.568 / 60.049 † | 48.320 / 60.329 | 47.568 / 60.049 † |
| YaleB | 45.148 / 54.367 | 44.239 / 52.608 | 44.249 / 52.648 | 43.912 / 52.497 U | 44.992 / 53.961 | 45.121 / 54.264 | 44.959 / 53.899 | 44.886 / 54.170 | 44.992 / 53.961 |
| USPS | 65.597 / 80.315 | 66.263 / 80.855 | 66.263 / 80.856 | 66.185 / 80.444 U | 66.154 / 80.959 | 66.085 / 80.347 | 65.707 / 80.268 | 66.126 / 81.041 | 66.154 / 80.959 |

Scores are percent means; complete same-configuration sample SDs are in primary_metrics.csv. ACC uses Hungarian matching and NMI uses geometric-mean entropy normalization. †: unqualified or unmatched intervention; U: uncertified unsquared reference. Missing entries remain NA. Native minimum-inertia assignments are diagnostic only and have no across-run SD.

## Stored historical reference

These frozen report measurements are not substituted for fresh outputs. Object identity checks are strict and include array storage representation; a mismatch alone does not quantify numerical value differences.

| Cohort | Stored ACC ± sample SD | Stored NMI ± sample SD | Replay G object matches stored |
|---|---:|---:|---|
| AR | 51.210 ± 2.005 | 72.940 ± 1.047 | True |
| JAFFE | 74.751 ± 8.371 | 85.600 ± 4.325 | True |
| ORL | 74.630 ± 0.635 | 89.714 ± 0.229 | True |
| UMIST | 69.968 ± 2.271 | 85.165 ± 1.000 | True |
| BinAlpha | 49.544 ± 2.707 | 63.459 ± 1.038 | True |
| MSRA50 | 49.252 ± 4.377 | 61.505 ± 3.888 | True |
| YaleB | 44.239 ± 0.816 | 52.608 ± 0.364 | True |
| USPS | 66.263 ± 1.702 | 80.855 ± 1.199 | True |

## Primary changes relative to fresh QSSC

- E1_v2: available-case mean ΔACC / ΔNMI = 0.179 / -0.057 percentage points; n=7/8. Missing: MSRA50. ACC wins/ties/losses 5/0/2; NMI 4/0/3.
- E4: available-case mean ΔACC / ΔNMI = -0.134 / -0.148 percentage points; n=6/8. Missing: UMIST;MSRA50. ACC wins/ties/losses 3/0/3; NMI 3/0/3.
- E5: available-case mean ΔACC / ΔNMI = 0.116 / 0.070 percentage points; n=7/8. Missing: MSRA50. ACC wins/ties/losses 3/0/4; NMI 5/0/2.
- E6: available-case mean ΔACC / ΔNMI = 0.101 / 0.044 percentage points; n=7/8. Missing: MSRA50. ACC wins/ties/losses 1/4/2; NMI 1/4/2.

The fixed .02/.10/.20 path, all three alignment controls and ORL/YaleB sensitivities remain separate. No best-performing path point replaces the .05 primary configuration. Intervals use 10,000 paired rounding-seed bootstrap draws (424242); fifty starts are not fifty independent datasets. They condition on the saved numerical embeddings and do not integrate solver approximation or historical-selection uncertainty.

## Mechanism evidence and limits

[Observed activation, correspondence controls and attribution](mechanism_evidence.md) give the data-dependent interpretation.

E1_v2 must move beyond the old fidelity and activate its relative stopping tubes before its mechanism is empirically tested. Coincident and uncertain edges are reported separately; the bound protects total dispersion rather than every edge or class.

E4 must change the graph under the recorded degree, mass and a-cost checks. Its real omitted band is compared with every row-permuted control; changed exchange mass is part of that comparison. An inactive certified graph is distinct from a failed QP fallback. Changed within/between-label masses are strictly post-fit diagnostics.

E5 must reduce triangle slack with nonuniform shape or permutation-invariant partition changes. An almost uniform scale/translation is not evidence of improved clustering.

E6 must confront a threatened direction: sufficient inactivity, actual LMI slack, PSD dual norm and the QSSC directional scale are reported. A singular-value floor is not a class-separation guarantee, and may preserve unhelpful directions.

Detailed per-point values and certificate-aware geometric diagnostics are in diagnostics.json; all failures and unmatched points are retained in coverage.csv.

## Computational cost

| Model | Main-path native CPU hours | Qualified/matched default outputs |
|---|---:|---:|
| QSSC | 0.149 | 29/32 |
| E1_v2 | 2.969 | 23/32 |
| E4 | 0.482 | 23/32 |
| E5 | 2.057 | 27/32 |
| E6 | 1.947 | 26/32 |

E4 additionally uses 0.152 CPU hours for the shared auxiliary bands and default graph QPs, plus 0.180 for control graph QPs. Main-path totals include failed attempts and all four declared movement targets; they exclude graph preparation, rounding and subsequent release verification. Full stage accounting is in resource_usage.csv. Unequal completion is explicit, so these costs are not a complete-capability ranking.

## Provenance and prior art

Seven Y0 raw bases were reused from verified historical objects; YaleB raw U0 was freshly replayed and Y3 applied explicitly. All eight final H object identities match their locked report counterparts. Historical scalar measurements are preserved as reference metadata, not silently reused as fresh baselines. Pre-evaluation storage-layout amendments preserve their original registrations.

[Quadratic convex clustering](https://www.ericchi.com/ec_papers/1304.0499v1.pdf), [TV-TV](https://jmota.eps.hw.ac.uk/documents/Vella21-RobustSingleImageSuperResolutionViaCNNsAndTVTVMinimization.pdf) / [PICCS](https://pmc.ncbi.nlm.nih.gov/articles/PMC3257752/) and [singular-value LMIs](https://shaharkov.github.io/ContSingVal.html) are established prior art. These are specific SSC extension candidates designed and tested in this project; E5 and E6 explicitly adapt tools from other fields. The scoped review cannot prove absolute novelty. No external image FFT or graphics optimizer was copied into these graph-vector solvers.
