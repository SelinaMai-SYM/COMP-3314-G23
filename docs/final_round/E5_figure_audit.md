# E5 — Published Figure 1 and Figure 2

PDF: `SSC_method/resources/Chang_et_al_2015_SSC_AAAI.pdf` (7 pages, AAAI 2015). Captions were read with `pdftotext`. Tick labels were not digitized. A page render shows small multiples; the axis numbers are too small to transcribe reliably, so no published point was copied into our plots.

## What the paper actually shows

Figure 1 caption: clustering performance (ACC) against parameter settings, eight panels (a) AR, (b) JAFFE, (c) ORL, (d) UMIST, (e) binalpha, (f) MSRA50, (g) YaleB, (h) USPS. The body text (Parameter Sensitivity) says the parameter is γ and the vertical axis is accuracy. It also says that, except on MSRA50 and USPS, γ = 1 gives the best or a respectable result. The prose cites “Eq. (3)” for γ. The displayed objective in the paper is Equation (8), and the convergence proof refers to Equation (8). We do not resolve that numbering slip by relabeling our objective.

Figure 2 caption: convergence curves on the same eight datasets. The body text says γ is fixed at 1, the median of the tuned range, and that the objective decreases quickly. The same “Eq. (3)” wording appears there. Our plot uses the recorded nonsmooth Equation (8) value, column `equation8_objective`, not `irls_quadratic_surrogate` and not the square-root smoothing.

The experimental section also says each clustering is repeated 50 times with random initialization and the reported result is the one with the best objective. Tables 1–2 still print mean ± standard deviation. Those two sentences are not the same protocol. Our curves use the mean ACC over all 50 seeds. They are not best-of-50 objective selections.

## Our Figure 1

`results/final_round/E5_parameter_sensitivity.pdf`, points in `E5_parameter_points.csv`.

Labeled as our reproduction, not the published figure. Panels: ORL att92, JAFFE zenodo, YaleB cropped2414, USPS libsvm. AR, UMIST, binalpha, and MSRA50 are omitted because there is no completed paper-identity run (see `docs/final_round_preflight.md`). Open circles mark E8 solves that had not met the relative-step tolerance at iteration 300. A dashed line is our SC mean from the strict_paper SC run, not the paper’s SC number.

γ grid is the saved grid {1e-6, 1e-3, 1, 1e3, 1e6}. It is a reconstruction of a log sweep. It is not a claim that the published ticks are exactly these five numbers.

Qualitative comparison that does not use digitized points:

- Our ACC is not flat in γ. USPS rises at 1e3 and falls at 1e6. The paper’s text already treats USPS as an exception to “γ = 1 is enough.”
- Our YaleB curve does not rise with γ. Published Table 1 has SSC well above SC on YaleB. Our E8 means do not.
- We do not claim the shape matches Figure 1.

## Our Figure 2

`results/final_round/E5_convergence.pdf`, rows in `E5_convergence_curves.csv`. Histories were already on disk. No solve was repeated for this figure.

| Dataset | Run | Iterations stored | Step rule at the saved cap |
| --- | --- | --- | --- |
| ORL γ = 1 | `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41` | 300 | not met |
| JAFFE γ = 1 | `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d` | 300 | not met |
| YaleB γ = 1 | `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff` | 300 | not met |
| USPS γ = 1 | `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b` | 298 | met |

E3 later ran ORL and YaleB past 300. Those longer traces are in `E3_convergence_figure.pdf`, not spliced into this figure. This figure is the saved γ = 1 history only.

The published caption says the objective converges quickly. Our saved traces still contain hundreds of iterations, and three of the four γ = 1 runs have not met `tol = 1e-6` at step 300. That is a statement about our logs. It is not a numeric overlay on Figure 2, because the published iteration counts were not read off the image.

Optimizer: IRLS, variant E8, `A = S + 2γ L̃`, `G_0 = F`, median pairwise floor on the first zero residual. The plotted number is the nonsmooth Equation (8) evaluation after each accepted step. The surrogate can move differently and is stored in the CSV but not drawn.
