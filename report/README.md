# Project report

**Spectral Shrunk Clustering: Reproduction, Numerical Audits, and Subset
Uncertainty**

Han Jiale, Lu Sinan, Mahatharadol Vie and Mai Sheung Ying — Group 23,
The University of Hong Kong, COMP3314 Machine Learning.

The [report PDF](Group_23.pdf) presents the SSC formulation, historical paper
reconstruction, numerical certificates, baseline comparisons and graph mechanism
experiments. Final source/subset matches and locked-selection rounding are
explicitly reserved, without partial winners. The NeurIPS 2026 preprint format has at most four main-text
pages; references and the detailed scientific appendix are separate. The appendix
contains full endpoint/coverage qualifications rather than treating unavailable
results as zeros.

## Build

From the checkout root, after installing the
[pinned Python dependencies](../environment/requirements.lock.txt):

```bash
make -C report
```

The build requires `make`, Bash, TeX Live with `pdflatex`, BibTeX, `standalone`,
TikZ and AMS math, plus Poppler's `pdftocairo` for figure conversion. It regenerates
tables from the historical and completed flat scalar records and writes
`report/Group_23.pdf`. Raw image
archives and model fitting are not required.

`PYTHON` selects the interpreter; `REPORT_DATE` controls the generated metadata
date. The table generator supports direct script invocation and loads its CSV
transport helper from the same checkout. A logical CSV can be supplied as its
sole gzip representation; ambiguous plain/gzip duplicates are rejected.

## Editable diagram and result sources

The diagram source is [ssc_two_graph_pipeline.tikz](figures/ssc_two_graph_pipeline.tikz),
with a standalone wrapper beside it. Rebuild its PDF/SVG/PNG exports with:

```bash
bash scripts/build_ssc_pipeline.sh
```

The input graph A and shrinkage graph W retain their distinct roles in both the
diagram and code. Generated report tables share the authoritative records used
by the [combined benchmark tables](../results/submission_refresh/per_benchmark/).
Final subset/scientific-archive rebuild interfaces require the corresponding
published final manifests; see [release availability](../docs/reproducibility.md#final-release-interfaces).
See [methods](../docs/methods.md), [experimental protocol](../docs/experimental_protocol.md),
[data](../docs/data.md), [reproducibility](../docs/reproducibility.md),
[results](../docs/results.md) and [limitations](../docs/limitations.md).
