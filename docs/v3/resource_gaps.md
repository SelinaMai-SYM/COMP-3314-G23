> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# v3 resource gaps

Raw images stay outside git. This file records availability, not a claim that a loaded matrix is the author's file.

- `AR` (AR): BLOCKED_DATA. AR is unavailable: Chang et al. name AR as 840 faces of 120 people and do not say which 840. Official Martinez distribution was not obtained. A THIRD-PARTY zip ARDB_Full.zip from Zenodo 19683234 (uploader Manu shree, not Martinez/OSU) was downloaded on 2026-10-21: 120587997 bytes, MD5 bb97bd9237680744c0c7268624696263 (matches the published Zenodo checksum), SHA-256 32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438. The zip is PKZIP, not HTML. It contains 100 folders s1-s100 with 120x165 BMP files named 1.bmp..26.bmp, not official M-xx-yy.raw / F-xx-yy.raw names. No archive document states an 840/120 or 7-image rule, so that subset was not invented. Status: SOURCE_RECOVERED_SUBSET_UNVERIFIED. Default load_dataset('AR') does not claim EXACT. See benchmarks/ar/README.md.
- `JAFFE` (JAFFE): AVAILABLE. 
- `ORL_att92` (ORL): AVAILABLE. 
- `UMIST_precropped575` (UMIST): AVAILABLE. 
- `BinAlpha_candidate26x30` (BinAlpha): AVAILABLE. 
- `MSRA50` (MSRA50): BLOCKED_DATA. MSRA50 is unavailable: MSRA50 is BLOCKED_NO_VERIFIED_DATA_URL. Chang et al. state 1799 images and 12 classes resized to 32x32, with no URL. Round 2 was given a null direct download URL. The page https://arxiv.org/html/2311.15214v1 is reference material only and was not saved as data. No MSRA-B, MSRA10K, TD500, or MSRC file was substituted. See benchmarks/msra50/README.md.
- `YaleB_dengcai32` (YaleB): AVAILABLE. 
- `YaleB_cropped2414` (YaleB): AVAILABLE. 
- `USPS` (USPS): AVAILABLE. 
- `AR_lzuf_superset1680` (AR): AVAILABLE. 
- `UMIST_lzuf574` (UMIST): AVAILABLE. 
- `UMIST_zenodo3634017` (UMIST): AVAILABLE. 
- `UMIST_roweis575` (UMIST): AVAILABLE. 

## Acquisition attempts

- SSC_AAAI_PDF: HTTP 200 `https://ojs.aaai.org/index.php/AAAI/article/download/9606/9465`
- BinaryAlphadigits_live: HTTP 200 `https://cs.nyu.edu/home/people/in_memoriam/roweis/data/binaryalphadigs.mat`
- BinaryAlphadigits_page: HTTP 200 `https://cs.nyu.edu/home/people/in_memoriam/roweis/data.html`
- DengCai_FaceData: HTTP 200 `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html`
- SLPS_DOI: HTTP 200 `https://doi.org/10.1016/j.ipm.2013.01.004`
- ATT_ORL_zip: HTTP 200 `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip`

## Still missing for a historical cell

- AR 840/120. The 100-identity zip is not that subset.
- UMIST 564. The 575-image release keeps its own version id.
- BinAlpha author's 26 by 30 draw. Seed 0 is only a candidate.
- MSRA50 1799/12. No file was substituted.
- LDA-SC has a name in Chang et al. and no algorithm.
