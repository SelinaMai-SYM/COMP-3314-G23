# Deliverable and acceptance checkpoint

Snapshot: **2026-11-10 07:57:38 UTC**, local HEAD `4c8979a5f478467c13a9c4cffbc982e7d6a560fb` with working changes. This is an execution checklist, not a completion certificate. It applies to the main execution specification and the combined refresh/subset instructions supplied on 2026-11-10.

At that snapshot the shared ledger had **3.6995 charged CPU-core hours**, 69 charged entries and 2 active reservations. Active CPU was not included in the charged total. The maximum remains 36 additional core-hours, with 2 reserved for finalization; USPS remains capped at 6 within that total. Subsequent focused v2 validation passed and the primary subset cohort started. Final subset aggregation, graph promotion, reporting and publication remain pending; the dated ledger total above is not a live resource reading.

## I1-I20

“Present” means the file exists; its stated scope still controls. Missing outputs must be generated from authoritative records, without placeholder measurements.

| Item | Exact path | Snapshot / remaining acceptance |
|---|---|---|
| I1 | `docs/submission_refresh/preflight.md` | PRESENT. Present: starting tip, verified backup, data/artifact roots and shared allowance. |
| I2 | `docs/submission_refresh/language_and_editorial_audit.md` | PRESENT. Present snapshot; repeat after final tables/PDF and repository-description update. |
| I3 | `docs/submission_refresh/source_recovery.md` | PRESENT. Present: EBSA16 verified, Fast-CD bounded 429 attempts, parent acquisition/provenance. |
| I4 | `docs/submission_refresh/protocol_map.md` | PRESENT. Present; reconcile final actual coverage and deviations. |
| I5 | `docs/submission_refresh/issue_closure.md` | PRESENT. Present execution-stage ledger; close/reclassify only from final validation and run evidence. |
| I6 | `docs/submission_refresh/research_findings.md` | PRESENT. Present execution-stage findings; final selected values and gate/cost conclusions pending. |
| I7 | `docs/submission_refresh/experiment_log.md` | PRESENT. Present append-only log; continue through aggregation, confirmation and publication. |
| I8 | `results/submission_refresh/dataset_inventory.csv` | MISSING. Corrected audit and duplicate maps are committed under `results/submission_refresh/source_audit/`; `experiments/submission_refresh/inventory.py` validates these against the frozen initial source_inventory.csv and will generate this file, `dataset_inventory.v2.csv` and its manifest during final aggregation. |
| I9 | `results/submission_refresh/joint_metric_selection.csv` | PRESENT. Present historical joint mean selection; new subset matches remain a separate pending block. |
| I10 | `results/submission_refresh/endpoint_comparison.csv` | PRESENT. Present historical endpoint separation; new endpoints need final scalar aggregation. |
| I11 | `results/submission_refresh/baseline_diagnostics.csv` | MISSING. Pending aggregation of completed/failed baseline jobs and all-50 eligibility. |
| I12 | `results/submission_refresh/error_cases.csv` | MISSING. Pending G1 casebook aggregation; implementation availability is not a measured casebook. |
| I13 | `results/submission_refresh/graph_diagnostics.csv` | MISSING. Pending current/schema2 export; corrected historical-graph validation completed externally. |
| I14 | `results/submission_refresh/extension_results.csv` | MISSING. Pending actual graph block and aggregation, or explicit unrun coverage. |
| I15 | `results/submission_refresh/extension_gate.json` | MISSING. Pending actual fixed G3 evidence; absence is not a failed gate. |
| I16 | `results/submission_refresh/artifact_manifest.json` | MISSING. Pending authoritative object references, availability checks and verified export/recovery record. |
| I17 | `results/submission_refresh/execution_coverage.csv` | MISSING. Pending consolidated planned/completed/failed/timeout/unrun inventory. |
| I18 | `results/submission_refresh/resource_usage.json` | PRESENT. Present scheduler snapshot; final actual CPU, active reservations and supplementary costs pending. |
| I19 | `report/Group_23.pdf` | PRESENT. Present PRELIMINARY PDF; regenerate from final authoritative records and repeat full visual QA. |
| I20 | `docs/submission_refresh/final_handover.md` | MISSING. Pending final English handover, actual outcomes, tested/final commits and publication checks. |

The report sources `report/main.tex`, `report/references.bib`, `report/neurips_2026.sty`, `report/tables/refresh_*.tex` and `report/figures/ssc_two_graph_pipeline.pdf` exist. The current PDF still matches the preliminary QA hash `5db5133444002788e070d136de20391b660783d3bb3f5298dac522f29f28c685`: four main pages and thirteen total pages were checked. That validation does not certify a later regenerated report.

## Additional subset and evidence block

