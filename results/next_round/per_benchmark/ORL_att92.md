# Performance-mechanism results

All means are over 50 greedy K-means++ seeds on a fixed representation. Solver uncertainty is retained.

Preregistered mechanism gate: 0/4 datasets support the required certified contrasts; 0/4 additionally meet the edge-length identifiability condition.

| Dataset | Phase / feature / controls | Kind | gamma | ACC ± SD (%) | NMI ± SD (%) | Solver | gap |
|---|---|---|---:|---|---|---|---:|
| ORL_att92 | N2_primary / N2_heat_t4_r128 | original | 1 | 77.375 ± 2.241 | 89.066 ± 0.998 | PRIMAL_DUAL_GAP_CERTIFIED | 9.389260061036607e-06 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 8.224323999606042e-15 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.401846625234294e-17 |
| ORL_att92 | N2_primary / N2_W_only_heat | original | 0.345008 | 77.965 ± 1.215 | 89.663 ± 0.699 | PRIMAL_DUAL_GAP_CERTIFIED | 9.97978169408205e-06 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5528190672474693e-14 |
| ORL_att92 | N2_primary / N2_hard128 | original | 0.0356478 | 47.825 ± 4.428 | 67.909 ± 3.109 | PRIMAL_DUAL_GAP_CERTIFIED | 2.0851480973245636e-06 |
| ORL_att92 | N2_primary / N2_hard128 | original | 1 | 44.395 ± 1.657 | 71.722 ± 1.227 | PRIMAL_DUAL_GAP_CERTIFIED | 9.991184097309364e-06 |
| ORL_att92 | B / Y0 | uniform_mass | 1e+06 | 51.680 ± 1.321 | 69.300 ± 0.473 | PRIMAL_DUAL_GAP_CERTIFIED | 9.714931540108501e-06 |
| ORL_att92 | N2_primary / Y0 | original | 0.270124 | 78.405 ± 1.181 | 89.592 ± 0.677 | PRIMAL_DUAL_GAP_CERTIFIED | 9.97194823881067e-06 |
| ORL_att92 | B / Y0 | uniform_mass | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.910519047993887e-14 |
| ORL_att92 | B / Y0 | oracle_delete | 1e+06 | 83.390 ± 0.904 | 93.452 ± 0.280 | PRIMAL_DUAL_GAP_CERTIFIED | 9.83944827886455e-06 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.4022450695326825e-14 |
| ORL_att92 | A / Y0 | original | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.0527067419044984e-17 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1 | 78.260 ± 1.472 | 89.759 ± 0.763 | PRIMAL_DUAL_GAP_CERTIFIED | 9.915629972041335e-06 |
| ORL_att92 | N0_selected / Y0 | original | 500 | 76.440 ± 1.195 | 90.158 ± 0.232 | PRIMAL_DUAL_GAP_CERTIFIED | 8.91580938294739e-06 |
| ORL_att92 | N2_primary / N2_W_only_heat | original | 1 | 77.690 ± 1.437 | 90.054 ± 0.705 | PRIMAL_DUAL_GAP_CERTIFIED | 9.602883865154466e-06 |
| ORL_att92 | B / Y0 | oracle_delete | 1000 | 82.405 ± 1.293 | 92.842 ± 0.296 | PRIMAL_DUAL_GAP_CERTIFIED | 9.925789507355709e-06 |
| ORL_att92 | A / Y0 | original | 1 | 78.390 ± 1.544 | 89.740 ± 0.873 | PRIMAL_DUAL_GAP_CERTIFIED | 3.2469663116350967e-06 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5052876440057048e-14 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.505862271157122e-17 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 8.224689917839256e-18 |
| ORL_att92 | N2_primary / N2_heat_t4_r128 | original | 0.403824 | 76.455 ± 1.793 | 88.684 ± 0.879 | PRIMAL_DUAL_GAP_CERTIFIED | 9.968172116726889e-06 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1000 | 74.465 ± 0.520 | 89.802 ± 0.210 | PRIMAL_DUAL_GAP_CERTIFIED | 9.72799516902651e-06 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1e+06 | 78.365 ± 1.205 | 89.728 ± 0.642 | PRIMAL_DUAL_GAP_CERTIFIED | 1.3703268915292788e-06 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5455332286483667e-14 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1 | 78.340 ± 1.439 | 89.789 ± 0.851 | PRIMAL_DUAL_GAP_CERTIFIED | 9.873347701226897e-06 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 49.355 ± 2.013 | 73.958 ± 1.353 | PRIMAL_DUAL_GAP_CERTIFIED | 9.849639204135906e-06 |
| ORL_att92 | B / Y0 | oracle_delete | 1 | 78.505 ± 1.433 | 89.915 ± 0.729 | PRIMAL_DUAL_GAP_CERTIFIED | 8.3303777186145e-06 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1 | 77.995 ± 1.423 | 89.576 ± 0.682 | PRIMAL_DUAL_GAP_CERTIFIED | 9.756340998407435e-06 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1000 | 78.065 ± 1.482 | 89.443 ± 0.747 | PRIMAL_DUAL_GAP_CERTIFIED | 7.195854538740471e-06 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1 | 78.235 ± 1.513 | 89.893 ± 0.845 | PRIMAL_DUAL_GAP_CERTIFIED | 9.557940804043706e-06 |
| ORL_att92 | B / Y0 | oracle_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.868053559403061e-17 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 53.415 ± 1.336 | 70.735 ± 0.575 | PRIMAL_DUAL_GAP_CERTIFIED | 9.768569890354666e-06 |
| ORL_att92 | B / Y0 | uniform_mass | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.910405206765776e-17 |
| ORL_att92 | A / Y0 | original | 1000 | 74.470 ± 0.251 | 89.618 ± 0.180 | PRIMAL_DUAL_GAP_CERTIFIED | 9.285747539022821e-06 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1000 | 75.610 ± 0.565 | 90.294 ± 0.232 | PRIMAL_DUAL_GAP_CERTIFIED | 8.517335069936535e-06 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1000 | 75.000 ± 0.000 | 89.542 ± 0.024 | PRIMAL_DUAL_GAP_CERTIFIED | 9.534277963951636e-06 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5529573030244612e-17 |
| ORL_att92 | A / Y0 | original | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.05241942832879e-14 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.047285731042071e-17 |
| ORL_att92 | A / Y0 | original | 1e+06 | 53.030 ± 1.259 | 69.955 ± 0.666 | PRIMAL_DUAL_GAP_CERTIFIED | 9.81340064636629e-06 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 47.570 ± 2.406 | 72.415 ± 1.552 | PRIMAL_DUAL_GAP_CERTIFIED | 9.982421628599519e-06 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1000 | 74.170 ± 0.234 | 89.840 ± 0.182 | PRIMAL_DUAL_GAP_CERTIFIED | 9.10782869640678e-06 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1e+06 | 78.065 ± 1.482 | 89.443 ± 0.747 | PRIMAL_DUAL_GAP_CERTIFIED | 7.195854538882734e-06 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5451645999097217e-17 |
| ORL_att92 | B / Y0 | uniform_mass | 1000 | 74.480 ± 0.252 | 89.629 ± 0.185 | PRIMAL_DUAL_GAP_CERTIFIED | 9.474833882649984e-06 |
| ORL_att92 | B / Y0 | uniform_mass | 1 | 78.560 ± 1.641 | 89.876 ± 0.851 | PRIMAL_DUAL_GAP_CERTIFIED | 6.740765840514423e-06 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1000 | 78.365 ± 1.205 | 89.728 ± 0.642 | PRIMAL_DUAL_GAP_CERTIFIED | 1.3703268915292788e-06 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.046868313205664e-14 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1 | 78.295 ± 1.531 | 89.844 ± 0.727 | PRIMAL_DUAL_GAP_CERTIFIED | 7.121964022564908e-06 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1e+06 | 75.610 ± 0.565 | 90.294 ± 0.232 | PRIMAL_DUAL_GAP_CERTIFIED | 8.517331953863489e-06 |
| ORL_att92 | B / Y0 | oracle_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.867150961094467e-14 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1 | 78.065 ± 1.464 | 89.550 ± 0.820 | PRIMAL_DUAL_GAP_CERTIFIED | 1.4310008032237755e-06 |
