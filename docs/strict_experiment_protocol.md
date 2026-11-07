# Strict Chang 2015 experiment protocol

Paper: Chang, Nie, Wang, Yang, *Spectral Shrunk Clustering*, AAAI 2015 Setup.
Code root: `v1/`. Config: `configs/strict_paper_reproduction.yaml`.
Runs: `runs/strict_paper/`. Matrix: `results/strict_reproduction_matrix.csv`.
This campaign does **not** overwrite `runs/strict_repro/`, `report/`, or `method_extension/`.

## Campaign outcome (real logs only)

- **n=50 main cells: 80** (ORL att92, JAFFE zenodo, CANDIDATE_BIN_ALPHA, YaleB cropped2414, USPS libsvm × K1/SC/PCA-KM/PCA-SC/LDA-KM/LLC + SSC E8×5γ + SSC E13×5γ).
- **Gamma grids finished:** SSC E8 and E13, all five γ ∈ {1e-6, 1e-3, 1, 1e3, 1e6}, n=50, on those five datasets. F,G solved once per (dataset, variant, γ); raw Eq.8 objectives were **not** compared across γ.
- **AR paper cells are not EXACT.** Third-party Zenodo zip (MD5 `bb97bd9237680744c0c7268624696263`, 100 identities s1–s100) is `SOURCE_RECOVERED_SUBSET_UNVERIFIED`, not official Martinez, not 840/120. Loader still returns no arrays; no clustering diagnostic was run.
- **BinAlpha** is `CANDIDATE_BIN_ALPHA` (seed 0, 780×320). Default `load_dataset('BinAlpha')` remains unavailable. Not historical identity.
- **UMIST 564** still missing (575 files / 565 unique) → `BLOCKED_DATA`.
- **MSRA50** → `BLOCKED_DATA_NOT_OBTAINED`.
- **SPLS** → `BLOCKED_MISSING_FULL_METHOD`.
- **LDA-SC** is APPROXIMATE (ORL/JAFFE/BinAlpha n=10) and is not a faithful table cell.
- Extra dim-grid and LDA-SC rows keep their actual n (5 / 10 / 1) and are not counted as paper-protocol n=50. Main protocol cells have **zero** INCOMPLETE.
- Shared F: SC F == SSC F at atol 1e-12 on all compared datasets.

## Paper → code → config → run IDs

| Paper setting | Code | Config | Typical factors / run IDs |
| --- | --- | --- | --- |
| k=5 neighborhood | `SSC_method.spectral_config.SpectralGraphConfig.k` | `params.k: 5` | SC_EQ4, SSC_E8_*, SSC_E13_* |
| Eq. (4) SC embedding F | `experiments.methods.prepare_spectral` + `SSC_method.spectral_embedding` | `laplacian: symmetric_normalized_eq4` | SC_EQ4 |
| SSC Eq. (8) / E8 | `SSC_method.optimizer.shrink_embedding` variant E8 | `params.variant: E8` | SSC_E8_G1em6 … G1e6 |
| Printed Eq. (13) / E13 | same optimizer, `variant=E13` | `params.variant: E13` | SSC_E13_G*; **separate column** |
| γ ∈ {1e-6, 1e-3, 1, 1e3, 1e6} | `params.gamma` | `gamma_grid` in YAML | one F,G solve per γ, then k-means trials |
| ACC Hungarian | `benchmarks.metrics.clustering_accuracy` | `acc: hungarian` | evaluation only |
| NMI geometric | `benchmarks.metrics.normalized_mutual_information` | `nmi: geometric` | evaluation only |
| 50 random clusterings | `scripts/run_experiment.py` n_trials | `n_trials_paper: 50` | K1_RANDOM_MEAN, SC_EQ4, SSC_* |
| K-means random mean (K1) | `baselines.kmeans` / `_kmeans_labels` init=random | `params.init: random` | K1_RANDOM_MEAN |
| Best inertia (K2) | derived from K1 trials | not a separate fit | extra column |
| k-means++ mean/best (K3/K4) | init=`k-means++` | `params.init: k-means++` | K3_KMEANSPP_MEAN; K4 derived |
| Dim {10,…,150} ASSUMPTION | `experiments.protocol.dimension_grid` | `dim_grid.status: ASSUMPTION` | PCAKM_GRID_D*, PCASC/PCAKM main at Track-B dim |
| LDA rank ≤ K−1 | `baselines.lda_kmeans` | `n_components: K-1` | LDAKM_D{K-1} |
| No sklearn SpectralClustering | `baselines.spectral_clustering` docstring + shared F path | `no_sklearn_SpectralClustering: true` | SC / PCA-SC / SSC |
| ORL att92 | `benchmarks.orl` version att92 | `dataset_version: att92` | see matrix |
| JAFFE Zenodo | `benchmarks.jaffe` version zenodo | `dataset_version: zenodo` | see matrix |
| YaleB cropped2414 | `benchmarks.yaleb` version cropped2414 | `dataset_version: cropped2414` | see matrix |
| USPS LIBSVM | `benchmarks.usps` | `dataset_version: libsvm` | see matrix |
| BinAlpha candidate | `benchmarks.binalpha` version=`CANDIDATE_BIN_ALPHA` (alias letters26x30_seed0) | seed 0, 780×320, not historical identity | default load_dataset('BinAlpha') still unavailable |
| AR 840/120 | not recovered; third-party Zenodo zip is 100 identities | `SOURCE_RECOVERED_SUBSET_UNVERIFIED` | paper cell is **not EXACT**; no official Martinez set |
| UMIST 564 | 575 files / 565 unique; paper 564 missing | BLOCKED_DATA | not used as paper UMIST |
| MSRA50 | no 1799×12 archive | BLOCKED_DATA_NOT_OBTAINED | |
| SPLS | `baselines.spls.fit_predict` | BLOCKED_MISSING_FULL_METHOD | SPLS_NOT_IMPLEMENTED |
| LDA-SC | `baselines.lda_spectral` | APPROXIMATE | LDASC_D*; not faithful table |

