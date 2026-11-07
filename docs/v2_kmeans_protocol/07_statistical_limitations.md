# Statistical limitations

P2 and P4 are one partition from one batch of 50. Their accuracy has no standard deviation until several independent batches are finished. The repeatability SD is that across-batch SD. It is not the SD of the 50 runs, and it is not what the paper's "mean ± SD" column has to be.

Ten batches were completed for ORL, JAFFE, both YaleB matrices, USPS, BinAlpha, and UMIST `precropped575`. That is our reconstruction of best-of-50 variability. It does not show that the authors averaged independent batches.

The gamma that maximizes labeled accuracy is `ORACLE_BEST_TEST_ACC`. It is computed after seeing the test labels. It is not a selected model. Every grid point remains a prespecified measurement and is reported, including the ones that lower accuracy.

Most gamma = 1 SSC solves did not converge. A numerical match or mismatch on those cells is about the returned iterate. USPS at gamma 1 did converge (iteration 298). USPS at gamma `1e3` did not.

Dataset identity is unresolved for every face benchmark. USPS is the standard split without an author checksum. AR and MSRA50 were not run. UMIST 564 was not reconstructed by dropping images. YaleB `cropped2414` and `dengcai32` are one benchmark counted once.

K-means++ here is the installed scikit-learn 1.8.0 greedy initializer, not a new algorithm. Vanilla seeding with `n_local_trials=1` is a different control.
