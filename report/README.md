# Report sources

Han Jiale, Lu Sinan, Mahatharadol Vie and Mai Sheung Ying — Group 23,
The University of Hong Kong, COMP3314 Machine Learning.

The maintained report consists of [Section 3](sec3_experimental_evidence.tex),
[Sections 4–7 and the deferred appendix](sec4-7.tex), and the shared
[bibliography](references.bib). The [section preview](sections_preview.pdf)
compiles these sources in NeurIPS preprint format, with numbering starting at 3.
It is a partial report; it does not include the final Overleaf abstract or
Sections 1–2. The complete report PDF is exported from the final Overleaf project.

## Compile the supplied sections

TeX Live with `pdflatex`, BibTeX, AMS math, `booktabs`, `graphicx`, `natbib`,
`hyperref` and `microtype` is required. From the repository root:

```bash
make -C report preview
```

The build reads the exact [presentation slide 6.2 image](../docs/figures/extension_pipeline_ppt_6_2.png)
from its canonical location. No benchmark data, fitting or Python table generation
is required to compile the supplied text.

## Integrate with Overleaf

Use the final Overleaf abstract and Sections 1–2 as `report/frontmatter.tex`,
without another document preamble or bibliography. Then run:

```bash
make -C report
```

[main.tex](main.tex) includes each supplied chapter once. Section 3 owns its
heading; Sections 4–7 follow it. A single shared bibliography precedes the
single `\PrintSSCAppendix` call. The appendix definition in `sec4-7.tex` is
deferred until that call. The complete build deliberately requires the final
front matter instead of substituting a superseded introduction.

The four-page limit applies to the complete main text. Its page count can be
checked only after integrating the final front matter; the preview's page count
is not a complete-report page count. The old full-report PDF is superseded.

See the [evidence map](../docs/report_evidence.md) for the precise records,
endpoints, cohort identities and generators behind the retained tables.

`tables/refresh_main.tex` is retained byte-for-byte as an input identity in the
earlier cohort lock. The current report driver does not include that historical
table; its role is provenance for the frozen selected inputs.
