# Scientific findings after E1–E6

Evidence labels: CONFIRMED, SUPPORTED, SUGGESTIVE, UNRESOLVED.
Numbers are from `runs/strict_paper/` and `results/final_round/`. Published table entries are historical comparisons, not our measurements. Primary SSC protocol: E8, γ = 1, random Lloyd, n_init = 1, seeds 0..49, one F and one G.

Convexity: Equation (8) is convex in G when F and W are fixed and W is nonnegative. That does not make spectral clustering or K-means convex, and it does not make a clustering metric unique.

## Q1. Which parts of SSC are mathematically validated?

CONFIRMED, on the n = 6 chain already in `tests/test_ssc.py` (re-run, pytest 0; CLARABEL status optimal): E13 matches Equation (8) with graph coefficient γ/2 (max |G| gap 2.3e-5). E8 matches Equation (8) at the printed γ (max |G| gap 1.2e-5). The ordered-pair sum counts both stored triangles once and does not apply another factor of two.

CONFIRMED as a code fact, not as the authors’ binary: Algorithm 1 line 10 (`(S + γ W̃)^{-1} S X`) is not the solver. E8 is the stationary system we use for the primary cells. E13 is the printed linear update.

UNRESOLVED on the real datasets: after the relative-step rule fires, the E8 fixed-point residual is still 0.002 (ORL γ = 1), 0.171 (YaleB γ = 1), and 0.058 (USPS γ = 1000). A small step is not a global-optimality certificate. The objective itself changes by at most 2.5e-5 when those runs are continued from 300 steps to the step rule (E3).

## Q2. Which published results were reproduced?

Datasets with a completed n = 50 protocol: ORL att92, JAFFE zenodo, YaleB cropped2414, USPS libsvm. Counts match the paper for JAFFE (213), YaleB (2414 / 38), and USPS (9298). ORL is the AT&T 92×112 release resized to 32×32, not an unidentified third crop.

Not reproduced, and not imputed: AR, UMIST, BinAlpha as a paper identity, MSRA50, SPLS.

Primary E8 γ = 1 mean ACC (fraction) against Table 1 (percent, historical):

| Dataset | Our SC | Our SSC γ = 1 | Table SC | Table SSC |
| --- | --- | --- | --- | --- |
| ORL | 0.5618 | 0.5726 | 72.7% | 76.0% |
| JAFFE | 0.6853 | 0.6843 | 76.1% | 81.2% |
| YaleB | 0.1834 | 0.1762 | 34.8% | 49.8% |
| USPS | 0.6174 | 0.6170 | 64.3% | 75.5% |

SUPPORTED: the γ = 1 table is not reproduced. The ordering SSC ≫ SC on YaleB is not reproduced. USPS at the non-primary grid point γ = 1e3 has mean ACC 0.7369, nearer the table’s 75.5%, and the paper’s text already singles out USPS as a case where γ = 1 is not the preferred setting. That cell was not selected by maximizing ACC. It is not reported as “the” reproduced USPS number.

Figure 1 and Figure 2 were not curve-matched. Our plots are labeled as reproductions from saved runs (`docs/final_round/E5_figure_audit.md`).

## Q3. Does SSC shrinkage improve clustering beyond SC on our reconstructions?

SUPPORTED: not as a general fact at E8 γ = 1.

Paired ΔACC = ACC(G) − ACC(F), random init, 95% bootstrap CI conditional on the fixed embedding: ORL +0.0109 [+0.0030, +0.0187]; JAFFE −0.0009 [−0.0107, +0.0089]; YaleB −0.0072 [−0.0097, −0.0048]; USPS −0.0004 [−0.0068, +0.0058]. Only ORL’s interval lies above zero, by about one percentage point. YaleB’s interval lies below zero.

SUPPORTED, separate from γ = 1: on the saved grid, USPS E8 at γ = 1e3 has ACC 0.7369 against SC 0.6174, and at γ = 1e6 the same dataset falls to 0.3881. One grid point can be higher without a monotone rule (E2).

## Q4. Does shrinkage effectiveness depend on K-means initialization?

SUPPORTED for ORL: the γ = 1 paired gain is present for random init and absent for k-means++ (ΔACC +0.0006, CI [−0.0048, +0.0060]). YaleB’s negative paired gap remains negative under both inits.

SUGGESTIVE and Level C: k-means++ changes the level of ACC by much more than shrinkage does on ORL (F: 0.562 → 0.783) and JAFFE (F: 0.685 → 0.953). YaleB only moves from 0.183 to 0.218. USPS moves from 0.617 to 0.656. These are not the authors’ initializer. JAFFE ++ exceeds the published SSC number, so “they must have used ++” does not fit every dataset. The ± in our SSC cells is K-means noise on one G (E6), not 50 independent shrinkages.

