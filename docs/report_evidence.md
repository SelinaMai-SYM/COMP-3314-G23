# Experimental evidence

Presentation slides 4.1–4.4, 5.1–5.4 and 6.1–6.3 define the displayed comparisons.
Table values below are traced to retained measurements; paper values are
quotations of reported results. Paths are relative to the repository root.

## Core SSC and reconstruction

| Display | Retained source | Filter, configuration and endpoint | Generator / entry point | Identity and qualification |
|---|---|---|---|---|
| Paper columns; slide 5.1 | `configs/v3/paper_reference.yaml`; `results/submission_refresh/paper_reference_verification.json` | Paper Tables 1–2, all nine methods and eight benchmarks; compare mean SSC−SC and SSC−SPLS | `experiments.v3_reproduction.compare_paper`; paper inventory in `experiments.submission_refresh.reporting` | Reported means/SD, not project measurements; no paired significance inference |
| Two-graph method | `SSC_method/graph_construction.py`, `spectral_embedding.py`, `objective.py`, `optimizer.py`, `ssc.py` | X→A→F→fixed W→IRLS G→rounding; E8 factor 2 vs E13 factor 1 | `examples/ssc_blobs.py`; `experiments.v3_reproduction` | F/W identity and coefficient convention are part of a fit; matched SC rounds F |
| Slide 4.1: membership | `results/subset_search/reference_contrasts.csv`; `candidate_catalogue.json`; `sample_manifests/` | `reference_candidate_reference_settings` vs `best_candidate_reference_settings`, within declared pools: AR mask0024, UMIST Wayback seed057, BinAlpha seed088 | `experiments.subset_search.aggregate`; `experiments.submission_refresh.current_release rebuild` | Retrospective alternatives; UMIST changes both source and membership; exact indices and aliases retained |
| Slide 4.1: source/pixels | Same reference contrasts; `results/submission_refresh/source_audit/`; `dataset_inventory.csv` | Cropped2414 vs DengCai32 at Y0; MSRA native16 remains separate | Same scalar rebuild; source-specific loaders in `benchmarks/` | Source, resolution and historical identity are separate; MSRA is an adapted proxy |
| Slide 4.1: graph/normalization | `reference_contrasts.csv`; `all_configurations.csv` in historical and subset results | Yale cropped Y0/Y1/Y2/Y3; union k5, median bandwidth | Same scalar rebuild; `SSC_method.graph_construction` | Y1 normalizes X; Y2 F; Y3 both; memberships fixed |
| Slide 4.1: numerical convention | `results/v3_reproduction/all_configurations.csv`; `solver_audit.csv` | ORL Y0 E8/E13 nominal gamma1, RANDOM | `experiments.v3_reproduction rebuild-results` | Finite historical IRLS, not gap certified; E13 gamma maps to E8 gamma/2 |
| Slide 4.1: rounding/reporting | Same historical configurations and `all_trials.csv.gz` | ORL E8 gamma1 RANDOM/vanilla++/greedy++; JAFFE mean vs batch0 minimum-SSE partition | `scripts.result_tables --historical-output`; historical rebuild | Original coordinates; a native-selected partition has no across-start SD |
| Slide 4.1: tuning/baselines | Same historical records; `configs/final/report_selection.yaml` | ORL E8 gamma1/1000 vanilla++; PCA d40; SPLS d50 alpha0.5; recorded LDA alternatives | Historical rebuild; `experiments.submission_refresh.reporting` | Configuration comparison, not a new parameter-selection rule; LDA adaptation separately named |
| Slides 4.2–4.3 fixed SC/SSC | `results/v3_reproduction/all_configurations.csv` | `prep=Y0`, `initialization=RANDOM`; SC `k5_median_delta2`; SSC `variant=E8`, `config_name=E8\|gamma=1e+00`; fields `batch0_selected_acc/nmi` | `scripts.result_tables.fixed_table`; historical rebuild | Minimum-SSE of 50 in batch0, one partition, no SD; fractions converted to percentages |
| Slide 4.3 baseline comparisons | Same historical records; `results/submission_refresh/expanded_baseline_selection.csv`; `baseline_diagnostics.csv`; adapted source records in `baseline_records.public.v2.jsonl.gz` | K-means raw; PCA d40; LLC ridge1/mult1, minimum Procrustes; SPLS d50/alpha0.5; LDA-Kmeans full-refit means; ridge LDA→SC matched-source means | Historical rebuild; `experiments.submission_refresh rebuild-evidence` | LDA means differ from native selection; incomparable cross-subspace inertia unavailable as a primary best-of-50 endpoint; failed updates retained |
| Slide 4.4; reconstruction table | `results/subset_search/closest_matches.csv`; `matched_sc_contrasts.csv`; `configs/subset_search/release_manifest.json` | `endpoint=mean_sample_sd_50`; `pool=specification_compatible`, except MSRA `pool=adapted` | `experiments.submission_refresh.current_release rebuild`; `scripts.result_tables.historical_markdown` | Joint D_max/D_mean retrospective selection; preserve candidate/source, init, gamma, SD and cap status; no historical fit certified |
| Search coverage | `results/subset_search/coverage_summary.json`; configuration inventory; `trials.csv.gz` | 2,482 inputs / 74,436 completed pairs; 2,480 full 30-setting grids | Same current-release rebuild | Two partial grids; input/configuration pairs are not necessarily separate fits |
| Slide 5.2 numerical check | `tests/test_repair_round1_math.py`; `tests/test_ssc.py`; `tests/v3/test_ssc_solver.py` | Small fixed convex references, E8 and E13 coefficient mapping | `python -m pytest` on these files | Six-point coordinate agreement is an instance check, not a benchmark certificate |
| Slide 5.3 initialization | `results/v3_reproduction/all_configurations.csv` | ORL/JAFFE Y0 SC and E8 gamma1 SSC; `per_run_acc_mean`, RANDOM vs greedy++ | `scripts.result_tables.historical_markdown` | ORL SSC **57.135→78.335**, not the later subset-search 57.265→78.390 |
| Slide 5.4 W quality | `results/submission_refresh/graph_correction/graph_diagnostics_schema2.csv` | `graph_role=W`, `prep=Y0`, `kind=original`; ORL/YaleB `cross_class_mass_fraction` | `experiments.submission_refresh rebuild-evidence` | 4.6%/70.2% are edge-weight mass, not counts; A audited separately; post-fit label diagnostic |

