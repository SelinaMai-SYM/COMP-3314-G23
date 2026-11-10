"""Conditional G4/G5 adapter: no benchmark execution before the fixed G3 gate.

This adapter introduces no loss or parameter grid. The shared scheduler owns
CPU reservations, workers and deadlines. Source and backend validation are
required even for label-blind runtime profiles on real benchmark inputs.
"""
from __future__ import annotations
import json
import math
import resource
import signal
import time
import traceback
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import laplacian
from scipy.sparse.linalg import eigsh
from threadpoolctl import threadpool_limits

from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_embedding import spectral_embedding,orient_eigenvector_signs
from method_extension.next_round.certified_solver import graph_arrays,solve
from method_extension.submission_refresh.ensc import elastic_net_code,coefficients_to_affinity,SOURCE_REVISION
from experiments.subset_search.runner import round_embedding
from experiments.v2_kmeans_protocol.kmeans_trials import GREEDY
from .core import ROOT,ArtifactStore,atomic_json,digest,identity,install_cpu_limit
from .graph_repair import (_solution,_save_result,row_unit,mass_match,angular_graph,
                           scientific_source_record)
from .selection import summarize,capability

DATASETS=('ORL_att92','JAFFE','YaleB_cropped2414','USPS')
K_VALUES={'ORL_att92':40,'JAFFE':10,'YaleB_cropped2414':38,'USPS':10}
GRAPH_GAMMAS=(.001,1.,10.,1000.,1000000.)
ORIGINAL_GAMMAS=(1e-6,.001,.01,.1,.3,1.,3.,10.,30.,100.,300.,1000.,10000.,100000.,1000000.)


def _authorization(task):
    gate_path=Path(task.get('gate_file',ROOT/'results/submission_refresh/extension_gate.json'))
    validation_path=Path(task.get('backend_validation_file',ROOT/'results/submission_refresh/ensc_backend_validation.json'))
    gate=json.loads(gate_path.read_text())
    if gate.get('promotion_passed') is not True or gate.get('decision')!='PASSED':
        raise ValueError('G4/G5 prohibited: the preregistered G3 completion gate has not passed')
    if task.get('gate_sha256') and digest(gate_path)!=task['gate_sha256']:
        raise ValueError('G3 gate record identity changed')
    validation=json.loads(validation_path.read_text())
    if (validation.get('passed') is not True or validation.get('source_revision')!=SOURCE_REVISION
        or validation.get('backend_source_sha256')!=digest(ROOT/'method_extension/submission_refresh/ensc.py')
        or validation.get('test_file_sha256')!=digest(ROOT/'tests/submission_refresh/test_ensc_backend.py')):
        raise ValueError('G4/G5 prohibited: verified true elastic-net backend record is missing or stale')
    return {'gate_sha256':digest(gate_path),'backend_validation_sha256':digest(validation_path),
            'source_revision':SOURCE_REVISION,'gate':gate,'backend_validation':validation}


def intended_configurations(dataset):
    if dataset not in DATASETS:raise ValueError('G4 inputs must use the four frozen full benchmarks')
    rows=[]
    for anchor in ['F0','U']:
        rows.append({'dataset':dataset,'family':'fair_sc','anchor':anchor,'graph':'W0','gamma':0.})
    for gamma in ORIGINAL_GAMMAS:
        rows.append({'dataset':dataset,'family':'original_ssc','anchor':'F0','graph':'W0','gamma':gamma})
    for graph in ['Wa','S_tau0.95','S_tau1','wider_knn','random_count_mass_seed400']:
        for gamma in GRAPH_GAMMAS:
            rows.append({'dataset':dataset,'family':graph,'anchor':'F0','graph':graph,'gamma':gamma})
    for graph in ['S_tau0.95','S_tau1']:
        rows.append({'dataset':dataset,'family':'native_ensc_'+graph,'anchor':'native_spectral','graph':graph,'gamma':None})
    for row in rows:row['config_id']=f"{dataset}|G4|{row['family']}|{row['anchor']}|{row['gamma']}"
    return rows


