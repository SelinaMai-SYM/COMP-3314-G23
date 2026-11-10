"""Enumerate intended baseline configurations and every external seed.

This is a metadata-only inventory: it neither fits models, evaluates labels,
selects scores, nor combines successful seeds across separate run IDs.
"""
from __future__ import annotations
from collections import Counter
import csv
import json
import math
from pathlib import Path
from .core import ROOT, atomic_json, digest

EXPECTED_SEEDS=tuple(range(50))
TERMINAL_FAILURES={'TIMEOUT','FAILED','KILLED_OR_CRASHED','INCOMPLETE_FAILED_SEEDS','CPU_LIMIT','CPU_LIMIT_UNCERTIFIED'}
UNRUN_BUDGET={'NOT_RUN_BUDGET','NOT_LAUNCHED_BUDGET','BUDGET_EXHAUSTED'}


def _read(path):
    if not path.is_file():return None
    try:return json.loads(path.read_text())
    except (OSError,ValueError) as exc:return {'_read_error':repr(exc),'_path':str(path)}


def _metric_valid(trial):
    try:return all(math.isfinite(float(trial[m])) and 0<=float(trial[m])<=1 for m in ['acc','nmi'])
    except (KeyError,TypeError,ValueError):return False


def _write_csv(path,rows):
    fields=list(dict.fromkeys(key for row in rows for key in row))
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list,tuple)) else v for k,v in row.items()})
    temporary.replace(path)


def _declare(task):
    """Mirror the existing adapter's endpoint names without loading data."""
    run_id=task['run_id'];block=task['block'];specs=[]
    def add(name,method,parameters=None,**extra):
        specs.append({'name':name,'method':method,'expected_config_id':run_id+'|'+name,
                      'parameters':parameters or {},**extra})
    if block=='lda_existing':
        for limit in task.get('limits',[30,100,300]):
            add(f'{block}__{limit}',block,{'max_iter':limit},limit=limit,evidence='lda_state',expected_config_id=run_id+f'|limit{limit}')
    elif block=='lda_reference':
        add(block+'__300',block,{'max_iter':300},limit=300,evidence='lda_state',expected_config_id=run_id+'|limit300')
    elif block=='lda_adapted':
        for name in ['raw_sc','pca_p0_sc','pca_r_sc']:add(name,name)
        add(block+'__300',block,{'max_iter':300},limit=300,evidence='lda_state',expected_config_id=run_id+'|limit300')
        add('lda_adapted_sc','lda_adapted_sc',{'max_iter':300},limit=300,evidence='adapted_sc',expected_config_id=run_id+'|adapted_sc')
    elif block=='slps':
        from .baselines import slps_configurations
        configs=slps_configurations(task)
        for k,alpha in sorted({(c['n_neighbors'],c['alpha']) for c in configs}):
            for config in sorted([c for c in configs if (c['n_neighbors'],c['alpha'])==(k,alpha)],key=lambda c:(c['dimension'],c['initialization'])):
                name=f"spls__k{k}__alpha{alpha:g}__d{config['dimension']}"
                if config['initialization']!='RANDOM':name+='__'+config['initialization']
                add(name,'spls',dict(config),evidence='slps_alias')
    elif block=='msra_llc':
        from .msra_llc_continuation import configurations
        for config in configurations(task):
            add(config['name'],'llc',config,evidence='msra_llc_rounding',
                expected_config_id=run_id+f"|{config['ridge']}|{config['bandwidth_factor']}")
    elif block=='msra_other':
        add('kmeans','kmeans')
        for dimension in task['dimensions']:
            add(f'pca_kmeans__d{dimension}','pca_kmeans',{'dimension':dimension})
            add(f'pca_sc__d{dimension}','pca_sc',{'dimension':dimension})
        for ridge in task['llc_ridge']:
            for bandwidth in task['llc_bandwidth']:
                add(f'llc__{ridge:g}__{bandwidth:g}','llc',{'ridge':ridge,'bandwidth_factor':bandwidth},
                    evidence='llc_checkpoint',expected_config_id=run_id+f'|{ridge}|{bandwidth}')
    else:raise ValueError('unknown baseline block '+str(block))
    for index,spec in enumerate(specs):spec['declaration_index']=index
    return specs


