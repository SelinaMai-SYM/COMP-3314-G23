# COMP3314 Group 23 — Spectral Shrunk Clustering (Phase 1)

HKU COMP3314 Machine Learning course project. **Branch: `v1`.**

This directory is a from-scratch reimplementation of Chang, Nie, Ma, Yang, and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015 ([doi:10.1609/aaai.v29i1.9606](https://doi.org/10.1609/aaai.v29i1.9606)). There is no official author code. The written report uses the NeurIPS 2026 LaTeX style with the **preprint** option and is a course report, not a NeurIPS submission.

Intended GitHub remote: [https://github.com/SelinaMai-SYM/COMP-3314-G23.git](https://github.com/SelinaMai-SYM/COMP-3314-G23.git), branch `v1` only.

Group membership, names, and emails require confirmation and are not invented here.

## Provenance (keep these distinct)

| Piece | Who |
| --- | --- |
| Original method (Eq. 4 embedding, Eq. 8 / Eq. 13 shrinkage, K-means on `G`) | Chang et al., AAAI 2015 |
| This reimplementation (`SSC_method/`) | this course project; Equation (13), not Algorithm 1 line 10 |
| Experiment protocol, Track A / Track B, aggregation | this course project |
| Mutual-kNN shrinkage graph (`method_extension/`) | adaptation of an established graph to SSC; not a new theorem |
| Datasets | third-party (AT&T/ORL, JAFFE, Extended Yale B, LIBSVM USPS). Four paper sets were not obtained |
| Libraries | NumPy, SciPy, scikit-learn, matplotlib, PyYAML |

Paper table numbers are labelled **Reported in Chang et al. (2015)**. Numbers in `results/` are **Our Reproduction** from `runs/`. They are not copies of the paper.

## Honest headline results

- ORL SSC Track A: **53.9 ± 3.0 (n=50)** vs paper **76.0**. SSC did **not** reproduce the paper's large ORL gain; it matches our SC baseline (54.2 ± 3.1).
- YaleB SSC: **19.7 ± 1.1 with n=10**, not 50.
- USPS SSC: **62.1 with n=1**, not 50.
- Mutual-kNN extension: mixed / negligible, not a win.
- SPLS: not implemented. LDA-SC: approximate, omitted from the main fair table.
- Unavailable: AR, UMIST, BinAlpha, MSRA50.

## Layout

```text
SSC_method/           original SSC only
baselines/            K-means, SC, PCA-*, LDA-*, LLC; SPLS raises NotImplementedError
benchmarks/           loaders, manifests, ACC/NMI; raw images gitignored
method_extension/     mutual-kNN W on F (RSSC); not mixed into SSC_method/
experiments/          runner helpers, aggregation, paper-reported tables (labelled as such)
scripts/              download, run_experiment, run_all_stages, tables, figures, validate
runs/                 one directory per job: config, metrics, status, logs
results/              generated tables/figures from runs/
report/               NeurIPS 2026 preprint LaTeX → main.pdf
docs/                 audit, deviations, literature, reproducibility, validation
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

| Dataset | Status | Notes |
| --- | --- | --- |
| ORL | approximate | scikit-learn Olivetti 64×64 → 32×32; not 92×112 originals |
| JAFFE | verified | Zenodo TIFF; **research only, no redistribution**; zip must not be committed |
| YaleB | approximate | Deng Cai `YaleB_32x32.mat`; official cropped PGM zips 404 |
| USPS | verified | LIBSVM 16×16, 9298 samples |
| AR, UMIST, BinAlpha, MSRA50 | unavailable | loaders raise `DatasetUnavailable`; no substitutes |

Raw archives live under `benchmarks/<name>/data/` and are gitignored. Manifests and checksums **are** committed. JAFFE forbids redistribution, including via git.

## Reproduction commands actually used

From this `v1` root, with datasets already on disk:

```bash
# single job
python3 scripts/run_experiment.py --config configs/generated/TRACKA__ssc__USPS__1p0__5________.yaml

# staged campaign (skips equivalent completed runs)
python3 scripts/run_all_stages.py --stages A,B,C,D,USPS

# rebuild tables/figures from runs/ (no new clustering)
python3 scripts/generate_report_tables.py
python3 scripts/generate_report_figures.py

# report
cd report && latexmk -pdf -interaction=nonstopmode main.tex

# checks (writes docs/validation_report.md)
python3 scripts/validate_project.py
```

Re-running the full campaign is not required to inspect numbers: every completed job is under `runs/` and is indexed in `results/run_index.csv`.

## Limitations

Documented in `docs/reproduction_deviations.md`, `docs/critical_analysis.md`, and report Section 9. Short version: Equation (13) vs printed Equation (8) ($\gamma/2$); median bandwidth assumption; $G_0=F$; SPLS missing; four datasets missing; YaleB 10 trials; USPS SSC 1 trial; extension did not help.

## Report

`report/main.pdf` (after `latexmk`). Style: `\usepackage[preprint]{neurips_2026}`.
