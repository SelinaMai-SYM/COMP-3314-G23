# P0 repository audit

Audit date: 2026-11-03. Branch `v1`. This note reads the repository as it was before the extension matrix. Historical ACC/NMI below are citations of existing `metrics.json` files. They are not copied into `results/extension_research/extension_matrix.csv`.

## Commit

- `HEAD` at the start of this round: `8e215ab859dfcf30d2ca9599f25c2abddc49ff8d`
- `origin/v1` at the start of this round: the same hash
- Remote: `git@github.com:SelinaMai-SYM/COMP-3314-G23.git`
- The working tree already had uncommitted edits under `report/`. Those files are not part of this extension round and are not staged.

## Solver

`SpectralShrunkClustering` defaults to `variant="E13"` (printed Equation 13, Laplacian coefficient 1). The primary control for this round is reconstructed SSC **E8**: `variant="E8"`, coefficient 2, `gamma=1`, `k=5`, `G0=F`, random Lloyd, `n_init=1`, seeds 0..49. E13 is not used as that control.

## What loads

| Name | Version | This-round status |
| --- | --- | --- |
| ORL | `att92` | loads, 400 x 1024, 40 classes |
| JAFFE | `zenodo` | loads, 213 x 676, 10 classes |
| YaleB | `cropped2414` | loads, 2414 x 1024, 38 classes |
| YaleB | `dengcai32` | loads, 2414 x 1024, 38 classes; same benchmark, different pixels |
| USPS | `libsvm` | loads, 9298 x 256, 10 classes |
| BinAlpha | `CANDIDATE_BIN_ALPHA` | loads, `NON_EXACT_DATASET` |
| UMIST | `precropped575` | loads, `NON_EXACT_DATASET` |
| MSRA50 | — | `DatasetUnavailable`, excluded |
| AR | — | `DatasetUnavailable`. License, 120-person labels, official images, and one paper preprocessing rule are not all satisfied. Status `BLOCKED`. Not called paper AR and not run as `AR100_ZENODO`. |

Registry: `configs/extension_dataset_registry.yaml`.

## Historical primary cells, read from disk

E8, gamma=1, cluster on G, unless noted. Values are `acc_mean` from the named file.

| Dataset | Role | acc_mean | File |
| --- | --- | --- | --- |
| ORL att92 | SC | 0.5618000000 | `runs/strict_paper/20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce/metrics.json` |
| ORL att92 | SSC E8 | 0.5726500000 | `runs/strict_paper/20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41/metrics.json` |
| JAFFE zenodo | SC | 0.6852582160 | `runs/strict_paper/20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b/metrics.json` |
| JAFFE zenodo | SSC E8 | 0.6843192488 | `runs/strict_paper/20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d/metrics.json` |
| YaleB cropped2414 | SC | 0.1833968517 | `runs/strict_paper/20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51/metrics.json` |
| YaleB cropped2414 | SSC E8 | 0.1762220381 | `runs/strict_paper/20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff/metrics.json` |
| USPS libsvm | SC | 0.6173886857 | `runs/strict_paper/20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055/metrics.json` |
| USPS libsvm | SSC E8 | 0.6169821467 | `runs/strict_paper/20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b/metrics.json` |

Mutual kNN on JAFFE, same F as union E8, from `runs/round2/20261021_161924__ROUND2__JAFFE__EXT_JAFFE_MUTUAL_KNN__45fd1c1f/metrics.json`: ACC 0.6836619718. Union control in that round, `runs/round2/20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7/metrics.json`: ACC 0.6843192488. The saved conclusion stays neutral to negative. Those files are not overwritten.

## Caches, convergence, open protocol points

- Large embedding arrays under `runs/strict_paper/` and `runs/final_round/` are gitignored. The committed record is `metrics.json`, config, and history.
- This round writes new runs under `runs/extension_research/` and does not write into `runs/strict_paper/` or `runs/final_round/`.
- A fresh USPS E8, gamma=1 call of `shrink_embedding` during this audit converged in 298 iterations (`runs/extension_research/cache/`, not committed). YaleB D0 did not meet the relative-step tolerance by iteration 300. That status is `NONCONVERGED` in the new diagnostic CSV, and the returned G is still scored.
- Unresolved, and not decided by this round's ACC: the authors' delta, union versus mutual, resize kernel, eigenvector signs, whether Table 1 used Equation (13) or the Equation (8) stationary system, and which gamma sits behind each published SSC cell. `report/main.tex` is not edited.

## Implementation check

See `docs/extension_research/P0_yaleb_root_cause.md`. Conclusion: `NO CONFIRMED IMPLEMENTATION BUG`. `SSC_method/` and `baselines/` were not modified.
