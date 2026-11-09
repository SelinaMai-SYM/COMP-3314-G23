# E01 — edge recurrence on W

F is the original Equation (4) embedding. Draw T=10 isotropic Gaussian perturbations of F with relative scale 0.02 and seed 20260311. Let p_ij be the fraction of those union-kNN graphs that contain the undirected edge. Replace the shrinkage weight by W' = W ⊙ p^β with β=1, then run E8 (coefficient 2). Only W changes. β, T, and the noise scale are fixed and are not chosen by ACC.

With noise scale 0 the perturbed graphs repeat the original support, so W' = W and G matches original E8 within the documented tolerance.
