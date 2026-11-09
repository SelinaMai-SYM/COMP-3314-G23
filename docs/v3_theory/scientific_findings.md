# Scientific findings

The five contrasts were fixed before measurement. Dataset-level intervals use ORL, JAFFE, USPS, and one YaleB unit formed by averaging the two Y0 versions when both seed-paired rows exist. Y3 is excluded from that unit. Seed intervals are conditional on the fixed `F` and `G` of that job. None of the five Bonferroni 99% intervals excludes 0. An ACC increase on one dataset is not a significant result. The ideas reuse convex clustering, fixed-graph reweighting, local scaling, and multi-scale graphs. They are not claimed as new theorems.

Assembly recorded source commit `5355ee04d0b052d0a61ad5bbc7c50520b4058361`. Two later numerical facts belong to the working tree that produced the last jobs: USPS random-graph controls with n=9298 used Jacobi-preconditioned conjugate gradients on the same symmetrized IRLS system after SuperLU fill-in failed to finish, and the assembled UMIST jobs use the cached embedding with `gamma_0 = 0.1367313859608112`. An earlier unseeded ARPACK embedding (`gamma_0 = 0.1366970750844067`) is preserved under `results/v3_theory/superseded/umist_embedding_run1/` and is excluded from the tables.

Of 540 assembled jobs, 88 are `OPTIMALITY_VERIFIED` and 452 are `NUMERICALLY_UNCERTIFIED`. Verified jobs are the G=F certificate region. Real-data ADMM often returned a higher exact objective than IRLS, so those points stay uncertified.

## Primary contrasts

Greedy k-means++, seeds 0–49, mean ACC. The right-hand side is the matched SSC E8 control on the same `F`.

| Contrast | ORL | JAFFE | USPS | YaleB dengcai Y0 | YaleB cropped Y0 | Dataset-level mean ACC diff | Bonferroni 99% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X1 `gamma_0` versus gamma=1 | 0.7833 versus 0.7834 | 0.9531 versus 0.9510 | 0.6560 versus 0.6579 | 0.2536 versus 0.2543 | 0.2178 versus 0.2155 | +0.0002 | [−0.0015, +0.0018] |
| X2 beta=1 versus beta=0 | 0.7830 versus 0.7834 | 0.9531 versus 0.9510 | 0.6548 versus 0.6579 | 0.2542 versus 0.2543 | 0.2150 versus 0.2155 | −0.0004 | [−0.0024, +0.0015] |
| X3 mass tau=1 versus original gamma=1 | 0.7783 versus 0.7834 | 0.9531 versus 0.9510 | 0.6485 versus 0.6579 | mass solve did not converge | 0.2177 versus 0.2155 | −0.0026 | [−0.0084, +0.0022] |
| X4 multi versus k=5 | 0.7753 versus 0.7834 | multi solve did not converge | 0.6618 versus 0.6579 | 0.2545 versus 0.2543 | 0.2122 versus 0.2155 | −0.0019 on 3 datasets | [−0.0080, +0.0038] |
| X5 alpha=1 versus alpha=0 | 0.7821 versus 0.7834 | alpha=1 did not converge | 0.6579 versus 0.6579 | 0.2524 versus 0.2543 | 0.2149 versus 0.2155 | −0.0008 on 3 datasets | [−0.0013, 0] |

X1 at `gamma_0` has `‖G−F‖/‖F‖` at or below 0.0014 and status `OPTIMALITY_VERIFIED`. The gamma=1 controls move (`‖G−F‖/‖F‖` 0.023 on USPS, 0.091 on dengcai Y0, 0.115 on ORL) and stay `NUMERICALLY_UNCERTIFIED`. The certified point does not raise dataset-level ACC.

X3 mass normalization reproduces the equivalent-gamma control. On ORL the objectives are 10.832864247918119 and 10.83286424791811, with the same greedy ACC 0.7783. That match is a rescaling, so it is not an algorithmic improvement. On dengcai Y0 the mass-tau objective is 25.445329 and the equivalent-gamma objective is 25.445359; the mass solve missed the iteration tolerance and was left unclustered.

X4 on JAFFE ran 1000 iterations without convergence (`‖G−F‖/‖F‖` 0.066). X5 alpha=1 on JAFFE likewise stopped at 1000 iterations. Both are exploratory. ORL multi-scale ACC is lower than k=5 by 0.0080 on the paired seeds; the seed interval excludes 0 and the dataset-level interval includes 0. The prespecified failure hypothesis, that larger neighborhoods add harmful edges, is consistent with the ORL decrease and is not established as a general effect. USPS multi-scale ACC is 0.6618 against 0.6579 at k=5, and that seed interval includes 0.

X5 alpha=0 matches the frozen unit fidelity. On USPS, alpha=1 returns the same greedy ACC and NMI as alpha=0, seed by seed. YaleB Y3 alpha=1 on both versions did not converge and was not clustered.

## Held-out perturbations

**2026-11-09 audit correction:** This historical table is not valid evidence of full SSC robustness: the script compared stored SSC labels to K-means on a perturbed F without rerunning shrinkage, and USPS was clipped to [0,1] despite its [-1,1] domain. Values are retained as historical measurements only. See docs/next_round/robustness_audit.md and the new full-pipeline evaluator.

ARI compares the unperturbed seed-0 partition with k-means on a held-out perturbed embedding. It is not class correctness and was not used to choose beta.

| Dataset | beta=0 ARI | beta=1 ARI | Edge Jaccard |
| --- | --- | --- | --- |
| ORL | 0.863 | 0.863 | 0.964 |
| JAFFE | 1.000 | 1.000 | 0.949 |
| USPS | 0.331 | 0.353 | 0.048 |
| YaleB dengcai Y0 | 0.742 | 0.717 | 0.835 |
| YaleB cropped Y0 | 0.738 | 0.697 | 0.860 |
| BinAlpha candidate | 0.519 | 0.514 | 0.779 |
| UMIST 575 | 0.783 | 0.844 | 0.988 |

On both YaleB Y0 versions the beta=1 partition is less stable under the held-out perturbations than beta=0.

## YaleB Y3 track

Y3 is reported beside Y0 and is not compared with Y0 as if the whole gap were an extension. Dengcai Y3 SSC E8 gamma=1 greedy ACC is 0.4338. Cropped Y3 is 0.3441. The extension contrasts on Y3 stay within a few thousandths of those controls where the solve converged. Details are in `results/v3_final/yaleb_questions.md`.

## Frozen reproduction, kept separate

The 72-cell table is `results/v3_final/reproduction_gap_matrix.md`. Primary cells use Y0, the reference role, and random initialization. LDA-SC stays blocked. AR 840, UMIST 564, and MSRA50 stay blocked. UMIST 575 and the BinAlpha candidate are supplemental.

USPS SSC E8 gamma=1000, seeds 0–49, from the frozen trial file: random ACC 0.7387 ± 0.0753, greedy ACC 0.7992 ± 0.0015. The primary cell remains gamma=1, E8 random ACC 61.70 ± 8.09. Gamma=1000 is sensitivity only.
