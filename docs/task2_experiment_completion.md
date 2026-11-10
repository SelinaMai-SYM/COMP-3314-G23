> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Task 2: Which published experiments were scientifically reproduced?

**None met the full protocol.** No cell among the 72 method-by-dataset entries in Chang et al. (AAAI 2015), Tables 1–2, met the complete published protocol (eight datasets, 50 random clustering trials per cell, unreleased preprocessing, and the unresolved SPLS / AR / MSRA50 / UMIST-564 / paper BinAlpha inputs).

The following cells count as **partial scientific execution**, rather than full paper reproduction: the method was faithfully reimplemented and the data used the declared reconstructed versions (ORL `att92`, JAFFE Zenodo, YaleB `cropped2414`, USPS LIBSVM); numbers came from actual trials in `runs/strict_repro/`. Gamma, dimension, and seeds were **not selected using ACC**. SC and SSC shared `SpectralGraphConfig`. LDA-SC was APPROXIMATE and excluded from faithful execution of the 72 cells. SPLS was BLOCKED_METHOD. E13 was recorded separately and did not replace E8 based on ACC.

Status of the 72 cells: `{"BLOCKED_DATA": 32, "completed": 30, "NOT_REPRODUCED": 2, "BLOCKED_METHOD": 8}`。Faithful execution completed 28 cells (7 methods x 4 loadable datasets). ORL/JAFFE had n=50; YaleB had n=10 and USPS n=3 or 5. Their protocol statuses explicitly stated that these were not the paper's 50 trials; no extrapolation was made.

## Partial scientific execution (actual logs)

### n=50 (ORL att92 and JAFFE Zenodo)

- K-means × JAFFE: ACC 73.2 ± 5.7 (n=50); NMI 83.1 ± 3.5 (n=50); -2.4 pp vs historical paper mean; `20261021_170320__STRICT_REPRO__JAFFE__KMEANS__8776ae41`
- K-means × ORL: ACC 61.5 ± 2.9 (n=50); NMI 82.8 ± 1.2 (n=50); +1.0 pp vs historical paper mean; `20261021_170315__STRICT_REPRO__ORL__KMEANS__4b8ea2b1`
- SC × JAFFE: ACC 68.5 ± 11.2 (n=50); NMI 83.0 ± 5.7 (n=50); -7.6 pp vs historical paper mean; `20261021_170322__STRICT_REPRO__JAFFE__SC_EQ4__91b67b99`
- SC × ORL: ACC 56.2 ± 4.2 (n=50); NMI 80.5 ± 2.3 (n=50); -16.5 pp vs historical paper mean; `20261021_170316__STRICT_REPRO__ORL__SC_EQ4__19517850`
- PCA-KM × JAFFE: ACC 74.8 ± 7.7 (n=50); NMI 83.1 ± 4.5 (n=50); -1.0 pp vs historical paper mean; `20261021_171014__STRICT_REPRO__JAFFE__PCAKM_D10__0e3cf840`
- PCA-KM × ORL: ACC 63.1 ± 3.3 (n=50); NMI 83.6 ± 1.2 (n=50); -1.4 pp vs historical paper mean; `20261021_170921__STRICT_REPRO__ORL__PCAKM_D40__b91fcfbc`
- PCA-SC × JAFFE: ACC 59.3 ± 7.7 (n=50); NMI 72.2 ± 4.7 (n=50); -17.6 pp vs historical paper mean; `20261021_171016__STRICT_REPRO__JAFFE__PCASC_D10__09a8767f`
- PCA-SC × ORL: ACC 55.4 ± 4.3 (n=50); NMI 80.6 ± 2.2 (n=50); -12.4 pp vs historical paper mean; `20261021_170924__STRICT_REPRO__ORL__PCASC_D40__fe3572e1`
- LDA-KM × JAFFE: ACC 64.4 ± 9.2 (n=50); NMI 78.6 ± 5.1 (n=50); -12.1 pp vs historical paper mean; `20261021_171017__STRICT_REPRO__JAFFE__LDAKM_D9__0e99bdae`
- LDA-KM × ORL: ACC 56.3 ± 4.1 (n=50); NMI 81.0 ± 1.7 (n=50); -9.3 pp vs historical paper mean; `20261021_170927__STRICT_REPRO__ORL__LDAKM_D39__94edb79b`
- LLC × JAFFE: ACC 88.4 ± 6.9 (n=50); NMI 91.2 ± 2.7 (n=50); +9.8 pp vs historical paper mean; `20261021_171027__STRICT_REPRO__JAFFE__LLC__aef43932`
- LLC × ORL: ACC 77.9 ± 2.0 (n=50); NMI 88.6 ± 0.8 (n=50); +6.4 pp vs historical paper mean; `20261021_171013__STRICT_REPRO__ORL__LLC__127454d2`
- SSC E8 × JAFFE: ACC 68.4 ± 11.1 (n=50); NMI 83.0 ± 5.7 (n=50); -12.8 pp vs historical paper mean; `20261021_170323__STRICT_REPRO__JAFFE__SSC_E8_G1__2d4a870b`
- SSC E8 × ORL: ACC 57.3 ± 3.8 (n=50); NMI 81.1 ± 2.2 (n=50); -18.7 pp vs historical paper mean; `20261021_170317__STRICT_REPRO__ORL__SSC_E8_G1__68341141`

