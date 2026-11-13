# JAFFE

The Japanese Female Facial Expression dataset is attributed to Lyons, Kamachi
and Gyoba. The [official Zenodo release](https://zenodo.org/records/14974867)
contains 213 TIFF images of ten models. Chang et al. specify those counts and
26×26 pixel features. Source membership is verified; the unspecified
interpolation/label convention is made explicit here rather than claimed as
recovered paper protocol.

## Source and preparation

Place `jaffe.zip` in `jaffe/data` beneath the independent data root. Expected
length is 12,290,558 bytes, SHA-256
`6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`,
and MD5 `fe13f3302eb9968ef04367456f665436`.

The default and only source version is `zenodo`. All TIFF filenames are sorted;
no images are discarded. Native 256×256 images are converted to 8-bit grayscale,
resized with PIL bilinear interpolation to 26×26, divided by 255 and flattened
in C order. The 23 palette-mode images have grayscale palettes and are converted
to L mode before resizing. Labels use alphabetical two-letter model codes:

| Code | KA | KL | KM | KR | MK | NA | NM | TM | UY | YM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Label | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| Count | 23 | 22 | 22 | 20 | 21 | 21 | 20 | 21 | 21 | 22 |

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset("JAFFE", root=Path("local/data/jaffe/data"))
```

The output shape is `(213,676)`. The loader requires all ten labels. Archive
reading/preprocessing happens directly in the loader; no separate prepared
image directory is required.

## Terms and interpretation

The provider permits noncommercial research and prohibits redistribution,
including redistribution in a Git repository. Keep the archive outside the
checkout and retain the requested attribution. Source verification does not
resolve every graph/rounding choice in the SSC paper.

See [the source manifest](manifest.yaml), [data setup](../../docs/data.md),
[experimental protocol](../../docs/experimental_protocol.md) and
[results](../../docs/results.md).
