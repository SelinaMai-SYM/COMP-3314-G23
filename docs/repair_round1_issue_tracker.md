> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Repair round 1 issue tracker

Date: 2026-10-20. Mathematical variants, ORL diagnostics, data recovery, transfer experiments, and a four-page report were completed. Measurements came from `runs/repair_round1/` and `results/repair_round1/`. ORL 76% was not labelled reproduced.

## Git checkpoints

The starting worktree was clean; no empty checkpoint commit was made. Its HEAD was:

`d73a6d1fe5cd514d1448e7c4e01d322e42bf1f9f`

Mathematical checkpoint: `a29efda` (Add E13 and E8 shrinkage variants as a math checkpoint). Report/data-recovery completion commits were recorded separately.

Earlier commits:

- `d73a6d1` Keep validation_report.json in sync with the markdown report.
- `6bd1373` Record post-commit validation and the origin/v1 403 push denial.
- `5d2d467` COMP3314 GP v1: faithful SSC reproduction, benchmark evaluation, method extension and report

## Fields

Each entry records Issue ID, Severity, Affected component, Original paper reference, Current implementation, Confirmed discrepancy, Suspected cause, Proposed repair, Experiments required, Verification criteria, and Final status.

A successful small convex check was not described as resolving the ORL clustering gap.

## Status overview

| Issue ID | Severity | Final historical status |
| --- | --- | --- |
| P0-EQ8-EQ13 | P0 | Small convex check verified; E8 did not close ORL/YaleB ACC gaps: ORL 53.3±3.2 n=50; YaleB 19.5±1.5 n=10 |
| P0-EQ10-DIM | P0 | Confirmed; retained row-wise n by n S rather than incompatible printed diagonal |
| P0-ALG1-L10 | P0 | Confirmed; line 10 not executed literally |
| P0-ORL-ACC | P0 | Unresolved: E8 53.3±3.2 n=50 versus 76.0±1.6; best att92 n=5 about 58.8; no reproduction claim |
| P0-YALEB-ACC | P0 | Unresolved: E8 19.5±1.5 n=10 versus 49.8±1.6; cropped2414 E13 18.0±0.7 |
| P0-DATA-MISSING | P0 | Partial recovery: att92/cropped2414 obtained; defaults unchanged; no AR/BinAlpha/MSRA50; UMIST 1012/575, not 564 |
| P0-SPLS | P0 | Unresolved; NOT_IMPLEMENTED |
| P0-REPORT-PAGES | P0 | Main text compressed: 13 total pages; conclusion/acknowledgments end page 4; references start page 4; appendix starts page 5; no Overfull |
| P1-STEP-VS-FP | P1 | Observed on block example; stopping unchanged; ORL/YaleB gamma 1 often missed tol 1e-6 |
| P1-E8-EPS-FLOOR | P1 | Observed; default initialization floor unchanged |

## P0-EQ8-EQ13

- Severity: P0
- Affected component: `SSC_method/optimizer.py` linear system and `SSC_method/objective.py` Equation (8).
- Original paper reference: Equations (8), (12), (13), and proof Equation (15), using ordered pairs.
- Current implementation: default E13 is \(A=S+\gamma\widetilde L\). Explicit `variant="E8"` uses \(A=S+2\gamma\widetilde L\). Omitting variant preserves E13.
- Confirmed discrepancy: ordered pairs, Equation (11)'s one-half, and the combinatorial Laplacian give coefficient 2 for Equation (8), whereas Equation (13) has1 because its Equation (12) trace omitted a factor2. Independent n=6 chain/block CVXPY 1.9.3/CLARABEL 0.11.1 references, tol_gap_abs=tol_gap_rel=tol_feas=1e-10, returned optimal. E8 objective differences were about 1e-10 and matrix differences about 1e-6. E13 matched the half-gamma problem similarly, while printed Equation (8) values were larger: chain 4.537 versus 4.021; block 3.656 versus 3.652.
- Suspected cause: \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert^2=2\operatorname{Tr}(G^\top\widetilde LG)\), but Equation (12) used only gamma times the trace.
- Proposed repair: preserve both named variants, and report their distinct targets without relabelling one as the other.
- Experiments required: small convex checks and ORL/YaleB/JAFFE shortlist completed; E8 did not outperform E13 or K-means(F) materially.
- Verification criteria: `tests/test_repair_round1_math.py` finite-difference gradients, dimensions, cross-residuals, CLARABEL objective/matrices, and L-BFGS-B surrogate checks. Original objective, smoothing, surrogate, and rebuilt residual remain distinct.
- Final status: convex implementation verified; not a repair of ORL76% or the clustering gap.

## P0-EQ10-DIM

