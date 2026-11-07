# E1 — K-means on one fixed F and one fixed G

Question: how much of the SSC gap is the final K-means stage?

Each dataset uses the saved strict_paper E8, γ = 1 embedding. F and G are not recomputed between arms.

| Dataset | Cache run |
| --- | --- |
| ORL att92 | `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41` |
| JAFFE zenodo | `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d` |
| YaleB cropped2414 | `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff` |
| USPS libsvm | `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b` |

Seeds are 0..49, the same list as those runs. Lloyd settings passed explicitly: `n_init=1`, `max_iter=300`, `tol=1e-4`, `algorithm=lloyd`, `copy_x=True`. scikit-learn 1.8.0 defaults `init` to `k-means++` and defaults `max_iter`/`tol` to 300 and 1e-4. The random arm sets `init="random"`. Recomputed random K-means on G matched the stored trial ACC on all 50 seeds of all four datasets (absolute gap < 1e-9).

`k-means++` is Level C. A higher score under `k-means++` is not evidence that Chang et al. used it.

Assignments: `runs/final_round/E1/{dataset}_labels.npz`, keyed from `results/final_round/E1_trials.csv`.

## Means (fraction, sample SD, ddof = 1)

Random init, K-means(F) / K-means(G):

| Dataset | ACC F | ACC G | NMI F | NMI G |
| --- | --- | --- | --- | --- |
| ORL | 0.5618 ± 0.0419 | 0.5726 ± 0.0380 | 0.8047 ± 0.0229 | 0.8113 ± 0.0216 |
| JAFFE | 0.6853 ± 0.1115 | 0.6843 ± 0.1108 | 0.8302 ± 0.0572 | 0.8305 ± 0.0572 |
| YaleB | 0.1834 ± 0.0128 | 0.1762 ± 0.0119 | 0.2690 ± 0.0067 | 0.2618 ± 0.0090 |
| USPS | 0.6174 ± 0.0809 | 0.6170 ± 0.0809 | 0.7494 ± 0.0449 | 0.7523 ± 0.0456 |

k-means++ (Level C), K-means(F) / K-means(G):

| Dataset | ACC F | ACC G |
| --- | --- | --- |
| ORL | 0.7833 ± 0.0131 | 0.7839 ± 0.0154 |
| JAFFE | 0.9531 ± 0.0000 | 0.9510 ± 0.0146 |
| YaleB | 0.2178 ± 0.0045 | 0.2155 ± 0.0047 |
| USPS | 0.6560 ± 0.0187 | 0.6579 ± 0.0190 |

JAFFE `k-means++` on F returned the same ACC on every seed. Every γ = 1 arm used all 40 / 10 / 38 / 10 cluster ids at least once (`n_unique_predicted` equals K). The best-inertia trial is recorded in `E1_summary.csv` and is not the reported mean.

## Paired differences

Δ = metric(G) − metric(F), same seed. 95% percentile bootstrap, 10,000 resamples, seed derived from dataset and init (`bootstrap_seed_*` in the CSV). The interval is only K-means noise on this fixed pair (F, G).

| Dataset | Init | ΔACC | 95% CI | CI excludes 0 | ΔNMI | mean ARI(F, G) | fraction of seeds with ACC(G) > ACC(F) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORL | random | +0.0109 | [+0.0030, +0.0187] | yes | +0.0066 | 0.846 | 0.72 |
| ORL | k-means++ | +0.0006 | [−0.0048, +0.0060] | no | −0.0013 | 0.840 | 0.42 |
| JAFFE | random | −0.0009 | [−0.0107, +0.0089] | no | +0.0003 | 0.964 | 0.24 |
| JAFFE | k-means++ | −0.0021 | [−0.0062, 0] | no | −0.0008 | 0.993 | 0.00 |
| YaleB | random | −0.0072 | [−0.0097, −0.0048] | yes, negative | −0.0072 | 0.685 | 0.14 |
| YaleB | k-means++ | −0.0023 | [−0.0040, −0.0005] | yes, negative | −0.0024 | 0.667 | 0.28 |
| USPS | random | −0.0004 | [−0.0068, +0.0058] | no | +0.0029 | 0.950 | 0.54 |
| USPS | k-means++ | +0.0020 | [−0.0034, +0.0072] | no | +0.0003 | 0.916 | 0.86 |

## Reading

SUPPORTED, and only for this fixed pair: under random init, ORL E8 γ = 1 raises mean ACC by about 1.1 percentage points. The same comparison under k-means++ does not.

SUPPORTED: YaleB E8 γ = 1 lowers mean ACC under both inits. The drop is smaller than the gap between our spectral clustering and the published YaleB SC number (34.8%).

SUPPORTED: JAFFE and USPS γ = 1 show no paired ACC gain. ARI between F labels and G labels is high on JAFFE and USPS (about 0.95–0.99 for the stronger init), so shrinkage barely changes the partition there.

SUGGESTIVE, Level C only: k-means++ lifts ORL K-means(F) from 0.562 to 0.783 and JAFFE from 0.685 to 0.953. Those levels are not equal to the published SC cells (ORL 72.7%, JAFFE 76.1%). On JAFFE, ++ overshoots the published SSC cell (81.2%). YaleB ++ reaches only 0.218, still far from 34.8%. Initialization can move ORL and JAFFE by more than shrinkage does. It is not identified as the authors' initializer, and it does not reproduce the YaleB table.

The published ORL SC–SSC gap is about 3 percentage points (72.7 to 76.0). Our random paired gap is about 1.1 points on a much lower base. Shrinkage at γ = 1 does not account for the distance to the published table.
