# Report evidence map

Every numeric claim in `report/main.tex` (including `report/tables/final_main.tex`) is listed here with source, run ID, checksum when recorded, and aggregation. Paper table entries and paper dataset counts are historical quotations from Chang et al. (2015), not our measurements. Round 2 report numbers are not reused when they disagree with these files.

Primary protocol: E8, γ = 1, random Lloyd, n_init = 1, seeds 0..49, one F and one G. ACC = Hungarian (`benchmarks.metrics.clustering_accuracy`). NMI = Strehl–Ghosh geometric mean. Sample SD uses ddof = 1.

Section numbers below match the six-section rewrite (problem → methods → paper experiments → critique → extension → reproduction). Percent cells in Table 1 match `results/strict_reproduction_matrix.csv` display strings (one decimal). Fraction cells match `docs/final_round/E1_analysis.md`, `E3_analysis.md`, `E4_analysis.md`, and `scientific_findings.md`, which round the CSVs without extra invented digits.

## Main table (Table 1, Section 6): paper SC/SSC vs our SC and E8 γ = 1

Aggregation for Our cells: mean ± sample SD over n = 50 random K-means trials on one embedding. Seeds exactly `[0, 1, …, 49]` (`docs/final_round/E6_analysis.md`; `results/final_round/E6_validation.json`, 52 cells, 0 problems).

| Report cell | Report string | Source | Run ID | Checksum / identity | Aggregation |
| --- | --- | --- | --- | --- | --- |
| ORL Paper SC ACC | 72.7 ± 2.3 | Chang et al. Table 1, quoted in matrix as historical only | n/a (not a run) | n/a | Reported in Chang et al. (2015) |
| ORL Our SC ACC | 56.2 ± 4.2 | `results/strict_reproduction_matrix.csv` SC ORL att92; fraction `acc_mean=0.5618` in `E1_summary.csv` F random | `20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce` | att92 SHA-256 `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | mean±sd n=50 on F |
| ORL Paper SSC ACC | 76.0 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| ORL Our E8 ACC | 57.3 ± 3.8 | matrix SSC E8 ORL; `E1_summary.csv` G random `0.57265 ± 0.03797` | `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41` | same att92 checksum | mean±sd n=50 on G |
| ORL Paper SC NMI | 85.8 ± 1.9 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| ORL Our SC NMI | 80.5 ± 2.3 | matrix; `E1_summary.csv` F `nmi_mean=0.804705 ± 0.022914` | `20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce` | att92 checksum above | mean±sd n=50 on F |
| ORL Paper SSC NMI | 88.6 ± 1.5 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| ORL Our E8 NMI | 81.1 ± 2.2 | matrix; `E1_summary.csv` G `0.811312 ± 0.021562` | `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41` | att92 checksum above | mean±sd n=50 on G |
| JAFFE Paper SC ACC | 76.1 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| JAFFE Our SC ACC | 68.5 ± 11.2 | matrix; `E1_summary.csv` F `0.685258 ± 0.111516` | `20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b` | zenodo SHA-256 `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | mean±sd n=50 on F |
| JAFFE Paper SSC ACC | 81.2 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| JAFFE Our E8 ACC | 68.4 ± 11.1 | matrix; `E1_summary.csv` G `0.684319 ± 0.110806` | `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d` | same zenodo checksum | mean±sd n=50 on G |
| JAFFE Paper SC NMI | 80.2 ± 0.9 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| JAFFE Our SC NMI | 83.0 ± 5.7 | matrix; `E1_summary.csv` F `0.830162 ± 0.057236` | `20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b` | zenodo checksum above | mean±sd n=50 on F |
| JAFFE Paper SSC NMI | 84.3 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| JAFFE Our E8 NMI | 83.0 ± 5.7 | matrix; `E1_summary.csv` G `0.830490 ± 0.057207` | `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d` | zenodo checksum above | mean±sd n=50 on G |
| YaleB Paper SC ACC | 34.8 ± 1.4 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| YaleB Our SC ACC | 18.3 ± 1.3 | matrix cropped2414; `E1_summary.csv` F `0.183397 ± 0.012841` | `20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51` | cropped zip SHA-256 `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | mean±sd n=50 on F |
| YaleB Paper SSC ACC | 49.8 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| YaleB Our E8 ACC | 17.6 ± 1.2 | matrix; `E1_summary.csv` G `0.176222 ± 0.011873` | `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff` | same cropped checksum | mean±sd n=50 on G |
| YaleB Paper SC NMI | 55.6 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| YaleB Our SC NMI | 26.9 ± 0.7 | matrix; `E1_summary.csv` F `0.269030 ± 0.006723` | `20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51` | cropped checksum above | mean±sd n=50 on F |
| YaleB Paper SSC NMI | 46.8 ± 1.3 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| YaleB Our E8 NMI | 26.2 ± 0.9 | matrix; `E1_summary.csv` G `0.261781 ± 0.008978` | `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff` | cropped checksum above | mean±sd n=50 on G |
| USPS Paper SC ACC | 64.3 ± 1.4 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| USPS Our SC ACC | 61.7 ± 8.1 | matrix; `E1_summary.csv` F `0.617389 ± 0.080858` | `20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055` | `usps.bz2=3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f`; `usps.t.bz2=a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | mean±sd n=50 on F |
| USPS Paper SSC ACC | 75.5 ± 1.9 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| USPS Our E8 ACC | 61.7 ± 8.1 | matrix; `E1_summary.csv` G `0.616982 ± 0.080893` | `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b` | same LIBSVM checksums | mean±sd n=50 on G |
| USPS Paper SC NMI | 69.5 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| USPS Our SC NMI | 74.9 ± 4.5 | matrix; `E1_summary.csv` F `0.749399 ± 0.044941` | `20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055` | LIBSVM checksums above | mean±sd n=50 on F |
| USPS Paper SSC NMI | 79.8 ± 1.6 | Chang et al. Table 1, historical only | n/a | n/a | Reported in Chang et al. (2015) |
| USPS Our E8 NMI | 75.2 ± 4.6 | matrix; `E1_summary.csv` G `0.752293 ± 0.045582` | `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b` | LIBSVM checksums above | mean±sd n=50 on G |

