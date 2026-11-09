"""Exact finite-state reference for the user's five-point fusion mechanism."""
from pathlib import Path
import itertools,json,time
import numpy as np
import cvxpy as cp
from scipy import sparse
from threadpoolctl import threadpool_limits
from method_extension.next_round.certified_solver import solve,graph_arrays,certificate
from method_extension.next_round.capped_fusion import fit
from scripts.final.run_synthetic import evaluate
from experiments.next_round.campaign import OUT,dump

def main():
    start=time.process_time();F=np.array([[0.],[0.],[4.],[4.],[4.]]);truth=np.array([0,0,1,1,1]);W=np.zeros((5,5))
    for i in range(5):
        for j in range(i+1,5):W[i,j]=W[j,i]=10. if truth[i]==truth[j] else .25
    W=sparse.csr_matrix(W);B,_,_,w=graph_arrays(W);c=2*w;tau=1.;best=3.;bounds=[];states=[];pruned=0
    with threadpool_limits(limits=1):
        g=cp.Variable(5);t=cp.Variable(5);z=cp.Variable(len(w));capacity=cp.Parameter(len(w),nonneg=True);const=cp.Parameter(nonneg=True)
        constraints=[t>=g-F[:,0],t>=F[:,0]-g,z>=B@g,z>=-B@g]
        problem=cp.Problem(cp.Minimize(cp.sum(t)+capacity@z+const),constraints)
        for mask in itertools.product([0,1],repeat=len(w)):
            mask=np.array(mask);constant=float(c@(1-mask))*tau
            if constant>best+1e-10:pruned+=1;continue
            capacity.value=c*mask;const.value=constant;problem.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_feas=1e-10,tol_gap_rel=1e-10)
            q=(constraints[2].dual_value-constraints[3].dual_value)[:,None];q[mask==0]=0.;dual=certificate(q,F,B,c*mask)
            P=float(np.sum(abs(g.value-F[:,0]))+(c*mask)@abs(B@g.value)+constant);D=dual['dual']+constant;gap=(P-D)/max(1,abs(P),abs(D))
            if problem.status!='optimal' or gap>1e-7 or gap < -1e-9:raise AssertionError((mask,problem.status,P,D,gap))
            bounds.append(D);states.append({'mask':mask.tolist(),'primal':P,'dual':D,'gap':gap});best=min(best,P)
        original=solve(F,W,1.);outputs=[]
        for name,G0 in [('F',F),('original_SSC',original['G'])]:
            r=fit(F,W,1.,1.,G_init=G0);trials,_,_=evaluate(F,r['G'],truth,2);outputs.append({'initialization':name,'objective':r['objective'],'ACC':float(np.mean([t['acc'] for t in trials])*100),'NMI':float(np.mean([t['nmi'] for t in trials])*100),'G':r['G'].tolist(),'local_status':r['status'],'global_certificate_from_local_solver':r['globally_certified']})
    result={'F':F.tolist(),'class_sizes':[2,3],'distance':4,'tau':1,'total_cross_attraction_lambda':3,'within_edge_weight':10,'cross_edge_weight':.25,'original_primal':original['primal'],'original_dual':original['dual'],'original_gap':original['gap'],'capped_global_primal':best,'capped_global_dual':min(bounds),'capped_global_gap':(best-min(bounds))/max(1,abs(best)),'enumerated_states':2**len(w),'states_pruned_by_nonnegative_constant_bound':pruned,'convex_states_solved_and_certified':len(states),'starts':outputs,'state_bounds':states,'cpu_seconds':time.process_time()-start,'scope':'Global reference only for this tiny enumerated problem. All real-data capped solves remain nonconvex local outcomes.'}
    dump(OUT/'five_point_global_check.json',result);print(json.dumps({k:v for k,v in result.items() if k!='state_bounds'},indent=2))
if __name__=='__main__':main()