### Budget-limited (YaleB n=10; USPS n=3 or 5)

- K-means × YaleB: ACC 9.1 ± 0.5 (n=10); NMI 12.4 ± 0.7 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_170325__STRICT_REPRO__YALEB__KMEANS__ab478656`
- K-means × USPS: ACC 66.4 ± 0.5 (n=5); NMI 60.9 ± 0.3 (n=5); budget_limited_n=5_paper_protocol_is_50; `20261021_170410__STRICT_REPRO__USPS__KMEANS__efa8d62b`
- SC × YaleB: ACC 18.1 ± 1.3 (n=10); NMI 26.6 ± 0.6 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_170327__STRICT_REPRO__YALEB__SC_EQ4__f8323013`
- SC × USPS: ACC 63.9 ± 1.7 (n=5); NMI 76.1 ± 3.6 (n=5); budget_limited_n=5_paper_protocol_is_50; `20261021_170412__STRICT_REPRO__USPS__SC_EQ4__19529e79`
- PCA-KM × YaleB: ACC 9.0 ± 0.5 (n=10); NMI 12.2 ± 0.5 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171028__STRICT_REPRO__YALEB__PCAKM_D38__31f464c2`
- PCA-KM × USPS: ACC 65.7 ± 1.8 (n=3); NMI 59.8 ± 0.4 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171120__STRICT_REPRO__USPS__PCAKM_D10__31bc23ed`
- PCA-SC × YaleB: ACC 16.2 ± 0.6 (n=10); NMI 23.3 ± 1.0 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171032__STRICT_REPRO__YALEB__PCASC_D38__2debde8e`
- PCA-SC × USPS: ACC 56.9 ± 2.1 (n=3); NMI 65.0 ± 1.2 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171122__STRICT_REPRO__USPS__PCASC_D10__ef12dd83`
- LDA-KM × YaleB: ACC 9.6 ± 0.8 (n=10); NMI 13.5 ± 1.3 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171037__STRICT_REPRO__YALEB__LDAKM_D37__ab5c8123`
- LDA-KM × USPS: ACC 52.9 ± 2.1 (n=3); NMI 57.4 ± 4.8 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171127__STRICT_REPRO__USPS__LDAKM_D9__4e9e3c66`
- LLC × YaleB: ACC 25.7 ± 1.1 (n=10); NMI 32.9 ± 0.7 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171117__STRICT_REPRO__YALEB__LLC__3fe07e59`
- LLC × USPS: ACC 58.3 ± 2.7 (n=3); NMI 66.2 ± 2.5 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171131__STRICT_REPRO__USPS__LLC__f27a8b6a`
- SSC E8 × YaleB: ACC 17.4 ± 1.1 (n=10); NMI 26.0 ± 1.1 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_170328__STRICT_REPRO__YALEB__SSC_E8_G1__333d3583`
- SSC E8 × USPS: ACC 62.1 ± 3.8 (n=5); NMI 75.4 ± 3.0 (n=5); budget_limited_n=5_paper_protocol_is_50; `20261021_170415__STRICT_REPRO__USPS__SSC_E8_G1__e36daae7`

## Why this still did not reproduce the paper protocol

- The paper required 50 random clustering trials per dataset. YaleB had n=10 and USPS n<=5. INCOMPLETE reports actual n and never substitutes 50.
- ORL `att92` was resized from the original AT&T 92x112 package to 32x32. Bilinear interpolation was an assumption; this was not Olivetti and was not claimed PAPER_PROTOCOL_MATCHED.
- JAFFE used the verified Zenodo archive, not the paper's unreleased preprocessed copy.
- YaleB `cropped2414` matched the count of 2414, without claiming pixel identity with Deng Cai's `YaleB_32x32.mat`.
- The PCA grid `{10,20,...,150}` was an assumption. The matrix used the predetermined dimension min(50,K,n-1,d), **not the grid's highest ACC**.
- LDA rank is <=K-1 (Ding and Li), so its grid cannot reach 150.
- The SSC gamma grid `{1e-6,1e-3,1,1e3,1e6}` was recorded. The matrix used predetermined gamma=1. Gamma was not chosen by ACC, and raw Equation (8) objectives were not compared across gamma. Unconverged IRLS remained labelled unconverged.
- Historical Track A / Round 2 measurements were not copied into this matrix.
- LDA-SC ran on ORL/JAFFE (n=10), labelled APPROXIMATE and excluded from faithful reproduction. YaleB/USPS LDA-SC remained NOT_REPRODUCED (optional approximate cells, not run).

## Blockers

- SPLS: Section 3 not obtained; `baselines/spls/spls.py` raises NotImplementedError; no substitute shrinking.
- AR: official host unavailable; unofficial Zenodo dump not used; 840/120 subset not invented.
- MSRA50: no 1799×12×1024 archive; other MSRA corpora not renamed.
- UMIST 564: not obtained. precropped575 (n=575, 565 unique pixels) is extra, labeled not-564.
- Paper BinAlpha 26×30: not identified. letters26x30_seed0 is UNVERIFIED reconstruction only.
- Shared F mismatch: max_abs_diff=0.0.

## Shared F

SC F must equal SSC F under the same `SpectralGraphConfig`. The saved `embedding_F.npy` comparisons for ORL att92 and the other reconstructed datasets appear below.

```json
{
  "note": "SC F must equal SSC F under the same SpectralGraphConfig. Compared from saved embedding_F.npy.",
  "pairs": {
    "ORL:att92": {
      "sc_run": "20261021_170316__STRICT_REPRO__ORL__SC_EQ4__19517850",
      "e8_run": "20261021_170317__STRICT_REPRO__ORL__SSC_E8_G1__68341141",
      "status": "compared",
      "equal_exact": true,
      "equal_atol_1e-12": true,
      "max_abs_diff": 0.0,
      "shape": [
        400,
        40
      ]
    },
    "JAFFE:zenodo": {
      "sc_run": "20261021_170322__STRICT_REPRO__JAFFE__SC_EQ4__91b67b99",
      "e8_run": "20261021_170323__STRICT_REPRO__JAFFE__SSC_E8_G1__2d4a870b",
      "status": "compared",
      "equal_exact": true,
      "equal_atol_1e-12": true,
      "max_abs_diff": 0.0,
      "shape": [
        213,
        10
      ]
    },
    "YaleB:cropped2414": {
      "sc_run": "20261021_170327__STRICT_REPRO__YALEB__SC_EQ4__f8323013",
      "e8_run": "20261021_170328__STRICT_REPRO__YALEB__SSC_E8_G1__333d3583",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 1.3292839051715077e-13,
      "shape": [
        2414,
        38
      ]
    },
    "USPS:libsvm": {
      "sc_run": "20261021_170412__STRICT_REPRO__USPS__SC_EQ4__19529e79",
      "e8_run": "20261021_170415__STRICT_REPRO__USPS__SSC_E8_G1__e36daae7",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 4.5102810375396984e-15,
      "shape": [
        9298,
        10
      ]
    }
  },
  "sc_run": "20261021_170316__STRICT_REPRO__ORL__SC_EQ4__19517850",
  "e8_run": "20261021_170317__STRICT_REPRO__ORL__SSC_E8_G1__68341141",
  "status": "compared",
  "equal_exact": true,
  "equal_atol_1e-12": true,
  "max_abs_diff": 0.0,
  "shape": [
    400,
    40
  ],
  "all_equal_atol_1e-12": true
}
```

Outputs: `results/reproduction_full_matrix.csv`, `results/reproduction_full_matrix.md`, `results/strict_repro/`, `runs/strict_repro/`.
No Git commit or push was made at that stage.

