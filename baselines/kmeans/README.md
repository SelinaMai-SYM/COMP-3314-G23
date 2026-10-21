# K-means

**Package status:** `PAPER_FAITHFUL_REIMPLEMENTATION`

Round 2 labels only: `EXACT_VERIFIED` / `PAPER_FAITHFUL_REIMPLEMENTATION` / `AMBIGUITY_RECONSTRUCTION` / `APPROXIMATE` / `NOT_IMPLEMENTED` / `UNVERIFIED`. This package is not `EXACT_VERIFIED` (no 2015 author binary). `init="k-means++"` is `AMBIGUITY_RECONSTRUCTION` and is **not** the default.

Master index: [`baselines/README.md`](../README.md). Short audit index: [`docs/round2_baseline_audit.md`](../../docs/round2_baseline_audit.md).

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| SSC comparison protocol | Chang, Nie, Ma, Yang, and Zhou, AAAI 2015, “A Convex Formulation for Spectral Shrunk Clustering”, Setup. OA PDF: https://ojs.aaai.org/index.php/AAAI/article/download/9606/9465 (read 2026-10-21). DOI `10.1609/aaai.v29i1.9606`. | `VERIFIED ORIGINAL PUBLICATION` |
| Classical estimator | Lloyd, IEEE TIT 1982, “Least Squares Quantization in PCM”, DOI `10.1109/TIT.1982.1056489`. Chang et al. name “the classical K-means” and do not cite Lloyd. | `VERIFIED ORIGINAL PUBLICATION` for the estimator; not a new 2015 algorithm |
| Author code | None located. | not `VERIFIED AUTHOR CODE` |
| Library used here | `sklearn.cluster.KMeans` | `THIRD-PARTY` library implementation of Lloyd, wrapped by this package |

No GitHub URL is invented for Chang et al. or Lloyd.

## Original math (original equation numbers)

Chang et al. do not reprint a K-means objective. Lloyd / Ding–Li Eq. (1) is the same sum of squares this fitter minimizes:

\[
\min_H J_K,\qquad J_K=\sum_k\sum_{i\in C_k}\|x_i-m_k\|_2^2
\]

(Ding and Li, ICML 2007, Eq. (1); `H` is the cluster indicator). sklearn inertia is this quantity.

Chang et al. Setup (verified): “repeat each clustering 50 times with **random initialization** and report the results corresponding to the **best objective function values**.”

## Original algorithm mapped to paper sections

| Paper step | Where | This package |
| --- | --- | --- |
| Random initialization | Chang et al., Setup | default `init="random"` in `_DEFAULTS` (`kmeans.py` lines 12–18) |
| Lloyd updates | Lloyd 1982; sklearn `algorithm="lloyd"` | `KMeans(...)` at `kmeans.py` lines 70–79 |
| 50 restarts / best objective | Chang et al., Setup | **not inside this function**. Protocol loops seeds outside. Default `n_init=1` (`kmeans.py` line 13) |

## Our implementation mapped to real files

Import: `from baselines.kmeans import fit_predict`

| Piece | File | Function / name | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Defaults, including `init="random"` | `baselines/kmeans/kmeans.py` | `_DEFAULTS` | 12–18 |
| Public fitter | `baselines/kmeans/kmeans.py` | `fit_predict` | 21–80 |
| sklearn call | `baselines/kmeans/kmeans.py` | `KMeans(...)` then `fit_predict` | 70–80 |
| Shared checks | `baselines/common.py` | `check_problem`, `resolve_params` | 43–61 |
| Export | `baselines/kmeans/__init__.py` | `fit_predict` | — |
| Jobs | `experiments/methods.py` | `run_stateless_method` branch `"kmeans"` | 333–335: `init="random"`, `n_init=1` |

`k-means++` is accepted only when the caller passes `init="k-means++"` (`kmeans.py` lines 63–64). It is not the silent default. sklearn’s own default is `k-means++`; wrapping it with `init="random"` is the paper-faithful choice relative to Chang’s “random initialization”.

## Fidelity audit

