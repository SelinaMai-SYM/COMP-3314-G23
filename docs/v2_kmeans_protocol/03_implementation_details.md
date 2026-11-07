# Implementation

Upstream SSC is the existing E8 solver, not a second copy and not Equation (13).

- Neighborhood size `k = 5`.
- `G0 = F`.
- Union symmetrization, symmetric normalized Laplacian, median positive kNN squared distance, no Ng–Jordan–Weiss row normalization.
- Linear system `A = S + 2 gamma Ltilde`. The coefficient 2 is the ordered-pair stationary system of printed Equation (8).
- IRLS `max_iter = 300`, `tol = 1e-6`. If the solver stops at the iteration cap, the status is `NONCONVERGED_RETURNED_ITERATE` and the cell is a measurement on that iterate.

`F` is computed once per dataset version. Each gamma rebuilds only `G`. A cache is reused only when the dataset hash, the `SSC_method` source hash, `variant=E8`, Laplacian coefficient 2, `G0=F`, `k=5`, and the config hash all match. v1 accuracy tables are not copied into the new CSVs.

K-means, via the installed scikit-learn `KMeans`:

- `n_init = 1`, `algorithm = "lloyd"`, `max_iter = 300`, `tol = 1e-4`
- seeds `0..49` for the primary batch
- `init = "random"` for P1/P2
- `init = "k-means++"` for P3/P4, labeled `SKLEARN_GREEDY_KMEANSPP`
- vanilla centers from `kmeans_plusplus(..., n_local_trials=1)`, then one Lloyd run

P2 reads the P1 rows. P4 reads the P3 rows. The selected seed on `F` is not forced onto `G`. Accuracy and NMI are computed from that one labeling with the Hungarian assignment and the geometric-mean NMI. Sample SDs use `ddof = 1` and are attached only to means of the 50 runs.

Full assignment arrays stay in `runs/v2_kmeans_protocol/arrays/` and are gitignored. Selected labelings and centers are copied into `results/v2_kmeans_protocol/selected_labels/` and `selected_centers/`.
