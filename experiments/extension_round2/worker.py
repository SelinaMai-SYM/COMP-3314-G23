"""Bounded numerical tasks. Labels are accessed only by the evaluation task."""
from __future__ import annotations
import argparse,json,time,traceback
import numpy as np
from scipy import linalg
from SSC_method.graph_construction import symmetric_normalized_laplacian
from .common import *
from .calibration import MovementPath
from method_extension.extension_round2.graph_repair import auxiliary_band,GraphRepair


def endpoint_path(store,definition,rho=None):
    key=identity({**definition,'rho':rho});return store.root/'endpoints'/f'{key}.json'

def freeze_endpoint(store,definition,outcome,result=None,*,rho=None):
    path=endpoint_path(store,definition,rho)
    if path.exists():return load_record(path)
    record={**definition,'point_id':path.stem,'rho':rho,'outcome':outcome,'result':store.put(put_arrays(store,result)) if result is not None else outcome.get('fit'),'fitting_used_labels':False,'rounding_input':'G directly, without output normalization'}
    atomic_json(path,record);return record

def graph_name(task):return task.get('variant','default')

def task_run(task,config_path,artifact_root):
    spec,lock,store=locked(artifact_root,config_path);b=task['benchmark'];entry=lock['cohorts'][b];H=store.get(entry['objects']['H']);W=store.get(entry['objects']['W0']);kind=task['kind'];started=time.process_time()
    definition={'benchmark':b,'method':task.get('method',kind),'variant':graph_name(task),'parameters':task.get('parameters',{}),'source_fingerprint':lock['source_fingerprint'],'protocol_sha256':lock['protocol_sha256'],'H_sha256':entry['objects']['H']['sha256'],'W_sha256':entry['objects']['W0']['sha256']}
    if kind=='aux':
        path=store.root/'auxiliary'/f'{b}.json'
        if path.exists():return load_record(path)
        U0=store.get(entry['objects']['U0']);Z,diagnostics=auxiliary_band(symmetric_normalized_laplacian(store.get(entry['objects']['A'])),U0,entry['K']);diagnostics['CPU_seconds']=time.process_time()-started
        record={'objects':{'Z_aux':store.put(Z)},'diagnostics':diagnostics,'source_fingerprint':lock['source_fingerprint']};atomic_json(path,record);return record
    if kind=='graph_controls':
        variations=[{'variant':f'perm{s}','permutation_seed':s,'beta':1.} for s in [400,401,402]]
        if b in ['ORL','YaleB']:variations += [{'variant':f'beta{v}','beta':v} for v in [.25,4.]]
        auxiliary=load_record(store.root/'auxiliary'/f'{b}.json');prepared=load_record(store.root/'graph_inputs'/f'{b}.json');model=None;outputs=[]
        if auxiliary and auxiliary['diagnostics']['qualified'] and prepared:
            fixed={k:store.get(prepared[k]) for k in ['a','r','d']};fixed.update(C=prepared['C'],a_info=prepared['a_info']);primary=load_record(store.root/'graphs'/f'{b}--default.json');warm=get_arrays(store,store.get(primary['state'])) if primary and primary.get('state') else None
            if warm is not None and ('QP_y' not in warm or warm['QP_y'] is None):warm=None
            model=GraphRepair(H,W,store.get(auxiliary['objects']['Z_aux']),edges=store.get(prepared['edges']),fixed=fixed,warm=warm)
        for variant in variations:
            path=store.root/'graphs'/f"{b}--{variant['variant']}.json"
            if path.exists():outputs.append(load_record(path));continue
            if model is None:record={'W':entry['objects']['W0'],'diagnostics':{'eligible':False,'status':'AUXILIARY_BAND_UNAVAILABLE'},'definition':{**definition,**variant}}
            else:
                result,diagnostics,arrays=model.fit(beta=variant['beta'],permutation_seed=variant.get('permutation_seed'),cpu_limit=570.)
                record={'W':store.put(result),'diagnostics':diagnostics,'state':store.put(put_arrays(store,arrays)),'definition':{**definition,**variant},'auxiliary_Z':auxiliary['objects']['Z_aux'],'fixed_graph_inputs_sha256':digest(store.root/'graph_inputs'/f'{b}.json'),'QP_structure_reused':True}
            atomic_json(path,record);outputs.append(record)
        return outputs
    if kind=='graph':
        path=store.root/'graphs'/f'{b}--{graph_name(task)}.json'
        if path.exists():return load_record(path)
        auxiliary=load_record(store.root/'auxiliary'/f'{b}.json')
        if not auxiliary or not auxiliary['diagnostics']['qualified']:
            record={'W':entry['objects']['W0'],'diagnostics':{'eligible':False,'status':'AUXILIARY_BAND_UNAVAILABLE'},'definition':definition}
        else:
            Z=store.get(auxiliary['objects']['Z_aux']);base=store.root/'graph_inputs'/f'{b}.json';prepared=load_record(base)
            edges=store.get(prepared['edges']) if prepared else None;model=GraphRepair(H,W,Z,edges=edges)
            if not prepared:atomic_json(base,{'edges':store.put(model.edges),'a':store.put(model.a),'a_info':model.a_info,'r':store.put(model.r),'d':store.put(model.d),'C':model.C})
            # Reuse one QP structure across beta / row-permutation settings when
            # they are submitted together; standalone tasks retain that structure.
            result,diagnostics,arrays=model.fit(beta=task.get('beta',1.),permutation_seed=task.get('permutation_seed'),cpu_limit=max(1.,570-(time.process_time()-started)))
            record={'W':store.put(result),'diagnostics':diagnostics,'state':store.put(put_arrays(store,arrays)),'definition':definition,'auxiliary_Z':auxiliary['objects']['Z_aux']}
        atomic_json(path,record);return record
    if kind=='path':
        graph_status=None
        if task['method']=='E4':
            graph=load_record(store.root/'graphs'/f'{b}--{graph_name(task)}.json')
            if graph is None:raise ValueError('E4 requires frozen graph task')
            W=store.get(graph['W']);definition['W_sha256']=graph['W']['sha256'];graph_status=graph['diagnostics']
        key=b+'--'+task['method']+'--'+graph_name(task);path=MovementPath(H,W,task['method'],task.get('parameters',{}),store,key,task['cpu_allowance']-10,definition)
        outputs=[]
        for rho in task['targets']:
            target=endpoint_path(store,definition,rho)
            if target.exists():outputs.append(load_record(target));continue
            outcome=path.target(rho)
            if graph_status is not None:
                outcome['graph_eligible']=graph_status['eligible'];outcome['graph_status']=graph_status['status']
                if not graph_status['eligible']:outcome['status']='E4_GRAPH_FALLBACK_'+outcome['status'];outcome['matched']=False
            outputs.append(freeze_endpoint(store,definition,outcome,rho=rho))
        return outputs
    if kind in ['SC','historical','SSC_reference','old_E1_reference']:
        path=endpoint_path(store,definition)
        if path.exists():return load_record(path)
        if kind=='SC':
            result={'G':H.copy(),'certified':None,'movement':0.,'relative_gap':None,'primal':None,'dual':None,'stable_gap':None,'CPU_seconds':time.process_time()-started};status='REFERENCE_COMPLETE'
        else:
            from method_extension.extension_verification.convex import Problem,solve
            problem=Problem(H,W,entry['gamma_effective'],kind='relative' if kind=='old_E1_reference' else 'ssc',eta=.25)
            if kind=='historical':
                import SSC_method.optimizer as optimizer
                from experiments.submission_refresh.core import install_cpu_limit
                latest={'G':H.copy(),'iterations':0};original=optimizer.solve_spd_system
                def observed(*args,**kwargs):
                    G=original(*args,**kwargs);latest['G']=G;latest['iterations']+=1
                    if latest['iterations']==1 or latest['iterations']%10==0:atomic_json(store.root/'reference_checkpoints'/f'{b}--historical.json',{'G':store.put(G),'iterations':latest['iterations'],'definition':definition})
                    return G
                optimizer.solve_spd_system=observed;install_cpu_limit(max(1.,565-(time.process_time()-started)));status='REFERENCE_COMPLETE'
                try:fit=optimizer.shrink_embedding(H,W,entry['gamma_nominal'],variant=entry['variant'],max_iter=300,tol=1e-6,eps=1e-8);G=fit.G;iterations=fit.n_iterations
                except TimeoutError:G=latest['G'];iterations=latest['iterations'];status='TIMEOUT_FINITE_REFERENCE'
                finally:
                    import signal
                    signal.setitimer(signal.ITIMER_PROF,0);optimizer.solve_spd_system=original
                d=problem.B@G;length=np.linalg.norm(d,axis=1);q=problem.c[:,None]*np.divide(d,length[:,None],out=np.zeros_like(d),where=length[:,None]>0);dual=problem.dual(q,repair=True);P=problem.primal(G);gap=P-dual['dual'];relative=gap/max(1.,abs(P),abs(dual['dual']))
                result={'G':G,'q':dual['q'],'p':dual['p'],'primal':P,'dual':dual['dual'],'stable_gap':gap,'relative_gap':relative,'certified':bool(gap>=0 and relative<=1e-5 and max([v for k,v in dual.items() if k.endswith('violation')],default=0)<=1e-8),'iterations':iterations,'certificate_tolerance':1e-5,'historical_variant':entry['variant'],'nominal_gamma':entry['gamma_nominal'],'effective_gamma':entry['gamma_effective']}
            else:
                def checkpoint(value):save_continuation(store.root/'reference_checkpoints'/f'{b}--{kind}',{'state':value,'definition':definition})
                raw=solve(problem,max_iter=200000,cpu_limit=max(1.,565-(time.process_time()-started)),checkpoint_callback=checkpoint);G=raw['G'];result=raw;result['stable_gap']=raw['absolute_gap'];result['certificate_tolerance']=1e-5;status='REFERENCE_CERTIFIED' if raw['certified'] else 'REFERENCE_UNCERTIFIED'
            result['movement']=float(linalg.norm(G-H)/linalg.norm(H-H.mean(axis=0))) if linalg.norm(H-H.mean(axis=0))>0 else 0.;result['CPU_seconds']=time.process_time()-started
        return freeze_endpoint(store,definition,{'status':status,'matched':None,'certified':result['certified']},result)
    if kind=='evaluate':
        # Evaluator is the only task which loads labels.
        from experiments.subset_search.runner import round_embedding
        from experiments.submission_refresh.selection import summarize
        endpoint=load_record(Path(task['endpoint']));target=store.root/'evaluations'/f"{endpoint['point_id']}.json"
        if target.exists():return load_record(target)
        result=get_arrays(store,store.get(endpoint['result']));G=result['G'];truth=store.get(entry['objects']['labels']);trials,pred,centers=round_embedding(G,truth,entry['K'],entry['initialization'],range(50));summary=summarize(trials,objective='inertia')
        record={'point_id':endpoint['point_id'],'benchmark':b,'trials':trials,'summary':summary,'predictions':store.put(pred),'centers':store.put(centers),'CPU_seconds':time.process_time()-started,'initialization':entry['initialization'],'scope':'Conditional rounding variability on a retrospectively locked cohort'};atomic_json(target,record);return record
    raise ValueError('unknown task kind')


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--config',required=True);p.add_argument('--artifact-root',required=True);args=p.parse_args();task=json.loads(Path(args.task).read_text());value=task_run(task,args.config,args.artifact_root);print(json.dumps({'completed':task['kind'],'benchmark':task['benchmark']}),flush=True)
if __name__=='__main__':main()