| Item | Status | Notes |
| --- | --- | --- |
| Lloyd objective | `PAPER_FAITHFUL_REIMPLEMENTATION` | sklearn Lloyd |
| Default `init="random"` | `PAPER_FAITHFUL_REIMPLEMENTATION` | Chang Setup |
| `init="k-means++"` | `AMBIGUITY_RECONSTRUCTION` | accepted argument; not default; do not switch in place |
| `n_init=1` | `PAPER_FAITHFUL_REIMPLEMENTATION` of “one seeded run”; 50-trial protocol is outside | |
| `tol=1e-4`, `max_iter=300` | `AMBIGUITY_RECONSTRUCTION` | unspecified in 2015 |
| `algorithm="lloyd"` | `PAPER_FAITHFUL_REIMPLEMENTATION` of Lloyd; `"elkan"` is accepted only if passed | |
| Author-binary numerical match | not `EXACT_VERIFIED` | no 2015 code |

## SSC comparison protocol vs this baseline’s own paper settings

| Setting | Chang et al. 2015 | Lloyd 1982 | This fitter |
| --- | --- | --- | --- |
| Initialization | “random initialization” | unspecified modern default | default `random` |
| Restarts | 50, then best objective | not specified | not inside `fit_predict` |
| `k-means++` | not written | not written | explicit argument only |

## Tests actually run

File: `baselines/kmeans/test_kmeans.py`. Tiny synthetic blobs only; not the paper’s eight datasets.

- `test_kmeans_is_deterministic_and_separates_blobs` (line 32)
- `test_kmeans_default_init_is_random_not_kmeanspp` (line 42)
- `test_kmeans_rejects_hidden_and_noninteger_controls` (line 55)

Command from `v1/` with Python 3.13: `python -m pytest baselines -q` → **13 passed in 0.89s** (2026-10-21), including the three tests in this folder.

## Experimental results

Paper cells are Chang et al. 2015 Tables 1–2, **reported only**. Our cells are Track A/B from `results/tables/`. No numbers are invented.

| Dataset | Paper ACC% | Our Track A ACC% | Track A run_id | Our Track B ACC% | Track B run_id |
| --- | --- | --- | --- | --- | --- |
| JAFFE | 75.6 ± 1.8 | 73.2 ± 5.7 (n=50) | `20261020_015445__TRACKA__KMEANS__JAFFE__c6d76526` | 73.2 ± 5.7 (n=50) | `20261020_015758__TRACKB__KMEANS__JAFFE__d794cf45` |
| ORL | 60.5 ± 1.8 | 51.8 ± 3.3 (n=50) | `20261020_015205__TRACKA__KMEANS__ORL__9c448e6b` | 51.8 ± 3.3 (n=50) | `20261020_015620__TRACKB__KMEANS__ORL__4276d994` |
| YaleB | 14.4 ± 1.5 | 9.3 ± 0.6 (n=10) | `20261020_015607__TRACKA__KMEANS__YALEB__e85daf75` | 9.3 ± 0.6 (n=10) | `20261020_015827__TRACKB__KMEANS__YALEB__f0337c3c` |
| USPS | 65.4 ± 1.7 | 66.3 ± 1.7 (n=10) | `20261020_020247__TRACKA__KMEANS__USPS__6af21281` | N/A — not reproduced | — |
| AR / UMIST / BinAlpha / MSRA50 | see paper table | N/A — not reproduced | — | N/A — not reproduced | — |

NMI: JAFFE 83.1 ± 3.5 vs paper 79.4 ± 0.8; ORL 74.4 ± 1.5 vs 80.3 ± 1.8 (`results/tables/table3_track_a_nmi.md`).

## Limitations

- sklearn Lloyd is not proven bit-identical to a 2015 MATLAB/C stack.
- “Random initialization” vs sklearn `init="random"` is the natural reading, not author-code verified.
- Best-objective vs mean±std remains unresolved at protocol level. This fitter does not drop trials by ACC.

## Reproduction commands

From `v1/`:

```text
python -m pytest baselines/kmeans -q
python -c "from baselines.kmeans import fit_predict; print('kmeans-ok')"
```

## Task 1（2026-10-21）

无新文件。Chang AAAI OA 已存于 `SSC_method/resources/`。作者代码 `CODE_NOT_FOUND`。本包装仍是 `THIRD_PARTY_CODE`（sklearn Lloyd）+ `PAPER_BASED_REIMPLEMENTATION`。矩阵状态：`COMPLETE_WITH_UNSPECIFIED_SETTINGS`。
