# G1 casebook findings: ORL and YaleB

Actual evidence snapshot: **10 November 2026, 11:10 UTC**. Both stored G1 jobs
and their casebooks report `COMPLETED`. This note reads only their saved
`status.json`, `casebook.json` and sample-level `error_cases.csv`; no matrices,
content-addressed objects, fitting or evaluators were opened or run. Arithmetic
means/differences of stored scalars are descriptive; no bootstrap or new
uncertainty interval was computed. The formal 362-task graph scope was already
frozen, independently of these results.

The evidence paths below are relative to the durable `ARTIFACT_ROOT` documented
in [preflight](preflight.md):

| Source | Job | Input/version directory |
|---|---|---|
| ORL att92, 400 samples / 40 classes | `graph_jobs/graph-31a61f36bb3d57b27553` | `26061d5eb6020b5a8aee794bf39b8647bf536b620a7d1682d4da7ada6eb522e7` |
| YaleB cropped2414, 2,414 samples / 38 classes | `graph_jobs/graph-7ebfc833a5648c01264d` | `5d150a617d9e9b424666eb43aa9700d0c6caba7da08079a0136cc0890bfd5e4e` |

Each job/version directory contains all three files. The sample CSVs have 400
and 2,414 rows; casebooks retain all 50 seeds and 2,000/1,900 per-class records.
The repository-level `results/submission_refresh/error_cases.csv` was still an
interim `NOT_RUN` row at this snapshot and needs regeneration from these actual
records. That stale export is not evidence that the two casebooks did not run.

## Same-F performance and numerical status

SC clusters the fixed F0 directly; SSC clusters the saved E8 gamma 1 output on
the same F0/W0. Both use the same 50 greedy K-means++/Lloyd one-start seeds 0–49.
Values are percent mean plus sample SD, from the stored summaries; deltas are
SSC minus SC in percentage points. They are conditional rounding variability,
not 50 independent datasets. Native-best assignments are separate endpoints and
are not substituted into this table.

| Source | SC ACC | SSC ACC | Delta ACC (pp) | SC NMI | SSC NMI | Delta NMI (pp) |
|---|---:|---:|---:|---:|---:|---:|
| ORL | 78.325 +/- 1.310 | 78.480 +/- 1.408 | +0.155 | 89.874 +/- 0.675 | 89.888 +/- 0.805 | +0.014 |
| YaleB cropped | 21.781 +/- 0.454 | 21.511 +/- 0.484 | -0.270 | 27.731 +/- 0.585 | 27.455 +/- 0.576 | -0.276 |

Both SSC solves are `PRIMAL_DUAL_GAP_CERTIFIED`, with recorded edge and node
capacity violations zero. ORL uses 1,450 PDHG updates, primal 14.582842829,
feasible dual 14.582698664 and relative gap 0.000009885927. YaleB uses 19,800
updates, primal 50.677253210, dual 50.676747546 and gap 0.000009978127. Normalized
L21 movement, `sum_i ||g_i-f_i|| / sum_i ||f_i||`, is 0.0895923 and 0.0975641
respectively. These are active, certified shrinkage points, not G=F cases.

Thus accurate optimization at this particular gamma does not produce a large
net gain: ORL has a small positive mean change; YaleB loses both means. No new
paired interval is supplied here, so a small positive mean is not declared
statistically established. These current solves neither replace historical
finite-iteration winners nor characterize SSC's entire parameter path.

## A and W diagnose different relations

A is the upstream input graph, with distances measured on the input vectors.
W0 is rebuilt in spectral F0 and controls shrinkage. Both tables count each
undirected edge once. Cross-class edge fraction and cross-class weight fraction
are different quantities; neither graph's value is substituted for the other.

| Source / graph | Edges | Whole-graph components | Cross-class edges (%) | Cross-class mass (%) | Edge-length AUROC for cross-class label |
|---|---:|---:|---:|---:|---:|
| ORL A | 1,273 | 3 | 22.310 | 11.990 | 0.866 |
| ORL W0 | 1,217 | 16 | 17.009 | 4.646 | 0.830 |
| YaleB A | 8,510 | 1 | 58.884 | 53.601 | 0.630 |
| YaleB W0 | 7,957 | 13 | 63.240 | 70.227 | 0.380 |

ORL's wrong W0 edges are a larger fraction of edge count than weight. YaleB's
wrong W0 edges instead carry a larger fraction of mass than count. On ORL,
larger W0 edge lengths rank cross-class edges reasonably well in this labelled
diagnostic. On YaleB, the corresponding AUROC is below 0.5: the simple premise
that wrong spectral neighbors are the longer edges is not supported. This is
not a learned deletion threshold or evidence that static filtering improves
clustering. A and W0 use different spaces and weights, so their raw length or
mass scales are not compared as equivalent units.

