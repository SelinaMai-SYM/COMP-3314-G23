# Diagnosis: mixed limitations, no single confirmed main cause

## Solver quality

The fixed-F/W objective is convex; our feasible lower bounds and returned G upper bounds distinguish optimization from K-means quality. Cold PDHG is replaced only by an explicitly recorded objective-accepted warm primal amendment, preserving cold records. Important USPS points remain uncertified after the declared iteration limits. Historical array identity is unavailable for baseline outputs, so fresh seeded results are not paired historical reoptimizations.

A separate same-new-F/W IRLS300 comparison supplies the valid paired optimization check. Returned IRLS points can be bounded by the corresponding feasible PDHG dual: ORL effective gamma500 gap 2.58e-7, cropped YaleB gamma1 gap 4.55e-6, and DengCai gamma.001 gap 1.23e-6. Their ACC differs little from cold PDHG (ORL 76.44 vs 76.34; cropped YaleB 21.548 vs 21.504; DengCai 43.583 vs 43.583). JAFFE gamma1 remains at gap 3.03e-5. USPS gamma1000 fails CG and gamma1 reaches the recorded audit timeout. Tight objective bounds neither recover missing old arrays nor guarantee identical rounding; nonuniqueness/near-optimal geometry can also matter.

## Parameter capability and selection

The five-point gamma curves show strong sensitivity in some cases. The strong historical USPS gamma1000 result (ACC79.918/NMI85.609) remains an observed capability reference, despite unknown old F/W identity and incomplete mathematical certification. Our new unresolved USPS curve cannot overturn it. We therefore cannot conclude that original SSC lacks a good objective-level solution throughout the intended parameter range.

The no-label operating point is fixed gamma1. No new automatic parameter selector is implemented or validated, as permitted by the approved scope. Oracle best values only describe the measured grid. Full 15-configuration capability fairness is not claimed because the real-data capped method was not promoted.

## Incorrect fusion

All 160 B interventions are completed. The locked gate selects the best certified original SSC gamma in the original five-point grid. It supports 0/4 primary datasets, fewer than the required two. Some large-gamma interventions show substantial Oracle gains, but these are conditional label-assisted findings; they do not justify changing the locked gate or replacing matched weakening controls with SC alone. Static filtering can remove useful same-class support and split classes, so both merge/split rates and graph fragments are retained.

This gate is deliberately local to the selected original operating point. The observed no-movement comparisons were local to the recorded graphs. Analytic G=F on the original graph does not imply G=F after deletion: removing edges can destroy cancellation of incident forces. The eight-cycle counterexample and corrected connectivity definitions are recorded in `../submission_refresh/numerical_repairs.md`. A separately valid sufficient bound is 2*gamma*max_i sum_j w_ij <= 1; deletion preserves this bound when it held initially. The gate can therefore miss gains from correcting W and changing gamma together; high-gamma Oracle results are retained as a separate capability diagnostic. A failed gate is not a complete falsification of wrong-edge effects or selective shrinkage. For cropped YaleB, W length AUROC .380 additionally contradicts the premise that long edges primarily identify wrong connections.

## Upstream geometry and candidate adaptations

The N2 geometry pilot motivates primary hard-dimension/heat/W-only tests. Its label results concern the locked projected implementation, not a proof that exact heat kernels cannot help. Restricted candidate kNN approximation recall can be low even when median pair-distance error is modest. Stability, dimension, projection quality and class information must be distinguished; no causal superiority claim is supported by stability alone.

The synthetic 2-by-2 supports a narrow capped damage-avoidance mechanism with bridge edges, but SC, static deletion and squared fidelity already suffice. Capping is not necessary there and can worsen anchor correction. Huber activation/MSE results also fail to show ACC/NMI gain. Neither candidate is promoted by moving the success criterion after observing outcomes.

Overall classification: **mixed solver/parameter/upstream limitations, conditional wrong-edge effects, and insufficient evidence for the main selective-fusion contribution**. The four-benchmark +2pp target is not established; this negative result is part of the deliverable.
