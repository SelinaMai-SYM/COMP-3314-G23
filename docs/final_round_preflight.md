# Final-round preflight (E1–E6)

Written from run records before any `runs/final_round/` solve.
Source of truth: `runs/strict_paper/*/metrics.json`, `status.json`, `config.yaml`, `objective_history.csv`, and on-disk `embedding_F.npy` / `embedding_G.npy`.
`results/strict_reproduction_matrix.csv` is an index of those runs. Older READMEs are not used as numbers.
HEAD at preflight: `cb870acd47f9a62726c0cdab9b3b03395cc5e1cc`. Not reset.
The strict_paper runs record `git_head` `47c0f83` with a dirty tree; that tree is an ancestor of HEAD, and HEAD is the commit of those campaign files. Embeddings are still taken from the run directory, not recomputed for E1–E2.

Datasets in scope: ORL `att92`, JAFFE `zenodo`, YaleB `cropped2414`, USPS `libsvm`.
Primary SSC cell: variant E8, γ = 1, k = 5, `cluster_on: G`, `kmeans_init: random`, `n_init: 1`, `max_iter: 300`, `tol: 1e-6`, `zero_residual_floor: median_pairwise`, `g_init: F`, `row_normalize: false`, symmetrization union, bandwidth median of positive kNN squared distances.

## What is reusable

For every SSC E8 and E13 cell on the four datasets, γ ∈ {1e-6, 1e-3, 1, 1e3, 1e6}:

- status COMPLETED, `n_trials_completed = 50`
- `metrics.json` `trial_seeds` is exactly `[0, 1, …, 49]` (48 cells checked: SSC E8, SSC E13, SC, K1; 0 mismatches)
- `embedding_F.npy` and `embedding_G.npy` exist (gitignored, present on disk)
- `objective_history.csv` exists and has one row per recorded IRLS iteration
- per-trial `label_disagreement_F_G` is stored for SSC cells (same seed on F and on G)
- shrinkage graph **statistics** and `delta2` are inside `metrics.json` (`shrinkage_graph`, `shrinkage_graph_stats`)

SC Eq. (4) cells also have `embedding_F.npy` and 50 seeds. They have no G and no objective history.

K1 cells have 50 seeds and no embedding files. They are not an F/G cache.

No `runs/strict_paper` directory has `max_iter` above 300. There is no saved iterate at budget 1000 or 2000.

The affinity matrix W is **not** stored as an array. E2/E3 must rebuild W from the saved F using the recorded `k`, `delta2`, `knn_method`, and symmetrization, then reject the rebuild unless `n_undirected_edges`, `n_stored_nnz`, and connected-component count match `shrinkage_graph_stats`.

## Primary E8 γ = 1 caches (one F, one G per dataset)

| Dataset | Run ID | IRLS | Eq. (8) history | ACC mean (metrics.json) |
| --- | --- | --- | --- | --- |
| ORL att92 | `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41` | not converged, 300 steps, fixed-point residual 0.01310 | 300 rows | 0.57265 |
| JAFFE zenodo | `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d` | not converged, 300 steps, fixed-point residual 0.07963 | 300 rows | 0.68432 |
| YaleB cropped2414 | `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff` | not converged, 300 steps, fixed-point residual 0.19422 | 300 rows | 0.17622 |
| USPS libsvm | `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b` | converged at iteration 298, fixed-point residual 0.32205 | 298 rows | 0.61698 |

ACC above is the stored mean over 50 random K-means trials on G. It is not a new measurement.

Matching SC Eq. (4) runs, same seeds, K-means on F: ORL `20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce` ACC 0.56180; JAFFE `20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b` ACC 0.68526; YaleB `20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51` ACC 0.18340; USPS `20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055` ACC 0.61739.

## Gamma-grid G files reused by E2 (E8)

All five γ values have F, G, history, and n = 50. E13 files exist and are not the primary arm.

