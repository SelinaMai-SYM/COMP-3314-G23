"""Post-fit mechanism checks; label-dependent quantities never feed fitting."""
import numpy as np
from scipy import linalg
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import adjusted_rand_score
from method_extension.extension_round2.models import QuadraticProblem,norms,center,sym
from .common import get_arrays

def graph_certificate(store,benchmark,variant):
    import json
    from scipy import sparse
    row=json.loads((store.root/'graphs'/f'{benchmark}--{variant}.json').read_text());state=get_arrays(store,store.get(row['state'])) if row.get('state') else None
    if not state or 'w0' not in state:return {'eligible':bool(row['diagnostics']['eligible']),'status':row['diagnostics']['status']}
    w0=state['w0'];t=state['t'];a=state['a'];b=state['b'];r=state['r'];v=state['v'];theta=state['theta'];edges=state['edges'];W=store.get(row['W']);n=W.shape[0]
    M=sparse.csc_matrix((np.ones(2*len(edges)),(edges.T.ravel(),np.tile(np.arange(len(edges)),2))),shape=(n,len(edges)));d=M@w0;C=1.05*float(a@w0);c=row['diagnostics']['beta']*b+M.T@v+theta*a;s=np.maximum(w0-r*c,0.);active=w0-r*c>0
    primal=.5*float(np.sum((t-w0)**2/r))+row['diagnostics']['beta']*float(b@t);dual=float(-v@d-theta*C+np.where(active,c*w0-.5*r*c*c,w0*w0/(2*r)).sum());gap=primal-dual;scale=max(1.,abs(primal),abs(dual));degree=float(np.max(np.abs(M@t-d),initial=0)/max(1.,float(d.max(initial=0))));budget=max(0.,float(a@t-C))/max(1.,C)
    weights=.75*w0+.25*t;expected=sparse.csr_matrix((np.r_[weights,weights],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=W.shape);delta=W-expected;mix_error=float(np.max(np.abs(delta.data),initial=0))
    eligible=bool(row['diagnostics']['eligible'] and degree<=1e-8 and budget<=1e-8 and float(t.min(initial=0))>=0 and theta>=0 and -1e-10*scale<=gap<=1e-6*scale and mix_error<=1e-12)
    return {'eligible':eligible,'primal':primal,'dual':dual,'signed_gap':gap,'relative_gap':max(0.,gap)/scale,'degree_residual':degree,'budget_residual':budget,'mixture_max_error':mix_error,'applied_positive_exchange_over_old_mass':float(.25*np.maximum(t-w0,0).sum()/w0.sum()) if w0.sum() else 0.,'status':'SAVED_ARRAYS_RECOMPUTED','qualification':'Numerical tolerances, not an interval-arithmetic certificate'}

def certificate_audit(endpoint,result,entry,store):
    """Recompute bounds directly from saved arrays, without solver iterates."""
    H=store.get(entry['objects']['H']);W=store.get(entry['objects']['W0']);method=endpoint['method'];G=result['G']
    if method=='SC':return {'qualified':True,'status':'ANCHOR_REFERENCE'}
    if method in ['historical','SSC_reference','old_E1_reference']:
        from method_extension.extension_verification.convex import Problem
        P=Problem(H,W,entry['gamma_effective'],kind='relative' if method=='old_E1_reference' else 'ssc',eta=.25);D=P.dual(result['q'],result.get('p'),repair=False);primal=P.primal(G);gap=primal-D['dual'];relative=gap/max(1.,abs(primal),abs(D['dual']));capacity=max([v for k,v in D.items() if k.endswith('violation')],default=0)
        return {'qualified':bool(0<=relative<=1e-5 and capacity<=1e-8),'status':'RECOMPUTED','primal':primal,'dual':D['dual'],'stable_gap':gap,'relative_gap':relative,'capacity_residual':capacity,'primal_difference_from_saved':primal-result['primal'],'dual_difference_from_saved':D['dual']-result['dual']}
    graph_check=None
    if method=='E4':
        import json
        graph=json.loads((store.root/'graphs'/f"{endpoint['benchmark']}--{endpoint['variant']}.json").read_text());W=store.get(graph['W']);graph_check=graph_certificate(store,endpoint['benchmark'],endpoint['variant'])
    P=QuadraticProblem(H,W,result['lam'],method,**endpoint['parameters']);q=result['q'];p=result.get('p',np.zeros_like(q));Z=result['Zf'] if method=='E6' else G;d=P.B@Z;res=Z-P.anchor
    capacity=float(np.max(np.maximum(norms(q)-P.r1,0)/np.maximum(1.,P.r1),initial=0));fidelity=.5*float(np.sum(res*res));feasible=True;psd_res=0.;reconstruction=0.
    if method=='E5':
        change=d-P.edge_H;constant=P.lam*P.alpha*P.tv_H;A=P.B.T@(q+p);primal=fidelity+float(P.r1@norms(d)+P.r2@norms(change))-constant;dual=float(np.sum(P.edge_H*q))-.5*float(np.sum(A*A))-constant
        stable=.5*float(np.sum((res+A)**2))+float(P.r1@norms(d)-np.sum(q*d)+P.r2@norms(change)-np.sum(p*change));capacity=max(capacity,float(np.max(np.maximum(norms(p)-P.r2,0)/np.maximum(1.,P.r2),initial=0)))
    elif method=='E6':
        S=result['S'];A=center(P.B.T@q-P.Y@S);primal=fidelity+float(P.r1@norms(d));dual=float(np.sum(P.Y*A))-.5*float(np.sum(A*A))+P.eta_dir*float(np.sum(P.sigma2*S));stable=.5*float(np.sum((res+A)**2))+float(P.r1@norms(d)-np.sum(q*d))+float(np.sum(S*(sym(P.Y.T@Z)-P.eta_dir*P.sigma2)))
        minimum=float(linalg.eigvalsh(P.whitened(Z))[0]) if len(P.s) else 1.;psd_res=max(0.,-float(linalg.eigvalsh(sym(S))[0]))/max(1.,float(linalg.norm(S))) if len(S) else 0.;reconstruction=float(np.max(np.abs(P.reconstruct(Z)-G),initial=0));feasible=minimum>=P.eta_dir-1e-8 and float(np.max(np.abs(Z.mean(axis=0)),initial=0))<=1e-8 and psd_res<=1e-8 and P.rank_info['whitened_roundoff_indicator']<=1e-8 and reconstruction<=1e-9
    else:
        A=P.B.T@q;penalty=P.r1*np.maximum(norms(d)-P.a,0);primal=fidelity+float(penalty.sum());dual=float(np.sum(H*A))-.5*float(np.sum(A*A))-float(P.a@norms(q));stable=.5*float(np.sum((res+A)**2))+float(np.sum(penalty-np.sum(q*d,axis=1)+P.a*norms(q)))
    scale=max(1.,abs(primal),abs(dual));tol=1e-12*scale;relative=max(0.,primal-dual)/scale;error=np.sqrt(2*max(0.,stable))/P.scale if P.scale else 0.;rho=endpoint['rho'];movement=float(linalg.norm(G-H)/P.scale) if P.scale else 0.;consistent=abs(stable-(primal-dual))<=1e-9*scale
    valid=feasible and capacity<=1e-8 and stable>=-tol and consistent;certified=valid and relative<=1e-6 and max(0.,stable)/scale<=1e-6 and error<=.02*rho;matched=certified and abs(movement-rho)+error<=.05*rho
    return {'qualified':bool(certified),'matched':bool(matched),'status':'RECOMPUTED','primal':primal,'dual':dual,'stable_gap':stable,'signed_subtracted_gap':primal-dual,'relative_gap':relative,'movement_error':float(error),'actual_movement':movement,'capacity_residual':capacity,'PSD_residual':psd_res,'gap_consistent':bool(consistent),'reconstruction_max_error':reconstruction,'stationarity_residual':float(linalg.norm(res+A)),'primal_difference_from_saved':primal-result['primal'],'dual_difference_from_saved':dual-result['dual'],'graph_certificate':graph_check}


def mechanism(endpoint,result,entry,store,qssc=None,sc_evaluation=None,evaluation=None,qssc_evaluation=None):
    H=store.get(entry['objects']['H']);W=store.get(entry['objects']['W0']);G=result['G'];dH=H.mean(axis=0);hc=center(H);gc=center(G);S=float(linalg.norm(hc));dot=float(np.sum(hc*hc));scale=max(0.,float(np.sum(hc*gc))/dot) if dot>0 else 1.;residual=float(linalg.norm(gc-scale*hc))/S if S>0 else 0.
    out={'movement_from_original_H':float(linalg.norm(G-H)/S) if S else 0.,'total_centered_Frobenius_dispersion':float(linalg.norm(gc)),'dispersion_ratio':float(linalg.norm(gc)/S) if S else None,'best_nonnegative_uniform_scale':scale,'translation':(G.mean(axis=0)-scale*dH).tolist(),'global_affine_residual_relative':residual}
    if qssc is not None:
        qc=center(qssc['G']);qnorm=float(np.sum(qc*qc));qs=max(0.,float(np.sum(qc*gc))/qnorm) if qnorm else 1.;out['distance_from_same_target_QSSC_relative']=float(linalg.norm(G-qssc['G'])/S) if S else 0.;out['residual_from_uniform_affine_transform_of_QSSC_relative']=float(linalg.norm(gc-qs*qc)/S) if S else 0.;out['QSSC_lambda']=qssc['lam'];out['QSSC_actual_movement']=qssc['movement'];out['movement_difference_from_QSSC']=out['movement_from_original_H']-qssc['movement']
    if evaluation and sc_evaluation:
        pred=store.get(evaluation['predictions']);base=store.get(sc_evaluation['predictions']);agreement=[float(adjusted_rand_score(x,y)) for x,y in zip(base,pred)];out.update(partition_ARI_with_SC=agreement,partition_changed_seeds=int(sum(x<1-1e-12 for x in agreement)))
    if evaluation and qssc_evaluation:
        pred=store.get(evaluation['predictions']);base=store.get(qssc_evaluation['predictions']);agreement=[float(adjusted_rand_score(x,y)) for x,y in zip(base,pred)];out.update(partition_ARI_with_same_target_QSSC=agreement,partition_changed_seeds_vs_QSSC=int(sum(x<1-1e-12 for x in agreement)))
    if endpoint['method'] not in ['QSSC','E1_v2','E4','E5','E6']:return out
    if endpoint['method']=='E4':
        graph=store.root/'graphs'/f"{endpoint['benchmark']}--{endpoint['variant']}.json"
        if graph.exists():
            import json
            row=json.loads(graph.read_text());W=store.get(row['W']);out['graph']=row['diagnostics']
            auxiliary=store.root/'auxiliary'/f"{endpoint['benchmark']}.json"
            if auxiliary.exists():out['auxiliary_band']=json.loads(auxiliary.read_text())['diagnostics']
            if row.get('state'):
                state=get_arrays(store,store.get(row['state']))
                if 'w0' not in state:return out
                w0=state['w0'];a=state['a'];b=state['b'];r=state['r'];t=state['t'];theta=state['theta'];v=state['v'];edges=state['edges'];M=__import__('scipy').sparse.csc_matrix((np.ones(2*len(edges)),(edges.T.ravel(),np.tile(np.arange(len(edges)),2))),shape=(len(H),len(edges)))
                c=row['diagnostics']['beta']*b+M.T@v+theta*a;s=np.maximum(w0-r*c,0.);mass=float(w0.sum());difference=.25*(t-w0);truth=store.get(entry['objects']['labels']);same=truth[edges[:,0]]==truth[edges[:,1]]
                out['graph_independent_checks']={'nonnegative_minimizer_KKT_residual':float(np.max(np.abs(t-s),initial=0)/max(1.,float(np.max(w0,initial=0)))),'budget_complementarity':float(abs(theta*(a@t-1.05*a@w0))),'positive_mass_within_labels':float(np.maximum(difference,0)[same].sum()),'positive_mass_between_labels':float(np.maximum(difference,0)[~same].sum()),'removed_mass_within_labels':float(np.maximum(-difference,0)[same].sum()),'removed_mass_between_labels':float(np.maximum(-difference,0)[~same].sum()),'attempted_candidate_exchange_mass':float(np.maximum(state['raw_t']-w0,0).sum()/mass) if mass else None,'labels_used_only_post_fit':True}
                from sklearn.metrics import roc_auc_score
                out['graph_independent_checks'].update(within_label_b_median=float(np.median(b[same])) if same.any() else None,between_label_b_median=float(np.median(b[~same])) if (~same).any() else None,b_cross_label_edge_AUROC=float(roc_auc_score(~same,b)) if same.any() and (~same).any() else None,a_cross_label_edge_AUROC=float(roc_auc_score(~same,a)) if same.any() and (~same).any() else None)
                added=np.maximum(difference,0);removed=np.maximum(-difference,0);out['graph_independent_checks'].update(original_between_label_mass_fraction=float(w0[~same].sum()/mass) if mass else None,new_between_label_mass_fraction=float((.75*w0+.25*t)[~same].sum()/mass) if mass else None,added_between_label_mass_fraction=float(added[~same].sum()/added.sum()) if added.sum()>0 else None,removed_between_label_mass_fraction=float(removed[~same].sum()/removed.sum()) if removed.sum()>0 else None)
    problem=QuadraticProblem(H,W,result['lam'],endpoint['method'],**endpoint['parameters']);edges=problem.B@G;anchor=problem.B@H;length=norms(edges);initial=norms(anchor);mass=float(problem.w.sum());tv=float(problem.w@initial)
    if endpoint['method']!='E6' and S:
        _,components=connected_components(W,directed=False);means=np.zeros((int(components.max())+1,H.shape[1]));np.add.at(means,components,H);counts=np.bincount(components);means/=counts[:,None];consensus=means[components];bound=float(linalg.norm(H-consensus)/S)
        if endpoint['method']=='E1_v2':bound*=1-endpoint['parameters'].get('eta',.25)
        out['componentwise_zero_penalty_movement_upper_bound']=bound
        out['target_lower_tolerance_exceeds_analytic_bound']=bool(.95*endpoint['rho']>bound)
        out['reachability_bound_qualification']='Exact-model bound from a componentwise zero-penalty candidate; floating evaluation, not an additional fit or a label-based target change'
    if endpoint['method']=='E1_v2':
        eta=endpoint['parameters'].get('eta',.25);threshold=eta*initial;positive=initial>0;epsilon=max(0.,result['stable_gap']);edge_error=2*np.sqrt(epsilon);inside=length<=threshold
        directions=np.divide(anchor,initial[:,None],out=np.zeros_like(anchor),where=positive[:,None]);force=result['lam']*(problem.B.T@(problem.w[:,None]*directions));old_node_max=float(np.max(norms(force),initial=0))
        out['relative_stopping']={'observed_fraction_at_or_below':float(inside.mean()) if len(inside) else 0.,'observed_weight_mass_at_or_below':float(problem.w@inside/mass) if mass else 0.,'certain_inside_fraction_given_gap':float(np.mean(length+edge_error<threshold)) if len(length) else 0.,'possible_inside_fraction_given_gap':float(np.mean(length-edge_error<=threshold)) if len(length) else 0.,'edge_error_bound':float(edge_error),'coincident_anchor_edges':int(sum(~positive)),'positive_anchor_ratio_quantiles':np.quantile(length[positive]/initial[positive],[0,.1,.5,.9,1]).tolist() if positive.any() else None,'dispersion_lower_bound_with_gap':S-np.sqrt((1-eta)**2*S*S+2*epsilon),'exact_optimizer_floor':eta*S,'old_unsquared_H_sufficient_certificate_at_this_lambda':old_node_max<=1.,'old_unsquared_H_node_capacity':old_node_max,'coincident_case_qualification':'This explicit zero subgradient is sufficient, not a necessary criterion at coincident edges'}
        positive_mass=float(problem.w[positive].sum());out['relative_stopping'].update(observed_positive_anchor_fraction=float(inside[positive].mean()) if positive.any() else None,observed_positive_anchor_weight_fraction=float(problem.w[positive]@inside[positive]/positive_mass) if positive_mass else None,certain_inside_positive_anchor_fraction=float(np.mean((length+edge_error<threshold)[positive])) if positive.any() else None,possible_inside_positive_anchor_fraction=float(np.mean((length-edge_error<=threshold)[positive])) if positive.any() else None,bound_requires_valid_certificate=bool(result.get('valid_bound',False)))
    if endpoint['method']=='E5':
        slack=length+norms(edges-anchor)-initial;dotedge=np.sum(edges*anchor,axis=1);valid=(length>0)&(initial>0);cos=np.divide(dotedge,length*initial,out=np.ones_like(length),where=valid);angles=np.degrees(np.arccos(np.clip(cos,-1,1)))
        out['direction_guard']={'weighted_triangle_slack_over_TV_H':float(problem.w@slack/tv) if tv else None,'raw_min_triangle_slack':float(slack.min(initial=0)),'reversal_weight_mass':float(problem.w[valid&(dotedge<0)].sum()/mass) if mass else None,'expansion_weight_mass':float(problem.w[length>initial].sum()/mass) if mass else None,'nonzero_edge_angle_quantiles_degrees':np.quantile(angles[valid],[0,.1,.5,.9,1]).tolist() if valid.any() else None,'zero_anchor_edges':int(sum(initial==0))}
        if qssc is not None:
            qedge=problem.B@qssc['G'];qslack=norms(qedge)+norms(qedge-anchor)-initial;out['direction_guard']['QSSC_weighted_triangle_slack_over_TV_H']=float(problem.w@qslack/tv) if tv else None
            truth=store.get(entry['objects']['labels']);same=truth[problem.i]==truth[problem.j]
            for name,mask in [('within_label',same),('between_label',~same)]:
                anchor_tv=float(problem.w[mask]@initial[mask]);out['direction_guard'][name+'_edge_TV_over_anchor']=float(problem.w[mask]@length[mask]/anchor_tv) if anchor_tv else None;out['direction_guard']['QSSC_'+name+'_edge_TV_over_anchor']=float(problem.w[mask]@norms(qedge)[mask]/anchor_tv) if anchor_tv else None
            out['direction_guard']['label_audit_scope']='Post-fit aggregate edge variation; a change alone does not establish useful or harmful class fusion'
    if endpoint['method']=='E6':
        Z=result['Zf'];T=problem.whitened(Z);eig=linalg.eigvalsh(T) if len(T) else np.array([1.]);gram=Z.T@Z
        scale_matrix=gram/problem.s[:,None]/problem.s[None,:] if len(problem.s) else np.eye(1);minimum=float(np.sqrt(max(0.,linalg.eigvalsh(sym(scale_matrix))[0])));eta=endpoint['parameters'].get('eta_dir',.5);rho=endpoint['rho'];sigmin=float(problem.s[-1]) if len(problem.s) else 0.
        out['directional_floor']={'whitened_min_eigenvalue':float(eig[0]),'generalized_min_directional_scale':minimum,'dual_PSD_norm':float(linalg.norm(result['S'])),'sufficient_inactivity_nominal_target':bool(rho*S<(1-eta)*sigmin),'sufficient_inactivity_actual_plus_error':bool((result['movement']+result['movement_error'])*S<(1-eta)*sigmin) if result['movement_error'] is not None else False,'repair':result['repair'],'rank_info':result['rank_info'],'basis_reconstruction_max_error':float(np.max(np.abs(problem.reconstruct(Z)-G),initial=0)),'basis':{k:store.put(v) for k,v in [('U',problem.U),('Sigma',problem.s),('V',problem.V),('Y',problem.Y)]},'basis_qualification':'Deterministically regenerated from exact frozen H under the locked numerical environment; reconstruction checked against saved G'}
        if qssc is not None:
            Q=qssc['G'];zq=(Q-problem.mean)@problem.V;Tq=problem.whitened(zq);out['directional_floor']['same_target_QSSC_whitened_min_eigenvalue']=float(linalg.eigvalsh(Tq)[0]) if len(Tq) else 1.;out['directional_floor']['distance_from_same_target_QSSC_relative']=float(linalg.norm(G-Q)/S) if S else 0.
            if qssc.get('valid_bound') and qssc['movement_error'] is not None and sigmin>0:
                lower=out['directional_floor']['same_target_QSSC_whitened_min_eigenvalue']-qssc['movement_error']*S/sigmin;out['directional_floor']['QSSC_optimum_whitened_min_lower_from_gap']=float(lower);out['directional_floor']['QSSC_optimal_retained_projection_guard_feasible_from_gap']=bool(lower>=eta)
        if len(problem.s):
            truth=store.get(entry['objects']['labels']);weak=problem.Y[:,-1];overall=weak.mean();between=sum(np.sum(truth==c)*(weak[truth==c].mean()-overall)**2 for c in np.unique(truth));total=float(np.sum((weak-overall)**2));out['directional_floor']['posthoc_weakest_direction_between_label_fraction']=float(between/total) if total else None;out['directional_floor']['weakest_direction_singular_gap_relative']=float((problem.s[-2]-problem.s[-1])/problem.s[-1]) if len(problem.s)>1 else None;out['directional_floor']['weak_direction_qualification']='Post-fit descriptive label association; repeated singular values make an individual weakest basis vector nonunique. This does not by itself establish noise preservation.'
    return out
