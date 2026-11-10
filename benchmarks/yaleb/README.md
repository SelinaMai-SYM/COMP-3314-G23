# Extended Yale B

**Current status, 2026-11-10:** Deng Cai32 and cropped2414 are separate full
2,414-image, 38-identity source versions. The catalogue retains nearest,
bilinear and bicubic preparation alternatives and Y0-Y3 factors without deleting
difficult illumination examples. Source membership, normalization and resize
choices remain distinct. See [source recovery](../../docs/submission_refresh/source_recovery.md)
and [current campaign records](../../results/subset_search/).

The default `load_dataset("YaleB")` still returns Deng Cai's `YaleB_32x32.mat`.
This identifies the source matrix; it does not claim pixel identity with the
cropped archive or the SSC authors' input.

## Source, paper and preparation

Extended Yale Face Database B is attributed to Georghiades et al. (TPAMI 2001),
with cropped images described by Lee et al. (TPAMI 2005). Deng Cai's page states
that its 32x32 matrix was derived by reducing UCSD cropped images. Chang et al.
specify 2,414 near-frontal images from 38 people, resized to 32x32. They do not
state whether ambient images were removed, the interpolation kernel, or use
of Deng Cai's MAT file.

| Version | Rows | Preparation |
|---|---:|---|
| Default / `dengcai32` | 2414 | Already 32x32; source resize kernel unknown |
| `cropped2414` / `cropped2414_bilinear` | 2414 | Exclude 38 Ambient images from 2452 PGM images, then bilinear 32x32 |
| `cropped2414_nearest` / `cropped2414_bicubic` | 2414 | Same membership and native images; alternate resize kernels |

The cropped loader keeps non-Ambient PGM images, sorted by subject number and
then filename. Subject yaleB14 is absent. Eighteen `.pgm.bad` files are excluded
as sidecars. All remaining native images have array shape `(192,168)`.
Pixels are resized to 32x32, divided by 255 and flattened in C order. Deng Cai's
matrix is divided by 255 without another resize. Class-count histograms agree
with Deng Cai's `gnd`; this does not establish pixel-by-pixel alignment.

## File integrity and terms

| File | Bytes | SHA256 |
|---|---:|---|
| `data/YaleB_32x32.mat` | 2214688 | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` |
| `data/cropped_wayback/CroppedYale_wayback_20220127.zip` | 58493820 | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` |
| Each prepared nearest/bilinear/bicubic uint8 NPY | 2472064 | See `manifest_cropped.yaml` |

The source is for research, with credit to Georghiades et al. (2001) and Lee
et al. (2005) for cropped experiments. Yale restricts inclusion of the images
in another public redistribution database. Raw images and archives remain
outside Git.

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("YaleB", root=Path("/path/to/benchmarks/yaleb/data"),
                             version="cropped2414")
assert X.shape == (2414, 1024)
```

Run `python -m pytest benchmarks/yaleb/test_yaleb_versions.py` for version and
preparation checks. Verified source and implemented preprocessing do not imply
that all unspecified paper settings were recovered.

## Historical recovery and experiment notes (2026-10-21)

Deng Cai's MAT HEAD returned HTTP 200 with Content-Length 2,214,688. The live
UCSD zip returned 404, while Wayback capture `20220127084451id_` returned 200.
Task 1 and Strict URL audits reused the existing files and found unchanged
hashes. The cropped archive has 2,452 PGM images, including 2,414 non-Ambient
images. Prepared-array hashes are in the cropped manifest. Its matrix status
was `COMPLETE_WITH_UNSPECIFIED_SETTINGS`.

Most Phase 1 and repair_round1 YaleB jobs used `dengcai32`, with six completed
jobs and separately retained failures. repair_round1 D01 used `cropped2414`,
with one completed and one failed job. Round 2 ran ten trials, not fifty:

| Source/method | Historical run ID | ACC mean +/- SD (%) |
|---|---|---:|
| Deng Cai SC | `20261021_161602__ROUND2__YALEB__D01_DENGCAI32_SC__6411988e` | 20.1 +/- 1.2 |
| Deng Cai E8 | `20261021_161603__ROUND2__YALEB__D08_DENGCAI32_E8__27f746d1` | 19.5 +/- 1.5 |
| Cropped SC | `20261021_161625__ROUND2__YALEB__D01_CROPPED2414_SC__d1a360fb` | 18.1 +/- 1.3 |
| Cropped E8 | `20261021_161626__ROUND2__YALEB__D08_CROPPED2414_E8__5fb5af8b` | 17.4 +/- 1.1 |

Cropped input did not improve that earlier controlled block. Those limited
runs do not exhaust source/preprocessing explanations. See
[Round 2 source records](../../docs/round2_source_of_truth.md),
[the Deng Cai manifest](manifest.yaml) and [the cropped manifest](manifest_cropped.yaml).
Earlier v1/v2 measurements remain historical, and LLC results predating the
Procrustes correction retain `PRE_FIX_LEGACY`.
