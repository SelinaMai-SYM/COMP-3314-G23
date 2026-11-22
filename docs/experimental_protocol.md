# Experimental protocol

## Inputs and reconstruction factors

The eight benchmark families are AR, JAFFE, ORL, UMIST, BinAlpha, MSRA50, YaleB
and USPS. Source identity, sample membership, resolution and preprocessing are
separate fields in the [data inventory](../results/submission_refresh/dataset_inventory.csv).
[Data setup](data.md) describes access and preparation. Y0 normalizes neither X
nor F by rows; Y1 normalizes X, Y2 normalizes F and Y3 normalizes both.

The reconstruction examines six interpretation groups: membership; source and
pixels; graphs and normalization; numerical convention; rounding and reporting;
and tuning/baselines. A changed subset rebuilds A, F, W and G. Reusing a parent
embedding's rows is not a subset reconstruction. Completed comparisons and
source filters are mapped in [report evidence](report_evidence.md).

## Distinct statistical endpoints

| Endpoint | Rule | Variability |
|---|---|---|
| Fixed best-SSE | E8 gamma 1, Y0, RANDOM; choose minimum inertia among seeds 0–49 in batch 0 | One partition; no across-start SD |
| Fixed mean | Same configuration and all 50 partitions | Mean and sample SD (ddof=1) |
| Historical closest display | ACC-only discrepancy using the frozen historical selection file | Its own configuration and seeds |
| Joint source/configuration match | Complete 50-start groups, joint ACC/NMI discrepancy within declared pools | Same configuration for both means/SD |
| Locked confirmation | First unused 50-seed block at or above 1,000,000 after selection | Conditional new rounding starts; no reselection |
| Extension native | Greedy++ centers generated on each fitted G | 50 paired seeds |
| Extension common indices | Centers use anchor-generated row indices on each G | 50 paired seeds |

The historical [report selection](../configs/final/report_selection.yaml) remains
unchanged. Joint matching uses [selection.yaml](../configs/submission_refresh/selection.yaml):
first $D_{max}=\max(|A-A_p|,|N-N_p|)$, then
$D_{mean}=(|A-A_p|+|N-N_p|)/2$, with a 1e-12 pp tie tolerance. Ties favor fewer
explicit paper deviations, fewer preparation assumptions, declared E8 target
preference and stable ID. A published-grid gamma is not penalized solely for
being different from one. Both metrics and SD stay attached to the same fit.
Source-native LDA objectives in different learned subspaces are not a common
selection objective.

The subset grid uses E8/E13 × gamma {1e-6,1e-3,1,1e3,1e6} × RANDOM/vanilla++/
greedy++. Common historical finite-IRLS settings are held fixed. An improved
certified solve does not replace one of these outputs. Eligibility pools separate
specification-compatible, adapted and diagnostic-only sources. Label/target-informed
matching is retrospective and does not estimate generalization or label-free tuning.

## Selected-extension protocol

[cohort_lock.json](../configs/extension_round3/cohort_lock.json) freezes the eight
selected inputs and source identities. The [full protocol](extension_round3/experiment_protocol.md)
and [configuration](../configs/extension_round3/protocol.yaml) define shared F/W,
rho=0.10 and tau_multiplier=1. Calibration uses geometry without labels. Labels
enter evaluation and post-fit semantic diagnostics after numerical outputs and
eligibility are frozen. The cohorts themselves were chosen retrospectively.

All finite outputs use seeds 0–49, greedy++ and one Lloyd start, max_iter=300,
tol=1e-4. Both native and anchor_generated panels are retained. ACC/NMI are
percentages, SD is sample SD, and differences are percentage points. Paired
bootstrap uses 10,000 draws and seed 424242, conditional on the fixed cohort and
representations. A native minimum-objective assignment is a separate endpoint.

Qualified movement comparisons require relative primal–dual gap ≤1e-6,
capacity residual ≤1e-8, movement uncertainty e_rho≤0.005rho and
|rho_hat−rho|+e_rho≤0.01rho. Both controls and metrics use the same paired cohort
mask. Partial masks have explicit denominators; their eight-cohort macros are
unavailable. Finite but movement-unmatched, finite but uncertified, failed and
unrun outputs remain distinct.

The ordinary SSC reference uses unsquared fidelity and its separately declared
fit, without the quadratic movement constraint. QSSC and plain-pilot controls
separate the intervention from the effect of the deletion correction. Uniform,
anchor and shuffled controls remain in the released records.