def _task_state(task,store,ledger):
    run_id=task['run_id'];folder=store/'baseline'/run_id
    state=_read(store/'task_status'/(run_id+'.json')) or _read(folder/'status.json')
    if state is not None:
        return {'status':'INVALID_BLOCK_METADATA','error':state['_read_error']} if state.get('_read_error') else state
    if run_id in ledger.get('active',{}):return {'status':'RUNNING'}
    entries=[row for row in ledger.get('entries',[]) if row.get('run_id')==run_id]
    if entries:return entries[-1]
    # During live work, reservations may be released below their maxima. Do not
    # label pending work budget-exhausted merely because another block is active.
    if ledger and not ledger.get('active'):
        charged=sum(float(row.get('charged_cpu_seconds',0)) for row in ledger.get('entries',[]))
        limit=float(ledger.get('limit_seconds',129600))
        if task.get('phase') not in ['validation','aggregation','confirmation']:limit-=float(ledger.get('reserve_seconds',7200))
        if charged+float(task.get('cpu_limit',0))>limit:return {'status':'NOT_RUN_BUDGET'}
    return {'status':'PENDING'}


def _record_files(folder):
    return {path.name:_read(path) for path in sorted(folder.glob('*.json'))}


def _slps_match(record,spec):
    if not record:return False
    wanted=spec['parameters']
    for alias in record.get('declared_configuration_aliases',[]):
        if all(alias.get(key)==wanted.get(key) for key in ['n_neighbors','alpha','dimension','initialization']):return True
    params=record.get('parameters',{})
    return all(params.get(key)==wanted.get(key) for key in ['n_neighbors','alpha','dimension','initialization'])


