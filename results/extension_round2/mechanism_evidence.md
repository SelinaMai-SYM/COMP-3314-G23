# Mechanism evidence on the locked cohorts

Primary observations and the separately labelled fixed path are reported below. A certified embedding, changed partition or geometric guarantee is not by itself an ACC/NMI improvement. The cohorts were selected retrospectively; all means are conditional on that fixed selection.

## E1_v2: movement and relative stopping

Among positive-anchor edges, the observed fraction of edge weight at/below the stopping distance ranges from 1.405–63.23%. Coincident edges and uncertainty bands are retained separately in diagnostics.json; this observed fraction is not an exact active-set certificate. The primary movement ranges from 0.033–0.05138.
Only 0/8 original non-squared E1 reference attempts were certified. Their finite movements range from 0.01012–0.6856; these outputs cannot establish stationary or optimal behavior of that older objective. Quadratic movement alone therefore does not validate the proposed failure explanation.
At these locked operating points, the new finite output moves farther than the old E1 attempt on 1/8 cohorts (USPS). These references are not movement-matched; this comparison describes the operating points and does not isolate a fidelity effect.

## E4: graph intervention and correspondence control

The real-band graph passes the independent numerical eligibility checks on 6/8 cohorts. Applied positive exchange divided by original edge mass ranges from 1.063–8.091% among these graphs. Auxiliary cutoff ambiguity is flagged on 1/8 cohorts; a frozen finite band is not necessarily a uniquely identified spectral feature.
The real-band versus mean-of-three-permutations comparison has 2/8 qualified pairs, with available-case ΔACC/ΔNMI +0.152/+0.044 percentage points. All three individual contrasts and exchange magnitudes are retained; no permutation is selected by its score.
Real-band and permuted graphs exchange different amounts of mass. These comparisons therefore do not isolate correspondence from intervention magnitude. Limited qualified coverage and the default E4 regressions prevent a general correspondence-benefit claim.
Post-fit b-distance cross-class edge AUROC ranges from 0.4857–0.785; the added edge-mass fraction crossing labels ranges from 0.0002829–40.18%. These are descriptive label audits, not inputs to graph construction or parameter selection.

## E5: directional slack versus shape change

Among 7/8 qualified primary QSSC pairs, E5 lowers weighted triangle slack on 7/7. Residual from a global scale/translation of the same-target QSSC embedding ranges from 0.007972–0.01829 relative to S_H. At least one rounding partition changes on 7/7 cohorts. Slack reduction and these nonuniform changes still require joint ACC/NMI evidence; dataset regressions remain in the primary table.
In the post-fit label audit, E5 retains more within-label edge variation than QSSC on 6/7 comparable cohorts. The within/between-label TV ratios are recorded separately. This identifies reduced compression of same-label relations, but does not establish whether that compression was useful; joint ACC/NMI changes remain the performance criterion.

## E6: was a threatened direction protected?

The nominal movement-ball bound proves sufficient inactivity on 2/8 cohorts. The stronger post-fit QSSC gap bound establishes feasibility of its optimal retained projection for the guard on 8/8 cohorts. E6 PSD-dual norms range from 0–0 at the primary point.
When the same-lambda QSSC optimum already satisfies the guard, separately rounded score differences cannot be credited to protection of a violated direction. The recorded lambdas, movement differences and embedding residuals expose finite calibration/solver effects. Individual weakest-vector label associations are basis-dependent at repeated singular values and do not alone prove retention of noise.

| Fixed E6 target | Qualified/matched outputs | Whitened minimum minus guard | PSD-dual norm |
|---|---:|---:|---:|
| 0.02 | 8/8 | 0.4457–0.497 | 0–0 |
| 0.05 | 7/8 | 0.3519–0.4678 | 0–0 |
| 0.10 | 7/8 | 0.1369–0.4368 | 0–0 |
| 0.20 | 4/8 | 1e-10–0.2958 | 0–1.066 |

The following cases exhaust the qualified fixed-.20 pairs whose QSSC guard violation is supported by the gap-based upper bound. This mechanism subset uses geometry and certificates, rather than scores. It does not replace the .05 primary comparison.

| Cohort at .20 | QSSC optimum minimum, upper bound | E6 minimum | PSD-dual norm | ΔACC / ΔNMI (pp) |
|---|---:|---:|---:|---:|
| ORL | 0.2461 | 0.5000 | 1.0663 | -0.010 / +0.045 |
| UMIST | 0.4435 | 0.5000 | 0.1364 | +0.323 / +0.089 |
| BinAlpha | 0.4237 | 0.5000 | 0.2007 | -0.269 / -0.223 |

The guard protects a threatened direction in these secondary cases, while ACC/NMI effects remain mixed. Direction protection alone does not establish better class separation.

## Calibration correction

The archived USPS E1_v2 .02 point reused a certificate attached to a looser movement target. Its recorded movement-error bound is 0.0004271509577, above the required 0.0004. Independent saved-array qualification excludes this point. The original source and output are retained. [Amendment 003](../../configs/extension_round2/amendments/003_cached_precision.json) corrects target-specific cache qualification for future independent runs; no additional fit replaces the archived point. Exact calibration-only source compatibility is permitted for report derivation, while fitting and resume remain source-locked.

## Reachability and uncertainty

For a componentwise zero-penalty candidate, strong convexity bounds the exact optimizer movement by its distance to H. The requested lower tolerance exceeds this analytical bound at: none recorded. These post-fit bounds explain reachability without changing targets or adding fits; a finite SEARCH_LIMIT alone is not such a proof.
Only complete qualified paired coverage supports an eight-cohort macro. Rounding-seed intervals are conditional initialization variability, and not independent-data significance or generalization evidence.
