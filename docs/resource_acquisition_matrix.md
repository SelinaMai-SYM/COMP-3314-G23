> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Task 1 resource acquisition matrix (2026-10-21)

Worktree: `v1/`. User-Agent: `COMP3314-SSC-dataset-recovery/3.0`. HTTP record: [task1_http_log.json](task1_http_log.json). Disk SHA-256 and sample counts were recomputed using [round2_source_of_truth.md](round2_source_of_truth.md). Hash-matching JAFFE, att_faces, CroppedYale, USPS, Olivetti MAT, YaleB MAT, Binary Alphadigits, both UMIST tars, and Figshare UMIST were not downloaded again.

Statuses: COMPLETE_VERIFIED / COMPLETE_WITH_UNSPECIFIED_SETTINGS / PARTIAL_VERIFIED / CANDIDATE_ONLY / BLOCKED_ACCESS / BLOCKED_MISSING_METHOD / NOT_FOUND.

Code-source labels: OFFICIAL_AUTHOR_CODE / VERIFIED_AUTHOR_DISTRIBUTION / THIRD_PARTY_CODE / PAPER_BASED_REIMPLEMENTATION / CODE_NOT_FOUND. Any obtained third-party algorithm would be isolated in vendor rather than hidden in fit_predict. No algorithm repository was cloned in this historical stage. sklearn was a library, not author code.

TUNA/PyPI were not treated as datasets. Paywalls were not bypassed. Zenodo 19683234 was not downloaded because it was unofficial and conflicted with AR redistribution terms. No AR840 subset was invented, no UMIST images were arbitrarily removed to reach 564, and no MSRA-B/10K/TD500 substitute was used.

No dataset reached COMPLETE_VERIFIED because interpolation, sample membership, or scaling remained underspecified by the paper.

## Datasets

| Dataset | Matrix status | Obtained | Verified | Exact paper membership | Source | Missing |
| --- | --- | --- | --- | --- | --- | --- |
| ORL `att92` | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y: 400 PGM / 40 people x10, `(112,92)` | Counts match 400/40 | Cambridge `att_faces.zip`, HEAD 200; not downloaded again | Interpolation unspecified |
| ORL default Olivetti | `PARTIAL_VERIFIED` | Y | Y: Figshare/sklearn MAT | N: 64x64 differs from 92x112 | `olivettifaces.mat` | Not original-source |
| JAFFE | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y: 213 TIFF / 10 people | Y: counts | Zenodo 14974867 `jaffe.zip` | Interpolation unspecified |
| YaleB `cropped2414` | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y: 2452 PGM minus 38 Ambient = 2414 / 38 | Counts match | Wayback UCSD `CroppedYale.zip` | Interpolation unspecified; current URL 404 |
| YaleB Deng Cai MAT | `PARTIAL_VERIFIED` | Y | Y: 2414×1024 | Counts match; pixels differ from cropped | Deng Cai `YaleB_32x32.mat` HEAD 200 | Unknown resize kernel |
| USPS | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y: 7291+2007=9298 / 10 / 256 | Counts match | LIBSVM `usps.bz2` + `usps.t.bz2` | Already 16x16 in release |
| AR Official images | `BLOCKED_ACCESS` | N | N | N | Official application HTTP **503**; HTTPS curl **60**(certificate); Purdue 404/502 | Password distribution; no redistribution |
| AR 840/120 | `NOT_FOUND` | N | N | N | 2012 official Wayback page did not list 840; related arXiv:1411.6241 listed 840x768 without indices | 840 indices unspecified; none invented |
| UMIST 564 | `CANDIDATE_ONLY` | Archive Y; 564 N | Y for 1012/575 archives | N: 565 differs from 564 | 2001 page states 564 and links 4.5Mb `cropped.tar.gz`=local 575 | No evidenced 564 membership rule |
| BinAlpha Paper 26x30 | `NOT_FOUND` | Parent Y | Parent 36x39 Y | N | Roweis Wayback `binaryalphadigs.mat` | No evidence of Chang usage/seed |
| BinAlpha `letters26x30_seed0` | `CANDIDATE_ONLY` | reconstruction | UNVERIFIED | N | Project reconstruction seed 0 | Not identified as paper membership |
| MSRA50 1799/12/1024 | `NOT_FOUND` | N | N | N | Related paper cites He 2004; no file on Deng Cai page; GitHub search zero | No actual file |

### Verified archives (rehashed, not overwritten)

