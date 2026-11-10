# ORL / AT&T faces

The primary explicit `att92` source contains all 400 images of forty people,
ten images each, resized to 32×32. The default `olivetti` version is a separate
64×64 source preparation. The paper does not identify which starting source or
interpolation kernel it used; those alternatives are not conflated.

## Sources and row order

The [AT&T/ORL provider](https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html)
attributes the database to Samaria and Harter (1994). Its PGM header has width
92 and height 112, so the native array shape is `(400,112,92)`, without a
transpose. Subject folders are ordered numerically `s1..s40`, then image numbers
`1..10`; labels are subject number minus one. All rows remain.

The scikit-learn/Figshare Olivetti matrix is native 64×64. Its loader follows
the scikit-learn axis convention, then applies bilinear 32×32 resizing. Both
sources are scaled by 255 and vectorized in C order after the declared resize.

| Version | Preparation |
|---|---|
| Default / `olivetti` | Native 64×64 matrix → bilinear 32×32 |
| `att92` / `att92_bilinear` | Native 112×92 PGM → bilinear 32×32 |
| `att92_nearest` / `att92_bicubic` | Same PGM membership with the named interpolation |

## Files and preparation

| Path beneath `orl/data` | Bytes | Expected SHA-256 |
|---|---:|---|
| `olivettifaces.mat` | 4260520 | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` |
| `att92/att_faces.zip` | 3769022 | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` |

Obtain the [AT&T archive](https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip)
and prepare its three interpolation versions from the checkout root:

```bash
python -m benchmarks.prepare --dataset ORL_att92 --data-root /path/to/benchmarks --archive /path/to/benchmarks/orl/data/att92/att_faces.zip
```

This writes the three uint8 arrays and integer labels under
`orl/data/att92/processed/`, with source names and array hashes. The explicit
AT&T loader uses those arrays. Their expected nearest/bilinear/bicubic hashes
are in [the AT&T manifest](manifest_att92.yaml); no private data are included in
this repository. The Olivetti matrix is supplied separately at the path above,
with [its source manifest](manifest.yaml).

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset(
    "ORL", root=Path("/path/to/benchmarks/orl/data"), version="att92"
)
```

All versions return `(400,1024)`. Interpolation is an explicit sensitivity, not
an unknown-subset search. The source requests credit to Olivetti Research
Laboratory / AT&T Laboratories Cambridge; retain that attribution and the
provider's conditions. Images stay outside the public code distribution.
See [data setup](../../docs/data.md) and [results](../../docs/results.md).