def _inputs(dataset,data_root,store,source):
    """Reuse a matching full G3 input, never a retrospectively chosen subset."""
    from .baselines import load
    X,y,data_meta=load(dataset,data_root);X=np.asarray(X,dtype=float);y=np.asarray(y)
    refs={'X':store.put(X),'y':store.put(y)};matches=[]
    for path in sorted((store.root/'graph_inputs'/dataset).glob('*/representation.json')):
        meta=json.loads(path.read_text())
        if all(meta['objects'][name]['sha256']==refs[name]['sha256'] for name in ['X','y']) and meta.get('input_preparation')=='Y0' and meta.get('K')==K_VALUES[dataset] and meta.get('source',{}).get('implementation_hash')==source['implementation_hash']:
            matches.append((path,meta))
    if len({m['objects']['F0']['sha256'] for _,m in matches})>1:
        raise ValueError('multiple distinct full F0 artifacts exist; freeze an explicit input record before G4')
    if matches:
        path,meta=matches[0]
        return path.parent,meta,{name:store.get(ref) for name,ref in meta['objects'].items()}
    key=identity({'dataset':dataset,'X':refs['X'],'y':refs['y'],'source':source['implementation_hash'],'k':5,'prep':'Y0'})
    folder=store.root/'ensc_inputs'/dataset/key;path=folder/'representation.json'
    if path.exists():
        meta=json.loads(path.read_text());return folder,meta,{name:store.get(ref) for name,ref in meta['objects'].items()}
    F0,info=spectral_embedding(X,K_VALUES[dataset],k=5);A,Ainfo=knn_affinity(X,k=5);W0,Winfo=knn_affinity(F0,k=5)
    U=row_unit(F0);Wa=angular_graph(U)
    arrays={'X':X,'y':y,'A':A,'F0':F0,'U':U,'W0':W0,'Wa_raw':Wa}
    meta={'dataset':dataset,'K':K_VALUES[dataset],'input_preparation':'Y0',
          'input_membership':'full_preregistered_confirmation_benchmark_not_subset_winner',
          'historical_F_identity':'new recovered current artifact; not a historical missing F claim',
          'objects':{name:store.put(value) for name,value in arrays.items()},'source':source,
          'input_metadata':data_meta,'spectral_info':info,'A_info':Ainfo,'W0_info':Winfo}
    atomic_json(path,meta);return folder,meta,arrays


def _coefficient_graph(X,tau,store,source,*,profile_rows=None):
    """Each completed independent row is a resumable, label-free checkpoint."""
    import ast
    tree=ast.parse(Path(__file__).read_text())
    node=next(item for item in tree.body if isinstance(item,ast.FunctionDef) and item.name=='_coefficient_graph')
    if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str):node.body=node.body[1:]
    adapter_behavior=identity(ast.dump(node,include_attributes=False))
    unit=row_unit(X);xref=store.put(unit)
    parameters={'input':xref,'tau':tau,'source_gamma':50.,'n_nonzero':50,'support_size':100,'max_outer':40,
                'backend_source':digest(ROOT/'method_extension/submission_refresh/ensc.py'),
                'source_revision':SOURCE_REVISION,'environment':source['environment'],'adapter_fitting_behavior':adapter_behavior}
    folder=store.root/'ensc_coefficients'/identity(parameters);result_path=folder/'graph.json'
    if result_path.exists() and profile_rows is None:
        record=json.loads(result_path.read_text());return {**record,'arrays':{name:store.get(ref) for name,ref in record['objects'].items()}}
    rows=[];cols=[];data=[];alphas=[];diagnostics=[];timings=[]
    count=min(len(unit),int(profile_rows)) if profile_rows is not None else len(unit)
    for i in range(count):
        path=folder/'rows'/f'{i}.json';start=time.process_time()
        if path.exists():
            row=json.loads(path.read_text())
            if row.get('row')!=i or row.get('parameters_id')!=identity(parameters):raise ValueError('coefficient row checkpoint identity mismatch')
            ids=store.get(row['indices']);values=store.get(row['values']);diag=row['diagnostics'];alpha=row['alpha']
        else:
            ids_all=np.delete(np.arange(len(unit)),i);D=unit[ids_all];target=unit[i]
            alpha=float(np.max(np.abs(D@target),initial=0)/(50*tau))
            c,diag=elastic_net_code(D,target,alpha,tau,active_support=True,support_size=100,max_outer=40)
            nz=np.flatnonzero(c);ids=ids_all[nz];values=c[nz]
            row={'row':i,'indices':store.put(ids),'values':store.put(values),'alpha':alpha,'diagnostics':diag,
                 'cpu_seconds':time.process_time()-start,'parameters_id':identity(parameters)}
            atomic_json(path,row)
        if np.any(ids==i) or len(np.unique(ids))!=len(ids) or not np.isfinite(values).all():raise ValueError('invalid coefficient row checkpoint')
        rows.extend([i]*len(ids));cols.extend(ids);data.extend(values);alphas.append(alpha);diagnostics.append(diag)
        timings.append({'row':i,'cpu_seconds_this_call':time.process_time()-start,'original_cpu_seconds':row['cpu_seconds']})
    if profile_rows is not None:
        return {'status':'PROFILE_ONLY_INELIGIBLE','profiled_rows':count,'n':len(unit),'parameters':parameters,
                'timings':timings,'mean_row_cpu_seconds':float(np.mean([r['original_cpu_seconds'] for r in timings])),
                'evaluation':'NOT_COMPUTED','checkpoint_directory':str(folder)}
    C=sparse.csr_matrix((data,(rows,cols)),shape=(len(unit),len(unit)))
    transformed=coefficients_to_affinity(C,n_nonzero=50)
    arrays={name:transformed.pop(name) for name in ['C_pre_truncation','C','Cn','S']}
    arrays.update(alpha_i=np.asarray(alphas),unit_input=unit)
    record={'status':'COMPLETED','parameters':parameters,'objects':{name:store.put(value) for name,value in arrays.items()},
            'diagnostics':diagnostics,'input_zero_rows':np.flatnonzero(np.linalg.norm(X,axis=1)==0).tolist(),
            **transformed,'all_rows_kkt_qualified':all(d.get('kkt_qualified',d['status'] in ['ORTHOGONAL_ZERO_CODE','EMPTY_DICTIONARY']) for d in diagnostics),
            'row_cpu_timings':timings,'source':source}
    atomic_json(result_path,record);return {**record,'arrays':arrays}


