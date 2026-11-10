# ORL / AT&T faces

> English editorial replacement of the frozen historical source snapshot.
> These dated recovery notes do not describe later experiment coverage.
> See the current submission refresh for subsequent work.

## Source and paper specifications

The AT&T/ORL database is attributed to Samaria and Harter (1994). Cambridge's
`att_faces.zip` contains 400 native 92x112 PGM images of 40 people, ten each.
The scikit-learn/Figshare `olivettifaces.mat` is a separate native 64x64 matrix;
its checksum agrees with scikit-learn 1.8.0's source record. Chang et al.
specify 40 people, ten images each, resized to 32x32 using pixel features.
They do not specify whether the starting images were 92x112 or 64x64, the
interpolation kernel, or prior cropping. Treating the usual 92x112 release as
an original-source candidate is an explicit reconstruction choice.

| Version | Preparation | Qualification |
|---|---|---|
| Default / `olivetti` | Native 64x64 to 32x32 bilinear | Counts match; distinct spatial source |
| `att92` / `att92_bilinear` | Native 92x112 to 32x32 bilinear | Explicit AT&T source candidate |
| `att92_nearest` / `att92_bicubic` | Same PGM source, other kernels | Interpolation sensitivity |

All versions retain 400 rows. Olivetti labels are column index divided by ten;
AT&T labels are subject folders s1-s40 mapped to 0-39. For AT&T, the PGM header
has width 92 and height 112, yielding `(400,112,92)` arrays without a transpose.
Native pixels span 0-251. Resized pixels are divided by 255 and vectorized in
C order. Olivetti follows the scikit-learn axis convention before bilinear
resizing.

## Source and prepared-array integrity

| File | Bytes | SHA256 |
|---|---:|---|
| `data/olivettifaces.mat` | 4260520 | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` |
| `data/att92/att_faces.zip` | 3769022 | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` |
| `orl_att92_32x32_nearest_uint8.npy` | 409728 | `d056a67cd3850f3c5cdf726c35247d0db11f41d45bfd11f4a5ee4da26f0fe2ea` |
| `orl_att92_32x32_bilinear_uint8.npy` | 409728 | `db8ed7a2db8b65aba8d34c9387420c014834d39cef5d27f6b994181de87a5f7d` |
| `orl_att92_32x32_bicubic_uint8.npy` | 409728 | `2e70df62a253d4f42b45dbb16b44ec0de1c832f5a1775fb398a77cbf4f058683` |
| `orl_att92_native_uint8.npy` | 4121728 | `c8559063d2dde31cdd1746f2038431d995013c96eaff31ef1aaa37f8053066fa` |

Prepared AT&T arrays are under `data/att92/processed/` in the independent data
root. The zip README requests credit to Olivetti Research Laboratory; the
Cambridge page requests credit to AT&T Laboratories Cambridge. Images remain
outside Git.

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("ORL", root=Path("/path/to/benchmarks/orl/data"),
                             version="att92")
assert X.shape == (400, 1024)
assert metadata["original_spatial_size"] == [112, 92]
```

The default must remain Olivetti. Explicit AT&T nearest, bilinear and bicubic
arrays must differ. Run `python -m pytest benchmarks/orl/test_orl_versions.py`.

## Historical recovery and experiment notes (2026-10-21)

The Figshare 5976027 HEAD request returned 403, while the existing MAT file
had already been obtained on 2026-10-20. Task 1 and Strict URL audits did not
download it or the AT&T archive again; all hashes remained unchanged. AT&T
contains 400 PGM images and its matrix status was
`COMPLETE_WITH_UNSPECIFIED_SETTINGS`, because the paper did not specify
interpolation.

Phase 1 Track A/B and most repair_round1 jobs used default Olivetti, with 27
registry entries marked `olivetti`. repair_round1 D01 included at least one
completed job for each of `att92`, `att92_nearest` and `att92_bicubic`.
The Round 2 shortlist used AT&T:

| Method/source | Historical run ID | ACC mean +/- SD (%) |
|---|---|---:|
| AT&T SC, 50 runs | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` | 56.2 +/- 4.2 |
| AT&T E8 | `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` | 57.3 +/- 3.8 |
| Olivetti SC control | `20261021_161536__ROUND2__ORL__D01_OLIVETTI_SC__9118018b` | 53.9 +/- 3.0 |

Those measurements remain historical; current records preserve their source
identities. See [Round 2](../../docs/round2_source_of_truth.md),
[missing resources](../../docs/round2_missing_resources.md),
[the base manifest](manifest.yaml) and [the AT&T manifest](manifest_att92.yaml).
Older LLC results preceding the Procrustes correction remain `PRE_FIX_LEGACY`.
