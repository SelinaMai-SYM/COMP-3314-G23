> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# v3 resource recovery round 2

Raw matrices and publisher PDFs stay in gitignored `resources/private/` directories.
A download failure is not evidence that the resource does not exist.
Count agreement is not historical identity.

| Resource | Status | Identity | Eligibility |
| --- | --- | --- | --- |
| `msra50_data` | BLOCKED_NO_VERIFIED_DATA_URL | BLOCKED_NO_VERIFIED_DATA_URL | blocked |
| `lda_sc_definition` | METHOD_DEFINITION_UNRESOLVED | METHOD_DEFINITION_UNRESOLVED | blocked |
| `slps_hou2013_pdf` | DOWNLOADED_VALID_FORMAT | FULL_TEXT_VERIFIED_LOCAL | method_text_only |
| `ar_lzuf_AR_mat` | DOWNLOADED_VALID_FORMAT | DOCUMENTED_SUPERSET_ONLY | not_eligible |
| `umist_lzuf_mat` | DOWNLOADED_VALID_FORMAT | INSUFFICIENT_FOR_TARGET_REPRODUCTION | not_eligible |
| `umist_zenodo_3634017_mat` | DOWNLOADED_VALID_FORMAT | NON_EXACT_UMIST575 | diagnostic_not_scheduled |
| `umist_roweis_cropped_mat` | DOWNLOADED_VALID_FORMAT | NON_EXACT_UMIST575 | diagnostic_not_scheduled |
| `binalpha_roweis_parent_mat` | DOWNLOADED_VALID_FORMAT | PARENT_DATA_VERIFIED | parent_not_historical_subset |
| `ding_li_2007_pdf` | DOWNLOADED_VALID_FORMAT |  |  |
| `wu_scholkopf_2006_llc_pdf` | DOWNLOADED_VALID_FORMAT |  |  |
| `shi_ncut9_zip` | DOWNLOADED_VALID_FORMAT |  |  |
| `ssc_monash_mirror_pdf` | DOWNLOADED_VALID_FORMAT |  |  |
| `ssc_aaai_official_pdf` | DOWNLOADED_VALID_FORMAT |  |  |
| `ar_lzuf_github_repo` | DOWNLOADED_VALID_FORMAT |  |  |
| `ar_lzuf_github_api` | DOWNLOADED_VALID_FORMAT |  |  |
| `shi_ncut_software_page` | DOWNLOADED_VALID_FORMAT |  |  |
| `umist_roweis_docs` | DOWNLOADED_VALID_FORMAT |  |  |
| `slps_stage_full_text` | FULL_TEXT_VERIFIED_LOCAL | FULL_TEXT_VERIFIED_LOCAL | method_text_only |
| `slps_stage_specification` | METHOD_SPECIFICATION_COMPLETE | METHOD_SPECIFICATION_COMPLETE | specification_only |
| `slps_stage_implementation` | IMPLEMENTED | IMPLEMENTED | executable_where_data_exists |
| `slps_stage_numerical` | NUMERICALLY_VALIDATED | NUMERICALLY_VALIDATED | executable_where_data_exists |
| `binalpha_letters26x30_seed0` | SUBSET_RECONSTRUCTED | HISTORICAL_INDICES_UNKNOWN | supplemental_not_historical |

LDA-SC has no verified definition in the SSC paper, the SLPS paper, or Ding and Li.
Ding and Li define LDA-Kmeans. SLPS calls that method LdaKm.
MSRA50 has no direct data URL. The arXiv HTML page was not saved as a dataset.
LDA-SC remains METHOD_DEFINITION_UNRESOLVED after reading SSC, SLPS, and Ding and Li.

## Procrustes cross-check

Ncut_9/discretisation.m computes `[U,S,V] = svd(Discrete' * EigenVectors)` and, on non-terminal iterations, sets `R = V*U'`.
`baselines/llc/llc.py` uses `R = Vt.T @ U.T` after `svd(discrete.T @ embedding)`, which is the same factor.
The archive is Jianbo Shi's Normalized Cuts package. It was not executed, and it is not LLC or SSC author code.