Table footnote dataset sizes: JAFFE 213, YaleB 2414/38, USPS 9298 — paper counts matched in `docs/final_round/scientific_findings.md` Q2 and the matrix identity columns. ORL is 400 AT&T images (att92), not claimed pixel-matched to 2015.

The same four paper ACC pairs are also quoted in Section 3 as *Reported in Chang et al. (2015)* (ORL 76.0±1.6 vs 72.7±2.3; JAFFE 81.2±1.6 vs 76.1±1.6; YaleB 49.8±1.6 vs 34.8±1.4; USPS 75.5±1.9 vs 64.3±1.4).

## Paper-only dataset counts and protocol (Section 3)

All of the following are *Reported in Chang et al. (2015)* (experimental section), not our measurements.

| Claim | Source |
| --- | --- |
| AR 840 faces, 120 people | Chang et al. 2015, Datasets |
| JAFFE 213 images, 10 subjects, 26×26 | Chang et al. 2015, Datasets; count also matched in matrix / scientific_findings Q2 |
| ORL 40 subjects, 10 images, 32×32 | Chang et al. 2015, Datasets |
| UMIST 564 images, 20 people | Chang et al. 2015, Datasets |
| BinAlpha 26 letters, 30 images each | Chang et al. 2015, Datasets |
| MSRA50 1799 images, 12 classes, 32×32 | Chang et al. 2015, Datasets |
| YaleB 2414 images, 38 people, 32×32 | Chang et al. 2015, Datasets; `E4_data_comparison.csv` both versions `n_images=2414`, `n_identities=38` |
| USPS 9298 digits, 16×16 | Chang et al. 2015, Datasets; matrix identity `verified_libsvm_9298` |
| Spectral k = 5; γ grid {1e-6, 1e-3, 1, 1e3, 1e6}; 50 random inits, best objective; Tables 1–2 print mean±std | Chang et al. 2015, Setup; grid also in `E2_shrinkage.csv` / preflight |
| Fig. 1 prefers γ = 1 except MSRA50/USPS; Fig. 2 objective decreases quickly | Chang et al. 2015, Parameter Sensitivity / Convergence Study; `docs/final_round/E5_figure_audit.md` |

## CVXPY small-graph (Section 4)

| Report number | Source | Run / test | Aggregation |
| --- | --- | --- | --- |
| n = 6 chain, printed γ | `results/final_round/E3_optimization.csv` rows `small_graph_cvxpy`; `E3_analysis.md` | `tests/test_ssc.py::test_equation13_fixed_point_matches_cvxpy_halved_graph_term` (re-run; pytest return code 0 in `E3_pytest_cvxpy.txt`) | one synthetic instance; CLARABEL status optimal |
| E8 max \|G\| gap 1.17e-5 | E3 CSV `max_abs_G_gap=1.172106445274101e-05` | same test | max absolute entrywise gap vs CVXPY at printed γ |
| E13 max \|G\| gap 2.33e-5 | E3 CSV `2.326988690209975e-05` | same test | vs CVXPY with graph coefficient γ/2 |
| Relative step stop 1e-6; IRLS cap 300 | `docs/final_round_preflight.md` protocol; run configs | all strict_paper SSC cells | solver setting, not a metric |

## Mutual-kNN extension (Section 5)

Existing Round 2 runs. Algorithm in `method_extension/` was not changed. Category C.

| Report string | Source | Run ID |
| --- | --- | --- |
| mutual E8 ACC 68.4 ± 11.2 | `runs/round2/…EXT_JAFFE_MUTUAL_KNN…/metrics.json` `acc_mean=0.683662`, `acc_std=0.111576`; README | `20261021_161924__ROUND2__JAFFE__EXT_JAFFE_MUTUAL_KNN__45fd1c1f` |
| union E8 ACC 68.4 ± 11.1 | `runs/round2/…D12_JAFFE_E8…/metrics.json` `acc_mean=0.684319`, `acc_std=0.110806` (same mean as strict JAFFE E8) | `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` |
| 410 vs 655 edges; 20 vs 9 components | mutual `n_undirected_edges=410`, `n_connected_components=20`; union `655`, `9` | same two runs; E2 JAFFE W also 655 / 9 |

