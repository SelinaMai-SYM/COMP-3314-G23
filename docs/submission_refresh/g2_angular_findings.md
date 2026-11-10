# G2 angular-anchor findings

Observed on **2026-11-10, 11:26–11:27 UTC** (19:26–19:27 Asia/Shanghai), after all 48 G2 point records were saved as `COMPLETED`. These records cover the two preregistered full development benchmarks, two anchors, two graphs and six fixed gammas. Every point has exactly the same 50 greedy K-means++/Lloyd seeds, 0–49, and `summary.n=50`. This is an interpretation of existing scalar records, not another experiment or a new selection rule.

**Anchor normalization explains substantially more of the observed improvement than the additional certified gamma-1 shrinkage.** Angular graph construction has different effects on the two datasets, and it does not reliably repair class fragmentation. Several large-gamma results remain numerically uncertified. These observations distinguish representation, graph and solver effects; they do not establish a four-benchmark extension benefit or replace the separate G3 promotion gate.

## Anchor-only comparison

F0 is the original saved spectral representation. U normalizes each nonzero F0 row to unit length; neither saved input contains zero rows. At gamma zero, the W0/Wa rows are declared aliases of the same anchor-only SC result, not independent scientific fits. ACC/NMI are percentages; every SD below is the sample SD of that same configuration's 50 rounds.

| Full benchmark | Anchor-only endpoint | ACC mean ± SD | NMI mean ± SD |
|---|---|---:|---:|
| ORL_att92 | F0-SC | 78.325 ± 1.310 | 89.874 ± 0.675 |
| ORL_att92 | U-SC | 80.175 ± 1.551 | 90.890 ± 0.641 |
| YaleB_cropped2414 | F0-SC | 21.781 ± 0.454 | 27.731 ± 0.585 |
| YaleB_cropped2414 | U-SC | 25.797 ± 0.709 | 32.595 ± 0.435 |

The U-minus-F0 differences are **+1.850 ACC / +1.016 NMI percentage points on ORL**, and **+4.016 / +4.864 on cropped YaleB**. These gains occur before shrinkage. They must not be credited to SSC or to replacing W0 with Wa. The two anchors also have different row scales: equal numeric gamma and equal graph mass do not imply equal relative regularization strength or equal node forces.

## Fixed gamma 1: incremental shrinkage at the same anchor

W0 is constructed in F0; Wa is constructed in U. Each is held fixed when the anchor changes, giving the intended factorial comparison. Wa is uniformly scaled to the undirected W0 mass. The following deltas subtract the SC result on the **same anchor**, not F0-SC for every row. No gamma is selected from its scores.

| Benchmark | Anchor / graph | ACC mean ± SD | NMI mean ± SD | ΔACC / ΔNMI vs same-anchor SC (pp) | Relative gap | Normalized L21 movement |
|---|---|---:|---:|---:|---:|---:|
| ORL | F0 / W0 | 78.480 ± 1.408 | 89.888 ± 0.805 | +0.155 / +0.014 | 9.886e-6 | 0.08959 |
| ORL | F0 / Wa | 77.825 ± 1.288 | 89.327 ± 0.692 | −0.500 / −0.547 | 9.763e-6 | 0.08192 |
| ORL | U / W0 | 80.005 ± 1.542 | 90.938 ± 0.577 | −0.170 / +0.048 | 9.957e-6 | 0.04521 |
| ORL | U / Wa | 80.345 ± 1.453 | 90.967 ± 0.530 | +0.170 / +0.077 | 9.927e-6 | 0.02128 |
| YaleB cropped | F0 / W0 | 21.511 ± 0.484 | 27.455 ± 0.576 | −0.270 / −0.276 | 9.978e-6 | 0.09756 |
| YaleB cropped | F0 / Wa | 22.531 ± 0.422 | 28.075 ± 0.530 | +0.750 / +0.344 | 9.997e-6 | 0.15960 |
| YaleB cropped | U / W0 | 25.169 ± 0.851 | 31.877 ± 0.464 | −0.628 / −0.718 | 9.754e-6 | 0.11705 |
| YaleB cropped | U / Wa | 26.111 ± 0.767 | 32.684 ± 0.533 | +0.314 / +0.089 | 9.963e-6 | 0.04937 |

All eight points above are `PRIMAL_DUAL_GAP_CERTIFIED`, with relative gap at most 1e-5 and recorded edge/node capacity violations zero. All are active under the preregistered normalized-L21 threshold of 1e-6. Movement is the sum of row-displacement norms divided by the sum of anchor-row norms, not Frobenius movement.

