# SLPS method specification

Source: Hou, Nie, Jiao, Zhang, and Wu, “Learning a subspace for clustering via pattern shrinking,” *Information Processing & Management* 49(4):871–883, 2013. DOI `10.1016/j.ipm.2013.01.004`. Local file `baselines/spls/resources/private/hou2013_slps.pdf` (PDF 1.7, 13 pages). This note is an independent mapping. It is not a transcription of the article.

Chang et al. (AAAI 2015) call the same method **SPLS**. The historical SSC comparison cell is this method. It is not SSC, not PCA on the raw pixels, and not LDA-SC.

The local PDF was read through page 13, including Section 3 and the experimental protocol in Section 4. `FULL_TEXT_VERIFIED_LOCAL` means the file was read. It does not mean the code is correct. The later stages are `METHOD_SPECIFICATION_COMPLETE`, `IMPLEMENTED` (`baselines/spls/spls.py`), and `NUMERICALLY_VALIDATED` (algebraic tests against Eqs. 18–19).

## What this paper does not define

Section 2.1 reviews Ding and Li’s alternating LDA and K-means and names it **LdaKm**. That is LDA-Kmeans. The article never defines an LDA spectral method and never uses the name LDA-SC. LDA-SC stays `METHOD_DEFINITION_UNRESOLVED`.

## Variables and shapes

Table 1 (p. 874):

| Symbol | Shape in the paper | Meaning |
| --- | --- | --- |
| `n` | scalar | number of samples |
| `r` | scalar | original dimension |
| `d` | scalar | subspace dimension |
| `c` | scalar | number of clusters, used only for the final clustering stage |
| `x_i` | `r × 1` | original sample |
| `X` | `r × n` | samples stored as columns |
| `y_i` | `r × 1` | shrunk pattern of `x_i` |
| `Y` | `r × n` | shrunk patterns as columns |
| `P` | `r × d` | orthogonal projection, `P^T P = I` |
| `z_i = P^T y_i` | `d × 1` | embedding |
| `Z = P^T Y` | `d × n` | embeddings as columns |
| `W` | `n × n` | symmetric nonnegative graph |
| `D` | `n × n` | diagonal degree, `D_ii = sum_j W_ij` |
| `L = D − W` | `n × n` | unnormalized Laplacian (p. 875) |
| `H = I − (1/n) 11^T` | `n × n` | centering matrix (Eq. 13) |
| `α` | scalar in `(0, 1)` | balance between graph shrinking and fidelity to `X` |
| `β` | scalar | balance for the variance term. One-shot SLPS is the limit `β → 0` |
| `k`, `r` (width) | scalars | graph neighborhood size and Gaussian width |

The code stores samples as rows, shape `(n, r)`. Eq. (18) is applied on the left, `Y_rows = α M^{-1} X_rows`, which is the transpose of the paper’s column layout.

## Graph

Eq. (7), p. 874, builds a union kNN graph. `W_ij = W_ji = exp(−||x_i − x_j||^2 / (2 σ^2))` when `x_j` is among the k neighbors of `x_i` or the reverse, and `0` otherwise. `σ` is the global width.

Section 3.3 (p. 877) and Section 4 (p. 879) do not search that global width. They replace it by the local scale of Zelnik-Manor and Perona (2004): `σ_i` is the distance from `x_i` to its k-th neighbor. The cited local-scaling weight is `exp(−||x_i − x_j||^2 / (σ_i σ_j))`. The code uses that product form. It does not keep an extra factor of 2 in the denominator after the Section 4 substitution. Section 4 fixes `k = 7` in every experiment. A one-sided kNN edge is kept at its own weight (`maximum` with the transpose), not averaged with a structural zero.

## Objective

Three terms (Section 3.1):

1. Nearby samples shrink together: `sum_{i,j} W_ij ||y_i − y_j||^2` (Eq. 8).
2. Shrunk patterns stay near the original points: `sum_i ||x_i − y_i||^2` (Eq. 9).
3. The embedding keeps variance: `sum_i ||z_i − mean(z)||^2` (Eq. 10), with `P^T P = I`.

