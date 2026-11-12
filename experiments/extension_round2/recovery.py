"""Retain finite scientific states after external limits, without another fit."""
from __future__ import annotations
import numpy as np
from scipy import linalg
from .common import *
from .worker import freeze_endpoint,endpoint_path


def partial_fits(store,lock):
    """Keep the last recorded best pair even if final serialization was cut off."""
    output={}
    for pointer in sorted(store.root.glob('fits/*/continuation/CURRENT.json')):
        folder=pointer.parent.parent
        if (folder/'result.json').exists():continue
        definition=load_record(folder/'definition.json');context={k:v for k,v in definition.items() if k not in ['lambda','attempt']};b=definition['benchmark'];entry=lock['cohorts'][b]
        if context['source_fingerprint']!=lock['source_fingerprint'] or context['protocol_sha256']!=lock['protocol_sha256'] or context['H_sha256']!=entry['objects']['H']['sha256']:raise ValueError('partial fit identity mismatch')
        key=b+'--'+definition['method']+'--'+definition['variant'];path=load_record(store.root/'paths'/f'{key}.json');token=float(definition['lambda']).hex()
        if not path or path['attempts'].get(token)!=definition['attempt']:continue
        saved=load_record(folder/'recovered_result.json');pointer_sha=digest(pointer)
        if not saved or saved['checkpoint_pointer_sha256']!=pointer_sha:
            value=recover_continuation(pointer.parent)
            if value['context']!=context or value['lambda']!=definition['lambda'] or value['parameters']!=definition['parameters']:raise ValueError('partial fit checkpoint context differs')
            state=value['state'];best=dict(state['best'])
            if best['G'].shape!=(entry['n'],entry['K']) or not np.isfinite(best['G']).all():continue
            checkpoint={k:v for k,v in state.items() if k!='best'}
            best.update(lam=definition['lambda'],fit_id=folder.name,attempt=definition['attempt'],method=definition['method'],parameters=definition['parameters'],context=context,certified=False,stopping_reason='INTERRUPTED_CHECKPOINT',iterations=state['iteration'],CPU_seconds=state['CPU_seconds'],fit_total_CPU_seconds=state['CPU_seconds'],checkpoint=checkpoint,history=[],history_status='Only the latest checkpoint best/current states survived this interrupted attempt; completed earlier attempts retain their histories',recovery_source_sha256=digest(Path(__file__)),CPU_scope='Checkpoint call CPU only; the native receipt includes later work and controller overhead')
            saved={'object':store.put(put_arrays(store,best)),'checkpoint_pointer_sha256':pointer_sha,'recorded_mtime_ns':pointer.stat().st_mtime_ns,'additional_iterations':0};atomic_json(folder/'recovered_result.json',saved)
        output.setdefault(key,[]).append((saved['recorded_mtime_ns'],saved['object'],store.get(saved['object'])))
    return output


