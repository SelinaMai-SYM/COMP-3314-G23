# SSC refinement under controlled movement

This study evaluates four refinement candidates for **Spectral Shrunk Clustering** (SSC). It asks whether a specified geometric intervention improves ACC and NMI beyond ordinary quadratic graph fusion at the same embedding movement. Quadratic fusion itself is established convex clustering and is a mandatory control, called QSSC here.

The eight cohorts are fixed to the mean-endpoint configurations of the existing report. Their earlier selection was retrospective against published targets. Consequently, these experiments describe conditional behavior on those cohorts; they are not an unbiased test or evidence of unseen-data generalization.

- [Results and interpretation](../../results/extension_round2/summary.md)
- [Primary results, including sample SDs](../../results/extension_round2/primary_metrics.csv)
- [Every declared endpoint and its qualification](../../results/extension_round2/coverage.csv)
- [Paired differences and intervals](../../results/extension_round2/paired_differences.csv)
- [Fixed secondary path](../../results/extension_round2/secondary_metrics.csv) and [controls](../../results/extension_round2/control_metrics.csv)
- [Observed mechanisms and attribution](../../results/extension_round2/mechanism_evidence.md)
- [Method definitions and prior art](methods.md)
- [Report and presentation integration](../../results/extension_round2/integration_note.md)

## Common inputs and evaluation

| Benchmark | Fixed candidate | Preparation | Rows × features | Classes | Initializer |
|---|---|---|---:|---:|---|
| AR | `AR_common_mask0092` | Y0 | 840 × 1024 | 120 | greedy k-means++ |
| JAFFE | `JAFFE` | Y0 | 213 × 676 | 10 | random |
| ORL | `ORL_att92` | Y0 | 400 × 1024 | 40 | vanilla k-means++ |
| UMIST | `UMIST_LZUFE574_stratified_seed079` | Y0 | 564 × 10304 | 20 | greedy k-means++ |
| BinAlpha | `BinAlpha_random_seed057` | Y0 | 780 × 320 | 26 | random |
| MSRA50 family | `MSRA25_EBSA_16x16` | Y0 | 1799 × 256 | 12 | vanilla k-means++ |
| YaleB | `YaleB_cropped2414_nearest_Y3` | Y3 | 2414 × 1024 | 38 | greedy k-means++ |
| USPS | `USPS` | Y0 | 9298 × 256 | 10 | greedy k-means++ |

Source/version and historical-identity qualifications remain in the [cohort lock](../../configs/extension_round2/cohort_lock.json). MSRA uses the native 16×16 EBSA source, which is an adapted member of the MSRA50 family; equivalence to the original paper's source is not established. Seven Y0 raw bases are verified historical objects. YaleB's raw basis was regenerated before its declared Y3 transformation. All eight final anchor-object identities match their report counterparts. Two [pre-evaluation amendments](../../configs/extension_round2/amendments/) document storage-layout corrections and preserve the initial registrations.

For each cohort, `A0 → U0 → H` and `H → W0` are frozen once. Every method receives the same H; E4 alone changes W through one frozen graph correction. Optimized G goes directly to k-means, with no additional row normalization or PCA. Each terminal output uses Lloyd, one start, and all seeds 0–49 with the cohort's locked initializer. ACC and NMI are means with sample SD (`ddof=1`) from the same configuration. The minimum-inertia assignment is diagnostic only.

The primary target is `||G−H||F / ||H−mean(H)||F = .05`. The separately reported fixed path is .02, .10 and .20. Lambda is selected without labels using feasible dual bounds, movement-uncertainty intervals and bounded searches. A point qualifies only when both relative gaps are at most `1e−6`, relative capacities are at most `1e−8`, movement uncertainty is at most `.02 rho`, and `|movement−rho| + uncertainty ≤ .05 rho`. E6 additionally requires its repaired, centered primal to pass the whitened LMI and conditioning checks. These are numerical certificates, not interval-arithmetic proofs.