On ORL, replacing W0 with Wa at fixed F0 lowers both metrics; at fixed U it produces small positive increments over U-SC. On YaleB, W0 shrinkage lowers both metrics at either anchor, whereas Wa gives positive mean increments at either anchor. Thus neither “normalization helps” nor “angular edges help” is a sufficient explanation for every cell. In particular, the U/Wa totals exceed F0-SC by +2.020 ACC points on ORL and +4.330 on YaleB, but their **shrinkage-only** increments are just +0.170 and +0.314.

These are descriptive differences across the same saved rounding seeds. The individual configuration SDs are not SDs of the paired differences, confidence intervals, or independent-dataset uncertainty. No new bootstrap or significance claim was produced for this note.

## Fixed gamma 1000: preserve numerical qualifications

| Benchmark | Anchor / graph | ACC mean ± SD | NMI mean ± SD | Relative gap | Normalized L21 movement | Solver qualification |
|---|---|---:|---:|---:|---:|---|
| ORL | F0 / W0 | 74.520 ± 0.252 | 89.657 ± 0.184 | 1.140e-4 | 0.30246 | MAX_ITER_REACHED; uncertified |
| ORL | F0 / Wa | 78.070 ± 1.138 | 89.579 ± 0.596 | 9.775e-6 | 0.13248 | gap certified |
| ORL | U / W0 | 74.820 ± 0.237 | 89.852 ± 0.090 | 1.078e-4 | 0.25651 | MAX_ITER_REACHED; uncertified |
| ORL | U / Wa | 80.010 ± 1.509 | 90.894 ± 0.577 | 8.682e-6 | 0.05780 | gap certified |
| YaleB cropped | F0 / W0 | 16.876 ± 0.174 | 24.758 ± 0.607 | 5.168e-2 | 0.71447 | MAX_ITER_REACHED; uncertified |
| YaleB cropped | F0 / Wa | 3.397 ± 0.000 | 8.666 ± 0.000 | 4.349e-1 | 0.96354 | MAX_ITER_REACHED; uncertified |
| YaleB cropped | U / W0 | 15.079 ± 0.000 | 30.019 ± 0.000 | 6.187e-5 | 0.82012 | MAX_ITER_REACHED; uncertified |
| YaleB cropped | U / Wa | 28.296 ± 0.504 | 34.705 ± 0.321 | 5.688e-5 | 0.44748 | MAX_ITER_REACHED; uncertified |

The certified ORL Wa points still do not improve mean ACC over their own SC anchors at gamma 1000. YaleB U/Wa has descriptive increments of +2.499 ACC / +2.110 NMI points over U-SC, but its gap exceeds 1e-5. Its favorable scores do not certify an optimum; the poor F0/Wa result is likewise not evidence that the mathematical objective must destroy the class structure at its optimum. A zero SD only records identical metric values across these rounding seeds and does not repair solver uncertainty.

Across the full fixed path, **32 of 48 rows are certified**: ORL has 18 certified and 6 uncertified rows; YaleB has 14 and 10. Sixteen certified rows are analytic G=F endpoints, comprising eight gamma-zero graph-arm aliases and eight gamma-0.001 rows. The other sixteen certified rows are active PDHG results. All sixteen uncertified rows stop at `MAX_ITER_REACHED`; every recorded capacity violation is zero, but dual feasibility alone is insufficient without the required gap. Every gamma-1,000,000 point is uncertified. Completion of the 50 rounding trials and certification of the representation are separate facts.

## Distinct A, W0 and Wa graph evidence

A is the upstream graph in input-feature space X. It is not the SSC fusion graph. A diagnostics below come from the matched G1 task status using the **same saved input version and scientific source** as G2. W0/Wa diagnostics come from G2. Graph statistics do not depend on the shrinkage gamma. Cross-class fractions use true labels for evaluation only.

| Benchmark | Graph / native length space | Undirected edges | Cross-class edges (%) | Cross-class weight (%) | Class-induced excess fragments | Class-induced isolates | Mean largest class-component fraction |
|---|---|---:|---:|---:|---:|---:|---:|
| ORL | A / X | 1,273 | 22.310 | 11.990 | 8 | 4 | 0.9450 |
| ORL | W0 / F0 | 1,217 | 17.009 | 4.646 | 16 | 4 | 0.8775 |
| ORL | Wa / U | 1,291 | 17.661 | 6.518 | 16 | 4 | 0.8775 |
| YaleB cropped | A / X | 8,510 | 58.884 | 53.601 | 438 | 301 | 0.6913 |
| YaleB cropped | W0 / F0 | 7,957 | 63.240 | 70.227 | 1,109 | 850 | 0.3255 |
| YaleB cropped | Wa / U | 8,385 | 60.692 | 54.288 | 1,106 | 893 | 0.4065 |

