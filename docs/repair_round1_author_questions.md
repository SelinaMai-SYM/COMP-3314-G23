# Repair round 1: questions for the original authors

These are questions only. **Do not send email from this round.** **Do not treat this file as a sendable letter.** Group 23 names and emails require confirmation and are not invented here.

Recommended contacts, if a later round chooses to write: corresponding authors of Chang, Nie, Ma, Yang, and Zhou, AAAI 2015 (SSC); and Chenping Hou for Hou, Nie, Jiao, Zhang, and Wu, IPM 2013 (SLPS / SPLS). Public author pages located on 2026-10-20 are listed in `docs/repair_round1_baseline_audit.md`. That listing is not a request to email them.

## Course / metadata

1. What are the confirmed Group 23 member names and emails for this COMP3314 report?

## Printed SSC mathematics

2. In the 2015 implementation, was the linear system \(G=(S+\gamma\widetilde L)^{-1}SF\) (printed Eq. 13) or \((S+2\gamma\widetilde L)G=SF\) (stationary point of printed Eq. 8 under an ordered-pair sum)?
3. Was \(S\) an \(n\times n\) diagonal over sample-row residuals, or the embedding-dimension diagonal printed in Eq. 10?
4. Was Algorithm 1 line 10 (\(G\leftarrow(S+\gamma\widetilde W)^{-1}SX\)) executed as printed, or is it a typesetting substitute for Eq. 13?

## Unspecified solver choices

5. What numerical rule defined the Gaussian bandwidth \(\delta\) on the feature graph and on the embedding graph?
6. What matrix was used for \(G_0\)? If \(G_0=F\), how was the undefined \(1/(2\|h_i\|_2)\) entry handled on the first iteration?
7. For the final \(K\)-means, was initialization uniform-random centres, \(k\)-means++, or another draw, and was there an inner `n_init` besides the 50 recorded runs?
8. How should the sentence “repeat each clustering 50 times … report the results corresponding to the best objective function values” be combined with the printed mean±standard deviation? Which objective was “best”?

## Graph and embedding

9. Was the kNN graph the union (OR) of directed neighbours, or mutual (AND)?
10. Were the Laplacian eigenvectors row-normalized before shrinkage or before \(K\)-means (Ng–Jordan–Weiss), or used as raw coordinates?

## Datasets

11. For ORL, were the inputs native AT&T \(92\times 112\) images resized to \(32\times 32\), and if so with which interpolation? They were not Olivetti \(64\times 64\).
12. For Extended Yale B, which cropped archive and which resize produced the 2414×38 matrix used in the tables?
13. For UMIST / Sheffield, how was a 564-image subset obtained? Archives recovered here contain 1012 uncropped PGM or 575 cropped \(112\times 92\) images, not 564.
14. For BinAlpha, what parent pool and random seed produced 26 letters × 30 images? Binary Alphadigits (36 classes) is a different set.
15. For MSRA50, what is the URL and identity of the 1799-image / 12-class collection? MSRA-B, MSRA10K, and MSRA-TD500 were not substituted.
16. For AR, which 840-image protocol was used, and is a research snapshot still distributable?

## SPLS / SLPS

17. Can Section 3 of Hou et al., IPM 2013 (the approximated solution / updates) or author code be shared for a faithful SPLS reimplementation? The open abstract does not contain the updates. We did not implement a substitute.

## What we are not asking them to endorse

We are not asking the 2015 authors to confirm our ORL 53.3% or YaleB 19.5% as their result. Those are Our Reproduction under documented assumptions. The ORL 76% table cell was **not** reproduced here.
