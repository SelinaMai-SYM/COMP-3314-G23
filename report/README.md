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
