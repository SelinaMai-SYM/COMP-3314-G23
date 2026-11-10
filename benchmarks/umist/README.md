# UMIST / Sheffield face datasets

Chang et al. report 564 images of twenty people without specifying a resize or
sample indices. The available UMIST sources differ in row count, pixels and
resolution. Strict `load_dataset("UMIST")` raises `DatasetUnavailable`; explicit
versions and subset hypotheses retain their own identities.

## Source versions

| Version | Rows / features | Scientific qualification |
|---|---:|---|
| Default / `sheffield564` | Unavailable | Historical 564-image membership unresolved |
| `lzuf574` | 574 / 10304 | Ten extra exact duplicate rows; first-occurrence dedup564 is a hypothesis |
| `precropped575` | 575 / 10304 | Archived cropped source, native 112×92; 565 distinct pixel rows |
| `figshare575` / `roweis575` | 575 / 10304 | Identical MAT-file bytes; pixels differ from the archived cropped source |
| `zenodo3634017` | 575 / 644 | Separate native 28×23 matrix |
| `uncropped1012` | No rectangular matrix | 122 spatial shapes; no undeclared resize |

The original database is attributed to Graham and Allinson (1998). The
[archived source description](resources/README.md) says 564 images, but that
statement does not identify a 564-row selection from the available archives.

## Files and pinned row rules

Paths below are beneath `umist/data` in the independent data root.

| File | Expected SHA-256 / role |
|---|---|
| `private/lzuf_umist.mat` | `b66a95533e77a90310bc6119c219bc96e6ad8e343e50e0db0f5e740402d50d92` |
| `wayback_sheffield/cropped_wayback_20070805.tar.gz` | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` |
| `wayback_sheffield/face_wayback_20050403.tar.gz` | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` |
| `figshare_umist_cropped/umist_cropped.mat` | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` |
| `private/roweis_umist_cropped.mat` | Same SHA-256 as the Figshare MAT; an alias, not independent evidence |
| `private/zenodo3634017_umist.mat` | Separate 28×23 source; identity retained in the source inventory |

Provider references are [LZUFE](https://raw.githubusercontent.com/LZUFE-Machine-Learning/Datasets/main/umist.mat),
[archived cropped images](https://web.archive.org/web/20070805190146id_/http://images.ee.umist.ac.uk/danny/cropped.tar.gz),
[Figshare](https://ndownloader.figshare.com/files/67153214),
[Roweis](https://cs.nyu.edu/home/people/in_memoriam/roweis/data/umist_cropped.mat)
and [Zenodo 3634017](https://zenodo.org/records/3634017).

The LZUFE source preserves matrix row order. Exact first-occurrence
deduplication retains 564 rows and records the full original-to-retained mapping;
this is not evidence that the SSC authors deduplicated that source.

The cropped archive contains 575 distinct filenames. Ten exact duplicate pairs
are in `1b/face`: `1b014.pgm=final00.pgm`, `1b016=final01`, `1b024=final02`,
`1b032=final03`, `1b038=final04`, `1b040=final05`, `1b048=final06`,
`1b056=final07`, `1b064=final08`, `1b072=final09`. Removing those copies leaves
565, not 564. Each single-omission candidate therefore records an explicitly
unknown omitted row. The uncropped archive contains 1,013 PGM members with
1,012 distinct names (`1t/1t052.pgm` is repeated) and is not stacked without
another declared spatial transformation.

Figshare/Roweis MATLAB cells are traversed by stored person order, then the last
image axis; labels are 0–19. Their pixels are distinct from the archived cropped
source, even after transposition. Raw source versions retain every row;
deduplication, omission and stratified subsets are separately named in the
[catalogue](../../configs/subset_search/candidate_catalogue.json).

## Loading and preparation

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset(
    "UMIST", root=Path("/path/to/benchmarks/umist/data"), version="lzuf574"
)
```

The named MAT versions read their files directly. For `precropped575`, the loader
requires `wayback_sheffield/processed/umist_precropped575_uint8.npy` with shape
`(575,112,92)` and `umist_precropped575_labels_int64.npy`. Its deterministic
preparation reads all PGM members from the pinned cropped archive, sorts archive
member names, retains every image in that order and assigns labels by canonical
person-directory order `1a..1t`. Save native uint8 images and integer labels;
the loader divides by 255 and vectorizes in C order, without resizing. The
shared `benchmarks.prepare` command is for ORL/YaleB, not UMIST.

The [Wayback manifest](manifest_wayback.yaml), [Figshare manifest](manifest_figshare_cropped.yaml)
and [source inventory](../../results/subset_search/source_inventory.csv) retain
checksums and source qualifications. Each changed subset rebuilds A/F/W/G rather
than selecting rows of a parent embedding.

## Terms

The original page permits publishing subject 1a only with written permission.
The Figshare mirror lists CC BY 4.0 for its copy; that is not an original Graham
release license. Keep raw images outside Git and retain Graham/Allinson
attribution. See [data terms](../../docs/data.md) and
[scientific limitations](../../docs/limitations.md).
