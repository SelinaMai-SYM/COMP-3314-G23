# Draft section for a later report

This file is the copy-ready draft for a future section 6. It is not inserted into `report/main.tex`. Numbers are the gamma=1 cells in `results/extension_research/extension_matrix.csv` unless a gamma is named. BinAlpha and UMIST are non-exact versions. YaleB extension numbers are not a claim that the published table was recovered.

## 6. Extensions of the reconstructed SSC step

### 6.1 Question

Section 5 fixes the comparison at Equation (8) with Laplacian coefficient 2, gamma = 1, k = 5, and random Lloyd. On that control the fresh run gives ORL SSC ACC 0.57265 against SC 0.5618, JAFFE 0.6843 against 0.6853, USPS 0.6170 against 0.6174, and YaleB cropped2414 0.1763 against 0.1834. The paired seed interval for ACC(G) − ACC(F) is above zero only for ORL, by about one point, and below zero for YaleB. The published YaleB entries, 34.8% SC and 49.8% SSC, stay outside every diagnostic and every extension tried here. The implementation check found no bug in the solver or the graph code.

The extensions ask a narrower question: if the weight, the data-term scale, the embedding graph, or the K-means protocol is changed by a rule fixed before looking at ACC, does the SC-to-SSC gap move? Gamma is not chosen by test ACC. A later maximum over the gamma grid is an oracle upper bound, not the reported operating point.

### 6.2 What was added

Nine extensions live under `method_extension/e01` through `method_extension/e09`. E01 reweights edges by how often they recur under small perturbations of F. E02 scales each point's data term by an unsupervised mutual-neighbor rate, with the weighted objective kept distinct from Equation (8) unless every weight is 1. E03 applies a local scale to the feature graph, the shrinkage graph, or both. E04 either degree-normalizes W or divides by the total edge weight; the second form is a global rescaling of gamma and is a control, not a new mechanism. E05 mixes the feature-space and pixel-space graphs, or keeps an edge only when both graphs support it. E06 rebuilds W three times from the latest G, with F held fixed and with no claim that the alternation converges globally. E07 clusters the same F and the same G with k-means++, with one minimum-inertia assignment, and with a majority vote of the 50 random runs. E08 freezes E01 and E02 together. E09 puts the E01 recurrence on the local-scale shrinkage graph. Mutual kNN is kept as an auxiliary baseline. On JAFFE it scores 0.6837, against the union control 0.6843.

When the extra weights are turned off, G matches the original E8 solve within absolute and relative tolerance 1e-5.

### 6.3 What the gamma = 1 matrix shows

The run covers ORL, JAFFE, both YaleB matrices, USPS, the candidate BinAlpha set, and the precropped UMIST set, each with 50 matched seeds, plus the gamma grid. MSRA50 and AR were not run. Three USPS cells at gamma = 1e6 (E06, E08, E09) stopped at a 180-second solver timeout and are recorded as failed, with blank ACC.

Shrinkage at gamma = 1 remains a small effect next to initialization. k-means++ on the control representation raises ORL SSC ACC from 0.573 to 0.784 and JAFFE from 0.684 to 0.951, while the gap between G and F under that initializer is about zero. The same initializer lifts YaleB cropped only to 0.215, still far below 0.348, and it lifts both F and G. Treating k-means++ as the paper protocol would also make JAFFE on F alone exceed the published SSC number, which the rest of the table does not support.

Among graph edits, fusing the feature-space and pixel-space affinities is the change that enlarges ACC(G) − ACC(F) on more than one set: ORL by 0.017, USPS by 0.022, and the non-exact BinAlpha set by 0.008. Against the E8 control those intervals are +0.007, +0.022, and +0.032. On YaleB the fused graph becomes connected and the gain against E8 is about 0.006, while G is still not above F. Keeping only the overlapping support of the two graphs fragments YaleB into hundreds of components and USPS into thousands, and ACC does not rise.

Local scale on the feature graph raises the embedding itself. ORL E03-A reaches SSC ACC 0.588 with a spectral-clustering baseline already near 0.584. JAFFE E03-A reaches 0.717 against an SC value of 0.716. USPS E03-A reaches 0.653 against an SC value of 0.661. The shrinkage step on that new embedding is not an additional gain. Local scale on the shrinkage graph alone lowers ACC on every set in the matrix.

Degree normalization and the reliability weight move ACC by amounts that are small beside the K-means standard deviation, or they lower it. Dividing by the total edge weight returns G to F, so the method reports the SC number. Where SSC was below SC, that return looks like a gain over E8 and is only the undone shrinkage. The two combinations, E08 and E09, follow their weaker ingredient. E09 in particular follows local-scale W and is below E8 on ORL, JAFFE, both YaleB matrices, BinAlpha, and UMIST.

### 6.4 YaleB and the other table gaps

The cropped and Deng Cai matrices are not the same pixels. Both give SC near 0.18–0.20 and SSC a little lower at gamma = 1. Every pre-specified diagnostic, including mutual symmetrization, row normalization, and k-means++, stays below the published 34.8% and 49.8%. Those higher diagnostic numbers use a different graph or a different initializer and are not adopted as the original protocol. The extensions do not close this gap, so they are not presented as an algorithmic explanation of Table 1.

On the other reconstructed sets the same control sits below the published SC cells before shrinkage: ORL 0.562 against 72.7%, JAFFE 0.685 against 76.1%, USPS 0.617 against 64.3%. USPS at the stored grid point gamma = 1e3 scores 0.739, nearer the published SSC figure of 75.5%, and at gamma = 1e6 scores 0.388. That grid is reported in full. Gamma = 1 remains the comparison point because the paper text treats it as the usual setting, with USPS already named as an exception whose exact table value is not listed.

### 6.5 Limits

The ± values are the spread of K-means on one fixed G. Many gamma = 1 solves are nonconverged at 300 iterations; the scored output is the returned iterate. One inertia-best or consensus label has no seed interval. Bootstrap intervals do not represent a new sample of images. Objective values under different weights are different functions and are not ranked against each other. BinAlpha and UMIST are not exact paper releases. No gamma and no extension was selected by maximizing test ACC.
