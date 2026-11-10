> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Reproduction deviations

The method notes identify assumptions and corrections relative to Chang et al., AAAI 2015. Experimental numbers came only from actual `runs/`, labelled Our Reproduction, rather than copies of the paper tables.

| Item | Paper | Implementation at this stage | Status |
| --- | --- | --- | --- |
| Solve | Algorithm 1 line 10: \((S_t+\gamma\widetilde W)^{-1}S_tX\) | Equation (13): \((S+\gamma\widetilde L)^{-1}SF\), sparse solve without explicit inverse | Locked correction |
| Reweighted W/L | Algorithm line 4, outside loop | Rebuilt from current G each iteration using Equation (11) | Locked correction; Equation (11) depends on G |
| S | Equation (10), embedding-dimensional diagonal \(1/(2\lVert h_j\rVert_2)\) | n by n row diagonal \(S_{ii}=1/(2\max(\lVert h_i\rVert_2,\varepsilon))\) | Correction of incompatible Equation (9) dimensions and row L21 norm |
| Equation (13) coefficient | Printed gamma L; Equation (8) stationarity has 2 gamma L | Printed Equation (13), equivalent to Equation (8) with half the graph coefficient | Locked distinct target; see independent CVXPY check |
| Initial point | Unspecified | G0=F | Assumption |
| Equation (10) at initialization | Undefined at H=0 | Median pairwise row distance only for the first all-zero residual; epsilon=1e-8 afterward | Using epsilon throughout can leave G near F; repeatedly resetting the larger scale can cycle |
| Objective monitoring | Proof discusses Equation (8); figure does not identify its plotted formula | Original Equation (8) and square-root smoothed objective | Original norm, smoothing, and floored denominator are distinct |
| Stopping | Unspecified | Relative Frobenius step; tol=1e-6, max_iter=100 | Assumption |
| Bandwidth | Unspecified | Each graph uses its median positive directed k-neighbor squared distance as delta squared | Assumption |
| Symmetrization | Unspecified | Union support, Gaussian weights, zero diagonal, k=5 | Union is assumed; k=5 is explicit in the paper |
| Spectral representation | Minimize trace(F.T Ln F), Equation (4) | Smallest c eigenvectors; largest-magnitude sign positive; isolated inverse degree zero | Sign/isolate conventions; not PCA |
| Data shape | Algorithm 1 writes d by n X | Samples are rows, shape (n,d) | Convention; Equation (13) does not use X |
| K-means | Cluster G; experiment text mentions both 50 trials and best objective | Output labels only; one external random seed, init=random, n_init=1 | Repetitions belong to experiment protocol; actual completed n retained |
| Default gamma | Search {1e-6,1e-3,1,1e3,1e6}; gamma=1 often good except MSRA50/USPS | API gamma=1 | API default, not a universal optimum |

## Experimental differences from actual runs

- JAFFE and USPS were verified; ORL used Olivetti 64x64 resized to 32x32; YaleB used Deng Cai's 32x32 MAT. AR, UMIST, BinAlpha, and MSRA50 were unavailable at this stage.
- SPLS was NOT_IMPLEMENTED (six SKIPPED directories); approximate LDA-SC was excluded from the main fair table.
- K-means, SC, SSC, and LLC used 50 trials on ORL/JAFFE, 10 on YaleB. USPS SSC used one trial and USPS K-means ten. These were not 50-trial USPS/YaleB reproductions.
- ORL SSC Track A: 53.9±3.0 (n=50, gamma=1e-6), versus paper 76.0±1.6; comparable to SC 54.2±3.1. The paper's large ORL improvement was not reproduced.
- JAFFE SSC Track A: 74.8±8.4 (n=50, selected gamma=1e6), versus paper 81.2±1.6; gamma=1 gave 68.6±11.3.
- YaleB SSC: 19.7±1.1 (n=10), versus paper 49.8±1.6.
- USPS SSC: 62.1 (n=1), versus paper 75.5±1.9.
- Mutual-kNN extension: ORL 53.7±2.8 versus 54.0±2.8 (n=50), JAFFE 68.6 versus 68.7 (n=50), YaleB 19.7 versus 19.9 (n=10). Effects were mixed or negligible, not a performance win.
- The failed NameError run `20261020_015425__TRACKA__LDAKM__ORL__fb14ac44` was rerun as `20261020_020157__TRACKA__LDAKM__ORL__fb14ac44`; its FAILED directory was retained.
- At gamma=1, ORL and YaleB IRLS did not meet tol=1e-6 within max_iter=300.

Full historical tables: `results/tables/` and `docs/critical_analysis.md`.