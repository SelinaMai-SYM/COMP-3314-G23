"""End-to-end saved-array certificates and atomic scalar recovery on synthetic data."""
import copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from scipy import sparse
from experiments.submission_refresh.core import ArtifactStore,atomic_json,digest
from experiments.submission_refresh.selection import summarize
from experiments.extension_verification.worker import fit
from experiments.extension_verification.reporting import rebuild


def test_saved_fit_has_exact_recomputable_certificate_without_labels(tmp_path):
    store=ArtifactStore(tmp_path/'objects');H=np.array([[0.,0.],[4.,0.]])
    entry={'objects':{'F0':store.put(H),'W0':store.put(sparse.csr_matrix([[0.,1.],[1.,0.]]))},'candidate_id':'synthetic','n':2,'K':2,'role':'synthetic','qualification':'synthetic'}
    lock={'datasets':{'synthetic':entry},'source_fingerprint':'fixture','protocol_sha256':'fixture','source_snapshot':store.put({'synthetic':True})}
    task={'benchmark':'synthetic','panel':'original','kind':'relative','gamma':.8,'parameters':{'eta':.25},'fit_id':'synthetic-fit','attempt_id':'attempt1','iteration_ceiling':30000,'cpu_allowance':60,'source_fingerprint':'fixture','protocol_sha256':'fixture'}
    with patch('experiments.extension_verification.worker.load_locked',return_value=({},lock,store)):
        record=fit(task,'unused',store.root)
    from method_extension.extension_verification.convex import Problem
    problem=Problem(H,store.get(entry['objects']['W0']),.8,kind='relative',eta=.25)
    result=problem.dual(store.get(record['objects']['q']),store.get(record['objects']['p']),repair=False)
    assert record['solver']['certified']
    assert problem.primal(store.get(record['objects']['G']))-result['dual']==record['solver']['absolute_gap']
    assert not record['labels_loaded_for_fitting']
    assert 'labels' not in entry['objects']
    state=store.get(record['checkpoint']);assert state['iterations_total']==record['solver']['iterations_total']


def fixture_release(tmp_path):
    names=['ORL','YaleB','AR','JAFFE','UMIST','BinAlpha','MSRA50','USPS']
    spec={'inputs':{'dataset_order':names}}
    entry={'candidate_id':'synthetic','role':'synthetic','qualification':'synthetic','gamma_references':{panel:{'reference_status':'VALID','primary_gamma':1} for panel in ['original','angular']}}
    lock={'protocol_sha256':'fixture','datasets':{b:entry for b in names}}
    point={'point_id':'synthetic','benchmark':'ORL','candidate_id':'synthetic','role':'synthetic','qualification':'synthetic','method':'SSC','panel':'original','primary':True,'parameters':{},'gamma':1.,'output_normalization':'none','n':10,'K':2,'solver':{'certified':True,'numerically_active':True},'objects':{'G':{'sha256':'G'},'Q':{'sha256':'Q'}},'source_fingerprint':'fixture','protocol_sha256':'fixture'}
    trials=[{'seed':i,'acc':.8,'nmi':.7,'inertia':i+1.} for i in range(50)];summary=summarize(trials);summary.pop('native_best')
    evaluation={'point_id':'synthetic','Q_object':point['objects']['Q'],'summary':summary,'trials':trials,'native_best':{'seed':0,'acc':.8,'nmi':.7,'inertia':1.}}
    packet={'protocol':spec,'datasets_lock':lock,'records':[{'point':point,'evaluation':evaluation}],'gates':{},'diagnostics':{},'run_state':{}}
    return packet


def write_release(tmp_path,packet):
    raw=(json.dumps(packet,sort_keys=True)+'\n').encode();path=tmp_path/'records.gz';path.write_bytes(gzip.compress(raw,mtime=0))
    manifest={'schema':'ssc-refinement-release-v1','checkout_root_relative':'.','packet_file':path.name,'protocol_sha256':'fixture','files':{path.name:{'sha256':digest(path),'bytes':path.stat().st_size,'uncompressed_sha256':hashlib.sha256(raw).hexdigest()}},'counts':{'trials':50}}
    target=tmp_path/'manifest.json';atomic_json(target,manifest);return target


def test_scalar_rebuild_verifies_full_seed_endpoint_and_prewrite_hashes(tmp_path):
    packet=fixture_release(tmp_path);manifest=write_release(tmp_path,packet);out=tmp_path/'reconstructed'
    result=rebuild(manifest,out);assert len(result['trials'])==50
    assert all(row['ACC_delta_pp'] is None for row in result['macros'])
    before=(out/'metrics.csv').read_bytes();(tmp_path/'records.gz').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash/size'):rebuild(manifest,out)
    assert before==(out/'metrics.csv').read_bytes()

@pytest.mark.parametrize('failure',['duplicate','incomplete','summary','native'])
def test_scalar_rebuild_rejects_inconsistent_packets(tmp_path,failure):
    packet=fixture_release(tmp_path);r=packet['records'][0]
    if failure=='duplicate':packet['records'].append(copy.deepcopy(r))
    elif failure=='incomplete':r['evaluation']['trials'].pop()
    elif failure=='summary':r['evaluation']['summary']['acc_mean']=.3
    else:r['evaluation']['native_best']['seed']=2
    manifest=write_release(tmp_path,packet);out=tmp_path/'rejected'
    with pytest.raises(ValueError):rebuild(manifest,out)
    assert not out.exists()
