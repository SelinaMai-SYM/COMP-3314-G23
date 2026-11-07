# Final recommendation

## Keep the reported control

Report reconstructed SSC E8, gamma=1, k=5, G0=F, random Lloyd, n_init=1, seeds 0..49. Do not switch the control to E13. Do not replace that row with k-means++, with E04-total, or with the gamma that maximizes ACC. The oracle envelope lives only in `results/extension_research/oracle_upper_bound.csv` under `ORACLE_UPPER_BOUND`.

`NO CONFIRMED IMPLEMENTATION BUG`. `SSC_method/` and `baselines/` stay as they were. The fresh control matches the strict-paper ORL, JAFFE, and USPS gamma=1 files. YaleB cropped differs in the fourth digit (0.1762551781 here, 0.1762220381 in the older metrics file). Both sit near 0.176 and both sit below the published 0.348 / 0.498 context.

## How to read the nine extensions

1. **SC-to-SSC gain.** The paired G−F interval is above 0 for the control only on ORL. The extension that repeats a positive G−F interval on more than one dataset is E05-fuse (ORL +0.017, USPS +0.022, BinAlpha +0.008). On YaleB the same fuse still leaves G at or below F. E05-bilateral increases fragmentation and does not add a positive G−F interval on the exact datasets. E01 preserves the ORL G−F interval and does not create one elsewhere.

2. **K-means only.** E07 k-means++ raises ORL from 0.573 to 0.784 and JAFFE from 0.684 to 0.951 on both F and G. The G−F gap under k-means++ is about zero on ORL and slightly negative on JAFFE. This is an initializer effect. It is large enough to dominate every graph extension in this round, and it is not the authors' stated initializer. JAFFE k-means++ on F already exceeds the published SSC figure of 81.2%, so this initializer does not identify the paper protocol. Inertia-best and consensus are single assignments. On UMIST those single assignments score higher on F than on G.

3. **A collapsed shrinkage.** E04-total is a global rescaling of gamma. At gamma=1 its relative move is about 1e-10 and G matches F, so ACC equals SC. Wherever E8 is below SC (YaleB, BinAlpha, UMIST), E04-total is above E8 by exactly that gap. The config name is `control_not_a_new_mechanism`. It is not a new clustering method.

4. **Embedding change.** E03-A replaces the feature graph with a local-scale graph, so F itself changes. Its SSC gains against E8 on ORL (+0.016), JAFFE (+0.032), and USPS (+0.036) come with a G−F interval that includes 0 or sits below 0. Report E03-A as a different spectral embedding, not as a stronger shrinkage step. E03-W, which keeps F and only changes W, lowers ACC on every dataset in the matrix, and those negative intervals exclude 0 on ORL, JAFFE, both YaleB matrices, BinAlpha, and UMIST.

5. **Optimizer.** E06 has no global-convergence claim. On ORL it matches the fuse-sized G−F gain and is not separated from E8 once K-means noise is included. On USPS it breaks the shrinkage graph into 4484 components and ACC falls. Three gamma=1e6 USPS cells (E06, E08, E09) are `FAILED` after 180s in the direct solver. They contribute no ACC.

6. **Combinations.** E08 does not improve on the better of E01 and E02. On ORL it is below E8. E09 follows E03-W downward. Combining the two factors that were specified in advance does not produce a method that should replace E8.

## YaleB

Do not describe any extension ACC on YaleB as progress toward the published table. D0–D6 and the gamma=1 extension matrix, on cropped2414 and on dengcai32, all stay below SC 34.8% and SSC 49.8%. The two matrices are not the same pixels (median matched L2 1.922 under the best orientation). The shrinkage step is already negative before any extension. The largest cropped movement that is still inside this protocol family is k-means++ at 0.2155, which remains a different initializer and remains below 0.348.

## What is blocked

MSRA50 is `BLOCKED_DATA` (no 1799×12 archive). AR is `BLOCKED`. The third-party archive did not pass the license, identity-count, official-image, and single-preprocessing checks, so it is not `AR100_ZENODO` and it was not run. BinAlpha `CANDIDATE_BIN_ALPHA` and UMIST `precropped575` ran, with eligibility `NON_EXACT_DATASET`.

## Practical next step

If a later report section is added, paste from `proposed_extension_draft.md` and keep the negative cells. Leave `report/main.tex` unchanged until that text is edited by hand. A further solver change is not justified by these ACC values: the control path still uses the original sparse direct solver, and the timeout exists so that a pathological factorization is stored as `FAILED` instead of a filled number.
