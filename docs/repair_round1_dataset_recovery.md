# First dataset-recovery round (2026-10-20)

> Historical record, translated into English on 2026-11-10. Access statuses and
> decisions below apply to 2026-10-20. Later explicit candidate reconstructions
> and MSRA recovery are recorded in the
> [submission refresh](submission_refresh/source_recovery.md).

Requests used `urllib` HEAD or `curl -sI -L` / `curl -L`, with User-Agent
`COMP3314-SSC-dataset-recovery/1.0`. No URLs, checksums or timestamps were
invented. The existing Olivetti MAT (SHA 256
`b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794`)
and Deng Cai YaleB MAT (SHA 256
`3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99`)
were not overwritten. New archives were kept under ignored dataset `data`
directories; `git check-ignore -v` verified exclusion. These historical paths
describe the original checkout, rather than a dependency on another branch.

The ORL default remained Olivetti 64 reduced to 32x32 with bilinear interpolation,
and the YaleB default remained Deng Cai 32. Strict UMIST/AR/BinAlpha/MSRA50
continued to raise `DatasetUnavailable`.

## File inventory and decisions

| Source | Saved historical path | SHA 256 | Verified contents / decision |
|---|---|---|---|
| AT&T/ORL92 | `benchmarks/orl/data/att92/att_faces.zip` |`509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec`|400 PGM,40 people, native 112x92 arrays; obtained|
| Cropped YaleB | `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` |`8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573`|2452 PGM in 38 subject folders;2414 non-Ambient arrays 192x168; obtained|
| AR | no file |none|No 840-image subset constructed; unavailable|
| UMIST strict 564 | no matching archive |none|Both available archives have 20 people but differing image counts; unavailable as 564|
| UMIST uncropped | `benchmarks/umist/data/wayback_sheffield/face_wayback_20050403.tar.gz` |`df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb`|1012 unique PGM names/1013 members,122 spatial shapes; approximate source|
| UMIST cropped | `benchmarks/umist/data/wayback_sheffield/cropped_wayback_20070805.tar.gz` |`c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4`|575 images,565 distinct pixel arrays, all 112x92; approximate source|
| UMIST Figshare | `benchmarks/umist/data/figshare_umist_cropped/umist_cropped.mat` |`ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361`|575 slices,565 unique,20 people; pixel hashes do not match the cropped tar|
| BinAlpha | no file in this round |none|No 26x30 historical set obtained; Binary Alphadigits not substituted|
| MSRA 50 | no file |none|No 1799/12 file obtained; unrelated MSRA collections not substituted|

## ORL / AT&T

Cambridge lists both `att_faces.zip` and `orl_faces.zip` as 3,769,022 bytes. Both
GET responses had the same SHA 256, so only `att_faces.zip` was retained. The
archive contains 40 directories with 10 PGM images each. Its README states 92x112,
8-bit images. PIL reports image size `(92,112)` in width/height order and arrays
`(112,92)` without a transpose. Across all images, pixels range 0-251. The upper
eight rows have mean approximately 80.5 and a central 32x32 window approximately
146.5. This describes the observed stored orientation; it does not establish
pixel identity with the Olivetti 64 matrix.

Prepared uint 8 arrays are in `benchmarks/orl/data/att92/processed/`:

| Interpolation | File | Pixel range | SHA 256 |
|---|---|---:|---|
| nearest | `orl_att92_32x32_nearest_uint8.npy` |0-244|`d056a67cd3850f3c5cdf726c35247d0db11f41d45bfd11f4a5ee4da26f0fe2ea`|
| bilinear | `orl_att92_32x32_bilinear_uint8.npy` |14-223|`db8ed7a2db8b65aba8d34c9387420c014834d39cef5d27f6b994181de87a5f7d`|
| bicubic | `orl_att92_32x32_bicubic_uint8.npy` |9-227|`2e70df62a253d4f42b45dbb16b44ec0de1c832f5a1775fb398a77cbf4f058683`|

The native `(400,112,92)` array `orl_att92_native_uint8.npy` has SHA 256
`c8559063d2dde31cdd1746f2038431d995013c96eaff31ef1aaa37f8053066fa`.
The loader divides the selected 32x32 array by 255 and flattens in C order.
Both `att92` and `att92_bilinear` select bilinear interpolation. The zip README
requests credit to Olivetti Research Laboratory; Cambridge's HTML page requests
credit to AT&T Laboratories Cambridge and displays Copyright 2002.

