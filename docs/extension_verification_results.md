# Independent refinement results

The inputs, objectives and operating points are registered before new benchmark scoring. ORL and YaleB are previously studied development datasets. All other inputs confirm the locked specification; they are not claimed to be unseen data.

Current scientific status: **COMPLETED**. A failed gate is a mechanism decision, not an optimized benchmark result.

| Benchmark | E1 original / angular | E2 angular | E3 angular |
|---|---|---|---|
| AR | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| JAFFE | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| ORL | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| UMIST | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| BinAlpha | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| MSRA50 | COMPLETED_UNCERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| YaleB | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |
| USPS | COMPLETED_CERTIFIED / COMPLETED_CERTIFIED | GATE_FAILED | GATE_FAILED |

## Fixed primary paired effects

Each entry uses the same configuration and complete seeds 0–49 for ACC/NMI. Differences are percentage points relative to matched ordinary SSC. Intervals are conditional rounding-seed intervals, not new-dataset uncertainty. Uncertified rows are exploratory.

| Benchmark | Method / panel | ACC delta [95% interval] | NMI delta [95% interval] | Qualified |
|---|---|---:|---:|---|
| ORL | E1 / original | -0.180 [-0.660, 0.315] | 0.206 [-0.027, 0.448] | True |
| ORL | E1 / angular | 0.010 [-0.015, 0.045] | 0.008 [0.000, 0.021] | True |
| YaleB | E1 / original | 0.030 [-0.103, 0.169] | 0.002 [-0.239, 0.245] | True |
| YaleB | E1 / angular | -0.214 [-0.412, -0.034] | -0.108 [-0.199, -0.022] | True |
| AR | E1 / original | 0.045 [-0.233, 0.333] | 0.042 [-0.068, 0.152] | True |
| AR | E1 / angular | -0.052 [-0.331, 0.233] | -0.022 [-0.110, 0.065] | True |
| JAFFE | E1 / original | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | True |
| JAFFE | E1 / angular | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | True |
| UMIST | E1 / original | 0.638 [0.082, 1.245] | 0.113 [-0.126, 0.366] | True |
| UMIST | E1 / angular | 0.004 [-0.238, 0.241] | -0.003 [-0.082, 0.057] | True |
| BinAlpha | E1 / original | 0.415 [-0.049, 0.885] | 0.292 [0.048, 0.536] | True |
| BinAlpha | E1 / angular | 0.249 [-0.087, 0.572] | 0.101 [-0.025, 0.233] | True |
| MSRA50 | E1 / original | -0.010 [-0.030, 0.000] | 0.066 [-0.003, 0.199] | False |
| MSRA50 | E1 / angular | -0.071 [-0.213, 0.000] | -0.016 [-0.047, 0.000] | True |
| USPS | E1 / original | 0.053 [-0.003, 0.163] | 0.153 [-0.007, 0.463] | True |
| USPS | E1 / angular | 0.012 [-0.490, 0.526] | 0.108 [0.000, 0.309] | True |

## Mechanisms and attribution

E1 tests protection of global dispersion, separately from any gain beyond interpolation. E2 uses the two fixed radial-neutralization development contrasts and the declared isotropic control. E3 uses frozen comparison coverage/semantics, triplet-only correction and three matched random-force controls. The complete objective, certificate, movement, runtime, mean/SD, native and contrast rows are retained in the result files.

E1 original against matched SC: eight-benchmark macro unavailable (7/8 qualified); explicitly partial ACC +0.178 pp / NMI +0.020 pp.

E1 original against matched SSC: eight-benchmark macro unavailable (7/8 qualified); explicitly partial ACC +0.143 pp / NMI +0.115 pp.

E1 original against matched interpolation: eight-benchmark macro unavailable (7/8 qualified); explicitly partial ACC +0.131 pp / NMI +0.082 pp.

E1 angular against matched SC: ACC +0.020 pp, NMI +0.023 pp (8/8 qualified).

E1 angular against matched SSC: ACC -0.008 pp, NMI +0.008 pp (8/8 qualified).

E1 angular against matched interpolation: ACC -0.040 pp, NMI +0.013 pp (8/8 qualified).

The saved primary E1 outputs retain at least 99.667% of anchor dispersion under the median bounds, far above the 25% guaranteed floor. At most 5.259% of edges lie strictly inside the stopping tubes. These supplementary geometric diagnostics do not identify correct class relations or establish a clustering benefit.

All 16 uniform-origin-scaling checks preserve the SC partitions for all 50 seeds; this is a geometry check and supplies no additional method benefit.

E2 promotion: **NOT PROMOTED**.
- ORL: FAILED. Inward energy 0.0786%; RMS neutralization angle 0.000148 degrees; ACC change +0.000 pp (adjusted lower +0.000); NMI change +0.000 pp.
- YaleB: FAILED. Inward energy 5.4648%; RMS neutralization angle 0.017962 degrees; ACC change -0.053 pp (adjusted lower -0.183); NMI change -0.072 pp.

E3 promotion: **NOT PROMOTED**.
- ORL: FAILED. 49 comparisons (minimum 20); correct 22.45% and reversed 8.16%.
- YaleB: FAILED. 1751 comparisons (minimum 121); correct 44.83% and reversed 1.88%.

## Coverage and limitations

An eight-benchmark macro requires all eight qualified paired rows of that named panel. Partial summaries keep their denominator and do not substitute for a full macro. Inactive certified outputs have valid metrics. All inputs retain unverified historical identity; native-16 MSRA is an adapted proxy, AR is a source-order hypothesis and UMIST retains 10,304 features. Mathematical bounds concern G; rounding and hinge satisfaction after row normalization concern Q. The scalar release rebuilds without data arrays, private artifact stores or old Git objects.
