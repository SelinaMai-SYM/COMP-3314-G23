# Data and source identity

Benchmark files are supplied through a separate data root. Published scalar
results and report tables can be rebuilt without image archives or a scientific
artifact store. Real-data experiments use the documented providers and exact
source versions below.

The [dataset inventory](../results/submission_refresh/dataset_inventory.csv)
records source URLs, native/processed dimensions, row order, hashes, duplicate
maps and historical-identity qualifications. The
[combined benchmark tables](../results/submission_refresh/per_benchmark/) distinguish
paper-compatible and adapted results.

## Sources and dimensions

| Benchmark / source | Matrix used or candidate construction | Identity qualification |
|---|---|---|
| ORL att92 | 400 samples, 40 identities; native 112×92 images resized to 32×32 | Verified source/preparation; unspecified paper settings remain distinct |
| JAFFE | 213 images, 10 models; native 256×256 TIFF images resized to 26×26 | Verified official archive; source identity does not resolve all paper choices |
| YaleB cropped2414 | 2,414 non-ambient images, 38 identities; native 192×168 resized to 32×32 | Cropped source, interpolation and row order are explicit |
| YaleB DengCai32 | 2,414 rows, 38 identities, 1,024 features | Separate supplied matrix; pixel/row identity with the cropped source is not assumed |
| USPS | 9,298 rows, 10 digits, 256 features | Full 7,291-row train file followed by the 2,007-row test file |
| MSRA25 EBSA16 | 1,799 rows, 12 classes, 256 native features | Native 16×16 source, distinct from the paper's unresolved 32×32 MSRA50 input |
| AR parent | 1,680 rows, 120 identities, 1,024 features; seven-of-fourteen hypotheses select 840 rows | Original subset identity and pixel geometry remain unverified |
| UMIST sources | Source-specific 574/575-row matrices; explicit deduplication/omission/stratified candidates | Matching the paper's 564-row count does not establish membership identity |
| BinAlpha parent | 1,404 rows, 36 digit/letter classes, 20×16 pixels; letter candidates select 30 samples per letter | The unchanged seed-0 manifest and further declared draws are reproducible hypotheses |

AR feature count alone is not treated as proof of 32×32 image geometry. UMIST's
112×92 and resized 28×23 sources remain separately named. Original full inputs
retain duplicate rows; derived deduplication candidates record their mappings
and exclusions explicitly. Source aliases do not multiply independent datasets.

## Data root

The root contains benchmark subdirectories such as `orl/data`, `jaffe/data`,
`yaleb/data`, `usps/data` and `msra50/data`. Resolution order is explicit
`--data-root`, `COMP3314_DATA_ROOT`, an ignored local pointer, then checkout-local
`benchmarks/`. Provider files and their source hashes identify the input.

| Source | Path beneath the data root | Provider |
|---|---|---|
| ORL att92 | `orl/data/att92/att_faces.zip` | [AT&T archive](https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html) |
| JAFFE | `jaffe/data/jaffe.zip` | [Official Zenodo record](https://zenodo.org/records/14974867) |
| YaleB cropped | `yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` | [Archived UCSD release](https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip) |
| YaleB DengCai32 | `yaleb/data/YaleB_32x32.mat` | [Deng Cai matrix](http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat) |
| USPS | `usps/data/usps.bz2`, `usps/data/usps.t.bz2` | [LIBSVM dataset page](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass.html#usps) |
| MSRA25 EBSA16 | `msra50/data/EBSA_c72bfbf_MSRA25.mat` | [Pinned EBSA file](https://github.com/LZUFE-Machine-Learning/EBSA/blob/c72bfbf13ac0e67db1a756eb26d56b7b996b64cb/dataset/MSRA25.mat) |

AR, UMIST and BinAlpha source-specific paths and checksums are defined by their
benchmark manifests and the source inventory. Strict original-dataset loaders
reject inferred substitutes. Use an explicitly named candidate/source endpoint
for those experiments.

## Downloading public files

USPS files can be fetched directly from LIBSVM; the loader verifies the identities listed in its [manifest](../benchmarks/usps/manifest.yaml):

```bash
mkdir -p local/data/usps/data
curl --fail --location --retry 2 https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.bz2 --output local/data/usps/data/usps.bz2
curl --fail --location --retry 2 https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.t.bz2 --output local/data/usps/data/usps.t.bz2
python -m benchmarks.msra50.retrieve --data-root "$PWD/local/data"
```

Other sources are obtained through the provider links above and placed at their declared paths. JAFFE requires compliance with its research-use and redistribution terms. Source-specific parent matrices and sample manifests are described in the individual [benchmark guides](../benchmarks/README.md).

## Deterministic preparation

From the repository root, prepare archives stored in `local/data`:

```bash
python -m benchmarks.prepare --dataset ORL_att92 --data-root "$PWD/local/data" --archive local/data/orl/data/att92/att_faces.zip
python -m benchmarks.prepare --dataset YaleB_cropped2414 --data-root "$PWD/local/data" --archive local/data/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip
python -m benchmarks.msra50.retrieve --data-root "$PWD/local/data"
```

ORL rows follow numeric subject/image order. Cropped YaleB excludes ambient
images and sorts subject/filename paths; nearest, bilinear and bicubic versions
retain the same membership. JAFFE sorts TIFF filenames, converts grayscale
consistently, applies bilinear 26×26 resizing and divides pixels by 255. Prepared
ORL/YaleB arrays retain uint8 before loader scaling. The DengCai matrix is not
resized again.

USPS retains its native `[-1,1]` range. Domain-aware brightness/noise operations
use that full range and return the input unchanged at zero perturbation. EBSA16
retains all 1,799 rows and duplicates, divides native 0–255 values by 255, and
does not upsample or deduplicate the matrix. The pinned EBSA file has SHA-256
`3c8681c40ebbed2f6dc2d2f30e7c5195e947467e8cf6797faa44753a190cd659`.

## Attribution and availability

Dataset use follows the source terms retained in each benchmark README and
manifest. JAFFE is noncommercial research data with redistribution prohibited;
YaleB also restricts redistribution of its images. These archives are therefore
not included with the code. A public mirror is not itself evidence of identical
source bytes or redistribution rights.

The paper's exact AR/UMIST/BinAlpha membership and native 32×32 MSRA50 file are
unresolved. EBSA16 availability does not identify that MSRA50 source. Recorded
hashes and explicit sample manifests support reproducible current inputs;
numerical agreement with a paper table cannot establish missing historical
identity. See [limitations](limitations.md) and [results](results.md).