| Required block | Existing paths / pending output |
|---|---|
| Frozen source/catalogue/protocol | Present: `results/subset_search/source_inventory.csv`, `candidate_catalogue.json`, `sample_manifests/*.json`; `configs/subset_search/protocol.yaml`, `compatibility.yaml`, `candidate_catalogue.json`, `executable_cohort.json`. Catalogue 4736 entries / 4630 unique inputs; initial executable cohort 1202 canonical inputs. |
| Exact sample replay | 4736 sample manifests exist; preserve their hashes, selected/excluded indices, quotas, order and aliases. Do not regenerate membership to improve scores. |
| Execution matrix and trials | Pending: `results/subset_search/execution_coverage.csv`, `trials.csv.gz`. Gzip is the documented transport equivalent of required `trials.csv`; keep compressed and decompressed hashes. |
| Analysis1 sensitivity | Pending: `fixed_protocol_summary.csv`, `fixed_protocol_distribution.csv`, `fixed_protocol_family_distributions.csv`; strict Y0/E8/gamma 1/random, separated benchmark/pool/family and alias weighting. |
| Analysis2 and endpoints | Pending: `joint_search_summary.csv`, `native_best_summary.csv`, `closest_matches.csv`, `top_matches.csv`, `reference_contrasts.csv`. Both metrics/SD must share a complete 50-seed configuration; single native endpoints have n=1 and no SD. |
| Matched SC | Pending: `matched_sc_summary.csv`, `matched_sc_contrasts.csv`; verify exact saved F/sample fingerprints, same initialization and complete 50 seeds. |
| Locked confirmation | Pending: `winner_lock.json`, `confirmation_seed_namespace.json`, `rounding_confirmation.csv`. First unused aligned block>=1000000 is audited against historical recorded seeds and persisted; no reselection. |
| Recoverable artifacts/cost | Durable external store exists. Pending final `results/subset_search/artifact_manifest.json`, final `resource_usage.json`, verified archive export and recovery evidence. A hash alone does not establish recovery. |
| Per-benchmark Markdown | Pending new `results/subset_search/{AR,JAFFE,ORL,UMIST,BinAlpha,MSRA50,YaleB,USPS}.md`; historical tables remain under `results/v3_reproduction/per_benchmark/`. |
| Current no-data releases | Code exists. Pending `configs/subset_search/release_manifest.json`, `results/subset_search/configuration_inventory.csv`, `source_records.json.gz`; and `configs/submission_refresh/evidence_manifest.json` plus its committed baseline/graph scalar records. |
| Campaign instructions | Present: `docs/subset_search/README.md` and `docs/submission_refresh/execution_status.md`; update final actual coverage, resume commands and skipped phases. |

## Remaining content checks beyond file existence

- **Headline design:** `experiments/submission_refresh/reporting.py` now reads new complete mean winners for all eight benchmark rows, prefers the specification-compatible pool, marks adaptations with a dagger, and places retrospective-selection and solver qualifications beside the headline. It prints unavailable values rather than substituting paper values. The appendix carries both pools/endpoints, candidate IDs, counts, settings and signed ACC/NMI differences. Verify those actual generated rows after aggregation; the current preliminary PDF still predates this final eight-row result table. The four-page main-text limit and every-page visual check must be repeated.
- **Benchmark Markdown detail:** aggregation and scalar rebuilding now share `experiments/subset_search/markdown.py`. It generates both eligibility pools and both endpoints, paper/our SD where defined, signed ACC/NMI and SD differences, counts/source/settings/deviations, solver and identity fields, with unavailable slots explicit. An exact-byte aggregation/rebuild parity assertion is prepared. These new metadata changes still need the next validation slot and actual final table generation; a correct detailed appendix does not replace these benchmark tables.
- **Existing repeatability:** `results/final/generated/batch_repeatability.csv` preserves per-batch ACC/NMI means, SD, native-selected pairs and seeds. Current joint metadata also carries historical ACC repeatability fields, but the report input manifest does not yet list a dedicated repeatability view. Link/report existing multi-batch results separately for both metrics; do not attach mean-endpoint SD to one best assignment or invent new nested batches.
- **Source inventory corrections:** the frozen initial `results/subset_search/source_inventory.csv` retains its original “not audited” entries and blank resolution fields. The committed `results/submission_refresh/source_audit/source_version_audit.json` and `source_duplicate_maps/*.json` audit all 16 parents, including BinAlpha cross-class duplicate conflicts. The versioned inventory helper derives corrected metadata from those records, preserving unverified geometry explicitly, native versus processed resolution, and MSRA50 paper-benchmark versus MSRA25_EBSA_16x16 source identity. It does not alter frozen catalogue membership or deduplicate official input rows. Its output and corruption-before-write regression checks remain to be run in final aggregation/validation.
- **Validation state:** focused v2 passed **138 tests with one expected no-data integration skip**; a separate real-data candidate replay passed **6 tests**. Both records report zero source/configuration changes during the checks: external `validation/validation-focused-tests-v2.json`/`.log` and `validation/validation-real-candidate-replay-v1.json`/`.log`. The original focused v1 record (118 passes, 1 skip, 3 failures and 5 fixture errors) remains preserved. Its fixture schema, small-support EnSC growth and scalar-evidence fixes were verified by v2. Historical rebuild, synthetic CLI, source audit and corrected historical-graph validation also have completed external records. Newly added Markdown/inventory checks await a later slot. Passing the EnSC backend implementation checks does not promote G4/G5: only an actually passed fixed G3 gate plus the verified backend permits those benchmark runs.
- **Independent scalar rebuilding:** require fresh-checkout historical, joint historical, current subset and current baseline/graph no-data rebuilds. Verify empty/missing/duplicate/hash failures before output replacement and ensure no external arrays, publisher PDF or old Git objects are read by the no-data paths.

