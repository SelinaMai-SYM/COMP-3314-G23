# UMIST / Sheffield face datasets

**Current status, 2026-11-10:** the new campaign records an exact-first-occurrence
LZUFE dedup564 candidate, the Wayback565 single-omission family and declared
stratified draws. These hypotheses preserve their exact sample manifests; none
establishes which 564 images the SSC authors used. The strict
`load_dataset("UMIST")` default remains unavailable. See
[source recovery](../../docs/submission_refresh/source_recovery.md) and the
[candidate catalogue](../../configs/subset_search/candidate_catalogue.json).

## Identity and versions

Graham and Allinson (1998) describe the Sheffield/UMIST faces. The Wayback page
from 2001-04-05 states 564 images of 20 people, approximately 220x220, and links
`face.tar.gz` (about 29 MB) and `cropped.tar.gz` (about 4.5 MB). Chang et al.
state 564 images, 20 people and pixel features without specifying a resize or
a rule for obtaining 564 rows from a larger archive.

| Explicit version | Rows/features | Qualification |
|---|---:|---|
| Default / `sheffield564` | unavailable | Strict historical sample identity unresolved |
| `lzuf574` | 574/10304 | Ten extra exact duplicate rows; dedup564 is an explicit candidate |
| `precropped575` | 575/10304 | Wayback cropped archive, native 112x92, pixels 0-238 |
| `figshare575` / `roweis575` | 575/10304 | Byte-identical MAT source copies; distinct pixels from Wayback |
| `zenodo3634017` | 575/644 | Native 28x23 matrix; resolution kept separate |
| `uncropped1012` | unavailable as a matrix | 122 spatial shapes; no undeclared resizing |

The LZUFE parent is read through the independent root at
`umist/data/private/lzuf_umist.mat`; SHA256
`b66a95533e77a90310bc6119c219bc96e6ad8e343e50e0db0f5e740402d50d92`.
Its ten extra duplicate rows have consistent labels. First occurrences are
retained in canonical source order, and the inverse row mapping is saved.
Matching 564 rows and 20 identities is not evidence that the authors applied
that deduplication.

## Archived files and duplicate audit

| File relative to UMIST data | Bytes | SHA256 |
|---|---:|---|
| `wayback_sheffield/face_wayback_20050403.tar.gz` | 29385054 | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` |
| `wayback_sheffield/cropped_wayback_20070805.tar.gz` | 4506480 | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` |
| `figshare_umist_cropped/umist_cropped.mat` | 5927440 | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` |

The cropped archive has 575 distinct filenames, including distinct basenames,
and 565 distinct pixel arrays. Ten exact duplicate pairs are all in `1b/face/`:
`1b014.pgm=final00.pgm`, `1b016=final01`, `1b024=final02`, `1b032=final03`,
`1b038=final04`, `1b040=final05`, `1b048=final06`, `1b056=final07`,
`1b064=final08`, `1b072=final09`.
Removing those ten `final*.pgm` copies leaves 565 images, not 564. Every
one-omission hypothesis is therefore labelled as an unknown omission.

The uncropped archive contains 1,013 PGM members with 1,012 distinct names;
`1t/1t052.pgm` occurs twice. Figshare has the same class-count distribution as
the cropped tar, but its pixel-hash intersection with Wayback is zero, even
after transposition. The Roweis MAT is byte-identical to Figshare, rather than
an independent release. Zenodo 3634017's measured MD5 is
`039e0d805a5c65df7bfecd172a24f14c`.

The 2001 page permits publication of subject 1a only with written permission.
The Figshare API lists CC BY 4.0 for its MAT copy; that is not a license statement
from the original Graham release. Raw images stay outside Git.

## Loading and checks

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("UMIST", root=Path("/path/to/benchmarks/umist/data"),
                             version="precropped575")
assert X.shape == (575, 10304)
assert metadata["unique_pixel_arrays"] == 565
```

The explicit cropped loader retains all 575 images, divides by 255 and does not
resize. Run `python -m pytest benchmarks/umist/test_umist.py` and the candidate
replay checks. The strict default remains unavailable, and the cropped metadata
retains `not_exact_564`.

## Historical recovery notes (2026-10-21)

Phase 1, repair_round1 and Round 2 ran no UMIST clustering jobs. At that time no
new 564-row reconstruction was authorized and images were not removed merely
to force the count. Those dated decisions do not describe the current explicit
candidate campaign. Earlier v3 notes retained LZUFE574 without deduplication;
new dedup564 results have distinct manifests and run identities.

On 2026-10-21, Lincoln `face.tar.gz` returned HTTP 202 through a WAF,
`images.ee.umist.ac.uk` returned 502 and the Sheffield page returned 404.
Existing archives were not downloaded again. The Wayback 2001 page was saved
as `resources/database_wayback_20010405.html`, 3,878 bytes, SHA256
`a8a91fbea393f524e3275acad9356512145547217c18f446eb08eae849cb263a`,
from a successful `id_` GET. It states 564 even though the corresponding saved
cropped archive contains 575 PGM files. A later strict Roweis GET returned 200,
5,927,440 bytes and the same hash as Figshare. Distinct byte arrays and distinct
pixel arrays both numbered 565 for the Wayback archive. Historical identity
remained `CANDIDATE_ONLY`, rather than recovered.

See [Round 2](../../docs/round2_source_of_truth.md), [the base manifest](manifest.yaml),
[Wayback](manifest_wayback.yaml) and [Figshare](manifest_figshare_cropped.yaml).
Older v1/v2 measurements remain historical; LLC results predating the Procrustes
correction retain the `PRE_FIX_LEGACY` qualification.