## Loader probe at campaign start

```json
{
  "ORL": {
    "dataset": "ORL",
    "dataset_version": "att92",
    "status": "AVAILABLE",
    "n": 400,
    "d": 1024,
    "n_clusters": 40,
    "checksum": "509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec",
    "identity": "obtained",
    "verification_status": "obtained",
    "wall_seconds": 0.1104108327999711
  },
  "JAFFE": {
    "dataset": "JAFFE",
    "dataset_version": "zenodo",
    "status": "AVAILABLE",
    "n": 213,
    "d": 676,
    "n_clusters": 10,
    "checksum": "6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b",
    "identity": "verified",
    "verification_status": "verified",
    "wall_seconds": 0.21262016566470265
  },
  "YaleB": {
    "dataset": "YaleB",
    "dataset_version": "cropped2414",
    "status": "AVAILABLE",
    "n": 2414,
    "d": 1024,
    "n_clusters": 38,
    "checksum": "8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573",
    "identity": "obtained",
    "verification_status": "obtained",
    "wall_seconds": 0.004609375260770321
  },
  "USPS": {
    "dataset": "USPS",
    "dataset_version": "libsvm",
    "status": "AVAILABLE",
    "n": 9298,
    "d": 256,
    "n_clusters": 10,
    "checksum": {
      "usps.bz2": "3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f",
      "usps.t.bz2": "a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e"
    },
    "identity": "verified",
    "verification_status": "verified",
    "wall_seconds": 1.2601168337278068
  },
  "BinAlpha": {
    "dataset": "BinAlpha",
    "dataset_version": "CANDIDATE_BIN_ALPHA",
    "status": "AVAILABLE",
    "n": 780,
    "d": 320,
    "n_clusters": 26,
    "checksum": "3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7",
    "identity": "CANDIDATE_BIN_ALPHA",
    "verification_status": "CANDIDATE_ONLY",
    "wall_seconds": 0.0046892911195755005
  },
  "BinAlpha_default": {
    "dataset": "BinAlpha",
    "dataset_version": null,
    "status": "BLOCKED_DATA",
    "reason": "BinAlpha is unavailable: Chang et al. name BinAlpha as 26 binary handwritten alphabets with 30 randomly selected images per alphabet, without a URL, image size, or seed. Binary Alphadigits (36 classes x 39 images, 20x16) is on disk (SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7). No evidence was found that Chang et al. used that file. Default load_dataset('BinAlpha') does not claim EXACT. Use version='CANDIDATE_BIN_ALPHA' (seed 0, 780x320) or version='binaryalphadigs36' for explicit non-paper versions. See benchmarks/binalpha/README.md.",
    "wall_seconds": 7.2908587753772736e-06
  },
  "AR": {
    "dataset": "AR",
    "dataset_version": null,
    "status": "BLOCKED_DATA",
    "reason": "AR is unavailable: Chang et al. name AR as 840 faces of 120 people and do not say which 840. Official Martinez distribution was not obtained. A THIRD-PARTY zip ARDB_Full.zip from Zenodo 19683234 (uploader Manu shree, not Martinez/OSU) was downloaded on 2026-10-21: 120587997 bytes, MD5 bb97bd9237680744c0c7268624696263 (matches the published Zenodo checksum), SHA-256 32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438. The zip is PKZIP, not HTML. It contains 100 folders s1-s100 with 120x165 BMP files named 1.bmp..26.bmp, not official M-xx-yy.raw / F-xx-yy.raw names. No archive document states an 840/120 or 7-image rule, so that subset was not invented. Status: SOURCE_RECOVERED_SUBSET_UNVERIFIED. Default load_dataset('AR') does not claim EXACT. See benchmarks/ar/README.md.",
    "wall_seconds": 0.00046516722068190575
  },
  "AR_zenodo": {
    "dataset": "AR",
    "dataset_version": "zenodo_third_party_full",
    "status": "BLOCKED_DATA",
    "reason": "AR is unavailable: version=zenodo_third_party_full is the third-party Zenodo dump, not the paper 840/120 set. The zip is on disk at /Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v1/benchmarks/ar/data/ARDB_Full.zip (SHA-256 32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438, MD5 bb97bd9237680744c0c7268624696263) with 100 identities. Status SOURCE_RECOVERED_SUBSET_UNVERIFIED. Arrays are not returned under a paper-AR name.",
    "wall_seconds": 3.816699609160423e-05
  },
  "UMIST": {
    "dataset": "UMIST",
    "dataset_version": null,
    "status": "BLOCKED_DATA",
    "reason": "UMIST is unavailable: No 564-image UMIST/Sheffield archive was obtained on 2026-10-20. The Wayback copy of http://images.ee.umist.ac.uk/danny/face.tar.gz has 1012 unique PGM files of 20 people with 122 different shapes. The pre-cropped cropped.tar.gz has 575 PGM files, 20 people, all 112x92, of which 565 pixel arrays are unique. Figshare 67153214 is also 575 slices and is not pixel-identical to that tar. Use version='precropped575' or version='figshare575' to load those non-exact files. See docs/repair_round1_dataset_recovery.md.",
    "wall_seconds": 0.00046070897951722145
  },
  "MSRA50": {
    "dataset": "MSRA50",
    "dataset_version": null,
    "status": "BLOCKED_DATA",
    "reason": "MSRA50 is unavailable: MSRA50 is BLOCKED_DATA_NOT_OBTAINED. Chang et al. state 1799 images and 12 classes resized to 32x32, with no URL. Local inspection plus the UTS-affiliation AAAI 2015 PDF and the local arXiv:1411.6241v1 sister PDF give only literature counts (1799/12/1024), not a file. No 1799x12x1024 archive is in benchmarks/msra50/data/. Other MSRA corpora were not substituted. See benchmarks/msra50/README.md.",
    "wall_seconds": 0.00040404172614216805
  },
  "SPLS": {
    "dataset": "SPLS",
    "status": "BLOCKED_MISSING_FULL_METHOD",
    "reason": "Section 3 not obtained; baselines.spls.fit_predict raises NotImplementedError"
  }
}
```

