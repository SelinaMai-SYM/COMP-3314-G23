# MSRA50: fixed-cohort results

Input `MSRA25_EBSA_16x16`: n=1799, K=12, preparation Y0. Historical identity: UNVERIFIED. Adaptations: ["native 16x16 instead of the stated 32x32"]. Locked original SSC: E13, nominal gamma 1000000.0, effective gamma 500000.0.

Conditional development evidence on a retrospectively selected cohort. ACC/NMI and sample SD are percentages from the same 50 starts. Unmatched or uncertified finite outputs are descriptive. Original SSC uses its locked historical gamma; new refinements use movement 0.10.

| panel | method | acc_mean | acc_sd | nmi_mean | nmi_sd | movement | qualified | status |
|---|---|---|---|---|---|---|---|---|
| anchor_generated | SC | 47.117 | 2.479 | 60.281 | 2.456 | 0.000 | True | EXACT_SC |
| anchor_generated | SSC_REFERENCE | 47.359 | 2.632 | 60.964 | 2.748 | 0.120 | False | REFERENCE_UNCERTIFIED |
| anchor_generated | HISTORICAL_IRLS | 47.345 | 2.721 | 61.048 | 2.741 | 0.127 | False | HISTORICAL_FINITE_IRLS |
| anchor_generated | QSSC | 47.183 | 2.646 | 60.596 | 2.691 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | UNIFORM_GRAPH_ALIAS | 47.183 | 2.646 | 60.596 | 2.691 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_CAVITY | 47.183 | 2.646 | 60.597 | 2.690 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_PILOT | 47.183 | 2.646 | 60.597 | 2.690 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_ANCHOR | 47.183 | 2.646 | 60.596 | 2.691 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_LEVERAGE | 47.181 | 2.646 | 60.592 | 2.694 | 0.099 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_SHUFFLE400 | 47.180 | 2.644 | 60.593 | 2.689 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_SHUFFLE401 | 47.181 | 2.646 | 60.592 | 2.694 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | R3_E7_SHUFFLE402 | 47.180 | 2.644 | 60.591 | 2.690 | 0.100 | True | QUALIFIED_MATCHED |
| anchor_generated | TUBE_UNIFORM | 47.019 | 2.604 | 59.982 | 2.613 | 0.043 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E1_V3_CAVITY | 47.043 | 2.658 | 59.979 | 2.648 | 0.028 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E1_V3_PILOT | 47.043 | 2.658 | 59.984 | 2.643 | 0.028 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E1_V3_SHUFFLE400 | 46.954 | 2.535 | 60.039 | 2.542 | 0.060 | False | FAILED |
| anchor_generated | R3_E1_V3_SHUFFLE401 | 47.024 | 2.527 | 60.316 | 2.412 | 0.074 | False | PATH_CPU_PROTOCOL_DEVIATION |
| anchor_generated | R3_E1_V3_SHUFFLE402 | 46.997 | 2.541 | 60.055 | 2.540 | 0.053 | False | FIT_CPU_LIMIT |
| anchor_generated | GUARD_UNIFORM | 47.102 | 2.585 | 60.113 | 2.588 | 0.053 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E5_V2_CAVITY | 47.163 | 2.588 | 60.237 | 2.544 | 0.076 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E5_V2_PILOT | 47.163 | 2.588 | 60.237 | 2.544 | 0.076 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E5_V2_SHUFFLE400 | 47.112 | 2.594 | 60.142 | 2.566 | 0.051 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E5_V2_SHUFFLE401 | 47.095 | 2.603 | 60.079 | 2.644 | 0.053 | False | FIT_CPU_LIMIT |
| anchor_generated | R3_E5_V2_SHUFFLE402 | 47.069 | 2.635 | 60.073 | 2.652 | 0.042 | False | FIT_CPU_LIMIT |
| native | SC | 47.117 | 2.479 | 60.281 | 2.456 | 0.000 | True | EXACT_SC |
| native | SSC_REFERENCE | 47.759 | 2.412 | 61.425 | 2.160 | 0.120 | False | REFERENCE_UNCERTIFIED |
| native | HISTORICAL_IRLS | 47.061 | 2.626 | 60.985 | 2.780 | 0.127 | False | HISTORICAL_FINITE_IRLS |
| native | QSSC | 47.344 | 2.937 | 61.068 | 3.098 | 0.100 | True | QUALIFIED_MATCHED |
| native | UNIFORM_GRAPH_ALIAS | 47.344 | 2.937 | 61.068 | 3.098 | 0.100 | True | QUALIFIED_MATCHED |
| native | R3_E7_CAVITY | 47.310 | 2.894 | 61.043 | 3.099 | 0.100 | True | QUALIFIED_MATCHED |
| native | R3_E7_PILOT | 47.310 | 2.894 | 61.043 | 3.099 | 0.100 | True | QUALIFIED_MATCHED |
| native | R3_E7_ANCHOR | 47.285 | 2.906 | 61.064 | 3.097 | 0.100 | True | QUALIFIED_MATCHED |
| native | R3_E7_LEVERAGE | 47.271 | 3.018 | 60.838 | 2.920 | 0.099 | True | QUALIFIED_MATCHED |
| native | R3_E7_SHUFFLE400 | 47.327 | 2.935 | 61.046 | 3.073 | 0.100 | True | QUALIFIED_MATCHED |
| native | R3_E7_SHUFFLE401 | 47.383 | 2.956 | 60.960 | 2.978 | 0.100 | True | QUALIFIED_MATCHED |
| native | R3_E7_SHUFFLE402 | 47.307 | 2.946 | 60.871 | 2.874 | 0.100 | True | QUALIFIED_MATCHED |
| native | TUBE_UNIFORM | 46.876 | 2.615 | 59.891 | 2.501 | 0.043 | False | FIT_CPU_LIMIT |
| native | R3_E1_V3_CAVITY | 47.614 | 3.165 | 60.057 | 2.920 | 0.028 | False | FIT_CPU_LIMIT |
| native | R3_E1_V3_PILOT | 47.705 | 3.119 | 60.185 | 2.930 | 0.028 | False | FIT_CPU_LIMIT |
| native | R3_E1_V3_SHUFFLE400 | 46.953 | 2.550 | 60.355 | 2.737 | 0.060 | False | FAILED |
| native | R3_E1_V3_SHUFFLE401 | 46.952 | 2.547 | 60.774 | 2.593 | 0.074 | False | PATH_CPU_PROTOCOL_DEVIATION |
| native | R3_E1_V3_SHUFFLE402 | 46.919 | 2.550 | 60.158 | 2.758 | 0.053 | False | FIT_CPU_LIMIT |
| native | GUARD_UNIFORM | 47.341 | 2.718 | 60.334 | 2.653 | 0.053 | False | FIT_CPU_LIMIT |
| native | R3_E5_V2_CAVITY | 47.164 | 2.806 | 60.449 | 2.916 | 0.076 | False | FIT_CPU_LIMIT |
| native | R3_E5_V2_PILOT | 47.164 | 2.806 | 60.449 | 2.916 | 0.076 | False | FIT_CPU_LIMIT |
| native | R3_E5_V2_SHUFFLE400 | 47.538 | 2.848 | 60.655 | 2.431 | 0.051 | False | FIT_CPU_LIMIT |
| native | R3_E5_V2_SHUFFLE401 | 47.619 | 2.883 | 60.772 | 2.432 | 0.053 | False | FIT_CPU_LIMIT |
| native | R3_E5_V2_SHUFFLE402 | 47.434 | 3.058 | 60.466 | 2.853 | 0.042 | False | FIT_CPU_LIMIT |

