> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Task 1: Original-paper resources still missing

Date: 2026-10-21. This stage verified resources and obtained lawful supporting material. It did not modify `method_extension/`, rewrite `report/`, run the 72 cells, or make a Git commit.

The remaining paper-protocol gaps were AR 840/120, UMIST 564, BinAlpha 26x30, the MSRA50 1799/12 file, Section 3 of Hou et al. (IPM 2013), and author code for all methods. Existing hash-matching archives were not downloaded again.

## Missing original resources

1. **Official AR images and the 840/120 rule.** The application page returned HTTP 503; HTTPS certificate verification failed (curl 60, no bypass). Purdue mirrors returned 404/502. A 2012 official Wayback page confirmed 126 people, university-email password applications, and no redistribution; it did not specify 840/120. CVC TR 24 was obtained lawfully but contained no image archive. Zenodo 19683234 was not downloaded because it was not from Martinez and conflicted with official redistribution terms. The related arXiv:1411.6241 listed AR 840x768 without image indices. No 7x120 subset was invented.

2. **The actual MSRA50 1799x12x1024 file.** Chang/Nie/Yang cited He 2004/TPAMI 2005 Laplacianfaces: 12 people, 64-80 images per session, cropped to 32x32. Deng Cai's data.html, FaceData.html, and MLData.html returned HTTP 200 without MSRA50. GitHub search `MSRA50 mat` returned total_count=0. MSRA-B/10K/TD500 and unofficial CSDN/Baidu packages were not substituted. A plausible total range of 1536-1920 did not establish file recovery.

3. **Paper UMIST 564.** The official 2001 page (Wayback 200) stated 564 images of 20 people and offered 29Mb face.tar.gz and 4.5Mb cropped.tar.gz. Both local archives matched Round 2 hashes. The uncropped archive had 1012 distinct PGM names; the cropped archive had 575 PGM files and 565 distinct pixel arrays. Removing ten `1b/final*.pgm` copies gave 565, not 564, with no evidence for one additional omission. The strict default loader remained unavailable.

4. **Paper BinAlpha 26x30.** The Binary Alphadigits parent (36x39) was present with unchanged hash. AAAI/arXiv did not identify the parent, image dimensions, or seed. `letters26x30_seed0` remained an UNVERIFIED reconstruction.

5. **SPLS/SLPS Section 3.** Unpaywall reported is_oa=false, oa_status=closed, oa_locations=[]; OpenAlex oa_url=null; Semantic Scholar CLOSED; arXiv had zero results. The author's PDF link led to Elsevier DOI. Find@HKUL returned a catalogue (200), Scholars Hub 403; there was no authenticated ScienceDirect PDF in the session. `fit_predict` still raised NotImplementedError. The method was not invented from its abstract.

6. **Author code.** xiaojun.ai returned 200 without a 2015 SSC implementation; GitHub `spectral shrunk clustering` found zero repositories. Hou's PublicationCode repository was empty. Ding-Li, Wu-Schölkopf, and Chang baselines remained CODE_NOT_FOUND. Elhamifar's Sparse Subspace Clustering and 2016 PSLSR were not substituted for Spectral Shrunk Clustering or SPLS.

## Lawfully obtained supporting resources

- AAAI SSC PDF, matching the existing `9736-45063-1-PB.pdf` hash.
- arXiv:1411.6308 preprint.
- NeurIPS 2006 LLC paper.
- Ding-Li 2007 author-page PDF; ACM 403 was not bypassed.
- CVC TR 24 and official AR Wayback HTML: terms, not images.
- UMIST 2001 HTML.
- Related arXiv:1411.6241v1: a MSRA50 bibliographic pointer, not data.

## Explicitly not done

- No repeated download of hash-matching JAFFE, att_faces, CroppedYale, USPS, Olivetti, YaleB MAT, Binary Alphadigits, or UMIST archives.
- No Zenodo ARDB_Full.zip download.
- No bypass of Elsevier access, contact with authors, or treatment of TUNA/PyPI as a dataset source.
- No SPLS implementation or clustering grid at this historical stage.