"""Thin LDA adapters used by the shared submission-refresh resource scheduler.

Fitting receives X, K and an external seed, never y. This module does not
schedule workers or own a second artifact store. The caller saves every array
in the state through the campaign's content-addressed artifact mechanism.
"""
from __future__ import annotations
import numpy as np
from baselines.lda_kmeans import (fit_state,fit_reference_state,fit_adapted_state,
                                  prepare_pca,trajectory_prefix_matches)
from SSC_method.spectral_embedding import spectral_embedding
from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,GREEDY

LIMITS=(30,100,300)


def fit_trial(X: np.ndarray,K: int,seed: int,*,implementation: str,max_iter: int=300,
              prepared: dict | None=None,retain_trajectory: bool=True) -> dict:
    """Return one externally seeded full fit and all available diagnostic state."""
    if implementation == 'existing':
        return fit_state(X,K,seed,n_components=K-1,max_iter=max_iter,
                         failure_policy='record',retain_trajectory=retain_trajectory)
    if implementation == 'clustpy_pinned':
        return fit_reference_state(X,K,seed,max_iter=max_iter,retain_trajectory=retain_trajectory)
    if implementation == 'pca_ridge_adapted':
        return fit_adapted_state(X,K,seed,max_iter=max_iter,prepared=prepared,
                                 retain_trajectory=retain_trajectory)
    raise ValueError(f'Unknown LDA implementation: {implementation}')


def audit_limits(X: np.ndarray,K: int,seed: int) -> dict:
    """Execute and compare limits independently before allowing prefix reuse.

    The legacy implementation reuses the same integer K-means seed at each
    update and full-SVD PCA consumes no randomness. Equality of every retained
    projection/label/center/objective verifies the actual trajectory, rather
    than assuming that a later run has the same prefix.
    """
    fits={limit:fit_trial(X,K,seed,implementation='existing',max_iter=limit) for limit in LIMITS}
    checks={f'{a}_within_{b}':trajectory_prefix_matches(fits[a],fits[b])
            for a,b in [(30,100),(30,300),(100,300)]}
    return {'fits':fits,'prefix_checks':checks,'prefix_reuse_verified':all(checks.values()),
            'seed':seed,'native_best_of_50_status':'UNAVAILABLE_CROSS_SUBSPACE_OBJECTIVE',
            'cpu_seconds':sum(f['cpu_seconds'] for f in fits.values())}


def prepare_controls(X: np.ndarray,K: int) -> dict:
    """Prepare seed-independent raw/PCA SC controls for the adapted pipeline."""
    pca=prepare_pca(X,K)
    if pca['status']!='PREPARED':
        return {'status':'DEGENERATE_INPUT','pca':pca}
    coordinates={'raw_sc':np.asarray(X,dtype=np.float64),
                 'pca_p0_sc':pca['coordinates'],
                 'pca_r_sc':pca['coordinates'][:,:pca['r']]}
    controls={}
    for name,Z in coordinates.items():
        F,info=spectral_embedding(Z,K)
        controls[name]={'input_representation':Z,'F':F,'spectral_info':info}
    return {'status':'PREPARED','pca':pca,'controls':controls}


def adapted_trial_with_sc(X: np.ndarray,K: int,seed: int,*,prepared: dict | None=None,
                           initialization: str=GREEDY) -> dict:
    """Fit exactly one learned representation and one paired downstream SC run.

    There are fifty external calls in a reportable configuration. This function
    deliberately does not nest fifty rounding runs inside each learned fit.
    """
    controls=prepare_controls(X,K) if prepared is None else prepared
    if controls['status']!='PREPARED':
        return {'status':'DEGENERATE_INPUT','prepared':controls}
    state=fit_adapted_state(X,K,seed,prepared=controls['pca'])
    if state['termination_reason'] in ['DEGENERATE_INPUT','LDA_UPDATE_FAILED']:
        return {'status':state['termination_reason'],'fit':state}
    F,info=spectral_embedding(state['representation'],K)
    rounding=fit_lloyd(F,K,seed,initialization)
    control_roundings={name:fit_lloyd(value['F'],K,seed,initialization)
                       for name,value in controls['controls'].items()}
    return {'status':state['termination_reason'],'fit':state,'F':F,'spectral_info':info,
            'rounding':rounding,'control_roundings':control_roundings,
            'initialization':initialization,'external_seed':seed,'nested_rounding_repetitions':1}


