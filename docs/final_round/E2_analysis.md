# E2 — Does shrinkage change the embedding, and does that raise ACC?

E8 only. G, F, the objective history, and the 50-trial ACC/NMI are the saved strict_paper files listed in `results/final_round/E2_shrinkage.csv` (`run_id` column). W was not stored. It was rebuilt from that run's F with the recorded `k`, `delta2`, `knn_method`, and symmetrization. The rebuild was kept only when undirected edge count, stored nnz, connected-component count, and mean degree matched `shrinkage_graph_stats`.

ORL and JAFFE F files are byte-identical across the five γ values. YaleB and USPS F hashes differ, but the max absolute entrywise gap between γ = 1e-6 and γ = 1e6 is below 5e-14. That is solver noise, not a second embedding. TV(F) is therefore the same number on each dataset for every γ.

## Summation convention

Equation (8) sums `W_ij ||g_i − g_j||_2` over pairs `(i, j)`. The stored affinity is symmetric and keeps both triangles (`symmetric_stored` true, `n_stored_nnz = 2 * n_undirected_edges`). `TV` is the sum over those stored entries, the same sum as `graph_l2_term` / `equation8_objective`. It is not multiplied by an extra 2. The column `tv_undirected_half_G` is 0.5 × TV and is not the objective. Rebuilt Eq. (8) matched the last history row within the script's relative tolerance on every cell.

`||G−F||_{2,1}` is the sum of row Euclidean norms. Near-coincident rows of G use absolute tolerances 1e-8 (exact-fusion screen), 1e-3, and 1e-2, plus `1e-3 * median ||g_i||`. A row of G is near the matching row of F when `||g−f|| ≤ 1e-8 + 1e-4 ||f||`. These tolerances are ours. They are not in the paper.

## What the grid does

Relative movement `||G−F||_F / ||F||_F` and `TV(G)/TV(F)`:

| Dataset | γ = 1e-6 | 1e-3 | 1 | 1e3 | 1e6 |
| --- | --- | --- | --- | --- | --- |
| ORL rel-F | ~0 | ~0 | 0.115 | 0.390 | 0.680 |
| ORL TV ratio | 1 | 1 | 0.118 | 2.2e-4 | ~0 |
| JAFFE rel-F | ~0 | ~0 | 0.029 | 0.153 | 0.192 |
| JAFFE TV ratio | 1 | 1 | 0.713 | 7.1e-5 | ~0 |
| YaleB rel-F | ~0 | ~0 | 0.105 | 0.710 | 0.837 |
| YaleB TV ratio | 1 | 1 | 0.323 | 6.7e-5 | ~0 |
| USPS rel-F | ~0 | ~0 | 0.023 | 0.571 | 0.847 |
| USPS TV ratio | 1 | 1 | 0.430 | 2.1e-3 | ~0 |

SUPPORTED on this five-point grid: once γ reaches 1, TV(G) is lower than TV(F), and further increases of γ keep lowering TV(G). Between 1e-6 and 1e-3 the TV change is ~1e-8 or smaller and the label-change fraction is 0. Higher γ is associated with lower TV here. Five preset points are not a proof that every intermediate γ behaves the same way.

Stored mean fraction of points whose K-means labels differ between F and G (random, 50 seeds; recomputed explicit Lloyd matched this fraction with gap 0 at γ ≤ 1):

| Dataset | γ = 1 | 1e3 | 1e6 |
| --- | --- | --- | --- |
| ORL | 0.094 | 0.305 | 0.560 |
| JAFFE | 0.029 | 0.124 | 0.175 |
| YaleB | 0.215 | 0.444 | 0.855 |
| USPS | 0.035 | 0.273 | 0.636 |

At YaleB γ = 1e3 the recomputed fraction is 0.006 higher than the stored fraction. At USPS and YaleB γ = 1e6 the gap is below 1e-4. The stored trial log is the one cited above. Duplicate rows at large γ make Lloyd emit fewer than K centers (sklearn `ConvergenceWarning` during the recompute). That is a consequence of collapsed rows, not a second algorithm.

Pairs of distinct G rows with distance ≤ 1e-8: zero at γ ≤ 1e-3 on all four datasets; positive at γ ≥ 1 (ORL 747, JAFFE 300, YaleB 3520, USPS 10405 at γ = 1). At γ = 1e6 the counts are 18448 (ORL), 1851 (JAFFE), 2.42e6 (YaleB), and 2.62e7 (USPS). Exact numerical coincidence appears as γ grows. It is not claimed to be a correct clustering merge. At γ = 1e6, ACC falls on ORL (0.511), YaleB (0.129), and USPS (0.388).

Connected components of this W (the kNN graph on F, not the pixel graph): ORL 16, JAFFE 9, YaleB 13, USPS 1. The count does not depend on γ.

## ACC is not monotone in shrinkage

Stored mean ACC on G:

| Dataset | γ ≤ 1e-3 | γ = 1 | γ = 1e3 | γ = 1e6 |
| --- | --- | --- | --- | --- |
| ORL | 0.5618 | 0.5726 | 0.5582 | 0.5109 |
| JAFFE | 0.6853 | 0.6843 | 0.7222 | 0.7189 |
| YaleB | 0.1834 | 0.1762 | 0.1705 | 0.1289 |
| USPS | 0.6174 | 0.6170 | 0.7369 | 0.3881 |

SUPPORTED: greater shrinkage is not necessarily higher ACC. YaleB ACC falls as γ and the movement grow. ORL peaks slightly at γ = 1 and is worse at 1e6 than at 1e-6. USPS is flat through γ = 1, higher at 1e3, and much worse at 1e6. JAFFE is flat through γ = 1 and higher at 1e3 than at 1e6. The USPS γ = 1e3 cell is one grid point. It was not chosen because it has the highest ACC, and it is not the primary protocol.

SUPPORTED: the objective can move while ACC does not. USPS γ = 1 cuts TV by about 57% (`relative_tv_reduction` 0.570) and changes only 3.5% of labels; ACC stays at the SC value. YaleB γ = 1 cuts TV by about 68% and ACC goes down.

No causal claim is made from the five-point correlation. The figure `results/final_round/E2_figure.pdf` plots movement, TV ratio, and stored ACC on the same γ axis so the non-monotone ACC curve is visible next to the monotone TV curve.
