# Course report source

Run `make -C report` from the checkout root. It compiles the retained NeurIPS 2026 **preprint** template and copies the resulting PDF to `Group_23.pdf`. TeX Live/LaTeX with BibTeX is required; no publisher PDF, image dataset, old branch or external worktree is used.

Tables and figures are generated from committed scalar manifests and measured records:

```bash
python -m scripts.final.analyze_next_round
python -m scripts.final.build_delivery
python -m scripts.final.summarize_secondary
python -m scripts.final.plot_delivery
python -m scripts.final.finalize_records
make -C report
```

The resource-ledger timestamp/envelope is retained when the measured inputs are unchanged; it is an audit envelope, not a new experiment. Rebuilding numerical tables does not rerun fits. Main text ends at `main_end` and must remain at most four pages; references and appendices are excluded. The checklist and presentation outline are under `docs/final/`.

## Method flowchart

The authoritative editable drawing is `report/figures/ssc_two_graph_pipeline.tikz`; the adjacent `.tex` file only wraps it for standalone compilation. From the repository root:

```bash
bash scripts/build_ssc_pipeline.sh
make -C report
```

Requires Bash, TeX Live (`pdflatex`, `standalone`, TikZ, AMS math), and Poppler (`pdftocairo`). The script exports the report PDF and GitHub SVG/PNG from the same drawing; SVG glyphs are vector paths, so no viewer font installation is needed. The PDF is included at report text width (approximately 9 pt figure text, with 8 pt arrow labels).

For an isolated rebuild, pass a new output directory, for example `bash scripts/build_ssc_pipeline.sh /tmp/ssc-figure-check`. Only the output root changes; sources are resolved relative to the script, without data, caches, or another checkout. Exports appear under `report/figures/` (PDF) and `docs/figures/` (SVG and PNG) within that directory.

The diagram follows `spectral_embedding.py` (X to A, normalized Laplacian, c smallest eigenvectors), `ssc.py` (F to W, fixed F/W refinement, K-means on G), and `objective.py` (unsquared Equation 8 norms). The symmetric ordered-pair sum in code equals twice the undirected-edge sum in the figure. Row normalization remains a protocol choice; the existing E8/E13 discussion in the report still applies to historical solver outputs.
