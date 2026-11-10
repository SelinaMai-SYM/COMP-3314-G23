import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh.selection import rank,distances,summarize,capability
from experiments.submission_refresh.core import ArtifactStore,ResourceLedger

def test_joint_counterexample_and_ties():
    p={'acc':75,'nmi':80}
    a=distances({'config_id':'a','acc_mean':75,'nmi_mean':65,'variant':'E8'},p)
    b=distances({'config_id':'b','acc_mean':76,'nmi_mean':79,'variant':'E8'},p)
    assert rank([a,b])[0]['config_id']=='b'
    assert rank([{**b,'variant':'E13','config_id':'a'},b])[0]['config_id']=='b'

def test_complete_mean_and_native_endpoint():
    rows=[{'seed':i,'acc':.5,'nmi':.6,'inertia':50-i} for i in range(50)]
    result=summarize(rows);assert result['native_best']['seed']==49;assert result['native_best']['acc_sd'] is None
    with pytest.raises(ValueError):summarize(rows[:-1])
    with pytest.raises(ValueError):summarize(rows+[rows[0]])

def test_objects_and_archive_detect_corruption(tmp_path):
    store=ArtifactStore(tmp_path);a=np.arange(10.);r=store.put(a);s=store.put(sparse.eye(3))
    np.testing.assert_array_equal(store.get(r),a)
    store.archive([r,s],tmp_path/'bundle.tar.gz')
    (tmp_path/r['path']).write_bytes(b'bad')
    with pytest.raises(ValueError):store.get(r)

def test_shared_ledger_reservations(tmp_path):
    l=ResourceLedger(tmp_path);assert l.reserve('a',100,'subset');assert l.reserve('b',100,'baseline');assert not l.reserve('c',1,'subset')
    l.finish('a',20,'COMPLETED');assert l.reserve('c',1,'confirmation');l.finish('b',None,'KILLED');assert l.state()['entries'][-1]['charged_cpu_seconds']==100
