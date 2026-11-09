"""Summarize all outcomes and evaluate the preregistered diagnostic gate."""
from pathlib import Path
import csv,json,collections,hashlib
import numpy as np
from experiments.next_round.evaluate import paired
from experiments.next_round.campaign import protocol,PRIMARY,OUT,CACHE,JOBS,dump

ROOT=Path(__file__).resolve().parents[2]
def csvwrite(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r));path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def load():
    alljobs=[json.loads(p.read_text()) for p in sorted(JOBS.glob('*.json'))]
    superseded={old for j in alljobs for old in j.get('supersedes_run_ids',[])}
    return [j for j in alljobs if j.get('run_id') not in superseded]

def original(jobs,dataset,gamma,phase='A'):
    return next((j for j in jobs if j.get('task',{}).get('dataset')==dataset and j['task']['kind']=='original' and j['task'].get('phase')==phase and j['task']['gamma']==gamma and j.get('status')=='COMPLETED'),None)
def run():
    jobs=load();rows=[];raw=[]
    for j in jobs:
        t=j['task'];s=j.get('solver',{});row={**t,'run_id':j.get('run_id'),'execution_status':j['status'],'solver_status':s.get('status'),'qualified':j.get('qualified_for_method_contrast',False),'primal':s.get('primal'),'dual':s.get('dual'),'gap':s.get('gap'),'movement':s.get('movement'),'cpu_seconds':j.get('cpu_seconds',0),'wall_seconds':j.get('wall_seconds'),'peak_rss_bytes':j.get('peak_rss_bytes'),**j.get('scores',{}),**j.get('graph',{}),**j.get('distance',{})}
        rows.append(row)
        for r in j.get('trials',[]):raw.append({'run_id':j['run_id'],'dataset':t['dataset'],'kind':t['kind'],'gamma':t['gamma'],'phase':t['phase'],**r})
    if rows:csvwrite(OUT/'configuration_table.csv',rows)
    if raw:csvwrite(OUT/'raw_trials.csv',raw)
    gate=[];diagnostics=[]
    for dataset in PRIMARY:
        baselines=[j for j in jobs if j.get('status')=='COMPLETED' and j['task']['dataset']==dataset and j['task']['phase']=='A' and j['task']['kind']=='original' and j.get('qualified_for_method_contrast')]
        if not baselines:gate.append({'dataset':dataset,'status':'INCONCLUSIVE_NO_CERTIFIED_SSC'});continue
        base=min(baselines,key=lambda j:(-j['scores']['acc_mean'],j['task']['gamma']));gamma=base['task']['gamma']
        candidates=[j for j in jobs if j.get('status')=='COMPLETED' and j['task']['dataset']==dataset and j['task']['phase']=='B' and j['task']['gamma']==gamma]
        oracle=next((j for j in candidates if j['task']['kind']=='oracle_delete'),None);uniform=next((j for j in candidates if j['task']['kind']=='uniform_mass'),None);random=sorted([j for j in candidates if j['task']['kind']=='random_delete'],key=lambda j:j['task']['delete_seed'])
        p=next((x for x in json.loads((OUT/'representations.json').read_text()) if x['dataset']==dataset and x['prep']=='Y0'),None);auc=p['graph_W']['cross_edge_length_AUROC'] if p else None
        record={'dataset':dataset,'label_assisted_gamma':gamma,'baseline_run_id':base['run_id'],'edge_length_AUROC':auc,'status':'INCONCLUSIVE_MISSING_OR_UNCERTIFIED_CONTROLS','passed':False}
        allparts=[base,oracle,uniform,*random]
        if oracle and uniform and len(random)==3 and all(j.get('qualified_for_method_contrast') for j in allparts):
            avg=[{'seed':seed,'acc':np.mean([j['trials'][seed]['acc'] for j in random]),'nmi':np.mean([j['trials'][seed]['nmi'] for j in random])} for seed in range(50)]
            comparisons={'oracle_vs_SSC':paired(oracle['trials'],base['trials']),'oracle_vs_uniform':paired(oracle['trials'],uniform['trials']),'oracle_vs_random_mean':paired(oracle['trials'],avg),'oracle_vs_SSC_NMI':paired(oracle['trials'],base['trials'],'nmi')}
            passed=all(comparisons[k]['ci_lower_pp']>0 for k in ['oracle_vs_SSC','oracle_vs_uniform','oracle_vs_random_mean']) and comparisons['oracle_vs_SSC_NMI']['delta_pp']>=0
            record.update(comparisons);record['passed']=passed;record['status']='SUPPORTED' if passed else 'NOT_SUPPORTED_AT_LOCKED_DIAGNOSTIC'
        gate.append(record)
        for gamma in protocol()['gamma5']:
            a=original(jobs,dataset,gamma)
            if not a:continue
            for j in jobs:
                if j.get('status')=='COMPLETED' and j['task']['dataset']==dataset and j['task']['phase']=='B' and j['task']['gamma']==gamma:
                    diagnostics.append({'dataset':dataset,'gamma':gamma,'kind':j['task']['kind'],'run_id':j['run_id'],'pair_certified':a.get('qualified_for_method_contrast') and j.get('qualified_for_method_contrast'),**paired(j['trials'],a['trials']),**{'NMI_'+k:v for k,v in paired(j['trials'],a['trials'],'nmi').items()}})
    supported=sum(r.get('passed',False) for r in gate);length_supported=sum(r.get('passed',False) and r.get('edge_length_AUROC') is not None and r['edge_length_AUROC']>.5 for r in gate)
    result={'supported_primary_datasets':supported,'length_identifiable_supported_datasets':length_supported,'required':2,'formal_capped_experiment_triggered':supported>=2 and length_supported>=2,'datasets':gate,'selection_bias_note':'Oracle gamma and gate use labels on these datasets. They are diagnosis, not held-out method validation.'}
    dump(OUT/'mechanism_gate.json',result)
    if diagnostics:csvwrite(OUT/'paired_diagnostics.csv',diagnostics)
    lines=['# Performance-mechanism results','','All means are over 50 greedy K-means++ seeds on a fixed representation. Solver uncertainty is retained.','',f"Preregistered mechanism gate: {supported}/4 datasets support the required certified contrasts; {length_supported}/4 additionally meet the edge-length identifiability condition.",'','| Dataset | Phase / feature / controls | Kind | gamma | ACC ± SD (%) | NMI ± SD (%) | Solver | gap |','|---|---|---|---:|---|---|---|---:|']
    for r in rows:
        setting=r['phase']+' / '+r['prep']
        if 'tau_multiplier' in r:setting+=' / tau-sF='+str(r['tau_multiplier'])
        if 'delete_seed' in r:setting+=' / deletion-seed='+str(r['delete_seed'])
        if 'fidelity' in r:setting+=' / '+r['fidelity']
        if r['execution_status']=='COMPLETED':lines.append(f"| {r['dataset']} | {setting} | {r['kind']} | {r['gamma']:g} | {r['acc_mean']:.3f} ± {r['acc_sd']:.3f} | {r['nmi_mean']:.3f} ± {r['nmi_sd']:.3f} | {r['solver_status']} | {r.get('gap') if r.get('gap') is not None else 'NA'} |")
        else:lines.append(f"| {r['dataset']} | {setting} | {r['kind']} | {r['gamma']:g} | NA | NA | {r['execution_status']} | NA |")
    (OUT/'all_results.md').write_text('\n'.join(lines)+'\n');folder=OUT/'per_benchmark';folder.mkdir(exist_ok=True)
    for dataset in PRIMARY:
        selected=[line for line in lines[7:] if line.startswith('| '+dataset+' |')];(folder/(dataset+'.md')).write_text('\n'.join(lines[:8]+selected)+'\n')
    dump(OUT/'global_status.json',{'jobs':len(jobs),'execution':dict(collections.Counter(j['status'] for j in jobs)),'solver':dict(collections.Counter(j.get('solver',{}).get('status','NOT_RUN') for j in jobs)),'cpu_seconds':sum(j.get('cpu_seconds',0) for j in jobs),'formal_four_dataset_gain_pp':None,'practical_target_status':'PENDING_MECHANISM_AND_COMPLETE_SEARCH' if result['formal_capped_experiment_triggered'] else 'NOT_ESTABLISHED_MECHANISM_GATE_NOT_PASSED'})
    print(json.dumps(result,indent=2))
if __name__=='__main__':run()
