"""One terminal scoring stage, after a verified freeze of numerical eligibility."""
from __future__ import annotations
import gzip,hashlib
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import roc_auc_score
from experiments.v2_kmeans_protocol.metrics import evaluate_partition
from method_extension.extension_round3.convex import FusionProblem,eligible,matched,lengths
from method_extension.extension_round3.e1_v3_selective_tube import dispersion_lower_bound
from .common import *
from .rounding import fit


def freeze_outputs(config,root):
    spec,lock,store=locked(root,config);marker=store.root/'numerical_freeze.json'
    for key,name in [('input_lock_sha256','cohort_lock.json'),('registry_sha256','method_registry.json'),('queue_sha256','experiment_queue.json')]:
        if lock[key]!=digest(ROOT/'configs/extension_round3'/name):raise ValueError('registered input, registry or queue changed')
    if marker.exists():
        frozen=read(marker)
        for rel,sha in frozen['files'].items():
            if digest(store.root/rel)!=sha:raise ValueError('numerical freeze object changed')
        return frozen
    if any(v['phase']=='fitting' for v in ResourceLedger(root).state()['active'].values()):raise RuntimeError('cannot score while numerical workers are active')
    audits={};profiles=[];files={}
    deviation_path=store.root/'resource_protocol_deviations.json'
    deviations=read(deviation_path) if deviation_path.exists() else {'affected_profile_ids':[]}
    scheduler={}
    if (store.root/'scheduler_log.jsonl').exists():
        for line in (store.root/'scheduler_log.jsonl').read_text().splitlines():
            entry=json.loads(line);scheduler[entry['id']]=entry['status']
    for planned in queue():
        p=profile_path(store,planned['id'])
        if not p.exists():
            gate=read(store.root/'optional_gate.json') if (store.root/'optional_gate.json').exists() else {'passed':False}
            status='UNRUN_PRIMARY_COVERAGE_GATE' if planned['stage']==6 and not gate.get('passed',False) else scheduler.get(planned['id'],'UNRUN_BUDGET_OR_PHASE')
            retained=dict(planned,status=status,qualified=False,certified=False)
            if status=='UNRUN_CUMULATIVE_CAP':
                path=store.root/'paths'/f"{planned['benchmark']}__{planned['method']}__t{planned['tau_multiplier']:g}"/'path.json'
                if path.exists() and read(path)['points']:
                    point=min(read(path)['points'],key=lambda x:abs(x['certificate']['movement']-planned['rho']))
                    retained.update(result=point['result'],certificate=point['certificate'],**{'lambda':point['lambda']},recovery_reason='Retain an earlier finite path point without optimization after the native cumulative cap')
            atomic_json(p,retained)
        record=read(p);audit={'qualified':False,'certified':False,'status':record['status']}
        if record.get('result'):
            result=get_arrays(store,record['result']);c=lock['cohorts'][planned['benchmark']];H=store.get(c['objects']['H']);W=store.get(c['objects']['W0'])
            if result['G'].shape!=H.shape or result['G'].dtype!=np.dtype('float64') or not np.isfinite(result['G']).all():raise ValueError('rounding matrix shape, dtype or finiteness is invalid')
            if planned['method'] in registry() or planned['method']=='UNIFORM_GRAPH_ALIAS':
                params=get_arrays(store,record.get('parameters',{}))
                if planned['method'] in registry() and 'parameters' not in record:
                    from .calibration import parameters
                    ep=store.root/'evidence'/f"{planned['benchmark']}__t{planned['tau_multiplier']:g}.json"
                    params,meta=parameters(H,W,get_arrays(store,read(ep)['result']),registry()[planned['method']])
                    audit['recovered_parameters']=put_arrays(store,params);audit['recovered_intervention_metadata']=put_arrays(store,meta)
                    audit['recovery_reason']='Restore model identity for a finite point retained after guarded interruption; no new optimization'
                if planned['method']=='UNIFORM_GRAPH_ALIAS':params={'weights':.9*FusionProblem(H,W,1.).w}
                P=FusionProblem(H,W,record.get('lambda',record.get('lambda_value')),**params)
                for key in ['q','p']:
                    if result.get(key) is not None and (result[key].shape!=P.h.shape or result[key].dtype!=np.dtype('float64') or not np.isfinite(result[key]).all()):raise ValueError('invalid quadratic dual domain')
                cert=P.certificate(result['G'],result['q'],result.get('p'))
                audit.update(certificate=scalar(cert),certified=eligible(cert,planned['rho']),qualified=matched(cert,planned['rho']))
                if record.get('qualified') and not audit['qualified']:audit['status']='QUALIFICATION_AUDIT_FAILURE'
            elif planned['method']=='SC':
                if not np.array_equal(result['G'],H):raise ValueError('SC is not frozen H')
                audit.update(qualified=True,certified=True)
            elif planned['method']=='SSC_REFERENCE':
                from method_extension.extension_verification.convex import Problem
                P=Problem(H,W,c['gamma_effective'],kind='ssc')
                if result['q'].shape!=P.anchor_edges.shape or result['q'].dtype!=np.dtype('float64') or not np.isfinite(result['q']).all():raise ValueError('invalid original-SSC edge dual domain')
                if result.get('p') is not None and result['p'].shape!=(len(P.hinges.anchors),):raise ValueError('invalid original-SSC hinge dual domain')
                dual=P.dual(result['q'],result.get('p'));primal=P.primal(result['G']);signed=primal-dual['dual'];relative=signed/max(1.,abs(primal),abs(dual['dual']));cap=max(v for k,v in dual.items() if k.endswith('violation'))
                qualified=bool(signed>=0 and relative<=1e-5 and cap<=1e-8);audit.update(qualified=qualified,certified=qualified,certificate={'primal':primal,'dual':dual['dual'],'signed_gap':signed,'relative_gap':relative,'capacity_residual':cap})
            if not np.isfinite(result['G']).all():raise ValueError('nonfinite rounding output')
            for ref in collect_refs([record,audit]):
                if digest(store.root/ref['path'])!=ref['sha256']:raise ValueError('numerical CAS identity mismatch')
                files[ref['path']]=ref['sha256']
        if planned['id'] in deviations['affected_profile_ids']:
            audit.update(qualified=False,status='PATH_CPU_PROTOCOL_DEVIATION',protocol_compliant=False,protocol_deviation='Native cumulative path cost exceeded 1800 CPU seconds; all outputs on this path are conservatively descriptive only. Numerical certification remains separately reported.')
        else:audit['protocol_compliant']=True
        audits[planned['id']]=audit;profiles.append(record);files[str(p.relative_to(store.root))]=digest(p)
    for p in (store.root/'evidence').glob('*.json'):
        evidence_record=read(p);cohort=lock['cohorts'][evidence_record['benchmark']]
        if evidence_record['H_sha256']!=cohort['objects']['H']['sha256'] or evidence_record['W_sha256']!=cohort['objects']['W0']['sha256']:raise ValueError('evidence and frozen geometry identities differ')
        files[str(p.relative_to(store.root))]=digest(p)
        for ref in collect_refs(read(p)):
            if digest(store.root/ref['path'])!=ref['sha256']:raise ValueError('evidence object changed')
            files[ref['path']]=ref['sha256']
    files['cohort_lock.json']=digest(store.root/'cohort_lock.json')
    if deviation_path.exists():files['resource_protocol_deviations.json']=digest(deviation_path)
    frozen=dict(schema='ssc-round3-terminal-numeric-freeze-v1',source_fingerprint=lock['source_fingerprint'],protocol_sha256=digest(config),effective_protocol_sha256=identity(spec),files=files,qualification=audits,labels_loaded=False,numerical_work_closed=True,analysis_source_files={str((ROOT/'experiments/extension_round3'/n).relative_to(ROOT)):digest(ROOT/'experiments/extension_round3'/n) for n in ['evaluate.py','report.py','release.py']})
    atomic_json(marker,frozen);return frozen


