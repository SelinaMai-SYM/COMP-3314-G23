> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# Reproduction root cause notes

These notes restate the frozen measurements. They do not assign one cause to every gap.

## ORL
K-means is close to the printed ACC. SC and SSC at the prespecified gamma=1 point are lower than K-means and lower than the printed SC/SSC numbers. The gap is therefore not explained by a failed K-means baseline.

## JAFFE
The per-run mean is well below the printed SC/SSC numbers, while the separate min-inertia selection inside a batch is higher. The primary table keeps the per-run mean. Selection is not used as the historical protocol.

## USPS
At gamma=1, SSC stays near SC. The primary E8 cell is random-init ACC 61.70 ± 8.09. Gamma=1000 was given extra solver iterations in the frozen runner because it was a prespecified priority point. Reaggregation of `ssc__Y0__E8__g1e+03.trials.jsonl`, seeds 0–49, gives random ACC 0.7387 ± 0.0753 and greedy ACC 0.7992 ± 0.0015. Those figures stay in the sensitivity grid.

## UMIST and BinAlpha
The historical UMIST cell is 564 images. The available 575-image sets are supplemental. The BinAlpha candidate, including any seed-0 subset, is not an exact historical cell.

## YaleB
Both 2414-image versions remain far from the printed SC and SSC numbers under Y0. Y3 is not promoted when its ACC is closer. See the controlled repair tables.

## Still blocked
LDA-SC is undefined in the source paper. AR 840, UMIST 564, and MSRA50 do not have a verified matrix. No samples were deleted to force a count of 564.
