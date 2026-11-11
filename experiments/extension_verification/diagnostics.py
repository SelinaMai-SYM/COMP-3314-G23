"""Label-free saved-point diagnostics and bounded matching on declared points."""
import json
import numpy as np
from experiments.submission_refresh.core import atomic_json
from method_extension.extension_verification.convex import row_norm,rowunit,Problem
from method_extension.extension_verification.dispersion import geometric_median_bounds
from .inputs import load_locked


def angular_movement(U,G,mask):
    if not np.any(mask):return None
    dot=np.sum(rowunit(U[mask])*rowunit(G[mask]),axis=1)
    return float(np.sqrt(np.mean(np.degrees(np.arccos(np.clip(dot,-1,1)))**2)))


def stopping_tube_diagnostic(H,W,G,gamma,eta=.25,ordinary=None):
    problem=Problem(H,W,gamma,kind='relative',eta=eta);distances=row_norm(problem.B@G);positive=problem.anchor_lengths>0;inside=distances<problem.a
    result={'positive_edges':len(problem.w),'coincident_anchor_edges':int((~positive).sum()),'strictly_inside_stopping_tube_count':int(inside.sum()),'strictly_inside_stopping_tube_fraction':float(inside.mean()) if len(inside) else None,'inside_tube_weight_fraction':float(problem.w[inside].sum()/problem.w.sum()) if problem.w.sum()>0 else None,'scope':'Supplementary label-free explanation on fixed saved outputs; does not select parameters or change primary eligibility'}
    if ordinary is not None:
        G0,q0=ordinary;edge0=row_norm(problem.B@G0);dual=problem.dual(q0,repair=False);primal=problem.primal(G0);gap=primal-dual['dual'];relative=gap/max(1.,abs(primal),abs(dual['dual']));feasible=max([v for k,v in dual.items() if k.endswith('violation')],default=0)<=1e-8
        result['ordinary_SSC_output']={'all_edges_at_or_above_frozen_tolerances':bool(np.all(edge0>=problem.a)),'strictly_inside_stopping_tube_count':int(np.sum(edge0<problem.a)),'E1_primal':primal,'E1_dual_using_SSC_q':dual['dual'],'absolute_gap':gap,'relative_gap':relative,'E1_cross_certificate':bool(feasible and 0<=gap and relative<=1e-5),'qualification':'Cross-objective diagnostic only; neither replaces the primary E1 output nor qualifies an uncertified ordinary-SSC control'}
    return result