JAFFE checksum on the extension run: `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`. n = 50.

## E1 paired ΔACC (Section 6)

Source: `results/final_round/E1_paired.csv` aggregate rows; `docs/final_round/E1_analysis.md`. Cache embeddings: the four E8 γ = 1 runs in the main-table SSC column. Same seeds 0..49. Δ = ACC(G) − ACC(F). 95% percentile bootstrap, 10,000 resamples, CI scope = K-means noise on this fixed (F, G) only.

| Dataset | Init | Report ΔACC | Report 95% CI | CSV mean / CI | CI excludes 0 | Cache run |
| --- | --- | --- | --- | --- | --- | --- |
| ORL | random | +0.0109 | [+0.0030, +0.0187] | 0.01085 / [0.003, 0.01865] | yes | `…ORL__SSC_E8_G1P0__4be5ba41` |
| JAFFE | random | −0.0009 | contains 0; CSV [−0.01070, 0.00892] | −0.000939 | no | `…JAFFE__SSC_E8_G1P0__8a4a026d` |
| YaleB | random | −0.0072 | [−0.0097, −0.0048] | −0.007175 / [−0.009652, −0.004789] | yes (negative) | `…YALEB__SSC_E8_G1P0__2ba528ff` |
| USPS | random | −0.0004 | contains 0; CSV [−0.00684, 0.00578] | −0.000407 | no | `…USPS__SSC_E8_G1P0__0a34012b` |

Prose “about one percentage point” is the rounding of ORL +0.0109.

## E4 YaleB versions (Section 6)

Source: `results/final_round/E4_data_comparison.csv`, `E4_graph_diagnostics.csv`, `docs/final_round/E4_analysis.md`.

| Report claim | CSV / analysis | Checksum |
| --- | --- | --- |
| Both 2414 × 1024, 38 classes, pixels [0, 1] | `n_images=2414`, `feature_dim=1024`, `n_identities=38`, `float_min=0`, `float_max=1` | Deng Cai mat `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99`; cropped zip `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` |
| Same per-class counts | `per_identity_count_vectors_equal=true`; min 59 max 64 | — |
| Best alignment transpose; median L2 1.92 | `best_orientation=transpose`, `median_matched_image_l2=1.922164770437778` | bilinear match row |
| Zero images coincide at 1e-8 | `fraction_matched_maxabs_le_1e-8=0` | same row |
| K-means(F) cropped 0.1834 | `E4_graph_diagnostics.csv` controlled cropped2414 `acc_mean=0.18339685 ± 0.012841`, n = 50 | matches strict SC F (max abs 4.2e-14) |
| K-means(F) Deng Cai 0.2016 | controlled dengcai32 `acc_mean=0.20159072 ± 0.012388`, n = 50, same graph rule and seeds | not selected by ACC |
| Published SC 34.8% | Chang et al. Table 1, historical only | n/a |

## Dataset / protocol facts in Section 6

| Claim | Source |
| --- | --- |
| JAFFE 213; YaleB 2414 / 38; USPS 9298 | matrix / JAFFE manifest; `E4_data_comparison.csv`; scientific_findings Q2 |
| UMIST 565 unique cropped, not 564 | prior dataset audit in `report/main.tex` Round 2 and `docs/final_round_preflight.md` (blocked; not re-counted this round) |
| n = 50 seeds 0..49 on one F (and one G) | `E6_validation.json` `kmeans_only_randomness`; 52 cells, `n_problems=0` |
| ACC Hungarian; NMI geometric | `E6_analysis.md`; pytest 16 passed, return code 0 (`E6_pytest.txt`) |
| ± is sample SD ddof = 1 | `E6_validation.json` `std_convention`; `E1_summary.csv` `std_convention` |
| IRLS budget 300; γ = 1 frozen; G0 = F | `docs/final_round_preflight.md` protocol; all strict_paper SSC cells |

## Explicitly not in the report as Our Reproduction

- Round 2 YaleB Deng Cai n = 10 (SC 20.1, E8 19.5) and USPS n = 3 (SC 63.8, E8 60.7).
- SPLS (matrix status `BLOCKED_MISSING_FULL_METHOD`).
- LDA-SC (`APPROXIMATE`).
- AR, UMIST-564, MSRA50 (blocked; not filled as EXACT).
- BinAlpha `CANDIDATE_BIN_ALPHA` (not a paper identity; omitted from Table 1).
- k-means++ and row-norm ACC as the paper method.
- E2 γ-grid ACC values and E3 IRLS-continuation ACC (not printed in this rewrite).
- Any claim that maximizing ACC identifies the 2015 protocol.
