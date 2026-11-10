# Binary alphabet candidates

Chang et al. specify 26 binary handwritten alphabets with thirty randomly
selected images per alphabet, without a parent URL, image size or seed. This
implementation provides an explicitly named Binary Alphadigits parent and a
manifest-defined 26×30 reconstruction. Neither establishes the authors'
historical parent or indices. Strict `load_dataset("BinAlpha")` raises
`DatasetUnavailable`.

## Source and values

Binary Alphadigits, attributed to Simon Lucas/Algoval and distributed as a
[Roweis MATLAB dump](https://cs.nyu.edu/home/people/in_memoriam/roweis/data/binaryalphadigs.mat),
contains digits 0–9 and letters A–Z: 36 classes, 39 examples each, 20×16 binary
pixels. The [recorded archived source](https://web.archive.org/web/20240616024002id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat)
is a separate retrieval reference. Place `binaryalphadigs.mat` in
`binalpha/data` beneath the independent data root.

Expected file length is 532,304 bytes; SHA-256 is
`3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7`
and MD5 is `194c4c91d95f1457bbd5829e75373b96`. The loader checks the MATLAB cell
shape/class ordering and native uint8 20×16 images, keeps values `{0,1}` without
dividing by 255, and vectorizes in C order to 320 features. The complete parent
has 1,404 rows and is a diagnostic source.

## Versions and exact row rules

| Version | Samples / classes | Qualification |
|---|---:|---|
| Default / `paper` | Unavailable | Strict historical identity unresolved |
| `binaryalphadigs36` | 1404 / 36 | Entire parent in class-major, stored-example order |
| `CANDIDATE_BIN_ALPHA` / `letters26x30_seed0` | 780 / 26 | Fixed seed-0 hypothesis, not recovered author membership |

The unchanged [seed-0 manifest](reconstructions/letters26x30_seed0.json) removes
parent digit classes 0–9. One `numpy.random.RandomState(0)` is advanced across
letters A–Z, parent class indices 10–35. It selects thirty of thirty-nine
examples without replacement, then sorts selected example indices within each
letter. Final labels are 0–25 in that canonical letter order. The loader reads
the stored exact indices rather than drawing a new subset.

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset(
    "BinAlpha", root=Path("/path/to/benchmarks/binalpha/data"),
    version="letters26x30_seed0"
)
```

The [candidate catalogue](../../configs/subset_search/candidate_catalogue.json)
keeps further RandomState seeds 0–99 and first/last-thirty sensitivities separate,
with selected/excluded original rows and aliases. A changed subset rebuilds its
own graphs and representation. Counts or close clustering scores do not resolve
historical identity.

No redistribution license is established by the MAT file or the archived Roweis
page. The source remains outside Git. See [the manifest](manifest.yaml),
[data terms](../../docs/data.md) and [scientific limitations](../../docs/limitations.md).
