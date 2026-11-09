# Performance-mechanism results

All means are over 50 greedy K-means++ seeds on a fixed representation. Solver uncertainty is retained.

Preregistered mechanism gate: 0/4 datasets support the required certified contrasts; 0/4 additionally meet the edge-length identifiability condition.

| Dataset | Phase / feature / controls | Kind | gamma | ACC ± SD (%) | NMI ± SD (%) | Solver | gap |
|---|---|---|---:|---|---|---|---:|
| YaleB_cropped2414 | A / Y0 | original | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.850664562880638e-14 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1 | 21.518 ± 0.438 | 27.709 ± 0.820 | PRIMAL_DUAL_GAP_CERTIFIED | 9.96242411599419e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1 | 21.664 ± 0.457 | 27.626 ± 0.642 | MAX_ITER_REACHED | 1.131973186243433e-05 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1000 | 20.424 ± 0.366 | 30.950 ± 0.357 | MAX_ITER_REACHED | 0.02662071866385217 |
| YaleB_cropped2414 | N2_primary / Y0 | original | 0.248475 | 21.792 ± 0.443 | 27.701 ± 0.667 | PRIMAL_DUAL_GAP_CERTIFIED | 9.872867173560071e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8687311857608644e-17 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.3374721212429672e-17 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1 | 21.505 ± 0.581 | 27.332 ± 0.659 | PRIMAL_DUAL_GAP_CERTIFIED | 9.95055400287332e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1e+06 | 22.234 ± 0.483 | 31.184 ± 0.561 | MAX_ITER_REACHED | 0.023867604250633317 |
| YaleB_cropped2414 | N2_primary / N2_hard128 | original | 0.180425 | 15.967 ± 1.317 | 24.506 ± 1.530 | PRIMAL_DUAL_GAP_CERTIFIED | 8.44618818816889e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1000 | 22.292 ± 0.547 | 29.739 ± 0.834 | PRIMAL_DUAL_GAP_CERTIFIED | 9.64546569052958e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1 | 21.574 ± 0.501 | 27.520 ± 0.638 | PRIMAL_DUAL_GAP_CERTIFIED | 9.96025501876471e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1000 | 21.770 ± 0.467 | 27.792 ± 0.572 | PRIMAL_DUAL_GAP_CERTIFIED | 9.842070193397552e-06 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1e+06 | 9.944 ± 0.575 | 24.542 ± 1.751 | PRIMAL_DUAL_GAP_CERTIFIED | 9.976871701607395e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 5.687318021044274e-17 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1e+06 | 21.770 ± 0.467 | 27.792 ± 0.572 | PRIMAL_DUAL_GAP_CERTIFIED | 9.842070193278112e-06 |
| YaleB_cropped2414 | A / Y0 | original | 1000 | 17.056 ± 0.345 | 29.669 ± 2.480 | PRIMAL_DUAL_GAP_CERTIFIED | 9.9437580940702e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 1.1456967644561666e-17 |
| YaleB_cropped2414 | A / Y0 | original | 1 | 21.548 ± 0.474 | 27.490 ± 0.559 | PRIMAL_DUAL_GAP_CERTIFIED | 9.969614383667304e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.869232629265639e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 1.1454379111874857e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.840136959785804e-17 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1e+06 | 24.953 ± 0.718 | 32.199 ± 0.823 | PRIMAL_DUAL_GAP_CERTIFIED | 9.665868656297854e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1000 | 22.272 ± 0.564 | 29.121 ± 0.579 | MAX_ITER_REACHED | 0.015084875480883721 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1000 | 17.761 ± 0.065 | 32.765 ± 0.068 | PRIMAL_DUAL_GAP_CERTIFIED | 9.967227796612385e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 17.987 ± 0.299 | 30.622 ± 0.357 | MAX_ITER_REACHED | 0.023347016581889705 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8928248685389235e-14 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.454023854785159e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1 | 21.643 ± 0.512 | 27.395 ± 0.700 | PRIMAL_DUAL_GAP_CERTIFIED | 9.996353536741654e-06 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 1 | 21.777 ± 0.430 | 27.658 ± 0.553 | PRIMAL_DUAL_GAP_CERTIFIED | 9.90990239808803e-06 |
| YaleB_cropped2414 | A / Y0 | original | 1e+06 | 10.336 ± 0.752 | 22.238 ± 3.467 | PRIMAL_DUAL_GAP_CERTIFIED | 9.92964479187255e-06 |
| YaleB_cropped2414 | N2_primary / N2_heat_t4_r128 | original | 0.0434256 | 19.421 ± 0.881 | 24.121 ± 0.922 | PRIMAL_DUAL_GAP_CERTIFIED | 3.415957130439112e-08 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1e+06 | 15.651 ± 0.090 | 31.371 ± 0.086 | PRIMAL_DUAL_GAP_CERTIFIED | 9.836877118234479e-06 |
| YaleB_cropped2414 | A / Y0 | original | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.852334234226266e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8938033609995917e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.8941421741784934e-17 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 18.066 ± 0.308 | 27.339 ± 0.280 | MAX_ITER_REACHED | 0.022572087543608652 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 7.838174553853605e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=0.5 | static | 1 | 21.607 ± 0.514 | 27.532 ± 0.657 | PRIMAL_DUAL_GAP_CERTIFIED | 9.94434230803025e-06 |
| YaleB_cropped2414 | N2_primary / N2_W_only_heat | original | 1 | 21.871 ± 0.356 | 27.639 ± 0.602 | PRIMAL_DUAL_GAP_CERTIFIED | 9.963841434378453e-06 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 5.687811333032755e-14 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 1000 | 21.874 ± 0.525 | 29.919 ± 0.500 | MAX_ITER_REACHED | 0.024326481253252465 |
| YaleB_cropped2414 | B / Y0 | uniform_mass | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.3370194668359545e-14 |
| YaleB_cropped2414 | N2_primary / N2_heat_t4_r128 | original | 1 | 17.054 ± 1.008 | 29.465 ± 2.113 | PRIMAL_DUAL_GAP_CERTIFIED | 9.977325447093157e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 21.201 ± 0.490 | 31.066 ± 0.472 | MAX_ITER_REACHED | 0.017156599953388883 |
| YaleB_cropped2414 | B / Y0 / tau-sF=2.0 | static | 1000 | 15.651 ± 0.090 | 31.371 ± 0.086 | PRIMAL_DUAL_GAP_CERTIFIED | 9.918554093970117e-06 |
| YaleB_cropped2414 | B / Y0 | oracle_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.4532459397264006e-14 |
| YaleB_cropped2414 | B / Y0 / tau-sF=1.0 | static | 1000 | 22.234 ± 0.483 | 31.184 ± 0.561 | MAX_ITER_REACHED | 0.023867604250633112 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 21.781 ± 0.454 | 27.731 ± 0.585 | ANALYTIC_G_EQUALS_F | 2.894212647319705e-14 |
| YaleB_cropped2414 | N2_primary / N2_W_only_heat | original | 0.0716108 | 21.830 ± 0.515 | 27.687 ± 0.639 | PRIMAL_DUAL_GAP_CERTIFIED | 9.590007280776916e-06 |
| YaleB_cropped2414 | N2_primary / N2_hard128 | original | 1 | 14.644 ± 1.247 | 24.895 ± 2.131 | PRIMAL_DUAL_GAP_CERTIFIED | 9.964135963204279e-06 |
| YaleB_cropped2414 | B / Y0 / deletion-seed=302 | random_delete | 1 | 21.663 ± 0.460 | 27.666 ± 0.554 | PRIMAL_DUAL_GAP_CERTIFIED | 9.981815234361822e-06 |