def _wider_graph(F0,target_edges):
    """Choose k by topology count only; record unattainable exact counts."""
    n=len(F0);lower=min(5,n-1);upper=min(n-1,max(lower,int(math.ceil(2*target_edges/n))))
    graphs={}
    def evaluate(k):
        if k not in graphs:
            W,info=knn_affinity(F0,k=k);graphs[k]=(W,info,W.nnz//2)
        return graphs[k][2]
    evaluate(lower);evaluate(upper)
    lo,hi=lower,upper
    while hi-lo>1:
        middle=(lo+hi)//2
        if evaluate(middle)<target_edges:lo=middle
        else:hi=middle
    for k in [lo,hi]:evaluate(k)
    chosen=min(graphs,key=lambda k:(abs(graphs[k][2]-target_edges),k))
    W,info,count=graphs[chosen]
    return W,{'k':chosen,'target_edge_count':target_edges,'actual_edge_count':count,'edge_count_difference':count-target_edges,
              'count_qualified':abs(count-target_edges)<=max(1,.05*target_edges),
              'choice_rule':'closest evaluated integer k by edge count; no metric labels',
              'examined_counts':{str(k):v[2] for k,v in graphs.items()},'graph_info':info}


def _random_graph(n,weights,seed=400):
    weights=np.asarray(weights,dtype=float);count=len(weights);total=n*(n-1)//2;rng=np.random.RandomState(seed)
    if count>total:raise ValueError('infeasible random edge count')
    if count>total/4:
        i,j=np.triu_indices(n,1);take=rng.choice(total,count,replace=False);edges=np.column_stack([i[take],j[take]])
    else:
        pairs=set()
        for _ in range(100):
            if len(pairs)>=count:break
            m=max(64,2*(count-len(pairs)));left=rng.randint(0,n,m);right=rng.randint(0,n-1,m);right+=right>=left
            pairs.update((min(int(a),int(b)),max(int(a),int(b))) for a,b in zip(left,right))
        if len(pairs)<count:raise ValueError('INFEASIBLE_MATCHED_CONTROL')
        # Membership sampling is uniform; permutation resolves deterministic overfill.
        candidates=np.asarray(sorted(pairs),dtype=np.int64);edges=candidates[rng.permutation(len(candidates))[:count]]
    shuffled=weights[rng.permutation(count)]
    graph=sparse.csr_matrix((np.r_[shuffled,shuffled],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(n,n)) if count else sparse.csr_matrix((n,n))
    return graph,{'seed':seed,'target_edge_count':count,'actual_edge_count':graph.nnz//2,
                  'weight_multiset_preserved':True,'label_access':'NONE'}


def _native_spectral(S,K,y,store,source):
    if S.nnz==0:return {'status':'DEGENERATE_AFFINITY'}
    generator=np.random.default_rng(20261108);v0=generator.standard_normal(S.shape[0])
    L=laplacian(S,normed=True);values,vectors=eigsh(sparse.eye(len(y))-L,k=K,which='LA',v0=v0)
    order=np.argsort(values)[::-1];values=values[order];vectors=orient_eigenvector_signs(vectors[:,order]);G=row_unit(vectors)
    trials,pred,centers=round_embedding(G,y,K,GREEDY)
    return {'status':'COMPLETED','summary':summarize(trials),'trials':trials,
            'objects':{'G':store.put(G),'raw_eigenspace':store.put(vectors),'eigenvalues':store.put(values),
                       'eigensolver_v0':store.put(v0),'predictions':store.put(pred),'centers':store.put(centers),'affinity':store.put(S)},
            'solver':{'status':'NATIVE_SPECTRAL_CONTROL','certified':None},'source':source,
            'rounding':'50 greedy K-means++ seeds0..49,n_init=1; source constructor default20 starts is not used',
            'eigensolver':'source I-minus-normalized-L largest-eigenvector path, explicit v0=default_rng(20261108)'}


def _movement(record,F0,store):
    G=store.get(record['objects']['G'])
    return float(np.linalg.norm(G-F0,axis=1).sum()/max(np.linalg.norm(F0,axis=1).sum(),np.finfo(float).tiny))


def _matched_movement(target,original,F0,W0,meta,store,source,fit_limit):
    if not target['solver'].get('certified'):return {'status':'NOT_EVALUABLE_UNCERTIFIED_TARGET','attempts':[]}
    value=_movement(target,F0,store);tolerance=max(1e-6,.05*value)
    points=[(float(r['gamma']),_movement(r,F0,store),r) for r in original if r['solver'].get('certified')]
    points.sort(key=lambda x:x[0]);attempts=[]
    def matching():
        return sorted([p for p in points if abs(p[1]-value)<=tolerance],key=lambda p:(abs(p[1]-value),p[0]))
    for iteration in range(7):
        candidates=matching()
        if candidates:
            chosen=candidates[0]
            return {'status':'MATCHED_CERTIFIED','target_movement':value,'matched_movement':chosen[1],
                    'tolerance':tolerance,'gamma':chosen[0],'matched_solution':chosen[2],'attempts':attempts,
                    'selection_rule':'movement difference only; no ACC/NMI used for bisection'}
        if iteration==6:break
        brackets=[(a,b) for a,b in zip(points,points[1:]) if (a[1]-value)*(b[1]-value)<0]
        if not brackets:return {'status':'NO_CERTIFIED_BRACKET','target_movement':value,'attempts':attempts,'points':[(a,b) for a,b,_ in points]}
        a,b=brackets[0];gamma=math.sqrt(a[0]*b[0])
        fitted=_solution(F0,W0,meta,store,source,gamma=gamma,fit_cpu_limit=fit_limit)
        movement=_movement(fitted,F0,store);attempts.append({'gamma':gamma,'movement':movement,'certified':fitted['solver'].get('certified'),'objects':fitted['objects'],'solver':fitted['solver']})
        if not fitted['solver'].get('certified'):return {'status':'UNRESOLVED_UNCERTIFIED_BISECTION','target_movement':value,'attempts':attempts}
        points.append((gamma,movement,{**fitted,'gamma':gamma}));points.sort(key=lambda x:x[0])
    return {'status':'NO_MATCH_WITHIN_SIX_LOG_BISECTIONS','target_movement':value,'tolerance':tolerance,'attempts':attempts,'points':[(a,b) for a,b,_ in points]}


def _select(records):
    groups={}
    for family in ['fair_sc','original_ssc','Wa','S_tau0.95','S_tau1','wider_knn','random_count_mass_seed400','native_ensc_S_tau0.95','native_ensc_S_tau1']:
        pool=[r for r in records if r['family']==family and r['status']=='COMPLETED']
        if pool:
            flat=[{**r,**{k:v for k,v in r['summary'].items() if k!='native_best'}} for r in pool]
            groups[family]=capability(flat)
    operating=next((r for r in records if r['family']=='S_tau0.95' and r['gamma']==1.),None)
    original_fixed=next((r for r in records if r['family']=='original_ssc' and r['gamma']==1.),None)
    datasets={r.get('dataset') for r in records}
    definitions=intended_configurations(next(iter(datasets))) if len(datasets)==1 and next(iter(datasets)) in DATASETS else []
    expected={r['config_id'] for r in definitions};actual={r['config_id'] for r in records}
    by_id={r['config_id']:r for r in records}
    missing=sorted(expected-actual);invalid=[]
    for definition in definitions:
        row=by_id.get(definition['config_id'])
        if row is None:continue
        if any(row.get(key)!=value for key,value in definition.items()) or row.get('status')!='COMPLETED':
            invalid.append(definition['config_id']);continue
        if definition['anchor']!='native_spectral' and not row.get('solver',{}).get('certified'):
            invalid.append(definition['config_id']);continue
        try:summarize(row['trials'],objective=None)
        except (KeyError,ValueError,TypeError):invalid.append(definition['config_id']);continue
        if definition['family']=='wider_knn' and row.get('mass_matching',{}).get('count_qualified') is False:
            invalid.append(definition['config_id'])
    validity=bool(definitions) and len(records)==len(actual)==44 and actual==expected and not missing and not invalid
    return {'capability':groups,'locked_label_free_operating_point':operating,'original_fixed_gamma1':original_fixed,
            'comparison_validity':'COMPLETE_CERTIFIED_REQUIRED_DESIGN' if validity else 'INCOMPLETE_OR_UNQUALIFIED_REQUIRED_DESIGN',
            'missing_required_configurations':missing,'invalid_required_configurations':invalid,
            'qualified_for_four_benchmark_claim':validity,
            'primary_method':'S_tau0.95 five-gamma grid, never replaced by a better control',
            'selection':'ACC mean then NMI mean then stable configuration ID; label-assisted capability oracle',
            'no_second_performance_gate':True}


def _resume_context(definition,graph,anchor,meta,store,source,construction_source,graph_metadata):
    ensc=definition['graph'].startswith('S_tau')
    return {'schema':'G4-resume-context-v1','definition':definition,
        'anchor':None if anchor is None else store.put(anchor),'graph':store.put(graph),'graph_shape':list(graph.shape),'graph_nnz':int(graph.nnz),
        'input_objects':{key:meta['objects'][key] for key in ['X','y','F0','U']},
        'scientific_source_fingerprint':source['implementation_hash'],
        'construction_source_fingerprint':construction_source['implementation_hash'] if ensc else None,
        'backend_source_sha256':digest(ROOT/'method_extension/submission_refresh/ensc.py') if ensc else None,
        'environment':source['environment'],'graph_metadata_fingerprint':identity(graph_metadata),
        'rounding':{'initialization':GREEDY,'n_init':1,'seeds':list(range(50))}}


def _verify_saved_record(record,definition,context,store,seen):
    if any(record.get(key)!=value for key,value in definition.items()) or record.get('resume_context')!=context:
        raise ValueError('G4 saved configuration anchor/graph/source context mismatch; preserve it under its original run ID')
    def verify(value):
        if isinstance(value,dict):
            if {'sha256','path','kind'}<=value.keys():
                key=(value['sha256'],value['path'])
                if key not in seen:
                    item=store.get(value);seen.add(key)
                    if isinstance(item,(dict,list)):verify(item)
            else:
                for item in value.values():verify(item)
        elif isinstance(value,list):
            for item in value:verify(item)
    verify(record.get('objects',{}));verify(record.get('graph_objects',{}))
    if record.get('status')=='COMPLETED':
        summarize(record['trials'],objective=None)
        predictions=store.get(record['objects']['predictions'])
        if predictions.shape!=(50,context['graph_shape'][0]):raise ValueError('G4 saved prediction dimensions mismatch')
        expected_source=context['construction_source_fingerprint'] if definition['anchor']=='native_spectral' else context['scientific_source_fingerprint']
        if record.get('source',{}).get('implementation_hash')!=expected_source:raise ValueError('G4 saved scientific source fingerprint mismatch')
        ref=record['objects'].get('affinity') if definition['anchor']=='native_spectral' else record.get('graph_objects',{}).get('fitted_W')
        if ref!=context['graph']:raise ValueError('G4 saved actual graph object mismatch')
        if definition['anchor']!='native_spectral' and record['objects'].get('anchor')!=context['anchor']:
            raise ValueError('G4 saved actual anchor object mismatch')
    elif record.get('status')=='DEGENERATE_AFFINITY':
        if context['graph_nnz']!=0 or record.get('graph_objects',{}).get('W')!=context['graph']:raise ValueError('G4 saved degenerate affinity context mismatch')
    else:raise ValueError('G4 saved result has an unknown/incomplete status')
    return record


def run_ensc(task,data_root,artifact_root):
    """Shared-scheduler callback; datasets are fixed full inputs, never winners."""
    start=time.perf_counter();cpu=time.process_time();store=ArtifactStore(artifact_root)
    rid=task.get('run_id',identity(task));folder=store.root/'ensc_jobs'/rid;folder.mkdir(parents=True,exist_ok=True)
    result={'task':task,'status':'RUNNING','intended_configurations':intended_configurations(task['dataset'])}
    if task.get('cpu_limit') is not None:install_cpu_limit(task['cpu_limit'])
    try:
        result['authorization']=_authorization(task)
        source=scientific_source_record();construction_source=scientific_source_record(include_ensc=True)
        result['source']=construction_source
        with threadpool_limits(limits=1):
            input_folder,meta,a=_inputs(task['dataset'],data_root,store,source)
            X,y,F0,U,W0=[a[name] for name in ['X','y','F0','U','W0']]
            result['input_record']=str(input_folder/'representation.json')
            if task.get('profile'):
                row_count=int(task.get('profile_rows',3))
                if row_count not in [1,3]:raise ValueError('blind EnSC profile row prefix must be fixed at1 or3')
                result['profiles']=[_coefficient_graph(X,tau,store,construction_source,profile_rows=row_count) for tau in [.95,1.]]
                t=time.process_time();fit=solve(F0,W0,1000.,max_iter=30000,preconditioned=True,
                    cpu_time_limit=min(1800.,float(task.get('fit_cpu_limit',60))),time_limit=7200,return_checkpoint=True)
                result.update(status='PROFILE_ONLY_INELIGIBLE',solver_profile={'cpu_seconds':time.process_time()-t,'status':fit['status'],'iterations':fit['iterations']},evaluation='NOT_COMPUTED')
                return result
            mass0=float(sparse.triu(W0,1).sum());graphs={'W0':W0};details={'W0':{'status':'ORIGINAL_GRAPH'}}
            graphs['Wa'],details['Wa']=mass_match(a['Wa_raw'],mass0)
            coefficient_records={}
            for tau,name in [(.95,'S_tau0.95'),(1.,'S_tau1')]:
                record=_coefficient_graph(X,tau,store,construction_source);coefficient_records[name]={k:v for k,v in record.items() if k!='arrays'}
                graphs[name],details[name]=mass_match(record['arrays']['S'],mass0)
            result['coefficient_records']=coefficient_records
            target_count=graphs['S_tau0.95'].nnz//2
            wider,info=_wider_graph(F0,target_count);graphs['wider_knn'],mass=mass_match(wider,mass0);details['wider_knn']={**info,**mass}
            _,_,_,weights=graph_arrays(graphs['S_tau0.95'])
            randomized,info=_random_graph(len(F0),weights,400);graphs['random_count_mass_seed400'],mass=mass_match(randomized,mass0);details['random_count_mass_seed400']={**info,**mass}
            result['graph_objects']={name:store.put(W) for name,W in graphs.items()};result['graph_metadata']=details
            records=[];result['records']=records;verified_resume_objects=set();fit_limit=min(1800.,float(task.get('fit_cpu_limit',1800)))
            for definition in result['intended_configurations']:
                result['active_configuration']=definition['config_id'];path=folder/'records'/(identity(definition)+'.json')
                graph=graphs[definition['graph']]
                anchor=None if definition['anchor']=='native_spectral' else F0 if definition['anchor']=='F0' else U
                context=_resume_context(definition,graph,anchor,meta,store,source,construction_source,details.get(definition['graph'],{'status':'ORIGINAL_GRAPH'}))
                if path.exists():
                    records.append(_verify_saved_record(json.loads(path.read_text()),definition,context,store,verified_resume_objects));continue
                if graph.nnz==0:
                    record={**definition,'status':'DEGENERATE_AFFINITY','graph_objects':{'W':store.put(graph)},'resume_context':context};atomic_json(path,record);records.append(record);continue
                if definition['anchor']=='native_spectral':
                    record={**definition,**_native_spectral(graph,meta['K'],y,store,construction_source),'resume_context':context};atomic_json(path,record)
                else:
                    anchor=F0 if definition['anchor']=='F0' else U
                    solution=_solution(anchor,graph,meta,store,source,gamma=definition['gamma'],fit_cpu_limit=fit_limit)
                    record=_save_result(path,{**definition,'phase':'G4','method':definition['family'],'resume_context':context},solution,graph,anchor,y,
                                        details.get(definition['graph'],{'status':'ORIGINAL_GRAPH'}),store)
                records.append(record)
            result.pop('active_configuration',None);result['records']=records;result['selection']=_select(records)
            proposed=result['selection']['capability'].get('S_tau0.95')
            if proposed is not None:
                original=[r for r in records if r['family']=='original_ssc' and r['status']=='COMPLETED']
                result['matched_movement']=_matched_movement(proposed,original,F0,W0,meta,store,source,fit_limit)
            result['status']='COMPLETED'
    except BaseException as exc:
        result.update(status='TIMEOUT' if isinstance(exc,TimeoutError) else 'FAILED',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_PROF,0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(folder/'status.json',result)
    return result


def aggregate_ensc(artifact_root,output):
    """Collect all fixed benchmarks; incomplete four-way conclusions stay NA."""
    from .aggregate import write_csv
    from experiments.next_round.evaluate import paired
    store=ArtifactStore(artifact_root);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    by_dataset={dataset:{} for dataset in DATASETS};metadata={};coverage=[]
    for folder in sorted((store.root/'ensc_jobs').glob('*')):
        status_path=folder/'status.json'
        if not status_path.exists():continue
        status=json.loads(status_path.read_text());task=status.get('task',{})
        if task.get('profile'):continue
        dataset=task.get('dataset')
        if dataset not in DATASETS:continue
        for path in sorted((folder/'records').glob('*.json')):
            row=json.loads(path.read_text());key=row['config_id']
            if key in by_dataset[dataset]:
                old=by_dataset[dataset][key]
                if old.get('objects',{}).get('G')!=row.get('objects',{}).get('G') or old.get('trials')!=row.get('trials'):
                    raise ValueError('distinct repeated G4 scientific outputs require separate labelled source tracks')
            else:by_dataset[dataset][key]=row
        metadata[dataset]=status
    selections=[];contrasts=[];dataset_status=[]
    for dataset in DATASETS:
        records=list(by_dataset[dataset].values());selected=_select(records)
        for definition in intended_configurations(dataset):
            record=by_dataset[dataset].get(definition['config_id'])
            coverage.append({**definition,'status':record['status'] if record else 'NOT_RUN_TASK_OR_BUDGET',
                             'certified':record.get('solver',{}).get('certified') if record else None})
        for family,row in selected['capability'].items():
            selections.append({'dataset':dataset,'family':family,'track':'label_assisted_capability',
                'config_id':row['config_id'],'gamma':row['gamma'],
                **{k:v for k,v in row['summary'].items() if k!='native_best'},
                'certified':row.get('solver',{}).get('certified'),'solver_status':row.get('solver',{}).get('status'),
                'qualification':'Same fixed data and paired rounding; ACC/NMI selected within a frozen named family'})
        operating=selected['locked_label_free_operating_point']
        if operating and operating['status']=='COMPLETED':
            selections.append({'dataset':dataset,'family':'S_tau0.95','track':'locked_label_free_gamma1',
                'config_id':operating['config_id'],'gamma':1.,**{k:v for k,v in operating['summary'].items() if k!='native_best'},
                'certified':operating['solver'].get('certified'),'solver_status':operating['solver'].get('status'),
                'qualification':'Fixed tau0.95/source50/SSCgamma1; no label-based parameter choice'})
        proposed=selected['capability'].get('S_tau0.95');sc=selected['capability'].get('fair_sc');ssc=selected['capability'].get('original_ssc')
        qualified=selected['qualified_for_four_benchmark_claim'] and all(v is not None for v in [proposed,sc,ssc])
        summary={'dataset':dataset,'qualified':qualified,'comparison_status':selected['comparison_validity'],
                 'complete_records':sum(r['status']=='COMPLETED' for r in records),'intended_records':44,
                 'missing_required_configurations':selected['missing_required_configurations'],'invalid_required_configurations':selected['invalid_required_configurations'],
                 'ACC_gain_vs_stronger_fair_baseline_pp':None,'NMI_gain_vs_SC_pp':None,'NMI_gain_vs_SSC_pp':None}
        if all(v is not None for v in [proposed,sc,ssc]):
            summary.update(ACC_gain_vs_stronger_fair_baseline_pp=proposed['acc_mean']-max(sc['acc_mean'],ssc['acc_mean']),
                           NMI_gain_vs_SC_pp=proposed['nmi_mean']-sc['nmi_mean'],NMI_gain_vs_SSC_pp=proposed['nmi_mean']-ssc['nmi_mean'])
            summary['ACC_loss_exceeds_1pp']=summary['ACC_gain_vs_stronger_fair_baseline_pp'] < -1.
        for track,new in [('capability',proposed),('locked_label_free_gamma1',operating)]:
            if new is None or new['status']!='COMPLETED':continue
            for control_name in ['fair_sc','original_ssc','native_ensc_S_tau0.95','Wa','S_tau1','wider_knn','random_count_mass_seed400']:
                old=selected['capability'].get(control_name)
                if old is None:continue
                for metric in ['acc','nmi']:
                    contrasts.append({'dataset':dataset,'track':track,'new_config_id':new['config_id'],'control':control_name,
                        'control_config_id':old['config_id'],'metric':metric,**paired(new['trials'],old['trials'],metric),
                        'qualification':'Conditional paired-rounding interval; capability selection used these same seeds, so this is not an unbiased interval for selection/generalization'})
        dataset_status.append(summary)
    complete=all(r['qualified'] for r in dataset_status)
    macro={'status':'COMPLETE_CERTIFIED_FOUR_BENCHMARKS' if complete else 'INCOMPLETE_FOUR_BENCHMARK_COMPARISON',
           'four_benchmark_ACC_gain_pp':None,'four_benchmark_NMI_gain_vs_SC_pp':None,'four_benchmark_NMI_gain_vs_SSC_pp':None,
           'practical_target_met':None,'dataset_status':dataset_status,'primary_family':'S_tau0.95',
           'equal_dataset_weights':True,'datasets':list(DATASETS),'same_development_and_confirmation_benchmarks_seen_during_design':True}
    if complete:
        macro.update(four_benchmark_ACC_gain_pp=float(np.mean([r['ACC_gain_vs_stronger_fair_baseline_pp'] for r in dataset_status])),
                     four_benchmark_NMI_gain_vs_SC_pp=float(np.mean([r['NMI_gain_vs_SC_pp'] for r in dataset_status])),
                     four_benchmark_NMI_gain_vs_SSC_pp=float(np.mean([r['NMI_gain_vs_SSC_pp'] for r in dataset_status])))
        macro['practical_target_met']=(macro['four_benchmark_ACC_gain_pp']>=2 and macro['four_benchmark_NMI_gain_vs_SC_pp']>=0 and macro['four_benchmark_NMI_gain_vs_SSC_pp']>=0)
    write_csv(out/'ensc_execution_coverage.csv',coverage);write_csv(out/'ensc_capability_and_operating_point.csv',selections)
    write_csv(out/'ensc_paired_contrasts.csv',contrasts);atomic_json(out/'ensc_four_benchmark_conclusion.json',macro)
    return macro