def _collect(spec,folder,files,block_state):
    """Collect final trials and per-seed/checkpoint evidence without evaluation."""
    name=spec['name'];final=files.get(name+'.json');fit=files.get(name+'__fit.json');actual_name=name
    if spec.get('evidence')=='slps_alias' and final is None and fit is None:
        matches=[(filename,record) for filename,record in files.items() if _slps_match(record,spec)]
        final_match=next(((filename,record) for filename,record in matches if not filename.endswith(('__fit.json','__checkpoint.json'))),None)
        fit_match=next(((filename,record) for filename,record in matches if filename.endswith('__fit.json')),None)
        if final_match:actual_name=final_match[0][:-5];final=final_match[1];fit=files.get(actual_name+'__fit.json')
        elif fit_match:actual_name=fit_match[0][:-len('__fit.json')];fit=fit_match[1]
    seeds={};duplicates=[];errors=[]
    def add_trial(trial,source):
        if 'seed' not in trial:return
        seed=int(trial['seed'])
        if seed in seeds and seeds[seed].get('metrics_present'):duplicates.append(seed)
        seeds[seed]={'seed_status':'COMPLETED' if _metric_valid(trial) else 'INVALID_METRICS',
            'fit_completed':True,'metrics_present':_metric_valid(trial),'evidence_record':str(source),
            'native_objective_present':any(key in trial for key in ['inertia','native_objective'])}
    if final:
        if final.get('_read_error'):errors.append(final['_read_error'])
        for trial in final.get('trials',[]):add_trial(trial,folder/(actual_name+'.json'))
        for failure in final.get('seed_failures',[]):
            seed=int(failure['seed']);seeds[seed]={'seed_status':failure.get('status','FAILED'),'fit_completed':False,
                'metrics_present':False,'evidence_record':str(folder/(actual_name+'.json')),'error':failure.get('error')}
    if spec.get('evidence')=='lda_state':
        for seed in EXPECTED_SEEDS:
            path=folder/f"state__{spec['limit']}__{seed}.json";state=files.get(path.name)
            if state is None:continue
            if state.get('_read_error'):
                errors.append(state['_read_error']);seeds[seed]={'seed_status':'INVALID_METADATA','fit_completed':False,'metrics_present':False,'evidence_record':str(path),'error':state['_read_error']};continue
            status=state.get('status','UNKNOWN');diagnostics=state.get('diagnostics',{})
            if seed not in seeds:
                seeds[seed]={'seed_status':'COMPLETED_FIT_CHECKPOINT_ONLY' if status=='COMPLETED' else status,
                    'fit_completed':status=='COMPLETED','metrics_present':False,'evidence_record':str(path)}
            seeds[seed]['fit_checkpoint_status']=status
            seeds[seed]['state_implementation_hash']=state.get('implementation_hash')
            seeds[seed]['fit_termination_reason']=diagnostics.get('termination_reason')
            seeds[seed]['state_objects_available']=bool(state.get('objects'))
    elif spec.get('evidence')=='adapted_sc':
        for seed in EXPECTED_SEEDS:
            path=folder/f'adapted_sc_seed{seed}.json';state=files.get(path.name)
            if state and seed not in seeds:
                add_trial({'seed':seed,**state.get('scores',{})},path)
    elif spec.get('evidence')=='llc_checkpoint':
        checkpoint=files.get(actual_name+'__checkpoint.json')
        if checkpoint and final is None:
            for trial in checkpoint.get('completed_trials',[]):add_trial(trial,folder/(actual_name+'__checkpoint.json'))
    elif spec.get('evidence')=='msra_llc_rounding':
        for seed in EXPECTED_SEEDS:
            path=folder/'rounding'/actual_name/(str(seed)+'.json');checkpoint=_read(path)
            if checkpoint is None:continue
            if checkpoint.get('_read_error'):
                errors.append(checkpoint['_read_error']);continue
            state=checkpoint.get('status','UNKNOWN')
            if seed not in seeds:
                if state=='COMPLETED' and checkpoint.get('trial'):
                    add_trial(checkpoint['trial'],path)
                else:
                    seeds[seed]={'seed_status':state,'fit_completed':False,'metrics_present':False,
                                 'evidence_record':str(path),'error':checkpoint.get('error')}
            seeds[seed]['fit_checkpoint_status']=state
    active=block_state.get('active_configuration')
    if active==actual_name:
        interrupted=block_state.get('interrupted_rounding',{})
        for trial in interrupted.get('completed_trials',[]):
            if int(trial.get('seed',-1)) not in seeds:add_trial(trial,folder/'status.json')
        failed_seed=interrupted.get('failed_rounding_seed')
        if failed_seed is not None:
            seeds[int(failed_seed)]={'seed_status':block_state.get('status','FAILED'),'fit_completed':False,
                'metrics_present':False,'evidence_record':str(folder/'status.json'),'error':block_state.get('error')}
    entered=bool(final or fit or seeds or active==actual_name)
    return {'final':final,'fit':fit,'actual_name':actual_name,'seeds':seeds,'duplicates':duplicates,'errors':errors,'entered':entered}


def _missing_status(block_status,entered):
    if block_status in UNRUN_BUDGET or ('BUDGET' in block_status and block_status.startswith('NOT_')):return 'NOT_RUN_BUDGET'
    if block_status=='INVALID_BLOCK_METADATA':return block_status
    if block_status in ['RUNNING','STARTED']:return 'PENDING_IN_ACTIVE_BLOCK'
    if block_status in TERMINAL_FAILURES:return 'NOT_RUN_AFTER_BLOCK'
    if block_status=='COMPLETED':return 'MISSING_FROM_COMPLETED_BLOCK'
    return 'PENDING'


