# Preliminary report validation

This is a preliminary layout check, not the final campaign or publication check.
New baseline/subset results were still being produced. Pending aggregation is
shown as unavailable; implementation checks are not substituted for measurements.

- Source generation: `python -m experiments.submission_refresh.reporting --date 2026-11-10`.
- Build: `make -C report all` using NeurIPS 2026 preprint style, pdflatex and BibTeX.
- The generated input manifest records every CSV/JSON input hash and availability.
- Main-text end label: page 4. Total preliminary PDF:13 pages.
- Latest checked PDF SHA-256: `5db5133444002788e070d136de20391b660783d3bb3f5298dac522f29f28c685`.
- Four confirmed authors and HKU affiliation are present. The two-graph diagram is preserved.
- No overfull boxes, undefined citations or undefined references remain in the final LaTeX log.
- All13 pages were rendered with Poppler and inspected individually. No clipped text,
  overlapping cells, unreadable tables, broken symbols or missing citations were found.
- Report metadata includes the exact title and all four authors.
- Three endpoint/provenance regression checks passed; native-best assignments never receive mean-endpoint SD.
- Figure generation uses only complete committed result rows; outlines refer to already locked winners.

`make` now regenerates refresh tables from authoritative current CSV/JSON records
before compiling. `PYTHON` and `REPORT_DATE` are explicit overridable variables.
The root campaign must regenerate after final aggregation and inspect the final
rendered PDF again; this preliminary hash does not certify a later version.
