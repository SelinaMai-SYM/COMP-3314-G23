# E6 — ACC, NMI, and the n = 50 audit

## Definitions that the tests lock

ACC is the fraction of points matched after a one-to-one Hungarian assignment (`benchmarks.metrics.clustering_accuracy`, Kuhn–Munkres on the contingency table). NMI uses the geometric mean of the entropies (`normalized_mutual_information`), the Strehl–Ghosh form written as Equation (21) in the AAAI paper, and the same normalization as `sklearn.metrics.normalized_mutual_info_score(..., average_method="geometric")`.

`tests/test_metrics.py` and `tests/test_final_round_e6.py` were run with the existing E8/E13 CVXPY test. Pytest return code 0 (`results/final_round/E6_pytest.txt`). Covered cases include a perfect partition, a pure label permutation, string labels, a 3/4 contingency, unequal sizes, a constant prediction, both-constant partitions, a single sample, more predicted labels than true labels, non-contiguous ids, label ids at 1e15, and rejected shapes. Empty clusters are not inserted: a label that never occurs is absent from the partition, so a prediction with fewer than K occupied clusters is scored as that coarser partition.

The Equation (8) graph term is tested to count each stored ordered pair once (`test_graph_term_counts_each_stored_ordered_pair_once`). Both triangles of a symmetric edge contribute. An extra factor of two is not applied.

## n = 50

`results/final_round/E6_validation.json` audits 52 completed strict_paper cells on ORL, JAFFE, YaleB, and USPS: SSC E8, SSC E13, SC, K1, and K3. Problems list is empty.

For every such cell:

- `status` is COMPLETED.
- Trial seeds are exactly `[0, 1, …, 49]`, 50 distinct integers.
- `acc_mean` / `acc_std` in `metrics.json` match the trial list. The standard deviation is the sample SD, `ddof = 1`, the same convention as `scripts/run_experiment.py`.
- SSC and SC stdout logs contain one `prepared` line. SSC cells have one `embedding_F.npy`, one `embedding_G.npy`, and one integer `n_irls_iterations`. The 50 trials do not re-solve F or G. The randomness that the ± reports is K-means (`kmeans_init` random for the SSC/SC/K1 cells; k-means++ only on the K3 cells, which are a separate diagnostic).

E1’s new table has 800 rows. Each of the 16 arms (4 datasets × 2 inits × F/G) has seeds 0..49. Explicit fields are `n_init=1`, `max_iter=300`, `tol=1e-4`, `algorithm=lloyd`.

## Paper numbers were not copied into the reproduced column

Matrix `results/strict_reproduction_matrix.csv`: the Paper ACC field of completed cells contains `historical only`. The Reproduced ACC field does not. For rows that report the 50-trial mean, the parsed percent matches `metrics.json` `acc_mean` within 6e-4 in fraction units (one decimal place in percent). Rows K2 and K4 report a single trial, the lowest K-means inertia inside the parent K1 or K3 run, and the matrix run id points at that parent. Those rows match that trial’s ACC under the same tolerance. They are not a second sample of 50. No reproduced cell failed this check after that distinction was applied.

SMOKE runs (n = 1) are excluded from the 52.
