# COMP3314 Group 23 — Spectral Shrunk Clustering (v1, repair round 1)

HKU COMP3314 Machine Learning course project. **Branch: `v1`.**

This directory is a from-scratch reimplementation of Chang, Nie, Ma, Yang, and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015 ([doi:10.1609/aaai.v29i1.9606](https://doi.org/10.1609/aaai.v29i1.9606)). There is no official author code. The written report uses the NeurIPS 2026 LaTeX style with the **preprint** option and is a course report, not a NeurIPS submission.

Intended GitHub remote: [https://github.com/SelinaMai-SYM/COMP-3314-G23.git](https://github.com/SelinaMai-SYM/COMP-3314-G23.git), branch `v1` only.

Group membership, names, and emails require confirmation and are not invented here.

## Provenance (keep these distinct)

| Piece | Who |
| --- | --- |
| Original method (Eq. 4 embedding, Eq. 8 objective, printed Eq. 13 update, \(K\)-means on `G`) | Chang et al., AAAI 2015 |
| This reimplementation (`SSC_method/`) | this course project. Variant **E8** (`A=S+2γL̃`) is the faithful stationary point of printed Eq. 8. Variant **E13** (`A=S+γL̃`) is the printed update (default). Algorithm 1 line 10 is not executed |
| Repair round 1 | configurable E8/E13, ORL one-factor diagnostics, dataset recovery, Track-B-style shortlists, four-page report. Records under `runs/repair_round1/` and `results/repair_round1/` |
| Experiment protocol, historical Track A / Track B | this course project; historical `runs/` were not deleted |
| Mutual-kNN shrinkage graph (`method_extension/`) | adaptation of an established graph to SSC; Category C; not a new theorem; negative/neutral |
| Datasets | third-party (AT&T/ORL, JAFFE, Extended Yale B, LIBSVM USPS, and extra UMIST archives that are **not** 564 images). AR, BinAlpha, and MSRA50 were not obtained |
| Libraries | NumPy, SciPy, scikit-learn, matplotlib, PyYAML; optional CVXPY for the convex audit |

Paper table numbers are labelled **Reported in Chang et al. (2015)**. Numbers in `results/` are **Our Reproduction** from `runs/`. They are not copies of the paper. Category C (row-normalized eigenvectors, mutual kNN, \(K\)-means on `F`) is never called the paper method.

## Honest headline results (repair round 1)

- **Shrinkage did not help.** \(K\)-means(`F`) vs E13 \(K\)-means(`G`): ORL 53.9 vs 53.7 (n=50); JAFFE 68.5 vs 68.6 (n=50); YaleB 20.1 vs 19.7 (n=10).
- **ORL 76% was not reproduced.** Faithful E8 ACC **53.3 ± 3.2 (n=50)** vs paper **76.0 ± 1.6**.
- Most faithful reconstruction: E8 (A). Numerically closest A/B reconstruction is **not** the same object (ORL/YaleB: \(k\)-means++, B; JAFFE: E13, B; USPS: E13 n=3).
- YaleB SSC: **n=10**, not 50. USPS SSC repair-round pilot: **n=3**, not 50.
- Mutual-kNN extension: negative / neutral, not a win.
- SPLS: `NOT_IMPLEMENTED`. LDA-SC: approximate, omitted from the faithful table.
- Unavailable at paper counts: AR, BinAlpha, MSRA50. UMIST files on disk are 1012 or 575 images, not 564.

## Extra dataset versions (default loaders unchanged)

`load_dataset("ORL")` still returns Olivetti 64×64 → 32×32. `load_dataset("YaleB")` still returns Deng Cai `YaleB_32x32.mat`. `load_dataset("UMIST"|"AR"|"BinAlpha"|"MSRA50")` still raises `DatasetUnavailable`.

| Extra `version=` | What it is | What it is not |
| --- | --- | --- |
| `ORL` `att92` (also `att92_nearest`, `att92_bicubic`) | Cambridge AT&T 92×112, 400 images, resized to 32×32 | not the silent default |
| `YaleB` `cropped2414` | Wayback CroppedYale, 2414 non-ambient 192×168 images | not claimed pixel-identical to Deng Cai |
| `UMIST` `precropped575` / `figshare575` | 575 cropped 112×92 images | **not** the paper's 564 |

See `docs/repair_round1_dataset_recovery.md`.

## Layout

```text
SSC_method/           original SSC only (E8 / E13 variants)
baselines/            K-means, SC, PCA-*, LDA-*, LLC; SPLS raises NotImplementedError
benchmarks/           loaders, manifests, ACC/NMI; raw images gitignored
method_extension/     mutual-kNN W on F (RSSC); not mixed into SSC_method/
experiments/          runner helpers, aggregation, paper-reported tables (labelled as such)
scripts/              download, run_experiment, repair_round1 runners, tables, validate
runs/                 Phase 1 jobs
runs/repair_round1/   repair-round jobs (YYYYMMDD_HHMMSS__REPAIR1__...)
results/repair_round1/  registry, gap table, comparison tex
report/               NeurIPS 2026 preprint LaTeX → main.pdf and Group_23.pdf
docs/                 audits, recovery log, issue tracker, this-round validation
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
| AR, BinAlpha, MSRA50 | unavailable | loaders raise `DatasetUnavailable`; no substitutes |
| UMIST | unavailable at 564 | extra 1012/575 archives are not the paper set |

Raw archives live under `benchmarks/<name>/data/` and are gitignored. Manifests and checksums **are** committed. JAFFE forbids redistribution, including via git.

## Reproduction commands actually used

From this `v1` root, with datasets already on disk:

```bash
# historical Phase 1 (already recorded under runs/)
python3 scripts/run_all_stages.py --stages A,B,C,D,USPS

# repair round 1 (already recorded under runs/repair_round1/)
python3 scripts/run_repair_round1_orl.py
python3 scripts/run_repair_round1_transfer.py

# rebuild Phase 1 tables/figures from runs/ (no new clustering)
python3 scripts/generate_report_tables.py
python3 scripts/generate_report_figures.py

# report (four-page main text)
cd report && latexmk -pdf -interaction=nonstopmode main.tex
```

Repair-round comparison tables live in `results/repair_round1/` and `report/tables/repair_round1_main.tex`. Re-running the full campaign is not required to inspect numbers.

## Limitations

Documented in `docs/repair_round1_issue_tracker.md`, `docs/repair_round1_closest_reconstruction.md`, and report Sections 4–5. Short version: E8 vs E13 factor of two; median bandwidth; \(G_0=F\); SPLS missing; AR/BinAlpha/MSRA50 missing; UMIST not 564; YaleB 10 trials; USPS 3 trials; shrinkage did not help; extension did not help; ORL 76% not reproduced.

## Report

`report/main.pdf` and `report/Group_23.pdf` (identical copies after `latexmk`). Style: `\usepackage[preprint]{neurips_2026}`. Main text ends on page 4; see `docs/repair_round1_validation.md`.
