# COMP3314 Group 23 — Spectral Shrunk Clustering (v1, round 2)

HKU COMP3314 Machine Learning course project. **Branch: `v1`.**

This directory is a from-scratch reimplementation of Chang, Nie, Ma, Yang, and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015 ([doi:10.1609/aaai.v29i1.9606](https://doi.org/10.1609/aaai.v29i1.9606)). There is no official author code. The written report uses the NeurIPS 2026 LaTeX style with the **preprint** option and is a course report, not a NeurIPS submission. The compiled PDF does **not** include the NeurIPS checklist.

Intended GitHub remote: [https://github.com/SelinaMai-SYM/COMP-3314-G23.git](https://github.com/SelinaMai-SYM/COMP-3314-G23.git), branch `v1` only.

Group membership, names, and emails require confirmation and are not invented here.

## Reproducibility Audit

Short index only. Details live next to the code and data, not here.

| Area | Where |
| --- | --- |
| Eight baselines (status, original paper, implementation map) | [`baselines/`](baselines/) |
| Eight datasets (provenance, SHA-256, sample-set status) | [`benchmarks/`](benchmarks/) |
| SSC equations, E8/E13, shared Eq. (4) \(F\) | [`SSC_method/`](SSC_method/) |
| Round 2 runs and aggregated numbers | [`results/`](results/), [`runs/`](runs/) |

No dataset is `FULL_PROTOCOL_REPRODUCED`. SPLS is `NOT_IMPLEMENTED`. LDA-SC is `APPROXIMATE` and is not in the faithful table. Documentation check: `python3 scripts/validate_reproducibility_docs.py`.

## Provenance (keep these distinct)

| Piece | Who |
| --- | --- |
| Original method (Eq. 4 embedding, Eq. 8 objective, printed Eq. 13 update, \(K\)-means on `G`) | Chang et al., AAAI 2015 |
| This reimplementation (`SSC_method/`) | this course project. Variant **E8** (`A=S+2γL̃`) is the faithful stationary point of printed Eq. 8. Variant **E13** (`A=S+γL̃`) is the printed update (library default). Algorithm 1 line 10 is not executed |
| Round 2 | shared SC/SSC \(F\), att92 / CroppedYale diagnostics, D1–D12, four-page report without checklist. Records under `runs/round2/` and `results/round2/` |
| Repair round 1 | configurable E8/E13 and extra archives. Records under `runs/repair_round1/` |
| Experiment protocol, historical Track A / Track B | this course project; historical `runs/` were not deleted |
| Mutual-kNN shrinkage graph (`method_extension/`) | adaptation of an established graph to SSC; Category C; not a new theorem; negative |
| Datasets | third-party (AT&T/ORL, JAFFE, Extended Yale B, LIBSVM USPS, Binary Alphadigits parent, extra UMIST archives that are **not** 564 images). AR Zenodo was not downloaded. MSRA50 was not found |
| Libraries | NumPy, SciPy, scikit-learn, matplotlib, PyYAML; optional CVXPY for the convex audit |

Paper table numbers are labelled **Reported in Chang et al. (2015)**. Numbers in `results/` are **Our Reproduction** from `runs/`. They are not copies of the paper. Category B (\(k\)-means++) and C (row-normalized eigenvectors, mutual kNN) are never called the paper method.

## Honest headline results (round 2)

- **\(F\) is shared.** Same `SpectralGraphConfig` ⇒ SC \(F\) equals SSC \(F\) (`results/round2/d2_shared_f.json`, max abs diff 0).
- **Earliest ORL gap:** random \(K\)-means on Eq. (4) \(F\), before IRLS. Historical Olivetti SC **54.2±3.1** (n=50) verified. Unified-\(F\) Olivetti SC **53.9±3.0**. att92 SC **56.2±4.2** vs paper SC 72.7 (**−16.5 pp**).
- **Faithful E8 does not reproduce 76%.** att92 E8 **57.3±3.8** (n=50) vs paper SSC 76.0 (**−18.7 pp**). Shrinkage still does not help.
- **\(k\)-means++ 78.3±1.3** on the saved att92 \(F\) is **B_AMBIGUITY**, not a reproduction.
- YaleB SSC: **n=10**, not 50. USPS SSC: **n=3**, not 50.
- Mutual-kNN extension (JAFFE n=50): 68.4 vs union E8 68.4, not a win.
- SPLS: `NOT_IMPLEMENTED`. LDA-SC: approximate, omitted from the faithful table.
- No dataset `FULL_PROTOCOL_REPRODUCED`. BinAlpha 26×30 is UNVERIFIED. AR Zenodo not downloaded. MSRA50 missing. UMIST 565≠564.

## Extra dataset versions (default loaders unchanged)

`load_dataset("ORL")` still returns Olivetti 64×64 → 32×32. `load_dataset("YaleB")` still returns Deng Cai `YaleB_32x32.mat`. `load_dataset("UMIST"|"AR"|"BinAlpha"|"MSRA50")` still raises `DatasetUnavailable`.

| Extra `version=` | What it is | What it is not |
| --- | --- | --- |
| `ORL` `att92` (also `att92_nearest`, `att92_bicubic`) | Cambridge AT&T 92×112, 400 images, resized to 32×32 | not the silent default |
| `YaleB` `cropped2414` | Wayback CroppedYale, 2414 non-ambient 192×168 images | not claimed pixel-identical to Deng Cai |
| `UMIST` `precropped575` / `figshare575` | 575 cropped 112×92 images | **not** the paper's 564 |
| `BinAlpha` `letters26x30_seed0` | 780-letter reconstruction, seed 0 | **UNVERIFIED**; default name still unavailable |

See `docs/round2_source_of_truth.md`.

## Layout

```text
SSC_method/           original SSC only (E8 / E13 variants)
baselines/            K-means, SC, PCA-*, LDA-*, LLC; SPLS raises NotImplementedError
benchmarks/           loaders, manifests, ACC/NMI; raw images gitignored
method_extension/     mutual-kNN W on F (RSSC); not mixed into SSC_method/
experiments/          runner helpers, aggregation, paper-reported tables (labelled as such)
scripts/              download, run_experiment, round2 runners, tables, validate
runs/                 Phase 1 jobs
runs/repair_round1/   repair-round jobs
runs/round2/          Round 2 D1–D12 jobs
results/round2/       registry, shared-F JSON, K-means-on-F JSON
report/               NeurIPS 2026 preprint LaTeX → main.pdf and Group_23.pdf (no checklist)
docs/                 round2 source-of-truth, matrix, root-cause, recovery log
tests/                unit tests (synthetic data unless a loader test needs a local file)
```

## Install

Python 3.13.3 was used (see `environment/README.md`). From this `v1` directory:

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest
```

`pyproject.toml` puts the repo root on `pythonpath`, so an editable install is optional. Optional `cvxpy` is only for an independent convex-solver check; tests skip it if missing.

## Datasets and licensing

Download (skips files whose SHA-256 already matches):

```bash
python3 scripts/download_datasets.py
```

| Dataset | Default status | Notes |
| --- | --- | --- |
| ORL | approximate | Olivetti 64×64 → 32×32; extra `att92` is 92×112 |
| JAFFE | verified | Zenodo TIFF; **research only, no redistribution**; zip must not be committed |
| YaleB | approximate | Deng Cai `YaleB_32x32.mat`; extra `cropped2414` from Wayback |
| USPS | verified | LIBSVM 16×16, 9298 samples |
| AR | unavailable | official hosts failed; unofficial Zenodo zip was **not** downloaded |
| BinAlpha | parent obtained; paper set UNVERIFIED | default still `DatasetUnavailable`; `letters26x30_seed0` is not the paper set |
| MSRA50 | unavailable | no 1799×12 file; other MSRA corpora were not renamed |
| UMIST | unavailable at 564 | extra 1012/575 archives; 565 unique cropped pixels ≠ 564 |

Raw archives live under `benchmarks/<name>/data/` and are gitignored. Manifests and checksums **are** committed. JAFFE forbids redistribution, including via git.

## Reproduction commands actually used

From this `v1` root, with datasets already on disk:

```bash
# historical Phase 1 (already recorded under runs/)
python3 scripts/run_all_stages.py --stages A,B,C,D,USPS

# repair round 1 (already recorded under runs/repair_round1/)
python3 scripts/run_repair_round1_orl.py
python3 scripts/run_repair_round1_transfer.py

# round 2 diagnostics (already recorded under runs/round2/)
python3 scripts/run_round2_diagnostics.py
python3 scripts/validate_reproducibility_docs.py

# rebuild Phase 1 tables/figures from runs/ (no new clustering)
python3 scripts/generate_report_tables.py
python3 scripts/generate_report_figures.py

# report (four-page main text)
cd report && latexmk -pdf -interaction=nonstopmode main.tex
```

Round 2 comparison tables live in `results/round2/` and `report/tables/round2_main.tex`. Re-running the full campaign is not required to inspect numbers.

## Limitations

Documented in `docs/round2_root_cause_analysis.md` and report Sections 4–5. Short version: E8 vs E13 factor of two; median bandwidth; \(G_0=F\); SPLS missing; AR not downloaded; BinAlpha UNVERIFIED; MSRA50 missing; UMIST not 564; YaleB 10 trials; USPS 3 trials; shrinkage did not help; extension did not help; att92 E8 57.3 is not the published 76.0; \(k\)-means++ 78.3 is B, not a reproduction.

## Report

`report/main.pdf` and `report/Group_23.pdf` (identical copies after `latexmk`). Style: `\usepackage[preprint]{neurips_2026}`. Main text ends on page 4. The NeurIPS checklist is not included.
