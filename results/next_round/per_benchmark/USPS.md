# Performance-mechanism results

All means are over 50 greedy K-means++ seeds on a fixed representation. Solver uncertainty is retained.

Preregistered mechanism gate: 0/4 datasets support the required certified contrasts; 0/4 additionally meet the edge-length identifiability condition.

| Dataset | Phase / feature / controls | Kind | gamma | ACC ± SD (%) | NMI ± SD (%) | Solver | gap |
|---|---|---|---:|---|---|---|---:|
| USPS | A / Y0 | original | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.574304853154763 |
| USPS | B / Y0 | uniform_mass | 1 | 65.538 ± 2.837 | 79.927 ± 2.162 | MAX_ITER_REACHED | 0.005695766795519227 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1000 | 65.905 ± 1.485 | 80.250 ± 1.861 | MAX_ITER_REACHED | 0.11734330442554979 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5889844687479331 |
| USPS | N2_primary / N2_W_only_heat | original | 0.0329932 | 65.409 ± 2.102 | 80.550 ± 1.518 | PRIMAL_DUAL_GAP_CERTIFIED | 9.84706372426819e-06 |
| USPS | B / Y0 | uniform_mass | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8939656700606156e-17 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1e+06 | 38.794 ± 0.208 | 49.423 ± 0.209 | MAX_ITER_REACHED | 0.6397911403496657 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1 | 65.661 ± 3.437 | 79.945 ± 2.035 | MAX_ITER_REACHED | 0.006880603465008723 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.9292022406663945e-17 |
| USPS | N2_primary / Y0 | original | 0.249611 | 65.550 ± 1.680 | 80.419 ± 1.724 | MAX_ITER_REACHED | 4.5358617832351206e-05 |
| USPS | B / Y0 | oracle_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8839096949108125e-14 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.82874548837475e-14 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1000 | 38.794 ± 0.208 | 49.423 ± 0.209 | MAX_ITER_REACHED | 0.6397911403496657 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5989788187595392 |
| USPS | B / Y0 | oracle_delete | 1000 | 96.028 ± 3.528 | 93.896 ± 0.800 | MAX_ITER_REACHED | 0.3937226733951016 |
| USPS | B / Y0 / tau-sF=2.0 | static | 1 | 65.498 ± 2.227 | 79.997 ± 2.476 | MAX_ITER_REACHED | 0.006012002635490321 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8318679906315083e-14 |
| USPS | B / Y0 | uniform_mass | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8932772016810873e-14 |
| USPS | B / Y0 | uniform_mass | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6745231396620066 |
| USPS | B / Y0 | oracle_delete | 1e+06 | 96.028 ± 3.528 | 93.896 ± 0.800 | MAX_ITER_REACHED | 0.2935179348908158 |
| USPS | B / Y0 / tau-sF=1.0 | static | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.4476267407026455e-14 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1 | 65.262 ± 2.582 | 80.420 ± 1.847 | MAX_ITER_REACHED | 0.006197273765549726 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1000 | 65.311 ± 2.752 | 80.776 ± 1.164 | MAX_ITER_REACHED | 0.4577783628554705 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.682238224141437 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 2.7825032317303766e-18 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1 | 65.470 ± 2.477 | 80.091 ± 2.272 | MAX_ITER_REACHED | 0.005711778326519839 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8312852319637973e-17 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.4475793068575993e-17 |
| USPS | B / Y0 | uniform_mass | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5744832935999964 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1 | 65.382 ± 2.059 | 80.319 ± 1.818 | MAX_ITER_REACHED | 0.0015043746687589277 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1 | 65.834 ± 2.321 | 80.284 ± 1.918 | MAX_ITER_REACHED | 0.005810158238031252 |
| USPS | B / Y0 / tau-sF=0.5 | static | 1e+06 | 65.905 ± 1.485 | 80.250 ± 1.861 | MAX_ITER_REACHED | 0.11734330442554979 |
| USPS | A / Y0 | original | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.932481952238163e-14 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 1e+06 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.5853418226458007 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6892428316816637 |
| USPS | N2_primary / N2_W_only_heat | original | 1 | 63.705 ± 2.951 | 76.768 ± 0.998 | MAX_ITER_REACHED | 0.0023043269824527 |
| USPS | N2_primary / N2_hard128 | original | 0.0584552 | 29.946 ± 4.559 | 33.319 ± 5.133 | PRIMAL_DUAL_GAP_CERTIFIED | 7.702031689899911e-06 |
| USPS | A / Y0 | original | 1 | 65.402 ± 2.478 | 80.111 ± 2.280 | MAX_ITER_REACHED | 0.005998629176992464 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8295911660692887e-17 |
| USPS | B / Y0 / tau-sF=2.0 | static | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.9290125052862095e-14 |
| USPS | B / Y0 | oracle_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8834624615146622e-17 |
| USPS | A / Y0 | original | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.9325903724554117e-17 |
| USPS | A / Y0 | original | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6740988122934555 |
| USPS | N0_selected / Y0 | original | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6740988122934555 |
| USPS | B / Y0 / deletion-seed=301 | random_delete | 1000 | 16.703 ± 0.000 | 0.000 ± 0.000 | MAX_ITER_REACHED | 0.6852162739387285 |
| USPS | N2_primary / N2_hard128 | original | 1 | 26.844 ± 5.557 | 27.716 ± 6.981 | MAX_ITER_REACHED | 3.736125845704364e-05 |
| USPS | N2_primary / N2_heat_t4_r128 | original | 1 | 17.378 ± 0.477 | 4.465 ± 0.775 | MAX_ITER_REACHED | 2.078860443715117e-05 |
| USPS | B / Y0 / tau-sF=0.5 | static | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 2.7820627745978044e-15 |
| USPS | B / Y0 | oracle_delete | 1 | 65.716 ± 1.522 | 80.660 ± 1.547 | MAX_ITER_REACHED | 0.005554911317705742 |
| USPS | B / Y0 / tau-sF=1.0 | static | 1e+06 | 65.311 ± 2.752 | 80.776 ± 1.164 | MAX_ITER_REACHED | 0.4577783628554705 |
| USPS | B / Y0 / deletion-seed=302 | random_delete | 1e-06 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8323016715005025e-17 |
| USPS | B / Y0 / deletion-seed=300 | random_delete | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | ANALYTIC_G_EQUALS_F | 1.8311741012411176e-14 |
| USPS | N2_primary / N2_heat_t4_r128 | original | 0.0264732 | 17.387 ± 1.030 | 3.552 ± 0.490 | PRIMAL_DUAL_GAP_CERTIFIED | 3.5780245857795244e-08 |