## Q5. Does improved optimization accuracy lead to improved clustering accuracy?

SUPPORTED: not on the three E3 cases. Continuing until the step rule fires changes Equation (8) by 2.5e-5, 1.3e-5, and 6e-6. ACC goes 0.57265 → 0.57135 (ORL), 0.17622 → 0.17614 (YaleB), and 0.73687 → 0.73861 (USPS γ = 1000). The USPS jump relative to γ = 1 is already in the 300-step G.

UNRESOLVED: a certificate that the real-data G is the global minimizer. The small-graph check does not extend to n = 2414 or n = 9298.

## Q6. Which gaps already exist before SSC?

SUPPORTED: the large YaleB gap is already in K-means on F. Cropped SC is 0.183; Deng Cai under the same graph rule is 0.202; published SC is 34.8%. SSC γ = 1 makes cropped YaleB slightly worse (E1).

SUPPORTED: ORL and JAFFE random-init SC (0.562, 0.685) sit below the published SC cells before any shrinkage. USPS random-init SC (0.617) is closer to published SC (64.3%). The γ = 1 shrink does not create the USPS table gap; γ = 1 leaves USPS at the SC value (E2, label-change fraction 0.035).

## Q7. Why do ORL, JAFFE, and YaleB differ from USPS?

SUPPORTED description, not a single cause:

- At γ = 1, USPS barely moves (`||G−F||_F/||F||_F` = 0.023) and ACC is unchanged. The same γ moves ORL by 0.115 and YaleB by 0.105. YaleB’s paired ACC goes down; ORL’s goes up by ~1 point under random init only.
- USPS is the dataset where a larger grid value (γ = 1e3) raises ACC (0.737) and a still larger value (γ = 1e6) destroys it (0.388). That non-monotone shape is why a USPS table cell can look successful at one γ and absent at γ = 1. JAFFE has a smaller version of the same bump (0.684 at γ = 1, 0.722 at γ = 1e3). YaleB’s ACC declines across the whole grid.
- The shrinkage graph on F has 16, 9, and 13 components on ORL, JAFFE, and YaleB, and 1 component on USPS. The YaleB pixel graph used for F is connected (E4). Those are different graphs.
- k-means++ (Level C) rewrites ORL and JAFFE and does little for YaleB. USPS ++ stays near the published SC number; the SSC table gap on USPS is a γ effect, not an init effect of this size.

## Q8. Which conclusions do the controlled experiments support?

SUPPORTED:

1. At E8 γ = 1, shrinkage is not a reliable ACC improvement over SC on these four reconstructions. ORL random init is a small positive exception; YaleB is negative.
2. On the preset γ grid, larger γ lowers TV(G) under the ordered-pair sum, and larger movement is not monotone in ACC.
3. Finishing the IRLS step rule after iteration 300 does not account for the table gaps.
4. Deng Cai versus cropped2414, same graph rule and same seeds, moves YaleB K-means(F) by about 1.8 points (0.183 → 0.202), not from 18% to 35%.
5. Reported ± values are sample SDs over 50 distinct K-means seeds on one embedding.

SUGGESTIVE: initialization and, on USPS, the choice of γ are large enough to matter. They are not identified with the unpublished protocol.

## Q9. Which implementation details remain historically ambiguous?

UNRESOLVED:

- Whether the authors minimized Equation (8), solved printed Equation (13), or ran Algorithm 1 line 10 as written.
- δ, union versus mutual kNN, and the 32×32 interpolation kernel.
- Whether “50 random initializations” plus “best objective” means the mean ± SD printed in the tables, one best trial, or 50 full SSC solves. Our logs are 50 K-means runs on one G.
- The exact γ behind each Table 1 SSC entry. The text says γ = 1 is usual except for MSRA50 and USPS, without listing the value used in the table.
- Which YaleB pixels and which ORL files were resized. att92 and cropped2414 are documented stand-ins, not pixel-matched to a missing author matrix. Deng Cai is a different matrix (E4).
- Eigenvector sign convention and row normalization. Row normalization is Level C and was not selected.

## Q10. What would the authors need to provide?

The original code or a parameter dump would have to include, for each table cell: the image files and resize operator; k and δ; union or mutual; the linear system actually solved (line 10, Equation 13, or the factor-2 system); the γ used in the table as distinct from the Figure 1 sweep; K-means `init`, `n_init`, and whether the printed ± is the mean of 50 trials or a best-objective trial; and the objective that Figure 2 plots (Equation 8, the surrogate, or another formula). Without those, the remaining YaleB gap and the USPS dependence on γ stay UNRESOLVED as historical facts, even though the controlled contrasts above are measured.
