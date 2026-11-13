import json,os
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse,linalg
from experiments.extension_round2.common import config,DEFAULT_CONFIG,ArtifactStore,save_continuation,recover_continuation,identity
from experiments.extension_round2.calibration import MovementPath
from SSC_method.graph_construction import knn_affinity


def test_label_free_interval_calibration_and_bounded_continuation(tmp_path):
    H=np.array([[-1.],[1.]]);W=sparse.csr_matrix([[0.,1.],[1.,0.]]);store=ArtifactStore(tmp_path)
    path=MovementPath(H,W,'QSSC',{},store,'toy',30,{'benchmark':'toy','source_fingerprint':'toy'});out=path.target(.05)
    assert out['matched'] and out['certified'];assert abs(out['actual_movement']-.05)+out['movement_error']<=.0025
    assert out['refinements']<=6 and out['distinct_lambda_count']<=32
    first=path.target(.02);assert first['matched'];assert len(path.state['distinct'])<=32
    folder=tmp_path/'continuation'
    save_continuation(folder,{'G':H,'nested':{'q':np.array([1.,2.])},'scalar':2})
    save_continuation(folder,{'G':H+1,'nested':{'q':np.array([2.,3.])},'scalar':3})
    assert len(list(folder.glob('generation-*')))==1;assert np.array_equal(recover_continuation(folder)['G'],H+1)


def test_locked_membership_Y3_and_per_benchmark_rounding():
    root=os.environ.get('COMP3314_ROUND2_ARTIFACT_ROOT')
    if not root:pytest.skip('Frozen input objects are checked by the round2 verify entry point')
    from experiments.extension_round2.report import locked_for_derivation
    from experiments.extension_round2.common import locked,source_files
    spec,lock,store=locked_for_derivation(root)
    if source_files()!=lock['source_files']:
        with pytest.raises(ValueError,match='source/environment changed|protocol hash changed'):locked(root)
    assert len(lock['cohorts'])==8
    for b,row in lock['cohorts'].items():
        assert row['initialization']==spec['cohorts'][b]['initialization'];assert len(row['selected_indices'])==row['n']
        H=store.get(row['objects']['H']);U=store.get(row['objects']['U0']);W=store.get(row['objects']['W0'])
        assert H.shape==U.shape==(row['n'],row['K']);assert linalg.norm(U.T@U-np.eye(row['K']))<1e-7
        if row['prep']=='Y3':
            assert b=='YaleB';norms=np.linalg.norm(U,axis=1,keepdims=True);expected=np.divide(U,norms,out=np.zeros_like(U),where=norms>0);assert np.array_equal(H,expected)
        else:assert np.array_equal(H,U)
        rebuilt,_=knn_affinity(H,k=5);assert (W!=rebuilt).nnz==0
    assert lock['cohorts']['USPS']['n']==9298
    assert lock['cohorts']['UMIST']['features']==10304
    assert lock['cohorts']['MSRA50']['n']==1799
