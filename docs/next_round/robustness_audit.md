# Robustness audit (2026-11-09)

The old `results/v3_theory/heldout_robustness.csv` is retained as historical evidence, not a valid full-SSC robustness evaluation.

1. `experiments/v3_theory/heldout_robustness.py` compared unperturbed saved SSC labels to K-means directly on perturbed F. It did not rerun the corresponding shrinkage method.
2. `perturb_images` clipped all normalized matrices to [0,1], while the USPS loader explicitly preserves [-1,1]. This removed legitimate negative pixels even for nominally mild perturbations.
3. Edge Jaccard is a graph statistic; partition ARI against the unperturbed result measures consistency, not agreement with true classes.

The corrected helper accepts an explicit domain and uses a brightness fraction of its full dynamic range. Zero perturbation is an identity. The new runner must recompute X -> A -> F -> W -> SSC -> K-means, preserving clean parameters and recording solver uncertainty. SC and SSC under a perturbation share that perturbation's actual F. An adaptive recalibration is a separate endpoint. Previously published values are not silently overwritten.
