# LDA + K-means (Ding and Li)

**Package status:** `PAPER_FAITHFUL_REIMPLEMENTATION` of Ding and Li, ICML 2007, Algorithm 1. Ridge and `max_iter=30` are `AMBIGUITY_RECONSTRUCTION`. Ground-truth labels are never used.

Master index: [`baselines/README.md`](../README.md).

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| Algorithm paper | Ding and Li, ICML 2007, “Adaptive Dimension Reduction Using Discriminant Analysis and K-means Clustering”, pp. 521–528, DOI `10.1145/1273496.1273562`. Author PDF read 2026-10-21: https://ranger.uta.edu/~chqding/papers/Ding-AdapDimReduct.pdf | `VERIFIED ORIGINAL PUBLICATION` |
| SSC citation | Chang et al., AAAI 2015, “LDA Kmeans (Ding and Li 2007)”. Setup still writes 10…150 for every DR baseline. | `VERIFIED ORIGINAL PUBLICATION` |
| Author code | No implementation repository found. | not `VERIFIED AUTHOR CODE` |
| This package | `baselines/lda_kmeans/` | `INDEPENDENT REIMPLEMENTATION` |

No invented GitHub URL.

## Original math (original equation numbers)

Ding and Li, after centering \(X\) (Section 2: “the data is centered in the preprocessing step”):

Eq. (2)–(3):

\[
S_t=\sum_i x_i x_i^\top,\quad
S_b=\sum_k n_k m_k m_k^\top,\quad
S_w=\sum_k\sum_{i\in C_k}(x_i-m_k)(x_i-m_k)^\top
\]

Eq. (1) is K-means \(J_K=\operatorname{Tr}(S_w)\). Eq. (4)/(6)–(7) are the LDA / joint objectives. Eq. (7) as printed:

\[
\max_{U,H}\ \operatorname{Tr}(U^\top S_b U)/\operatorname{Tr}(U^\top S_w U)
\]

Labels in \(H\) are **cluster indicators from K-means**, not ground truth (Section 3: “we use K-means clustering to generate class labels and use LDA to do subspace selection”).

Algorithm 1 Step 1: subspace dimension \(d=K-1\).

## Original algorithm mapped to paper sections

Ding and Li Algorithm 1 (Section 3):

| Step | Paper | This package |
| --- | --- | --- |
| 1 | \(K\) clusters, \(d=K-1\) | `n_components` required; values \(>K-1\) raise (`_prepare_subspace`, `lda_kmeans.py` 99–113) |
| 2 | PCA on \(X\) for initial \(U\) | `_pca_basis` (25–29), called at 163 |
| 3 | LDA-Km(1): K-means in the subspace → \(H\) | `kmeans_fit_predict(centered @ basis, ...)` (164, 169) |
| 4 | LDA-Km(2): LDA from \(H\) → \(U\) | `lda_basis` (58–96, 168) |
| 5 | repeat until convergence | loop 165–173; stop on unchanged labels or `max_iter` |

Section 2 centering: `lda_kmeans.py` 112.

## Our implementation mapped to real files

Import: `from baselines.lda_kmeans import fit_predict`

| Piece | File | Function | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Defaults | `baselines/lda_kmeans/lda_kmeans.py` | `_DEFAULTS` | 14–22 (`max_iter=30`, `sw_reg=1e-8`, `init="random"`) |
| Scatter \(S_b,S_w\) | same | `_scatter` | 32–55 |
| LDA generalized eigenproblem | same | `lda_basis` | 58–96 |
| Rank / centering | same | `_prepare_subspace` | 99–113 |
| Public fitter | same | `fit_predict` | 116–174 |
| Signature has no `y` | same | passing `y=` raises `TypeError` via `resolve_params` | tested |

Inner K-means uses `init="random"`, `n_init=1` unless overridden.

## Fidelity audit

| Item | Status | Notes |
| --- | --- | --- |
| Algorithm 1 loop | `PAPER_FAITHFUL_REIMPLEMENTATION` | |
| Cluster labels, never GT | `PAPER_FAITHFUL_REIMPLEMENTATION` | |
| \(d=K-1\) cap | `PAPER_FAITHFUL_REIMPLEMENTATION` of Ding–Li; Chang’s 10…150 is infeasible above \(K-1\) | no PCA padding |
| Centering | `PAPER_FAITHFUL_REIMPLEMENTATION` of Section 2 | |
| `sw_reg=1e-8` when \(S_w\) singular | `AMBIGUITY_RECONSTRUCTION` | paper silent; `sw_reg=0` refuses |
| `max_iter=30` | `AMBIGUITY_RECONSTRUCTION` | paper: “until convergence”; complexity remark \(t\simeq 10\) |
| Chang 10…150 on LDA | not implemented as padding | fitter raises rather than inventing extra axes |

## SSC comparison protocol vs this baseline’s own paper settings

| Setting | Ding and Li 2007 | Chang et al. 2015 | This fitter |
| --- | --- | --- | --- |
| Subspace dim | \(K-1\) | “10 to 150” for every DR method | required; \(\le K-1\) |
| Labels for LDA | K-means indicators | not restated | cluster labels only |
| Inner K-means init | unspecified | random | default `random` |

For USPS (\(K=10\)) classical LDA has at most 9 directions. The fitter does not silently clip or pad.

## Tests actually run

`baselines/lda_kmeans/test_lda_kmeans.py`: `test_lda_kmeans_uses_cluster_labels_and_respects_rank` (line 34). Rejects missing `n_components`, `n_components>K-1`, and `y=truth`. Tiny blobs only.

## Experimental results

| Dataset | Paper ACC% | Our Track A | Track A run_id | Track B | Track B run_id |
| --- | --- | --- | --- | --- | --- |
| JAFFE | 76.5 ± 1.7 | 64.8 ± 11.7 (n=10, dim=9) | `20261020_015602__TRACKA__LDAKM__JAFFE__769f39c4` | 64.4 ± 9.2 (n=50) | `20261020_015808__TRACKB__LDAKM__JAFFE__05066b21` |
| ORL | 65.6 ± 2.6 | 48.5 ± 3.7 (n=10, dim=20) | `20261020_020157__TRACKA__LDAKM__ORL__fb14ac44` (rerun; FAILED `20261020_015425__TRACKA__LDAKM__ORL__fb14ac44` kept) | 48.5 ± 3.0 (n=50) | `20261020_015636__TRACKB__LDAKM__ORL__f5aa3bcc` |
| others | see paper | N/A — not reproduced | — | N/A — not reproduced | — |

## Limitations

- Why Track A selected ORL dim=20 rather than \(39=K-1\) is a protocol/selection issue.
- Whether Chang padded LDA with PCA to reach dim≥10 is unknown; this code does not.

## Reproduction commands

```text
python -m pytest baselines/lda_kmeans -q
```
