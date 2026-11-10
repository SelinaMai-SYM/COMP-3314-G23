# UMIST / Sheffield

> English editorial replacement of the frozen historical source snapshot.
> These dated source findings do not describe subsequent candidate experiments.
> The strict original identity remains distinct from a later reconstruction.

The 2001 Sheffield/UMIST page states 564 images of 20 people, but the recovered
archives do not contain 564 images. They are verified as Wayback/Figshare sources,
not as the SSC paper's exact sample set. The default `load_dataset("UMIST")`
raises `DatasetUnavailable`; no complete numerical reproduction is claimed.

Graham and Allinson (1998) describe the source. The Wayback 2001-04-05 page lists
approximately 220x220 PGM images and links `face.tar.gz` (about 29 MB) and
`cropped.tar.gz` (about 4.5 MB). Chang et al. specify 564 images, 20 people and
pixel features without a resize size or a rule for choosing 564 rows. Eleven
arbitrary images were not removed merely to reach the count.

| Saved file | Bytes | SHA256 |
|---|---:|---|
| `data/wayback_sheffield/face_wayback_20050403.tar.gz` |29385054|`df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb`|
| `data/wayback_sheffield/cropped_wayback_20070805.tar.gz` |4506480|`c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4`|
| `data/figshare_umist_cropped/umist_cropped.mat` |5927440|`ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361`|

On 2026-10-21 Lincoln's archive request returned 202 through a WAF, live UMIST
returned 502 and Sheffield's page returned 404. Existing archives were not
downloaded again. The 2001 page restricts publication to subject 1a with written
permission. Figshare lists CC BY 4.0 for its MAT copy, not Graham's release.

| Version | Rows | Meaning |
|---|---:|---|
| Default / `sheffield564` |unavailable|Strict historical sample set unresolved|
| `precropped575` |575|Native 112x92, pixels 0-238, divided by255 without resizing|
| `figshare575` |575|Same class counts as Wayback, distinct pixel arrays|
| `uncropped1012` |unavailable as matrix|122 spatial shapes|

The cropped tar contains 575 distinct PGM filenames, also distinct basenames,
and 565 distinct pixel arrays. Ten exact pairs are all in `1b/face/`:
`1b014.pgm=final00.pgm`, `1b016=final01`, `1b024=final02`, `1b032=final03`,
`1b038=final04`, `1b040=final05`, `1b048=final06`, `1b056=final07`,
`1b064=final08`, `1b072=final09`. Removing ten `final*.pgm` copies yields 565,
not 564. No evidence identified a further omitted image, so no 564 reconstruction
was created in that historical round. The uncropped tar contains 1,013 PGM
members with 1,012 unique names: `1t/1t052.pgm` occurs twice.

Figshare and Wayback pixel hashes have zero intersection, including after
transposition. The later Roweis download at
`https://cs.nyu.edu/home/people/in_memoriam/roweis/data/umist_cropped.mat`
returned 200 and 5,927,440 bytes, byte-identical to Figshare. For Wayback,
distinct file bytes and distinct pixels both number 565. No eleven-image
deletion was performed to force 564.

The Wayback 2001 page was saved as `resources/database_wayback_20010405.html`,
3,878 bytes, SHA256
`a8a91fbea393f524e3275acad9356512145547217c18f446eb08eae849cb263a`.
Its successful `id_` GET states 564 and links the 4.5 MB cropped archive whose
actual saved contents number 575. The historical 564 status remained
`CANDIDATE_ONLY`, with no UMIST clustering jobs in Phase 1, repair_round1 or
Round 2.

```python
from benchmarks import load_dataset
X, y, metadata = load_dataset("UMIST", version="precropped575")
assert X.shape == (575, 10304)
assert metadata["unique_pixel_arrays"] == 565
```

Run `python -m pytest benchmarks/umist/test_umist.py`; the strict default must
remain unavailable and the explicit575 metadata retains `not_exact_564`.
See `manifest.yaml`, `manifest_wayback.yaml`, `manifest_figshare_cropped.yaml`
and the historical Round 2 source records.

The historical v3 note additionally records LZUFE `umist.mat` as 574x10304 with
ten extra exact duplicate rows, retained without deduplication. Zenodo3634017
has 575x644 features at 28x23 and MD5 `039e0d805a5c65df7bfecd172a24f14c`.
Roweis repeats Figshare's hash. None was scheduled as the strict historical cell.
Earlier v1/v2 results remain historical; LLC before the Procrustes correction
retains `PRE_FIX_LEGACY`.