def mechanisms(store,lock,record,G,y):
    c=lock['cohorts'][record['benchmark']];H=store.get(c['objects']['H']);W=store.get(c['objects']['W0']);P=FusionProblem(H,W,1.);w=P.w;a0=lengths(P.h);edge=P.B@G;lg=lengths(edge);cross=y[P.i]!=y[P.j];S=P.S;Hc=H-H.mean(axis=0);Gc=G-G.mean(axis=0);scale=float(np.sum(Hc*Gc)/S**2) if S else 1.;gap=record.get('certificate',{}).get('gap',0.)
    out=dict(id=record['id'],benchmark=record['benchmark'],method=record['method'],rho=record['rho'],tau_multiplier=record['tau_multiplier'],numerically_certified=record.get('certified',False),movement_matched=record.get('qualified',False),movement=float(np.linalg.norm(G-H)/S) if S else 0.,activity='EXACT_IDENTITY_INACTIVE' if np.array_equal(G,H) else 'MOVED',dispersion=float(np.linalg.norm(Gc)/S) if S else 0.,affine_scale=scale,affine_residual=float(np.linalg.norm(Gc-scale*Hc)/S) if S else 0.,weighted_slack=float(w@(lg+lengths(edge-P.h)-a0)),reversed_edge_fraction=float(np.mean(np.sum(edge*P.h,axis=1)<-1e-12)) if len(w) else 0.,expanded_edge_fraction=float(np.mean(lg>a0+1e-10)) if len(w) else 0.,original_components=int(connected_components(W,directed=False,return_labels=False)),cross_class_edge_fraction=float(cross.mean()) if len(w) else None,cross_class_weight_fraction=float(w[cross].sum()/w.sum()) if len(w) else None)
    _,class_index=np.unique(y,return_inverse=True);counts=np.bincount(class_index);hmean=np.zeros((len(counts),H.shape[1]));gmean=np.zeros_like(hmean);np.add.at(hmean,class_index,H);np.add.at(gmean,class_index,G);hmean/=counts[:,None];gmean/=counts[:,None]
    hwithin=float(np.sum((H-hmean[class_index])**2));gwithin=float(np.sum((G-gmean[class_index])**2));hbetween=float(np.sum(counts[:,None]*(hmean-H.mean(axis=0))**2));gbetween=float(np.sum(counts[:,None]*(gmean-G.mean(axis=0))**2))
    out['within_label_variation_ratio']=gwithin/hwithin if hwithin else None;out['between_label_variation_ratio']=gbetween/hbetween if hbetween else None
    for key,mask in [('within',~cross),('between',cross)]:
        denom=float(w[mask]@a0[mask]);out[key+'_length_ratio']=float(w[mask]@lg[mask]/denom) if denom else None
    params=get_arrays(store,record.get('parameters',{}))
    if record['method']=='UNIFORM_GRAPH_ALIAS':params={'weights':.9*w}
    meta=get_arrays(store,record.get('intervention_metadata',{}))
    if 'weights' in params:
        from scipy import sparse
        new=params['weights'];new_graph=sparse.csr_matrix((np.r_[new,new],(np.r_[P.i,P.j],np.r_[P.j,P.i])),shape=W.shape);out['modified_components']=int(connected_components(new_graph,directed=False,return_labels=False));fraction=np.divide(new,w);removed=w-new;degree=np.asarray(W.sum(axis=1)).ravel();new_degree=np.bincount(np.r_[P.i,P.j],weights=np.r_[new,new],minlength=len(H));out.update(nonuniform_weight_deviation=float(w@np.abs(fraction-.9)/w.sum()) if len(w) else 0.,removed_mass_fraction=float(removed.sum()/w.sum()) if len(w) else None,minimum_edge_fraction=float(fraction.min()) if len(w) else None,maximum_edge_fraction=float(fraction.max()) if len(w) else None,degree_ratio_min=float(np.min(new_degree[degree>0]/degree[degree>0])) if np.any(degree>0) else None,degree_ratio_max=float(np.max(new_degree[degree>0]/degree[degree>0])) if np.any(degree>0) else None,support_unchanged=bool(np.all(new>0)),cross_class_removed_mass=float(removed[cross].sum()),within_class_removed_mass=float(removed[~cross].sum()))
    if 'tubes' in params:
        a=params['tubes'];uncertainty=2*np.sqrt(max(0.,gap));out.update(tube_budget=float(w@a),tube_target_budget=meta.get('target_budget'),tube_deviation_from_uniform=float(w@np.abs(a-.25*a0)/(w@a0)) if w@a0 else 0.,tube_reference_budget=float(.25*(w@a0)),active_tubes=int(np.sum(lg-a>uncertainty)),uncertain_tubes=int(np.sum(np.abs(lg-a)<=uncertainty)),dispersion_certified_lower=float(dispersion_lower_bound(S,gap)/S) if S else 0.,cross_class_tube_budget=float(w[cross]@a[cross]),within_class_tube_budget=float(w[~cross]@a[~cross]))
    if 'alpha' in params:
        alpha=params['alpha'];out.update(realized_guard_loss=float((w*alpha)@(lg+lengths(edge-P.h)-a0)),guard_alpha_deviation_from_uniform=float(w@np.abs(alpha-1)/w.sum()) if len(w) else 0.,guard_coefficient_mass=float(w@alpha),cross_class_guard_mass=float(w[cross]@alpha[cross]),within_class_guard_mass=float(w[~cross]@alpha[~cross]))
    for key,mask in [('within',~cross),('between',cross)]:
        mass=float(w[mask].sum());anchor_mass=float(w[mask]@a0[mask])
        if 'weights' in params:out[key+'_removed_mass_rate']=float((w[mask]-params['weights'][mask]).sum()/mass) if mass else None
        if 'tubes' in params:out[key+'_weighted_eta']=float(w[mask]@params['tubes'][mask]/anchor_mass) if anchor_mass else None
        if 'alpha' in params:out[key+'_weighted_alpha']=float(w[mask]@params['alpha'][mask]/mass) if mass else None
    ep=store.root/'evidence'/f"{record['benchmark']}__t{record['tau_multiplier']:g}.json"
    if ep.exists():
        E=get_arrays(store,read(ep)['result']);ell=E['raw_leverage'];out.update(leverage_min=float(ell.min()) if len(ell) else None,leverage_median=float(np.median(ell)) if len(ell) else None,leverage_max=float(ell.max()) if len(ell) else None,denominator_min=float(E['denominator'].min()) if len(ell) else None,denominator_bound_margin=float(np.min(E['denominator']-E['denominator_bound'])) if len(ell) else None,evidence_CPU_seconds=E['CPU_seconds'],evidence_max_residual=E['max_residual'],inverse_symmetry=E['inverse_symmetry'])
        cavity=E['scores']['cavity'];pilot_score=E['scores']['pilot'];pilot_mass=float(w@pilot_score)
        out.update(cavity_score_median=float(np.median(cavity)) if len(w) else None,pilot_score_median=float(np.median(pilot_score)) if len(w) else None,cavity_pilot_weighted_score_difference=float(w@np.abs(cavity-pilot_score)/w.sum()) if len(w) else 0.,cavity_pilot_relative_score_difference=float(w@(cavity-pilot_score)/pilot_mass) if pilot_mass else 0.)
        for score in ['cavity','pilot','anchor','leverage']:
            out[score+'_cross_class_auroc']=float(roc_auc_score(cross,E['scores'][score])) if len(np.unique(cross))==2 else None
        if 'ranks' in meta and record['method'] in registry():
            from .calibration import parameters
            method=registry()[record['method']];pilot=dict(method,score='pilot');_,pm=parameters(H,W,E,pilot);mass=w*a0 if method['family']=='tube' else w
            out['weighted_rank_difference_from_pilot']=float(mass@np.abs(meta['ranks']-pm['ranks'])/mass.sum()) if mass.sum() else 0.
    return out