- Severity: P0
- Affected component: `row_l21_diagonal` in `SSC_method/objective.py`.
- Original paper reference: Equation (9) trace \(\operatorname{Tr}((G-F)^\top S(G-F))\); Equation (10) embedding-length diagonal \(1/(2\lVert h_j\rVert)\).
- Current implementation: n by n S, with \(S_{ii}=1/(2\max(\lVert h_i\rVert,\varepsilon))\), hi a residual row.
- Confirmed discrepancy: Equation (13)'s n by n Laplacian requires n by n S. A c-length diagonal cannot be added or used in Equation (9), while Equation (8) sums sample-row norms.
- Suspected cause: Equation (10) mixes row residuals and embedding coordinates.
- Proposed repair: retain the row-wise definition; do not add an unexecutable printed-diagonal branch.
- Experiments required: dimension checks in existing `test_row_wise_s_shape_and_hand_value` and variant tests; no clustering run needed.
- Verification criteria: S diagonal length equals n, distinct from c when c!=n.
- Final status: confirmed; row weighting retained. Literal printed Equation (10) was not implemented and is not claimed repaired verbatim.

## P0-ALG1-L10

- Severity: P0
- Affected component: `SSC_method/optimizer.py`.
- Original paper reference: Algorithm 1 line10 \((S_t+\gamma\widetilde W)^{-1}S_tX\), and line4 placing G-dependent W outside the loop; compare Equation(13)'s L and F.
- Current implementation: solve \((S+c\gamma\widetilde L)G=SF\), c=1 for E13 or2 for E8. Rebuild W from current G; do not multiply X or substitute W for L.
- Confirmed discrepancy: line10 differs in both matrix and right-hand side. Paper X is d by n, unlike F.
- Suspected cause: inconsistent typesetting between Algorithm 1 and Equation(13).
- Proposed repair: do not execute line10 literally; retain named E13/E8 systems.
- Experiments required: none; line10 is not an experimental factor.
- Verification criteria: use sparse solves and L with SF right-hand side, without explicit inverses.
- Final status: confirmed; follows Equation(13)/E8 rather than claiming literal repair of line10.

## P0-ORL-ACC

- Severity: P0
- Affected component: ORL SSC and TrackA cited by `report/main.tex`.
- Original paper reference: ORL SSC 76.0±1.6, Tables 1-2.
- Current implementation: report used53.9±3.0, n=50, gamma=1e-6 selected with labels; Olivetti64x64 bilinearly resized32x32 differed from native92x112 source.
- Confirmed discrepancy: faithful E8 gave53.3±3.2 (n=50, `20261020_032508__REPAIR1__ORL__D12_KMEANS_G_E8__d484f3c9`) versus 76.0±1.6. E13 gave53.7±2.8, K-means(F)53.9±3.0. k-means++ B62.1±1.6 remained about 14 pp below; row normalization C60.2±2.9 was not the paper method. att92 E13 bilinear gave53.9±3.8 and nearest58.8±5.3 (n=5 each).
- Suspected cause: no A/B one-factor setting approached76%; unresolved candidates included unreleased2015 preparation, K-means details, and image identity.
- Proposed repair: do not label C results reproduced; questions recorded in `docs/repair_round1_author_questions.md`.
- Experiments required: ORL one-factor matrix and n=50 shortlist completed; invalid variants were not expanded.
- Verification criteria: actual run IDs/n and gap to76.0±1.6; never rewrite53.9/53.3 as76.
- Final status: unresolved; ORL76% was not reproduced.

## P0-YALEB-ACC

- Severity: P0
- Affected component: YaleB SSC.
- Original paper reference: SSC 49.8±1.6.
- Current implementation: Deng Cai E8 gave19.5±1.5, E13 19.7±1.1, n=10 rather than50.
- Confirmed discrepancy: roughly30 pp gap. Bilinear cropped2414 E13 gave18.0±0.7 (n=10), without improvement. k-means++ B gave25.2±0.6; row normalization C26.7±1.8.
- Suspected cause: not isolated; trial counts and image provenance differed. No historical sample-identity claim.
- Proposed repair: report actual n and keep C separate from faithful results.
- Experiments required: E8/E13/F/++/row-normalization/cropped2414 transfer block executed at n=10.
- Verification criteria: actual n/source and gap to49.8±1.6.
- Final status: unresolved.

## P0-DATA-MISSING

