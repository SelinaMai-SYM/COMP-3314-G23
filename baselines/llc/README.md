# LLC (Wu and Schölkopf, NIPS 2006)

**Package status:** `PAPER_FAITHFUL_REIMPLEMENTATION` of Wu and Schölkopf Eqs. (9)–(15) and (17)–(19). Default `k=5` is the **SSC comparison protocol**, not LLC’s own search. Yang, Xu, Nie, Yan, and Zhuang, IEEE TIP 2010 is **not** the specification and is **not** mixed in.

Master index: [`baselines/README.md`](../README.md).

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| Spec | Wu and Schölkopf, NIPS 2006, “A Local Learning Approach for Clustering”. OA PDF read 2026-10-21: https://proceedings.neurips.cc/paper_files/paper/2006/file/366f0bc7bd1d4bf414073cabbadfdfcd-Paper.pdf | `VERIFIED ORIGINAL PUBLICATION` |
| Discretization they adopt | Yu and Shi, ICCV 2003, “Multiclass Spectral Clustering” (their ref. [10]). They point at Jianbo Shi’s 2006 spectral-clustering code for that step only. | `VERIFIED ORIGINAL PUBLICATION`; no maintained LLC package found |
| SSC comparison | Chang et al., AAAI 2015, Setup `k=5` for all spectral methods; they also mention Yang et al. 2010 **and** Wu–Schölkopf when replacing \(L\) in Eq. (3) by a local-learning Laplacian. | `VERIFIED ORIGINAL PUBLICATION` |
| Yang et al. 2010 | **Not used as the spec.** Different local-learning Laplacian. Mixing it in would be a silent method swap. | not implemented |
| This package | `baselines/llc/` | `INDEPENDENT REIMPLEMENTATION` of Wu–Schölkopf |

No invented GitHub URL. The 2006 Jianbo Shi software URL in Wu–Schölkopf §4 is a historical pointer, not a cloned repo here.

## Original math (original equation numbers)

Wu–Schölkopf:

- Eq. (9): \(\alpha_i^\top = k_i^\top(K_i+\lambda I)^{-1}\)
- Eq. (10): \(o^l = A f^l\), with \(A_{ij}\) from \(\alpha_i\) on neighbors, else 0
- Eq. (13): \(T=(I-A)^\top(I-A)\)
- Eq. (14)–(15): \(\min_F \operatorname{Tr}(F^\top T F)\) s.t. \(F^\top F=I\)
- Eq. (17)–(19): Yu–Shi discrete Procrustes problem on the row-normalized embedding \(P^\star\)
- Eq. (22): cosine kernel \(x_i^\top x_j/(\|x_i\|\|x_j\|)\)
- Eq. (23): Gaussian \(K_2(x_i,x_j)=\exp(-\|x_i-x_j\|_2^2/\gamma)\) — divide by \(\gamma\), **not** \(\gamma^2\)

§4.3 grids: \(k\in\{5,10,20,40,80\}\); \(\lambda\in\{0.1,1,1.5\}\); \(\gamma\in\{\sigma_0^2/16,\ldots,16\sigma_0^2\}\) with \(\sigma_0\) the mean Euclidean norm of the rows.

They explicitly adopt Yu–Shi rather than K-means on the embedding (§3.6).

## Original algorithm mapped to paper sections

| Paper step | Section / eq. | This package |
| --- | --- | --- |
| Local KRR coefficients | §3.4, Eqs. (9)–(10) | `local_regression_matrix` (`llc.py` 54–95) |
| Neighbors | §3; \(k\) searched in §4.3 | `baselines.spectral_clustering.neighbor_indices` (LLC helper, not the Eq. (4) graph) |
| \(T=(I-A)^\top(I-A)\), smallest eigenvectors | Eqs. (13)–(15) | `fit_predict` 189–193 |
| Row-normalize \(F^\star\to P^\star\) | mapping (2) / §3.6 | `fit_predict` 194–195 |
| Yu–Shi discretization | Eqs. (17)–(19) | `yu_shi_discretize` 117–148 |
| Gaussian / cosine kernels | Eqs. (23)/(22) | `_kernel_blocks` 37–51 |

## Our implementation mapped to real files

Import: `from baselines.llc import fit_predict`