| Historical request | Result and action |
|---|---|
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip` |Initial urllib HEAD failed certificate validation with no HTTP response; curl HEAD and GET returned 200, application/zip, Content-Length3769022. Saved 400 images/40 classes and the hash above.|
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/orl_faces.zip` |Same urllib TLS failure; curl HEAD/GET200, length 3769022. Downloaded bytes matched the saved zip, so no second copy was retained.|
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.tar.Z` |Only urllib HEAD attempted; certificate validation failed. No curl retry or saved tar. Page describes another format of the same database.|
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html` |urllib TLS failure; curl HEAD/GET200, text/html,6036 bytes. Documentation, not an image archive.|
| `http://www.cl.cam.ac.uk/Research/DTG/attarchive/pub/data/att_faces.zip` |urllib failed TLS after redirect. curl followed 302 to HTTPS,301 to the lowercase path, then 200, length 3769022. Same final saved archive; no new copy.|
| `https://cam-orl.co.uk/facedatabase.html` |curl HEAD/GET200, text/html,“AT&T Database of Faces.” The page links obsolete ftp.uk.research.att.com downloads; FTP was not requested. It requests Cambridge credit and displays Copyright 2001.|

## Extended Yale B cropped images

The following live-source requests did not recover the required full cropped
archive. Their recorded statuses remain dated observations:

| Historical request | Result and interpretation |
|---|---|
| `http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` |urllib/curl404, text/html; no zip.|
| `https://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` |404; no zip.|
| `http://vision.ucsd.edu/~leekc/ExtYaleDatabase/CroppedYaleBZip/CroppedYale.zip` |urllib 404; old path.|
| `http://vision.ucsd.edu/~iskwak/ExtYaleDatabase/CroppedYaleBZip/CroppedYale.zip` |urllib 404; old path.|
| `http://vision.ucsd.edu/~leekc/ExtYaleDatabase/ExtYaleB.html` |curl 404; documentation path.|
| `http://vision.ucsd.edu/~iskwak/ExtYaleDatabase/ExtYaleB.html` |curl 404; documentation path.|
| `https://vision.ucsd.edu/datasets/extended-yale-face-database-b-b` |urllib TLS failure; curl HEAD/GET200,31820 HTML bytes. It describes 16128 images/28 people and links the unavailable datarepo page; no working CroppedYale.zip.|
| `https://datarepo.eng.ucsd.edu/visiondata/iskwak/public_html/ExtYaleDatabase/ExtYaleB.html` |GET 404, Apache error.|
| `https://datarepo.eng.ucsd.edu/visiondata/iskwak/public_html/ExtYaleDatabase/CroppedYaleBZip/CroppedYale.zip` |404; attempted mapping of the old iskwak path.|
| `https://datarepo.eng.ucsd.edu/visiondata/iskwak/public_html/ExtYaleDatabase/` |404.|
| `https://datarepo.eng.ucsd.edu/visiondata/` |404.|
| `http://vision.caltech.edu/~greg/ee148_spring2008/CroppedYale.zip` |urllib TLS failure; curl 301 to www.vision.caltech.edu HTTPS, then 404 served by GitHub.com.|
| `https://vision.caltech.edu/~greg/ee148_spring2008/CroppedYale.zip` |Same 301 then 404.|
| `http://luthuli.cs.uiuc.edu/~daf/courses/CV23/Assignments/assignment3/croppedyale.zip` |HEAD/GET200, application/zip,6132444 bytes. Temporary download SHA 256 `f548d2ae451dece41657a0840769ec4c69eca9bb5981ee1755730057a3d7001c`;260 non-MacOS PGM images in yaleB 01/02/05/07 only, so not 2414/38 and not added to the project.|
| `https://www.cs.yale.edu/cvc/projects/yalefacesB/yalefacesB.html` |urllib TLS failure; curl HEAD/GET200,9088 bytes. Original 10-person YaleB, not 38-person cropped set. Page describes 90 archives of about 11 MB; about 1 GB was not downloaded.|
| `ftp://plucky.cs.yale.edu/CVC/pub/images/yalefacesB/TarSets/` |curl 56, response-reading failure, HTTP code 000; no archive.|
| `https://academictorrents.com/details/aad8bf8e6ee5d8a3bf46c7ab5adfacdd8ad36247` |200, text/html; only page saved, no torrent. It lists CroppedYale.zip58.49 MB but describes 28 people/16128 images; no validated image archive was inferred.|
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` |HEAD/GET200; states 32x32 YaleB comes from UCSD cropped images but points to 404 ExtYaleB.html.|
| `http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/` |403; existing MAT unchanged.|
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` |HEAD/GET200; no MSRA 50 or BinAlpha file links.|

