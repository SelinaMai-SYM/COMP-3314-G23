"""Optional AR planning uses synthetic metadata, never fits or real stores."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest


@pytest.fixture
def planner():
    path=Path(__file__).resolve().parents[2]/'scripts/submission_refresh/optional_ar_cohort.py'
    spec=importlib.util.spec_from_file_location('optional_ar_planner_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True))


@pytest.fixture
def metadata_case(tmp_path,monkeypatch,planner):
    root=tmp_path/'checkout';store=tmp_path/'scientific metadata';store.mkdir()
    primary_ids=list(planner.FIXED_AR)+[f'primary_{i:04d}' for i in range(1198)]
    primary=[{'candidate_id':candidate,'family':'AR_fixed7' if candidate in planner.FIXED_AR else 'primary',
        'alias_of':None,'prep':'Y0','n':840,'classes':120,'fingerprint':{'x_sha256':'pixels','y_sha256':'labels'},
        'manifest_sha256':'new-metadata-manifest'} for candidate in primary_ids]
    masks=[{'candidate_id':f'AR_common_mask{i:04d}','family':'AR_common_mask','alias_of':None} for i in range(1,9)]
    masks.append({'candidate_id':'AR_common_mask0000','family':'AR_common_mask','alias_of':'AR_first7'})
    catalogue={'candidates':primary+masks};write_json(root/planner.CATALOGUE,catalogue)
    original={'version':1,'candidate_ids':primary_ids,'cpu_limit_per_candidate':1200,
        'catalogue_sha256':planner._sha(root/planner.CATALOGUE),'per_candidate_limits':{'primary_0000':7200},
        'rationale':'Original primary scope, preserved exactly.'}
    # Deliberately noncanonical whitespace verifies byte-preserving copies.
    (root/planner.PRIMARY).parent.mkdir(parents=True,exist_ok=True)
    (root/planner.PRIMARY).write_text(json.dumps(original,indent=3)+'\n')
    (root/planner.ORDER).write_text(json.dumps({'version':1,'candidate_ids':list(reversed(primary_ids))},indent=1)+'\n')
    (root/planner.PROTOCOL).write_bytes((planner.ROOT/planner.PROTOCOL).read_bytes())
    queue_path=root/'configs/submission_refresh/graph_queue.json'
    queue_path.parent.mkdir(parents=True)
    queue_path.write_bytes((planner.ROOT/'configs/submission_refresh/graph_queue.json').read_bytes())
    tasks=json.loads(queue_path.read_text())['tasks']
    coverage=root/'results/graph_coverage.csv';coverage.parent.mkdir(parents=True,exist_ok=True)
    with coverage.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['run_id','controller_status']);writer.writeheader()
        writer.writerows({'run_id':task['run_id'],'controller_status':'NOT_RUN'} for task in tasks)
    gate=root/'results/gate.json';write_json(gate,{'promotion_passed':False,'G4_G5_status':'NOT_RUN_GATE_NOT_PASSED',
        'contrasts':'Opaque performance payload is never decoded by the planner.'})
    terminal=root/'terminal.json';write_json(terminal,{'schema':'optional-ar-terminal-decision-v1',
        'graph_design_terminal':True,'G4_G5_terminal':True,'unrun_work_frozen':True,
        'G4_G5_disposition':'NOT_PERMITTED','evidence':{
            'graph_coverage':{'path':str(coverage.relative_to(root)),'sha256':planner._sha(coverage)},
            'gate':{'path':str(gate.relative_to(root)),'sha256':planner._sha(gate)}}})
    ledger={'version':1,'active':{},'entries':[{'run_id':'prior','charged_cpu_seconds':122300,'status':'COMPLETED'}],
        'limit_seconds':129600,'reserve_seconds':7200,'max_workers':2,'rss_target_bytes':8*2**30}
    write_json(store/'resource_ledger.json',ledger)
    profile=store/'task_status/blind-ar.json'
    write_json(profile,{'status':'PROFILE_ONLY_INELIGIBLE','profile_only':True,'candidate_id':'AR_first7',
        'candidate':{**primary[0],'manifest_sha256':'old-metadata-manifest'},'cpu_seconds':1.,'rounding_cpu_per_seed':.001,
        'solver_timings':[{'variant':variant,'gamma':gamma,'cpu_seconds':.01} for variant in ['E8','E13'] for gamma in planner.GAMMAS]})
    for index,candidate in enumerate(planner.FIXED_AR,1):
        raw=b'x'*(index*10);sha=hashlib.sha256(raw).hexdigest();object_path=store/'objects'/sha[:2]/(sha+'.npz')
        object_path.parent.mkdir(parents=True,exist_ok=True);object_path.write_bytes(raw)
        reference={'sha256':sha,'path':str(object_path.relative_to(store)),'kind':'compressed_array','bytes':len(raw)}
        folder=store/'subset'/candidate
        write_json(folder/'status.json',{'candidate_id':candidate,'status':'COMPLETED','profile_only':False})
        write_json(folder/'representation.json',{'objects':{'F':reference}})
        write_json(folder/'source.json',{'source_archive':reference})
        for variant in ['E8','E13']:
            for gamma in planner.GAMMAS:
                write_json(folder/f'{variant}__{gamma:g}__solver.json',{'objects':{'G':reference}})
                for init in planner.INITS:
                    write_json(folder/f'{variant}__{gamma:g}__{init}.json',{'candidate_id':candidate,'status':'COMPLETED',
                        'objects':{'G':reference},'trials':'These performance values are intentionally not interpreted.'})
        for init in planner.INITS:
            write_json(folder/f'SC__{init}.json',{'candidate_id':candidate,'status':'COMPLETED','objects':{'G':reference}})
    disk={'artifact_store_bytes':1000,'total_bytes':planner.BUFFER+100000,'used_bytes':0,
        'free_bytes':planner.BUFFER+2000+3*150+149}
    monkeypatch.setattr(planner,'_disk_snapshot',lambda store:dict(disk))
    return SimpleNamespace(root=root,store=store,profile=profile,terminal=terminal,ledger=ledger,disk=disk,
        primary_raw=(root/planner.PRIMARY).read_bytes(),order_raw=(root/planner.ORDER).read_bytes())


def test_cost_and_disk_caps_follow_the_predeclared_formulas(planner):
    result=planner.plan_counts(700,10.,.02,100,planner.BUFFER+2*1000+3*375+374,1000,20)
    assert result['cpu_estimate_seconds_per_mask']==86.
    assert result['cpu_count_cap']==8 and result['disk_count_cap']==3 and result['selected_count']==3
    assert result['per_new_mask_reserved_bytes']==375
    assert planner.plan_counts(700,10.,.02,100,planner.BUFFER,1000,20)['selected_count']==0
    assert planner.plan_counts(0,10.,.02,100,10*planner.BUFFER,1000,20)['selected_count']==0


def test_freeze_excludes_aliases_preserves_primary_bytes_and_never_opens_objects(planner,metadata_case,monkeypatch):
    case=metadata_case
    original_open=Path.open
    def no_objects(path,*args,**kwargs):
        if (case.store/'objects') in path.resolve().parents:raise AssertionError('matrix objects must not be opened')
        return original_open(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',no_objects)
    record=planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    expected=[f'AR_common_mask{i:04d}' for i in range(1,9)]
    expected=[expected[int(index)] for index in np.random.RandomState(20261110).permutation(8)]
    assert record['canonical_permutation']==expected and record['candidate_ids']==expected[:3]
    assert 'AR_common_mask0000' not in record['candidate_ids']
    assert record['catalogued_aliases']=={'AR_common_mask0000':'AR_first7'}
    assert set(record['unrun_candidate_ids'])|set(record['candidate_ids'])==set(expected)
    assert (case.root/planner.PRIMARY_COPY).read_bytes()==case.primary_raw
    assert (case.root/planner.ORDER_COPY).read_bytes()==case.order_raw
    union=json.loads((case.root/planner.PRIMARY).read_text())
    assert union['candidate_ids']==json.loads(case.primary_raw)['candidate_ids']+expected[:3]
    assert union['per_candidate_limits']==json.loads(case.primary_raw)['per_candidate_limits']
    assert union['cpu_limit_per_candidate']==record['cpu_limit_per_candidate']==1200
    assert json.loads((case.root/planner.ORDER).read_text())['candidate_ids']==json.loads(case.order_raw)['candidate_ids']+expected[:3]
    assert record['score_values_decoded'] is record['matrix_objects_opened'] is False
    assert record['profile_membership_identity']['profile_manifest_sha256']=='old-metadata-manifest'


def test_resume_is_immutable_despite_updated_cost_disk_and_ledger_charges(planner,metadata_case,monkeypatch):
    case=metadata_case
    first=planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    frozen=(case.root/planner.FROZEN).read_bytes()
    ledger=json.loads((case.store/'resource_ledger.json').read_text())
    ledger['entries'].append({'run_id':'later optional work','charged_cpu_seconds':20,'status':'COMPLETED'})
    write_json(case.store/'resource_ledger.json',ledger)
    case.profile.write_text('updated cost is never consulted on resume')
    def never(*args,**kwargs):raise AssertionError('resume must not reprofile, read disk costs or expand the prefix')
    monkeypatch.setattr(planner,'_disk_snapshot',never)
    monkeypatch.setattr(planner,'_fixed_object_inventory',never)
    resumed=planner.freeze_optional_ar(case.store,'missing new profile','missing new terminal',root=case.root)
    assert resumed['freeze_id']==first['freeze_id'] and resumed['candidate_ids']==first['candidate_ids']
    assert (case.root/planner.FROZEN).read_bytes()==frozen


def test_zero_disk_capacity_freezes_an_empty_optional_cohort_without_new_ids(planner,metadata_case):
    case=metadata_case;case.disk['free_bytes']=planner.BUFFER
    record=planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    assert record['candidate_ids']==[] and record['union_count']==1202
    assert set(record['unrun_candidate_ids'])==set(record['canonical_permutation'])
    assert json.loads((case.root/planner.PRIMARY).read_text())['candidate_ids']==json.loads(case.primary_raw)['candidate_ids']


def test_resume_rejects_independent_union_changes_without_reselection(planner,metadata_case):
    case=metadata_case
    planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    frozen=(case.root/planner.FROZEN).read_bytes()
    current=json.loads((case.root/planner.PRIMARY).read_text());current['unapproved_scope_change']=True
    write_json(case.root/planner.PRIMARY,current)
    with pytest.raises(ValueError,match='changed independently'):
        planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    assert (case.root/planner.FROZEN).read_bytes()==frozen
    assert json.loads((case.root/planner.PRIMARY).read_text())['unapproved_scope_change'] is True


def test_interrupted_publication_resumes_the_original_frozen_bytes(planner,metadata_case,monkeypatch):
    case=metadata_case;atomic=planner._atomic
    def interrupt(path,raw,**kwargs):
        if path==case.root/planner.PRIMARY:raise OSError('simulated interruption before default union replacement')
        return atomic(path,raw,**kwargs)
    monkeypatch.setattr(planner,'_atomic',interrupt)
    with pytest.raises(OSError,match='simulated interruption'):
        planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    frozen=(case.root/planner.FROZEN).read_bytes()
    assert (case.root/planner.PRIMARY).read_bytes()==case.primary_raw
    monkeypatch.setattr(planner,'_atomic',atomic)
    record=planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    assert (case.root/planner.FROZEN).read_bytes()==frozen
    assert len(json.loads((case.root/planner.PRIMARY).read_text())['candidate_ids'])==1202+len(record['candidate_ids'])


@pytest.mark.parametrize('failure',['active','not_terminal','wrong_hash'])
def test_prerequisite_failures_do_not_write_any_cohort(planner,metadata_case,failure):
    case=metadata_case
    if failure=='active':
        ledger={**case.ledger,'active':{'still-running':{'seconds':1}}};write_json(case.store/'resource_ledger.json',ledger)
    else:
        terminal=json.loads(case.terminal.read_text())
        if failure=='not_terminal':terminal['graph_design_terminal']=False
        else:terminal['evidence']['gate']['sha256']='wrong'
        write_json(case.terminal,terminal)
    with pytest.raises(ValueError):planner.freeze_optional_ar(case.store,case.profile,case.terminal,root=case.root)
    assert not (case.root/planner.FROZEN).exists()
    assert (case.root/planner.PRIMARY).read_bytes()==case.primary_raw
    assert not (case.root/planner.PRIMARY_COPY).exists()
