# Independent benchmark data setup

`--data-root` and `COMP3314_DATA_ROOT` mean the directory containing `orl/data`, `jaffe/data`, `yaleb/data`, `usps/data`, etc. Priority is CLI > environment > untracked `local/data_root.txt` > checkout `benchmarks/`. Historical v2 loaders use the same interpretation. They no longer accept an old worktree as a necessary root.

Licensed images and publisher PDFs are not required for import, synthetic tests or scalar-release rebuilding. Images are not redistributed here. Obtain each dataset under its provider's conditions; if access is unavailable, the corresponding experiment is `NOT_RUN_DATA_BLOCKED`, never synthetic fallback data.

| Version | Files beneath benchmark root | Processed shape / classes | Source and restrictions |
|---|---|---|---|
| ORL_att92 | `orl/data/att92/att_faces.zip`; prepare arrays below | 400 x 1024 / 40 | [AT&T archive](https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html), [archive](https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip); respect provider terms; images not committed |
| JAFFE | `jaffe/data/jaffe.zip` | 213 x 676 / 10 | [Official Zenodo](https://zenodo.org/records/14974867); the historical manifest also names record 3451524; JAFFE prohibits redistribution. Verify the exact archive hash |
| YaleB_cropped2414 | `yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip`; prepare arrays below | 2414 x 1024 / 38 | [Archived UCSD release](https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip); non-ambient images, bilinear resize, source conditions apply |
| YaleB_dengcai32 | `yaleb/data/YaleB_32x32.mat` | 2414 x 1024 / 38 | [Deng Cai matrix](http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat); different pixels/order from cropped source, not a fifth benchmark |
| USPS | `usps/data/usps.bz2`, `usps/data/usps.t.bz2` | 9298 x 256 / 10 | [LIBSVM](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass.html#usps); all 7291 train then 2007 test samples, native [-1,1] |
| MSRA25_EBSA_16x16 | `msra50/data/EBSA_c72bfbf_MSRA25.mat` | 1799 x 256 / 12 | [Pinned EBSA matrix](https://github.com/LZUFE-Machine-Learning/EBSA/blob/c72bfbf13ac0e67db1a756eb26d56b7b996b64cb/dataset/MSRA25.mat); native 16x16, all rows and duplicates retained; adapted resolution, historical identity unverified |

Archive hashes, preprocessing and provenance are in [external_data_manifest.csv](../v3_final/external_data_manifest.csv). [external_data_file_hashes.csv](external_data_file_hashes.csv) inventories the acquired local package without distributing its contents. Processed feature/label hashes are recorded per release job and in each new representation manifest.

## Prepare the image arrays from raw archives

Do not rely on processed arrays in an old worktree. The following deterministic commands create all three interpolation sensitivities and preserve sample identities:

```bash
python -m benchmarks.prepare --dataset ORL_att92 --data-root /path/to/benchmarks --archive /path/to/benchmarks/orl/data/att92/att_faces.zip
python -m benchmarks.prepare --dataset YaleB_cropped2414 --data-root /path/to/benchmarks --archive /path/to/benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip
```

ORL uses subject s1..s40, then image 1..10 in numeric order; resize 92x112 PGM to 32x32. YaleB uses sorted non-ambient PGM paths, 2414 images and 38 subject IDs. Both retain uint8 before dividing by 255 in the loader. A raw-archive hash mismatch is an error, not a reason to change the subset. Each preparation writes an image-name/array-hash manifest beside the arrays. This preparation is an explicit data-writing command; ordinary loaders read the prepared files.

JAFFE is processed directly from its zip (sorted TIFF paths, grayscale, bilinear 26x26). The DengCai matrix is already 32x32; divide uint8 by 255 and retain file row order. USPS is parsed without [0,1] rescaling. A cached spectral representation is not a replacement for this source manifest.

The historical release did not recover the paper's exact AR, UMIST or MSRA50 source/subset identities. The current candidate campaign supplies reproducible AR/UMIST/BinAlpha membership hypotheses, not proof of historical identity. Native 16x16 EBSA MSRA is now available through a separately named loader; the unknown 32x32 source remains unresolved. These distinctions preserve the original 72-cell statuses while allowing new qualified measurements.

Retrieve the pinned native matrix without upsampling:

```bash
python -m benchmarks.msra50.retrieve --data-root /path/to/benchmarks
```

The retrieval verifies the expected SHA-256 before atomic registration. See the [current source audit](../submission_refresh/source_recovery.md) and [dataset inventory](../../results/submission_refresh/dataset_inventory.csv) for exact hashes, resolution, row order and identity status. Private parent sources used by candidate loaders must likewise be obtained and verified beneath this independent root; an old worktree is not a fallback source.

The actual execution directory has a separate data root outside all v1/v2/v3 worktrees. Paths to that local copy are recorded only as provenance; they are not committed configuration defaults.
