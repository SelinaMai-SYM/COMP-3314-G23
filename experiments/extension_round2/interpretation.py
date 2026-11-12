"""Concise evidence statements derived from the registered primary endpoints."""
import numpy as np
from .common import ORDER,METHODS


def write_evidence(output,points,macros,diagnostics,alignment):
    lookup={(p['benchmark'],p['method'],p['variant'],p['rho']):p for p in points}
    def row(b,m,rho=.05):return lookup[b,m,'default',rho]
    def data(b,m,rho=.05):return diagnostics.get(row(b,m,rho)['point_id'],{})
    def interval(values,percent=False):
        values=[v for v in values if v is not None and np.isfinite(v)]
        if not values:return 'NA'
        factor=100 if percent else 1
        return f'{min(values)*factor:.4g}–{max(values)*factor:.4g}'+('%' if percent else '')
    def paired(b,m):return bool(row(b,m)['qualified_matched_pair_candidate'] and row(b,'QSSC')['qualified_matched_pair_candidate'])
    lines=['# Mechanism evidence on the locked cohorts','','These are primary-point observations. A certified embedding, changed partition or geometric guarantee is not by itself an ACC/NMI improvement. The cohorts were selected retrospectively; all means are conditional on that fixed selection.','']
    lines+=['## E1_v2: movement and relative stopping','']
    d=[data(b,'E1_v2').get('relative_stopping',{}) for b in ORDER]
    old=[row(b,'old_E1_reference',None) for b in ORDER]
    lines.append(f"Among positive-anchor edges, the observed fraction of edge weight at/below the stopping distance ranges from {interval([v.get('observed_positive_anchor_weight_fraction') for v in d],True)}. Coincident edges and uncertainty bands are retained separately in diagnostics.json; this observed fraction is not an exact active-set certificate. The primary movement ranges from {interval([row(b,'E1_v2')['actual_movement'] for b in ORDER])}.")
    lines.append(f"Only {sum(bool(r['certified']) for r in old)}/8 original non-squared E1 reference attempts were certified. Their finite movements range from {interval([r['actual_movement'] for r in old])}; these outputs cannot establish stationary or optimal behavior of that older objective. Quadratic movement alone therefore does not validate the proposed failure explanation.")
    comparable=[b for b in ORDER if row(b,'E1_v2')['actual_movement'] is not None and row(b,'old_E1_reference',None)['actual_movement'] is not None]
    increased=[b for b in comparable if row(b,'E1_v2')['actual_movement']>row(b,'old_E1_reference',None)['actual_movement']]
    lines.append(f"At these locked operating points, the new finite output moves farther than the old E1 attempt on {len(increased)}/{len(comparable)} cohorts ({', '.join(increased) or 'none'}). These references are not movement-matched; this comparison describes the operating points and does not isolate a fidelity effect.")
    lines+=['','## E4: graph intervention and correspondence control','']
    eligible=[b for b in ORDER if row(b,'E4')['graph_eligible'] and row(b,'E4')['point_id']]
    ambiguous=sum(bool(data(b,'E4').get('auxiliary_band',{}).get('cutoff_ambiguity')) for b in ORDER)
    exchange=[.25*data(b,'E4').get('graph',{}).get('exchange_mass',float('nan')) for b in eligible]
    lines.append(f"The real-band graph passes the independent numerical eligibility checks on {len(eligible)}/8 cohorts. Applied positive exchange divided by original edge mass ranges from {interval(exchange,True)} among these graphs. Auxiliary cutoff ambiguity is flagged on {ambiguous}/8 cohorts; a frozen finite band is not necessarily a uniquely identified spectral feature.")
    controls=[r for r in alignment if r['permutation_seeds']=='400;401;402' and r['qualified']]
    if controls:lines.append(f"The real-band versus mean-of-three-permutations comparison has {len(controls)}/8 qualified pairs, with available-case ΔACC/ΔNMI {np.mean([r['ACC_delta_pp'] for r in controls]):+.3f}/{np.mean([r['NMI_delta_pp'] for r in controls]):+.3f} percentage points. All three individual contrasts and exchange magnitudes are retained; no permutation is selected by its score.")
    else:lines.append('No complete qualified real-band/three-permutation comparison is available in this release. A correspondence advantage is not established.')
    checks=[data(b,'E4').get('graph_independent_checks',{}) for b in eligible]
    lines.append(f"Post-fit b-distance cross-class edge AUROC ranges from {interval([v.get('b_cross_label_edge_AUROC') for v in checks])}; the added edge-mass fraction crossing labels ranges from {interval([v.get('added_between_label_mass_fraction') for v in checks],True)}. These are descriptive label audits, not inputs to graph construction or parameter selection.")
    lines+=['','## E5: directional slack versus shape change','']
    cohorts=[b for b in ORDER if paired(b,'E5')];slack=[]
    for b in cohorts:
        guard=data(b,'E5').get('direction_guard',{})
        if guard.get('weighted_triangle_slack_over_TV_H') is not None and guard.get('QSSC_weighted_triangle_slack_over_TV_H') is not None:slack.append(guard['weighted_triangle_slack_over_TV_H']<guard['QSSC_weighted_triangle_slack_over_TV_H'])
    changed=sum(data(b,'E5').get('partition_changed_seeds_vs_QSSC',0)>0 for b in cohorts)
    lines.append(f"Among {len(cohorts)}/8 qualified primary QSSC pairs, E5 lowers weighted triangle slack on {sum(slack)}/{len(slack)}. Residual from a global scale/translation of the same-target QSSC embedding ranges from {interval([data(b,'E5').get('residual_from_uniform_affine_transform_of_QSSC_relative') for b in cohorts])} relative to S_H. At least one rounding partition changes on {changed}/{len(cohorts)} cohorts. Slack reduction and these nonuniform changes still require joint ACC/NMI evidence; dataset regressions remain in the primary table.")
    lines+=['','## E6: was a threatened direction protected?','']
    guards=[data(b,'E6').get('directional_floor',{}) for b in ORDER]
    sufficient=sum(bool(g.get('sufficient_inactivity_nominal_target')) for g in guards);proved=sum(bool(g.get('QSSC_optimal_retained_projection_guard_feasible_from_gap')) for g in guards)
    lines.append(f"The nominal movement-ball bound proves sufficient inactivity on {sufficient}/8 cohorts. The stronger post-fit QSSC gap bound establishes feasibility of its optimal retained projection for the guard on {proved}/8 cohorts. E6 PSD-dual norms range from {interval([g.get('dual_PSD_norm') for g in guards])} at the primary point.")
    lines.append('When the same-lambda QSSC optimum already satisfies the guard, separately rounded score differences cannot be credited to protection of a violated direction. The recorded lambdas, movement differences and embedding residuals expose finite calibration/solver effects. Individual weakest-vector label associations are basis-dependent at repeated singular values and do not alone prove retention of noise.')
    lines+=['','| Fixed E6 target | Qualified/matched outputs | Whitened minimum minus guard | PSD-dual norm |','|---|---:|---:|---:|']
    for rho in [.02,.05,.1,.2]:
        bs=[b for b in ORDER if row(b,'E6',rho)['qualified_matched_pair_candidate']];gs=[data(b,'E6',rho).get('directional_floor',{}) for b in bs]
        lines.append(f"| {rho:.2f} | {len(bs)}/8 | {interval([g['whitened_min_eigenvalue']-.5 for g in gs if 'whitened_min_eigenvalue' in g])} | {interval([g.get('dual_PSD_norm') for g in gs])} |")
    lines+=['','## Reachability and uncertainty','']
    bounded=[]
    for p in points:
        if p['method'] in METHODS and p['variant']=='default' and p['point_id'] and diagnostics.get(p['point_id'],{}).get('target_lower_tolerance_exceeds_analytic_bound'):bounded.append(f"{p['benchmark']}/{p['method']}/{p['rho']}")
    lines.append('For a componentwise zero-penalty candidate, strong convexity bounds the exact optimizer movement by its distance to H. The requested lower tolerance exceeds this analytical bound at: '+(', '.join(bounded) if bounded else 'none recorded')+'. These post-fit bounds explain reachability without changing targets or adding fits; a finite SEARCH_LIMIT alone is not such a proof.')
    lines.append('Only complete qualified paired coverage supports an eight-cohort macro. Rounding-seed intervals are conditional initialization variability, and not independent-data significance or generalization evidence.')
    (output/'mechanism_evidence.md').write_text('\n'.join(lines)+'\n')
    summary=output/'summary.md';text=summary.read_text();text=text.replace('## Mechanism evidence and limits','## Mechanism evidence and limits\n\n[Observed activation, correspondence controls and attribution](mechanism_evidence.md) give the data-dependent interpretation.')
    summary.write_text(text)
    note=output/'integration_note.md';content=note.read_text();e5=next(r for r in macros if r['method']=='E5')
    if e5['qualified_denominator'] and e5['available_case_ACC_pp']>0 and e5['available_case_NMI_pp']>=0 and sum(slack)>0:
        content+='\nUse E5 as one compact exploratory mechanism example: report its available-case denominator, small/mixed primary effects and dataset regressions beside the slack result. This is not a completed eight-benchmark performance claim. E1_v2 belongs with the stopping-bound/tradeoff evidence; E4 needs its permutation and failed-QP qualifications; E6 belongs with the inactive-guard/null attribution unless its separately labelled path demonstrates activation. Keep the complete primary comparison visible.\n'
    else:content+='\nA short negative/null-results account is preferable to promoting a new accuracy-improving method. Keep all primary methods visible, and use the mechanism figures to distinguish inactivity, numerical limits and actual adverse effects.\n'
    note.write_text(content)