Internet Archive CDX returned 200 and listed successful captures of the original
UCSD cropped zip, with approximately 58 MB length fields. The leekc zip CDX query
returned an empty array. The file actually saved was:

`https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip`

curl HEAD/GET returned 200, application/zip,58,493,820 bytes. `unzip -t` found no
errors; SHA 256 is in the inventory above. A HEAD request for the corresponding
2016-09-09 `id_` capture also returned 200 and Content-Length58493820; a duplicate
archive was not downloaded.

The 2015-01-10 Wayback `ExtYaleB.html` page returned 200 and linked that UCSD zip
under “Cropped Images.” It requests research use, citation of Georghiades et al.
(PAMI 2001), and Lee et al.(PAMI 2005) for cropped-image experiments. Yale's original
page also restricts incorporation into another public redistribution database
without Yale permission.

The zip has 38 subject directories, excluding yaleB 14, with 2452 PGM images.
Among 38 Ambient files, ten arrays are 192x168 and 28 are 480x640. Every remaining
2,414 image is 192x168, uint 8, with pixels 0-255. Eighteen `.pgm.bad` sidecars are
excluded. In subject order, the counts are 64 ten times, then 60,59,60,63,62,63,63,
then 64 for the remaining subjects. This matches Deng Cai's `gnd` histogram;
no pixel alignment was performed, and matrix identity is not asserted.
Three 32x32 uint 8 preparations were saved, with hashes in
`benchmarks/yaleb/manifest_cropped.yaml`. The explicit `cropped2414` version
uses bilinear and divides by 255 on load.

## AR Face Database

No login was bypassed, no images saved, and no 840-image subset invented in this
round. The existing source notice required a university-email password request
and prohibited redistribution.

| Historical request | Result and decision |
|---|---|
| `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` |HEAD/GET503, nginx “Service Temporarily Unavailable”; no data.|
| `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` |curl expired-certificate error, HTTP 000. No `-k` bypass.|
| `https://engineering.purdue.edu/~aleix/aleix_face_DB.html` |404.|
| `https://engineering.purdue.edu/~aleix/ARdatabase.html` |404.|
| `http://rvl.ecn.purdue.edu/~aleix/aleix_face_DB.html` |301 to engineering.purdue.edu, then 404.|
| `http://www.cat.uab.cat/Public/Publications/1998/MaB1998/` |GET 200, but only 65-byte MySQL connection error; not data.|
| `https://tsapps.nist.gov/BDbC/Search/Details/301` |404; catalogue entry rather than images.|
| `https://doi.org/10.57702/q1qmqyrd` |HEAD 302 to service.tib.eu UUID record, then 200, text/html; metadata only.|
| `https://service.tib.eu/ldmservice/dataset/3df8623c-9ddc-40e5-936d-3f0d4960a944` |DOI target 200; no images.|
| `https://service.tib.eu/ldmservice/dataset/ar-database` |HEAD/GET200, but Anubis JavaScript bot challenge; not images and not bypassed.|

The CVC technical-report search result described access by email. No application
was submitted and no working direct archive was obtained. Decision: unavailable.

## UMIST / Sheffield

The target was 564 images and 20 people. Sources with other counts were kept
separate rather than asserted exact.

