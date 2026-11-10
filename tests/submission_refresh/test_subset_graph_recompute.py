"""Changed membership must fit its own graph geometry, not slice parent F/G."""
import numpy as np
from experiments.subset_search import catalogue,runner
from experiments.submission_refresh.core import ArtifactStore

def test_each_subset_recomputes_spectral_geometry(monkeypatch,tmp_path):
    rng=np.random.RandomState(233);parent=rng.normal(size=(12,3));labels=np.arange(12)%2
    subsets={'a':np.arange(8),'b':np.arange(4,12)}
    monkeypatch.setattr(catalogue,'materialize',lambda c,root:(parent[subsets[c['candidate_id']]],labels[subsets[c['candidate_id']]],{'construction':'test_only'}))
    calls=[];original=runner.spectral_embedding
    def observed(X,K,**kwargs):
        calls.append(X.copy());return original(X,K,**kwargs)
    monkeypatch.setattr(runner,'spectral_embedding',observed)
    store=ArtifactStore(tmp_path/'objects')
    outputs=[runner.prepare({'candidate_id':cid,'preprocessing':'Y0'},tmp_path,store) for cid in ['a','b']]
    assert len(calls)==2
    for cid,X in zip(['a','b'],calls):np.testing.assert_array_equal(X,parent[subsets[cid]])
    assert outputs[0][-1]['objects']['F']['sha256']!=outputs[1][-1]['objects']['F']['sha256']
    assert outputs[0][-1]['objects']['A']['sha256']!=outputs[1][-1]['objects']['A']['sha256']
