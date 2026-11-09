"""Audit the 88 analytic-region claims against explicitly supplied persisted arrays."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy import sparse
from method_extension.next_round.certified_solver import graph_arrays,objective,certificate,threshold,solve

ROOT=Path(__file__).resolve().parents[2]
def load_sparse(path):
    d=np.load(path);return sparse.csr_matrix((d['data'],d['indices'],d['indptr']),shape=tuple(d['shape']))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True);args=ap.parse_args()
    rows=list(csv.DictReader((ROOT/'results/v3_theory/all_configurations.csv').open()));out=[]
    for row in rows:
        if row['optimality_status']!='OPTIMALITY_VERIFIED':continue
        folder=args.cache/(row['dataset_id']+'__'+row['prep']);F=np.load(folder/'F.npy');W=load_sparse(folder/'weights/W_k5.npz');a=np.ones(len(F))
        mapping={'control_degree_matched':'degree_matched','control_edge_budget_random':'edge_random','control_mass_matched_random':'mass_random'}
        if row['name'] in mapping:W=load_sparse(folder/'weights'/(mapping[row['name']]+'.npz'))
        if row['extension']=='X4_refit_F':
            k=row['name'].rsplit('_',1)[-1];F=np.load(folder/('F_k'+k+'.npy'));W=load_sparse(folder/'weights'/('refit_k_'+k+'.npz'))
        B,_,_,w=graph_arrays(W);gamma=float(row['gamma']);diff=B@F;norm=np.linalg.norm(diff,axis=1);unit=np.divide(diff,norm[:,None],out=np.zeros_like(diff),where=norm[:,None]>0);q=2*gamma*w[:,None]*unit
        cert=certificate(q,F,B,2*gamma*w,a=a);analytic=gamma<=threshold(F,W)['gamma0']
        solver_cpu=0.
        if not analytic:
            fitted=solve(F,W,gamma,time_limit=600);cert={'dual':fitted['dual'],'node_violation':fitted['node_violation'],'edge_violation':fitted['edge_violation']};solver_cpu=fitted['cpu_seconds']
        P=float(row['objective']);gap=(P-cert['dual'])/max(1,abs(P),abs(cert['dual']))
        new=('ANALYTIC_G_EQUALS_F' if row['extension']=='X1' and analytic else 'RECORDED_OBJECTIVE_GAP_CERTIFIED') if -1e-9<=gap<=1e-5 and max(cert['node_violation'],cert['edge_violation'])<=1e-8 else 'LEGACY_RETURNED_ITERATE_UNCERTIFIED'
        out.append({'job_id':row['job_id'],'legacy_status':row['optimality_status'],'current_audit_status':new,'primal':P,'dual':cert['dual'],'gap':gap,'edge_violation':cert['edge_violation'],'node_violation':cert['node_violation'],'persisted_F_sha256':hashlib.sha256(F.tobytes()).hexdigest(),'cpu_seconds':solver_cpu,'analytic_F_is_optimal':analytic,'returned_G_array_available':False,'claim_scope':'Persisted theory F/W; X1 analytic outputs are F. Other certification uses the recorded primal scalar, not reevaluation of an unavailable historical G.'})
    dest=ROOT/'results/next_round/legacy_certificate_audit.csv'
    with dest.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print({s:sum(r['current_audit_status']==s for r in out) for s in sorted({r['current_audit_status'] for r in out})})
if __name__=='__main__':main()
