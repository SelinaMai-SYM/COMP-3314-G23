# Optional common-mask cost cohort

`scripts/submission_refresh/optional_ar_cohort.py` is prepared only. **It has not been invoked, and no optional cohort or primary copies have been frozen by this editing task.** AR common masks remain the last priority after the cost-frozen graph work and conditional G4/G5 stage close. The helper never opens matrix objects or decodes performance fields. It projects only object references/status from completed fixed-AR metadata; trial/summary values are skipped. Source bytes are hashed for provenance without entering the selection calculation.

First invocation requires the existing shared ledger with no active reservations, its unchanged 36-hour maximum and at least two hours reserved, all four fixed AR inputs completed, and an explicit terminal-decision JSON. Empty ledger alone is insufficient. The terminal JSON uses schema `optional-ar-terminal-decision-v1`, three true flags `graph_design_terminal`, `G4_G5_terminal`, `unrun_work_frozen`, and `G4_G5_disposition` equal to `COMPLETED`, `FAILED_OR_INCOMPLETE_WITHIN_ALLOWANCE` or `NOT_PERMITTED`. Its `evidence` object must contain `graph_coverage` and `gate`, each with a checkout-relative `path` and exact `sha256`. The helper checks the actual full 362-task coverage and rejects live/pending controllers. A completed G4/G5 disposition must match the recorded complete four-benchmark state; failed/incomplete or unpermitted work remains explicitly qualified.

The CPU estimate is fixed before common-mask scores:

```text
estimate_per_mask = 2 * (blind_AR_profile_total_CPU + 33 * 50 * rounding_CPU_per_seed)
CPU_count_cap = floor(remaining_nonfinalization_CPU / estimate_per_mask)
```

The declared AR_first7 blind profile must contain the full ten E8/E13 five-gamma timing points. Total CPU uses the larger of recorded whole-process and callback CPU when both exist. Its exact processed X/y fingerprint, Y0 and dimensions must match the frozen input. Older metadata-only sample-manifest versions are preserved and qualified rather than confused with changed pixels. The exact profile bytes and both manifest hashes are recorded.

The profile's original blinding/source/environment provenance is retained. Recorded versus current SSC/rounding source-byte differences are listed, while archived effective-code identity is explicitly not asserted by this cost planner. Differing or unavailable archived behavior remains a cost-approximation qualification; it never licenses reuse of a scientific fit or invents a solver/source identity.

Disk accounting uses file sizes and reference byte counts only. It reserves two extra copies of the entire existing artifact store for archive/recovery, an additional 8 GiB free buffer, and `ceil(3 * 1.25 * max_fixed_AR_unique_object_bytes)` for every new mask. The maximum comes from unique references in the four completed fixed AR inputs. The selected count is the minimum of the CPU cap, disk cap and eligible family size. All references, source hashes, the shared ledger and disk snapshot, and the full cost formula are frozen. An estimate does not guarantee completion; the existing 1200-second per-input cap and scheduler's shared allowance still control execution.

The helper sorts canonical unaliased AR_common_mask IDs, applies `numpy.random.RandomState(20261110).permutation`, and freezes a prefix without score access. Alias IDs, the full canonical permutation, selected IDs and every unscheduled canonical ID remain explicit. It preserves the original 1202-input cohort/order bytes as `executable_cohort_primary_v1.json` and `executable_cohort_order_primary_v1.json`, including every existing primary override cap. Default cohort/order become their original lists plus the optional prefix, so aggregation/reporting see the total scope. The optional inputs retain cap 1200.

The immutable decision is `configs/subset_search/optional_ar_common_cohort_v1.json`; it is also a usable optional-only `--cohort` for the existing runner. Its sibling `_order.json` preserves permutation order. Execute only this optional-only cohort after checking its selected count is positive; a zero-count cohort is never launched. Do not rerun unlaunched primary scope through the default union merely because the optional family opened.

The frozen decision is written atomically and exclusively before publishing the union files. It seals the exact publication payloads, versioned primary copies, terminal evidence and profile copy. Every target is validated before writes. If interrupted, resume accepts only the original/expected target hashes and repairs the same bytes; an independently changed target fails. Resume verifies the append-only ledger ancestry, catalogue/protocol and frozen payloads, never recalculates the prefix from updated costs, disk space or scores. The helper does not alter the shared ledger; its small metadata utility cost must be included in the existing campaign bookkeeping.

After the root workflow creates the terminal record and all prerequisites hold, the intended explicit invocation is:

```bash
python scripts/submission_refresh/optional_ar_cohort.py \
  --artifact-root ARTIFACT_ROOT \
  --profile-record task_status/DECLARED_BLIND_AR_PROFILE.json \
  --terminal-record PATH_TO_TERMINAL_DECISION.json
```

This is an invocation template, not evidence of a run. No scientific source library, protocol, catalogue, solver or search grid is changed. Prepared fixtures cover cost/disk caps, deterministic canonical order and alias exclusion, primary-byte preservation, immutable resume, interrupted-publication recovery and failure before writes; actual test outcomes belong to the shared validation record.