def compute(config,artifact_root):
    specification,lock,store=load_locked(config,artifact_root);records=[json.loads(p.read_text()) for p in sorted((store.root/'points').glob('*.json'))];records=[r for r in records if r['source_fingerprint']==lock['source_fingerprint']];results={};anchors={}
    for row in records:
        entry=lock['datasets'][row['benchmark']];H=store.get(entry['objects']['F0' if row['panel']=='original' else 'U']);G=store.get(row['objects']['G']);mask=np.any(H!=0,axis=1)&(row_norm(G)>1e-12)
        result={'point_id':row['point_id'],'normalized_L21_movement':float(row_norm(G-H).sum()/max(float(row_norm(H).sum()),1e-12)),'G_norm_min':float(row_norm(G).min()),'G_norm_max':float(row_norm(G).max()),'angular_mask_count':int(mask.sum()),'angular_excluded_count':int((~mask).sum()),'RMS_angle_degrees':angular_movement(H,G,mask) if row['panel']=='angular' else None}
        if row['method'] in ['E1','SSC'] and row.get('primary'):
            key=(row['benchmark'],row['panel'])
            if key not in anchors:anchors[key]=geometric_median_bounds(H)
            baseline=anchors[key];output=geometric_median_bounds(G);result['dispersion']={'anchor':{k:v for k,v in baseline.items() if k!='center'},'output':{k:v for k,v in output.items() if k!='center'},'scope':'Optimized G before rounding normalization'}
            if row['method']=='E1':
                eta=row['parameters']['eta'];epsilon=row['solver']['absolute_gap'];lower=output['lower']-eta*baseline['upper']+epsilon;upper=output['upper']-eta*baseline['lower']+epsilon
                result['dispersion'].update(absolute_optimality_gap=epsilon,eta=eta,verified_lower_margin=lower,possible_upper_margin=upper,bound_status='VERIFIED_BOUND' if lower>=0 else 'INCONSISTENT_BOUND' if upper<0 else 'INTERVAL_UNRESOLVED')
        if row['kind']=='relative_neighbor':
            from method_extension.extension_verification.convex import Hinges
            system=entry['random_hinges'][str(row['parameters']['random_seed'])] if row['parameters'].get('random_seed') is not None else {k:entry['objects']['hinge_'+k] for k in ['anchors','normals','beta']}
            h=Hinges(store.get(system['anchors']),store.get(system['normals']),store.get(system['beta']));Q=store.get(row['objects']['Q']);g=h.apply(G)+h.beta;q=h.apply(Q)+h.beta
            result['hinges']={'count':len(g),'positive_G_hinges':int(np.sum(g>1e-8)),'positive_Q_hinges':int(np.sum(q>1e-8)),'G_hinge_sum':float(np.maximum(g,0).sum()),'Q_hinge_sum':float(np.maximum(q,0).sum()),'scope':'Frozen references; normalization may change a positive margin'}
        if row['method']=='E1' and row.get('primary'):
            ordinary=[r for r in records if r['benchmark']==row['benchmark'] and r['panel']==row['panel'] and r['method']=='SSC' and r.get('primary')]
            control=(store.get(ordinary[0]['objects']['G']),store.get(ordinary[0]['objects']['q'])) if len(ordinary)==1 else None
            result['stopping_tubes']=stopping_tube_diagnostic(H,store.get(entry['objects']['W0']),G,row['gamma'],row['parameters']['eta'],control)
        results[row['point_id']]=result
    matches=[]
    for target in records:
        if not target.get('primary') or target['method'] not in ['E1','E2'] or not target['solver'].get('certified'):continue
        candidates=[r for r in records if r['benchmark']==target['benchmark'] and r['panel']==target['panel'] and r['method']=='SSC' and r['solver'].get('certified')];ranked=[]
        for base in candidates:
            if target['method']=='E1':
                a=results[target['point_id']]['normalized_L21_movement'];b=results[base['point_id']]['normalized_L21_movement'];floor=1e-6;mask_count=None
            else:
                entry=lock['datasets'][target['benchmark']];H=store.get(entry['objects']['U']);A=store.get(target['objects']['G']);B=store.get(base['objects']['G']);mask=np.any(H!=0,axis=1)&(row_norm(A)>1e-12)&(row_norm(B)>1e-12);a=angular_movement(H,A,mask);b=angular_movement(H,B,mask);floor=.1;mask_count=int(mask.sum())
                if a is None or b is None:continue
            ranked.append((abs(a-b),base['gamma'],base['point_id'],a,b,floor,mask_count))
        if ranked:
            ranked.sort();distance,gamma,point,a,b,floor,count=ranked[0];tolerance=max(.05*a,floor);available=distance<=tolerance
            match={'target_point_id':target['point_id'],'control_point_id':point if available else None,'nearest_declared_point_id':point,'status':'DEGENERATE_ZERO_MATCH' if available and a<=floor and b<=floor else 'MATCHED' if available else 'UNAVAILABLE_TOLERANCE','target_movement':a,'control_movement':b,'absolute_difference':distance,'tolerance':tolerance,'angular_common_mask_count':count,'added_search':False}
        else:match={'target_point_id':target['point_id'],'control_point_id':None,'status':'UNAVAILABLE_NO_CERTIFIED_POINT','added_search':False}
        matches.append(match)
    affine=[]
    for scaled in records:
        if scaled['method']!='uniform_scaling' or scaled['parameters'].get('eta')!=.25:continue
        controls=[r for r in records if r['benchmark']==scaled['benchmark'] and r['panel']==scaled['panel'] and r['method']=='SC' and r.get('primary')]
        if len(controls)!=1:continue
        base=controls[0];factor=.25 if scaled['panel']=='original' else 1.;error=float(np.max(np.abs(store.get(scaled['objects']['Q'])-factor*store.get(base['objects']['Q']))))
        a=store.root/'evaluations'/f"{scaled['point_id']}.json";b=store.root/'evaluations'/f"{base['point_id']}.json";agreement=None
        if a.exists() and b.exists():
            from sklearn.metrics import adjusted_rand_score
            A=store.get(json.loads(a.read_text())['predictions']);B=store.get(json.loads(b.read_text())['predictions']);agreement=all(adjusted_rand_score(x,y)==1 for x,y in zip(A,B))
        affine.append({'benchmark':scaled['benchmark'],'panel':scaled['panel'],'scaled_point_id':scaled['point_id'],'SC_point_id':base['point_id'],'expected_scale_in_Q':factor,'maximum_coordinate_error':error,'all_50_partitions_equivalent':agreement})
    output={'schema':'ssc-refinement-diagnostics-v1','affine_checks':affine,'source_fingerprint':lock['source_fingerprint'],'protocol_sha256':lock['protocol_sha256'],'points':results,'movement_matches':matches};atomic_json(store.root/'diagnostics.json',output);return output
