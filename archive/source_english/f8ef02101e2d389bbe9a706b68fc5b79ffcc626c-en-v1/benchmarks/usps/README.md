# USPS

> English editorial replacement of the frozen historical source snapshot.
> These dated recovery notes do not describe later experiment coverage.
> See the current submission refresh for subsequent work.

## Source, paper statements and preparation

The LIBSVM multiclass page distributes `usps.bz2` and `usps.t.bz2`, with dataset
attribution to Hull (TPAMI 1994); the 16x16 form is described in Hastie et al.'s
`zip.info`. Chang et al. report 9,298 grayscale handwritten digits resized to
16x16, without identifying a specific file release. The obtained LIBSVM data
already have 256 native features with values in [-1,1]. No second resize or
rescaling is applied. Preparation is verified for this source, while exact
identity with the authors' preprocessing remains unverified.

| File | Bytes | SHA256 |
|---|---:|---|
| `usps.bz2` | 6579383 | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` |
| `usps.t.bz2` | 1831726 | `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` |

The compressed files contain no license notice; exact redistribution terms are
unknown. LIBSVM makes them publicly available for research. The raw files remain
outside Git. `version="libsvm"` is the only source version and the default;
there is no recovered second file that the SSC authors independently resized.

The loader parses features 1-256, concatenates all 7,291 training rows and 2,007
test rows, and maps file labels 1-10 to digit labels 0-9. Class counts match the
Hastie `zip.info` table. The declared test split is not used for supervised
training in this clustering task.

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("USPS", root=Path("/path/to/benchmarks/usps/data"))
assert X.shape == (9298, 256)
assert X.min() >= -1 and X.max() <= 1
```

## Historical recovery and experiment notes (2026-10-21)

Both file HEAD requests returned HTTP 200 in the integrity audit. The existing
archives were not replaced. Task 1 and Strict URL checks found unchanged hashes,
lengths and `(9298,256)` matrix shape; the matrix status was
`COMPLETE_WITH_UNSPECIFIED_SETTINGS`.

Phase 1 and repair_round1 used `libsvm`. The Round 2 pilot had only three runs,
rather than the required 50: SC
`20261021_161647__ROUND2__USPS__D12_USPS_SC__6324d037`, ACC 63.8 +/- 1.7%;
E8 `20261021_161650__ROUND2__USPS__D08_USPS_E8__c638f49b`, ACC 60.7 +/- 4.0%.
These pilots are not labelled complete reproductions.
See [Round 2 source records](../../docs/round2_source_of_truth.md) and
[the manifest](manifest.yaml). Older LLC results predating the Procrustes
correction retain `PRE_FIX_LEGACY`.
