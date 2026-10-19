# Reproducibility guide

This is the course reimplementation of Chang et al., AAAI 2015, on branch `v1`. Numbers in `results/` come from `runs/`. Paper percentages stay labelled as reported by Chang et al. and are never copied into Our Reproduction cells.

## Environment

Recorded on 2026-10-20:

- Python 3.13.3 (`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`)
- numpy 2.4.2, scipy 1.17.1, scikit-learn 1.8.0, pandas 2.3.3, matplotlib 3.10.8, PyYAML 6.0.3, pytest 9.1.1
- Optional: cvxpy 1.9.3 + CLARABEL for the synthetic convex check
- 8 CPU cores, 16 GB RAM, no GPU
- `pdflatex` / `latexmk` for the report

Install from the `v1` root:

```bash
python3 -m pip install -r requirements.txt
```

Do not use the Anaconda Python on the course machine: its scikit-learn was binary-incompatible with the system numpy.

## Data

```bash
python3 scripts/download_datasets.py
```

Checksums are in each `benchmarks/<dataset>/manifest.yaml` and in `scripts/download_datasets.py`. Files that already match are left in place.

JAFFE: non-commercial research only; redistribution forbidden. The official Zenodo URL returned HTTP 403 to curl on 2026-10-20; a browser download of the same URL matched SHA-256 `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`. The zip is gitignored.

AR, UMIST, BinAlpha, and MSRA50 were not obtained. Loaders raise `DatasetUnavailable`. Binary Alphadigits and other MSRA collections were not renamed to fill those slots.

## What the solver actually does

See `docs/ssc_mathematical_audit.md` and `SSC_method/README.md`. Locked choices:

- Solve Equation (13), not Algorithm 1 line 10.
- Row-wise $n\times n$ $S$, not the printed embedding-dimension diagonal.
- $G_0=F$; median kNN bandwidth; $k=5$ unless a job says otherwise.
- IRLS `tol=1e-6`, `max_iter=300` in the campaign (the library default is 100).
- Labels only for ACC/NMI (Hungarian ACC; geometric-mean NMI).

## Re-running jobs

One config:

```bash
python3 scripts/run_experiment.py --config path/to.yaml
```

The orchestrator used for Phase 1:

```bash
python3 scripts/run_all_stages.py --stages A,B,C,D,USPS
```

`--dry-run` prints jobs without executing. Equivalent completed runs are skipped by `_equivalent_completed`. Do not invent extra USPS or YaleB trials if a job times out; leave the directory as TIMEOUT/INCOMPLETE/SKIPPED.

Track A selects the setting with the highest mean ACC (labels used). Track B freezes $\gamma=1$ and `min(50, n_clusters, n-1, d)` (LDA: $K-1$).

## Regenerating tables, figures, and the PDF

```bash
python3 scripts/generate_report_tables.py
python3 scripts/generate_report_figures.py
cd report && latexmk -pdf -interaction=nonstopmode main.tex
```

`generate_report_tables.py` writes `results/tables/*.md|csv` and `report/tables/*.tex`. `generate_report_figures.py` writes `results/figures/` and copies PDF/PNG into `report/figures/`.

## Validation

```bash
python3 scripts/validate_project.py
```

The script records real pass/fail/skip outcomes in `docs/validation_report.md`. It does not invent checks.

## What was and was not a 50-run protocol

| Setting | Completed trials |
| --- | --- |
| ORL / JAFFE Track A K-means, SC, SSC, LLC | 50 |
| ORL / JAFFE PCA-KM Track A | 50 |
| ORL / JAFFE PCA-SC and LDA-KM Track A | 10 (triage) |
| YaleB K-means, SC, SSC | 10 |
| USPS K-means | 10 |
| USPS SSC | 1 |
| Robustness EX2–EX4 | 20 trials × 3 perturbation seeds |
| Robustness EX5 | 20 trials × 2 seeds |
| $k$ sweep EX6 | 20 |

SPLS jobs are SKIPPED. One Track A LDA-KM ORL dim=20 job FAILED and was rerun to completion; the FAILED directory was kept.
