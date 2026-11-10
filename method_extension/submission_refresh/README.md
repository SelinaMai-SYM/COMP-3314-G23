# Elastic-net affinity for the SSC graph adaptation

[`ensc.py`](ensc.py) provides an attributed, compatible implementation of
the elastic-net coefficient and affinity conventions of
[You et al., CVPR 2016](https://openaccess.thecvf.com/content_cvpr_2016/html/You_Oracle_Based_Active_CVPR_2016_paper.html).
It follows [source revision 55e330e38415951f140e74739c869306acdb7a98](https://github.com/ChongYou/subspace-clustering/tree/55e330e38415951f140e74739c869306acdb7a98).
The original [MIT notice](third_party/ensc/LICENSE), including Chong
You's copyright, is retained.

## Coefficients and affinity

For each unit-L2 input row \(x_i\), exclude its self dictionary entry and
minimize

\[
\tfrac12\|x_i-c_iD_i\|_2^2+
\alpha_i\left(\tau\|c_i\|_1+
\tfrac{1-\tau}{2}\|c_i\|_2^2\right),\qquad
\alpha_i=\frac{\max_{j\ne i}|x_j^Tx_i|}{\gamma_{\rm source}\tau}.
\]

`elastic_net_code` uses a true sklearn elastic-net backend. Its
`alpha=alpha_i/d` compensates for sklearn's squared-error normalization
by feature count \(d\). Primary source settings are
`source_gamma=50` and `tau=0.95`; `tau=1` is a sparse-only control.
The source active-support loop uses initial support size 100 and at most
40 updates, with a disclosed minimum-one growth repair for small supports.

`coefficients_to_affinity` retains at most 50 largest-magnitude
coefficients per row, row-L2-normalizes to \(C_n\), then forms
\(S=(|C_n|+|C_n^T|)/2\) with zero diagonal. Pre-truncation coefficients,
zero input/code rows and KKT diagnostics remain distinct outputs.
Zero affinity is a degenerate result, not a request for a fallback graph.

## Scope and qualification

The implementation is a compatible port, not an assertion that the
source SPAMS installation was executed unchanged. Coefficient KKT
residuals concern the untruncated coefficient target; a screening or
source-objective stop does not itself satisfy KKT conditions.
Truncation and normalization define a later graph construction.

The SSC adaptation mass-matches this affinity to \(W_0\) and keeps
anchor \(F_0\). Native EnSC spectral clustering uses its own eigenspace
and is a separate control. A downstream SSC primal–dual certificate
does not certify upstream coefficient accuracy or final labels.

All four benchmark comparisons are reported with their numerical
qualifications. Required uncertified controls keep the formal macro
targets unavailable. No superiority claim follows from this helper's
availability. See [methods](../../docs/methods.md),
[theory](../../docs/theory.md), [results](../../docs/results.md)
and [reproducibility](../../docs/reproducibility.md).