Eq. (11) combines them. Eq. (12) substitutes `z_i = P^T y_i`. With the Laplacian and the centering matrix this is Eq. (13):

`L(P, Y) = (1 − α) tr(Y L Y^T) + α tr((X − Y)^T (X − Y)) − β tr(P^T Y H Y^T P)`.

The first trace is a ratio of quadratic forms only in the sense that it is already written as a trace. It is not “the trace of a matrix ratio.”

## Updates

The joint problem is not claimed to be convex in `(P, Y)` (p. 876). Table 2 alternates:

1. Build `W` by Eq. (7), with the Section 4 local-scaling substitution.
2. Fix `P` and solve the linear system Eq. (16) for the vectorized shrunk pattern. `M = P P^T`.
3. Fix `Y` and take the top eigenvectors of `Y H Y^T` (Eq. 17), which is PCA of the shrunk patterns.
4. Set `Z = P^T Y`.

Proposition 1: as `β → 0`, the Y-step collapses to Eq. (18),

`Y = α X [(1 − α) L + α I]^{-1}`.

Eq. (19) is then PCA of that `Y`. The paper states that every comparison experiment uses this one-shot form (p. 876): “in the following experiments, we all use one-shot SLPS.” The alternating `β > 0` procedure is derived and illustrated on a toy, and it is not the experimental comparator. The v3 code implements Eqs. (18)–(19), not the alternating Table 2 loop. `β` is recorded as 0.

Initialization of one-shot SLPS is the input matrix `X` and the kNN graph. There is no random start inside the shrink. K-means, which comes after the embedding, has its own initialization.

Stopping: one-shot SLPS has no iteration. The paper does not give a numeric tolerance for the alternating loop. v3 does not run that loop, so it does not invent a tolerance for it.

## Final clustering

Section 3.3 (p. 877) says pattern shrinking is a preprocessing step. The paper then clusters the embedding with K-means (**PsKm**) or normalized cut (**PsNcut**). Section 4 evaluates the K-means run, among 100 runs, that minimizes the K-means loss, and it plots that result against subspace dimension `d`. Alpha is searched on `{0.05, 0.10, …, 0.95}` and “the best one” is chosen (p. 877). No label-blind selection rule for alpha or `d` is stated. v3 does not choose either quantity by test accuracy or by comparing K-means inertia across different subspaces.

PsNcut is a second method in Hou et al. Chang et al. list one SPLS column. v3 keeps the K-means stage (PsKm) for that column and does not relabel PsNcut as SPLS.

## SSC comparison settings that override the SLPS paper

These overrides are protocol differences, not a different shrink:

- Neighbor count inside SSC’s own methods is `k = 5`. SLPS keeps the paper’s `k = 7`.
- Chang et al. repeat clustering 50 times and report mean and standard deviation. Hou et al. report the minimum K-means loss over 100 runs. v3 uses the SSC repetition count and reports per-run mean and standard deviation separately from a minimum-inertia selection inside one subspace.
- The SSC parameter grid `{1e-6, …, 1e6}` is not Hou’s alpha grid. v3 searches Hou’s alpha grid and does not rename alpha to `ssc_gamma`.
- No single alpha or dimension is declared the paper operating point. The locked numeric column stays empty. `α = 0.5`, `d = 50` is only a repeatability probe.

## Code map

| Paper object | Code |
| --- | --- |
| Eq. (7) with Section 4 local scaling | `local_scaling_affinity` |
| Eq. (18) | `oneshot_shrunk_patterns` |
| Eq. (19) | `pca_embedding` |
| PsKm | `fit_predict`, one K-means call on the embedding |
| Ground-truth labels | rejected if passed as `y` |

No author implementation was found. The code is an independent reimplementation of the published one-shot procedure.
