# Strict URL source acquisition (Task 1, 2026-10-21)

> Historical investigation record, translated into English on 2026-11-10.
> These source-access and implementation statuses describe the recorded round.
> Later recovery and explicit candidate work appear in the
> [submission refresh](submission_refresh/source_recovery.md).

The historical working checkout was `v1`, starting at
`47c0f835ef69afa560b891524da894ab4b39bad2`. Requests used
`COMP3314-SSC-strict-url-repro/1.0`. The detailed records are
[strict URL JSON](strict_http_logs/task1_strict_url.json) and
[the request log](strict_http_logs/task1_requests.log).
Only URLs in the authorized local plan `strict_url_repro_c525e30e.plan.md`
and exact file links from those authorized pages were used. No host was
invented. This round did not modify `method_extension` or the report, commit or
push Git changes, or run the 72-cell clustering campaign. Restricted images
remained ignored by Git. The historical local planning-file path is not a
runtime dependency of the current checkout.

## Acquired and verified resources

| Resource | Historical path | Bytes | SHA 256 | MD 5 | Sample count / status |
|---|---|---:|---|---|---|
| Third-party AR zip | `benchmarks/ar/data/ARDB_Full.zip` |120587997|`32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438`|`bb97bd9237680744c0c7268624696263`|100 identities;2599 numbered BMP files plus `s7/22 - Copy.bmp`; `SOURCE_RECOVERED_SUBSET_UNVERIFIED`|
| UMIST cropped tar | `benchmarks/umist/data/wayback_sheffield/cropped_wayback_20070805.tar.gz` |4506480|`c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4`|`da0ae0037ef9d6f3d58deaac6c4cb412`|575 PGM;565 unique byte/pixel arrays, not 564|
| UMIST uncropped tar | `benchmarks/umist/data/wayback_sheffield/face_wayback_20050403.tar.gz` |29385054|`df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb`|`11011ab5dded043f5e4331711c2407c8`|1013 members;1012 unique names, not 564|
| UMIST Roweis MAT | `benchmarks/umist/data/roweis_umist_cropped/umist_cropped.mat` |5927440|`ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361`|`62bbcdd946c62a2b112d0062aa279caa`|575; byte-identical to Figshare, not 564|
| BinAlpha parent | `benchmarks/binalpha/data/binaryalphadigs.mat` |532304|`3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7`|`194c4c91d95f1457bbd5829e75373b96`|36x39=1404; verified parent, not historical BinAlpha|
| BinAlpha candidate | `benchmarks/binalpha/reconstructions/letters26x30_seed0.json`; `CANDIDATE_BIN_ALPHA.json` pointer |derived|parent hash above|parent MD 5 above|780x320, seed 0; `CANDIDATE_BIN_ALPHA`, not EXACT|
| JAFFE | `benchmarks/jaffe/data/jaffe.zip` |12290558|`6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`|`fe13f3302eb9968ef04367456f665436`|213 TIFF; hash matched existing file|
| ORL AT&T92 | `benchmarks/orl/data/att92/att_faces.zip` |3769022|`509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec`|`ea6281c63bb2e68a64c046957a749086`|400 PGM/40 people; hash matched existing file|
| YaleB cropped | `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` |58493820|`8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573`|`4447b8e69c0c2f7479f67f2481efe13f`|2452 PGM/2414 non-Ambient; hash matched existing file|
| USPS | `benchmarks/usps/data/usps.bz2` + `usps.t.bz2` |6579383+1831726|`3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` / `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e`|`ec16c51db3855ca6c91edd34d0e9b197` / `8ea070ee2aca1ac39742fdd1ef5ed118`|9298; hashes matched existing files|
| MSRA 50 images | no file |—|—|—|`BLOCKED_DATA_NOT_OBTAINED`|
| SPLS Section 3 | no PDF |—|—|—|`BLOCKED_MISSING_FULL_METHOD`|

No dataset was marked EXACT with respect to the paper's entire protocol.
JAFFE permits noncommercial research and prohibits redistribution. The original
UMIST page restricts image publication; Figshare lists CC BY 4.0 for its MAT copy,
not for Graham's release. The AR uploader's CC-BY-4.0 statement does not establish
official Martinez licensing. Yale restricts redistribution; AT&T requests credit.
The USPS compressed files and BinAlpha MAT contain no license file.

## Third-party AR archive

