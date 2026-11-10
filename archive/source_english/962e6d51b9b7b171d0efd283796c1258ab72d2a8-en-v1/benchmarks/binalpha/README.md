# Binary alphabet candidates

> English editorial replacement of the frozen historical source snapshot.
> These dated recovery notes do not describe later experiment coverage.
> See the current submission refresh for subsequent work.

## Identity and source

Chang et al. specify 26 binary handwritten alphabets with 30 randomly selected
images per alphabet. They give no parent URL, image size or seed. Binary
Alphadigits, attributed to Simon Lucas/Algoval and distributed as a Roweis
MATLAB dump, contains digits 0-9 and letters A-Z: 36 classes with 39 images each,
20x16 pixels, or 1,404 images. Dropping digits and sampling 30 per letter is a
reproducible hypothesis, not direct evidence that Chang et al. used that parent.
Neither the AAAI paper, arXiv:1411.6308 nor the related arXiv:1411.6241 paper
identifies Binary Alphadigits as its BinAlpha source.

The source `binaryalphadigs.mat` is 532,304 bytes, SHA256
`3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7`,
MD5 `194c4c91d95f1457bbd5829e75373b96`. The source is kept outside Git;
the exact reconstruction index JSON is committed. No license was found inside
the MAT file or on the archived Roweis page, so redistribution permission is
not assumed.

## Explicit versions and reconstruction

| Version | Samples/classes | Meaning |
|---|---:|---|
| Default / `paper` | unavailable | `DatasetUnavailable`; strict paper identity unresolved |
| `binaryalphadigs36` | 1404/36 | Complete parent diagnostic |
| `CANDIDATE_BIN_ALPHA` / `letters26x30_seed0` | 780/26 | Fixed seed0 reconstruction; historical identity unverified |

The stored [seed0 manifest](reconstructions/letters26x30_seed0.json) drops
parent classes 0-9. One `numpy.random.RandomState(0)` is advanced sequentially
across A-Z, parent class indices 10-35. It chooses 30 of 39 indices per letter
without replacement, then sorts the indices within each letter. Seed 0 is our
reconstruction seed, not a recovered author seed. Cells are native uint8
20x16 images with values in {0,1}; no division by 255 is applied. Images are
vectorized in C order to 320 features.

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("BinAlpha", root=Path("/path/to/benchmarks/binalpha/data"),
                             version="letters26x30_seed0")
```

Integrity checks require `(1404,320)` for the full parent, `(780,320)` and 30
samples per class for the reconstruction, and `identity="CANDIDATE_BIN_ALPHA"`.
The strict default must remain unavailable; no explicit version claims EXACT.
Run `python -m pytest benchmarks/binalpha/test_binalpha.py`.

## Historical recovery notes (2026-10-21)

No BinAlpha clustering jobs ran in Phase 1, repair_round1 or Round 2.
The live legacy `cs.nyu.edu/~roweis/data/binaryalphadigs.mat` GET returned 403,
while Wayback capture `20240616024002id_` returned 200. The original download
created the file without overwriting an older archive. Later Task 1 and Strict
URL checks reused it and found the same SHA256 and length. The planned live
Roweis URL's HEAD returned 200 in the strict check. Historical 26-by-30 identity
remained `NOT_FOUND`; the stored reconstruction remained `CANDIDATE_ONLY`.
See [Round 2 source records](../../docs/round2_source_of_truth.md) and
[the manifest](manifest.yaml).
