# Results

ACC and geometric NMI are reported in percent. Differences are percentage
points. Each mean and sample SD uses one complete configuration and its 50
rounding seeds. A native-objective-selected assignment is a separate endpoint
with no across-start SD.

## Reconstruction and critical findings

The [generated reconstruction tables](reconstruction_tables.md) contain the
fixed best-SSE SC/SSC diagnostic, eight joint mean matches and initialization
contrasts. The [evidence map](report_evidence.md) specifies their exact filters.
The original paper's reported SSC−SC macro difference is +9.99/+3.61 pp;
against SPLS it is +2.09/+2.14 pp. YaleB has +15.0 ACC but −8.8 NMI pp.

The search completed 74,436 configuration pairs on 2,482 inputs: 2,480 complete
30-setting grids and two partial grids. AR, ORL, UMIST and BinAlpha match both
published means within 1.37 pp. Matching is retrospective, based on labels and
paper targets within declared eligibility pools. It does not resolve historical
membership. Five selected historical IRLS fits reached the cap; none has a gap
certificate. The [matched-SC contrasts](../results/subset_search/matched_sc_contrasts.csv)
show positive changes in both means on six selected reconstructions, with
regressions on AR and YaleB.

Fixed-setting discrepancies also occur in the eight baselines before SSC
refinement. The [historical records](../results/v3_reproduction/all_configurations.csv)
and [baseline tables](../results/submission_refresh/per_benchmark/) preserve
PCA/SPLS configurations, LDA failures and the separately named ridge LDA→SC
adaptation. The presentation uses native best-of-50 for comparable fixed
objectives and mean/sample-SD for the stated LDA endpoints.

On the original ORL records, RANDOM→greedy++ changes mean SSC ACC from
57.135 to 78.335; SC changes from 56.180 to 78.325. This is distinct from later
subset-search outputs. Refinement W has cross-class weight fractions 4.6% on
ORL and 70.2% on YaleB, according to the original Y0 W diagnostics. These are
post-fit label associations, separate from upstream graph A.

## Selected extensions

The [complete selected comparison](../results/extension_round3/summary.md)
retains both panels, controls, measured exclusions and sample SD. The README
primary table is generated from `macro_differences.csv` at rho=0.10 and
`tau_multiplier=1`, native panel. Both controls use identical paired masks.

| Method | Qualified mask | Native vs QSSC (ACC/NMI pp) | Native vs plain pilot | Common indices vs plain pilot |
|---|---|---:|---:|---:|
| E7 | All eight | −0.022/+0.013 | +0.004/−0.001 | −0.001/−0.001 |
| E1_v3 | Excludes MSRA50, YaleB | +0.157/+0.358 | −0.123/−0.068 | +0.014/+0.009 |
| E5_v2 | Excludes MSRA50 | +0.235/+0.204 | +0.061/+0.045 | +0.004/+0.003 |

E1_v3 MSRA50/YaleB and E5_v2 MSRA50 are finite and certified, but their
movements are 0.027871/0.070613 and 0.075561, outside the primary match.
Their evaluations remain in the eight-cohort table. The MSRA50 unsquared SSC
reference is finite but uncertified. Full eight-cohort matched macros for E1_v3
and E5_v2 remain unavailable.

The correction improves cross-class-edge AUROC only on ORL
(0.838901→0.839508) and USPS (0.752293→0.752378). E5_v2 lowers weighted triangle
slack to 20.4–40.9% of QSSC on its seven qualified cohorts, while shrinking
both within-class and between-class variation. UMIST improves +1.287/+1.432 pp
over QSSC, but is −4.475/−2.729 pp below the independently fitted SSC reference.
The controlled results support limited local gains rather than a reliable
general improvement attributable to edge-deletion correction.

The [development summary](development_summary.md) retains the earlier E1–E7
values displayed in slide 6.1, including the E2/E3 failed gates. It is distinct
from the selected extension comparison.

## Source availability

Committed scalar records, complete seed measurements and sample manifests
support no-data table rebuilding. Historical selected arrays were not retained;
a newly generated representation cannot certify one of those historical fits.
Current provider-derived numerical stores have integrity inventories but no
public download endpoint. Their availability is separate from scalar
reconstruction. See [data](data.md) and [reproducibility](reproducibility.md).