Within-class fragmentation is computed on each class-induced graph, including isolated class members. It is distinct from whole-graph connectivity: the whole-graph component counts for A/W0/Wa are 3/16/26 on ORL and 1/13/2 on YaleB. YaleB Wa being nearly globally connected therefore does not mean that identities are internally connected. Conversely, its larger mean largest-component fraction coexists with more class-induced isolates than W0; one connectivity statistic cannot replace the others.

ORL Wa slightly worsens both cross-class contamination fractions without reducing the excess-fragment count. YaleB Wa lowers the cross-class weight fraction by 15.939 percentage points relative to W0, but still places 54.288% of weight across classes. Excess fragments fall by only three, while class-induced isolates rise by 43. This is evidence of a graph tradeoff, not a general graph-repair success or a causal demonstration that incorrect edges alone explain the clustering errors.

Mass matching applies to W0 and Wa, not to upstream A. Their common undirected masses are 444.432738 on ORL and 2,814.033957 on YaleB; the Wa scaling factors are 0.901997 and 0.925980. Their edge supports and local forces remain different after this scaling.

Edge-length discrimination also requires an explicit space. Native-space cross-edge length AUROC for A/X, W0/F0 and Wa/U is 0.8656/0.8303/0.7841 on ORL and 0.6300/0.3800/0.5641 on YaleB. On the **unchanged YaleB W0 edge support**, replacing F0 distances by U distances changes AUROC from 0.3800 to 0.6076. Raw spectral edge length therefore does not universally identify cross-class relations, and the angular improvement cannot be described as merely deleting the longest incorrect edges. These label-assisted diagnostics do not define a new unsupervised selection rule or authorize another penalty/grid experiment.

## Provenance and conclusion boundaries

The full 48-cell scalar view is generated into [extension_results.csv](../../results/submission_refresh/extension_results.csv), with [graph_diagnostics.csv](../../results/submission_refresh/graph_diagnostics.csv), [graph_execution_coverage.csv](../../results/submission_refresh/graph_execution_coverage.csv), and the report appendix. The completed external point records below are the source for this dated interpretation; final aggregation and report generation must carry all 48 cells and their qualifications. This note highlights fixed gamma 1 and 1000; it does not select a new winner or replace those authoritative views. G2 uses these external metadata locations relative to the durable artifact root:

| Benchmark | Input version | Representation JSON SHA-256 |
|---|---|---|
| ORL_att92 | `26061d5eb6020b5a8aee794bf39b8647bf536b620a7d1682d4da7ada6eb522e7` | `996bd0ed458e9b741406e933ec0cb21ecdadf50ab09165758f0cb8b5a69d23bb` |
| YaleB_cropped2414 | `5d150a617d9e9b424666eb43aa9700d0c6caba7da08079a0136cc0890bfd5e4e` | `83a2485e9097e4935631afd3341e1904915d73da21879c75f8bbe44d4ea6c6ab` |

The representation metadata paths are `graph_inputs/<dataset>/<input_version>/representation.json`; G2 records are `graph_records/<dataset>/<input_version>/G2__*.json`. Both inputs record scientific fingerprint `2ed5b6fb520753cd8a339744ed4c787b6efa630ec77d554f1637a5d110eaccbb`. Matched G1 A diagnostics are in `graph_jobs/graph-31a61f36bb3d57b27553/<ORL input version>/status.json` and `graph_jobs/graph-7ebfc833a5648c01264d/<YaleB input version>/status.json`.

Only saved JSON scalars and metadata were read for this interpretation. No CAS matrix, new fit, evaluator, bootstrap or performance-based scope change was used. The frozen 362-task design is unchanged. The two-dataset findings do not satisfy the four-benchmark, fairly searched SSC comparison; that formal macro remains unavailable from G2. G3 still uses its separately frozen 15%/gamma-1000 deletion/completion experiment, required certificates/activity, fragmentation change and paired intervals against deletion and fixed-Oracle-deletion plus blind additions. No favorable G2 anchor/graph/gamma can substitute for that gate.
