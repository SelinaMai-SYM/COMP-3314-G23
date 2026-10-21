# Spectral clustering

Status: `PAPER_FAITHFUL_REIMPLEMENTATION`

Original paper: Chang et al., AAAI 2015, Equation (4), the symmetric normalized Laplacian; Shi and Malik, TPAMI 2000, for normalized cut.

## Shared embedding \(F\) with SSC

When the math is the same — Equation (4), \(k=5\), union \(k\)-NN Gaussian — this package and `SSC_method` use one graph / Laplacian / eigensolve (`SSC_method.spectral_config.SpectralGraphConfig` and `SSC_method.spectral_embedding`). `experiments/methods.py` `prepare_spectral` no longer switches backends at `n>1500`.

After the documented sign convention (each column flipped so its largest-magnitude entry is positive), the SC embedding equals the SSC embedding. Shrinkage must not be judged against a second, different \(F\).

Row-normalization stays **off** (Ng–Jordan–Weiss / Category C). LLC does **not** use this graph: `neighbor_indices` remains sklearn brute-force for Wu & Schölkopf local regression only.

Check:

```bash
python3 -m pytest tests/test_shared_spectral_embedding.py baselines/spectral_clustering/test_spectral_clustering.py tests/test_ssc.py tests/test_repair_round1_math.py tests/test_mutual_knn.py -q
```

## Why Does Our ORL Spectral Clustering Differ From the Original SSC Paper?

Chang et al. (AAAI 2015, Table 1) report ORL spectral clustering ACC **72.7±2.3** (NMI 85.8±1.9). Those numbers are theirs, not ours.

### What we actually measured

Historical Phase 1, Olivetti 64×64→32×32, sklearn-NN graph, 50 random K-means seeds, `n_init=1`:

- ACC **54.2±3.1**, NMI **76.5±1.6**, \(n=50\)
- Runs: `20261020_015207__TRACKA__SC__ORL__a86c9d70` and `20261020_015621__TRACKB__SC__ORL__263aa38a` (both `acc_mean=0.54215`, backend `baselines.spectral`)

Round 2, **shared Eq. (4) path** (same `SpectralGraphConfig` as SSC; sign convention `largest_magnitude_positive`):

| Setting | Identity | \(n\) | ACC | NMI | Graph | Run |
| --- | --- | --- | --- | --- | --- | --- |
| Olivetti, union, median directed \(\delta^2\), random KM | **not** original-source | 50 | 53.9±3.0 | 76.5±1.7 | 1329 edges, 2 CC, \(\delta^2=7.09\) | `20261021_161536__ROUND2__ORL__D01_OLIVETTI_SC__9118018b` |
| att92 92×112→32×32 bilinear, same SC config | original-source reconstruction | 50 | 56.2±4.2 | 80.5±2.3 | 1273 edges, 3 CC, \(\delta^2=9.34\) | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |

SC \(F\) equals SSC \(F\) on both versions (`results/round2/d2_shared_f.json`, max abs diff 0). Git HEAD `f9c381487d8a4915f35c2eadb638b5f28d830b11`; numbers are from a dirty tree.

### Quantified one-factor effects (att92 unless noted)

All of these keep \(k=5\) and Eq. (4). Invalid / Category C settings did not get 50 trials.

| Factor | Category | Effect on ACC | Evidence |
| --- | --- | --- | --- |
| Unified \(F\) vs Phase 1 sklearn-NN | A | Olivetti 54.2 → 53.9 (−0.3 pp) | historical vs `…D01_OLIVETTI_SC__9118018b` |
| att92 vs Olivetti | A vs approximate source | +2.3 pp | two \(n=50\) SC runs above |
| Mean vs median directed bandwidth | B | ~0 pp at \(n=5\) (54.6 vs 54.6 on seeds 0–4) | `…D03_BW_MEAN_SC__8f25437b` |
| Undirected-edge median bandwidth | B | +1.0 pp at \(n=5\) (55.6) | `…D03_BW_UNDIRECTED_MEDIAN_SC__96ae6849` |
| Mutual symmetrization | C | −5.0 pp at \(n=5\); 46 CC / 727 edges | `…D04_MUTUAL_SC__64f5f71e` |
| Row-normalize eigenvectors | C | +11 pp at \(n=5\) (67.7±3.1) | `…D06_ROW_NORM_SC__c17f11c3` |
| E8 shrinkage vs K-means(\(F\)) | A | +1.1 pp (57.3 vs 56.2, \(n=50\)) | `…D08_E8_ATT92__d3809fd0` |
| E13 vs E8 | B vs A | −0.6 pp (56.7 vs 57.3) | `…D08_E13_ATT92__a9ac25d0` |
| 50 random KM, best **inertia** (not ACC) | A protocol, extra column | 62.3 ACC at seed 21 | `results/round2/d10_d11_kmeans_on_saved_f.json` |
| 50 k-means++ on saved \(F\) | **B** | **78.3±1.3** (best inertia ACC 79.0) | same file, att92 SC/E8 \(F\) |

k-means++ on att92 \(F\) exceeds the paper’s 72.7 and even 76.0. That is **not** a reproduction. The paper’s written protocol is random initialization with mean±std. We do not promote ++ or row-norm into a faithful table.

### Remaining gap vs 72.7 / 76.0

Faithful protocol (att92, Eq. (4), union, median directed bandwidth, raw \(F\), random KM, \(n=50\)):

- vs published **SC 72.7**: **−16.5 pp** (we have 56.2)
- vs published **SSC 76.0**: **−18.7 pp** on E8 \(G\) (we have 57.3); SC/K-means(\(F\)) is already 56.2, so IRLS is not the missing 19 points

The earliest verified stage of the ORL SC gap is **K-means on \(F\)**, not the shrinkage solver. Unified \(F\) did not close it. att92 recovered a few points. The large ++ lift shows that this \(F\) is clusterable, but switching the initializer is an ambiguity, not a proof that Chang et al. used k-means++.

Confidence: **high** that the gap is present before IRLS and that source/bandwidth/E8–E13 are small relative to 16–19 pp; **high** that k-means++ and row-norm move ACC a lot and must stay labeled B/C; **unresolved** which unpublished choice produced 72.7.

Full matrix: `docs/round2_reproduction_matrix.md`. Causal labels: `docs/round2_root_cause_analysis.md`.