## Paired candidate contrasts

| panel | candidate | control | acc_delta | nmi_delta | acc_lower | acc_upper | nmi_lower | nmi_upper | qualified_pair | status |
|---|---|---|---|---|---|---|---|---|---|---|
| anchor_generated | R3_E7_CAVITY | QSSC | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.003 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | SC | 0.066 | 0.317 | -0.127 | 0.295 | -0.032 | 0.673 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | SSC_REFERENCE | -0.176 | -0.367 | -0.330 | -0.047 | -0.563 | -0.153 | False | COMPLETE |
| anchor_generated | R3_E7_CAVITY | R3_E7_PILOT | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | UNIFORM_GRAPH_ALIAS | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.003 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | R3_E7_ANCHOR | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.003 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | R3_E7_LEVERAGE | 0.002 | 0.005 | 0.000 | 0.007 | 0.000 | 0.014 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | R3_E7_SHUFFLE400 | 0.003 | 0.004 | 0.000 | 0.008 | -0.001 | 0.010 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | R3_E7_SHUFFLE401 | 0.002 | 0.005 | 0.000 | 0.007 | 0.000 | 0.014 | True | COMPLETE |
| anchor_generated | R3_E7_CAVITY | R3_E7_SHUFFLE402 | 0.003 | 0.006 | 0.000 | 0.008 | 0.001 | 0.012 | True | COMPLETE |
| native | R3_E7_CAVITY | QSSC | -0.034 | -0.025 | -0.177 | 0.073 | -0.078 | 0.005 | True | COMPLETE |
| native | R3_E7_CAVITY | SC | 0.192 | 0.762 | -0.719 | 1.138 | -0.232 | 1.749 | True | COMPLETE |
| native | R3_E7_CAVITY | SSC_REFERENCE | -0.449 | -0.382 | -1.412 | 0.587 | -1.258 | 0.514 | False | COMPLETE |
| native | R3_E7_CAVITY | R3_E7_PILOT | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | True | COMPLETE |
| native | R3_E7_CAVITY | UNIFORM_GRAPH_ALIAS | -0.034 | -0.025 | -0.177 | 0.073 | -0.078 | 0.005 | True | COMPLETE |
| native | R3_E7_CAVITY | R3_E7_ANCHOR | 0.024 | -0.021 | 0.000 | 0.073 | -0.073 | 0.006 | True | COMPLETE |
| native | R3_E7_CAVITY | R3_E7_LEVERAGE | 0.039 | 0.205 | -0.140 | 0.229 | -0.119 | 0.589 | True | COMPLETE |
| native | R3_E7_CAVITY | R3_E7_SHUFFLE400 | -0.018 | -0.003 | -0.169 | 0.089 | -0.072 | 0.062 | True | COMPLETE |
| native | R3_E7_CAVITY | R3_E7_SHUFFLE401 | -0.073 | 0.083 | -0.176 | 0.000 | -0.033 | 0.276 | True | COMPLETE |
| native | R3_E7_CAVITY | R3_E7_SHUFFLE402 | 0.002 | 0.172 | -0.119 | 0.116 | -0.016 | 0.430 | True | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | QSSC | -0.140 | -0.617 | -0.286 | -0.020 | -0.799 | -0.447 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | SC | -0.074 | -0.301 | -0.206 | 0.102 | -0.574 | -0.021 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | SSC_REFERENCE | -0.316 | -0.985 | -0.516 | -0.150 | -1.244 | -0.716 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | R3_E1_V3_PILOT | 0.000 | -0.005 | 0.000 | 0.000 | -0.013 | 0.000 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | TUBE_UNIFORM | 0.023 | -0.003 | -0.011 | 0.059 | -0.099 | 0.087 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | R3_E1_V3_SHUFFLE400 | 0.089 | -0.060 | 0.004 | 0.169 | -0.219 | 0.088 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | R3_E1_V3_SHUFFLE401 | 0.019 | -0.337 | -0.077 | 0.116 | -0.491 | -0.188 | False | COMPLETE |
| anchor_generated | R3_E1_V3_CAVITY | R3_E1_V3_SHUFFLE402 | 0.046 | -0.076 | -0.022 | 0.115 | -0.210 | 0.044 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | QSSC | 0.270 | -1.011 | -0.666 | 1.166 | -1.945 | -0.084 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | SC | 0.497 | -0.224 | -0.410 | 1.407 | -1.131 | 0.685 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | SSC_REFERENCE | -0.145 | -1.368 | -1.066 | 0.787 | -2.072 | -0.616 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | R3_E1_V3_PILOT | -0.091 | -0.128 | -0.280 | 0.007 | -0.339 | 0.000 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | TUBE_UNIFORM | 0.738 | 0.166 | -0.020 | 1.508 | -0.578 | 0.955 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | R3_E1_V3_SHUFFLE400 | 0.661 | -0.298 | -0.258 | 1.629 | -1.225 | 0.622 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | R3_E1_V3_SHUFFLE401 | 0.663 | -0.717 | -0.295 | 1.601 | -1.508 | 0.047 | False | COMPLETE |
| native | R3_E1_V3_CAVITY | R3_E1_V3_SHUFFLE402 | 0.695 | -0.101 | -0.199 | 1.586 | -0.946 | 0.750 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | QSSC | -0.020 | -0.359 | -0.122 | 0.109 | -0.519 | -0.199 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | SC | 0.046 | -0.044 | -0.173 | 0.306 | -0.370 | 0.315 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | SSC_REFERENCE | -0.196 | -0.727 | -0.297 | -0.093 | -0.954 | -0.470 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | R3_E5_V2_PILOT | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | GUARD_UNIFORM | 0.061 | 0.124 | -0.028 | 0.181 | 0.016 | 0.239 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | R3_E5_V2_SHUFFLE400 | 0.051 | 0.095 | -0.038 | 0.175 | 0.003 | 0.191 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | R3_E5_V2_SHUFFLE401 | 0.068 | 0.158 | -0.026 | 0.188 | 0.038 | 0.291 | False | COMPLETE |
| anchor_generated | R3_E5_V2_CAVITY | R3_E5_V2_SHUFFLE402 | 0.093 | 0.164 | -0.017 | 0.237 | 0.034 | 0.306 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | QSSC | -0.180 | -0.619 | -0.989 | 0.679 | -1.488 | 0.276 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | SC | 0.047 | 0.168 | -0.803 | 0.921 | -0.843 | 1.213 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | SSC_REFERENCE | -0.595 | -0.976 | -1.543 | 0.377 | -1.815 | -0.081 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | R3_E5_V2_PILOT | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | GUARD_UNIFORM | -0.177 | 0.115 | -0.972 | 0.657 | -0.641 | 0.897 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | R3_E5_V2_SHUFFLE400 | -0.374 | -0.206 | -1.165 | 0.454 | -0.888 | 0.493 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | R3_E5_V2_SHUFFLE401 | -0.455 | -0.323 | -1.331 | 0.468 | -1.221 | 0.616 | False | COMPLETE |
| native | R3_E5_V2_CAVITY | R3_E5_V2_SHUFFLE402 | -0.270 | -0.017 | -1.250 | 0.692 | -0.966 | 0.911 | False | COMPLETE |

Intervals are pointwise 95% paired bootstrap intervals (10,000 draws, seed 424242), conditional on these fixed embeddings and rounding starts. They are unadjusted for multiple comparisons and do not quantify dataset generalization or solver uncertainty.