The authorized [Zenodo record](https://zenodo.org/records/19683234) supplied the
exact API file URL
`https://zenodo.org/api/records/19683234/files/ARDB_Full.zip/content`.
GET returned 200, `application/octet-stream`, filename `ARDB_Full.zip`, and
120,587,997 bytes. The `PK\x03\x04` header established PKZIP rather than HTML.
Measured and published MD 5 agree. The uploader was Manu shree, ORCID
`0009-0007-8493-5282`, with a “MAS Machine” manuscript; the uploader was not
Aleix Martinez or OSU.

The official 2012 page describes 126 people (70 men,56 women), names
`M-xx-yy.raw` and `F-xx-yy.raw`, indices 1-26 for expressions, lighting and
occlusion, and native 768x576 RAW images. The third-party zip instead has
`ARDB_Full/s1` through `s100`, with 2,600 valid `BM` files, all 120x165,
24-bit BMP. No filename matches the official RAW convention. Folder `s7`
lacks `26.bmp` but has `22 - Copy.bmp`; there are also AppleDouble sidecars
and `.DS_Store`. No README, PDF or 840/120 selection rule is in the zip.

Chang et al.'s local UTS paper states 840 faces of 120 people without naming the
images. This 100-identity archive cannot supply that specification. No
seven-per-person subset was constructed in this historical round. The status
was `SOURCE_RECOVERED_SUBSET_UNVERIFIED`, and the strict AR default remained
unavailable. The ignored archive was not committed.

## UMIST counts and copies

Existing Wayback tars and the Figshare MAT passed hash checks and were not
downloaded again. Their source URLs were:

- `https://web.archive.org/web/20050403232828id_/http://images.ee.umist.ac.uk/danny/face.tar.gz`
- `https://web.archive.org/web/20070805190146id_/http://images.ee.umist.ac.uk/danny/cropped.tar.gz`

The live [Roweis page](https://cs.nyu.edu/home/people/in_memoriam/roweis/data.html)
returned 200. Its `data/umist_cropped.mat` link resolved to
`https://cs.nyu.edu/home/people/in_memoriam/roweis/data/umist_cropped.mat`.
GET returned 200 and 5,927,440 bytes, identical to Figshare by SHA 256 and MD 5.

The cropped tar has 575 members with 575 unique filenames. Both unique byte
arrays and unique pixel arrays number 565, with the same ten duplicate groups,
all in `1b/face`, from `1b014.pgm=final00.pgm` through
`1b072.pgm=final09.pgm`. Removing ten copies leaves 565, not 564. Reaching 564
requires eleven deletions from 575, or one additional deletion after deduplication;
no evidence justified that additional choice in this round, so it was not made.
The uncropped tar has 1,012 unique names, with `1t/1t052.pgm` repeated with the
same bytes. The strict 564 endpoint remained unavailable, separate from 575.

## BinAlpha candidate

The existing Binary Alphadigits file passed its hash check and was not
downloaded again. A HEAD request to
`https://cs.nyu.edu/home/people/in_memoriam/roweis/data/binaryalphadigs.mat`
returned 200 and 532,304 bytes. The stored seed 0 rule drops digit classes 0-9,
uses one RandomState(0) over A-Z to choose 30 of 39 examples without replacement,
and sorts indices within each letter. The resulting matrix is 780x320.

Its explicit version is `CANDIDATE_BIN_ALPHA`; exact indices are in
`benchmarks/binalpha/reconstructions/letters26x30_seed0.json`, with a
`CANDIDATE_BIN_ALPHA.json` pointer. Seed 0 is the project's reconstruction seed,
not a recovered Chang seed. The strict BinAlpha default remained unavailable
and no historical sample identity was claimed.

## MSRA 50 and SPLS restrictions at the recorded date

The plan had no MSRA 50 download URL. Local data contained no 1799x1024,
12-class matrix. The UTS-hosted SSC paper described 1,799 images from 12 classes;
the related arXiv:1411.6241v1 paper listed 1024/1799/12 and cited He et al.2004.
Neither was a data file. No unrelated MSRA collection was substituted; the
status remained `BLOCKED_DATA_NOT_OBTAINED`.

For SPLS, `baselines/spls/resources` contained no full-method PDF. DOI
`https://doi.org/10.1016/j.ipm.2013.01.004` yielded 2,671 bytes of Linkinghub HTML,
not Section 3. The ScienceDirect abstract URL
`https://www.sciencedirect.com/science/article/abs/pii/S0306457313000095`
returned HEAD 403 with `cf-mitigated: challenge`; the full-text PII also returned
403. No access restriction was bypassed and no implementation was invented
from the abstract. At that historical point, `fit_predict` still raised
`NotImplementedError` and the method was `BLOCKED_MISSING_FULL_METHOD`.

JAFFE, ORL AT&T92, cropped YaleB and USPS were checked by SHA 256 only, without
new downloads. All matched their prior READMEs. Experiments were required to
state source version and checksum. Strict AR/UMIST/BinAlpha/MSRA50 defaults
remained unavailable; explicit third-party AR still did not return paper 840
arrays. No CK+ or Extended Yale B file was downloaded from the AR Zenodo record,
no author contact or Elsevier bypass was attempted, and no 72-cell campaign ran
in this resource-only round.
