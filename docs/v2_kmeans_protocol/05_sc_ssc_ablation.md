# SC versus SSC

Under a matched protocol, gamma = 1, the SSC minus SC accuracy gap is about one point or smaller, and it is sometimes negative.

| Version | P1 | P2 | P3 | P4 | Paper SSC − SC |
| --- | --- | --- | --- | --- | --- |
| ORL att92 | +1.09 | 0.00 | +0.07 | −0.75 | +3.3 |
| JAFFE zenodo | −0.09 | 0.00 | −0.21 | 0.00 | +5.1 |
| YaleB cropped2414 | −0.72 | −0.25 | −0.23 | −0.04 | +15.0 |
| YaleB dengcai32 | −0.61 | −0.17 | +0.07 | −0.54 | +15.0 |
| USPS libsvm | −0.04 | +0.13 | +0.20 | +0.13 | +11.2 |

The same pattern holds for NMI at gamma 1. ORL P1 NMI is 80.47 (SC) and 81.13 (SSC). YaleB cropped NMI is about 26.9 (SC) and 26.2 (SSC), whereas the paper reports 55.6 and 46.8.

Changing the initializer moves SC and SSC together. A high SSC accuracy on JAFFE under k-means++ is not evidence that shrinkage helped: SC reaches the same 95.31. On ORL, greedy k-means++ puts both representations near 78–79, above the paper SSC value of 76.0 and well above the paper SC value of 72.7, with almost no shrinkage gap.

BinAlpha `CANDIDATE_BIN_ALPHA` and UMIST `precropped575` are `NOT_COMPARABLE` to the paper. On those files the gamma = 1 shrinkage gap is also under one point for the greedy protocols, and the random-mean gap is negative (BinAlpha P1 −2.42, UMIST P1 −1.39).

Inertia was never compared across F and G. P2 and P4 choose the seed separately on each representation. On ORL the random-best seeds differ (F seed 21, G seed 12) and the selected accuracies still match at 62.25.