Comparisons use 10,000 paired rounding-seed bootstrap draws with PCG64 seed 424242. These intervals describe conditional initialization variability on fixed data. An eight-cohort macro is reported only when all eight comparisons are qualified and movement-matched; otherwise the available-case denominator and missing cohorts are explicit.

## Reproduction

Use CPython 3.13.3 and the [pinned environment](../../configs/extension_round2/requirements.txt). The independent data root contains the registered source files; scientific arrays are stored outside Git in the project's content-addressed artifact store. Data-provider terms remain separate from the project's MIT license.

```bash
git clone --single-branch --branch extension_v2 https://github.com/SelinaMai-SYM/COMP-3314-G23.git
cd COMP-3314-G23
python3 -m venv .venv
.venv/bin/python -m pip install -r configs/extension_round2/requirements.txt
```

Set `DATA_ROOT` and `ARTIFACT_ROOT` to explicit directories. A recovered artifact store includes the original deadline and cumulative resource ledger; `--resume` does not allocate a new budget. To conduct a new independent study, create a new artifact root and record it separately from this release.

```bash
python -m experiments.extension_round2.run --phase freeze --config configs/extension_round2/protocol.yaml --data-root "$DATA_ROOT" --artifact-root "$ARTIFACT_ROOT" --resume
python -m experiments.extension_round2.run --phase verify --config configs/extension_round2/protocol.yaml --artifact-root "$ARTIFACT_ROOT"
python -m experiments.extension_round2.run --phase primary --all-benchmarks --resume --config configs/extension_round2/protocol.yaml --artifact-root "$ARTIFACT_ROOT"
python -m experiments.extension_round2.run --phase secondary --all-benchmarks --resume --config configs/extension_round2/protocol.yaml --artifact-root "$ARTIFACT_ROOT"
python -m experiments.extension_round2.run --phase controls --resume --config configs/extension_round2/protocol.yaml --artifact-root "$ARTIFACT_ROOT"
python -m experiments.extension_round2.report --config configs/extension_round2/protocol.yaml --artifact-root "$ARTIFACT_ROOT" --output results/extension_round2
```

The executable [protocol](../../configs/extension_round2/protocol.yaml) fixes two single-thread workers, a 24-hour wall deadline, 600 CPU seconds per fit/QP/auxiliary attempt, 1800 CPU seconds per complete main method/cohort path, and 600 CPU seconds per control target. All eight primary/reference attempts precede secondary paths and controls. Unmatched, inactive, uncertified, failed and unrun endpoints remain distinct. Resource and coverage tables report actual execution rather than equating a declared matrix with completed work.

Interrupted paths retain the latest recorded finite checkpoint as a diagnostic output, with independent certificate checks and no additional fitting iterations. The registered failure policy does not promote it to a completed matched target. A later target that was never reached remains unrun, with its last finite path reference stored separately. An interrupted attempt may retain only its checkpoint summary; completed attempts retain full recorded scalar histories.

The [artifact manifest](../../results/extension_round2/artifact_manifest.json) describes recoverable matrices, duals, continuation states, predictions, numerical histories and source snapshots. A verified archive is retained outside Git because source-derived arrays may be restricted. The existing export/recovery interface accepts only this study's manifest:

```bash
python -m experiments.submission_refresh.export_artifacts export --artifact-root "$ARTIFACT_ROOT" --manifest results/extension_round2/artifact_manifest.json --archive "$ARCHIVE"
python -m experiments.submission_refresh.export_artifacts recover --archive "$ARCHIVE" --output "$RECOVERED_ROOT"
```

Scalar tables and figures can also be checked and rebuilt without any dataset or numerical archive. This independently recomputes mean/sample SD and paired bootstrap contrasts, verifies compressed and decompressed trial hashes, and replaces the destination only after validation:

```bash
python -m experiments.extension_round2.release --release-manifest results/extension_round2/release_manifest.json --output /path/to/rebuilt-results
```

Rechecking primal/dual certificates additionally requires the saved numerical arrays and the `report` command. Scalar reconstruction alone does not certify optimization.

This branch adds an independent research namespace. The original report, presentation, historical measurements and existing rebuild interfaces are preserved.
