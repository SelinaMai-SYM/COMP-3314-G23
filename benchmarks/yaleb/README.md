# Extended Yale B

DengCai32 and cropped2414 are separate 2,414-image, 38-identity source versions.
They are sensitivities of one benchmark, not independent datasets. The default
`load_dataset("YaleB")` returns Deng Cai's matrix; an explicit cropped version
uses the documented archive/preparation below.

## Sources and membership

Extended Yale B is attributed to Georghiades et al. (TPAMI 2001), with cropped
images described by Lee et al. (TPAMI 2005). [Deng Cai's matrix](http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat)
is described as reduced UCSD cropped images. The paper does not identify its
interpolation, ambient-image convention or use of that MAT file. Matching class
histograms does not establish pixel/row alignment between source versions.

| Version | Rows | Preparation |
|---|---:|---|
| Default / `dengcai32` | 2414 | Supplied 32×32 matrix; no second resize |
| `cropped2414` / `cropped2414_bilinear` | 2414 | Non-ambient native 192×168 images → bilinear 32×32 |
| `cropped2414_nearest` / `cropped2414_bicubic` | 2414 | Same membership with named resize kernels |

The cropped archive has 2,452 PGM images, including 38 Ambient images. Preparation
retains the 2,414 non-ambient `.pgm` files in sorted subject/filename order;
`.pgm.bad` sidecars are not image rows. Subject yaleB14 is absent. Labels follow
sorted subject codes. Native arrays have shape `(192,168)`, are converted to
uint8 grayscale and resized to 32×32. The loader divides by 255 and flattens in
C order. DengCai32 is divided by 255 without resizing.

## Files and preparation

Paths below are beneath `yaleb/data` in the independent data root.

| File | Bytes | Expected SHA-256 |
|---|---:|---|
| `YaleB_32x32.mat` | 2214688 | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` |
| `cropped_wayback/CroppedYale_wayback_20220127.zip` | 58493820 | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` |

Use the [recorded UCSD archive](https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip)
for the cropped preparation, then run from the checkout root:

```bash
python -m benchmarks.prepare --dataset YaleB_cropped2414 --data-root local/data --archive local/data/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip
```

This writes three uint8 interpolation arrays and integer labels under
`yaleb/data/cropped_wayback/processed/`, recording source names and array hashes.
The explicit cropped loader reads those arrays; each image array has shape
`(2414,32,32)`. Expected array hashes are in
[the cropped manifest](manifest_cropped.yaml); [the matrix manifest](manifest.yaml)
keeps DengCai32 separate.

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset(
    "YaleB", root=Path("local/data/yaleb/data"), version="cropped2414"
)
```

The returned shape is `(2414,1024)`. All declared interpolation versions preserve
membership; no difficult illumination examples are silently removed. Y0–Y3
normalization factors are separate from source/resize choices.

## Terms

Credit Georghiades et al. and Lee et al. for cropped experiments. The source is
for research and restricts inclusion of images in another public redistribution
database. Keep raw archives/images outside the code repository. See
[data setup](../../docs/data.md), [experimental protocol](../../docs/experimental_protocol.md)
and [identity limitations](../../docs/limitations.md).
