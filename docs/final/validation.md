> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# Final validation

## Fresh environment and single-branch checkout

`fresh_environment.json` records the actual temporary directory with spaces, depth-1 single-branch clone, new virtual environment, exact dependency freeze, commands, exit codes and log hashes. The repository's ignored data pointer and old branches are absent. PYTHONPATH and all legacy/root environment variables are cleared. Installation uses a verified existing CA bundle because the host Python had no usable default CA; certificate verification was never disabled.

PASS: editable install, no-data synthetic smoke, 53 focused certificate/release/provenance/legacy compatibility tests, no-data release rebuild, and real ORL/JAFFE three-seed smoke using the physically separate data root. Rebuilt coverage, selected manifests and complete configuration tables are byte-identical. The smoke is not counted as a 50-trial experiment or a published performance result.

## Scientific checks

- Feasible dual lower bounds versus independent Clarabel small problems, analytic one-edge cases, squared versus radial domains, exact E8/E13 scaling, zero graph/gamma and coincident rows.
- Capped objective nonincrease, local/global distinction, two starts and exhaustive tiny-state reference; model fitting interfaces accept no labels.
- Native perturbation domains and zero-change identity, including USPS [-1,1]. Corrected robustness reconstructs the full corresponding method.
- All release hashes, decompressed CSV hash, complete seed keys, duplicate-key rejection and safe replacement behavior. Empty legacy aggregation refuses overwrite.
- Continuation metadata corrected with zero changes among 144 selected config IDs; old display manifests retained.
- Raw ORL/Yale source-archive preparation in a directory with spaces reproduced all eight existing prepared-array hashes exactly.

Focused local tests: `python -m pytest tests/next_round tests/v3 tests/v3_theory -q` -> 53 passed. This statement does not imply every historical or data-dependent test in the repository was run.

Final LaTeX/render and post-publication clone outcomes are recorded below and in `publication_status.json`. Member names were subsequently supplied and added; course-system upload and future presentation attendance are outside this GitHub task.

Final local focused suite: **55 passed** after two additional empty/hash-coverage release tests. Final report: **3 main pages, 11 total**, all pages rendered and visually inspected, no overfull boxes or unresolved references/citations; PDF hash and source/copy consistency are in `report_verification.json`.

## Final candidate and GitHub verification

`final_candidate_verification.json`: a second brand-new venv installed all 35 exact observed dependencies in a new directory with spaces. Its depth-1 single-branch clone passed 55 tests, synthetic, no-data rebuild, explicit ORL/JAFFE smoke and forced LaTeX compilation. All 72 cells, 144 selections and complete configuration tables match byte-for-byte; compiled PDF text is identical. Key logs are committed in verification_logs.

`publication_status.json` records exact-lease publication, default-branch verification and individually leased deletions. `post_publish_verification.json` records a new GitHub v3 depth-1 single-branch clone, isolated module import, synthetic and byte-identical no-data rebuild. Default v3 and only remote v3 were verified after deletion. Subsequent audit-record commits change no scientific source, data, measurements or report PDF.
