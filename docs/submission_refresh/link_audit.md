# English and publication-link audit

The link audit supports the history-preserving `v3` to `main` migration. It does
not perform a push, rename or default-branch change. Current publication state
must be verified separately after the authorized migration.

The machine-readable inventory is
[`results/submission_refresh/link_audit.csv`](../../results/submission_refresh/link_audit.csv),
with [scan metadata](../../results/submission_refresh/link_audit_summary.json) and
[ordinary public HEAD evidence](../../results/submission_refresh/external_link_checks.json).
The scanner reads tracked and delivery text files, including decompressed scalar
records. Its initial pass covered 13,184 text files and two gzip inputs. No
project-owned GitHub URL used the `v1`, `v2` or `v3` branch. The report's project
link already names future `main`; relative navigation resolves to paths in this
checkout. No workflow files or branch filters were present.

Current navigation is checked in the README, report sources/README, maintained
data/source notes, presentation outline and submission/subset documentation.
Each relative target receives a future `main` URL and an explicit local status:
tracked file, directory, pending addition, missing, or local-only unpublished
object. Local presence does not establish that an object has been pushed or that
the future URL already returns HTTP 200. Original immutable commit citations,
experiment-version module names and other repositories' branches are preserved.

An initial markup-parsing error included closing Markdown parentheses in several
requested URLs. The parser was corrected and the canonical targets were checked
again; those draft false 404 responses were not classified as provider failures.

The bounded public-source pass checked twelve distinct ordinary URLs and received
HTTP 200 for each: pinned ClustPy, EnSC, EBSA and Fast-CD source pages; AR/UMIST
raw-source leads; the Fast-CD paper; and the other selected source/documentation
links recorded in the machine table. A HEAD response is an availability check,
not a dataset-content, license or historical-identity verification. Later scans
reuse those explicitly timestamped external checks; post-rename project `main`
checks are requested afresh. The SharePoint source-recovery endpoint is not
retried by this audit, so its previous HTTP 429/Retry-After record does not restart a
source-recovery allowance or become a claim of permanent deletion.

At this preliminary stage, nine unique current target paths remain absent:

- `docs/submission_refresh/research_findings.md` and `final_handover.md`;
- `results/submission_refresh/baseline_diagnostics.csv`, `execution_coverage.csv`,
  `extension_gate.json` and `extension_results.csv`;
- `results/subset_search/closest_matches.csv`, `execution_coverage.csv` and
  `rounding_confirmation.csv`.

These are pending required campaign deliverables. Their links must be resolved
before publication. The audit does not insert placeholder results to make those
paths appear complete. The final machine inventory, rather than this dated
preliminary list, determines the remaining local or public-link issues.

Eighteen earlier English analysis/preflight documents now carry a historical-scope
banner. Their existing scientific text, measurements and recorded publication
state remain unchanged. This prevents an earlier “default v3” or approval-request
record from reading as the current instruction. The
[editorial hash record](link_editorial_changes.json) preserves before/after hashes
and the commit containing the earlier bytes. No archive, original source
manifest, release-hashed input or fitting module was edited in this pass.

The [presentation outline](../final/presentation_outline.md) now follows the
combined research story and links current authoritative tables. It lists the four
confirmed authors, leaves speaking roles for the team to agree, and requires
actual coverage and gate status beside results. It introduces no measured value
or individual contribution claim. English prose retains names, mathematical
notation, identifiers and legal attribution; the broader
[language audit](language_and_editorial_audit.md) records the repository-wide pass.

Run a local/future-URL audit before publication:

```bash
python3 scripts/submission_refresh/link_audit.py --external-limit 12
```

After GitHub has actually renamed the branch and the final files are committed,
run the project HTTP checks:

```bash
python3 scripts/submission_refresh/link_audit.py --published --external-limit 12 --project-limit 80
```

Inspect every missing/unpublished target and non-200 project response. External
checks remain bounded and retain status, redirects, final URL, timestamp and
Retry-After where supplied. The scanner does not bypass access restrictions,
send messages, change protections or alter repository settings.

<!-- BEGIN CURRENT LINK STATUS -->

## Current machine-verified snapshot

Prepublication local/future-main pass at 2026-11-10T07:05:23Z, local commit `a24dcda0d49e39da51b44dd414541370dba0cd1c`. Legacy project branch URLs: 0. Missing current target paths: 9. Fresh project HTTP requests: 0; response counts: {}. Public main availability is pending the separate rename verification.

<!-- END CURRENT LINK STATUS -->