| Dataset | γ = 1e-6 | 1e-3 | 1 | 1e3 | 1e6 |
| --- | --- | --- | --- | --- | --- |
| ORL | `…ORL__SSC_E8_G1EM6__adf2580d` conv 3 | `…G1EM3__df6428ad` conv 4 | `…G1P0__4be5ba41` **not** conv 300 | `…G1E3__242cbb2a` conv 206 | `…G1E6__6f1ea6fc` **not** conv 300 |
| JAFFE | `…JAFFE__SSC_E8_G1EM6__675147ed` conv 3 | `…G1EM3__c0897140` conv 4 | `…G1P0__8a4a026d` **not** conv 300 | `…G1E3__ef79feea` conv 296 | `…G1E6__a7b0e589` **not** conv 300 |
| YaleB | `…YALEB__SSC_E8_G1EM6__da885cd6` conv 3 | `…G1EM3__19b9bf6c` conv 4 | `…G1P0__2ba528ff` **not** conv 300 | `…G1E3__9a7861d8` conv 130 | `…G1E6__96e89a23` **not** conv 300 |
| USPS | `…USPS__SSC_E8_G1EM6__ddf1165e` conv 3 | `…G1EM3__5c173e5c` conv 4 | `…G1P0__0a34012b` conv 298 | `…G1E3__e8aad5e1` **not** conv 300 | `…G1E6__bf47b88e` conv 288 |

Run IDs are prefixed `20261021_*__STRICT_PAPER__`. “conv k” means `irls_converged` true and `n_irls_iterations = k`. A true flag means the relative Frobenius step met `tol = 1e-6`. It is not an optimality certificate: several converged cells still have a fixed-point residual well above 1e-4 (ORL E8 γ = 1e-3 residual 0.194; USPS E8 γ = 1 residual 0.322).

## E3 budgets

Required real-data cases: ORL γ = 1, YaleB γ = 1, USPS γ = 1000 (run `20261021_225950__STRICT_PAPER__USPS__SSC_E8_G1E3__e8aad5e1`, 300 steps, not converged, IRLS wall time 13.23 s).

None of the three already has a solved iterate past 300. Budgets 1000 and 2000 have to be computed, with F and rebuilt W held fixed. Budget 300 is the saved G, checked by a fresh 300-step solve.

USPS E8 γ = 1 already stopped at iteration 298. That run is not the E3 USPS case. It is not re-solved.

The small-graph CVXPY comparison is `tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term`. Re-run it. Do not treat a pass as a new proof.

## E4 and E5 gaps

Strict-paper YaleB rows use `cropped2414` only. Deng Cai `YaleB_32x32.mat` is on disk (`benchmarks/yaleb/data/YaleB_32x32.mat`) but has no strict_paper embedding. E4 must embed both versions. The 72-cell matrix is not rerun.

Objective histories for E5 Figure 2 (γ = 1, E8) exist for all four datasets. No minimum solve is required unless a history file fails to load. Figure 1 uses the saved E8 γ-grid ACC values. Published Figure 1 and Figure 2 also include AR, UMIST, binalpha, and MSRA50. Those four panels have no completed strict_paper clustering run (AR / UMIST / MSRA50 blocked; BinAlpha is `CANDIDATE_BIN_ALPHA`, not a paper identity). They are omitted, not imputed.

Paper PDF inspected for captions: `SSC_method/resources/Chang_et_al_2015_SSC_AAAI.pdf` (7 pages). Body text: Figure 1 is ACC versus γ on all eight experimental datasets; Figure 2 is the objective curve with γ fixed at 1. Published points were not digitized.

## What E1 still has to compute

Saved SSC trials use `init: random` only. `experiments/methods.py` `_kmeans_labels` passes `n_init=1` and `algorithm=lloyd` but does not pass `max_iter` or `tol`. scikit-learn 1.8.0 defaults those to 300 and 1e-4, and its default `init` is `k-means++`. E1 must pass every setting explicitly and add the k-means++ arms. Those arms are Level C. New trial logs go under `runs/final_round/`.

## Not reused as if they were this protocol

- Smoke run `20261021_222114__STRICT_PAPER__ORL__SMOKE_SSC_E8_G1__e5e77e45` (n = 1).
- Any `runs/strict_repro/` or Track A directory.
- README tables and `docs/critical_analysis.md` (different trial counts and, for ORL, a different image release).