The presentation rounds baseline values to one decimal; the generated baseline
diagnostic retains two (for example, ORL K-means and PCA→SC are 64.25%).
This is a display-precision difference, with the underlying configuration fixed.

The six-point coordinate error quoted in slide 5.2 is a historical instance
statistic. The maintained chain/block reference tests specify their own solver
tolerances; current reference agreement does not transfer a certificate to the
historical benchmark fits.

The historical ACC-only closest display and fixed-reference 72-cell tables
remain governed by `configs/final/report_selection.yaml`. PCA/SPLS without a
unique fixed reference remain `GRID_NOT_COLLAPSED`. They are separate from the
joint subset matches. The [generated reconstruction tables](reconstruction_tables.md)
show the displayed fixed, closest and initialization endpoints.

## Selected refinements and controls

| Display | Retained source | Filter / endpoint | Generator | Required interpretation |
|---|---|---|---|---|
| Slide 6.1 development | `results/extension_verification/macro_summary.csv`, `diagnostics/gates.json`; `results/extension_round2/macro_summary.csv` | E1 angular vs matched SSC; E2 radial-neutralization gate; E3 semantic gate; E4/E5/E6 vs fresh QSSC | `scripts.result_tables --development-output` and the corresponding scalar releases | Distinct cohorts and controls; failed gates do not represent completed formal E2/E3 campaigns |
| Slide 6.2 | `docs/figures/extension_pipeline_ppt_6_2.png` | Exact 2655×750 embedded image from PDF page35 / slide6.2 | Lossless image extraction from the supplied presentation | Three independent quadratic refinements, not a sequence; rank mass w for E7/E5 and wd for E1 |
| Slide 6.3 eight-cohort table | `results/extension_round3/primary_metrics.csv`; `configs/extension_round3/cohort_lock.json` | `rho=0.10`, `tau_multiplier=1`, `panel=native`; SC, SSC_REFERENCE, QSSC and three CAVITY methods | `experiments.extension_round3 rebuild` | Retrospectively selected cohort inputs; MSRA native16 adaptation; both metrics use the same 50 seeds |
| README primary differences | `macro_differences.csv`; `paired_differences.csv` in the same directory | Same primary point; candidate vs QSSC and corresponding `_PILOT`; explicit `cohort_mask` | `scripts.result_tables`; round3 rebuild | E7 8/8; E1_v3 6/8; E5_v2 7/8; different masks do not rank methods |
| Common-index controls | Same macro and paired records | `panel=anchor_generated`, same rho/tau, same-method plain pilot | Round3 rebuild | Centers use indices generated on the anchor; this panel differs from native |
| Qualification exclusions | `primary_metrics.csv`; `coverage.csv`; scalar packet pinned in `release_manifest.json` | Certificate and movement fields, including finite outputs outside matching tolerance | Round3 rebuild | E1 MSRA/Yale and E5 MSRA certified but movement-unmatched; MSRA SSC reference finite but uncertified; neither is “unrun” |
| Mechanism claims | `mechanism_diagnostics.csv`; `summary.md` | Primary cavity vs plain-pilot AUROC; qualified E5 guard vs QSSC slack and class scatter | Round3 rebuild with `--figures` | AUROC improves only on ORL/USPS; geometry changes do not imply recovered labels |
| UMIST control contrasts | `paired_differences.csv` | Native E5_v2 at rho.10/tau1 vs QSSC and SSC_REFERENCE | Round3 rebuild | +1.287/+1.432 pp vs QSSC, −4.475/−2.729 pp vs separately fitted SSC reference |

Fitting identities include numerical source hashes, protocol/cohort hashes,
configuration IDs, exact arrays, saved primal/dual bounds and both rounding
panels. Scalar rebuilding validates compressed/decompressed hashes and complete
seed sets. The public scalar packet is sufficient to regenerate reported tables;
provider-derived arrays are separately held, as described in
[reproducibility](reproducibility.md#numerical-artifacts).
