# Report compile validation

Compiled from `report/main.tex` with `latexmk -pdf -interaction=nonstopmode` in `report/` on 2026-10-30. Style: `\usepackage[preprint]{neurips_2026}`. `neurips_2026.sty` was not edited. `checklist.tex` is on disk and is **not** `\input`.

## PDF identity

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `report/main.pdf` | 229264 | `c33304078bc4a8144d4630406e6fd0f420b9b34790910247973f905b5ae99853` |
| `report/Group_23.pdf` | 229264 | `c33304078bc4a8144d4630406e6fd0f420b9b34790910247973f905b5ae99853` |

`cmp` reports the two files identical. `Group_23.pdf` is a byte copy of `main.pdf`.

## Page count (`pdfinfo`)

- Pages: **5** (letter, 612 × 792 pts)
- Main text (title through Section 7 Conclusion): **pages 1–4**
- Acknowledgments start on page 4 after the conclusion
- References continue onto page 5
- No appendix
- No NeurIPS checklist pages

`pdftotext -layout -f 4 -l 4` begins with `7 Conclusion` and contains CONFIRMED / SUPPORTED / UNRESOLVED. Page 5 is remaining bibliography only. `pdftotext` of the whole PDF has no `NeurIPS Paper Checklist` and no `answerYes`.

## Overfull / Underfull

`rg Overfull main.log` and `rg Underfull main.log`: **no matches**.

## Title and authors

- Title: When Does Spectral Shrinkage Improve Clustering? A Reproduction and Failure Analysis of SSC
- Authors: Group 23, Department of Computer Science, The University of Hong Kong, COMP3314 Machine Learning
- Names and emails: not invented; footnote says they require confirmation
- Footer: Preprint (neurips_2026 preprint option)

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
