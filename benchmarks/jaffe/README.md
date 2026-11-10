# JAFFE

**Current status, 2026-11-10:** the official source and implemented preparation
are verified for this release. The paper does not specify interpolation or
label encoding, so this is not proof of complete paper-protocol identity.
Current measured coverage is in the [campaign records](../../results/subset_search/)
and [submission refresh](../../docs/submission_refresh/source_recovery.md).
The dated results below are historical and are not substituted for new runs.

## Source and preparation

The Japanese Female Facial Expression dataset is attributed to Lyons,
Kamachi and Gyoba (1997). The official Zenodo release 14974867 contains 213
TIFF images of ten models. Chang et al. specify 213 images of ten people,
resized to 26x26 using pixel features. Our loader uses PIL bilinear resizing;
it maps two-letter poser codes in alphabetical order, KA through YM, to 0-9.

`jaffe.zip` is 12,290,558 bytes, SHA256
`6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`.
The published MD5 is `fe13f3302eb9968ef04367456f665436`, checked in Round 1.
The release is for noncommercial research and prohibits redistribution,
including Git redistribution. Keep the archive outside the checkout.

`version="zenodo"` is the only source version and the default. All 213 TIFF
images are sorted by filename. Counts are KA 23, KL 22, KM 22, KR 20, MK 21,
NA 21, NM 20, TM 21, UY 21 and YM 22. Native 256x256 images are resized to
26x26, divided by 255 and flattened in C order. The 190 L-mode images are
already grayscale; 23 P-mode images use grayscale palettes with R=G=B and are
converted to L first. The loader rejects shapes other than `(213,676)` and
label sets other than ten classes.

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("JAFFE", root=Path("/path/to/benchmarks/jaffe/data"))
assert X.shape == (213, 676)
assert metadata["SHA256_checksum"].startswith("6da27f59")
```

## Historical recovery and experiment notes (2026-10-21)

The record page and `jaffe.zip?download=1` HEAD requests returned HTTP 200,
with Content-Length 12,290,558. A curl request had returned 403 on 2026-10-20;
the existing file was not overwritten. Task 1 and Strict URL checks reused
that file and confirmed the same length and SHA256. Its prepared matrix status
was `COMPLETE_WITH_UNSPECIFIED_SETTINGS`.

All six completed Phase 1/repair_round1 JAFFE jobs used `zenodo`. The Round 2
D12 block used 50 runs of that version:

| Method | Historical run ID | ACC mean +/- SD (%) |
|---|---|---:|
| SC | `20261021_161557__ROUND2__JAFFE__D12_JAFFE_SC__2983a645` | 68.5 +/- 11.2 |
| E8 | `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` | 68.4 +/- 11.1 |
| E13 | `20261021_161559__ROUND2__JAFFE__D12_JAFFE_E13__50a3c90d` | 68.6 +/- 11.3 |

These are earlier protocol results, not a current matched reconstruction of
every setting. See [Round 2 source records](../../docs/round2_source_of_truth.md)
and [the manifest](manifest.yaml). Older LLC results preceding the Procrustes
correction remain `PRE_FIX_LEGACY`.
