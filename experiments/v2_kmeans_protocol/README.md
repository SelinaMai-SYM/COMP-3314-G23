# K-means rounding protocols

This package supplies the common Lloyd, vanilla K-means++ and scikit-learn greedy K-means++ utilities used by the current experiments. Each protocol uses one initialization per declared external seed. Matching SC and SSC comparisons cluster the same initial representation F and its fixed shrinkage output G.

Labels are used by the evaluator after clustering for Hungarian ACC and geometric-normalized NMI. Native minimum-inertia selection is defined within one fixed representation; inertia is not compared between different representations or learned LDA subspaces. Mean/sample-SD and a single native-best assignment remain separate statistical endpoints.

Use the supported end-to-end commands in the [reproducibility guide](../../docs/reproducibility.md). Dataset lookup follows the shared independent-data-root resolver. Stored historical scalar trials remain separately identified in the published results.
