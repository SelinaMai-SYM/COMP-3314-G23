# Round-three results

This is conditional development evidence on eight retrospectively selected report cohorts, not an unseen test. Full eight-cohort means are NA whenever an exact contrast lacks any qualified pair. Available-case comparisons with different masks must not be ranked.

There are 352/378 finite declared profiles and 153/168 qualified primary/control profiles, including exact aliases. Charged CPU at this export: 18.333 core-hours. Missing, failed, timed-out and unmatched outputs remain in [coverage.csv](coverage.csv).

A pre-scoring resource audit identified native path-cap overruns on 2 paths (MSRA50 / R3_E1_V3_SHUFFLE401; YaleB / R3_E1_V3_PILOT). All 4 declared profiles on those paths are conservatively descriptive only, even when their numerical certificate passes. Failed work and overruns remain charged globally. [Native path totals](native_path_costs.csv) · [Recorded deviations and repair](../../docs/extension_round3/experiment_protocol.md#resource-accounting-amendment-005-and-deviations).

## Primary comparisons

Changes are percentage points. Both metrics use one paired cohort mask. Original SSC and movement-matched QSSC answer different questions.

| panel | candidate | control | paired_n | cohort_mask | acc_eight_cohort_delta | nmi_eight_cohort_delta | acc_available_case_delta | nmi_available_case_delta | joint_wins | joint_losses |
|---|---|---|---|---|---|---|---|---|---|---|
| anchor_generated | R3_E1_V3_CAVITY | QSSC | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | NA | NA | 0.117 | 0.336 | 4 | 2 |
| native | R3_E1_V3_CAVITY | QSSC | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | NA | NA | 0.157 | 0.358 | 3 | 3 |
| anchor_generated | R3_E1_V3_CAVITY | SC | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | NA | NA | 0.456 | 0.642 | 4 | 2 |
| native | R3_E1_V3_CAVITY | SC | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | NA | NA | 0.450 | 0.618 | 4 | 2 |
| anchor_generated | R3_E1_V3_CAVITY | SSC_REFERENCE | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | NA | NA | 1.461 | 0.738 | 5 | 1 |
| native | R3_E1_V3_CAVITY | SSC_REFERENCE | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | NA | NA | 4.876 | 2.287 | 3 | 3 |
| anchor_generated | R3_E5_V2_CAVITY | QSSC | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 0.069 | 0.206 | 4 | 2 |
| native | R3_E5_V2_CAVITY | QSSC | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 0.235 | 0.204 | 3 | 4 |
| anchor_generated | R3_E5_V2_CAVITY | SC | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 0.308 | 0.417 | 5 | 1 |
| native | R3_E5_V2_CAVITY | SC | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 0.422 | 0.373 | 4 | 3 |
| anchor_generated | R3_E5_V2_CAVITY | SSC_REFERENCE | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 1.448 | 0.802 | 6 | 1 |
| native | R3_E5_V2_CAVITY | SSC_REFERENCE | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 4.344 | 2.050 | 5 | 2 |
| anchor_generated | R3_E7_CAVITY | QSSC | 8 | AR;BinAlpha;JAFFE;MSRA50;ORL;UMIST;USPS;YaleB | 0.002 | 0.005 | 0.002 | 0.005 | 4 | 2 |
| native | R3_E7_CAVITY | QSSC | 8 | AR;BinAlpha;JAFFE;MSRA50;ORL;UMIST;USPS;YaleB | -0.022 | 0.013 | -0.022 | 0.013 | 2 | 5 |
| anchor_generated | R3_E7_CAVITY | SC | 8 | AR;BinAlpha;JAFFE;MSRA50;ORL;UMIST;USPS;YaleB | 0.220 | 0.229 | 0.220 | 0.229 | 5 | 2 |
| native | R3_E7_CAVITY | SC | 8 | AR;BinAlpha;JAFFE;MSRA50;ORL;UMIST;USPS;YaleB | 0.170 | 0.259 | 0.170 | 0.259 | 6 | 2 |
| anchor_generated | R3_E7_CAVITY | SSC_REFERENCE | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 1.382 | 0.602 | 6 | 1 |
| native | R3_E7_CAVITY | SSC_REFERENCE | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | NA | NA | 4.089 | 1.864 | 5 | 2 |

## Self-influence falsification

The decisive control is the same intervention using uncorrected pilot scores. A candidate that does not improve over that control has no demonstrated self-influence benefit.

| panel | candidate | control | paired_n | cohort_mask | acc_available_case_delta | nmi_available_case_delta | joint_wins | joint_losses |
|---|---|---|---|---|---|---|---|---|
| anchor_generated | R3_E1_V3_CAVITY | R3_E1_V3_PILOT | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | 0.014 | 0.009 | 4 | 1 |
| native | R3_E1_V3_CAVITY | R3_E1_V3_PILOT | 6 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS | -0.123 | -0.068 | 0 | 6 |
| anchor_generated | R3_E5_V2_CAVITY | R3_E5_V2_PILOT | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | 0.004 | 0.003 | 3 | 1 |
| native | R3_E5_V2_CAVITY | R3_E5_V2_PILOT | 7 | AR;BinAlpha;JAFFE;ORL;UMIST;USPS;YaleB | 0.061 | 0.045 | 4 | 2 |
| anchor_generated | R3_E7_CAVITY | R3_E7_PILOT | 8 | AR;BinAlpha;JAFFE;MSRA50;ORL;UMIST;USPS;YaleB | -0.001 | -0.001 | 1 | 2 |
| native | R3_E7_CAVITY | R3_E7_PILOT | 8 | AR;BinAlpha;JAFFE;MSRA50;ORL;UMIST;USPS;YaleB | 0.004 | -0.001 | 1 | 4 |

[Contribution verdict](contribution_verdict.md) · [All paired contrasts](paired_differences.csv) · [Mechanisms](mechanism_diagnostics.csv) · [Protocol](../../docs/extension_round3/experiment_protocol.md). Bootstrap intervals are conditional on rounding starts, use 10,000 draws with seed 424242, are pointwise and unadjusted across contrasts, and are not a generalization guarantee. All planned controls and secondary rows are listed, including failures.
