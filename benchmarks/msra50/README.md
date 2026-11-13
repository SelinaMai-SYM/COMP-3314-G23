# MSRA source versions

The explicit `MSRA25_EBSA_16x16` source has 1,799 samples, twelve classes and
256 native pixel features. Its 16×16 resolution differs from the SSC paper's
stated 32×32 MSRA50 input. Strict `load_dataset("MSRA50")` therefore raises
`DatasetUnavailable`; the native16 source is a separately named adaptation.

## Pinned EBSA source

[EBSA MSRA25.mat](https://github.com/LZUFE-Machine-Learning/EBSA/blob/c72bfbf13ac0e67db1a756eb26d56b7b996b64cb/dataset/MSRA25.mat)
is pinned to commit `c72bfbf13ac0e67db1a756eb26d56b7b996b64cb`.

| Property | Value |
|---|---|
| File | `msra50/data/EBSA_c72bfbf_MSRA25.mat` beneath the independent data root |
| Bytes | 387675 |
| SHA-256 | `3c8681c40ebbed2f6dc2d2f30e7c5195e947467e8cf6797faa44753a190cd659` |
| MATLAB variables | `X`, `Y`, `im_height`, `im_width` |
| Shape / resolution | 1799×256; 16×16 |
| Class counts | 175, 154, 113, 178, 186, 159, 179, 128, 133, 131, 128, 135 |

The loader reads MATLAB-declared double variables using
`scipy.io.loadmat(mat_dtype=True)`, verifies finite integer pixels in 0–255,
and divides by 255. All rows remain in source order, including thirteen extra
exact duplicate rows with consistent labels. There is no resize, upsampling or
deduplication. Labels are shifted from 1–12 to 0–11.

```bash
python -m benchmarks.msra50.retrieve --data-root local/data
```

The retrieval command checks length/hash before publishing a download and
refuses to overwrite an existing mismatching file.

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset(
    "MSRA25_EBSA_16x16", root=Path("local/data/msra50/data")
)
```

`load_dataset("MSRA50", version="ebsa16", root=...)` is the equivalent explicit
version. See [the EBSA manifest](manifest_ebsa16.yaml).

## Historical identity and terms

The paper specifies 1,799 images, twelve classes and 32×32 input without an
identifying file URL. The [Fast-CD source](https://github.com/moetayuko/Fast-CD/tree/f13a4f6e08fc5677062dfbbb2b208e324109edd7)
expects `MSRA50_uni.mat` and describes 1,024 features, but that matrix was not
recovered. Matching counts or upsampling EBSA16 cannot
establish historical source/pixel identity. Other unrelated MSRA-named datasets
are not substitutes.

Redistribution rights for the EBSA matrix are not established. Public access
does not itself grant redistribution permission, so raw files remain outside
Git. [Supporting literature](resources/README.md), [data identity](../../docs/data.md)
and [limitations](../../docs/limitations.md) keep source, resolution and
historical identity separate.
