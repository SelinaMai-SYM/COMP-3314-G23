# COMP3314 Group 23: Spectral Shrunk Clustering - final v3

Study and critical analysis of Chang, Nie, Ma, Yang and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015, pp. 2532-2538, DOI [10.1609/aaai.v29i1.9606](https://doi.org/10.1609/aaai.v29i1.9606). SSC means Spectral Shrunk Clustering.

The repository separates paper reconstruction, controlled reproduction and retrospective numerical matching. An optimum for a convex representation objective does not guarantee optimal labels or improved ACC/NMI.

## Setup and three checks

Tested CPython 3.13.3. Package minimum is Python 3.10; other versions are not claimed bit-identical.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
python -m pip install -e .
python -m experiments.v3_reproduction smoke --dataset synthetic
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output results/rebuilt
python -m experiments.v3_reproduction run-experiments --config configs/v3/campaign.yaml --data-root /path/to/benchmarks --datasets ORL_att92 JAFFE --smoke --output runs/next_round/data_smoke
```

Synthetic smoke and results rebuild need no images, caches, Git history or old branches. Real-data smoke uses three seeds, not a full experiment. [Data preparation and restrictions](docs/final/data_setup.md). Root precedence: CLI > `COMP3314_DATA_ROOT` > `local/data_root.txt` > checkout `benchmarks`; it contains `orl/data`, `jaffe/data`, `yaleb/data`, `usps/data`. There is no old-worktree pointer.

Omit `--smoke` only to deliberately run the large baseline grid. New mechanism experiments are separate:

```bash
python -m experiments.next_round.campaign prepare --data-root /path/to/benchmarks
python -m experiments.next_round.campaign sc
python -m experiments.next_round.campaign run --phases A N0_selected B --workers 2 --budget-hours 36
python -m scripts.final.analyze_next_round
```

Phase C requires the documented evidence gate. [Protocol](configs/next_round/protocol.yaml), [job manifest](configs/next_round/job_manifest.json), [all results](results/next_round/all_results.md), [negative findings](results/next_round/negative_findings.md). Model and parameter functions do not accept labels; Oracle interventions and evaluation explicitly do.

## 9 methods x 8 benchmarks

**32 COMPLETED, 24 BLOCKED_DATA, 8 BLOCKED_METHOD, 8 SUBSET_UNVERIFIED.** SLPS (SPLS in the SSC table) has a one-shot implementation. LDA-SC is unresolved. AR, historical UMIST564 and MSRA50 remain blocked. Candidate BinAlpha and UMIST575 are supplementary. PCA/SLPS have measured grids without one unique locked reference.

- [Closest-to-paper display: all 72 cells](results/final/closest_to_paper.md): complete batch-0 configuration mean minimizing absolute unrounded ACC distance. This is label/paper-assisted post-hoc display selection.
- [Fixed controlled reference: all 72 cells](results/final/fixed_protocol_reference.md): existing Y0/E8/gamma=1/random; uncollapsed grids stay explicit.
- [Selection manifest](results/final/selection_manifest.csv), [complete configuration statistics](results/final/generated/configuration_table.csv), [batch repeatability](results/final/generated/batch_repeatability.csv), [supplemental versions](results/final/generated/supplemental.md), [per-benchmark tables](results/final/generated/per_benchmark).

This historical release reconstructs 378550 trials, 3059 jobs and 6563 configurations. Counts are package-specific. Scalar reproducibility is not full recovery of old F/W arrays. Compressed and decompressed hashes are distinct in the release manifest; new executions have separate run IDs and supersedes links.

| Benchmark | Method | Paper ACC (%) | Closest mean ± sample SD (%) | Setting and original solver |
|---|---|---:|---|---|
| JAFFE | SC | 76.1 | 68.526 ± 11.152 | JAFFE, Y0, SC, RANDOM; NOT_APPLICABLE |
| JAFFE | SSC | 81.2 | 74.751 ± 8.371 | JAFFE, Y0, E13, RANDOM, nominal gamma=1e+06; MAX_ITER_REACHED; 300-step returned iterate, optimum not certified |
| ORL | SC | 72.7 | 72.725 ± 3.149 | ORL_att92, Y0, SC, VANILLA_KMEANSPP; NOT_APPLICABLE |
| ORL | SSC | 76.0 | 75.965 ± 1.367 | ORL_att92, Y0, E13, VANILLA_KMEANSPP, nominal gamma=1000; MAX_ITER_REACHED; 300-step returned iterate, optimum not certified |
| YaleB | SC | 34.8 | 34.362 ± 0.957 | YaleB_cropped2414, Y3, SC, SKLEARN_GREEDY_KMEANSPP; NOT_APPLICABLE |
| YaleB | SSC | 49.8 | 43.583 ± 1.287 | YaleB_dengcai32, Y3, E8, SKLEARN_GREEDY_KMEANSPP, nominal gamma=0.001; CONVERGED_BY_ITERATE_CRITERION |
| USPS | SC | 64.3 | 65.597 ± 1.867 | USPS, Y0, SC, SKLEARN_GREEDY_KMEANSPP; NOT_APPLICABLE |
| USPS | SSC | 75.5 | 76.844 ± 5.117 | USPS, Y0, E8, VANILLA_KMEANSPP, nominal gamma=1000; CONVERGED_BY_ITERATE_CRITERION |

NMI/SD/n follow the same configuration and seeds. Min-inertia assignments are separate. Paper tuning, fixed control and closest display answer different questions. E13(gamma) maps to E8(gamma/2). Vanilla++ differs from sklearn greedy++.

## Performance-driven extensions

N0 provides feasible-dual certificates; A studies parameter curves; B diagnoses incorrect fusion with Oracle deletion and matched weakening controls. The practical target is >=2 points mean ACC gain across four benchmarks, nondecreasing NMI, and comparison with SC. A 15-configuration capability oracle is separate from the fixed no-label operating point. Capped fusion is an existing penalty adapted to SSC, with inner certificates only. Huber/heat remain evidence-dependent candidates.

The diagnostic gate currently supports **0/4** datasets (two required). Formal capped experiment triggered: **False**. This is not evidence that SSC fails universally; uncertified outcomes remain visible.

The old held-out robustness table is retained but invalid as full-SSC robustness evidence: shrinkage was not rerun and USPS was clipped incorrectly. [Correction](docs/next_round/robustness_audit.md).

## Deliverables and attribution

[Report PDF](report/Group_23.pdf) and [LaTeX](report/main.tex); [guideline checklist](docs/final/guideline_checklist.md); [9-minute outline](docs/final/presentation_outline.md); [Q&A](docs/final/qa_notes.md); [validation](docs/final/validation.md); [sources, ownership and licenses](docs/final/sources_and_licenses.md). [Scientific snapshots](archive/source) are provenance only, never current imports.

This is a course report, not a NeurIPS submission. Main text is <=4 pages, excluding references/appendix. Members: Han Jiale; Lu Sinan; Mahatharadol Vie; Mai Sheung Ying. Affiliation: The University of Hong Kong. Names were supplied explicitly by the user. Only the PDF is submitted to the course system by the group.

Slides: 2026-11-15 23:59; report: 2026-11-29 23:59, Hong Kong/Shanghai time. Rubric: understanding 40%, analysis/insight 30%, writing 10%, presentation/Q&A 20%; reproduction is optional, up to 10 bonus points.

## Measured final status

The main mechanism gate is **0/4**, so the formal real-data capped search is **NOT_RUN_MECHANISM_NOT_SUPPORTED**; the four-benchmark practical target is **not established (NA)**. Synthetic results show damage avoidance shared by simpler controls, not gain beyond SC. N1 has no demonstrated ACC/NMI gain; N2 primary ablations and corrected full-pipeline robustness are reported separately.

[Planned/executed coverage](results/next_round/planned_execution_coverage.csv), [heat ablations](results/next_round/heat_primary_summary.csv), [synthetic results](results/next_round/synthetic/summary.json), [corrected robustness](results/next_round/corrected_robustness_summary.csv), [resource ledger](results/next_round/resource_ledger.json), [execution decisions](docs/next_round/execution_decisions.md), [publication status](docs/final/publication_status.json).

Measured fit/audit CPU: 2.623 core-hours; conservative session envelope at completion: 3.82 core-hours, against the 36-hour cap. Maximum two single-thread experiment workers; per-fit RSS and enforcement limits are in the ledger. No task is described as budget-exhausted merely because it was not promoted.