| Piece | File | Function | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Defaults | `baselines/llc/llc.py` | `_DEFAULTS` | 12–19: `n_neighbors=5`, `reg=1.0`, `kernel="gaussian"`, `gamma=None` |
| Matrix \(A\) | same | `local_regression_matrix` | 54–95 |
| Yu–Shi | same | `yu_shi_discretize` | 117–148 |
| Public fitter | same | `fit_predict` | 151–203 |
| Jobs | `experiments/methods.py` | `prepare_llc_embedding` + `yu_shi_discretize` | 268–292, 316–320: `k` from protocol, `reg=1.0`, `gamma=None` |

Default `gamma=None` sets \(\gamma=\sigma_0^2=(\text{mean row Euclidean norm})^2\) (`llc.py` 79–81): the **center** of Wu–Schölkopf’s \(\gamma\) grid, not a selected optimum.

## Fidelity audit

| Item | Status | Notes |
| --- | --- | --- |
| Eqs. (9)–(15), (17)–(19), (22)–(23) | `PAPER_FAITHFUL_REIMPLEMENTATION` | |
| Default \(k=5\) | SSC protocol, not LLC’s search | documented; not a silent Yang-2010 swap |
| Default \(\lambda=1\) | one value on their `{0.1,1,1.5}` | `AMBIGUITY_RECONSTRUCTION` vs a search |
| Default \(\gamma=\sigma_0^2\) | center of their grid | `AMBIGUITY_RECONSTRUCTION` vs a search |
| Yu–Shi `tol=1e-8` | `AMBIGUITY_RECONSTRUCTION` | paper: machine epsilon |
| Yang et al. 2010 Laplacian | **not implemented** | do not mix |

**Higher ACC is not evidence of greater faithfulness.**

## SSC comparison protocol vs this baseline’s own paper settings

| Setting | Wu–Schölkopf 2006 | Chang et al. 2015 | This fitter default |
| --- | --- | --- | --- |
| \(k\) | search `{5,10,20,40,80}` | 5 for all spectral methods | 5 (SSC protocol) |
| \(\lambda\) | `{0.1,1,1.5}` | comparison-alg grid `{1e-6,…,1e6}` does not map cleanly | 1 |
| \(\gamma\) | grid around \(\sigma_0^2\) | same mismatched grid | \(\sigma_0^2\) |
| Laplacian | \(T=(I-A)^\top(I-A)\) | also cites Yang 2010 | Wu–Schölkopf only |
| Discretization | Yu–Shi, not K-means | unspecified for LLC | Yu–Shi |

An independent LLC grid (their §4.3) may be stored separately later. Do not silently replace SSC `k=5` jobs with that grid under the same method name.

## Tests actually run

`baselines/llc/test_llc.py`: `test_llc_follows_local_learning_and_is_deterministic` (line 31). Gaussian and cosine. Tiny blobs only.

## Experimental results

| Dataset | Paper ACC% | Our Track A | Track A run_id | Track B | Track B run_id |
| --- | --- | --- | --- | --- | --- |
| JAFFE | 78.6 ± 1.5 | **88.4 ± 6.9 (n=50)** | `20261020_015458__TRACKA__LLC__JAFFE__23d153da` | 88.4 ± 6.9 (n=50) | `20261020_015824__TRACKB__LLC__JAFFE__3badacab` |
| ORL | 71.5 ± 2.2 | 62.1 ± 2.0 (n=50) | `20261020_015219__TRACKA__LLC__ORL__81ec6378` | 62.1 ± 2.0 (n=50) | `20261020_015755__TRACKB__LLC__ORL__07af2c07` |
| others | see paper | N/A — not reproduced | — | N/A — not reproduced | — |

JAFFE beating the paper by ~10 points can come from `k=5`, \(\gamma=\sigma_0^2\), Yu–Shi vs another discretizer, preprocessing, or a 2015 Yang-2010 Laplacian. It does **not** mean this LLC is “more correct than the paper”, and it must not replace SSC numbers.

## Limitations

- Which \((k,\lambda,\gamma)\) Chang reported is unknown.
- Whether 2015 used Yang et al. 2010 is unknown; this code did not.

## Reproduction commands

```text
python -m pytest baselines/llc -q
```

## Task 1（2026-10-21）

新文件：`resources/Wu_Schoelkopf_2006_NIPS_LLC.pdf` 127718 字节 SHA-256 `17828ebae410aca05c026767bffb2befec09a5edfe4232c770c2782a904c12c3`（NeurIPS OA GET **200**）。作者代码 `CODE_NOT_FOUND`。矩阵状态：`COMPLETE_WITH_UNSPECIFIED_SETTINGS`。