| Historical request | Result and interpretation |
|---|---|
| `http://eprints.lincoln.ac.uk/id/eprint/16081/` |202, WAF challenge, Content-Length0.|
| `https://eprints.lincoln.ac.uk/id/eprint/16081/` |202, same WAF challenge.|
| `http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` |202, WAF challenge; no archive.|
| `https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` |202, WAF challenge; no archive.|
| `https://web.archive.org/cdx/search/cdx?url=eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz&output=json&fl=timestamp,statuscode,length,original&limit=15` |200 with `[]`; no successful capture for that URL.|
| `http://images.ee.umist.ac.uk/danny/database.html` |502, Content-Length0.|
| `http://images.ee.umist.ac.uk/danny/face.tar.gz` |502.|
| `http://images.ee.umist.ac.uk/danny/cropped.tar.gz` |502.|
| `https://www.sheffield.ac.uk/eee/research/iel/research/face` |301 to sheffield.ac.uk, then 404.|
| `https://web.archive.org/web/20010405074800id_/http://images.ee.umist.ac.uk/danny/database.html` |200; page states 564 images,20 people, PGM, approximately 220x220; publication restricted to subject 1a with written permission; links 29 MB face.tar.gz and 4.5 MB cropped.tar.gz.|
| `https://web.archive.org/web/20050403232828id_/http://images.ee.umist.ac.uk/danny/face.tar.gz` |HEAD/GET200,29385054 bytes, application/x-tar; actual gzip originally named face.tar,1997-07-08. Saved 1012 unique PGM/20 directories/122 shapes; approximate, not 564.|
| `https://web.archive.org/web/20070805190146id_/http://images.ee.umist.ac.uk/danny/cropped.tar.gz` |HEAD/GET200,4506480 bytes; gzip originally cropped.tar,1998-10-16. Saved 575 images,112x92, pixels 0-238,565 unique arrays,20 people; not 564.|
| `https://cs.nyu.edu/~roweis/data.html` |403, text/html.|
| `http://www.cs.nyu.edu/~roweis/data.html` |301 to HTTPS www, then 301 to non-www, then 403.|
| `https://cs.nyu.edu/~roweis/data/umist_cropped.mat` |403; not downloaded.|
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html` |200; page states 575 UMIST images,20 people,112x92, hand-cropped by Daniel Graham, and links cropped/uncropped MAT files. Not treated as 564.|
| `https://api.figshare.com/v2/articles/33130868` |200 JSON:“UMIST Dataset,”file umist_cropped.mat, size 5927440, supplied MD 5 `62bbcdd946c62a2b112d0062aa279caa`, CC BY 4.0; description only the dataset title.|
| `https://ndownloader.figshare.com/files/67153214` |HEAD 302 to ten-second S3 signed URL, then 403. A direct GET to the original Figshare URL returned 200,5927440 bytes. Saved 20 cells/575 slices 112x92/565 unique arrays; pixel-hash intersection with cropped tar zero, including after transpose.|

CDX queries for the UMIST database page, face/cropped tars, and Roweis page
returned 200 JSON and supplied the chosen capture timestamps. Around 2000, some
face.tar.gz captures were only about 1 MB; they were not downloaded as full data.
The uncropped archive has 122 shapes, most commonly 196x170 for 71 images, pixels
0-238, and was not stacked into one matrix. The cropped loader divides all 575
images by 255 without resizing; both cropped and Figshare metadata retain
`not_exact_564`. The uncropped matrix endpoint remains unavailable.

## BinAlpha and MSRA 50

Chang et al. specify 26 alphabets with 30 random images each, without a seed or
URL. No 26x30 file was obtained in this first round, and the 36-class parent was
not substituted.

| Historical BinAlpha request | Result and decision |
|---|---|
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html` |200; Binary Alphadigits listed as 0-9 plus A-Z,39/class,20x16, so 36 classes rather than 26x30.|
| `https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` |403; not downloaded.|
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` |302 to 20240616024002id_ capture; subsequent HEAD 200,532304 bytes, text/plain. HEAD only; no MAT saved or loaded.|
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` |200; no BinAlpha link.|
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` |200; only Yale/ORL/Extended YaleB matrices.|

MSRA 50 also remained unavailable:neither Deng Cai page linked a1799-row,
12-class matrix. No MSRA-TD500, MSRA-B or MSRA 10K download was substituted,
and a TUNA PyPI mirror was not treated as a dataset. A search tool had obtained
response content for
`https://people.sc.fsu.edu/~jburkardt/octave_src/exm/harvard500.mat`;
that is the Harvard 500 MATLAB example, not MSRA 50. No separate curl HTTP status
was recorded, and the file was not retained or exposed to a loader.

## Historical loader interface

```python
from benchmarks import load_dataset
load_dataset("ORL")
load_dataset("ORL", version="att92")
load_dataset("ORL", version="att92_nearest")
load_dataset("ORL", version="att92_bicubic")
load_dataset("YaleB")
load_dataset("YaleB", version="cropped2414")
load_dataset("UMIST", version="precropped575")
```

The first ORL and YaleB calls use their old defaults; the explicit UMIST call
loads 575, not 564. Unversioned UMIST/AR/BinAlpha/MSRA50 continued to raise
`DatasetUnavailable`. These commands describe that historical implementation;
current data-root commands are documented separately.