| File | Bytes | SHA-256 | Samples |
| --- | --- | --- | --- |
| `benchmarks/orl/data/att92/att_faces.zip` | 3769022 | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | 400 PGM, 40 people |
| `benchmarks/orl/data/olivettifaces.mat` | 4260520 | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` | Loaded `(400,1024)` |
| `benchmarks/jaffe/data/jaffe.zip` | 12290558 | `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | 213 TIFF |
| `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` | 58493820 | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | 2452 PGM / 2414 non-Ambient |
| `benchmarks/yaleb/data/YaleB_32x32.mat` | 2214688 | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` | Loaded `(2414,1024)` |
| `benchmarks/usps/data/usps.bz2` | 6579383 | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` | 9298 together with .t.bz2 |
| `benchmarks/usps/data/usps.t.bz2` | 1831726 | `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | See above |
| `benchmarks/binalpha/data/binaryalphadigs.mat` | 532304 | `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7` | 36×39=1404 |
| `benchmarks/umist/data/wayback_sheffield/face_wayback_20050403.tar.gz` | 29385054 | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` | 1012 distinct PGM |
| `benchmarks/umist/data/wayback_sheffield/cropped_wayback_20070805.tar.gz` | 4506480 | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` | 575 PGM; 565 unique pixels |
| `benchmarks/umist/data/figshare_umist_cropped/umist_cropped.mat` | 5927440 | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` | 575, not 564 |

