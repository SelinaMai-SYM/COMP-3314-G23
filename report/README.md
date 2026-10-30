# COMP3314 course report (NeurIPS 2026 preprint style)

This directory is the written report for HKU COMP3314 Group 23. It uses the official NeurIPS 2026 style with the **preprint** option. It is a course project, not a NeurIPS submission.

## Compile

From this `report/` directory:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

Equivalent one-shot sequence if `latexmk` is unavailable:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The expected PDFs are `main.pdf` and an identical copy `Group_23.pdf`.

Main text (title through conclusion, including the abstract) must fit in **four pages**. References and appendix are excluded from that cap. **Do not include the NeurIPS checklist** (`\input{checklist.tex}` is not used). Do not edit `neurips_2026.sty` fonts, margins, or spacing to squeeze. After `latexmk`, check with `pdfinfo`, `pdftotext -layout`, and `rg Overfull main.log`.

## Layout

- `main.tex` — body and appendix (no checklist)
- `references.bib` — verified BibTeX entries
- `neurips_2026.sty` — copied from the official NeurIPS 2026 bundle
- `tables/final_main.tex` — n=50 SC vs E8 γ=1 comparison from `results/strict_reproduction_matrix.csv`
- `tables/round2_main.tex` — Round 2 table (superseded; not used by `main.tex`)

Paper ACC/NMI stay in a column labelled as Chang et al. (2015), historical only. Our cells come from `results/strict_reproduction_matrix.csv` (n=50). Number sources: `docs/final_round/report_evidence_map.md`.
