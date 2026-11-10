"""Source conflicts are evidence, while A and W use their actual coordinates."""
import csv
import hashlib
import json
import numpy as np
from scipy import sparse
from experiments.submission_refresh.source_audit import duplicate_audit,audit_sources
from experiments.submission_refresh.correct_graph_diagnostics import regenerate
from experiments.v3_reproduction.provenance import sha256_array


def test_duplicate_conflicts_are_retained_without_rejecting_binalpha():
    X=np.array([[0.,1.],[0.,1.],[2.,2.]])
    result=duplicate_audit(X,np.array([0,1,1]))
    assert result['unique_rows']==2 and result['duplicate_extra_rows']==1
    assert result['cross_class_duplicate_groups']==1
    assert result['duplicate_groups'][0]['original_indices']==[0,1]
    assert result['original_to_first_occurrence_row']==[0,0,1]
    assert not result['official_input_modified']


def test_only_umist_conflict_check_is_strict(tmp_path,monkeypatch):
    import experiments.submission_refresh.source_audit as audit
    X=np.array([[0.,1.],[0.,1.],[2.,2.]])
    monkeypatch.setattr(audit,'PARENTS',{'BinAlpha_parent36':('BinAlpha','binalpha/data','binaryalphadigs36'),'UMIST_test':('UMIST','umist/data','test')})
    monkeypatch.setattr(audit,'load_parent',lambda *args:(X,np.array([0,1,1]),{}))
    result=audit_sources(tmp_path,tmp_path/'audit')
    rows={r['parent_id']:r for r in result['parents']}
    assert rows['BinAlpha_parent36']['status']=='AUDITED_WITH_DUPLICATE_LABEL_CONFLICTS'
    assert rows['UMIST_test']['status']=='FAILED_UMIST_DUPLICATE_LABEL_CONSISTENCY'
    assert np.array_equal(X,np.array([[0.,1.],[0.,1.],[2.,2.]]))
    mapping=rows['BinAlpha_parent36']['duplicate_map']
    assert (tmp_path/'audit'/mapping['path']).is_file()


def test_recovered_A_lengths_use_X_and_W_lengths_use_F(tmp_path):
    cache=tmp_path/'cache';folder=cache/'unit__Y0';folder.mkdir(parents=True)
    X=np.array([[0.],[1.],[10.]]);F=np.array([[0.],[10.],[11.]]);y=np.array([0,0,1])
    W=sparse.csr_matrix([[0.,1.,0.],[1.,0.,1.],[0.,1.,0.]])
    for name,array in [('X',X),('F',F),('y',y)]:np.save(folder/(name+'.npy'),array)
    sparse.save_npz(folder/'W.npz',W);sparse.save_npz(folder/'A.npz',W)
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    meta={'dataset':'unit','prep':'Y0','feature_hash':sha256_array(X),'label_hash':sha256_array(y),
          'F_hash':sha256_array(F),'W_hash':sha(folder/'W.npz'),'A_hash':sha(folder/'A.npz')}
    (folder/'meta.json').write_text(json.dumps(meta))
    jobs=tmp_path/'jobs';jobs.mkdir()
    fitted_hash=hashlib.sha256(np.ascontiguousarray(W.data).tobytes()+np.ascontiguousarray(W.indices).tobytes()+np.ascontiguousarray(W.indptr).tobytes()).hexdigest()
    job={'status':'COMPLETED','run_id':'unit-job','task':{'dataset':'unit','prep':'Y0','phase':'A','kind':'original','gamma':1.},
         'representation':meta,'fitted_graph_hash':fitted_hash,'graph':{'within_class_components_mean':1.}}
    (jobs/'unit-job.json').write_text(json.dumps(job))
    result=regenerate(cache_root=cache,jobs_root=jobs,output=tmp_path/'out')
    assert result['rows_by_graph_role']=={'A':1,'W':1}
    rows={r['graph_role']:r for r in csv.DictReader((tmp_path/'out/graph_diagnostics_schema2.csv').open())}
    assert rows['A']['length_space']=='X' and rows['W']['length_space']=='F'
    assert float(rows['A']['cross_edge_length_AUROC'])==1.
    assert float(rows['W']['cross_edge_length_AUROC'])==0.
    assert not result['failures']
