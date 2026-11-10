> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Round 2 source of truth (index)

Date: 2026-10-21; worktree then named `v1/`. This index does not duplicate full dataset tables. Package READMEs provide details, SHA-256 values, experiment attribution, and reproduction commands:

- [benchmarks/orl/README.md](../benchmarks/orl/README.md)
- [benchmarks/jaffe/README.md](../benchmarks/jaffe/README.md)
- [benchmarks/yaleb/README.md](../benchmarks/yaleb/README.md)
- [benchmarks/usps/README.md](../benchmarks/usps/README.md)
- [benchmarks/ar/README.md](../benchmarks/ar/README.md)
- [benchmarks/umist/README.md](../benchmarks/umist/README.md)
- [benchmarks/binalpha/README.md](../benchmarks/binalpha/README.md)
- [benchmarks/msra50/README.md](../benchmarks/msra50/README.md)

Full HTTP records: [round2_missing_resources.md](round2_missing_resources.md) and [round2_http_log.json](round2_http_log.json).

Checksums were recomputed locally on 2026-10-21 or calculated immediately after downloads. Existing archives were not overwritten. Default ORL/YaleB loaders, the SSC optimizer, and report were unchanged in this resource stage; no Git commit was made.

The eight README fidelity labels were used alongside the six dimensions below: NOT_FOUND / CANDIDATE_FOUND / DOWNLOADED_UNVERIFIED / SOURCE_VERIFIED / SAMPLE_SET_RECONSTRUCTED / PREPROCESSING_VERIFIED / PAPER_PROTOCOL_MATCHED / FULLY_REPRODUCED.

## Six dataset verification dimensions

Y=yes; N=no; P=partial (paper underspecified); R=reconstruction only; U=unverified identity.

| Dataset | SOURCE_FOUND | ARCHIVE_DOWNLOADED | CONTENTS_VERIFIED | SAMPLE_SET_MATCHED | PREPROCESSING_MATCHED | FULL_PROTOCOL_REPRODUCED | README assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORL att92 | Y | Y | Y | Y (400/40) | P (32x32; interpolation unspecified) | N | PREPROCESSING_VERIFIED |
| ORL default Olivetti | Y (different source) | Y | Y | Y (400/40) | N (64x64 differs from 92x112) | N | SOURCE_VERIFIED for MAT |
| JAFFE | Y | Y | Y | Y (213/10) | P (26x26 bilinear) | N | SOURCE_VERIFIED |
| YaleB cropped2414 | Y | Y | Y | Y (2414/38; Ambient removed) | P | N | SOURCE_VERIFIED |
| YaleB default Deng Cai | Y | Y | Y | Y (counts) | N (unknown resize kernel) | N | SOURCE_VERIFIED for MAT |
| USPS | Y | Y | Y | Y (9298/10) | P (release already 16x16) | N | SOURCE_VERIFIED |
| AR | N (official); Zenodo candidate rejected | N | N | N (840/120 unspecified) | N | N | NOT_FOUND |
| UMIST 564 | P (page says 564; files differ) | Y (1012/575) | Y (existing archives) | N | N | N | CANDIDATE_FOUND; unmatched membership |
| Paper BinAlpha | U | Y (parent) | Y (36x39x20x16) | R (26x30 seed0) | P (no parent resizing) | N | SAMPLE_SET_RECONSTRUCTED / UNVERIFIED |
| MSRA50 | P (bibliographic pointer; no URL) | N | N | N | N | N | CANDIDATE_FOUND -> NOT_FOUND |

No dataset reached FULL_PROTOCOL_REPRODUCED or PAPER_PROTOCOL_MATCHED.

## Recovery findings

- BinAlpha reconstruction existed: `version="letters26x30_seed0"`, 780 images, with indices in `benchmarks/binalpha/reconstructions/letters26x30_seed0.json`. The strict default remained unavailable; the 36-class parent was not the paper dataset.
- AR: Zenodo ARDB_Full.zip HEAD returned 200 and 120587997 bytes, but the uploader was unofficial and its CC-BY claim conflicted with official redistribution terms. It was not downloaded or used in this stage.
- MSRA50: the related Nie/Yang paper cited He et al. 2004 and listed 1799/12/1024. He ICCV 2003 / TPAMI 2005 described 12 people and 64-80 images per session without a 1799-row file. Other MSRA corpora were not substituted.
- UMIST: 575 cropped filenames were unique; ten pixel duplicate groups occurred among `1b/final*.pgm`. Deduplication gave 565, not 564. Eleven images were not arbitrarily deleted.

## Baseline fidelity

Evidence: `baselines/*/...py` and [repair_round1_baseline_audit.md](repair_round1_baseline_audit.md). No author binary was available, so no method was ORIGINAL_CODE_VERIFIED.

| Method | Label | Explanation |
| --- | --- | --- |
| K-means | PAPER_FAITHFUL_REIMPLEMENTATION | Lloyd, init=random; k-means++ is an explicit ambiguity reconstruction |
| SC | PAPER_FAITHFUL_REIMPLEMENTATION | Equation (4), k=5; no sklearn SpectralClustering; bandwidth/union support assumed |
| PCA-KM | PAPER_FAITHFUL_REIMPLEMENTATION | Centered, no default whitening; dimension increment 10 assumed |
| PCA-SC | PAPER_FAITHFUL_REIMPLEMENTATION | PCA followed by Equation (4) |
| LDA-KM | PAPER_FAITHFUL_REIMPLEMENTATION | Ding-Li alternation using pseudo-labels |
| LDA-SC | APPROXIMATE | Chang did not specify its loop; excluded from faithful main table |
| LLC | PAPER_FAITHFUL_REIMPLEMENTATION | Wu and Schölkopf; k=5 comparison protocol |
| SPLS/SLPS | NOT_IMPLEMENTED | Section 3 had not been obtained at this stage |

Round 1 results remained historical comparisons in `results/repair_round1/`.