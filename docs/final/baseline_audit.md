> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# Baseline audit and corrections

Audit date: 2026-11-09, Hong Kong/Shanghai. Reviewed snapshot: `95d599918627379b21f665b9b2754dd3852dc6dc`; local starting v3: `7406f6b030130100414faace1e919b51ce0cf56b`. Scientific trees were identical; the migration-approval document differed and is preserved in `archive/docs/`. Source/status/parameter evidence below comes from that snapshot unless a new result file is named.

| Claim checked | Actual evidence and action |
|---|---|
| Root README/report were outdated | Archived the old README/report sources; replaced current root/report with manifest-driven prose and tables. Historical statements do not control current authorization |
| SLPS/SPLS and LDA-SC | `baselines/spls`, `configs/v3/methods.yaml`, historical SPLS job metadata show a one-shot implementation; LDA-SC remains method-blocked, not a fabricated faithful baseline |
| Machine workspace path | `configs/v3/campaign.yaml` had a real absolute path used by CLI/aggregate. Current defaults derive from file locations |
| Loader root mismatch | v2 appended `benchmarks/`, v3 did not. All current loaders now share `benchmarks.data_paths`; old worktree pointers and runtime fallbacks removed |
| Frozen package | 3059 jobs, 378550 trials, 6563 configurations. `543f10e6607739e0c77fd8191ebabc2ef260e814d46efa6115bc7fb91122925b` is SHA256 of the **decompressed CSV**, not the gzip; compressed SHA256 is in the release manifest |
| Empty aggregation | Old aggregate read only ignored `runs/v3_reproduction/jobs`. New no-data entry reads committed trials/metadata and validates before replacement; legacy empty aggregation now rejects rather than replacing tables |
| 72 cells | `coverage_72_cells.csv`: 32 completed, 24 data-blocked, 8 method-blocked, 8 subset-unverified; rebuilt exactly. Supplemental versions do not fill historical cells |
| Measured but uncollapsed grids | PCA-Kmeans, PCA-SC and SLPS have measured configurations. Their fixed reference remains uncollapsed; LLC and LDA use existing source-defined reference settings |
| Old closest rule | Old `compare_paper.oracle_and_closest` used joint squared ACC/NMI distance. Current display uses absolute unrounded ACC distance, complete batch 0, same-row NMI/SD, frozen tie/deviation rules |
| E/X extension history | All historical E01-E09 and X1-X5 results retained. No rerun/rebranding of the old stability/multi-k/inverse-fidelity proposals as a new contribution |
| 88 old verified statuses | Individual audit found analytic G=F checks, recorded-primal gap certificates, and six returned-iterate claims still above the new tolerance. Seven original statuses came from generic solver agreement rather than the simple G=F path. See `results/next_round/legacy_certificate_audit.csv`; no blanket invalidation |
| YaleB eigen diagnostics | `results/v3_final/yaleb_graph_stats.csv`: raw eigen residuals range from 1.3156786566050814e-15 to 6.293577742970126e-13. Large Gram error for row-normalized F is not raw eigenpair failure |
| E8/E13 | Undirected c=2*gamma*w. E13(nominal gamma) maps to E8(gamma/2). The selected-row audit uses effective gamma, not an unequal-objective comparison |
| Old robustness | Old held-out script did not rerun SSC and USPS was clipped to [0,1]. Historical table retained with invalidity annotation; new full-pipeline checks use declared native domains |

The original baseline F/W and G arrays are not identified by public scalar trials alone. New seeded reexecutions and same-F/W IRLS/PDHG audits have new run IDs and do not overwrite historical rows. Theory-cache audits explicitly name the persisted F/W they use. Unknown identity is not repaired by numerical proximity.