- Severity: P0
- Affected component: benchmarks/ar, umist, binalpha, msra50.
- Original paper reference: experimental sample counts and image sizes.
- Current implementation: strict AR/UMIST/BinAlpha/MSRA50 defaults raised DatasetUnavailable. Explicit additional versions included att92 (400 images92x112), cropped2414, and UMIST1012/575; ORL/YaleB defaults were unchanged.
- Confirmed discrepancy: no AR/BinAlpha/MSRA50 files; UMIST did not have564 rows. Binary Alphadigits and other MSRA corpora were not relabelled.
- Suspected cause: broken links, WAF, access terms, or unrecoverable historical membership.
- Proposed repair: use verifiable files and record URL/date/HTTP for failures; see `docs/repair_round1_dataset_recovery.md`.
- Experiments required: recovery completed; att92/cropped2414 did not close the ACC gaps.
- Verification criteria: counts, resolutions, checksums; missing564/26x30/1799x12 cells remained unreproduced.
- Final status: partial recovery; four historical dataset names unresolved.

## P0-SPLS

- Severity: P0
- Affected component: `baselines/spls/spls.py`.
- Original paper reference: Hou, Nie, Jiao, Zhang, Wu, IPM2013; Chang wrote SPLS, original acronym SLPS.
- Current implementation: fit_predict raised NotImplementedError rather than substituting K-means or SC.
- Confirmed discrepancy: paper comparison included SPLS; repository had no SPLS measurements.
- Suspected cause: abstract lacked Section 3 updates; no official code.
- Proposed repair: implement only once objective and algorithm were available; otherwise NOT_IMPLEMENTED.
- Experiments required: 2026-10-20 full-text search in `docs/repair_round1_baseline_audit.md`; Unpaywall/OpenAlex closed, arXiv0, author PDF linked Elsevier DOI.
- Verification criteria: small checks against actual updates before reportable cells.
- Final status: unresolved, NOT_IMPLEMENTED at this stage.

## P0-REPORT-PAGES

- Severity: P0
- Affected component: main text of `report/main.tex`, title through conclusion including abstract.
- Original paper reference: course maximum4 main pages, references/appendix excluded; preserve template typography.
- Current implementation: `\usepackage[preprint]{neurips_2026}`, unchanged style; latexmk succeeded. pdfinfo reported13 Letter pages. Page4 contained Conclusion, Acknowledgments, References; page 5 continued references and appendixA; page 6 appendixB; page 7 checklist. No Overfull matches. Group_23.pdf and main.pdf were byte-identical.
- Confirmed discrepancy: old22-page narrative replaced; main text ended on page 4.
- Suspected cause: excessive length had been compressed.
- Proposed repair: completed.
- Experiments required: none; commands in `docs/repair_round1_validation.md`.
- Verification criteria: readable, compilable main text ends by page 4.
- Final status: historical four-page check passed at 2026-10-20 03:49 CST.

## P1-STEP-VS-FP

- Severity: P1
- Affected component: shrink_embedding convergence flag versus rebuilt fixed-point residual.
- Original paper reference: no stopping rule; implementation used relative Frobenius steps.
- Current implementation: converged=True when \(\lVert G_{t+1}-G_t\rVert_F\le\mathrm{tol}(1+\lVert G_t\rVert_F)\); rebuilt residual separate.
- Confirmed discrepancy: block E13 gamma 0.8, tol 1e-8 stopped at 57; step 2.18e-8, frozen residual 1.06e-6, rebuilt residual 0.361. With rebuilt residual 1.41e-6 later, steps still jittered around1e-7 and converged=False despite agreement with CLARABEL.
- Suspected cause: reweighted W sensitivity at tiny distances; small steps do not establish stationarity at current G.
- Proposed repair: retain both diagnostics; do not call unconverged runs successful. Stopping unchanged in this stage.
- Experiments required: existing block example; no dataset required.
- Verification criteria: `test_block_e13_small_step_is_not_a_small_fixed_point_residual` requires simultaneous step convergence and rebuilt residual>0.1.
- Final status: phenomenon verified; stopping rule not repaired.

## P1-E8-EPS-FLOOR

- Severity: P1
- Affected component: E8 with `zero_residual_floor="eps"`.
- Original paper reference: Equation 10 divides by zero at G0=F; no epsilon specified.
- Current implementation: median_pairwise default applies only to the first all-zero residual; eps remains optional. E13 stayed within 1.41e-8 of F in the linearly spaced chain example.
- Confirmed discrepancy: E8 first step 2.83e-8; at 30 steps movement 0.390, Equation 8 value2.277, rebuilt residual 0.987, not converged.
- Suspected cause: E8's doubled coefficient moved some residual rows past epsilon, reducing S and allowing further movement; E13 remained within the floor.
- Proposed repair: retain eps and default median_pairwise. Record E8/eps separately rather than describing it as always stuck at F.
- Experiments required: future initialization diagnostics; this stage retained the counterexample only.
- Verification criteria: E13/eps movement<1e-5; E8/eps executable with first step<1e-6.
- Final status: phenomenon verified; default floor unchanged.