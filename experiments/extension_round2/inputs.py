"""Exact membership replay and one immutable shared spectral geometry per cohort."""
from __future__ import annotations
import csv,json,os,subprocess,time
from pathlib import Path
import numpy as np
from scipy import linalg
from SSC_method.graph_construction import knn_affinity,symmetric_normalized_laplacian
from SSC_method.spectral_embedding import smallest_eigenpairs
from experiments.subset_search.catalogue import materialize,_manifest
from experiments.v3_reproduction.provenance import fingerprint_matrix
from .common import *

def freeze(config_path,data_root,artifact_root):
    initialize_ledger(artifact_root);spec=config(config_path);store=ArtifactStore(artifact_root)
    if (store.root/'cohort_lock.json').exists():
        _,lock,_=locked(artifact_root,config_path)
        for row in lock['cohorts'].values():
            for ref in row['objects'].values():store.get(ref)
        return lock
    registry=json.loads((ROOT/'configs/subset_search/candidate_catalogue.json').read_text());cat=json.loads((ROOT/registry['catalogue_path']).read_text());lookup={c['candidate_id']:c for c in cat['candidates']}
    if digest(ROOT/registry['catalogue_path'])!=registry['catalogue_sha256']:raise ValueError('catalogue pointer hash mismatch')
    winners=list(csv.DictReader((ROOT/'results/subset_search/closest_matches.csv').open()));cohorts={};data_root=Path(data_root).resolve()
    base=data_root.parent/'scientific-artifacts';roots=[p for p in base.iterdir() if p.is_dir()] if base.exists() else []
    for name in ORDER:
        started=time.process_time();expected=spec['cohorts'][name];pool='adapted' if name=='MSRA50' else 'specification_compatible';rows=[r for r in winners if r['benchmark']==name and r['pool']==pool and r['endpoint']=='mean_sample_sd_50']
        if len(rows)!=1 or rows[0]['candidate_id']!=expected['candidate_id']:raise ValueError('report cohort differs: '+name)
        old=rows[0];candidate=lookup[expected['candidate_id']];manifest_path=ROOT/candidate['manifest_path'];manifest=_manifest(candidate)
        if digest(manifest_path)!=expected['manifest_sha256']:raise ValueError('membership hash mismatch')
        for key in ['initialization','prep','variant']:
            if old[key]!=expected[key]:raise ValueError('historical setting differs: '+key)
        if float(old['gamma_nominal'])!=expected['gamma_nominal'] or float(old['gamma_effective'])!=expected['gamma_effective']:raise ValueError('historical gamma differs')
        X,y,meta=materialize(candidate,data_root,verify=True);X=np.asarray(X,dtype=float);y=np.asarray(y,dtype=np.int64)
        if list(X.shape)!=[expected['n'],expected['features']] or len(np.unique(y))!=expected['K'] or fingerprint_matrix(X,y)!=json.loads(old['input_fingerprint']):raise ValueError('cohort input/shape differs')
        historical=None;reason='Required raw basis or metadata unavailable'
        for root in roots:
            path=root/'subset'/candidate['candidate_id']/'representation.json'
            if not path.exists():continue
            raw=json.loads(path.read_text());refs=raw['objects']
            if refs['F']['sha256']!=old['F_sha256']:continue
            if expected['prep'] in ['Y2','Y3']:reason='Historical F is row-normalized; raw U0 not preserved';continue
            try:
                source=ArtifactStore(root);A=source.get(refs['A']);U0=source.get(refs['F']);W=source.get(refs['W']);xold=source.get(refs['X']);yold=source.get(refs['y'])
                if not np.array_equal(X,xold) or not np.array_equal(y,yold):raise ValueError('historical array fingerprint differs')
                if linalg.norm(U0.T@U0-np.eye(expected['K']))>1e-7:raise ValueError('historical raw basis is not orthonormal')
                H=U0;spectral=raw['spectral'];Ainfo=raw['A_config'];Winfo=raw['W_config'];historical={'representation_metadata_sha256':digest(path),'reuse':'Verified historical A/U0=H/W0, exact processed X/y and report F identity'};break
            except (OSError,ValueError,KeyError):continue
        if historical is None:
            A,Ainfo=knn_affinity(X,k=5);values,U0,eigenmethod=smallest_eigenpairs(symmetric_normalized_laplacian(A),expected['K']);H=U0
            if expected['prep'] in ['Y2','Y3']:
                norms=np.linalg.norm(H,axis=1,keepdims=True);H=np.divide(H,norms,out=np.zeros_like(H),where=norms>0)
            W,Winfo=knn_affinity(H,k=5);spectral={'eigenvalues':values.tolist(),'eigen_solver':eigenmethod,'row_normalize':expected['prep'] in ['Y2','Y3']};historical={'reuse':'Fresh whole shared numerical replay of exact report cohort','reason':reason}
        L=symmetric_normalized_laplacian(A);eigenvalues=np.sum(U0*(L@U0),axis=0)
        residual=float(linalg.norm(L@U0-U0*eigenvalues));gram=float(linalg.norm(U0.T@U0-np.eye(expected['K'])))
        if gram>1e-7 or residual>1e-7:raise ValueError('invalid frozen raw spectral subspace')
        objects={k:store.put(v) for k,v in [('X',X),('labels',y),('A',A),('U0',U0),('H',H),('W0',W),('original_ids',np.asarray(manifest['selected_indices'],dtype=np.int64))]}
        cohorts[name]={**expected,'objects':objects,'source_files':manifest['source_files'],'selected_indices':manifest['selected_indices'],'input_fingerprint':fingerprint_matrix(X,y),'historical_identity':old['historical_identity'],'adaptation_flags':old['source_specification_deviations'],'historical_selection':{k:old[k] for k in ['config_id','F_sha256','G_sha256','acc_mean','acc_sd','nmi_mean','nmi_sd','scientific_source_commit','scientific_source_fingerprint']},'shared_representation_provenance':historical,'historical_H_identity_matches':objects['H']['sha256']==old['F_sha256'],'A_metadata':Ainfo,'W_metadata':Winfo,'spectral_metadata':spectral,'raw_U0_orthogonality_residual':gram,'raw_U0_eigen_residual':residual,'preparation_CPU_seconds':time.process_time()-started,'rounding_input':'G directly; no output normalization'}
        atomic_json(store.root/'inputs'/f'{name}.json',cohorts[name]);print('FROZEN',name,historical['reuse'],flush=True)
    hashes=source_files();lock={'schema':'ssc-extension-round2-cohort-lock-v1','base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_sha256':digest(config_path),'source_files':hashes,'environment':environment(),'source_fingerprint':identity({'files':hashes,'environment':environment()}),'source_snapshot':store.put({n:(ROOT/n).read_text() for n in hashes}),'cohorts':cohorts,'selection_qualification':'Conditional evaluation on retrospectively selected locked report cohorts; not unseen data','audit_files':{n:digest(ROOT/n) for n in spec['snapshot_audit']}}
    atomic_json(store.root/'cohort_lock.json',lock);atomic_json(ROOT/'configs/extension_round2/cohort_lock.json',lock);return lock