## Shared F (SC == SSC)

```json
{
  "note": "SC F must equal SSC F under the same SpectralGraphConfig.",
  "pairs": {
    "ORL:att92": {
      "sc_run": "20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce",
      "e8_run": "20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41",
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
      "sc_run": "20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b",
      "e8_run": "20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d",
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
      "sc_run": "20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51",
      "e8_run": "20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 4.2212761064419624e-14,
      "shape": [
        2414,
        38
      ]
    },
    "USPS:libsvm": {
      "sc_run": "20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055",
      "e8_run": "20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 1.0443035325380379e-14,
      "shape": [
        9298,
        10
      ]
    },
    "BinAlpha:CANDIDATE_BIN_ALPHA": {
      "sc_run": "20261021_222540__STRICT_PAPER__BINALPHA__SC_EQ4__3ee1fb96",
      "e8_run": "20261021_222551__STRICT_PAPER__BINALPHA__SSC_E8_G1P0__bb112504",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 1.534883331544279e-14,
      "shape": [
        780,
        26
      ]
    }
  },
  "all_equal_atol_1e-12": true
}
```

## Cells with n=50 (80)

- K-means K1 × JAFFE γ=NA n=50 `20261021_222424__STRICT_PAPER__JAFFE__K1_RANDOM_MEAN__04a75613`
- SC × JAFFE γ=NA n=50 `20261021_222427__STRICT_PAPER__JAFFE__SC_EQ4__2a69392b`
- PCA-KM × JAFFE γ=NA n=50 `20261021_222444__STRICT_PAPER__JAFFE__PCAKM_D10__7c72e3f5`
- PCA-SC × JAFFE γ=NA n=50 `20261021_222445__STRICT_PAPER__JAFFE__PCASC_D10__081fec38`
- LDA-KM × JAFFE γ=NA n=50 `20261021_222447__STRICT_PAPER__JAFFE__LDAKM_D9__e9500286`
- LLC × JAFFE γ=NA n=50 `20261021_222459__STRICT_PAPER__JAFFE__LLC__27bff2c2`
- SSC E8 × JAFFE γ=1e-06 n=50 `20261021_222428__STRICT_PAPER__JAFFE__SSC_E8_G1EM6__675147ed`
- SSC E8 × JAFFE γ=0.001 n=50 `20261021_222431__STRICT_PAPER__JAFFE__SSC_E8_G1EM3__c0897140`
- SSC E8 × JAFFE γ=1.0 n=50 `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d`
- SSC E8 × JAFFE γ=1000.0 n=50 `20261021_222437__STRICT_PAPER__JAFFE__SSC_E8_G1E3__ef79feea`
- SSC E8 × JAFFE γ=1000000.0 n=50 `20261021_222440__STRICT_PAPER__JAFFE__SSC_E8_G1E6__a7b0e589`
- SSC E13 × JAFFE γ=1e-06 n=50 `20261021_222429__STRICT_PAPER__JAFFE__SSC_E13_G1EM6__07f9ec02`
- SSC E13 × JAFFE γ=0.001 n=50 `20261021_222432__STRICT_PAPER__JAFFE__SSC_E13_G1EM3__7909b415`
- SSC E13 × JAFFE γ=1.0 n=50 `20261021_222436__STRICT_PAPER__JAFFE__SSC_E13_G1P0__3b0a6293`
- SSC E13 × JAFFE γ=1000.0 n=50 `20261021_222439__STRICT_PAPER__JAFFE__SSC_E13_G1E3__e8d79da1`
- SSC E13 × JAFFE γ=1000000.0 n=50 `20261021_222442__STRICT_PAPER__JAFFE__SSC_E13_G1E6__399b063f`
- K-means K1 × ORL γ=NA n=50 `20261021_222132__STRICT_PAPER__ORL__K1_RANDOM_MEAN__e6f86081`
- SC × ORL γ=NA n=50 `20261021_222136__STRICT_PAPER__ORL__SC_EQ4__45db39ce`
- PCA-KM × ORL γ=NA n=50 `20261021_222154__STRICT_PAPER__ORL__PCAKM_D40__2c598f1e`
- PCA-SC × ORL γ=NA n=50 `20261021_222155__STRICT_PAPER__ORL__PCASC_D40__4b701796`
- LDA-KM × ORL γ=NA n=50 `20261021_222157__STRICT_PAPER__ORL__LDAKM_D39__d5cab533`
- LLC × ORL γ=NA n=50 `20261021_222251__STRICT_PAPER__ORL__LLC__e1060d1f`
- SSC E8 × ORL γ=1e-06 n=50 `20261021_222137__STRICT_PAPER__ORL__SSC_E8_G1EM6__adf2580d`
- SSC E8 × ORL γ=0.001 n=50 `20261021_222140__STRICT_PAPER__ORL__SSC_E8_G1EM3__df6428ad`
- SSC E8 × ORL γ=1.0 n=50 `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41`
- SSC E8 × ORL γ=1000.0 n=50 `20261021_222146__STRICT_PAPER__ORL__SSC_E8_G1E3__242cbb2a`
- SSC E8 × ORL γ=1000000.0 n=50 `20261021_222150__STRICT_PAPER__ORL__SSC_E8_G1E6__6f1ea6fc`
- SSC E13 × ORL γ=1e-06 n=50 `20261021_222138__STRICT_PAPER__ORL__SSC_E13_G1EM6__762e2e6b`
- SSC E13 × ORL γ=0.001 n=50 `20261021_222141__STRICT_PAPER__ORL__SSC_E13_G1EM3__d107e201`
- SSC E13 × ORL γ=1.0 n=50 `20261021_222145__STRICT_PAPER__ORL__SSC_E13_G1P0__2ac11826`
- SSC E13 × ORL γ=1000.0 n=50 `20261021_222148__STRICT_PAPER__ORL__SSC_E13_G1E3__b06add0f`
- SSC E13 × ORL γ=1000000.0 n=50 `20261021_222152__STRICT_PAPER__ORL__SSC_E13_G1E6__e0769e27`
- K-means K1 × BinAlpha γ=NA n=50 `20261021_222536__STRICT_PAPER__BINALPHA__K1_RANDOM_MEAN__87fee2df`
- SC × BinAlpha γ=NA n=50 `20261021_222540__STRICT_PAPER__BINALPHA__SC_EQ4__3ee1fb96`
- PCA-KM × BinAlpha γ=NA n=50 `20261021_222608__STRICT_PAPER__BINALPHA__PCAKM_D26__29513129`
- PCA-SC × BinAlpha γ=NA n=50 `20261021_222609__STRICT_PAPER__BINALPHA__PCASC_D26__f1832940`
- LDA-KM × BinAlpha γ=NA n=50 `20261021_222611__STRICT_PAPER__BINALPHA__LDAKM_D25__1a9891ae`
- LLC × BinAlpha γ=NA n=50 `20261021_222617__STRICT_PAPER__BINALPHA__LLC__376d2f24`
- SSC E8 × BinAlpha γ=1e-06 n=50 `20261021_222542__STRICT_PAPER__BINALPHA__SSC_E8_G1EM6__1aba155f`
- SSC E8 × BinAlpha γ=0.001 n=50 `20261021_222547__STRICT_PAPER__BINALPHA__SSC_E8_G1EM3__8d7cbc0b`
- SSC E8 × BinAlpha γ=1.0 n=50 `20261021_222551__STRICT_PAPER__BINALPHA__SSC_E8_G1P0__bb112504`
- SSC E8 × BinAlpha γ=1000.0 n=50 `20261021_222558__STRICT_PAPER__BINALPHA__SSC_E8_G1E3__ee448a30`
- SSC E8 × BinAlpha γ=1000000.0 n=50 `20261021_222603__STRICT_PAPER__BINALPHA__SSC_E8_G1E6__f433ed58`
- SSC E13 × BinAlpha γ=1e-06 n=50 `20261021_222544__STRICT_PAPER__BINALPHA__SSC_E13_G1EM6__5c09589c`
- SSC E13 × BinAlpha γ=0.001 n=50 `20261021_222549__STRICT_PAPER__BINALPHA__SSC_E13_G1EM3__6b3594d4`
- SSC E13 × BinAlpha γ=1.0 n=50 `20261021_222555__STRICT_PAPER__BINALPHA__SSC_E13_G1P0__ab5189db`
- SSC E13 × BinAlpha γ=1000.0 n=50 `20261021_222601__STRICT_PAPER__BINALPHA__SSC_E13_G1E3__f6c6cdbd`
- SSC E13 × BinAlpha γ=1000000.0 n=50 `20261021_222605__STRICT_PAPER__BINALPHA__SSC_E13_G1E6__62a04adb`
- K-means K1 × YaleB γ=NA n=50 `20261021_222703__STRICT_PAPER__YALEB__K1_RANDOM_MEAN__00d342a9`
- SC × YaleB γ=NA n=50 `20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51`
- PCA-KM × YaleB γ=NA n=50 `20261021_223145__STRICT_PAPER__YALEB__PCAKM_D38__25a72e9a`
- PCA-SC × YaleB γ=NA n=50 `20261021_223148__STRICT_PAPER__YALEB__PCASC_D38__4dbafed6`
- LDA-KM × YaleB γ=NA n=50 `20261021_223151__STRICT_PAPER__YALEB__LDAKM_D37__fdebf13f`
- LLC × YaleB γ=NA n=50 `20261021_223619__STRICT_PAPER__YALEB__LLC__f34e8285`
- SSC E8 × YaleB γ=1e-06 n=50 `20261021_222723__STRICT_PAPER__YALEB__SSC_E8_G1EM6__da885cd6`
- SSC E8 × YaleB γ=0.001 n=50 `20261021_222809__STRICT_PAPER__YALEB__SSC_E8_G1EM3__19b9bf6c`
- SSC E8 × YaleB γ=1.0 n=50 `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff`
- SSC E8 × YaleB γ=1000.0 n=50 `20261021_222955__STRICT_PAPER__YALEB__SSC_E8_G1E3__9a7861d8`
- SSC E8 × YaleB γ=1000000.0 n=50 `20261021_223047__STRICT_PAPER__YALEB__SSC_E8_G1E6__96e89a23`
- SSC E13 × YaleB γ=1e-06 n=50 `20261021_222746__STRICT_PAPER__YALEB__SSC_E13_G1EM6__9151ee18`
- SSC E13 × YaleB γ=0.001 n=50 `20261021_222833__STRICT_PAPER__YALEB__SSC_E13_G1EM3__43df00ac`
- SSC E13 × YaleB γ=1.0 n=50 `20261021_222926__STRICT_PAPER__YALEB__SSC_E13_G1P0__1b4ce239`
- SSC E13 × YaleB γ=1000.0 n=50 `20261021_223020__STRICT_PAPER__YALEB__SSC_E13_G1E3__cef2ff26`
- SSC E13 × YaleB γ=1000000.0 n=50 `20261021_223116__STRICT_PAPER__YALEB__SSC_E13_G1E6__693e4708`
- K-means K1 × USPS γ=NA n=50 `20261021_223721__STRICT_PAPER__USPS__K1_RANDOM_MEAN__c94c1dff`
- SC × USPS γ=NA n=50 `20261021_223747__STRICT_PAPER__USPS__SC_EQ4__adec7055`
- PCA-KM × USPS γ=NA n=50 `20261021_231412__STRICT_PAPER__USPS__PCAKM_D10__421e9140`
- PCA-SC × USPS γ=NA n=50 `20261021_231417__STRICT_PAPER__USPS__PCASC_D10__1323a23f`
- LDA-KM × USPS γ=NA n=50 `20261021_231422__STRICT_PAPER__USPS__LDAKM_D9__36a4c97e`
- LLC × USPS γ=NA n=50 `20261021_231531__STRICT_PAPER__USPS__LLC__48716f45`
- SSC E8 × USPS γ=1e-06 n=50 `20261021_223754__STRICT_PAPER__USPS__SSC_E8_G1EM6__ddf1165e`
- SSC E8 × USPS γ=0.001 n=50 `20261021_224502__STRICT_PAPER__USPS__SSC_E8_G1EM3__5c173e5c`
- SSC E8 × USPS γ=1.0 n=50 `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b`
- SSC E8 × USPS γ=1000.0 n=50 `20261021_225950__STRICT_PAPER__USPS__SSC_E8_G1E3__e8aad5e1`
- SSC E8 × USPS γ=1000000.0 n=50 `20261021_230701__STRICT_PAPER__USPS__SSC_E8_G1E6__bf47b88e`
- SSC E13 × USPS γ=1e-06 n=50 `20261021_224130__STRICT_PAPER__USPS__SSC_E13_G1EM6__0c0aa27c`
- SSC E13 × USPS γ=0.001 n=50 `20261021_224824__STRICT_PAPER__USPS__SSC_E13_G1EM3__00915b34`
- SSC E13 × USPS γ=1.0 n=50 `20261021_225621__STRICT_PAPER__USPS__SSC_E13_G1P0__ee3ef1fe`
- SSC E13 × USPS γ=1000.0 n=50 `20261021_230328__STRICT_PAPER__USPS__SSC_E13_G1E3__f136da9a`
- SSC E13 × USPS γ=1000000.0 n=50 `20261021_231040__STRICT_PAPER__USPS__SSC_E13_G1E6__a3b2648d`