## Final English, link and publication checks

The existing language inventory covers 13,159 text files, two decompressed historical scalar records and text extraction from 41 committed PDFs; its last reviewed snapshot had no CJK/Japanese/Korean prose flags. Repeat it after final generated tables, figures and PDF, manually reviewing flagged context, natural English, legal notices and author identities. A Unicode count alone does not certify English. Minor joined words/numbers in campaign prose also need the final editorial pass.

The link snapshot at 07:05:23 UTC listed nine unique missing current targets; `research_findings.md` now exists, so that dated list is stale. Remaining listed gaps are final_handover, baseline diagnostics/coverage/extension/gate, subset closest/coverage/confirmation. Re-run local target checks after all I-items are generated and committed, then live main checks after rename. Keep immutable commit citations and genuine module-version names unchanged.

A read-only remote check during this audit found sole head `v3` at `5a02a702e6a0764299829885e8a3850e6483aaab`, default `v3`, administrator/push access available and repository description null. Publication/rename/default verification and an English description remain pending; this is not a permissions blocker. Re-fetch again immediately before the normal fast-forward push, then use the branch-rename API without force-overwriting divergent work.

**Fresh-environment dependency:** `environment/requirements.lock.txt` now pins `certifi==2026.2.25`, the installed version inspected on 2026-11-10, for the verified-HTTPS link auditor. `environment/README.md` documents that dependency. The final isolated installation/import and published-link checks remain pending; TLS verification stays enabled. pdflatex, BibTeX and Poppler are available on the present host; fresh-host prerequisites must remain documented.

## Isolated acceptance commands to run later

Run after committing the concrete release inputs, through the shared finalization allowance, without adding a third worker. These commands are a checklist and were not executed by this audit. Before rename, use an isolated checkout of the exact committed candidate; after rename, repeat against the actual shallow remote main checkout:

```bash
COMP3314_VERIFY_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/COMP3314 acceptance.XXXXXX")"
git clone --single-branch --depth 1 --branch main https://github.com/SelinaMai-SYM/COMP-3314-G23.git "$COMP3314_VERIFY_ROOT/fresh main checkout"
cd "$COMP3314_VERIFY_ROOT/fresh main checkout"
python3 -m venv "$COMP3314_VERIFY_ROOT/fresh environment"
source "$COMP3314_VERIFY_ROOT/fresh environment/bin/activate"
unset PYTHONPATH COMP3314_DATA_ROOT
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
python -m pip install -r environment/requirements.lock.txt
python -m pip install --no-deps -e .
python -m pip freeze > "$COMP3314_VERIFY_ROOT/tested-environment.txt"
python -m experiments.v3_reproduction smoke --dataset synthetic
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output "$COMP3314_VERIFY_ROOT/historical rebuild"
python -m experiments.submission_refresh rebuild --config configs/submission_refresh/campaign.yaml --output "$COMP3314_VERIFY_ROOT/joint historical rebuild"
python -m experiments.submission_refresh.current_release rebuild --release-manifest configs/subset_search/release_manifest.json --output "$COMP3314_VERIFY_ROOT/subset rebuild"
python -m experiments.submission_refresh rebuild-evidence --config configs/submission_refresh/campaign.yaml --release-manifest configs/submission_refresh/evidence_manifest.json --output "$COMP3314_VERIFY_ROOT/baseline graph rebuild"
python -m experiments.v3_reproduction run-experiments --config configs/submission_refresh/reproduction_adapter.yaml --data-root DATA_ROOT --datasets ORL_att92 JAFFE MSRA25_EBSA_16x16 --smoke --output "$COMP3314_VERIFY_ROOT/real smoke"
make -C report all PYTHON="$(command -v python)" REPORT_DATE=2026-11-10
pdftoppm -r 110 -png report/Group_23.pdf "$COMP3314_VERIFY_ROOT/report page"
python scripts/submission_refresh/link_audit.py --published --external-limit 12 --project-limit 80
```

Use an authorized independent DATA_ROOT, with the checksum-verified native MSRA file; no old worktree or cache pointer may supply it implicitly. If the host requires a CA bundle, configure a valid PIP_CERT/SSL_CERT_FILE rather than disabling TLS. Confirm the fresh checkout has no tracked/local data pointer, run the required regression suite through its reserved validation job, inspect every rendered final report page and PDF text, and compare rebuilt tables/report inputs against authoritative committed records.

Record the exact candidate and published commits actually tested, dependency freeze, command exits/log hashes, report hash/main-page count, sole remote head/default branch and live README/report links. Any later documentation-only audit commit must be identified separately and its diff checked. Update this checklist and the final handover from those outcomes; do not mark pending acceptance steps complete from these prepared commands.
