# USPS

The explicit/default `libsvm` source consists of the complete training file
followed by the complete test file: 7,291+2,007=9,298 digit samples, ten classes
and 256 native features. Train-only/test-only subsets are diagnostics and do
not compete as the paper's 9,298-row input.

## Source and preparation

The [LIBSVM dataset page](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass.html#usps)
attributes USPS to Hull (TPAMI 1994). The source files already represent 16×16
images in `[-1,1]`. They receive no second resize or rescaling. Chang et al.
report 9,298 digits and 16×16 pixels, but do not identify the exact release or
all preprocessing, so source verification is distinct from historical identity.

Place both files in `usps/data` beneath the independent data root:

| File | Bytes | Expected SHA-256 |
|---|---:|---|
| `usps.bz2` | 6579383 | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` |
| `usps.t.bz2` | 1831726 | `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` |

The loader parses feature indices 1–256, preserves all rows in train-then-test
order and maps stored labels 1–10 to 0–9. The declared split is not supervised
training in this clustering task. It returns a float64 `(9298,256)` matrix;
missing sparse feature entries remain zero.

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset("USPS", root=Path("/path/to/benchmarks/usps/data"))
```

Perturbations use the full native `[-1,1]` domain and preserve zero-change input
identity. Clipping these values to `[0,1]` changes the unperturbed data and does
not represent a small-noise comparison.

## Terms and interpretation

The compressed files contain no license notice; exact redistribution terms are
not established by public availability. Keep the raw files outside Git and
retain the source attribution. The [manifest](manifest.yaml),
[data guide](../../docs/data.md), [protocol](../../docs/experimental_protocol.md)
and [results](../../docs/results.md) record source and numerical qualifications,
including the distinction between a saved output and a certified optimum.
