# Scientific conclusion

The question is whether a previously unstated K-means initialization and selection rule can explain the gap between this E8 reconstruction and Chang et al. (2015). The decisive comparison is SC versus SSC under the same rule, across datasets, including the published SC-to-SSC gain. A high SSC accuracy on one dataset is not that explanation.

## H1: uniform random Lloyd, then the minimum-inertia run

Evidence that fits H1 is narrow. On JAFFE, P2 lifts SSC from 68.43 to 95.31, and on ORL from 57.27 to 62.25. The lift appears on F as well.

Evidence against H1 is broader. ORL P2 SSC is 62.25 against a published 76.0. JAFFE P2 is 95.31 against a published 81.2, and SC is 95.31 as well, so the published +5.1 shrinkage gain is not there. YaleB P2 stays near 20 on both matrices, against 49.8. USPS P2 is 65.63 against 75.5, and the shrinkage gain is +0.13 against +11.2. Across ten batches, ORL SSC random-best averages 65.70 ± 2.46, still far from 76. H1 is not a sufficient historical account.

## H2: k-means++ described as random initialization

Greedy k-means++ (`SKLEARN_GREEDY_KMEANSPP`) does move ORL and JAFFE SSC accuracy onto or above the published SSC numbers (ORL P3 78.39, JAFFE P3 95.10). That is the observation that motivated this study.

It does not survive the controlled comparison. ORL SC P3 is 78.33, so the shrinkage gain is +0.07 rather than +3.3. JAFFE SC P3 is 95.31. YaleB greedy cells remain 21–26 against a paper SC of 34.8 and SSC of 49.8. USPS greedy SSC at gamma 1 is about 65.8 against 75.5, with a shrinkage gain of about +0.2. Ten greedy best-of-50 batches keep those conclusions: ORL SSC greedy-best averages 79.50 ± 0.84, still matched by SC at 79.05 ± 0.26.

Vanilla k-means++ (`n_local_trials=1`) is a separate control, not P3. On ORL its means are SC 72.73 and SSC 74.38. The SC mean sits on the published 72.7, and the SSC mean is 1.6 below 76.0, so the gap is +1.66 rather than +3.3. That single-dataset coincidence does not extend. JAFFE vanilla means are about 89 and 90, well above the paper. YaleB vanilla means stay near 21 and 24. USPS vanilla means stay near 62.5 and 62.8. Vanilla seeding is not an identified author setting.

## H3: the embedding and other upstream choices still matter

At gamma 1, after every protocol tested here, shrinkage adds essentially no accuracy. The large ORL and JAFFE deficits of random Lloyd are mostly an initialization effect, and they appear in F before shrinkage. YaleB is already far below the published SC accuracy on both matrices, under random means, minimum inertia, greedy k-means++, and vanilla k-means++. Initialization does not explain YaleB.

The gamma grid, which was fixed in advance, shows where shrinkage can still move the result. At `1e-6` and `1e-3`, SSC P1 accuracy equals SC P1 on these versions: G has not changed the clustering mean. At gamma `1e3` on USPS, SSC P1 rises to 73.86 (NMI 82.83) while SC stays at 61.74 (NMI 74.94). The paper values are SSC 75.5 / 79.8 and SC 64.3 / 69.5. That cell is closer to the published SSC number and does show an SSC-over-SC gap of about 12 points. It is one prespecified grid point, not a gamma chosen by accuracy. The solver did not converge. Greedy k-means++ on that same unconverged G reaches 79.91, which overshoots the paper. Calling gamma `1e3` the operating point would be `ORACLE_BEST_TEST_ACC` for the USPS P1 column. It is reported as a grid measurement and is not a fair unsupervised claim.

## What would count as a historical-protocol explanation

It would need, on more than one benchmark, both the published SC level and the published SSC level, hence the published gap, under one prespecified rule. None of P1, P2, P3, P4, or vanilla k-means++ does that at gamma 1. The USPS gamma `1e3` cell is a lead for a later upstream study. It is not, by itself, evidence that the authors used a particular K-means initializer.

Unresolved assumptions that this experiment does not close: the authors' K-means code, whether they reported a mean or a selected run, the gamma used on each dataset, graph symmetrization and bandwidth, the exact face-image files, and the fact that several gamma = 1 solves returned an unconverged iterate.