| Source / graph | Mean class-induced components | Excess fragments | Class-induced isolates | Mean largest class-component fraction (%) |
|---|---:|---:|---:|---:|
| ORL A | 1.200 | 8 | 4 | 94.500 |
| ORL W0 | 1.400 | 16 | 4 | 87.750 |
| YaleB A | 12.526 | 438 | 301 | 69.129 |
| YaleB W0 | 30.184 | 1,109 | 850 | 32.548 |

These are connected components of each true class's induced subgraph, including
isolates. YaleB A has one whole-graph component while its classes average 12.526
induced components; whole-graph connectivity plainly does not establish intact
within-class connectivity. YaleB W0 combines substantial class fragmentation
with high cross-class weight. This motivates separate upstream and fusion-graph
controls, but does not identify which is causally responsible for the final
error without an intervention.

## Paired errors and cancellation of gains and losses

False merge divides cross-class pairs assigned to the same cluster by all
cross-class pairs. False split divides same-class pairs assigned to different
clusters by all same-class pairs. Their denominators differ, so their raw rates
are not interchangeable measures of error severity. The following are arithmetic
means over the 50 stored paired seeds, shown in percent.

| Source / rate | SC (%) | SSC (%) | Change (pp) |
|---|---:|---:|---:|
| ORL false merge | 0.911 | 0.923 | +0.012 |
| ORL false split | 24.366 | 24.209 | -0.157 |
| YaleB false merge | 7.775 | 7.947 | +0.171 |
| YaleB false split | 84.314 | 84.336 | +0.022 |

ORL reduces splitting slightly while increasing merging slightly. YaleB worsens
both rates at this point. Sample-level correctness transitions show why the net
ACC differences are much smaller than the total changes: ORL has 1,264
SC-correct/SSC-wrong and 1,295 SC-wrong/SSC-correct sample-seed events out of
20,000; YaleB has 4,804 losses and 4,478 gains out of 120,700. Their net
differences reproduce +0.155 and -0.270 pp. These pooled events are dependent
across samples and seeds; they are not independent observations for a new test.
Correctness is defined after each partition's optimal class matching, so a
category change is not a direct observation of one particular edge causing a
sample to move across a class boundary.

## Quintiles and fixed illustrations

Quintiles are fixed from initial F0 row norms or W0 weighted degree, with tied
cut values assigned to the higher bin. ORL has 80 samples per bin; YaleB has
483, 483, 482, 483 and 483. The stored cut values are:

| Source / variable | 20%, 40%, 60%, 80% cuts |
|---|---|
| ORL F0 row norm | 0.233785, 0.290198, 0.331550, 0.372617 |
| ORL W0 degree | 0.964800, 1.737086, 2.606045, 3.368766 |
| YaleB F0 row norm | 0.056559, 0.075746, 0.100792, 0.153002 |
| YaleB W0 degree | 0.782164, 1.589427, 2.492739, 3.695669 |

ORL's lowest-norm bin has 2.600 wrong incident edges per sample but only 0.0733
wrong incident mass, and gains exceed losses by 1.825 pp within that bin. Its
highest-norm bin instead has a -0.650 pp net change. Wrong edge count alone is
therefore not an adequate proxy for attraction or for harm. For YaleB, the
lowest-norm bin has more wrong edges/mass than the highest (5.484/2.305 versus
1.427/0.363), yet its net correctness change is positive (+0.282 pp), while the
fourth norm bin has the largest negative change (-1.735 pp). Weighted-degree
strata also have mixed net changes rather than a monotone harm pattern. These
label-assisted associations do not establish a label-free norm/degree repair.

Illustration IDs are zero-based original rows, selected by the frozen rule
“first row in each seed-0 correctness category.” No images were inspected for
this note. Counts below describe all 50 seeds, not the seed-0 selection alone.

| Source | Seed-0 category | Sample ID | True class | SC-correct / SSC-correct rounds |
|---|---|---:|---:|---:|
| ORL | Both correct | 10 | 1 | 50 / 50 |
| ORL | Both wrong | 0 | 0 | 4 / 5 |
| ORL | SC correct, SSC wrong | 1 | 0 | 10 / 18 |
| ORL | SC wrong, SSC correct | 271 | 27 | 26 / 23 |
| YaleB | Both correct | 0 | 0 | 38 / 31 |
| YaleB | Both wrong | 2 | 0 | 0 / 0 |
| YaleB | SC correct, SSC wrong | 145 | 2 | 3 / 2 |
| YaleB | SC wrong, SSC correct | 174 | 2 | 1 / 2 |

ORL row 1 illustrates a seed-0 loss but improves in aggregate; row 271 illustrates
a seed-0 gain but loses in aggregate. These fixed examples are inspectable cases,
not representative effect estimates or proof of lighting/pose mechanisms.

For the main report, the supported conclusion is that **certified active
gamma-1 shrinkage has small, mixed net clustering effects, while the two graphs
show distinct contamination and class-connectivity limitations**. G1 does not
itself show that erroneous fusion edges cause the loss, satisfy the G3 gate,
validate angular completion, or establish a four-benchmark extension gain. Those
claims require their separately frozen controls and qualified results.
