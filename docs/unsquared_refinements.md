# Unsquared-fidelity refinements

The fixed question is whether three separate adaptations of Spectral Shrunk
Clustering improve ACC and NMI for a specified reason. Mathematical correctness,
mechanism evidence and benchmark effects are separate claims. The complete
machine-readable design is `configs/extension_verification/protocol.yaml`;
its frozen hash and the exact inputs accompany every new configuration.

## Inputs and comparison panels

The eight fixed reference candidates are AR_first7, JAFFE, ORL_att92,
UMIST_LZUFE574_exact_dedup564, BinAlpha_random_seed000, MSRA25_EBSA_16x16,
YaleB_cropped2414_Y0 and full USPS. Source hashes, original IDs, order, dimensions
and class counts are locked before scoring. All retain unverified historical
identity; native-16 MSRA is an adapted proxy, AR is a source-order hypothesis,
and UMIST retains 10,304 features.

A0 is the input affinity, F0 its spectral representation, and W0 the graph built
from F0. U is rowunit(F0). The original panel clusters G directly for SC(F0),
ordinary SSC and relative stopping distances. The angular panel uses anchor U
and the SAME W0 for every arm, and row-normalizes every G before rounding.
Exact zero rows remain zero under normalization. Tangent displacement is frozen
at zero on zero anchors. Optimized G and actual rounding Q are both retained.

## Fixed objectives

With one positive undirected edge stored once and c=2 gamma w, ordinary SSC uses
unsquared fidelity plus the weighted norms of BG. Each refinement changes one
mechanism and is evaluated independently.

**E1: relative stopping distances.** Replace each edge norm by
max(norm(BG)-eta norm(BH),0), with eta=.25. An edge has no own attractive
force inside its frozen tolerance; this is not repulsion or a minimum-distance
constraint. A minimizer has global geometric-median dispersion D(G) at least
eta D(H). A computed point subtracts its absolute primal-dual gap from this
bound. The activation threshold at H is unchanged for eta<1. Interpolation and
uniform origin-scaling controls distinguish this property from added clustering
benefit. Eta=.5 is a development-only sensitivity.

**E2: fixed tangent constraints.** Minimize ordinary SSC on U+Delta subject to
u_i^T Delta_i=0 and norm(Delta_i)<=tan(15 degrees). The planes stay fixed.
The dual includes the radius support cost rather than ordinary node-ball
constraints. An isotropic control has radius sin(15 degrees), not the same
numerical radius. A 30-degree sensitivity is confined to development inputs.

**E3: frozen relative neighbors.** Construct at most one triplet per anchor
using two centered, normalized feature views and immutable-ID tie breaks. All
three roles must belong to the common valid pool. Verified image geometry uses
checkerboards; otherwise PCG64(20261111) freezes a balanced coordinate split.
Add unit-gradient affine hinges with mu=2 against frozen U references. Their
combined operator changes the solver step bound and node capacities. At gamma
zero, this is a meaningful triplet-only correction, not a shortcut to SC.
Mu=.5 is a development-only sensitivity. Seeds 400–402 give fixed matched random
hinges with the same anchors, initial hinges and unit gradient scale.

## Operating points and gates

The common primary gamma is twice the inverse maximum node force at H, using
zero edge subgradients on exactly coincident anchors. M=0 has a finite gamma-one
fallback and no reference-scaled probes. Coincident edges permit only a
sufficient anchor-optimality bound. Both primary SSC/E1 outputs must be certified
inactive to activate their additional 8/32-reference probes.

ORL followed by YaleB are development inputs. They are not unseen data. E1 has
no performance gate and is evaluated on all eight in both panels. E2 selects
one certified active ordinary-SSC output in fixed 2/8/32-reference order without
labels. Promotion requires at least 10% inward energy, one degree RMS angular
change, a positive adjusted lower ACC bound and nonnegative mean NMI change on
that same output. E3 requires max(20,ceil(.05n)) triplets, at least 60% correct
relations and at most 10% reversed relations. Each gate records both development
outcomes; either pass enables all-eight evaluation. Fitting is label-free;
these promotion decisions use development labels explicitly.

## Numerical and statistical qualification

Independent small convex references precede benchmark fitting. Certification
requires relative gap <=1e-5 and applicable feasibility/capacity violations
<=1e-8 for the exact saved G and objective. Negative gaps are retained as an
inconsistency. Checkpoints permit only the declared cumulative iteration/CPU
ceilings. Uncertified finite outputs can be exploratory but are not optima.

Greedy K-means++, one Lloyd start and seeds 0–49 supply one complete endpoint
on a fixed Q. ACC and geometric NMI share the configuration/trials; mean and
sample SD use all fifty. The secondary native endpoint selects one assignment
by SSE and then seed, with no across-run SD. Paired bootstrap uses 10,000
resamples and seed 424242. Its intervals concern conditional rounding variation.
The two E2 gate contrasts use the predeclared .025 lower quantile.

Movement matches use only declared certified points, 5% relative tolerance and
absolute floors 1e-6 (normalized L2,1) or .1 degree (RMS angle). No extra search
or monotonicity assumption is permitted. Full macros require all eight qualified
paired rows; partial summaries state their denominator and excluded reasons.
New work shares one 36-core-hour ledger, at most two single-thread workers and
an 8 GiB aggregate RSS target, with two core-hours reserved for final delivery.
