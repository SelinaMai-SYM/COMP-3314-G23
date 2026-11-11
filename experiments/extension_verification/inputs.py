"""Freeze exact reference memberships, graph objects, comparisons and source bytes."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
import yaml
from scipy.sparse.csgraph import connected_components
from SSC_method.graph_construction import knn_affinity,symmetric_normalized_laplacian
from SSC_method.spectral_embedding import smallest_eigenpairs
from experiments.subset_search.catalogue import materialize,_manifest
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest,identity,ROOT
from method_extension.extension_verification.convex import Problem,rowunit,row_norm
from method_extension.extension_verification.comparisons import construct
from method_extension.extension_verification.relative_neighbor import triplet_hinges,random_hinges


def source_files():
    files=list((ROOT/'SSC_method').glob('*.py'))+list((ROOT/'method_extension/extension_verification').glob('*.py'))
    files += [p for p in (ROOT/'benchmarks').rglob('*.py') if not p.name.startswith('test')]
    files += [ROOT/'method_extension/next_round/certified_solver/solver.py',ROOT/'method_extension/next_round/certified_solver/__init__.py',ROOT/'experiments/subset_search/catalogue.py',ROOT/'experiments/v3_reproduction/provenance.py',ROOT/'experiments/submission_refresh/core.py',ROOT/'experiments/v2_kmeans_protocol/kmeans_trials.py',ROOT/'experiments/v2_kmeans_protocol/metrics.py',ROOT/'experiments/v2_kmeans_protocol/vanilla_kmeanspp.py']
    files += [ROOT/'experiments/extension_verification'/name for name in ['inputs.py','worker.py','evaluation.py','gates.py','statistics.py','resources.py','campaign.py']]
    if any(not p.is_file() for p in files):raise ValueError('complete campaign source is required before freezing')
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(set(files))}


def protocol(config):
    path=Path(config).resolve();value=yaml.safe_load(path.read_text());sha=digest(path);lock=ROOT/'configs/extension_verification/protocol.lock.json'
    if sha!=digest(ROOT/'configs/extension_verification/protocol.yaml'):raise ValueError('use the registered protocol bytes; an alternative design requires a separately versioned implementation')
    if lock.is_file() and json.loads(lock.read_text())['protocol_sha256']!=sha:raise ValueError('frozen protocol changed; create a new version before scoring')
    if value['version']!='ssc-refinement-verification-20261111-v1':raise ValueError('unsupported protocol version')
    return value,sha


def load_locked(config,artifact_root,*,check_code=True):
    specification,sha=protocol(config);path=ROOT/'configs/extension_verification/datasets.lock.json'
    if not path.is_file():raise ValueError('freeze reference inputs before running or evaluating')
    lock=json.loads(path.read_text())
    if lock['protocol_sha256']!=sha:raise ValueError('data/protocol identity mismatch')
    if check_code and lock['source_files']!=source_files():raise ValueError('frozen scientific code changed; retain old attempts and qualify a new source identity')
    store=ArtifactStore(artifact_root);marker=store.root/'freeze.json'
    if not marker.is_file() or json.loads(marker.read_text())['datasets_lock_sha256']!=digest(path):raise ValueError('artifact root lacks the exact frozen input registration')
    return specification,lock,store


def freeze(config,data_root,artifact_root):
    specification,sha=protocol(config);store=ArtifactStore(artifact_root);target=ROOT/'configs/extension_verification/datasets.lock.json';hashes=source_files()
    if target.exists():
        _,lock,_=load_locked(config,artifact_root)
        for entry in lock['datasets'].values():
            for source in entry['source_files']:
                if digest(Path(data_root)/source['path_relative_to_data_root'])!=source['sha256']:raise ValueError('source data changed')
            for ref in entry['objects'].values():store.get(ref)
        return lock
    catalogue=json.loads((ROOT/'results/subset_search/candidate_catalogue.json').read_text());lookup={c['candidate_id']:c for c in catalogue['candidates']};datasets={}
    snapshot=store.put({name:(ROOT/name).read_text() for name in hashes})
    environment={'python':sys.version.split()[0],'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','cvxpy','threadpoolctl']},'threads_per_worker':1}
    for benchmark in specification['inputs']['dataset_order']:
        definition=specification['inputs']['references'][benchmark];candidate=lookup[definition['candidate_id']];manifest=_manifest(candidate);X,y,meta=materialize(candidate,Path(data_root),verify=True);X=np.asarray(X,dtype=np.float64);y=np.asarray(y,dtype=np.int64)
        if list(X.shape)!=[definition['n'],definition['features']] or len(np.unique(y))!=definition['K']:raise ValueError('reference dimensions/class count differ')
        A,Ainfo=knn_affinity(X,k=5,symmetrization='union_maximum');L=symmetric_normalized_laplacian(A);values,F,eigenmethod=smallest_eigenpairs(L,definition['K'],eigen_seed=20261108);W,Winfo=knn_affinity(F,k=5,symmetrization='union_maximum');U=rowunit(F)
        ids=np.asarray(manifest['original_row_indices'],dtype=np.int64)
        comparison=construct(X,U,W,ids,spatial_shape=definition['spatial_shape']);hinges=triplet_hinges(U,comparison['triplets'])
        objects={name:store.put(value) for name,value in [('X',X),('labels',y),('original_ids',ids),('A0',A),('F0',F),('W0',W),('U',U),('triplets',comparison['triplets']),('hinge_anchors',hinges.anchors),('hinge_normals',hinges.normals),('hinge_beta',hinges.beta),('view_norms',comparison['view_norms']),('feature_view1_columns',comparison['feature_columns'][0]),('feature_view2_columns',comparison['feature_columns'][1])]}
        if comparison['neighbors']:
            objects.update(view1_neighbors=store.put(comparison['neighbors'][0]),view2_neighbors=store.put(comparison['neighbors'][1]))
        random={}
        for seed in [400,401,402]:
            system,redraws=random_hinges(U,hinges,seed,ids);random[str(seed)]={'anchors':store.put(system.anchors),'normals':store.put(system.normals),'beta':store.put(system.beta),'numerical_redraws':redraws}
        references={}
        for panel,H in [('original',F),('angular',U)]:
            force=Problem(H,W,0,kind='tangent' if panel=='angular' else 'ssc',radius=np.tan(np.deg2rad(15)) if panel=='angular' else None).reference();force.pop('q_unit_gamma');references[panel]=force
        diagnostics={**comparison['diagnostics'],'F0_zero_rows':int(np.sum(~np.any(F!=0,axis=1))),'U_zero_rows':int(np.sum(~np.any(U!=0,axis=1))),'A0_components':int(connected_components(A,directed=False)[0]),'W0_components':int(connected_components(W,directed=False)[0]),'F0_norm_range':[float(row_norm(F).min()),float(row_norm(F).max())]}
        entry={'benchmark':benchmark,**definition,'role':'development' if benchmark in ['ORL','YaleB'] else 'confirmation','historical_identity':'UNVERIFIED','sample_manifest_path':candidate['manifest_path'],'sample_manifest_sha256':candidate['manifest_sha256'],'input_fingerprint':manifest['fingerprint'],'source_files':manifest['source_files'],'original_row_ids':ids.tolist(),'source_url':manifest['source_url'],'objects':objects,'random_hinges':random,'gamma_references':references,'graph_preparation':{'A0':Ainfo,'W0':Winfo,'spectral_solver':eigenmethod,'eigenvalues':values.tolist(),'spectral_seed':20261108},'label_free_diagnostics':diagnostics,'triplet_construction_precedes_semantic_label_audit':True}
        datasets[benchmark]=entry;atomic_json(store.root/'inputs'/f'{benchmark}.json',entry)
        print('FROZEN_INPUT',benchmark,definition['candidate_id'],X.shape,diagnostics['selected_triplets'],flush=True)
    result={'schema':'ssc-refinement-input-lock-v1','protocol_sha256':sha,'source_files':hashes,'source_snapshot':snapshot,'source_fingerprint':identity(hashes),'environment':environment,'datasets':datasets}
    atomic_json(target,result);atomic_json(ROOT/'configs/extension_verification/protocol.lock.json',{'schema':'ssc-refinement-protocol-lock-v1','protocol_sha256':sha,'version':specification['version'],'definitions_frozen_before_new_scores':True})
    atomic_json(store.root/'freeze.json',{'protocol_sha256':sha,'datasets_lock_sha256':digest(target),'source_fingerprint':result['source_fingerprint'],'source_snapshot':snapshot,'input_count':8,'no_extension_scores_computed':True})
    return result