## Gamma-grid rows with at least one real trial (50)

- SSC E8 × JAFFE γ=1e-06 n=50 status=completed `20261021_222428__STRICT_PAPER__JAFFE__SSC_E8_G1EM6__675147ed`
- SSC E8 × JAFFE γ=0.001 n=50 status=completed `20261021_222431__STRICT_PAPER__JAFFE__SSC_E8_G1EM3__c0897140`
- SSC E8 × JAFFE γ=1.0 n=50 status=completed `20261021_222434__STRICT_PAPER__JAFFE__SSC_E8_G1P0__8a4a026d`
- SSC E8 × JAFFE γ=1000.0 n=50 status=completed `20261021_222437__STRICT_PAPER__JAFFE__SSC_E8_G1E3__ef79feea`
- SSC E8 × JAFFE γ=1000000.0 n=50 status=completed `20261021_222440__STRICT_PAPER__JAFFE__SSC_E8_G1E6__a7b0e589`
- SSC E13 × JAFFE γ=1e-06 n=50 status=completed `20261021_222429__STRICT_PAPER__JAFFE__SSC_E13_G1EM6__07f9ec02`
- SSC E13 × JAFFE γ=0.001 n=50 status=completed `20261021_222432__STRICT_PAPER__JAFFE__SSC_E13_G1EM3__7909b415`
- SSC E13 × JAFFE γ=1.0 n=50 status=completed `20261021_222436__STRICT_PAPER__JAFFE__SSC_E13_G1P0__3b0a6293`
- SSC E13 × JAFFE γ=1000.0 n=50 status=completed `20261021_222439__STRICT_PAPER__JAFFE__SSC_E13_G1E3__e8d79da1`
- SSC E13 × JAFFE γ=1000000.0 n=50 status=completed `20261021_222442__STRICT_PAPER__JAFFE__SSC_E13_G1E6__399b063f`
- SSC E8 × ORL γ=1e-06 n=50 status=completed `20261021_222137__STRICT_PAPER__ORL__SSC_E8_G1EM6__adf2580d`
- SSC E8 × ORL γ=0.001 n=50 status=completed `20261021_222140__STRICT_PAPER__ORL__SSC_E8_G1EM3__df6428ad`
- SSC E8 × ORL γ=1.0 n=50 status=completed `20261021_222143__STRICT_PAPER__ORL__SSC_E8_G1P0__4be5ba41`
- SSC E8 × ORL γ=1000.0 n=50 status=completed `20261021_222146__STRICT_PAPER__ORL__SSC_E8_G1E3__242cbb2a`
- SSC E8 × ORL γ=1000000.0 n=50 status=completed `20261021_222150__STRICT_PAPER__ORL__SSC_E8_G1E6__6f1ea6fc`
- SSC E13 × ORL γ=1e-06 n=50 status=completed `20261021_222138__STRICT_PAPER__ORL__SSC_E13_G1EM6__762e2e6b`
- SSC E13 × ORL γ=0.001 n=50 status=completed `20261021_222141__STRICT_PAPER__ORL__SSC_E13_G1EM3__d107e201`
- SSC E13 × ORL γ=1.0 n=50 status=completed `20261021_222145__STRICT_PAPER__ORL__SSC_E13_G1P0__2ac11826`
- SSC E13 × ORL γ=1000.0 n=50 status=completed `20261021_222148__STRICT_PAPER__ORL__SSC_E13_G1E3__b06add0f`
- SSC E13 × ORL γ=1000000.0 n=50 status=completed `20261021_222152__STRICT_PAPER__ORL__SSC_E13_G1E6__e0769e27`
- SSC E8 × BinAlpha γ=1e-06 n=50 status=completed `20261021_222542__STRICT_PAPER__BINALPHA__SSC_E8_G1EM6__1aba155f`
- SSC E8 × BinAlpha γ=0.001 n=50 status=completed `20261021_222547__STRICT_PAPER__BINALPHA__SSC_E8_G1EM3__8d7cbc0b`
- SSC E8 × BinAlpha γ=1.0 n=50 status=completed `20261021_222551__STRICT_PAPER__BINALPHA__SSC_E8_G1P0__bb112504`
- SSC E8 × BinAlpha γ=1000.0 n=50 status=completed `20261021_222558__STRICT_PAPER__BINALPHA__SSC_E8_G1E3__ee448a30`
- SSC E8 × BinAlpha γ=1000000.0 n=50 status=completed `20261021_222603__STRICT_PAPER__BINALPHA__SSC_E8_G1E6__f433ed58`
- SSC E13 × BinAlpha γ=1e-06 n=50 status=completed `20261021_222544__STRICT_PAPER__BINALPHA__SSC_E13_G1EM6__5c09589c`
- SSC E13 × BinAlpha γ=0.001 n=50 status=completed `20261021_222549__STRICT_PAPER__BINALPHA__SSC_E13_G1EM3__6b3594d4`
- SSC E13 × BinAlpha γ=1.0 n=50 status=completed `20261021_222555__STRICT_PAPER__BINALPHA__SSC_E13_G1P0__ab5189db`
- SSC E13 × BinAlpha γ=1000.0 n=50 status=completed `20261021_222601__STRICT_PAPER__BINALPHA__SSC_E13_G1E3__f6c6cdbd`
- SSC E13 × BinAlpha γ=1000000.0 n=50 status=completed `20261021_222605__STRICT_PAPER__BINALPHA__SSC_E13_G1E6__62a04adb`
- SSC E8 × YaleB γ=1e-06 n=50 status=completed `20261021_222723__STRICT_PAPER__YALEB__SSC_E8_G1EM6__da885cd6`
- SSC E8 × YaleB γ=0.001 n=50 status=completed `20261021_222809__STRICT_PAPER__YALEB__SSC_E8_G1EM3__19b9bf6c`
- SSC E8 × YaleB γ=1.0 n=50 status=completed `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff`
- SSC E8 × YaleB γ=1000.0 n=50 status=completed `20261021_222955__STRICT_PAPER__YALEB__SSC_E8_G1E3__9a7861d8`
- SSC E8 × YaleB γ=1000000.0 n=50 status=completed `20261021_223047__STRICT_PAPER__YALEB__SSC_E8_G1E6__96e89a23`
- SSC E13 × YaleB γ=1e-06 n=50 status=completed `20261021_222746__STRICT_PAPER__YALEB__SSC_E13_G1EM6__9151ee18`
- SSC E13 × YaleB γ=0.001 n=50 status=completed `20261021_222833__STRICT_PAPER__YALEB__SSC_E13_G1EM3__43df00ac`
- SSC E13 × YaleB γ=1.0 n=50 status=completed `20261021_222926__STRICT_PAPER__YALEB__SSC_E13_G1P0__1b4ce239`
- SSC E13 × YaleB γ=1000.0 n=50 status=completed `20261021_223020__STRICT_PAPER__YALEB__SSC_E13_G1E3__cef2ff26`
- SSC E13 × YaleB γ=1000000.0 n=50 status=completed `20261021_223116__STRICT_PAPER__YALEB__SSC_E13_G1E6__693e4708`
- SSC E8 × USPS γ=1e-06 n=50 status=completed `20261021_223754__STRICT_PAPER__USPS__SSC_E8_G1EM6__ddf1165e`
- SSC E8 × USPS γ=0.001 n=50 status=completed `20261021_224502__STRICT_PAPER__USPS__SSC_E8_G1EM3__5c173e5c`
- SSC E8 × USPS γ=1.0 n=50 status=completed `20261021_225145__STRICT_PAPER__USPS__SSC_E8_G1P0__0a34012b`
- SSC E8 × USPS γ=1000.0 n=50 status=completed `20261021_225950__STRICT_PAPER__USPS__SSC_E8_G1E3__e8aad5e1`
- SSC E8 × USPS γ=1000000.0 n=50 status=completed `20261021_230701__STRICT_PAPER__USPS__SSC_E8_G1E6__bf47b88e`
- SSC E13 × USPS γ=1e-06 n=50 status=completed `20261021_224130__STRICT_PAPER__USPS__SSC_E13_G1EM6__0c0aa27c`
- SSC E13 × USPS γ=0.001 n=50 status=completed `20261021_224824__STRICT_PAPER__USPS__SSC_E13_G1EM3__00915b34`
- SSC E13 × USPS γ=1.0 n=50 status=completed `20261021_225621__STRICT_PAPER__USPS__SSC_E13_G1P0__ee3ef1fe`
- SSC E13 × USPS γ=1000.0 n=50 status=completed `20261021_230328__STRICT_PAPER__USPS__SSC_E13_G1E3__f136da9a`
- SSC E13 × USPS γ=1000000.0 n=50 status=completed `20261021_231040__STRICT_PAPER__USPS__SSC_E13_G1E6__a3b2648d`

