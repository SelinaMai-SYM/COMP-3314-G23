# K-means

Status: `FAITHFUL_REIMPLEMENTATION`

Original paper: Classical Lloyd K-means. Chang et al., AAAI 2015, treat it as the standard clustering baseline and do not cite a single algorithm paper for it. Setup says "random initialization".

Default `init="random"` is the historical protocol default. `init="k-means++"` is accepted as a **B_AMBIGUITY** reconstruction of an unspecified modern alternative; it is not the silent default and must not be switched in place.
