# Edge-deletion evidence for spectral shrinkage

The preceding study found small conditional changes against movement-matched quadratic SSC: E1_v2 changed ACC/NMI by +0.179/−0.057 percentage points on seven qualified pairs; E5 changed them by +0.116/+0.070. E5 reduced triangle slack while retaining more within-label variation on six of seven comparable cohorts. The primary E6 constraint was inactive. Earlier E2/E3 mechanism gates failed. These observations motivate a discriminator for individual edges, rather than additional global constraints. They do not establish erroneous edges as the cause of every failure.

## Fixed geometry and evidence

H is the frozen n×K anchor; each positive undirected W0 edge appears once, lexicographically. B has entries +1 and −1; weights remain outside B. Let L=Bᵀdiag(w)B, S=‖H−mean(H)‖F, τ=1/median of positive weighted degrees, M=I+τL, and Z=M⁻¹H. The pilot Z is never a substitute for the fitted rounding matrix G.

For edge b and a=τw, set r=bᵀM⁻¹b and ℓ=ar. With A=M−abbᵀ≽I, t=bᵀA⁻¹b≤‖b‖²=2. Sherman–Morrison gives ℓ=at/(1+at), 0≤ℓ<1, and 1−ℓ=1/(1+at)≥1/(1+2a). Applying the same identity to H gives bᵀZ^(−e)=bᵀZ/(1−ℓ). Thus the evidence is s=‖bᵀZ‖²/(1−ℓ)². This is exact deletion of one pilot edge with τ fixed. It is not an unbiased risk estimate, statistical independence, or a probability that an edge is wrong.

Sparse LU and coordinate solves in batches of 32 retain the inverse diagonal and the two inverse entries needed for each edge. No full dense inverse is constructed. Linear-system residuals and retained-entry symmetry must be ≤10⁻⁹. Raw leverage is preserved; only negative roundoff within 10⁻¹² may be corrected. Material bound violations fail the evidence stage.

Controls use uncorrected pilot squared length, anchor squared length, leverage alone, and three fixed permutations (PCG64 400–402). All share the original support. Scores divided by their positive median are rounded to ten decimal places for ties. Weighted midranks u satisfy Σvu=½Σv: each pair of distinct tie groups contributes its product once, and each group's self-product contributes half. The identity holds with unequal tied masses.

## Three independent insertion points

All objectives have fidelity ½‖G−H‖². No candidate combines interventions. λ multiplies a single undirected edge sum; it is distinct from historical gamma.

**Graph:** w′=w(1−0.2u), ranks weighted by w. Total mass is 0.9Σw, each ratio is at least 0.8, support/components are unchanged and 0.8L≼L′≼L. A uniform rank gives 0.9W0: the exact control uses λ′=λQ/0.9 and the same QSSC solution. An exact rescaling is not an additional optimization result.

**Tube:** a0=‖BH‖, ranks weighted by wa0 on positive a0, η=⅛+¼u, a=ηa0. Zero-length edges receive η=¼. The penalty is λΣw max(‖BG‖−a,0), with Σwa=¼Σwa0. For ‖q_e‖≤λw_e,

D(q)=⟨BH,q⟩−½‖Bᵀq‖²−Σa‖q‖.

The dual step soft-thresholds by σa and then projects onto edge balls. The zero-penalty competitor mean(H)+⅛(H−mean(H)) has objective ½(7S/8)². Hence an ε-suboptimal feasible G has ‖G−H‖≤√((7S/8)²+2ε). Centering is contractive, so its dispersion is at least max(0,S−√((7S/8)²+2ε)); the exact floor is ⅛S. This is not a class-separation guarantee. Equal scores recover uniform η=¼; the old ¼ floor does not apply to selective tubes.

**Guard:** α=2u with ranks weighted by w, giving Σwα=Σw. With κ=‖BG‖+‖B(G−H)‖−‖BH‖, the penalty is λΣw(‖BG‖+ακ). It is two TV terms with capacities r1=λw(1+α), r2=λwα and constant C=λΣwα‖BH‖. The dual is

D(q,p)=⟨BH,q⟩−½‖Bᵀ(q+p)‖²−C,

with the two capacity constraints. The weighted vector constant is retained in both bounds. Equal scores give uniform α=1; α=0 gives QSSC. Coefficient mass is matched, rather than realized guard loss.

## Numerical meaning and limitations

Diagonal PDHG uses one incidence block for graph/tube and the stacked [B;B] bound for guards. Its diagonal row steps are 0.99/(number of blocks × unweighted incident degree), dual step 0.495. Isolates have primal step one. Cauchy–Schwarz bounds the squared preconditioned operator norm by 0.9801. Quadratic fidelity makes each fixed G problem strongly convex with a unique optimizer. The data-dependent full pipeline is not jointly convex.

Independent best feasible primal and dual states are retained. Both direct and stable gaps, capacities and movement uncertainty are recomputed from arrays. Relative gap ≤10⁻⁶ and capacity residual ≤10⁻⁸ are necessary; movement error must additionally be ≤0.005ρ. Matching uses |movement−ρ|+error≤0.01ρ. Negative gaps beyond recorded roundoff invalidate eligibility. Objective improvements do not imply clustering improvements.

Wrong dense neighborhoods can mutually support each other. A genuine sparse within-class bridge may receive high cavity evidence. Existing support cannot repair missing edges. Near-identical pilot and cavity ranks may yield no distinguishable intervention. These failure modes remain relevant even if every convex solve is certified.
