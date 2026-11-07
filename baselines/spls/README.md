# SPLS / SLPS

**Package status:** `NUMERICALLY_VALIDATED` one-shot reimplementation.

Hou, Nie, Jiao, Zhang, and Wu, *Information Processing & Management* 49(4):871–883, 2013. DOI `10.1016/j.ipm.2013.01.004`. Title: “Learning a subspace for clustering via pattern shrinking.” Chang et al. (AAAI 2015) call it **SPLS**.

The 13-page publisher PDF is local and read-only. A private copy for this worktree is `resources/private/hou2013_slps.pdf`. That directory is gitignored. The PDF and a full text extract are not committed. Reading the PDF is `FULL_TEXT_VERIFIED_LOCAL`. The equation-level notes are `docs/v3/slps_method_specification.md` (`METHOD_SPECIFICATION_COMPLETE`). `spls.py` is `IMPLEMENTED`. Algebraic tests are `NUMERICALLY_VALIDATED`. None of these stages means the SSC table has been reproduced.

No author code was found. Earlier v1/v2 notes that said Section 3 had not been obtained are historical and are superseded by the local PDF.

## Paper procedure that this package runs

Section 4 of Hou et al. uses one-shot SLPS, the `β → 0` case:

1. Union kNN graph, `k = 7`, Zelnik-Manor local scaling in place of the global width in Eq. (7).
2. Shrunk patterns, Eq. (18): `Y = α X [(1−α)L + α I]^{-1}` with samples as columns in the paper. The code stores rows and solves on the left.
3. PCA of those patterns, Eq. (19), subspace dimension `d`.
4. K-means on the embedding (their PsKm). PsNcut is a different wrapper and is not this SSC cell.

`α` is searched on `{0.05, …, 0.95}` in the paper. The paper does not state a label-blind rule for choosing `α` or `d`. v3 does not choose them by accuracy. The campaign’s 50-run SSC protocol overrides the paper’s “best of 100 K-means runs” reporting rule. See the specification for shapes, the objective, and the overrides.

LDA-SC is not defined in this paper. The paper’s LdaKm citation is Ding and Li’s LDA-Kmeans.

## Code

| Piece | Function |
| --- | --- |
| Local scaling graph | `local_scaling_affinity` |
| Eq. (18) | `oneshot_shrunk_patterns` |
| Eq. (19) | `pca_embedding` |
| PsKm | `fit_predict` |

Ground-truth labels are rejected.

## Tests

```text
python -m pytest baselines/spls/test_spls.py -q
```

The tests check a dense Eq. (18) solve, that alpha changes `Y`, that the local-scaling weight matches `exp(-d^2/(σ_i σ_j))`, and that labels are not accepted.

## v3 status

v1/v2 numbers are historical and are not copied into v3 rows. Fresh measurements live under `results/v3_reproduction/` after the campaign writes them.
