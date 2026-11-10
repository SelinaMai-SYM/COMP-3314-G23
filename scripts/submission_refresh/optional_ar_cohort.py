"""Freeze a last-priority AR common-mask cohort from blind cost metadata.

Scope selection follows the completed fixed graph design. No matrix objects
or performance values are decoded. A frozen decision is immutable:
resume verifies/reuses it rather than consulting updated costs or scores.
"""
from __future__ import annotations
import argparse
import base64
import csv
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

ROOT=Path(__file__).resolve().parents[2]
PRIMARY='configs/subset_search/executable_cohort.json'
ORDER='configs/subset_search/executable_cohort_order.json'
PRIMARY_COPY='configs/subset_search/executable_cohort_primary_v1.json'
ORDER_COPY='configs/subset_search/executable_cohort_order_primary_v1.json'
FROZEN='configs/subset_search/optional_ar_common_cohort_v1.json'
OPTIONAL_ORDER='configs/subset_search/optional_ar_common_cohort_v1_order.json'
EVIDENCE='configs/subset_search/optional_ar_common_evidence_v1'
CATALOGUE='results/subset_search/candidate_catalogue.json'
PROTOCOL='configs/subset_search/protocol.yaml'
PROTOCOL_SHA='339bc600672ff04c7fdbb74e49ee596178ffa55b3df518cb8621cc131ed3ea28'
FIXED_AR=('AR_first7','AR_last7','AR_even7','AR_odd7')
GAMMAS=(1e-6,.001,1.,1000.,1000000.)
INITS=('RANDOM','VANILLA_KMEANSPP','SKLEARN_GREEDY_KMEANSPP')
SEED=20261110
CAP=1200
BUFFER=8*2**30
SCHEMA='optional-ar-cost-cohort-v1'


def _hash(raw):return hashlib.sha256(raw).hexdigest()


def _sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def _inside(root,relative):
    root=Path(root).resolve();relative=Path(relative);path=(root/relative).resolve()
    if relative.is_absolute() or root not in path.parents:raise ValueError('metadata path escapes its declared root')
    return path


