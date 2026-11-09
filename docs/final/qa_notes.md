# Q&A notes

**Why call a result closest if it is not faithful?** It is a retrospective display statistic selected against the paper ACC. Inputs, gamma, E13 and K-means choices can differ. It is useful for tracing numerical proximity, not for recovering the author protocol or proving superiority.

**Why not compare only gamma=1?** USPS has a much better historical gamma=1000 result. New methods face the predeclared search region, including that value. A label-assisted best-in-grid oracle is distinct from a no-label operating rule.

**E8 versus E13?** An undirected edge is counted twice by the paper's ordered sum. E13 at nominal gamma targets E8 at gamma/2. Different target values at the same nominal gamma are not solver error.

**Vanilla++ versus greedy++?** Vanilla samples one candidate at each seeding step. sklearn's greedy++ tests multiple local candidates. Same seed does not select the same initial indices on different representations. Both differ from random initialization.

**Why does a convex optimum not guarantee better clustering?** Convexity concerns the representation objective for fixed F/W. The graph may connect wrong classes and the objective contains no true labels; K-means is another nonconvex step. A lower objective need not improve ACC/NMI.

**Why is partial reproduction meaningful?** It tests executable mathematical claims and controls on available, explicitly identified data. Blocked datasets, an ambiguous baseline and unknown historical subsets are reported honestly; the course explicitly allows partial reproduction bonus assessment.

**Why use Oracle deletion?** It tests whether correcting known cross-class W edges changes outcomes. It is a label-assisted intervention and cannot become an unsupervised method. Random deletion and equal remaining edge mass test whether targeted correctness matters beyond less shrinkage.

**What if the wrong-edge gate fails?** Then the evidence does not justify promoting that mechanism to the main real-data method claim. Solver uncertainty and parameter limitations are separate from a negative mechanism result. We retain the derivation and synthetic checks rather than changing the success metric.

**Is capped fusion new?** No: PRclust already uses a truncated group penalty, and Shah-Koltun RCC weakens spurious relations. The course extension is an SSC-specific diagnosis/adaptation with fidelity controls, initialization checks and explicit failure conditions.

**What does the nonconvex certificate prove?** The inner active-edge problem is convex and receives a primal-dual bound. A stable active set is a local algorithm outcome, not a global certificate for the capped objective. Tiny state enumeration is global only for those tiny examples.

**Why can heat-only improve without SSC helping?** Changing upstream geometry can improve K-means before any shrinkage. Heat+SSC must beat the same heat representation without shrinkage to attribute extra benefit to SSC. Stability alone does not imply correctness.

**Why report NMI with ACC?** The paper's YaleB ACC improves but NMI falls. They detect different assignment structures. NMI must accompany the same selected configuration; it cannot be independently cherry-picked.

**What was wrong with the old robustness table?** It did not rerun shrinkage on perturbed inputs and clipped USPS to [0,1] instead of its native [-1,1]. ARI against an unperturbed partition and edge overlap do not by themselves measure classification accuracy.

**What is independent about the release?** A shallow single-branch checkout can import, run synthetic tests and rebuild scalar tables from committed inputs. Raw-image reruns require separately licensed data. Historical scalar provenance does not recover every old embedding array.

**How much evidence does a 50-seed interval provide?** It measures conditional K-means rounding variability on fixed F/G, not uncertainty over datasets or the data-generating process. Oracle parameter selection introduces additional bias. Perturbation seeds are separate experimental units.
