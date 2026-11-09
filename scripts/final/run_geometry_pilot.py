"""Prerequisite geometry diagnostics, not a heat+SSC performance experiment."""
from pathlib import Path
import csv,json,time,hashlib
import numpy as np
from scipy import sparse,linalg
from scipy.sparse.linalg import eigsh
from threadpoolctl import threadpool_limits
from SSC_method.graph_construction import symmetric_normalized_laplacian,knn_affinity
from SSC_method.spectral_embedding import smallest_eigenpairs
from method_extension.next_round.certified_solver import graph_arrays
from method_extension.next_round.heat_geometry import project_heat
from experiments.next_round.campaign import CACHE,OUT,PRIMARY,dump

def norm2(M):
    if M.shape[0]<=800:return float(np.linalg.norm(M.toarray() if sparse.issparse(M) else M,2))
    return float(abs(eigsh(sparse.csr_matrix(M),k=1,which='LM',v0=np.random.default_rng(20261108).normal(size=M.shape[0]),return_eigenvectors=False)[0]))
def edges(W):
    _,i,j,_=graph_arrays(W);return set(zip(i.tolist(),j.tolist()))
def main():
    start=time.process_time();rows=[]
    with threadpool_limits(limits=1):
        for dataset in PRIMARY:
            folder=CACHE/(dataset+'__Y0');meta=json.loads((folder/'meta.json').read_text());A=sparse.load_npz(folder/'A.npz');L=symmetric_normalized_laplacian(A);K=meta['K'];values,raw,_=smallest_eigenpairs(L,K+1);F=raw[:,:K];Z,R=project_heat(L,t=4,r=128,seed=20261108);Wz,_=knn_affinity(Z,k=5);Wf,_=knn_affinity(F,k=5);ef,ez=edges(Wf),edges(Wz);B,i,j,w=graph_arrays(A)
            rng=np.random.default_rng(20261108);pi=rng.integers(0,len(F),4096);pj=rng.integers(0,len(F),4096);pj=np.where(pi==pj,(pj+1)%len(F),pj);baseF=np.sum((F[pi]-F[pj])**2,axis=1);baseZ=np.sum((Z[pi]-Z[pj])**2,axis=1)
            H=Kt=None
            if len(F)<=800:
                ev,U=linalg.eigh(L.toarray());H=(U*np.exp(-2*ev))@U.T;Kt=H@H.T
            for seed in range(200,210):
                factors=np.random.default_rng(seed).uniform(-1,1,len(w))
                for eta in [.01,.05]:
                    wp=w*(1+eta*factors);Ap=sparse.coo_matrix((np.r_[wp,wp],(np.r_[i,j],np.r_[j,i])),shape=A.shape).tocsr();Lp=symmetric_normalized_laplacian(Ap);eps=norm2(L-Lp);vp,Up,_=smallest_eigenpairs(Lp,K+1);Fp=Up[:,:K];Zp,_=project_heat(Lp,t=4,r=128,R=R);Wfp,_=knn_affinity(Fp,k=5);Wzp,_=knn_affinity(Zp,k=5);efp,ezp=edges(Wfp),edges(Wzp)
                    row={'dataset':dataset,'eta':eta,'perturbation_seed':seed,'cutoff_eigengap':float(values[K]-values[K-1]),'L_operator_change':eps,'raw_subspace_max_angle_degrees':float(np.rad2deg(linalg.subspace_angles(F,Fp)).max()),'F_pair_squared_distance_change_mean':float(np.mean(abs(baseF-np.sum((Fp[pi]-Fp[pj])**2,axis=1)))),'projected_heat_pair_squared_distance_change_mean':float(np.mean(abs(baseZ-np.sum((Zp[pi]-Zp[pj])**2,axis=1)))),'F_knn_Jaccard':len(ef&efp)/max(1,len(ef|efp)),'projected_heat_knn_Jaccard':len(ez&ezp)/max(1,len(ez|ezp)),'t':4,'r':128,'projection_seed':20261108,'scope':'geometry prerequisite pilot, not a performance claim'}
                    if H is not None:
                        ep,U=linalg.eigh(Lp.toarray());Hp=(U*np.exp(-2*ep))@U.T;Kp=Hp@Hp.T;change=norm2(Kt-Kp);exact=np.sum((H[pi]-H[pj])**2,axis=1);row.update(exact_kernel_operator_change=change,exact_kernel_bound=4*eps,exact_bound_verified=change<=4*eps+1e-10,projected_pair_relative_error_median=float(np.median(abs(baseZ-exact)/np.maximum(exact,np.finfo(float).eps))))
                        if not row['exact_bound_verified']:raise AssertionError(row)
                    rows.append(row)
            print('GEOMETRY_PILOT',dataset,'gap',float(values[K]-values[K-1]),flush=True)
    keys=list(dict.fromkeys(k for r in rows for k in r));p=OUT/'geometry_pilot.csv'
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    dump(OUT/'geometry_pilot_summary.json',{'rows':len(rows),'cpu_seconds':time.process_time()-start,'scope':'No clustering benefit is inferred from this operator/topology pilot. Full N2 ablations remain conditional.','datasets':{d:{k:float(np.mean([r[k] for r in rows if r['dataset']==d])) for k in ['raw_subspace_max_angle_degrees','F_knn_Jaccard','projected_heat_knn_Jaccard']} for d in PRIMARY}})
if __name__=='__main__':main()
