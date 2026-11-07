# Comparison with Chang et al. (2015)

Paper numbers are the audited Tables 1 and 2 in `configs/paper_2015_reference.yaml`. Gaps below are percentage points, our value minus the published mean. Exploratory gaps are not exact-reproduction errors: image interpolation, the JAFFE file, and the YaleB matrix identity are not certified as the authors' files. USPS is the standard 9298-sample LIBSVM split; the paper does not publish a checksum. BinAlpha, UMIST, AR, and MSRA50 gaps are `NOT_COMPARABLE`.

Published SSC accuracy: ORL 76.0, JAFFE 81.2, YaleB 49.8, USPS 75.5.
Published SC accuracy: ORL 72.7, JAFFE 76.1, YaleB 34.8, USPS 64.3.

At gamma 1:

- ORL SSC is 18.7 points below the paper under P1 and 13.8 below under P2. P3 is 2.4 above the paper and P4 is 2.3 above. SC under P3 is 78.33, which is 5.6 above the paper SC value, so the protocol that nears the paper SSC number misses the paper SC number in the other direction.
- JAFFE SSC P1 is 12.8 below the paper. P2, P3, and P4 are about 14 points above it. SC is above the paper by the same margin.
- YaleB cropped SSC is 27 to 32 points below 49.8 under every protocol. SC is 13 to 16 points below 34.8. On dengcai32 the highest primary SSC cell is P3 at 25.43, still about 24 points below 49.8. The highest primary SC cell is P4 at 25.64, about 9 points below 34.8.
- USPS SSC at gamma 1 is 13.8 below the paper under P1 and about 9.7 below under P3/P4. SC is within about 2.6 of the paper SC mean under P1 and about 1.3 above it under P3. The missing SSC points are not matched by a similar SC deficit.

The published YaleB table itself has a higher SSC accuracy and a lower SSC NMI. Our YaleB cells are low on both scores, so we do not reproduce that tradeoff.

No protocol at gamma 1 reproduces the published SC-to-SSC gaps of +3.3 (ORL), +5.1 (JAFFE), +15.0 (YaleB), and +11.2 (USPS) at the same time.
