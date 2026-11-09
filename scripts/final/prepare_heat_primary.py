"""Prepare the already specified N2 primary ablation after the geometry pilot.

No labels enter feature construction or gamma calibration. Labels are copied only
for the separate evaluator. All four benchmarks are retained.
"""
from pathlib import Path
import json,time,subprocess,shutil
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import expm_multiply
from threadpoolctl import threadpool_limits
from SSC_method.graph_construction import symmetric_normalized_laplacian,knn_affinity
from SSC_method.spectral_embedding import smallest_eigenpairs
from method_extension.next_round.heat_geometry import project_heat
from method_extension.next_round.certified_solver import threshold
from experiments.next_round.campaign import ROOT,CACHE,OUT,PRIMARY,dump,ident,filehash
from experiments.v3_reproduction.provenance import sha256_array,source_fingerprint,environment_record

def main():
    start=time.process_time();tasks=[];records=[]
    with threadpool_limits(limits=1):
        for dataset in PRIMARY:
            folder=CACHE/(dataset+'__Y0');meta=json.loads((folder/'meta.json').read_text());F0=np.load(folder/'F.npy');y=np.load(folder/'y.npy');W0=sparse.load_npz(folder/'W.npz');A=sparse.load_npz(folder/'A.npz');L=symmetric_normalized_laplacian(A);r=min(128,len(F0)-1)
            hard_values,hard,_=smallest_eigenpairs(L,r);heat,R=project_heat(L,t=4,r=128,seed=20261108);Wh,_=knn_affinity(heat,k=5);Wr,_=knn_affinity(hard,k=5)
            # Exact full-spectrum kernel entries on a fixed subset, never a truncated eigensum.
            rng=np.random.default_rng(20261108);subset=np.sort(rng.choice(len(F0),min(128,len(F0)),replace=False));E=np.zeros((len(F0),len(subset)));E[subset,np.arange(len(subset))]=1
            columns=expm_multiply(-4*L,E);Kss=columns[subset];D=np.maximum(0,np.diag(Kss)[:,None]+np.diag(Kss)[None,:]-2*Kss);Dz=np.sum((heat[subset,None,:]-heat[None,subset,:])**2,axis=2);mask=np.triu(np.ones(D.shape,bool),1);rel=abs(Dz[mask]-D[mask])/np.maximum(D[mask],1e-15)
            exact_nn=np.argsort(D+np.eye(len(subset))*1e10,axis=1)[:,:5];proj_nn=np.argsort(Dz+np.eye(len(subset))*1e10,axis=1)[:,:5]
            approximation={'fixed_subset_seed':20261108,'subset_size':len(subset),'exact_reference':'selected columns of exp(-4L), full spectrum','squared_distance_relative_error_median':float(np.median(rel)),'squared_distance_relative_error_p95':float(np.quantile(rel,.95)),'restricted_candidate_knn_recall':float(np.mean([len(set(a)&set(b))/5 for a,b in zip(exact_nn,proj_nn)])),'limit':'Restricted candidate-set overlap is not full-graph exact kNN recall; r=128 has no uniform empirical guarantee.'}
            dump(OUT/('heat_approximation_'+dataset+'.json'),approximation)
            modes=[('N2_hard128',hard,Wr),('N2_heat_t4_r128',heat,Wh),('N2_W_only_heat',F0,Wh)]
            # Original gamma=1 is a reused, explicitly linked A control. Its own-threshold point is new.
            t=threshold(F0,W0);tasks.append({'phase':'N2_primary','dataset':dataset,'prep':'Y0','kind':'original','gamma':2*t['gamma0'],'parameter_role':'own_2gamma0'})
            for mode,F,W in modes:
                target=CACHE/(dataset+'__'+mode);target.mkdir(parents=True,exist_ok=True)
                np.save(target/'F.npy',F);np.save(target/'y.npy',y);sparse.save_npz(target/'W.npz',W);shutil.copy2(folder/'A.npz',target/'A.npz');t=threshold(F,W)
                if not np.isfinite(t['gamma0']):raise ValueError('Zero-TV analytic case must be recorded explicitly, not generate an infinite gamma')
                record={**meta,'prep':mode,'embedding_kind':mode,'F_shape':list(F.shape),'F_hash':sha256_array(F),'W_hash':filehash(target/'W.npz'),'gamma0':t['gamma0'],'scale':t['scale'],'A_hash':filehash(target/'A.npz'),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_hash':source_fingerprint(),'environment':environment_record(),'t':4 if 'heat' in mode else None,'r':128 if 'heat' in mode else r,'projection_seed':20261108 if 'heat' in mode else None,'primary_claim_scope':'Secondary geometry candidate, distinct from same-original-F capped-fusion goal'}
                record['original_spectral_eigenvalues']=meta.get('eigenvalues')
                if mode=='N2_hard128':record['eigenvalues']=hard_values.tolist()
                else:record.pop('eigenvalues',None)
                dump(target/'meta.json',record);records.append(record)
                for gamma,role in [(1.,'common_gamma1'),(2*t['gamma0'],'own_2gamma0')]:tasks.append({'phase':'N2_primary','dataset':dataset,'prep':mode,'kind':'original','gamma':gamma,'parameter_role':role})
            print('HEAT_PREPARED',dataset,flush=True)
    for task in tasks:task['task_id']=ident(task)
    manifest=ROOT/'configs/next_round/job_manifest.json';m=json.loads(manifest.read_text());existing={t['task_id'] for t in m['tasks']};m['tasks'].extend(t for t in tasks if t['task_id'] not in existing);m['counts']['N2_primary']=len(tasks);m['N2_trigger']='Prespecified geometry pilot observed eigenspace/topology sensitivity and higher projected-heat kNN overlap; this is not evidence of ACC/NMI improvement.';dump(manifest,m)
    dump(OUT/'heat_primary_representation_manifest.json',records);dump(OUT/'heat_primary_preparation_usage.json',{'cpu_seconds':time.process_time()-start,'tasks':len(tasks),'new_parameters_selected_using_labels':False})
if __name__=='__main__':main()