## INCOMPLETE (0)

- none

## BLOCKED (56)

- K-means K1 × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- SC × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- PCA-KM × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- PCA-SC × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- LDA-KM × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- LLC × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- SPLS × AR: BLOCKED_MISSING_FULL_METHOD (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- SSC E8 × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- SSC E13 × AR: SOURCE_RECOVERED_SUBSET_UNVERIFIED (SOURCE_RECOVERED_SUBSET_UNVERIFIED_third_party_zenodo_100_ids_not_official_Martinez_not_paper_840_120_not_EXACT)
- SPLS × JAFFE: BLOCKED_MISSING_FULL_METHOD (verified_zenodo_213_not_paper_unpublished_copy)
- SPLS × ORL: BLOCKED_MISSING_FULL_METHOD (original_source_att92_92x112_bilinear_32x32)
- K-means K1 × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- SC × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- PCA-KM × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- PCA-SC × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- LDA-KM × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- LLC × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- SPLS × UMIST: BLOCKED_MISSING_FULL_METHOD (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- SSC E8 × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- SSC E13 × UMIST: BLOCKED_DATA (BLOCKED_DATA_paper_564_not_obtained_575_files_565_unique)
- SPLS × BinAlpha: BLOCKED_MISSING_FULL_METHOD (CANDIDATE_BIN_ALPHA)
- K-means K1 × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- SC × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- PCA-KM × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- PCA-SC × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- LDA-KM × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- LLC × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- SPLS × MSRA50: BLOCKED_MISSING_FULL_METHOD (BLOCKED_DATA_NOT_OBTAINED)
- SSC E8 × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- SSC E13 × MSRA50: BLOCKED_DATA_NOT_OBTAINED (BLOCKED_DATA_NOT_OBTAINED)
- SPLS × YaleB: BLOCKED_MISSING_FULL_METHOD (obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai)
- SPLS × USPS: BLOCKED_MISSING_FULL_METHOD (verified_libsvm_9298)

## Extra (K2/K3/K4, LDA-SC APPROXIMATE, PCA dim grid)

These are not substitutes for paper cells and are never chosen by ACC.

| Method | Dataset | Reproduced ACC | trial count | status | run IDs |
| --- | --- | --- | --- | --- | --- |
| K-means K2 | AR |  | 0 | SOURCE_RECOVERED_SUBSET_UNVERIFIED |  |
| K-means K3 | AR |  | 0 | SOURCE_RECOVERED_SUBSET_UNVERIFIED |  |
| K-means K4 | AR |  | 0 | SOURCE_RECOVERED_SUBSET_UNVERIFIED |  |
| LDA-SC | AR |  | 0 | SOURCE_RECOVERED_SUBSET_UNVERIFIED |  |
| K-means K2 | JAFFE | 82.6 ± 0.0 (n=1) | 1 | completed | 20261021_222424__STRICT_PAPER__JAFFE__K1_RANDOM_MEAN__04a75613 |
| K-means K3 | JAFFE | 80.0 ± 6.4 (n=50) | 50 | completed | 20261021_222425__STRICT_PAPER__JAFFE__K3_KMEANSPP_MEAN__f093070d |
| K-means K4 | JAFFE | 84.0 ± 0.0 (n=1) | 1 | completed | 20261021_222425__STRICT_PAPER__JAFFE__K3_KMEANSPP_MEAN__f093070d |
| LDA-SC | JAFFE | 34.6 ± 9.9 (n=10) | 10 | INCOMPLETE | 20261021_222522__STRICT_PAPER__JAFFE__LDASC_D9__e73843d5 |
| PCA-KM grid | JAFFE | 73.8 ± 4.9 (n=5) | 5 | INCOMPLETE | 20261021_222501__STRICT_PAPER__JAFFE__PCAKM_GRID_D20__c1a4ff98 |
| PCA-KM grid | JAFFE | 72.5 ± 4.1 (n=5) | 5 | INCOMPLETE | 20261021_222502__STRICT_PAPER__JAFFE__PCAKM_GRID_D30__a16a66e5 |
| PCA-KM grid | JAFFE | 72.5 ± 4.1 (n=5) | 5 | INCOMPLETE | 20261021_222504__STRICT_PAPER__JAFFE__PCAKM_GRID_D40__a855a915 |
| PCA-KM grid | JAFFE | 71.1 ± 5.4 (n=5) | 5 | INCOMPLETE | 20261021_222505__STRICT_PAPER__JAFFE__PCAKM_GRID_D50__7302b003 |
| PCA-KM grid | JAFFE | 72.5 ± 4.1 (n=5) | 5 | INCOMPLETE | 20261021_222507__STRICT_PAPER__JAFFE__PCAKM_GRID_D60__a4f53a14 |
| PCA-KM grid | JAFFE | 72.5 ± 4.1 (n=5) | 5 | INCOMPLETE | 20261021_222508__STRICT_PAPER__JAFFE__PCAKM_GRID_D70__8460dbfe |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222510__STRICT_PAPER__JAFFE__PCAKM_GRID_D80__73c7433c |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222511__STRICT_PAPER__JAFFE__PCAKM_GRID_D90__6de416db |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222513__STRICT_PAPER__JAFFE__PCAKM_GRID_D100__595e649e |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222514__STRICT_PAPER__JAFFE__PCAKM_GRID_D110__533bfb36 |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222516__STRICT_PAPER__JAFFE__PCAKM_GRID_D120__a124a159 |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222517__STRICT_PAPER__JAFFE__PCAKM_GRID_D130__db9252be |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222519__STRICT_PAPER__JAFFE__PCAKM_GRID_D140__fe855322 |
| PCA-KM grid | JAFFE | 72.3 ± 4.2 (n=5) | 5 | INCOMPLETE | 20261021_222520__STRICT_PAPER__JAFFE__PCAKM_GRID_D150__691e18f5 |
| K-means K2 | ORL | 64.2 ± 0.0 (n=1) | 1 | completed | 20261021_222132__STRICT_PAPER__ORL__K1_RANDOM_MEAN__e6f86081 |
| K-means K3 | ORL | 69.2 ± 3.5 (n=50) | 50 | completed | 20261021_222134__STRICT_PAPER__ORL__K3_KMEANSPP_MEAN__8f6d296d |
| K-means K4 | ORL | 72.5 ± 0.0 (n=1) | 1 | completed | 20261021_222134__STRICT_PAPER__ORL__K3_KMEANSPP_MEAN__8f6d296d |
| LDA-SC | ORL | 46.1 ± 5.5 (n=10) | 10 | INCOMPLETE | 20261021_222345__STRICT_PAPER__ORL__LDASC_D39__31fc0fa3 |
| PCA-KM grid | ORL | 59.0 ± 4.5 (n=5) | 5 | INCOMPLETE | 20261021_222252__STRICT_PAPER__ORL__PCAKM_GRID_D10__ea61d53a |
| PCA-KM grid | ORL | 62.2 ± 3.0 (n=5) | 5 | INCOMPLETE | 20261021_222254__STRICT_PAPER__ORL__PCAKM_GRID_D20__1de19745 |
| PCA-KM grid | ORL | 62.4 ± 1.6 (n=5) | 5 | INCOMPLETE | 20261021_222255__STRICT_PAPER__ORL__PCAKM_GRID_D30__8d25114b |
| PCA-KM grid | ORL | 63.1 ± 1.2 (n=5) | 5 | INCOMPLETE | 20261021_222256__STRICT_PAPER__ORL__PCAKM_GRID_D50__543337d8 |
| PCA-KM grid | ORL | 62.2 ± 1.8 (n=5) | 5 | INCOMPLETE | 20261021_222257__STRICT_PAPER__ORL__PCAKM_GRID_D60__d6b48b1a |
| PCA-KM grid | ORL | 62.5 ± 2.7 (n=5) | 5 | INCOMPLETE | 20261021_222258__STRICT_PAPER__ORL__PCAKM_GRID_D70__85b3327e |
| PCA-KM grid | ORL | 61.9 ± 3.1 (n=5) | 5 | INCOMPLETE | 20261021_222300__STRICT_PAPER__ORL__PCAKM_GRID_D80__dbcea863 |
| PCA-KM grid | ORL | 61.1 ± 3.9 (n=5) | 5 | INCOMPLETE | 20261021_222301__STRICT_PAPER__ORL__PCAKM_GRID_D90__101759d6 |
| PCA-KM grid | ORL | 61.5 ± 3.3 (n=5) | 5 | INCOMPLETE | 20261021_222302__STRICT_PAPER__ORL__PCAKM_GRID_D100__5076874c |
| PCA-KM grid | ORL | 61.9 ± 2.9 (n=5) | 5 | INCOMPLETE | 20261021_222304__STRICT_PAPER__ORL__PCAKM_GRID_D110__f986f134 |
| PCA-KM grid | ORL | 61.5 ± 2.6 (n=5) | 5 | INCOMPLETE | 20261021_222305__STRICT_PAPER__ORL__PCAKM_GRID_D120__2155d617 |
| PCA-KM grid | ORL | 60.9 ± 1.6 (n=5) | 5 | INCOMPLETE | 20261021_222306__STRICT_PAPER__ORL__PCAKM_GRID_D130__70fd019e |
| PCA-KM grid | ORL | 60.9 ± 1.7 (n=5) | 5 | INCOMPLETE | 20261021_222307__STRICT_PAPER__ORL__PCAKM_GRID_D140__7bf7d036 |
| PCA-KM grid | ORL | 61.0 ± 1.8 (n=5) | 5 | INCOMPLETE | 20261021_222309__STRICT_PAPER__ORL__PCAKM_GRID_D150__0aa29277 |

## Integrity

- Every reproduced number comes from `runs/strict_paper/` trial logs.
- Unconverged IRLS is left unconverged.
- No trial is invented, extrapolated, or selected by ACC.
- Paper ACC/NMI in the matrix are historical Chang et al. Tables 1–2 only.