def baseline_coverage(artifact_root,output):
    """Write configuration/seed coverage from frozen queues and raw metadata."""
    store=Path(artifact_root).resolve();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    ledger=_read(store/'resource_ledger.json') or {};tasks=[];queue_sources=[];seen={}
    for relative in ['configs/submission_refresh/execution_queue.json','configs/submission_refresh/validation_queue.json','configs/submission_refresh/msra_llc_continuation_queue.json']:
        path=ROOT/relative;queue=_read(path)
        if queue is None:continue
        if queue.get('_read_error'):raise ValueError('corrupt frozen queue '+str(path))
        queue_sources.append({'path':relative,'sha256':digest(path)})
        for task in queue.get('tasks',[]):
            if task.get('kind') not in ['baseline','msra_llc_repair'] or task.get('profile'):continue
            if task['run_id'] in seen:
                if seen[task['run_id']]!=task:raise ValueError('conflicting frozen baseline task '+task['run_id'])
                continue
            seen[task['run_id']]=task;tasks.append({**task,'source_queue':relative})
    if not tasks:raise ValueError('no frozen baseline tasks; coverage output not written')
    configs=[];seed_rows=[]
    def emit(task,specs,folder,block_state):
        files=_record_files(folder);block_status=block_state.get('status','PENDING')
        for spec in specs:
            evidence=_collect(spec,folder,files,block_state);observed=evidence['seeds']
            unexpected=sorted(set(observed)-set(EXPECTED_SEEDS));missing=_missing_status(block_status,evidence['entered'])
            completed=sum(seed in observed and observed[seed].get('metrics_present',False) for seed in EXPECTED_SEEDS)
            fits=sum(seed in observed and observed[seed].get('fit_completed',False) for seed in EXPECTED_SEEDS)
            failed=sum(seed in observed and not observed[seed].get('fit_completed',False) for seed in EXPECTED_SEEDS)
            invalid_metrics=sum(row.get('seed_status')=='INVALID_METRICS' for row in observed.values())
            final=evidence['final'] or {};complete=completed==50 and not evidence['duplicates'] and not unexpected and not evidence['errors']
            if complete:status='COMPLETED'
            elif evidence['errors']:status='INVALID_METADATA'
            elif evidence['duplicates'] or unexpected:status='INVALID_SEED_SET'
            elif invalid_metrics:status='INVALID_METRICS'
            elif any('TIMEOUT' in row.get('seed_status','') or 'CPU_LIMIT' in row.get('seed_status','') for row in observed.values()):status='INCOMPLETE_TIMEOUT'
            elif failed:status='INCOMPLETE_FAILED_SEEDS'
            elif evidence['entered'] and block_status in TERMINAL_FAILURES:status='TIMEOUT' if 'TIMEOUT' in block_status else 'FAILED_IN_BLOCK'
            elif evidence['entered'] and block_status=='COMPLETED':status='INCOMPLETE_MISSING_METRICS'
            else:status=missing
            config_id=final.get('config_id',spec['expected_config_id'])
            common={'run_id':task['run_id'],'dataset':task['dataset'],'block':task['block'],
                'declaration_index':spec['declaration_index'],'intended_config_id':spec['expected_config_id'],
                'effective_config_id':config_id,'configuration_name':evidence['actual_name'],'method':spec['method'],
                'source_queue':task['source_queue'],'parameters':spec['parameters'],'block_status':block_status,
                'supersedes_run_id':task.get('supersedes_run_id'),
                'supersedes_config_id':task['supersedes_run_id']+f"|limit{spec['limit']}" if task.get('supersedes_run_id') and 'limit' in spec else None,
                'source_implementation_hash':(final.get('source') or block_state.get('source') or {}).get('implementation_hash'),
                'source_record':str(folder/(evidence['actual_name']+'.json')) if evidence['final'] else None}
            configs.append({**common,'status':status,'complete_configuration':complete,'expected_seed_count':50,
                'completed_metric_seeds':completed,'completed_fit_checkpoint_seeds':fits,'failed_seed_count':failed,'invalid_metric_seed_count':invalid_metrics,
                'unobserved_seed_count':50-sum(seed in observed for seed in EXPECTED_SEEDS),
                'duplicate_metric_seeds':sorted(set(evidence['duplicates'])),'unexpected_seeds':unexpected,
                'final_record_status':final.get('status'),'native_best_status':final.get('native_best_status'),'fit_termination_counts':dict(Counter(row.get('fit_termination_reason') for row in observed.values() if row.get('fit_termination_reason'))),
                'qualification':'Coverage is execution/evidence completeness; degenerated or failed LDA updates retain their separate method qualifications. No cross-run seed merging.'})
            for seed in EXPECTED_SEEDS:
                seed_rows.append({**common,'seed':seed,**observed.get(seed,{'seed_status':missing,'fit_completed':False,'metrics_present':False,'evidence_record':None})})
    for task in tasks:
        if 'timerfix' in task['run_id'] and not task.get('supersedes_run_id'):
            prior=next((t for t in tasks if t['dataset']==task['dataset'] and t['block']==task['block'] and 'timerfix' not in t['run_id']),None)
            if prior:task['supersedes_run_id']=prior['run_id']
        emit(task,_declare(task),store/'baseline'/task['run_id'],_task_state(task,store,ledger))
    # MSRA's primary K-means/SC/SSC block is nested inside the first MSRA
    # baseline worker. It is a declared design, not an extra CPU reservation.
    msra_tasks=[task for task in tasks if task['dataset']=='MSRA25_EBSA_16x16']
    if msra_tasks:
        controller=next((task for task in msra_tasks if task['run_id'] in ledger.get('active',{})),msra_tasks[0])
        primary_folder=store/'baseline/msra-primary-v1';primary_record=_read(primary_folder/'kmeans.json') or {}
        charged_in=primary_record.get('cpu_charged_in',controller['run_id'])
        controller=next((task for task in msra_tasks if task['run_id']==charged_in),controller)
        primary_task={'run_id':'msra-primary-v1','block':'nested_msra_primary','dataset':'MSRA25_EBSA_16x16',
            'source_queue':'nested preregistered MSRA first block; CPU charged in '+controller['run_id']}
        emit(primary_task,[{'name':'kmeans','method':'kmeans','expected_config_id':'msra-primary-v1|kmeans','parameters':{},'declaration_index':0}],primary_folder,_task_state(controller,store,ledger))
        candidate_id='MSRA25_EBSA_16x16';nested_task={**primary_task,'run_id':'msra-primary-subset'}
        specs=[]
        for initialization in ['RANDOM','VANILLA_KMEANSPP','SKLEARN_GREEDY_KMEANSPP']:
            name='SC__'+initialization;specs.append({'name':name,'method':'sc','expected_config_id':candidate_id+'|SC|'+initialization,'parameters':{'initialization':initialization},'declaration_index':len(specs)})
        for variant in ['E8','E13']:
            for gamma in [1e-6,1e-3,1.,1e3,1e6]:
                for initialization in ['RANDOM','VANILLA_KMEANSPP','SKLEARN_GREEDY_KMEANSPP']:
                    name=f'{variant}__{gamma:g}__{initialization}'
                    specs.append({'name':name,'method':'ssc','expected_config_id':candidate_id+f'|{variant}__{gamma:g}|'+initialization,
                        'parameters':{'variant':variant,'gamma_nominal':gamma,'gamma_effective':gamma/(2 if variant=='E13' else 1),'initialization':initialization},'declaration_index':len(specs)})
        nested_folder=store/'subset'/candidate_id;nested_state=_read(nested_folder/'status.json') or _task_state(controller,store,ledger)
        emit(nested_task,specs,nested_folder,nested_state)
    _write_csv(output/'baseline_execution_coverage.csv',configs);_write_csv(output/'baseline_seed_coverage.csv',seed_rows)
    manifest={'schema':'baseline-execution-coverage-v1','metadata_only_no_score_selection':True,
        'source_queues':queue_sources,'intended_configuration_declarations':len(configs),'explicit_seed_rows':len(seed_rows),
        'status_counts':dict(Counter(row['status'] for row in configs)),
        'complete_configuration_count':sum(row['complete_configuration'] for row in configs),
        'each_configuration_has_seeds_0_to_49':len(seed_rows)==50*len(configs),
        'cross_run_successful_seed_merging':False,
        'files':{name:digest(output/name) for name in ['baseline_execution_coverage.csv','baseline_seed_coverage.csv']}}
    atomic_json(output/'baseline_coverage_manifest.json',manifest)
    return manifest
