"""Coverage exposes failed and unrun seeds without merging separate attempts."""
import csv
import json
from pathlib import Path
import experiments.submission_refresh.coverage as coverage


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def setup_queues(tmp_path,monkeypatch,tasks,repaired=()):
    root=tmp_path/'repo';store=tmp_path/'artifacts'
    monkeypatch.setattr(coverage,'ROOT',root)
    write(root/'configs/submission_refresh/execution_queue.json',{'tasks':tasks})
    write(root/'configs/submission_refresh/validation_queue.json',{'tasks':list(repaired)})
    return store


def trials():return [{'seed':seed,'acc':.5,'nmi':.6} for seed in range(50)]


def test_lda_timeout_and_new_full_attempt_remain_separate(tmp_path,monkeypatch):
    old={'run_id':'lda-Yale-v1','kind':'baseline','block':'lda_existing','dataset':'Yale','limits':[30,100,300],'cpu_limit':6000}
    new={**old,'run_id':'lda-Yale-timerfix-v2','limits':[100,300]}
    store=setup_queues(tmp_path,monkeypatch,[old],[new]);folder=store/'baseline'/old['run_id']
    write(folder/'status.json',{'status':'TIMEOUT'})
    write(folder/'lda_existing__30.json',{'status':'COMPLETED','config_id':old['run_id']+'|limit30','trials':trials()})
    for seed in range(19):write(folder/f'state__100__{seed}.json',{'status':'COMPLETED','objects':{'labels':{'path':'available-separately'}},'diagnostics':{'termination_reason':'MAX_ITER'}})
    write(folder/'state__100__19.json',{'status':'TIMEOUT'})
    manifest=coverage.baseline_coverage(store,tmp_path/'out')
    rows=list(csv.DictReader((tmp_path/'out/baseline_execution_coverage.csv').open()))
    indexed={(r['run_id'],json.loads(r['parameters'])['max_iter']):r for r in rows}
    assert indexed[(old['run_id'],30)]['status']=='COMPLETED'
    partial=indexed[(old['run_id'],100)]
    assert partial['status']=='INCOMPLETE_TIMEOUT'
    assert int(partial['completed_fit_checkpoint_seeds'])==19
    assert int(partial['completed_metric_seeds'])==0
    assert int(partial['failed_seed_count'])==1 and int(partial['unobserved_seed_count'])==30
    assert indexed[(old['run_id'],300)]['status']=='NOT_RUN_AFTER_BLOCK'
    assert indexed[(new['run_id'],100)]['status']=='PENDING'
    assert indexed[(new['run_id'],100)]['supersedes_run_id']==old['run_id']
    assert manifest['intended_configuration_declarations']==5 and manifest['explicit_seed_rows']==250
    seeds=list(csv.DictReader((tmp_path/'out/baseline_seed_coverage.csv').open()))
    current=[r for r in seeds if r['run_id']==new['run_id'] and json.loads(r['parameters'])['max_iter']==100]
    assert [int(r['seed']) for r in current]==list(range(50))
    assert all(r['seed_status']=='PENDING' for r in current)


def test_exact_slps_and_msra_other_catalogue_counts():
    slps={'run_id':'slps','block':'slps','extra_configs':[{'n_neighbors':k,'alpha':.85,'dimension':40,'initialization':'SKLEARN_GREEDY_KMEANSPP','role':'paired_existing_reported_setting'} for k in [5,7]]}
    assert len(coverage._declare(slps))==20
    msra={'run_id':'other','block':'msra_other','dimensions':list(range(10,151,10)),'llc_ridge':[.1,1.,1.5],'llc_bandwidth':[.0625,.25,1.,4.,16.]}
    declared=coverage._declare(msra)
    assert len(declared)==46
    assert len([r for r in declared if r['method']=='llc'])==15


def test_nested_msra_primary_is_not_omitted(tmp_path,monkeypatch):
    task={'run_id':'msra-other-v1','kind':'baseline','block':'msra_other','dataset':'MSRA25_EBSA_16x16','cpu_limit':1800,
          'dimensions':list(range(10,151,10)),'llc_ridge':[.1,1.,1.5],'llc_bandwidth':[.0625,.25,1.,4.,16.]}
    store=setup_queues(tmp_path,monkeypatch,[task])
    write(store/'baseline/msra-primary-v1/kmeans.json',{'status':'COMPLETED','config_id':'msra-primary-v1|kmeans','cpu_charged_in':task['run_id'],'trials':trials()})
    write(store/'subset/MSRA25_EBSA_16x16/SC__RANDOM.json',{'status':'COMPLETED','config_id':'MSRA25_EBSA_16x16|SC|RANDOM','trials':trials()})
    result=coverage.baseline_coverage(store,tmp_path/'out')
    assert result['intended_configuration_declarations']==46+34
    assert result['complete_configuration_count']==2
    assert result['explicit_seed_rows']==80*50
    rows=list(csv.DictReader((tmp_path/'out/baseline_execution_coverage.csv').open()))
    assert len([r for r in rows if r['block']=='nested_msra_primary' and r['method']=='ssc'])==30


def test_unlaunched_budget_is_explicit_and_ledger_is_not_changed(tmp_path,monkeypatch):
    task={'run_id':'budget','kind':'baseline','block':'lda_existing','dataset':'unit','limits':[300],'cpu_limit':30}
    store=setup_queues(tmp_path,monkeypatch,[task])
    write(store/'resource_ledger.json',{'limit_seconds':100,'reserve_seconds':20,'active':{},'entries':[{'run_id':'previous','charged_cpu_seconds':90}]})
    old=(store/'resource_ledger.json').read_bytes()
    coverage.baseline_coverage(store,tmp_path/'out')
    rows=list(csv.DictReader((tmp_path/'out/baseline_seed_coverage.csv').open()))
    assert len(rows)==50 and all(r['seed_status']=='NOT_RUN_BUDGET' for r in rows)
    assert (store/'resource_ledger.json').read_bytes()==old