def _pack_arrays(value,store):
    """Keep nested trajectory matrices and mutable RNG states recoverable."""
    if isinstance(value,np.ndarray):
        return {'__artifact__':store.put(value)}
    if isinstance(value,dict):
        return {key:_pack_arrays(item,store) for key,item in value.items()}
    if isinstance(value,(list,tuple)):
        return [_pack_arrays(item,store) for item in value]
    return value


def run_block(task,X,y,K,store,folder,source):
    """Run or resume a seeded LDA baseline block.

    Every external seed has its own final checkpoint. Failures are retained and
    disqualify the corresponding complete configuration. Fifty independent
    learned representations are fifty fits with one paired downstream rounding,
    never a nested fifty-by-fifty experiment. Resource limits belong to the
    calling worker and remain active while this function runs.
    """
    import json,time,traceback
    from .core import atomic_json
    from .selection import summarize
    from SSC_method.graph_construction import knn_affinity
    from experiments.v2_kmeans_protocol.metrics import evaluate_partition
    from experiments.v2_kmeans_protocol.kmeans_trials import RANDOM
    folder=__import__('pathlib').Path(folder)
    block=task['block']; profile=task.get('profile',False)
    seeds=list(range(1) if profile else range(50))
    implementation={'lda_existing':'existing','lda_reference':'clustpy_pinned','lda_adapted':'pca_ridge_adapted'}[block]
    limits=([30] if profile else task.get('limits',[30,100,300])) if block=='lda_existing' else [300]
    if task.get('continue_from'):
        from .lda_continuation import adopt_fit_checkpoints
        adopt_fit_checkpoints(task,X,y,K,store,folder,source)
    prepared=prepare_pca(X,K) if block=='lda_adapted' else None
    if profile:
        # The pilot never invokes evaluation or accesses y. It is ineligible for
        # either endpoint, even if the exact same fit is subsequently repeated.
        limit=30 if block=='lda_existing' else 300
        state=fit_trial(X,K,0,implementation=implementation,max_iter=limit,
                        prepared=prepared,retain_trajectory=True)
        if block=='lda_adapted' and 'representation' in state:
            # Include the downstream SC cost, but do not round or evaluate it.
            F,info=spectral_embedding(state['representation'],K)
            extra={'F':store.put(F),'spectral_info':info}
        else:
            extra={}
        atomic_json(folder/(block+'__profile.json'),{'status':'PROFILE_ONLY_INELIGIBLE',
            'method':block,'max_iter':limit,'external_seed':0,'source':source,
            'state':_pack_arrays(state,store),'downstream':extra,
            'evaluation':'NOT_COMPUTED; no true labels enter profiling'})
        return {'status':'PROFILE_ONLY_INELIGIBLE'}
    if prepared is not None:
        atomic_json(folder/'adapted_pca.json',_pack_arrays(prepared,store))
        if prepared['status']!='PREPARED':
            atomic_json(folder/'lda_adapted.json',{'dataset':task['dataset'],'method':block,'status':'FAILED_DEGENERATE_INPUT','prepared':_pack_arrays(prepared,store)})
            return
        # All three controls are seed-independent representations with the same
        # external seed controlling only their one Lloyd rounding.
        Zs={'raw_sc':X,'pca_p0_sc':prepared['coordinates'],
            'pca_r_sc':prepared['coordinates'][:,:prepared['r']]}
        for name,Z in Zs.items():
            path=folder/(name+'.json')
            if path.exists():
                continue
            F,info=spectral_embedding(Z,K);A,_=knn_affinity(Z,k=5)
            trials,pred,centers=__import__('experiments.subset_search.runner',fromlist=['round_embedding']).round_embedding(F,y,K,RANDOM,seeds)
            atomic_json(path,{'dataset':task['dataset'],'method':name,'config_id':task['run_id']+'|'+name,
                'status':'PROFILE_ONLY_INELIGIBLE' if profile else 'COMPLETED','trials':trials,
                'summary':None if profile else summarize(trials),'spectral_info':info,
                'objects':{'input_representation':store.put(Z),'A':store.put(A),'F':store.put(F),'G':store.put(F),
                           'predictions':store.put(pred),'centers':store.put(centers)},
                'seed_protocol':'one RANDOM Lloyd start per external seed, paired with learned-fit seed',
                'row_normalization':False,'source':source})
    for limit in limits:
        trials=[];diagnostics=[];state_objects=[];failed=[];sc_trials=[];sc_objects=[]
        for seed in seeds:
            path=folder/f'state__{limit}__{seed}.json'
            if path.exists():
                saved=json.loads(path.read_text())
                if saved.get('implementation_hash')!=source['implementation_hash']:
                    adoption=saved.get('adoption',{})
                    if adoption.get('accepted_current_implementation_hash')!=source['implementation_hash'] or not adoption.get('compatibility_proof'):
                        raise ValueError('LDA continuation source mismatch')
                    store.get(adoption['compatibility_proof'])
            else:
                begin=time.process_time()
                try:
                    state=fit_trial(X,K,seed,implementation=implementation,max_iter=limit,
                                    prepared=prepared,retain_trajectory=True)
                    top_arrays={key:store.put(value) for key,value in state.items() if isinstance(value,np.ndarray)}
                    if 'labels' not in top_arrays:
                        raise ValueError('LDA returned no fitted labels: '+state.get('termination_reason','unknown'))
                    failed_update=state.get('termination_reason')=='LDA_UPDATE_FAILED'
                    saved={'seed':seed,'status':'FAILED_LDA_UPDATE' if failed_update else 'COMPLETED',
                           'diagnostics':_pack_arrays({key:value for key,value in state.items() if not isinstance(value,np.ndarray)},store),
                           'objects':top_arrays,'implementation_hash':source['implementation_hash'],
                           'cpu_seconds':time.process_time()-begin}
                except TimeoutError as exc:
                    atomic_json(path,{'seed':seed,'status':'TIMEOUT','error':repr(exc),'implementation_hash':source['implementation_hash'],
                                      'cpu_seconds':time.process_time()-begin})
                    raise
                except Exception as exc:
                    saved={'seed':seed,'status':'FAILED','error':repr(exc),'traceback':traceback.format_exc(),
                           'implementation_hash':source['implementation_hash'],'cpu_seconds':time.process_time()-begin}
                atomic_json(path,saved)
            diagnostics.append(saved.get('diagnostics',{'error':saved.get('error')}))
            if saved['status']!='COMPLETED':
                failed.append({'seed':seed,'status':saved['status'],'error':saved.get('error')})
                continue
            labels=store.get(saved['objects']['labels'])
            trials.append({'seed':seed,**evaluate_partition(y,labels)})
            state_objects.append({'seed':seed,'objects':saved['objects']})
            if block=='lda_adapted':
                scpath=folder/f'adapted_sc_seed{seed}.json'
                if scpath.exists():
                    scsaved=json.loads(scpath.read_text())
                else:
                    Z=store.get(saved['objects']['representation']);F,info=spectral_embedding(Z,K);A,_=knn_affinity(Z,k=5)
                    rounding=fit_lloyd(F,K,seed,RANDOM)
                    scsaved={'seed':seed,'scores':evaluate_partition(y,rounding['labels']),
                             'inertia':rounding['inertia'],'spectral_info':info,
                             'objects':{'A':store.put(A),'F':store.put(F),'G':store.put(F),
                                        'predictions':store.put(rounding['labels']),'centers':store.put(rounding['centers'])}}
                    atomic_json(scpath,scsaved)
                sc_trials.append({'seed':seed,**scsaved['scores']});sc_objects.append(scsaved)
        complete=len(trials)==50 and not failed and not profile
        status='COMPLETED' if complete else ('PROFILE_ONLY_INELIGIBLE' if profile else 'INCOMPLETE_FAILED_SEEDS')
        record={'dataset':task['dataset'],'method':block,'config_id':task['run_id']+f'|limit{limit}',
                'max_iter':limit,'trials':trials,'diagnostics':diagnostics,'state_objects':state_objects,
                'seed_failures':failed,'expected_seeds':seeds,'status':status,
                'summary':summarize(trials,objective=None) if complete else None,
                'native_best_status':'UNAVAILABLE_NOT_COMMON_ACROSS_LEARNED_SUBSPACES',
                'implementation':implementation,'source':source,
                'qualification':'ClustPy update failures and return-state inconsistency remain visible in per-seed diagnostics' if block=='lda_reference' else 'Learned representation fitted independently for each external seed'}
        atomic_json(folder/f'{block}__{limit}.json',record)
        if block=='lda_adapted':
            atomic_json(folder/'lda_adapted_sc.json',{'dataset':task['dataset'],'method':'lda_adapted_sc',
                'config_id':task['run_id']+'|adapted_sc','status':status,'trials':sc_trials,
                'summary':summarize(sc_trials,objective=None) if complete and len(sc_trials)==50 else None,
                'state_records':sc_objects,'seed_failures':failed,'source':source,
                'native_best_status':'UNAVAILABLE_NOT_COMMON_ACROSS_LEARNED_SUBSPACES',
                'seed_protocol':'50 learned representations, one RANDOM Lloyd rounding on each, paired external index',
                'historical_lda_sc_identity':'UNRESOLVED; explicitly adapted pipeline'})
