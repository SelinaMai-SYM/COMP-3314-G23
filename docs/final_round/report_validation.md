# Report compile validation

Compiled from `report/main.tex` with `latexmk -pdf -interaction=nonstopmode` in `report/` on 2026-11-01. Style: `\usepackage[preprint]{neurips_2026}`. `neurips_2026.sty` was not edited. `checklist.tex` is on disk and is **not** `\input`.

## PDF identity

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `report/main.pdf` | 225660 | `3dfe349b87987bc35c6e4f363a43c9f9d4ef9829fde9fcf3dab9c8bb2ac5f5a2` |
| `report/Group_23.pdf` | 225660 | `3dfe349b87987bc35c6e4f363a43c9f9d4ef9829fde9fcf3dab9c8bb2ac5f5a2` |

`cmp` reports the two files identical. `Group_23.pdf` is a byte copy of `main.pdf`.

## Page count (`pdfinfo`)

- Pages: **5** (letter, 612 × 792 pts)
- Main text (title through Section 6 Reproduction): **pages 1–3**
- References start on page 4 and continue onto page 5
- No acknowledgments environment
- No appendix
- No NeurIPS checklist pages

`pdftotext -layout -f 3 -l 3` ends with the last paragraph of Section 6 (`The project is not marked fully reproduced.`). `pdftotext -layout -f 4 -l 5` is bibliography only. `pdftotext` of the whole PDF has no `NeurIPS Paper Checklist` and no `answerYes`.

## Overfull / Underfull

`rg Overfull main.log`: **no matches**.

`rg Underfull main.log`: one `Underfull \vbox (badness 10000)` on page 3, after the last main-text paragraph and before references begin on page 4. Not an Overfull hbox.

## Title, authors, and six sections

- Title: A Paper Study of Spectral Shrunk Clustering
- Authors: Group 23, Department of Computer Science, The University of Hong Kong, COMP3314 Machine Learning
- Names and emails: not invented; footnote says they require confirmation
- Footer: Preprint (neurips_2026 preprint option)
- Sections: (1) Problem formulation, motivation, and contributions; (2) Methods, algorithms, and course connections; (3) Experimental setup and results reported in the paper; (4) Critical analysis; (5) Insights and proposed extension; (6) Reproduction

## Main table

`report/tables/final_main.tex`, sourced from `results/strict_reproduction_matrix.csv` n = 50 cells. Mapping: `docs/final_round/report_evidence_map.md`.

| Set | Our SC ACC | Our E8 γ=1 ACC | Paper SC / SSC (historical) |
| --- | --- | --- | --- |
| ORL att92 | 56.2 ± 4.2 | 57.3 ± 3.8 | 72.7 ± 2.3 / 76.0 ± 1.6 |
| JAFFE zenodo | 68.5 ± 11.2 | 68.4 ± 11.1 | 76.1 ± 1.6 / 81.2 ± 1.6 |
| YaleB cropped2414 | 18.3 ± 1.3 | 17.6 ± 1.2 | 34.8 ± 1.4 / 49.8 ± 1.6 |
| USPS libsvm | 61.7 ± 8.1 | 61.7 ± 8.1 | 64.3 ± 1.4 / 75.5 ± 1.9 |

Trial count in every Our cell: n = 50. SPLS, LDA-SC, k-means++, row-norm, AR, UMIST-564, MSRA50 are not in the table.

## Constraints checked

- Did not `\input{checklist.tex}`
- Did not edit `neurips_2026.sty`
- Did not reset git; did not rewrite history
- Did not change `method_extension/` algorithms
- Did not rerun the 72-cell matrix
- Did not invent author names, emails, or extra digits
