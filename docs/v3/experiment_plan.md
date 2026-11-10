> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# v3 experiment plan

Historical cells: 72.
Executable historical cells: 32.

Supplemental versions are not additional historical cells.
Labels are not used to choose seeds, gamma, dimension, or which YaleB preprocessing is primary.
Y0 is the locked input. Y1--Y3 are diagnostics.
PCA dimensions are a grid. Inertia is not compared across dimensions.
SSC E8 and E13 are separate reconstructions of one SSC cell.

- AR__kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__sc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__pca_kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__pca_sc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__lda_kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- AR__llc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__spls: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- AR__ssc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- JAFFE__kmeans: executable=True status=PLANNED blocker=None
- JAFFE__sc: executable=True status=PLANNED blocker=None
- JAFFE__pca_kmeans: executable=True status=PLANNED blocker=None
- JAFFE__pca_sc: executable=True status=PLANNED blocker=None
- JAFFE__lda_kmeans: executable=True status=PLANNED blocker=None
- JAFFE__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- JAFFE__llc: executable=True status=PLANNED blocker=None
- JAFFE__spls: executable=True status=PLANNED blocker=None
- JAFFE__ssc: executable=True status=PLANNED blocker=None
- ORL__kmeans: executable=True status=PLANNED blocker=None
- ORL__sc: executable=True status=PLANNED blocker=None
- ORL__pca_kmeans: executable=True status=PLANNED blocker=None
- ORL__pca_sc: executable=True status=PLANNED blocker=None
- ORL__lda_kmeans: executable=True status=PLANNED blocker=None
- ORL__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- ORL__llc: executable=True status=PLANNED blocker=None
- ORL__spls: executable=True status=PLANNED blocker=None
- ORL__ssc: executable=True status=PLANNED blocker=None
- UMIST__kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__sc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__pca_kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__pca_sc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__lda_kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- UMIST__llc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__spls: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- UMIST__ssc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- BinAlpha__kmeans: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__sc: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__pca_kmeans: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__pca_sc: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__lda_kmeans: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- BinAlpha__llc: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__spls: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- BinAlpha__ssc: executable=False status=SUBSET_UNVERIFIED blocker=SUBSET_UNVERIFIED
- MSRA50__kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__sc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__pca_kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__pca_sc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__lda_kmeans: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- MSRA50__llc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__spls: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- MSRA50__ssc: executable=False status=BLOCKED_DATA blocker=BLOCKED_DATA
- YaleB__kmeans: executable=True status=PLANNED blocker=None
- YaleB__sc: executable=True status=PLANNED blocker=None
- YaleB__pca_kmeans: executable=True status=PLANNED blocker=None
- YaleB__pca_sc: executable=True status=PLANNED blocker=None
- YaleB__lda_kmeans: executable=True status=PLANNED blocker=None
- YaleB__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- YaleB__llc: executable=True status=PLANNED blocker=None
- YaleB__spls: executable=True status=PLANNED blocker=None
- YaleB__ssc: executable=True status=PLANNED blocker=None
- USPS__kmeans: executable=True status=PLANNED blocker=None
- USPS__sc: executable=True status=PLANNED blocker=None
- USPS__pca_kmeans: executable=True status=PLANNED blocker=None
- USPS__pca_sc: executable=True status=PLANNED blocker=None
- USPS__lda_kmeans: executable=True status=PLANNED blocker=None
- USPS__lda_sc: executable=False status=BLOCKED_METHOD blocker=BLOCKED_METHOD
- USPS__llc: executable=True status=PLANNED blocker=None
- USPS__spls: executable=True status=PLANNED blocker=None
- USPS__ssc: executable=True status=PLANNED blocker=None