def _recover_finite(root,config_path):
    _,lock,store=locked(root,config_path);recovered=[]
    partial=partial_fits(store,lock)
    for file in sorted((store.root/'tasks').glob('*.json')):
        task=load_record(file);b=task['benchmark'];entry=lock['cohorts'][b];kind=task['kind']
        definition={'benchmark':b,'method':task.get('method',kind),'variant':task.get('variant','default'),'parameters':task.get('parameters',{}),'source_fingerprint':lock['source_fingerprint'],'protocol_sha256':lock['protocol_sha256'],'H_sha256':entry['objects']['H']['sha256'],'W_sha256':entry['objects']['W0']['sha256']}
        if kind=='path':
            graph=None
            if task['method']=='E4':
                graph=load_record(store.root/'graphs'/f"{b}--{definition['variant']}.json")
                if not graph:continue
                definition['W_sha256']=graph['W']['sha256']
            key=b+'--'+task['method']+'--'+definition['variant'];state=load_record(store.root/'paths'/f'{key}.json')
            if not state or not state['fits'] and not partial.get(key):continue
            unfinished=[rho for rho in task['targets'] if str(rho) not in state['targets']]
            first_unfinished=unfinished[0] if unfinished else None
            candidates=list(partial.get(key,[]))
            for ref in state['fits'].values():
                result=store.get(ref)
                if result['context']!=definition:raise ValueError('finite recovery input identity mismatch')
                path=store.root/'fits'/result['fit_id']/'result.json'
                candidates.append((path.stat().st_mtime_ns if path.exists() else 0,ref,result))
            for rho in task['targets']:
                path=endpoint_path(store,definition,rho);old=load_record(path)
                if old and old.get('result'):continue
                if old and old['outcome']['status']=='UNRUN_PATH_BUDGET':continue
                known=state['targets'].get(str(rho),{});selected=known.get('fit')
                if selected:result=store.get(selected)
                else:_,selected,result=max(candidates,key=lambda v:(v[0],v[2]['fit_id']))
                outcome={'status':'TIMEOUT_RECOVERED_LAST_FINITE','rho':rho,'fit':selected,'fit_id':result['fit_id'],'lambda':result['lam'],'actual_movement':result['movement'],'movement_error':result['movement_error'],'certified':result['certified'],'matched':False,'recovery':'Saved finite fit only; no optimization, search or score-based choice','selection':'Last completed fit by original result-file modification time' if not known.get('fit') else 'Existing frozen target fit'}
                outcome['search_outcome_saved_before_interruption']=bool(known)
                if not known and first_unfinished is not None and task['targets'].index(rho)>task['targets'].index(first_unfinished):
                    outcome.update(status='UNRUN_PATH_BUDGET',last_finite_fit=selected,fit=None,certified=False,actual_movement=None,movement_error=None)
                    outcome['recovery']='A preceding target was interrupted; this later target was not reached. Last finite path state retained separately.'
                if graph:outcome.update(graph_eligible=graph['diagnostics']['eligible'],graph_status=graph['diagnostics']['status'])
                if old:
                    atomic_json(store.root/'recovery_records'/f'{path.stem}--original.json',old);path.unlink()
                new=freeze_endpoint(store,definition,outcome,rho=rho);recovered.append(new['point_id'])
        elif kind in ['historical','SSC_reference','old_E1_reference']:
            if endpoint_path(store,definition).exists():continue
            file=store.root/'reference_checkpoints'/f'{b}--{kind}';historical=load_record(file.with_suffix('.json')) if kind=='historical' else None
            if not historical and not (file/'CURRENT.json').exists():continue
            from method_extension.extension_verification.convex import Problem
            H=store.get(entry['objects']['H']);W=store.get(entry['objects']['W0']);P=Problem(H,W,entry['gamma_effective'],kind='relative' if kind=='old_E1_reference' else 'ssc',eta=.25)
            if historical:
                if historical['definition']!=definition:raise ValueError('reference recovery identity mismatch')
                G=store.get(historical['G']);d=P.B@G;length=np.linalg.norm(d,axis=1);q=P.c[:,None]*np.divide(d,length[:,None],out=np.zeros_like(d),where=length[:,None]>0);dual=P.dual(q,repair=True);result={'G':G,'q':dual['q'],'p':dual['p'],'iterations':historical['iterations']}
            else:
                checkpoint=recover_continuation(file)
                if checkpoint['definition']!=definition:raise ValueError('reference recovery identity mismatch')
                result=checkpoint['state'];G=result['G'];dual=P.dual(result['q'],result['p'],repair=False)
            primal=P.primal(G);gap=primal-dual['dual'];relative=gap/max(1.,abs(primal),abs(dual['dual']));capacity=max([v for k,v in dual.items() if k.endswith('violation')],default=0)
            result.update(primal=primal,dual=dual['dual'],stable_gap=gap,relative_gap=relative,movement=float(linalg.norm(G-H)/linalg.norm(H-H.mean(axis=0))) if linalg.norm(H-H.mean(axis=0)) else 0.,certified=bool(0<=relative<=1e-5 and capacity<=1e-8),recovery='Saved checkpoint, independently recomputed bound; no further fit')
            new=freeze_endpoint(store,definition,{'status':'RECOVERED_FINITE_REFERENCE','certified':result['certified'],'matched':None},result);recovered.append(new['point_id'])
    if recovered:atomic_json(store.root/'recovery_records'/'finite_recovery.json',{'point_ids':recovered,'additional_fits':0,'policy':'No score-based selection or allowance reset'})
    return recovered


def recover_finite(root,config_path):
    """Account array recovery separately; no optimization is performed."""
    import sys,time
    from experiments.extension_verification.resources import run_command
    root=Path(root);ordinal=1
    while (root/'command_jobs'/f'recover-finite-{ordinal}').exists():ordinal+=1
    while len(ResourceLedger(root).state()['active'])>=2:
        if remaining_wall(root)<15:return []
        time.sleep(.5)
    command=[sys.executable,'-c','from experiments.extension_round2.recovery import _recover_finite;import sys;_recover_finite(*sys.argv[1:])',str(root),str(config_path)]
    run_command(root,f'recover-finite-{ordinal}',command,cpu_limit=600,wall_limit=min(1320,remaining_wall(root)),phase='recovery',cwd=ROOT)
    record=load_record(root/'recovery_records/finite_recovery.json')
    return record['point_ids'] if record else []