def evaluate(config,root):
    spec,lock,store=locked(root,config);frozen=freeze_outputs(config,root);marker_sha=digest(store.root/'numerical_freeze.json');started=store.root/'terminal_evaluation.json'
    if started.exists() and read(started)['numeric_freeze_sha256']!=marker_sha:raise ValueError('evaluation freeze differs')
    if not started.exists():atomic_json(started,dict(numeric_freeze_sha256=marker_sha,stage='LABEL_ACCESS_OPEN',fitting_closed=True))
    for b in ORDER:
        c=lock['cohorts'][b];y=store.get(c['objects']['labels']);initial=store.get(c['anchor_initial_indices'])
        for planned in [r for r in queue() if r['benchmark']==b]:
            record=read(profile_path(store,planned['id']));dest=store.root/'evaluations'/(record['id']+'.json')
            if dest.exists():continue
            audit=frozen['qualification'][record['id']]
            record=dict(record,certificate=audit.get('certificate',record.get('certificate',{})),qualified=audit['qualified'],certified=audit['certified'])
            if 'recovered_parameters' in audit:record=dict(record,parameters=audit['recovered_parameters'],intervention_metadata=audit['recovered_intervention_metadata'])
            if not record.get('result'):
                atomic_json(dest,dict(id=record['id'],status=record['status'],complete=False));continue
            result=get_arrays(store,record['result']);G=result['G'];panels={}
            for panel in spec['rounding']['panels']:
                rows=[];saved=[];failure=[]
                for seed in range(50):
                    try:
                        out=fit(G,c['K'],seed,indices=initial[seed] if panel=='anchor_generated' else None);metrics=evaluate_partition(y,out['labels']);rows.append(dict(seed=seed,acc=100*metrics['acc'],nmi=100*metrics['nmi'],inertia=out['inertia'],iterations=out['iterations']));saved.append(put_arrays(store,out))
                    except Exception as e:failure.append({'seed':seed,'exception':type(e).__name__,'message':str(e)})
                panels[panel]={'trials':rows,'scientific_objects':saved,'complete':len(rows)==50,'failure':failure}
            diagnostic=mechanisms(store,lock,record,G,y)
            atomic_json(dest,dict(id=record['id'],status=record['status'],qualified=audit['qualified'],certified=audit['certified'],complete=all(p['complete'] for p in panels.values()),panels=panels,mechanism=diagnostic,numeric_freeze_sha256=marker_sha));print('SCORED',record['id'],flush=True)
    atomic_json(started,dict(numeric_freeze_sha256=marker_sha,stage='TERMINAL_SCORING_COMPLETE',fitting_closed=True))
