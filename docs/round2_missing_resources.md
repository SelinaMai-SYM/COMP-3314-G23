> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Round 2 missing resources (HTTP index)

Date: 2026-10-21. User-Agent: `COMP3314-SSC-dataset-recovery/2.0`. Local urllib returned CERTIFICATE_VERIFY_FAILED for many HTTPS requests; these TLS failures were not interpreted as origin HTTP statuses. HTTP values below came from `curl -sI -L` or actual GET requests. Raw records: [round2_http_log.json](round2_http_log.json).

Read the corresponding dataset README together with this index.

TUNA/PyPI are not dataset sources and were not requested.

## Targets still missing at that stage

| Target | Remaining limitation | Checksums |
| --- | --- | --- |
| Official AR and 840/120 | Official 503/certificate errors; unofficial Zenodo archive rejected | None; no images saved |
| UMIST 564 | Existing 1012/575; ten copies removed from 575 give 565 | [UMIST README](../benchmarks/umist/README.md) |
| Paper BinAlpha 26x30 | Parent obtained; no evidence Chang used it | Parent SHA-256 below |
| MSRA50 1799/12 | Bibliographic pointer without URL/file | None |

## Actual requests

| URL | HTTP | License / notes | Saved? |
| --- | --- | --- | --- |
| `https://cs.nyu.edu/~roweis/data.html` | 403 | Current page | No |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html` | 200 | Roweis page: Binary Alphadigits 36×39、20×16; UMIST 575 | No (page) |
| `https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | HEAD/GET 403 | — | No |
| `http://www.cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | GET 403 (redirected to HTTPS) | — | No |
| `https://web.archive.org/web/20240616024002id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | GET **200**, 532304 bytes | No license text in MAT | **Yes** `benchmarks/binalpha/data/binaryalphadigs.mat` SHA-256 `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7` |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | HEAD 200 | No repeated GET; previous capture already present | No |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` | 200 | Noncommercial research; no MSRA50/BinAlpha file | No |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` | 200 | Yale/ORL/YaleB only | No |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat` | 200, `Content-Length: 2214688` | Deng Cai page terms | No; existing file retained |
| `https://zenodo.org/records/19683234` | 200 | Uploader claimed CC-BY-4.0 | No (metadata) |
| `https://zenodo.org/api/records/19683234` | 200 | Same; `ARDB_Full.zip` size 120587997, md5 `bb97bd9237680744c0c7268624696263` | No |
| `https://zenodo.org/records/19683234/files/ARDB_Full.zip?download=1` | HEAD 200, `Content-Length: 120587997` | Official AR prohibits redistribution; unofficial mirror; body not fetched | No |
| `https://zenodo.org/api/records/19683234/files/ARDB_Full.zip/content` | HEAD 200, same 120587997 | Same | No |
| `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | 503 | Official application page | No |
| `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | curl 0 (TLS) | Certificate verification retained | No |
| `https://engineering.purdue.edu/~aleix/ARdatabase.html` | curl 0 (TLS) | — | No |
| `https://engineering.purdue.edu/~aleix/aleix_face_DB.html` | 404 | — | No |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip` | 200 | AT&T/Olivetti attribution | No; existing archive retained |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html` | 200 | Same | No |
| `https://zenodo.org/records/14974867` | 200 | JAFFE: noncommercial, no redistribution | No |
| `https://zenodo.org/records/14974867/files/jaffe.zip?download=1` | HEAD 200, `Content-Length: 12290558` | Matched local archive size; retained existing file | No |
| `https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.bz2` | 200, 6579383 | Public research release; no license file in archive | No; already present |
| `https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.t.bz2` | 200 | Same | No; already present |
| `https://ndownloader.figshare.com/files/5976027` | HEAD 403 | Olivetti MAT already local | No |
| `http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` | 404 | — | No |
| `https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` | 200 | Research use and Yale redistribution limits | No; existing archive retained |
| `https://lear.inrialpes.fr/people/triggs/events/iccv03/cdrom/iccv03/0385_he.pdf` | 200 | He ICCV 2003 | No; text read only |
| `https://people.engr.tamu.edu/rgutier/web_courses/cpsc689_s07/he2005laplacianfaces.pdf` | 200 | He TPAMI 2005 teaching copy | No |
| `https://people.engr.tamu.edu/rgutierrez/web_courses/cpsc689_s07/he2005laplacianfaces.pdf` | 404 | Incorrect path | No |
| `https://arxiv.org/abs/1411.6241` | 200 | Related paper; MSRA50 cites He 2004 | No |
| `https://arxiv.org/pdf/1411.6241.pdf` | 404 | Invalid PDF path | No |
| `http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` | 202 | WAF | No |
| `https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` | 202 | WAF | No |
| `http://images.ee.umist.ac.uk/danny/database.html` | 502 | — | No |
| `https://www.sheffield.ac.uk/eee/research/iel/research/face` | 404 | — | No |

## Main observations

1. Binary Alphadigits was obtained only through Wayback; current NYU returned 403.
2. AR Zenodo was technically downloadable (HEAD 200), but its licensing was unsuitable.
3. Official JAFFE HEAD returned 200 that day (previously 403); local hashes were unchanged and the archive was not downloaded again.
4. Current CroppedYale.zip still returned 404.
5. No PyPI/TUNA dataset URLs were requested.