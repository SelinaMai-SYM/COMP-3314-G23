"""New same-F/W 300-step IRLS reexecutions, never substitutes for old missing arrays."""
from pathlib import Path
import csv,json,time,signal,resource
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from SSC_method.optimizer import shrink_embedding
from method_extension.next_round.certified_solver import graph_arrays,objective,certificate
from experiments.next_round.campaign import OUT,CACHE,ARRAYS,JOBS,dump
from experiments.next_round.evaluate import evaluate

ROOT=Path(__file__).resolve().parents[2]
def main():
    jobs=[json.loads(p.read_text()) for p in JOBS.glob('*.json')];targets=[j for j in jobs if j['status']=='COMPLETED' and (j['task']['phase']=='N0_selected' or (j['task']['phase']=='A' and j['task']['gamma']==1))];rows=[];folder=ROOT/'runs/next_round/irls_audit';folder.mkdir(parents=True,exist_ok=True)
    for job in targets:
        task=job['task'];d=CACHE/(task['dataset']+'__'+task['prep']);F=np.load(d/'F.npy');W=sparse.load_npz(d/'W.npz');y=np.load(d/'y.npy');meta=json.loads((d/'meta.json').read_text());variant=task.get('legacy_variant','E8');nominal=task.get('gamma_nominal',task['gamma']);start=time.perf_counter();cpu=time.process_time()
        try:
            with threadpool_limits(limits=1):
                result=shrink_embedding(F,W,nominal,max_iter=300,tol=1e-6,eps=1e-8,variant=variant)
                B,_,_,w=graph_arrays(W);P=objective(result.patterns,F,B,2*task['gamma']*w);array=np.load(ROOT/job['array_path']);cert=certificate(array['q'],F,B,2*task['gamma']*w);D=cert['dual'];gap=(P-D)/max(1,abs(P),abs(D))
                if P<D-1e-8*max(1,abs(P),abs(D)):raise ArithmeticError('new IRLS primal below feasible dual')
                trials,pred,dist=evaluate(F,result.patterns,y,meta['K']);np.savez_compressed(folder/(job['run_id']+'.npz'),G=result.patterns,predictions=pred)
                row={'run_id':'IRLS300-'+job['run_id'],'paired_PDHG_run_id':job['run_id'],'dataset':task['dataset'],'prep':task['prep'],'variant':variant,'gamma_nominal':nominal,'gamma_effective':task['gamma'],'iterations':result.n_iterations,'iterate_converged':result.converged,'primal':P,'dual_from_paired_PDHG':D,'gap':gap,'current_status':'RECERTIFIED_NEW_IRLS_RETURNED_POINT' if gap<=1e-5 else 'ITERATE_CONVERGED_UNCERTIFIED' if result.converged else 'MAX_ITER_REACHED','PDHG_primal':job['solver']['primal'],'PDHG_gap':job['solver']['gap'],'movement':float(np.linalg.norm(result.patterns-F)/np.linalg.norm(F)),'ACC':float(np.mean([r['acc'] for r in trials])*100),'NMI':float(np.mean([r['nmi'] for r in trials])*100),'PDHG_ACC':job['scores']['acc_mean'],'PDHG_NMI':job['scores']['nmi_mean'],'F_hash':meta['F_hash'],'W_hash':meta['W_hash'],'trials':trials,'distance':dist,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-start,'status':'COMPLETED','scope':'New 300-step IRLS execution on the same new seeded F/W as PDHG, not the unavailable original baseline arrays.'}
        except BaseException as exc:row={'dataset':task['dataset'],'status':'FAILED','error':repr(exc),'cpu_seconds':time.process_time()-cpu}
        rows.append(row);dump(OUT/'irls_vs_pdhg.json',rows);print('IRLS_AUDIT',row['dataset'],task['gamma'],row.get('primal'),row.get('gap'),row.get('current_status'),flush=True)
    scalars=[{k:v for k,v in r.items() if k not in ['trials','distance']} for r in rows];fields=list(dict.fromkeys(k for r in scalars for k in r))
    with (OUT/'irls_vs_pdhg.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(scalars)
if __name__=='__main__':main()
