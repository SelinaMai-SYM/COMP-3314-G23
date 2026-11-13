# Interpretation of the frozen study

The experiment does not establish a reliable, complete two-panel clustering benefit from removing pilot-edge self-influence. The identity and convex implementations are supported; a useful class discriminator and a broadly better SSC refinement are separate, unsupported conclusions. These are conditional results on eight retrospectively selected report cohorts, including the adapted native-16 MSRA proxy.

## Performance and the decisive controls

E7 has eight qualified primary outputs. Against movement-matched QSSC, its equal-cohort ACC/NMI changes are +0.002/+0.005 percentage points with anchor-generated starts and −0.022/+0.013 with native starts. Against its plain-pilot counterpart they are −0.001/−0.001 and +0.004/−0.001. Thus the complete comparison does not support the self-influence hypothesis. In the native panel, E7 also loses mean ACC to all three shuffled-score controls; it loses both mean metrics to the anchor-score control. Leverage-only weighting gives a tradeoff rather than a unique cavity advantage.

E1_v3 has six qualified primary pairs, excluding MSRA and YaleB. Its native changes against QSSC are +0.157/+0.358 pp, and against uniform tubes +0.114/+0.086. However, against plain-pilot tubes they are −0.123/−0.068; every one of these six cohorts loses at least one metric. The small positive anchor-generated pilot contrast (+0.014/+0.009) does not survive native rounding. Selective allocation can be useful without supporting the particular self-influence correction.

E5_v2 has seven qualified primary pairs, excluding MSRA. Native changes are +0.235/+0.204 pp against QSSC, +0.210/+0.049 against uniform guards, and +0.061/+0.045 against plain-pilot guards. The anchor-generated pilot contrast is only +0.004/+0.003. This is a small conditional positive signal, not a complete eight-cohort result: native QSSC comparisons contain three joint wins and four joint losses, and shuffled-402 guards have slightly higher mean ACC. Neither partial macro may be ranked against an eight-cohort or differently masked macro.

Comparisons with original SSC use its locked historical gamma and a separately checked unsquared-fidelity solution. They are not comparisons against a new fair gamma search. Large gains on AR and BinAlpha coexist with losses on UMIST; most of those gains are shared by QSSC and simple controls. They cannot be credited to cavity correction. Full eight-cohort original-SSC macros remain NA because its MSRA reference is uncertified.

## What the mechanism evidence supports

The exact evidence computation passes its numerical checks: the largest recorded linear-system residual is below 1.6×10⁻¹⁵, and retained inverse-entry asymmetry is below 1.7×10⁻¹⁶. Cavity and pilot weighted ranks differ on every cohort, by approximately 0.011–0.025 under graph/guard masses and 0.016–0.033 under tube masses. This is coefficient activity, not demonstrated class relevance.

Post-freeze cross-class-edge AUROC improves over plain pilot on only ORL and USPS, by approximately 0.00061 and 0.00009. It decreases on the other six cohorts. On UMIST and MSRA both pilot and cavity AUROC are below 0.5. The correction therefore does not provide a consistently better wrong-edge discriminator on these frozen inputs. These audits are label-dependent explanations, not training signals or probabilities of edge error.

The returned refinements are non-affine, but cavity–pilot differences are often small relative to certificate uncertainty. A positive lower bound on their normalized embedding difference is obtained for only 2/8 graph profiles and 1/7 qualified guard profiles; five of six qualified tube pairs have such a bound. These bounds concern the retained, approximately movement-matched lambda points, not an isolated causal effect of the score. Some native partitions change despite small embedding differences.

Unlike the preceding round at its different operating point, the new guard reduces within-label variation relative to QSSC on all seven qualified cohorts. Its weighted triangle slack is approximately 20–41% of QSSC's. The guard is doing something measurable, yet that does not establish the benefit of cavity over pilot allocation. The stronger native gains are concentrated in UMIST, BinAlpha and USPS, while AR, JAFFE, ORL and YaleB each regress on at least one metric.

