# Performance-mechanism results

All means are over 50 greedy K-means++ seeds on a fixed representation. Solver uncertainty is retained.

Preregistered mechanism gate: 0/4 datasets support the required certified contrasts; 0/4 additionally meet the edge-length identifiability condition.

| Dataset | Phase / feature / controls | Kind | gamma | ACC ± SD (%) | NMI ± SD (%) | Solver | gap |
|---|---|---|---:|---|---|---|---:|
| YaleB_cropped2414 | A / Y0 | original | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.850664562880638e-14 |
| USPS | A / Y0 | original | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.574304853154763 |
| ORL_att92 | N2_primary / N2_heat_t4_r128 | original | 1 | 77.375 ± 2.241 | 89.066 ± 0.998 | PRIMAL_DUAL_GAP_CERTIFIED | 9.389260061036607e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1 | 21.518 ± 0.438 | 27.709 ± 0.820 | PRIMAL_DUAL_GAP_CERTIFIED | 9.96242411599419e-06 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 8.224323999606042e-15 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.401846625234294e-17 |
| USPS | B / Y0 | uniform_mass | 1 | 65.538 ± 2.837 | 79.927 ± 2.162 | MAX_ITER_REACHED | 0.005695766795519227 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1000 | 65.905 ± 1.485 | 80.250 ± 1.861 | MAX_ITER_REACHED | 0.11734330442554979 |
| ORL_att92 | N2_primary / N2_W_only_heat | original | 0.345008 | 77.965 ± 1.215 | 89.663 ± 0.699 | PRIMAL_DUAL_GAP_CERTIFIED | 9.97978169408205e-06 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5889844687479331 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1 | 21.664 ± 0.457 | 27.626 ± 0.642 | MAX_ITER_REACHED | 1.131973186243433e-05 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1000 | 20.424 ± 0.366 | 30.950 ± 0.357 | MAX_ITER_REACHED | 0.02662071866385217 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5528190672474693e-14 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1 | 95.099 ± 1.461 | 94.058 ± 0.569 | PRIMAL_DUAL_GAP_CERTIFIED | 9.5039100718175e-06 |
| USPS | N2_primary / N2_W_only_heat | original | 0.0329932 | 65.409 ± 2.102 | 80.550 ± 1.518 | PRIMAL_DUAL_GAP_CERTIFIED | 9.84706372426819e-06 |
| USPS | B / Y0 | uniform_mass | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8939656700606156e-17 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.3765711620882257e-15 |
| ORL_att92 | N2_primary / N2_hard128 | original | 0.0356478 | 47.825 ± 4.428 | 67.909 ± 3.109 | PRIMAL_DUAL_GAP_CERTIFIED | 2.0851480973245636e-06 |
| YaleB_cropped2414 | N2_primary / Y0 | original | 0.248475 | 21.792 ± 0.443 | 27.701 ± 0.667 | PRIMAL_DUAL_GAP_CERTIFIED | 9.872867173560071e-06 |
| JAFFE | B / Y0 | uniform_mass | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 7.866843010416364e-06 |
| JAFFE | B / Y0 | uniform_mass | 1 | 95.099 ± 1.461 | 94.053 ± 0.568 | PRIMAL_DUAL_GAP_CERTIFIED | 9.99283644033265e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.623261037646568e-18 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8687311857608644e-17 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1e+06 | 38.794 ± 0.208 | 49.423 ± 0.209 | MAX_ITER_REACHED | 0.6397911403496657 |
| ORL_att92 | N2_primary / N2_hard128 | original | 1 | 44.395 ± 1.657 | 71.722 ± 1.227 | PRIMAL_DUAL_GAP_CERTIFIED | 9.991184097309364e-06 |
| JAFFE | A / Y0 | original | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.8119867545584043e-15 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.3374721212429672e-17 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1 | 21.505 ± 0.581 | 27.332 ± 0.659 | PRIMAL_DUAL_GAP_CERTIFIED | 9.95055400287332e-06 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1 | 65.661 ± 3.437 | 79.945 ± 2.035 | MAX_ITER_REACHED | 0.006880603465008723 |
| ORL_att92 | B / Y0 | uniform_mass | 1e+06 | 51.680 ± 1.321 | 69.300 ± 0.473 | PRIMAL_DUAL_GAP_CERTIFIED | 9.714931540108501e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1e+06 | 22.234 ± 0.483 | 31.184 ± 0.561 | MAX_ITER_REACHED | 0.023867604250633317 |
| YaleB_cropped2414 | N2_primary / N2_hard128 | original | 0.180425 | 15.967 ± 1.317 | 24.506 ± 1.530 | PRIMAL_DUAL_GAP_CERTIFIED | 8.44618818816889e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1000 | 95.305 ± 0.000 | 94.132 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 9.838947646273808e-06 |
| JAFFE | B / Y0 | oracle_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6579893884839945e-18 |
| JAFFE | N2_primary / N2_W_only_heat | original | 0.303313 | 95.305 ± 0.000 | 94.144 ± 0.021 | PRIMAL_DUAL_GAP_CERTIFIED | 9.929548933983624e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1000 | 22.292 ± 0.547 | 29.739 ± 0.834 | PRIMAL_DUAL_GAP_CERTIFIED | 9.64546569052958e-06 |
| ORL_att92 | N2_primary / Y0 | original | 0.270124 | 78.405 ± 1.181 | 89.592 ± 0.677 | PRIMAL_DUAL_GAP_CERTIFIED | 9.97194823881067e-06 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.9292022406663945e-17 |
| ORL_att92 | B / Y0 | uniform_mass | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.910519047993887e-14 |
| ORL_att92 | B / Y0 | oracle_delete | 1e+06 | 83.390 ± 0.904 | 93.452 ± 0.280 | PRIMAL_DUAL_GAP_CERTIFIED | 9.83944827886455e-06 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.4022450695326825e-14 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1 | 95.099 ± 1.461 | 94.056 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.888804845339634e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 8.71531141764541e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1 | 21.574 ± 0.501 | 27.520 ± 0.638 | PRIMAL_DUAL_GAP_CERTIFIED | 9.96025501876471e-06 |
| JAFFE | B / Y0 | uniform_mass | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6122496093322622e-18 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 6.506656121817737e-06 |
| JAFFE | A / Y0 | original | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.812149384884277e-18 |
| USPS | N2_primary / Y0 | original | 0.249611 | 65.550 ± 1.680 | 80.419 ± 1.724 | MAX_ITER_REACHED | 4.5358617832351206e-05 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1000 | 21.770 ± 0.467 | 27.792 ± 0.572 | PRIMAL_DUAL_GAP_CERTIFIED | 9.842070193397552e-06 |
| ORL_att92 | A / Y0 | original | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.0527067419044984e-17 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1e+06 | 9.944 ± 0.575 | 24.542 ± 1.751 | PRIMAL_DUAL_GAP_CERTIFIED | 9.976871701607395e-06 |
| USPS | B / Y0 | oracle_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8839096949108125e-14 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1 | 78.260 ± 1.472 | 89.759 ± 0.763 | PRIMAL_DUAL_GAP_CERTIFIED | 9.915629972041335e-06 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6107588313450947e-15 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 5.687318021044274e-17 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1e+06 | 21.770 ± 0.467 | 27.792 ± 0.572 | PRIMAL_DUAL_GAP_CERTIFIED | 9.842070193278112e-06 |
| JAFFE | N2_primary / Y0 | original | 0.25176 | 95.305 ± 0.000 | 94.134 ± 0.020 | PRIMAL_DUAL_GAP_CERTIFIED | 9.994495350995614e-06 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.82874548837475e-14 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1000 | 38.794 ± 0.208 | 49.423 ± 0.209 | MAX_ITER_REACHED | 0.6397911403496657 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5989788187595392 |
| ORL_att92 | N0_selected / Y0 | original | 500 | 76.440 ± 1.195 | 90.158 ± 0.232 | PRIMAL_DUAL_GAP_CERTIFIED | 8.91580938294739e-06 |
| ORL_att92 | N2_primary / N2_W_only_heat | original | 1 | 77.690 ± 1.437 | 90.054 ± 0.705 | PRIMAL_DUAL_GAP_CERTIFIED | 9.602883865154466e-06 |
| USPS | B / Y0 | oracle_delete | 1000 | 96.028 ± 3.528 | 93.896 ± 0.800 | MAX_ITER_REACHED | 0.3937226733951016 |
| JAFFE | N2_primary / N2_hard128 | original | 1 | 10.798 ± 0.000 | 0.000 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 4.9624672212925795e-06 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1 | 65.498 ± 2.227 | 79.997 ± 2.476 | MAX_ITER_REACHED | 0.006012002635490321 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8318679906315083e-14 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6207334913319613e-15 |
| YaleB_cropped2414 | A / Y0 | original | 1000 | 17.056 ± 0.345 | 29.669 ± 2.480 | PRIMAL_DUAL_GAP_CERTIFIED | 9.9437580940702e-06 |
| USPS | B / Y0 | uniform_mass | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8932772016810873e-14 |
| USPS | B / Y0 | uniform_mass | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6745231396620066 |
| JAFFE | B / Y0 | uniform_mass | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 8.720660388866983e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 1.1456967644561666e-17 |
| ORL_att92 | B / Y0 | oracle_delete | 1000 | 82.405 ± 1.293 | 92.842 ± 0.296 | PRIMAL_DUAL_GAP_CERTIFIED | 9.925789507355709e-06 |
| USPS | B / Y0 | oracle_delete | 1e+06 | 96.028 ± 3.528 | 93.896 ± 0.800 | MAX_ITER_REACHED | 0.2935179348908158 |
| USPS | B / Y0 / tau-sF=1.0 | static | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.4476267407026455e-14 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1 | 65.262 ± 2.582 | 80.420 ± 1.847 | MAX_ITER_REACHED | 0.006197273765549726 |
| JAFFE | B / Y0 | oracle_delete | 1000 | 95.559 ± 0.495 | 94.559 ± 0.802 | PRIMAL_DUAL_GAP_CERTIFIED | 9.81240019232967e-06 |
| JAFFE | B / Y0 | oracle_delete | 1e+06 | 95.080 ± 1.593 | 94.079 ± 0.354 | PRIMAL_DUAL_GAP_CERTIFIED | 9.486751262608968e-06 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1000 | 65.311 ± 2.752 | 80.776 ± 1.164 | MAX_ITER_REACHED | 0.4577783628554705 |
| YaleB_cropped2414 | A / Y0 | original | 1 | 21.548 ± 0.474 | 27.490 ± 0.559 | PRIMAL_DUAL_GAP_CERTIFIED | 9.969614383667304e-06 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1000 | 95.305 ± 0.000 | 94.137 ± 0.021 | PRIMAL_DUAL_GAP_CERTIFIED | 9.998673605626784e-06 |
| ORL_att92 | A / Y0 | original | 1 | 78.390 ± 1.544 | 89.740 ± 0.873 | PRIMAL_DUAL_GAP_CERTIFIED | 3.2469663116350967e-06 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.682238224141437 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 1.0890726119322167e-18 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.869232629265639e-14 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 2.7825032317303766e-18 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5052876440057048e-14 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.505862271157122e-17 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 1.1454379111874857e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.840136959785804e-17 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 8.224689917839256e-18 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1 | 65.470 ± 2.477 | 80.091 ± 2.272 | MAX_ITER_REACHED | 0.005711778326519839 |
| ORL_att92 | N2_primary / N2_heat_t4_r128 | original | 0.403824 | 76.455 ± 1.793 | 88.684 ± 0.879 | PRIMAL_DUAL_GAP_CERTIFIED | 9.968172116726889e-06 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1000 | 95.333 ± 0.199 | 94.177 ± 0.320 | PRIMAL_DUAL_GAP_CERTIFIED | 9.243125066528243e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.619872905857551e-18 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1000 | 74.465 ± 0.520 | 89.802 ± 0.210 | PRIMAL_DUAL_GAP_CERTIFIED | 9.72799516902651e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1e+06 | 24.953 ± 0.718 | 32.199 ± 0.823 | PRIMAL_DUAL_GAP_CERTIFIED | 9.665868656297854e-06 |
| JAFFE | A / Y0 | original | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.528427610330008e-06 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1e+06 | 78.365 ± 1.205 | 89.728 ± 0.642 | PRIMAL_DUAL_GAP_CERTIFIED | 1.3703268915292788e-06 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8312852319637973e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1000 | 22.272 ± 0.564 | 29.121 ± 0.579 | MAX_ITER_REACHED | 0.015084875480883721 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5455332286483667e-14 |
| YaleB_dengcai32 | A / Y0 | original | 0.001 | 25.363 ± 0.485 | 31.281 ± 0.564 | ANALYTIC_G_EQUALS_F | 6.698808174832038e-14 |
| JAFFE | N2_primary / N2_hard128 | original | 0.0245688 | 22.592 ± 4.831 | 27.092 ± 5.708 | PRIMAL_DUAL_GAP_CERTIFIED | 8.398514807566868e-06 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1 | 78.340 ± 1.439 | 89.789 ± 0.851 | PRIMAL_DUAL_GAP_CERTIFIED | 9.873347701226897e-06 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1000 | 17.761 ± 0.065 | 32.765 ± 0.068 | PRIMAL_DUAL_GAP_CERTIFIED | 9.967227796612385e-06 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 49.355 ± 2.013 | 73.958 ± 1.353 | PRIMAL_DUAL_GAP_CERTIFIED | 9.849639204135906e-06 |
| ORL_att92 | B / Y0 | oracle_delete | 1 | 78.505 ± 1.433 | 89.915 ± 0.729 | PRIMAL_DUAL_GAP_CERTIFIED | 8.3303777186145e-06 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1 | 77.995 ± 1.423 | 89.576 ± 0.682 | PRIMAL_DUAL_GAP_CERTIFIED | 9.756340998407435e-06 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.4475793068575993e-17 |
| JAFFE | B / Y0 | oracle_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.658463726934457e-15 |
| USPS | B / Y0 | uniform_mass | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5744832935999964 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 17.987 ± 0.299 | 30.622 ± 0.357 | MAX_ITER_REACHED | 0.023347016581889705 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1000 | 78.065 ± 1.482 | 89.443 ± 0.747 | PRIMAL_DUAL_GAP_CERTIFIED | 7.195854538740471e-06 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1 | 65.382 ± 2.059 | 80.319 ± 1.818 | MAX_ITER_REACHED | 0.0015043746687589277 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 9.26569959602875e-06 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1 | 65.834 ± 2.321 | 80.284 ± 1.918 | MAX_ITER_REACHED | 0.005810158238031252 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1 | 78.235 ± 1.513 | 89.893 ± 0.845 | PRIMAL_DUAL_GAP_CERTIFIED | 9.557940804043706e-06 |
| ORL_att92 | B / Y0 | oracle_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.868053559403061e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8928248685389235e-14 |
| YaleB_dengcai32 | A / Y0 | original | 1 | 25.430 ± 0.429 | 31.421 ± 0.600 | PRIMAL_DUAL_GAP_CERTIFIED | 9.982000644927544e-06 |
| YaleB_dengcai32 | A / Y0 | original | 1000 | 22.167 ± 0.406 | 37.013 ± 0.166 | PRIMAL_DUAL_GAP_CERTIFIED | 9.828377615127406e-06 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 53.415 ± 1.336 | 70.735 ± 0.575 | PRIMAL_DUAL_GAP_CERTIFIED | 9.768569890354666e-06 |
| JAFFE | N2_primary / N2_heat_t4_r128 | original | 1 | 55.418 ± 6.168 | 64.902 ± 5.042 | PRIMAL_DUAL_GAP_CERTIFIED | 9.968470939974661e-06 |
| ORL_att92 | B / Y0 | uniform_mass | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.910405206765776e-17 |
| ORL_att92 | A / Y0 | original | 1000 | 74.470 ± 0.251 | 89.618 ± 0.180 | PRIMAL_DUAL_GAP_CERTIFIED | 9.285747539022821e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1 | 95.099 ± 1.461 | 94.056 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.533632440276017e-06 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1 | 95.099 ± 1.461 | 94.059 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.970922647093852e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.454023854785159e-17 |
| JAFFE | N2_primary / N2_W_only_heat | original | 1 | 95.211 ± 1.509 | 94.231 ± 0.772 | PRIMAL_DUAL_GAP_CERTIFIED | 9.997972406312496e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1 | 21.643 ± 0.512 | 27.395 ± 0.700 | PRIMAL_DUAL_GAP_CERTIFIED | 9.996353536741654e-06 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1e+06 | 65.905 ± 1.485 | 80.250 ± 1.861 | MAX_ITER_REACHED | 0.11734330442554979 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1 | 21.777 ± 0.430 | 27.658 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.90990239808803e-06 |
| USPS | A / Y0 | original | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.932481952238163e-14 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1000 | 75.610 ± 0.565 | 90.294 ± 0.232 | PRIMAL_DUAL_GAP_CERTIFIED | 8.517335069936535e-06 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5853418226458007 |
| YaleB_cropped2414 | A / Y0 | original | 1e+06 | 10.336 ± 0.752 | 22.238 ± 3.467 | PRIMAL_DUAL_GAP_CERTIFIED | 9.92964479187255e-06 |
| YaleB_cropped2414 | N2_primary / N2_heat_t4_r128 | original | 0.0434256 | 19.421 ± 0.881 | 24.121 ± 0.922 | PRIMAL_DUAL_GAP_CERTIFIED | 3.415957130439112e-08 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6892428316816637 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1 | 95.305 ± 0.000 | 94.136 ± 0.019 | PRIMAL_DUAL_GAP_CERTIFIED | 9.665560678571736e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1000 | 95.099 ± 1.461 | 94.054 ± 0.579 | PRIMAL_DUAL_GAP_CERTIFIED | 9.780567689630894e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1e+06 | 15.651 ± 0.090 | 31.371 ± 0.086 | PRIMAL_DUAL_GAP_CERTIFIED | 9.836877118234479e-06 |
| YaleB_cropped2414 | A / Y0 | original | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.852334234226266e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8938033609995917e-17 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1000 | 75.000 ± 0.000 | 89.542 ± 0.024 | PRIMAL_DUAL_GAP_CERTIFIED | 9.534277963951636e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1e+06 | 95.023 ± 1.992 | 94.044 ± 0.649 | PRIMAL_DUAL_GAP_CERTIFIED | 8.836857105709386e-06 |
| YaleB_dengcai32 | A / Y0 | original | 1e+06 | 14.548 ± 0.582 | 29.895 ± 0.915 | PRIMAL_DUAL_GAP_CERTIFIED | 9.96452633614425e-06 |
| USPS | N2_primary / N2_W_only_heat | original | 1 | 63.705 ± 2.951 | 76.768 ± 0.998 | MAX_ITER_REACHED | 0.0023043269824527 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8941421741784934e-17 |
| ORL_att92 | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5529573030244612e-17 |
| ORL_att92 | A / Y0 | original | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.05241942832879e-14 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.047285731042071e-17 |
| JAFFE | N2_primary / N2_heat_t4_r128 | original | 0.420688 | 53.615 ± 4.997 | 62.337 ± 3.464 | PRIMAL_DUAL_GAP_CERTIFIED | 9.637494678503885e-06 |
| ORL_att92 | A / Y0 | original | 1e+06 | 53.030 ± 1.259 | 69.955 ± 0.666 | PRIMAL_DUAL_GAP_CERTIFIED | 9.81340064636629e-06 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.8102520310824275e-15 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.461061595960813e-06 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 47.570 ± 2.406 | 72.415 ± 1.552 | PRIMAL_DUAL_GAP_CERTIFIED | 9.982421628599519e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 18.066 ± 0.308 | 27.339 ± 0.280 | MAX_ITER_REACHED | 0.022572087543608652 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1 | 95.099 ± 1.461 | 94.060 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.967902781583174e-06 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1e+06 | 95.305 ± 0.000 | 94.137 ± 0.021 | PRIMAL_DUAL_GAP_CERTIFIED | 9.99867360540474e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.3784685158900754e-18 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.838174553853605e-14 |
| JAFFE | A / Y0 | original | 1 | 95.099 ± 1.461 | 94.056 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.87172756773812e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1 | 21.607 ± 0.514 | 27.532 ± 0.657 | PRIMAL_DUAL_GAP_CERTIFIED | 9.94434230803025e-06 |
| USPS | N2_primary / N2_hard128 | original | 0.0584552 | 29.946 ± 4.559 | 33.319 ± 5.133 | PRIMAL_DUAL_GAP_CERTIFIED | 7.702031689899911e-06 |
| USPS | A / Y0 | original | 1 | 65.402 ± 2.478 | 80.111 ± 2.280 | MAX_ITER_REACHED | 0.005998629176992464 |
| YaleB_cropped2414 | N2_primary / N2_W_only_heat | original | 1 | 21.871 ± 0.356 | 27.639 ± 0.602 | PRIMAL_DUAL_GAP_CERTIFIED | 9.963841434378453e-06 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8295911660692887e-17 |
| USPS | B / Y0 / tau-sF=2.0 | static | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.9290125052862095e-14 |
| USPS | B / Y0 | oracle_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8834624615146622e-17 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 5.687811333032755e-14 |
| USPS | A / Y0 | original | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.9325903724554117e-17 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1000 | 74.170 ± 0.234 | 89.840 ± 0.182 | PRIMAL_DUAL_GAP_CERTIFIED | 9.10782869640678e-06 |
| JAFFE | B / Y0 | uniform_mass | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.611192512214089e-15 |
| ORL_att92 | B / Y0 / tau-sF=1.0 | static | 1e+06 | 78.065 ± 1.482 | 89.443 ± 0.747 | PRIMAL_DUAL_GAP_CERTIFIED | 7.195854538882734e-06 |
| USPS | A / Y0 | original | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6740988122934555 |
| USPS | N0_selected / Y0 | original | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6740988122934555 |
| YaleB_dengcai32 | A / Y0 | original | 1e-06 | 25.363 ± 0.485 | 31.281 ± 0.564 | ANALYTIC_G_EQUALS_F | 6.697658920529204e-17 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.8096082860425142e-18 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1000 | 21.874 ± 0.525 | 29.919 ± 0.500 | MAX_ITER_REACHED | 0.024326481253252465 |
| ORL_att92 | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.5451645999097217e-17 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6852162739387285 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.608861477543245e-18 |
| ORL_att92 | B / Y0 | uniform_mass | 1000 | 74.480 ± 0.252 | 89.629 ± 0.185 | PRIMAL_DUAL_GAP_CERTIFIED | 9.474833882649984e-06 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.3370194668359545e-14 |
| JAFFE | N0_selected / Y0 | original | 500000 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.752572021757795e-06 |
| USPS | N2_primary / N2_hard128 | original | 1 | 26.844 ± 5.557 | 27.716 ± 6.981 | MAX_ITER_REACHED | 3.736125845704364e-05 |
| YaleB_cropped2414 | N2_primary / N2_heat_t4_r128 | original | 1 | 17.054 ± 1.008 | 29.465 ± 2.113 | PRIMAL_DUAL_GAP_CERTIFIED | 9.977325447093157e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 21.201 ± 0.490 | 31.066 ± 0.472 | MAX_ITER_REACHED | 0.017156599953388883 |
| USPS | N2_primary / N2_heat_t4_r128 | original | 1 | 17.378 ± 0.477 | 4.465 ± 0.775 | MAX_ITER_REACHED | 2.078860443715117e-05 |
| ORL_att92 | B / Y0 | uniform_mass | 1 | 78.560 ± 1.641 | 89.876 ± 0.851 | PRIMAL_DUAL_GAP_CERTIFIED | 6.740765840514423e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.823158926869991e-06 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1000 | 78.365 ± 1.205 | 89.728 ± 0.642 | PRIMAL_DUAL_GAP_CERTIFIED | 1.3703268915292788e-06 |
| JAFFE | A / Y0 | original | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 9.657303047057903e-06 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 3.046868313205664e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1000 | 15.651 ± 0.090 | 31.371 ± 0.086 | PRIMAL_DUAL_GAP_CERTIFIED | 9.918554093970117e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.4532459397264006e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1000 | 22.234 ± 0.483 | 31.184 ± 0.561 | MAX_ITER_REACHED | 0.023867604250633112 |
| YaleB_dengcai32 | N0_selected / Y3 | original | 0.001 | 43.583 ± 1.287 | 54.906 ± 0.826 | ANALYTIC_G_EQUALS_F | 2.680078381445128e-13 |
| USPS | B / Y0 / tau-sF=0.5 | static | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 2.7820627745978044e-15 |
| USPS | B / Y0 | oracle_delete | 1 | 65.716 ± 1.522 | 80.660 ± 1.547 | MAX_ITER_REACHED | 0.005554911317705742 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1e+06 | 65.311 ± 2.752 | 80.776 ± 1.164 | MAX_ITER_REACHED | 0.4577783628554705 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8323016715005025e-17 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1e+06 | 95.333 ± 0.199 | 94.177 ± 0.320 | PRIMAL_DUAL_GAP_CERTIFIED | 9.243125066528243e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.894212647319705e-14 |
| JAFFE | B / Y0 | oracle_delete | 1 | 95.117 ± 1.328 | 94.061 ± 0.508 | PRIMAL_DUAL_GAP_CERTIFIED | 9.916200327163457e-06 |
| YaleB_cropped2414 | N2_primary / N2_W_only_heat | original | 0.0716108 | 21.830 ± 0.515 | 27.687 ± 0.639 | PRIMAL_DUAL_GAP_CERTIFIED | 9.590007280776916e-06 |
| YaleB_cropped2414 | N2_primary / N2_hard128 | original | 1 | 14.644 ± 1.247 | 24.895 ± 2.131 | PRIMAL_DUAL_GAP_CERTIFIED | 9.964135963204279e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.624636619152909e-15 |
| ORL_att92 | B / Y0 / deletion-seed=302 | random_delete | 1 | 78.295 ± 1.531 | 89.844 ± 0.727 | PRIMAL_DUAL_GAP_CERTIFIED | 7.121964022564908e-06 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 1.0920084281274e-15 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1 | 21.663 ± 0.460 | 27.666 ± 0.554 | PRIMAL_DUAL_GAP_CERTIFIED | 9.981815234361822e-06 |
| ORL_att92 | B / Y0 / tau-sF=2.0 | static | 1e+06 | 75.610 ± 0.565 | 90.294 ± 0.232 | PRIMAL_DUAL_GAP_CERTIFIED | 8.517331953863489e-06 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8311741012411176e-14 |
| ORL_att92 | B / Y0 | oracle_delete | 0.001 | 78.325 ± 1.310 | 89.874 ± 0.675 | ANALYTIC_G_EQUALS_F | 2.867150961094467e-14 |
| ORL_att92 | B / Y0 / tau-sF=0.5 | static | 1 | 78.065 ± 1.464 | 89.550 ± 0.820 | PRIMAL_DUAL_GAP_CERTIFIED | 1.4310008032237755e-06 |
| USPS | N2_primary / N2_heat_t4_r128 | original | 0.0264732 | 17.387 ± 1.030 | 3.552 ± 0.490 | PRIMAL_DUAL_GAP_CERTIFIED | 3.5780245857795244e-08 |
