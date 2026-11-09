# Performance-mechanism results

All means are over 50 greedy K-means++ seeds on a fixed representation. Solver uncertainty is retained.

Preregistered mechanism gate: 0/4 datasets support the required certified contrasts; 0/4 additionally meet the edge-length identifiability condition.

| Dataset | Phase / feature / controls | Kind | gamma | ACC ± SD (%) | NMI ± SD (%) | Solver | gap |
|---|---|---|---:|---|---|---|---:|
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1 | 95.099 ± 1.461 | 94.058 ± 0.569 | PRIMAL_DUAL_GAP_CERTIFIED | 9.5039100718175e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.3765711620882257e-15 |
| JAFFE | B / Y0 | uniform_mass | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 7.866843010416364e-06 |
| JAFFE | B / Y0 | uniform_mass | 1 | 95.099 ± 1.461 | 94.053 ± 0.568 | PRIMAL_DUAL_GAP_CERTIFIED | 9.99283644033265e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.623261037646568e-18 |
| JAFFE | A / Y0 | original | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.8119867545584043e-15 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1000 | 95.305 ± 0.000 | 94.132 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 9.838947646273808e-06 |
| JAFFE | B / Y0 | oracle_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6579893884839945e-18 |
| JAFFE | N2_primary / N2_W_only_heat | original | 0.303313 | 95.305 ± 0.000 | 94.144 ± 0.021 | PRIMAL_DUAL_GAP_CERTIFIED | 9.929548933983624e-06 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1 | 95.099 ± 1.461 | 94.056 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.888804845339634e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 8.71531141764541e-06 |
| JAFFE | B / Y0 | uniform_mass | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6122496093322622e-18 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 6.506656121817737e-06 |
| JAFFE | A / Y0 | original | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.812149384884277e-18 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6107588313450947e-15 |
| JAFFE | N2_primary / Y0 | original | 0.25176 | 95.305 ± 0.000 | 94.134 ± 0.020 | PRIMAL_DUAL_GAP_CERTIFIED | 9.994495350995614e-06 |
| JAFFE | N2_primary / N2_hard128 | original | 1 | 10.798 ± 0.000 | 0.000 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 4.9624672212925795e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.6207334913319613e-15 |
| JAFFE | B / Y0 | uniform_mass | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 8.720660388866983e-06 |
| JAFFE | B / Y0 | oracle_delete | 1000 | 95.559 ± 0.495 | 94.559 ± 0.802 | PRIMAL_DUAL_GAP_CERTIFIED | 9.81240019232967e-06 |
| JAFFE | B / Y0 | oracle_delete | 1e+06 | 95.080 ± 1.593 | 94.079 ± 0.354 | PRIMAL_DUAL_GAP_CERTIFIED | 9.486751262608968e-06 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1000 | 95.305 ± 0.000 | 94.137 ± 0.021 | PRIMAL_DUAL_GAP_CERTIFIED | 9.998673605626784e-06 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 1.0890726119322167e-18 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1000 | 95.333 ± 0.199 | 94.177 ± 0.320 | PRIMAL_DUAL_GAP_CERTIFIED | 9.243125066528243e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.619872905857551e-18 |
| JAFFE | A / Y0 | original | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.528427610330008e-06 |
| JAFFE | N2_primary / N2_hard128 | original | 0.0245688 | 22.592 ± 4.831 | 27.092 ± 5.708 | PRIMAL_DUAL_GAP_CERTIFIED | 8.398514807566868e-06 |
| JAFFE | B / Y0 | oracle_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.658463726934457e-15 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 9.26569959602875e-06 |
| JAFFE | N2_primary / N2_heat_t4_r128 | original | 1 | 55.418 ± 6.168 | 64.902 ± 5.042 | PRIMAL_DUAL_GAP_CERTIFIED | 9.968470939974661e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 1 | 95.099 ± 1.461 | 94.056 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.533632440276017e-06 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1 | 95.099 ± 1.461 | 94.059 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.970922647093852e-06 |
| JAFFE | N2_primary / N2_W_only_heat | original | 1 | 95.211 ± 1.509 | 94.231 ± 0.772 | PRIMAL_DUAL_GAP_CERTIFIED | 9.997972406312496e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1 | 95.305 ± 0.000 | 94.136 ± 0.019 | PRIMAL_DUAL_GAP_CERTIFIED | 9.665560678571736e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1000 | 95.099 ± 1.461 | 94.054 ± 0.579 | PRIMAL_DUAL_GAP_CERTIFIED | 9.780567689630894e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1e+06 | 95.023 ± 1.992 | 94.044 ± 0.649 | PRIMAL_DUAL_GAP_CERTIFIED | 8.836857105709386e-06 |
| JAFFE | N2_primary / N2_heat_t4_r128 | original | 0.420688 | 53.615 ± 4.997 | 62.337 ± 3.464 | PRIMAL_DUAL_GAP_CERTIFIED | 9.637494678503885e-06 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.8102520310824275e-15 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.461061595960813e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1 | 95.099 ± 1.461 | 94.060 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.967902781583174e-06 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 1e+06 | 95.305 ± 0.000 | 94.137 ± 0.021 | PRIMAL_DUAL_GAP_CERTIFIED | 9.99867360540474e-06 |
| JAFFE | B / Y0 / tau-sF=1.0 | static | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.3784685158900754e-18 |
| JAFFE | A / Y0 | original | 1 | 95.099 ± 1.461 | 94.056 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.87172756773812e-06 |
| JAFFE | B / Y0 | uniform_mass | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.611192512214089e-15 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.8096082860425142e-18 |
| JAFFE | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.608861477543245e-18 |
| JAFFE | N0_selected / Y0 | original | 500000 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.752572021757795e-06 |
| JAFFE | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 95.305 ± 0.000 | 94.091 ± 0.000 | PRIMAL_DUAL_GAP_CERTIFIED | 9.823158926869991e-06 |
| JAFFE | A / Y0 | original | 1000 | 95.305 ± 0.000 | 94.131 ± 0.017 | PRIMAL_DUAL_GAP_CERTIFIED | 9.657303047057903e-06 |
| JAFFE | B / Y0 / tau-sF=2.0 | static | 1e+06 | 95.333 ± 0.199 | 94.177 ± 0.320 | PRIMAL_DUAL_GAP_CERTIFIED | 9.243125066528243e-06 |
| JAFFE | B / Y0 | oracle_delete | 1 | 95.117 ± 1.328 | 94.061 ± 0.508 | PRIMAL_DUAL_GAP_CERTIFIED | 9.916200327163457e-06 |
| JAFFE | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 2.624636619152909e-15 |
| JAFFE | B / Y0 / tau-sF=0.5 | static | 0.001 | 95.305 ± 0.000 | 94.134 ± 0.020 | ANALYTIC_G_EQUALS_F | 1.0920084281274e-15 |