Prepared-array hashes under data/*/processed/ agreed with Round 2 package READMEs; see those files for their recorded paths.

### Newly saved supporting resources (not image datasets)

| File | Bytes | SHA-256 | License/identity |
| --- | --- | --- | --- |
| `SSC_method/resources/Chang_et_al_2015_SSC_AAAI.pdf` | 851255 | `970ee4e65fd73aca46b3f983098f87105fb7e45726b767ec7925c9188646dfaf` | AAAI OA; matches external `9736-45063-1-PB.pdf` hash |
| `SSC_method/resources/Chang_et_al_2014_SSC_arxiv_1411.6308.pdf` | 233802 | `b4bb9f8984db89ee5c17a2c2200a6764085d81d3da5fc26b2c144e2202262e39` | arXiv OA preprint |
| `baselines/llc/resources/Wu_Schoelkopf_2006_NIPS_LLC.pdf` | 127718 | `17828ebae410aca05c026767bffb2befec09a5edfe4232c770c2782a904c12c3` | NeurIPS OA |
| `baselines/lda_kmeans/resources/Ding_Li_2007_ICML_LDA_Kmeans.pdf` | 219382 | `6b643ed6605daca3aaeaf1423572836a783f90df0ee0f4a5aec32c13784b342a` | Author-page OA PDF; not ACM paywall |
| `benchmarks/ar/resources/Martinez_Benavente_1998_CVC_TR24.pdf` | 306151 | `9dfb1d979781d48f5a2de1b7c277a59dc71ffcb768da60f20e562d689418951b` | CVC TR; not images |
| `benchmarks/ar/resources/ARdatabase_wayback_20120501.html` | 19396 | `fea9bd20c825f94f9abd8862be63f7261cd533c43085149af0179d784a4344d8` | Official terms page Wayback `id_` GET **200** |
| `benchmarks/umist/resources/database_wayback_20010405.html` | 3878 | `a8a91fbea393f524e3275acad9356512145547217c18f446eb08eae849cb263a` | States 564 and links 4.5Mb cropped tar |
| `benchmarks/msra50/resources/Chang_Nie_Yang_Huang_2014_arxiv_1411.6241v1.pdf` | 463461 | `d3d00b0fa2eeff938d65800a3a7e4d1b08987de73932e9bd04de801e708badb2` | Related OA paper; table lists MSRA50 1799/12/1024. `arxiv.org/pdf/1411.6241.pdf` 404 that day |

## Baselines and SSC

| Method | Matrix status | paper | code | implemented | gaps |
| --- | --- | --- | --- | --- | --- |
| SSC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | AAAI OA/arXiv saved | `CODE_NOT_FOUND`(GitHub repository search `spectral shrunk clustering` `total_count=0`; xiaojun.ai: no 2015 code) | `PAPER_BASED_REIMPLEMENTATION`(E8/E13) | No author binary; bandwidth/symmetrization assumed |
| K-means | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Chang Setup OA | `THIRD_PARTY_CODE` sklearn Lloyd; `CODE_NOT_FOUND` author code | fit_predict wrapper | 50 repeats at protocol level |
| SC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Eq. (4) OA | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | δ、union kNN |
| PCA-KM | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Name and OA setup | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | Dimension step 10 |
| PCA-SC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Name and Eq.(4) | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | Same |
| LDA-KM | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Ding-Li author PDF GET **200** | `CODE_NOT_FOUND`; ACM PDF **403** | `PAPER_BASED_REIMPLEMENTATION` | `sw_reg` / `max_iter` |
| LDA-SC | `BLOCKED_MISSING_METHOD` | Chang gives only the name | `CODE_NOT_FOUND` | Two APPROXIMATE interpretations only | Excluded from faithful main table |
| LLC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | NIPS 2006 OA GET **200** | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | Yang2010 not mixed in; k=5 comparison protocol |
| SPLS / SLPS | `BLOCKED_MISSING_METHOD` | Hou et al. IPM 2013 DOI `10.1016/j.ipm.2013.01.004`; Unpaywall/OpenAlex **closed**; arXiv `totalResults=0`; Author PDF link=Elsevier DOI | `CODE_NOT_FOUND`(Hou GitHub lacks SLPS; PublicationCode empty) | `NotImplementedError` | Section3 unavailable; no implementation without equations |

## Actual HTTP searches for missing resources

Zenodo ARDB_Full.zip was not fetched and Elsevier access was not bypassed.

| Target | URL | HTTP | Result |
| --- | --- | --- | --- |
| AR official | `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | **503** | No images |
| AR official HTTPS | `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | curl **60** | Certificate failure; no -k |
| AR Purdue | `engineering.purdue.edu/~aleix/ARdatabase.html` and related URLs | **404** | — |
| AR RVL | `http://rvl1.ecn.purdue.edu/ARdatabase/ARdatabase.html` | **502** | — |
| AR Wayback CDX | OSU page | **200**, captures from 2012-2016 | Fetched 20120501 HTML; 126 people, password, no redistribution, no840 rule |
| AR CVC TR | `.../MaB1998/CVCReport24.pdf` | **200** | Technical report; no image archive |
| AR Zenodo 19683234 | Record page | **200**(metadata) | Not downloaded |
| MSRA Deng Cai | `data.html` / `FaceData.html` / `MLData.html` | **200** | No MSRA/MSRA50/BinAlpha files |
| MSRA GitHub | `search/repositories?q=MSRA50+mat` | **200** | `total_count=0` |
| UMIST current site | `images.ee.umist.ac.uk` | **502**; Sheffield **404**; Lincoln **202** WAF | Existing tar not redownloaded |
| UMIST2001 page | Wayback `id_` | **200** | States 564 images of20 people; 4.5Mb cropped tar gives575 local files |
| SPLS Unpaywall | `api.unpaywall.org/v2/10.1016/j.ipm.2013.01.004` | **200** | `is_oa=false`, `oa_status=closed`, `oa_locations=[]` |
| SPLS OpenAlex | Same DOI | **200** | `is_oa=false`, `oa_url=null`, `any_repository_has_fulltext=false` |
| SPLS S2 | Same DOI | **200** | `isOpenAccess=false`, `CLOSED` |
| SPLS arXiv | export query | **200** | `totalResults=0` |
| SPLS HKU Find | Find@HKUL | **200** Catalogue shell | No authenticated PDF in session |
| SPLS HKU Hub | Scholars Hub | **403** | — |
| SSC author page | `https://www.xiaojun.ai/` | **200** | No 2015 code |
| SSC GitHub | `search/repositories?q=spectral+shrunk+clustering` | **200** | `total_count=0` |
| AAAI SSC PDF | ojs download | **200** | Saved |
| NIPS LLC PDF | proceedings.neurips.cc | **200** | Saved |
| Ding-Li author PDF | ranger.uta.edu | **200** | Saved |
| Ding–Li ACM | `dl.acm.org/doi/pdf/10.1145/1273496.1273562` | **403** | Not bypassed |
| Related1411.6241 | `/pdf/1411.6241.pdf` **404**; `/pdf/1411.6241v1.pdf` **200** | v1 saved |

Loader spot checks: ORL (400,1024); att92 (400,1024), native [112,92]; JAFFE (213,676); YaleB/cropped2414 (2414,1024); USPS (9298,256). Strict AR/UMIST/BinAlpha/MSRA50 defaults still raised DatasetUnavailable. UMIST precropped575 had 575 rows and 565 unique pixel arrays.