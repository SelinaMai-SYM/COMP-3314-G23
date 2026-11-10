"""Current v2 scalar records coexist with controls without merging contexts."""
import copy
import hashlib
import pytest
from experiments.submission_refresh import ensc_campaign as campaign


def ref(name):
    sha=hashlib.sha256(name.encode()).hexdigest()
    return {'sha256':sha,'path':'objects/'+sha[:2]+'/'+sha+'.npz','kind':'compressed_array','bytes':1}


@pytest.fixture
def current_records(monkeypatch):
    # These are compact scalar records only, with no available matrices/store.
    # Bootstrap numerics are tested elsewhere; this fixture isolates context
    # compatibility and deliberately never runs another bootstrap or fit.
    import experiments.next_round.evaluate as evaluate
    monkeypatch.setattr(evaluate,'paired',lambda *args,**kwargs:{'delta_pp':0.,'ci_lower_pp':0.,'ci_upper_pp':0.})
    inputs={name:ref(name) for name in ['X','y','F0','U']};records=[]
    for definition in campaign.intended_configurations('ORL_att92'):
        graph=definition['graph'];ensc=graph.startswith('S_tau');native=definition['anchor']=='native_spectral'
        context={'schema':'G4-resume-context-v2','definition':definition,'input_objects':inputs,
            'anchor':None if native else inputs[definition['anchor']],'graph':ref(graph),'graph_shape':[40,40],'graph_nnz':100,
            'graph_metadata_fingerprint':graph,'scientific_source_fingerprint':'shared-science',
            'construction_source_fingerprint':'shared-construction','input_adapter_fingerprint':'input-adapter-v2',
            'backend_source_sha256':'true-elastic-net-backend' if ensc else None,
            'environment':{'python':'fixture'},'rounding':{'initialization':'SKLEARN_GREEDY_KMEANSPP','n_init':1,'seeds':list(range(50))}}
        record={**definition,'status':'COMPLETED','resume_context':context,
            'source':{'implementation_hash':'shared-construction' if native else 'shared-science'},
            'trials':[{'seed':seed,'acc':.5,'nmi':.6} for seed in range(50)],'solver':{'certified':True},
            'mass_matching':{'count_qualified':True},'objects':{'G':inputs['F0']}}
        records.append({'record_path':'ensc_jobs/formal/records/'+str(len(records))+'.json',
            'job_record_path':'ensc_jobs/formal/status.json','record':record})
    return {'schema':'ensc-scalar-metadata-v1','conditional_status':'FORMAL_JOBS_RECORDED',
        'jobs':[{'record_path':'ensc_jobs/formal/status.json','record':{'task':{'dataset':'ORL_att92'},'status':'COMPLETED'}}],
        'records':records}


def test_all_44_current_v2_contexts_accept_nonbackend_controls_and_two_ensc_graphs(current_records):
    derived=campaign.derive_ensc_metadata(current_records)
    row=next(item for item in derived['macro']['dataset_status'] if item['dataset']=='ORL_att92')
    assert row['qualified'] is True and row['complete_records']==44
    provenance=row['input_and_source_provenance']
    assert provenance['common_context']['resume_context_schema']=='G4-resume-context-v2'
    assert provenance['common_context']['input_adapter_fingerprint']=='input-adapter-v2'
    assert provenance['construction_context']=={'construction_source_fingerprint':'shared-construction'}
    assert provenance['ensc_backend_source_sha256']=='true-elastic-net-backend'
    assert provenance['graphs']['W0']['backend_source_sha256'] is None
    assert provenance['graphs']['S_tau0.95']['backend_source_sha256']=='true-elastic-net-backend'
    assert derived['macro']['four_benchmark_ACC_gain_pp'] is None  # Three benchmarks remain absent.


def test_complete_legacy_v1_scalar_track_remains_explicitly_supported(current_records):
    for entry in current_records['records']:
        context=entry['record']['resume_context'];context['schema']='G4-resume-context-v1'
        context.pop('input_adapter_fingerprint')
        if not entry['record']['graph'].startswith('S_tau'):context['construction_source_fingerprint']=None
    derived=campaign.derive_ensc_metadata(current_records)
    row=derived['macro']['dataset_status'][0]
    assert row['qualified'] is True
    assert row['input_and_source_provenance']['common_context']['resume_context_schema']=='G4-resume-context-v1'
    assert row['input_and_source_provenance']['common_context']['input_adapter_fingerprint'] is None


@pytest.mark.parametrize('change',['missing_adapter','adapter_mixture','schema_mixture','backend_mixture','backend_on_control'])
def test_current_scalar_contexts_reject_missing_or_mixed_bindings(current_records,change):
    evidence=copy.deepcopy(current_records)
    first=evidence['records'][0]['record']['resume_context']
    if change=='missing_adapter':first.pop('input_adapter_fingerprint')
    elif change=='adapter_mixture':first['input_adapter_fingerprint']='another-adapter'
    elif change=='schema_mixture':first['schema']='G4-resume-context-v1';first.pop('input_adapter_fingerprint')
    elif change=='backend_on_control':first['backend_source_sha256']='unexpected-backend'
    else:
        entry=next(item for item in evidence['records'] if item['record']['family']=='S_tau1')
        entry['record']['resume_context']['backend_source_sha256']='another-backend'
    with pytest.raises(ValueError,match='v2 resume|mix|non-EnSC control'):
        campaign.derive_ensc_metadata(evidence)