def _json_bytes(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def _identity(value):return _hash(json.dumps(value,sort_keys=True,separators=(',',':')).encode())


def _string_end(text,index):
    index+=1
    while index<len(text):
        if text[index]=='\\':index+=2
        elif text[index]=='"':return index+1
        else:index+=1
    raise ValueError('unclosed metadata string')


def _skip_value(text,index):
    """Skip an unselected JSON value without decoding its metric numbers."""
    if text[index]=='"':return _string_end(text,index)
    if text[index] in '[{':
        stack=[']' if text[index]=='[' else '}'];index+=1
        while index<len(text):
            char=text[index]
            if char=='"':index=_string_end(text,index);continue
            if char in '[{':stack.append(']' if char=='[' else '}')
            elif char in ']}':
                if not stack or char!=stack.pop():raise ValueError('unbalanced metadata value')
                if not stack:return index+1
            index+=1
        raise ValueError('unclosed metadata value')
    while index<len(text) and text[index] not in ',}] \r\n\t':index+=1
    return index


def _project(raw,keys):
    """Decode selected top-level metadata only; trial/summary values stay raw."""
    text=raw.decode('utf-8');decoder=json.JSONDecoder();index=0;selected={}
    def ws(position):
        while position<len(text) and text[position].isspace():position+=1
        return position
    index=ws(index)
    if index>=len(text) or text[index]!='{':raise ValueError('metadata must be a JSON object')
    index=ws(index+1)
    while index<len(text) and text[index]!='}':
        key,index=decoder.raw_decode(text,index)
        if not isinstance(key,str):raise ValueError('metadata object key is not text')
        index=ws(index)
        if text[index]!=':':raise ValueError('metadata key has no value')
        index=ws(index+1)
        if key in keys:selected[key],index=decoder.raw_decode(text,index)
        else:index=_skip_value(text,index)
        index=ws(index)
        if index<len(text) and text[index]==',':index=ws(index+1)
        elif index>=len(text) or text[index]!='}':raise ValueError('invalid metadata delimiter')
    if index>=len(text) or text[index]!='}' or text[index+1:].strip():raise ValueError('invalid metadata object ending')
    return selected


def _references(value):
    if isinstance(value,dict):
        if {'sha256','path','kind','bytes'}<=value.keys():yield value
        else:
            for item in value.values():yield from _references(item)
    elif isinstance(value,list):
        for item in value:yield from _references(item)


def _fixed_object_inventory(store):
    inventory=[]
    for candidate in FIXED_AR:
        folder=store/'subset'/candidate;status_raw=(folder/'status.json').read_bytes()
        status=_project(status_raw,{'status','candidate_id','profile_only'})
        if status.get('status')!='COMPLETED' or status.get('candidate_id')!=candidate or status.get('profile_only') is not False:
            raise ValueError('all four fixed AR inputs must be completed before optional cost freezing')
        point_names=[f'SC__{init}.json' for init in INITS]+[
            f'{variant}__{gamma:g}__{init}.json' for variant in ['E8','E13'] for gamma in GAMMAS for init in INITS]
        solver_names=[f'{variant}__{gamma:g}__solver.json' for variant in ['E8','E13'] for gamma in GAMMAS]
        required=set(point_names+solver_names+['representation.json','source.json','status.json'])
        if any(not (folder/name).is_file() for name in required):raise ValueError('completed fixed AR input lacks required metadata')
        references={};metadata=[]
        for path in sorted(folder.glob('*.json')):
            raw=path.read_bytes();projection=_project(raw,{'status','candidate_id','objects','source_archive'})
            if path.name in point_names and (projection.get('status')!='COMPLETED' or projection.get('candidate_id')!=candidate):
                raise ValueError('fixed AR point is not a completed matching endpoint')
            metadata.append({'path':str(path.relative_to(store)),'sha256':_hash(raw),'bytes':len(raw)})
            for reference in _references(projection):
                length=reference['bytes']
                if isinstance(length,bool) or not isinstance(length,int) or length<0:raise ValueError('invalid object byte count')
                object_path=_inside(store,reference['path'])
                if not object_path.is_file() or object_path.stat().st_size!=length:raise ValueError('fixed AR object reference is unavailable or has a wrong byte count')
                old=references.get(reference['sha256'])
                if old is not None and old['bytes']!=length:raise ValueError('conflicting unique-object byte counts')
                references[reference['sha256']]={key:reference[key] for key in ['sha256','path','kind','bytes']}
        total=sum(reference['bytes'] for reference in references.values())
        if total<=0:raise ValueError('fixed AR object inventory must be nonempty')
        inventory.append({'candidate_id':candidate,'unique_object_bytes':total,'unique_objects':len(references),
            'references':sorted(references.values(),key=lambda reference:reference['sha256']),'metadata':metadata})
    return inventory


def _ledger(path):
    raw=path.read_bytes();state=json.loads(raw)
    if state.get('active'):raise ValueError('optional AR cohort freezing requires an empty active ledger')
    if not 0<float(state.get('limit_seconds',0))<=129600 or float(state.get('reserve_seconds',0))<7200:
        raise ValueError('the shared 36-hour allowance and two-hour reserve must be preserved')
    if state.get('max_workers')!=2:raise ValueError('the existing two-worker ledger is required')
    charges=[float(entry['charged_cpu_seconds']) for entry in state.get('entries',[])]
    if any(not math.isfinite(value) or value<0 for value in charges):raise ValueError('invalid shared ledger charge')
    return raw,state,max(0.,float(state['limit_seconds'])-float(state['reserve_seconds'])-sum(charges))


def _terminal(root,path):
    raw=Path(path).read_bytes();decision=json.loads(raw)
    if decision.get('schema')!='optional-ar-terminal-decision-v1' or any(decision.get(key) is not True
        for key in ['graph_design_terminal','G4_G5_terminal','unrun_work_frozen']):
        raise ValueError('an explicit graph/G4 terminal-decision record is required')
    if decision.get('G4_G5_disposition') not in {'COMPLETED','FAILED_OR_INCOMPLETE_WITHIN_ALLOWANCE','NOT_PERMITTED'}:
        raise ValueError('the terminal record must state the G4/G5 disposition')
    evidence=decision.get('evidence',{});copies={'terminal_decision.json':raw};references={}
    for role,filename in [('graph_coverage','graph_execution_coverage.csv'),('gate','extension_gate.json')]:
        reference=evidence.get(role,{})
        source=_inside(root,reference.get('path',''))
        content=source.read_bytes()
        if _hash(content)!=reference.get('sha256'):raise ValueError('terminal-decision evidence hash mismatch')
        copies[filename]=content;references[role]={'path':reference['path'],'sha256':_hash(content)}
    graph_rows=list(csv.DictReader(io.StringIO(copies['graph_execution_coverage.csv'].decode())))
    intended_raw=(root/'configs/submission_refresh/graph_queue.json').read_bytes()
    intended={task['run_id'] for task in json.loads(intended_raw)['tasks']}
    if len(graph_rows)!=362 or len(intended)!=362 or {row['run_id'] for row in graph_rows}!=intended:
        raise ValueError('terminal graph coverage must retain all 362 intended tasks')
    if any(row.get('controller_status') in {'RUNNING','PENDING'} for row in graph_rows):
        raise ValueError('graph coverage still contains live or pending controllers')
    gate=_project(copies['extension_gate.json'],{'G4_G5_status','promotion_passed'})
    if decision['G4_G5_disposition']=='NOT_PERMITTED' and gate.get('promotion_passed') is not False:
        raise ValueError('G4/G5 cannot be marked not permitted after a passed gate; use an explicit allowance/incomplete disposition')
    if decision['G4_G5_disposition']=='COMPLETED' and gate.get('G4_G5_status')!='COMPLETE_CERTIFIED_FOUR_BENCHMARKS':
        raise ValueError('a completed G4/G5 disposition requires the recorded complete four-benchmark state')
    return copies,{'decision_sha256':_hash(raw),'evidence':references,'graph_queue_sha256':_hash(intended_raw),
        'G4_G5_disposition':decision['G4_G5_disposition'],'gate_status':gate.get('G4_G5_status')}


def plan_counts(remaining_seconds,profile_cpu,rounding_cpu,max_object_bytes,free_bytes,store_bytes,family_count):
    values=[remaining_seconds,profile_cpu,rounding_cpu,max_object_bytes,free_bytes,store_bytes]
    if any(not math.isfinite(float(value)) or value<0 for value in values) or profile_cpu<=0 or max_object_bytes<=0:
        raise ValueError('cost/disk metadata must be finite, nonnegative and nonempty')
    if isinstance(family_count,bool) or not isinstance(family_count,int) or family_count<0:raise ValueError('invalid optional family count')
    estimate=2*(profile_cpu+33*50*rounding_cpu)
    per_mask_bytes=(15*int(max_object_bytes)+3)//4
    disk_available=max(0,int(free_bytes)-2*int(store_bytes)-BUFFER)
    cpu_cap=max(0,math.floor(remaining_seconds/estimate));disk_cap=disk_available//per_mask_bytes
    return {'cpu_estimate_seconds_per_mask':estimate,'cpu_count_cap':cpu_cap,'disk_count_cap':disk_cap,
        'family_count_cap':family_count,'selected_count':min(cpu_cap,disk_cap,family_count),
        'existing_store_extra_copy_reserve_bytes':2*int(store_bytes),'free_buffer_bytes':BUFFER,
        'per_new_mask_reserved_bytes':per_mask_bytes,'disk_available_for_new_masks_bytes':disk_available,
        'formula':'2 * (blind_AR_profile_total_CPU + 33 * 50 * rounding_CPU_per_seed)',
        'disk_formula':'free - 2*existing_store_bytes - 8GiB; per mask = ceil(3*1.25*max_fixed_AR_unique_object_bytes)',
        'cpu_limit_per_candidate':CAP}


def _disk_snapshot(store):
    size=sum(path.stat().st_size for path in store.rglob('*') if path.is_file())
    usage=shutil.disk_usage(store)
    return {'artifact_store_bytes':size,'total_bytes':usage.total,'used_bytes':usage.used,'free_bytes':usage.free}


def _profile_source_qualification(root,profile):
    """Cost provenance only: differing bytes never imply a fit/cache identity."""
    source=profile.get('source') or {};recorded=source.get('source_files',{})
    paths=sorted((root/'SSC_method').glob('*.py'))+[root/'experiments/v2_kmeans_protocol/kmeans_trials.py']
    comparisons=[]
    for path in paths:
        relative=str(path.relative_to(root));current=_sha(path) if path.is_file() else None
        previous=recorded.get(relative)
        comparisons.append({'path':relative,'recorded_sha256':previous,'current_sha256':current,
            'byte_status':'IDENTICAL' if previous is not None and previous==current else 'DIFFERENT' if previous is not None and current is not None else 'UNAVAILABLE'})
    return {'recorded_source_commit':source.get('source_commit'),'recorded_implementation_hash':source.get('implementation_hash'),
        'recorded_environment':source.get('environment'),'source_byte_comparisons':comparisons,
        'archived_effective_code_identity':'NOT_ASSERTED',
        'qualification':'This is blind cost-approximation evidence on matching processed X/y, not a fit-output/cache identity. Byte differences or unavailable archived effective-code/environment evidence remain explicit; no identity is invented and no scientific output is reused by this planner.'}


def _payload(path,raw,previous=None):
    return {'path':path,'sha256':_hash(raw),'bytes':len(raw),'previous_sha256':previous,
        'content_base64':base64.b64encode(raw).decode('ascii')}


def _atomic(path,raw,*,exclusive=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,temporary=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        if exclusive:os.link(temporary,path)
        else:os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def _publish_frozen(root,record,catalogue,ledger):
    expected=record.get('freeze_id');body={key:value for key,value in record.items() if key!='freeze_id'}
    if record.get('schema')!=SCHEMA or expected!=_identity(body):raise ValueError('optional AR frozen decision identity mismatch')
    if _sha(root/CATALOGUE)!=record['catalogue_sha256'] or _sha(root/PROTOCOL)!=record['protocol_sha256']:
        raise ValueError('frozen optional AR catalogue/protocol changed')
    before=record['ledger_snapshot']['state']
    if (ledger.get('entries',[])[:len(before.get('entries',[]))]!=before.get('entries',[])
        or any(ledger.get(key)!=before.get(key) for key in ['limit_seconds','reserve_seconds','max_workers'])):
        raise ValueError('optional AR resume requires the same append-only shared ledger')
    lookup={candidate['candidate_id']:candidate for candidate in catalogue['candidates']}
    permutation=record['canonical_permutation'];selected=record['candidate_ids']
    if len(permutation)!=len(set(permutation)) or any(value not in lookup or lookup[value].get('alias_of')
        or lookup[value].get('family')!='AR_common_mask' for value in permutation) or selected!=permutation[:len(selected)]:
        raise ValueError('frozen optional AR canonical prefix is invalid')
    planned=[]
    allowed={PRIMARY,ORDER,PRIMARY_COPY,ORDER_COPY,OPTIONAL_ORDER}|{EVIDENCE+'/'+name for name in
        ['terminal_decision.json','graph_execution_coverage.csv','extension_gate.json','blind_AR_profile.json']}
    paths=[item['path'] for item in record['files_to_publish']]
    if len(paths)!=len(set(paths)) or set(paths)!=allowed:raise ValueError('unexpected optional AR publication targets')
    for item in record['files_to_publish']:
        path=_inside(root,item['path']);raw=base64.b64decode(item['content_base64'],validate=True)
        if len(raw)!=item['bytes'] or _hash(raw)!=item['sha256']:raise ValueError('frozen optional AR publication payload is corrupt')
        current=_sha(path) if path.is_file() else None
        if current not in {item['sha256'],item['previous_sha256']}:
            raise ValueError('optional AR publication target was changed independently: '+item['path'])
        planned.append((path,raw,current==item['sha256']))
    # Validate every target before any repair/write. A crash after the frozen
    # decision is durable resumes these exact bytes, never a fresh cost choice.
    for path,raw,done in planned:
        if not done:_atomic(path,raw)
    if any(_sha(path)!=_hash(raw) for path,raw,_ in planned):raise ValueError('optional AR publication verification failed')
    return record


def freeze_optional_ar(artifact_root,profile_record,terminal_record,*,root=ROOT):
    """Explicit invocation only; initial decision is frozen before union writes."""
    root=Path(root).resolve();store=Path(artifact_root).resolve();frozen=root/FROZEN
    if not (store/'resource_ledger.json').is_file():raise ValueError('the existing shared ledger is required')
    with (store/'resource_ledger.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger_raw,ledger,remaining=_ledger(store/'resource_ledger.json')
        catalogue_raw=(root/CATALOGUE).read_bytes();catalogue=json.loads(catalogue_raw)
        if frozen.exists():return _publish_frozen(root,json.loads(frozen.read_text()),catalogue,ledger)
        if _sha(root/PROTOCOL)!=PROTOCOL_SHA:raise ValueError('the unchanged frozen subset protocol is required')
        primary_raw=(root/PRIMARY).read_bytes();order_raw=(root/ORDER).read_bytes()
        primary=json.loads(primary_raw);order=json.loads(order_raw);ids=primary['candidate_ids']
        lookup={candidate['candidate_id']:candidate for candidate in catalogue['candidates']}
        if (len(ids)!=1202 or len(set(ids))!=1202 or set(order['candidate_ids'])!=set(ids)
            or len(order['candidate_ids'])!=1202 or primary.get('catalogue_sha256')!=_hash(catalogue_raw)
            or primary.get('cpu_limit_per_candidate')!=CAP
            or any(value not in lookup or lookup[value].get('alias_of') for value in ids)):
            raise ValueError('the exact canonical 1202-input primary cohort/order must be preserved')
        terminal_copies,terminal=_terminal(root,terminal_record)
        profile_path=Path(profile_record)
        if not profile_path.is_absolute():profile_path=_inside(store,profile_path)
        elif store not in profile_path.resolve().parents:raise ValueError('blind profile must be inside the same artifact store')
        profile_raw=profile_path.read_bytes();profile=json.loads(profile_raw)
        timings=profile.get('solver_timings',[])
        if (profile.get('status')!='PROFILE_ONLY_INELIGIBLE' or profile.get('profile_only') is not True
            or profile.get('candidate_id')!='AR_first7' or 'trials' in profile or 'summary' in profile
            or len(timings)!=10 or {(item['variant'],float(item['gamma'])) for item in timings}!={(variant,gamma) for variant in ['E8','E13'] for gamma in GAMMAS}):
            raise ValueError('the declared complete label-blind AR_first7 profile is required')
        profiled=profile.get('candidate',{});reference=lookup['AR_first7']
        if (not profiled.get('fingerprint') or profiled.get('fingerprint')!=reference.get('fingerprint')
            or any(profiled.get(key)!=reference.get(key) for key in ['prep','n','classes'])):
            raise ValueError('the blind AR profile must match the exact frozen Y0 input fingerprint and dimensions')
        fixed=_fixed_object_inventory(store);disk=_disk_snapshot(store)
        profile_cpu=max(float(profile['cpu_seconds']),float(profile.get('process_cpu_seconds',profile['cpu_seconds'])))
        family=[candidate for candidate in catalogue['candidates'] if candidate.get('family')=='AR_common_mask']
        canonical=sorted(candidate['candidate_id'] for candidate in family if not candidate.get('alias_of'))
        if not canonical or len(canonical)!=len(set(canonical)) or set(canonical)&set(ids):raise ValueError('invalid canonical optional AR family')
        import numpy as np
        permutation=[canonical[int(index)] for index in np.random.RandomState(SEED).permutation(len(canonical))]
        costs=plan_counts(remaining,profile_cpu,float(profile['rounding_cpu_per_seed']),
            max(item['unique_object_bytes'] for item in fixed),disk['free_bytes'],disk['artifact_store_bytes'],len(canonical))
        selected=permutation[:costs['selected_count']]
        union={**primary,'version':2,'candidate_ids':ids+selected,
            'ar_common_masks':{'frozen_record':FROZEN,'selected_count':len(selected),'permutation_seed':SEED},
            'primary_cohort_preserved_at':PRIMARY_COPY}
        union_order={**order,'version':2,'candidate_ids':order['candidate_ids']+selected,
            'optional_AR_order':'frozen permutation prefix appended after unchanged primary order'}
        files=[_payload(PRIMARY_COPY,primary_raw),_payload(ORDER_COPY,order_raw),
            _payload(PRIMARY,_json_bytes(union),_hash(primary_raw)),_payload(ORDER,_json_bytes(union_order),_hash(order_raw)),
            _payload(OPTIONAL_ORDER,_json_bytes({'version':1,'candidate_ids':selected,'permutation_seed':SEED}))]
        for name,raw in {**terminal_copies,'blind_AR_profile.json':profile_raw}.items():files.append(_payload(EVIDENCE+'/'+name,raw))
        record={'schema':SCHEMA,'version':1,'catalogue_sha256':_hash(catalogue_raw),'protocol_sha256':PROTOCOL_SHA,
            'planner_source_path':'scripts/submission_refresh/optional_ar_cohort.py','planner_source_sha256':_sha(Path(__file__)),
            'candidate_ids':selected,'cpu_limit_per_candidate':CAP,'canonical_permutation':permutation,
            'permutation_seed':SEED,'rng':'numpy.random.RandomState','numpy_version':np.__version__,
            'unrun_candidate_ids':permutation[len(selected):],
            'catalogued_aliases':{candidate['candidate_id']:candidate['alias_of'] for candidate in family if candidate.get('alias_of')},
            'all_not_newly_scheduled_family_ids':sorted(set(candidate['candidate_id'] for candidate in family)-set(selected)),
            'primary_cohort_sha256':_hash(primary_raw),'primary_order_sha256':_hash(order_raw),
            'original_primary_count':len(ids),'union_count':len(ids)+len(selected),
            'profile':{'path_relative_to_artifact_root':str(profile_path.resolve().relative_to(store)),
                'sha256':_hash(profile_raw),'cpu_seconds':profile['cpu_seconds'],'rounding_cpu_per_seed':profile['rounding_cpu_per_seed']},
            'profile_total_cpu_seconds_used':profile_cpu,
            'profile_total_cpu_definition':'Maximum of recorded process_cpu_seconds (when present) and recorded cpu_seconds.',
            'profile_source_qualification':_profile_source_qualification(root,profile),
            'profile_membership_identity':{'exact_processed_fingerprint_verified':True,
                'profile_manifest_sha256':profiled.get('manifest_sha256'),'frozen_manifest_sha256':reference.get('manifest_sha256'),
                'qualification':'Manifest metadata versions may differ; exact processed X/y fingerprint, preprocessing and dimensions must match.'},
            'costs':costs,'remaining_normal_budget_seconds':remaining,'disk_snapshot':disk,
            'ledger_snapshot':{'sha256':_hash(ledger_raw),'state':ledger},'terminal_decision':terminal,
            'fixed_AR_object_inventories':fixed,'files_to_publish':files,
            'score_values_decoded':False,'matrix_objects_opened':False,'score_based_scope_selection':False,
            'resume_policy':'Verify/reuse this frozen prefix and publication bytes; never recompute from updated cost, disk or scores.'}
        record['freeze_id']=_identity(record)
        # Validate all payloads/targets before making the immutable decision
        # durable. Publication itself uses compare-and-swap accepted hashes.
        for item in files:
            path=_inside(root,item['path']);current=_sha(path) if path.is_file() else None
            if current not in {item['sha256'],item['previous_sha256']}:raise ValueError('optional AR target already has unrelated contents: '+item['path'])
        expected_inputs={root/CATALOGUE:_hash(catalogue_raw),root/PROTOCOL:PROTOCOL_SHA,
            root/PRIMARY:_hash(primary_raw),root/ORDER:_hash(order_raw),profile_path:_hash(profile_raw),
            Path(terminal_record):terminal['decision_sha256']}
        for reference in terminal['evidence'].values():expected_inputs[_inside(root,reference['path'])]=reference['sha256']
        for item in fixed:
            for reference in item['metadata']:expected_inputs[_inside(store,reference['path'])]=reference['sha256']
        if any(_sha(path)!=expected for path,expected in expected_inputs.items()):raise ValueError('optional AR freeze inputs changed during validation')
        _atomic(frozen,_json_bytes(record),exclusive=True)
        return _publish_frozen(root,record,catalogue,ledger)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-root',required=True)
    parser.add_argument('--profile-record',required=True)
    parser.add_argument('--terminal-record',required=True)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    record=freeze_optional_ar(args.artifact_root,args.profile_record,args.terminal_record,root=args.root)
    print(json.dumps({'freeze_id':record['freeze_id'],'selected_count':len(record['candidate_ids']),
        'union_count':record['union_count'],'frozen_record':FROZEN},sort_keys=True))


if __name__=='__main__':main()
