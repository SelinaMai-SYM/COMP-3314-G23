# AR Face Database

> English editorial replacement of the frozen historical source snapshot.
> These dated recovery notes do not describe later experiment coverage.
> See the current submission refresh for subsequent work.

## Source identity and the paper

The AR Face Database is described by Martinez and Benavente, CVC Technical
Report 24 (1998). The official release requires an application and password and
prohibits redistribution. Its usual description has 126 people and more than
4,000 images. Chang et al. report 840 faces of 120 people, using pixel features,
without identifying the selected images or a resize size. Within-class image
positions cannot be labelled as sessions or illumination conditions without
supporting source metadata.

## Historical recovery notes (2026-10-21)

No AR clustering jobs ran in Phase 1, repair_round1 or Round 2. The third-party
archive was examined only as a source. No 840-image subset was constructed.

A third-party Zenodo archive `ARDB_Full.zip` was downloaded and verified:
120,587,997 bytes; MD5 `bb97bd9237680744c0c7268624696263`; SHA256
`32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438`.
It is PKZIP, not HTML, and contains 100 identities `s1` through `s100`, with
120x165 BMP images named `1.bmp` through `26.bmp`. Those names and counts differ
from official `M-xx-yy.raw` and `F-xx-yy.raw` naming and cannot supply 120 people.
It is not the official Martinez distribution.

[Zenodo record 19683234](https://zenodo.org/records/19683234) and its API returned
HTTP 200 on 2026-10-21. Its title is “Facial Image datasets,” uploaded by Manu
shree (ORCID 0009-0007-8493-5282), rather than Martinez or OSU. The description
links the files to a 2026 “MAS Machine: Multi-kernel Attention Spatio Machine”
manuscript and includes AR, Extended Yale B and CK+. The uploader selected
CC-BY-4.0. That claim does not make the archive an official release or override
the original source's redistribution restrictions. Images remain outside Git.
The archive's published and measured MD5 values agree.

Before that download, official-page HTTP returned 503, HTTPS curl returned
certificate error 60, Purdue returned 404 and RVL returned 502. A Wayback OSU
page was saved at `resources/ARdatabase_wayback_20120501.html`, 19,396 bytes,
SHA256 `fea9bd20c825f94f9abd8862be63f7261cd533c43085149af0179d784a4344d8`.
It describes 126 people, password access and no redistribution, without an
840-image rule. The CVC report was saved as
`resources/Martinez_Benavente_1998_CVC_TR24.pdf`, 306,151 bytes, SHA256
`9dfb1d979781d48f5a2de1b7c277a59dc71ffcb768da60f20e562d689418951b`.
At that earlier stage the official images were `BLOCKED_ACCESS` and the
840/120 subset `NOT_FOUND`. The later third-party download changed the source
status to `SOURCE_RECOVERED_SUBSET_UNVERIFIED`; it did not identify the subset.

## Loading and checks

```python
from benchmarks import DatasetUnavailable, load_dataset
try:
    load_dataset("AR")
except DatasetUnavailable:
    pass
```

The strict default must continue raising `DatasetUnavailable`; it is tested by
`python -m pytest benchmarks/ar/test_ar.py`. The old default-loader command was
expected to fail and was not a runnable paper-data acquisition command.
See [Round 2 source records](../../docs/round2_source_of_truth.md),
[missing-resource records](../../docs/round2_missing_resources.md) and
[the manifest](manifest.yaml) for the earlier request history.
