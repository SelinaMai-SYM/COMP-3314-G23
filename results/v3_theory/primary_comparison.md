# Primary comparisons

Source commit recorded at assembly: `5355ee04d0b052d0a61ad5bbc7c50520b4058361`.

The five contrasts were fixed before measurement: X1 multiplier 1 versus SSC gamma=1; X2 beta=1 versus beta=0; X3 mass-normalized tau=1 versus original gamma=1; X4 multi-scale versus k=5; X5 alpha=1 versus alpha=0. Seed-level intervals are conditional on fixed F and G. Dataset-level intervals use ORL, JAFFE, USPS, and one YaleB unit. A Bonferroni 99% interval is reported across the five contrasts. An interval that covers 0 is not a significant improvement.

| contrast | datasets | mean ACC diff | uncorrected 95% | Bonferroni 99% | excludes 0 |
| --- | --- | --- | --- | --- | --- |
| X1 | ORL|JAFFE|USPS|YaleB | 0.0002 | [-0.0013, 0.0015] | [-0.0015, 0.0018] | False |
| X2 | ORL|JAFFE|USPS|YaleB | -0.0004 | [-0.0024, 0.0014] | [-0.0024, 0.0015] | False |
| X3 | ORL|JAFFE|USPS|YaleB | -0.0026 | [-0.0073, 0.0021] | [-0.0084, 0.0022] | False |
| X4 | ORL|USPS|YaleB | -0.0019 | [-0.0080, 0.0038] | [-0.0080, 0.0038] | False |
| X5 | ORL|USPS|YaleB | -0.0008 | [-0.0013, 0.0000] | [-0.0013, 0.0000] | False |

Negative differences mean the prespecified extension scored lower than its matched SSC control on that contrast.
