# N0: objective-specific primal-dual certification

This is a from-scratch application of Chambolle-Pock PDHG, not a new optimizer or clustering algorithm.

Each undirected positive edge is stored once. B has +1 and -1 on its oriented endpoints; c=2 gamma w reproduces Equation 8's ordered sum. Auditing E13 at gamma_nominal uses gamma_effective=gamma_nominal/2.

For radial Huber phi_delta and positive a, the primal is sum a_i phi_delta(||G_i-F_i||)+sum c_e||(BG)_e||. The conjugate of the shifted fidelity gives

D(q)=<B^T q,F>-(delta/2) sum ||(B^T q)_i||^2/a_i,

subject to ||q_e||<=c_e and ||(B^Tq)_i||<=a_i. The sign is consistent with the primal update G-tau B^Tq. For delta=0 the quadratic dual term vanishes. Squared fidelity has the same quadratic dual term but **no node balls**.

Any q is scaled by the minimum edge/node capacity ratio and a 1-1e-12 inward factor, then checked again. q=0 supplies a lower bound of zero. We retain the best feasible dual and an actual G supplying the best primal, including last/ergodic and valid component-consensus upper bounds. A small objective or agreement between solvers is not a lower bound. Significant P<D is an error.

Relative gap is (P-D)/max(1,|P|,|D|). Certification requires gap<=1e-5 and recorded violations<=1e-8. PDHG uses tau=sigma=.99/sqrt(2*dmax), theta=1, with checks every 50 iterations and at most 30000 per fit. No-edge/zero-gamma cases return F.

At F, define u_e=(BF)_e/||(BF)_e||, or zero for an exactly coincident edge, and b=B^T(2 w u). gamma0=1/max_i(||b_i||/a_i) gives a sufficient G=F region: q=gamma*2wu supplies P(F)=D(q). With coincident edges this need not be the maximal onset. Infinity is asserted only for the explicit zero-TV analytic case, not a finite numerical search reaching a large gamma.

Historical solver statuses are retained. New seeded representations are new artifacts; scalar metadata alone does not identify the old F/W arrays. The new audit therefore separates an audit of a persisted theory-cache certificate from fresh baseline reexecution.