## Coverage, interpretation and scope

All eight inputs and their exact graph evidence were available. There are 352 finite declared profiles, each with both complete 50-seed panels (35,200 trials), out of 378 planned profiles. Of 168 primary/control profiles, 153 qualify, including eight exact graph-rescaling aliases. Sensitivity coverage is 101/160 qualified profiles. The 26 optional development sensitivities were not run because the primary-qualification gate failed; unused budget does not override that gate.

Finite endpoints from CPU limits, finite search limits, repeated bracket proposals and unresolved certificates remain descriptive. Search failure is not proof that a movement target is unattainable. Two native path-cap deviations are separately recorded and all four affected profiles are excluded from qualified comparisons. Numerical certification and protocol eligibility remain distinct. The original clock, all failed work and both overruns remain in resource accounting.

The 0.05/0.20 movement paths and anchor-score diagnostics are separate fixed sensitivities; no favorable secondary row replaces the primary 0.10 target. Bootstrap intervals describe variation over paired rounding starts, conditional on fixed embeddings. They are pointwise, unadjusted for multiple comparisons, and do not integrate dataset selection, solver uncertainty or unseen-data generalization.

The contribution is a reproducible controlled study of one frozen edge-deletion signal at three alternative SSC insertion points, including its limitations and negative outcomes. Rank-one inversion and leverage correction are inherited. This study supplies no new class-recovery theorem, no proof of absolute novelty, and no general-purpose clustering improvement claim. Genuine sparse bridges and mutually supporting wrong neighborhoods remain explicit failure cases.

The tables below are generated from the authoritative paired records. Full means, sample SDs, intervals, both panels and control rows are retained in the [result tables](../../results/extension_round3/summary.md) and [per-cohort pages](../../results/extension_round3/benchmarks/). This interpretation was written after terminal scoring; no fitting, parameters, eligibility decisions or seed selection changed.

## Native primary effects by cohort

Each cell is ΔACC / ΔNMI in percentage points. Q denotes QSSC; S denotes the locked original SSC reference. † denotes a descriptive comparison excluded from qualified aggregation.

| Cohort | E7 vs Q | E7 vs S | E1_v3 vs Q | E1_v3 vs S | E5_v2 vs Q | E5_v2 vs S |
|---|---:|---:|---:|---:|---:|---:|
| AR | +0.024 / -0.075 | +12.007 / +3.491 | +0.019 / +0.004 | +12.002 / +3.570 | +0.071 / -0.146 | +12.055 / +3.420 |
| JAFFE | +0.000 / +0.000 | +0.000 / +0.045 | -0.216 / -0.081 | -0.216 / -0.036 | -0.216 / -0.084 | -0.216 / -0.039 |
| ORL | +0.025 / +0.029 | +4.280 / +0.372 | -0.110 / +0.372 | +4.145 / +0.715 | -0.330 / +0.075 | +3.925 / +0.418 |
| UMIST | -0.057 / +0.057 | -5.819 / -4.103 | +1.174 / +1.529 | -4.589 / -2.632 | +1.287 / +1.432 | -4.475 / -2.729 |
| BinAlpha | -0.238 / +0.039 | +18.244 / +11.320 | -0.205 / +0.065 | +18.277 / +11.347 | +0.228 / +0.284 | +18.710 / +11.566 |
| MSRA50 | -0.034 / -0.025 | -0.449 / -0.382 † | +0.270 / -1.011 † | -0.145 / -1.368 † | -0.180 / -0.619 † | -0.595 / -0.976 † |
| YaleB | -0.030 / +0.022 | +0.416 / +1.364 | +0.317 / -0.002 † | +0.763 / +1.340 † | -0.075 / -0.297 | +0.371 / +1.045 |
| USPS | +0.137 / +0.056 | -0.505 / +0.559 | +0.279 / +0.258 | -0.362 / +0.760 | +0.680 / +0.163 | +0.038 / +0.665 |
