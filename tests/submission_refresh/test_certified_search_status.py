"""Pure metadata coverage: availability must never become a certified winner."""
import pytest
from experiments.subset_search.certified_status import certified_search_status,UNAVAILABLE
from experiments.subset_search.markdown import benchmark_markdown


def complete_row(candidate='A',alias=None,pool='specification_compatible'):
    return {'benchmark':'ORL','pool':pool,'candidate_id':candidate,'alias_of':alias,
            'config_id':candidate+'|E8|1|RANDOM','variant':'E8','gamma_nominal':1.,
            'initialization':'RANDOM','endpoint':'mean_sample_sd_50'}


@pytest.mark.parametrize('public',[False,True])
def test_availability_preserves_alias_counts_empty_pools_and_both_endpoints(monkeypatch,public):
    from experiments.subset_search import markdown
    monkeypatch.setattr(markdown,'_public_mode',lambda:public)
    rows=[complete_row(),complete_row('alias','A'),complete_row('diagnostic',pool='diagnostic')]
    result=certified_search_status(rows,{'ORL':{'specification_compatible','adapted'},'USPS':{'specification_compatible'}})
    assert len(result)==6
    assert {r['endpoint'] for r in result}=={'mean_sample_sd_50','native_best_of_50'}
    assert all(r['status']==UNAVAILABLE and r['certified_closest_config_id'] is None for r in result)
    assert all(r['comparable_certified_search_configurations']==0 and not r['certificate_transfer_allowed'] for r in result)
    orl=[r for r in result if r['benchmark']=='ORL' and r['pool']=='specification_compatible']
    assert all(r['historical_complete_configurations']==2 and r['historical_complete_canonical_configurations']==1 and r['historical_complete_unique_inputs']==1 for r in orl)
    assert all(r['historical_complete_configurations']==0 for r in result if r['pool']=='adapted' or r['benchmark']=='USPS')
    text=benchmark_markdown('ORL',[],{},result)
    if public:
        assert 'Comparable certified subset-search coverage is unavailable' in text
        assert 'its certificate does not certify a finite-iteration IRLS output' in text
    else:
        assert UNAVAILABLE in text and 'cannot be transferred to an IRLS G' in text
    assert '2 / 1' in text and 'certified_search_status.csv' in text


def test_availability_rejects_duplicate_or_native_input_instead_of_overcounting():
    row=complete_row()
    with pytest.raises(ValueError,match='duplicate complete configuration'):
        certified_search_status([row,row])
    with pytest.raises(ValueError,match='complete mean configuration'):
        certified_search_status([{**row,'endpoint':'native_best_of_50'}])
