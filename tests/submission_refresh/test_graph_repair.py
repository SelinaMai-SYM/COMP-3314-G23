"""Graph-repair construction and gate checks; no benchmark-score tuning."""
import inspect
from pathlib import Path
import numpy as np
from scipy import sparse
from experiments.submission_refresh.graph_repair import (row_unit,angular_graph,mass_match,
    stable_neighbors,frozen_pool,oracle_edits,graph_family,random_additions,edit_graph,
    paired_interval,gate_dataset,intended_tasks)


def W(edges,n,weight=1.):
    edges=np.asarray(edges,dtype=int).reshape(-1,2)
    return sparse.csr_matrix((np.ones(2*len(edges))*weight,
         (np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(n,n))


def test_angular_zero_rows_and_mass_status():
    U=row_unit(np.array([[0.,0.],[1.,0.],[0.,2.],[-1.,1.]]))
    graph=angular_graph(U,k=2)
    assert graph[0].nnz==0 and graph[:,0].nnz==0
    matched,info=mass_match(graph,7.)
    np.testing.assert_allclose(sparse.triu(matched,1).sum(),7.)
    assert info['status']=='MASS_MATCHED'
    zero,info=mass_match(graph*0,7.)
    assert info['status']=='DEGENERATE_AFFINITY' and zero.sum()==0


def test_stable_neighbors_and_pool_excludes_existing_without_labels():
    F=np.array([[0.,0.],[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    assert stable_neighbors(F,2)[0].tolist()==[1,2]
    graph=W([(0,1),(1,2)],5)
    pool=frozen_pool(F,F,row_unit(F),graph,k=2)
    edges=set(map(tuple,pool['edges'].tolist()))
    assert (0,1) not in edges and (1,2) not in edges
    assert all(i<j for i,j in edges)
    assert 'y' not in inspect.signature(frozen_pool).parameters
    assert 'y' not in inspect.signature(random_additions).parameters
    order=np.lexsort((pool['edges'][:,1],pool['edges'][:,0],pool['angular_distance']))
    np.testing.assert_array_equal(order,np.arange(len(order)))


def test_oracle_budget_degree_caps_and_reused_addition_set():
    y=np.repeat([0,1],8)
    # Two within-class components per class, linked by an erroneous bridge.
    edges=[(0,1),(1,2),(2,3),(4,5),(5,6),(6,7),
           (8,9),(9,10),(10,11),(12,13),(13,14),(14,15),(3,8),(7,12)]
    graph=W(edges,16)
    candidates=np.array([(3,4),(11,12),(0,5),(8,13),(1,10),(2,9)],dtype=int)
    pool={'edges':candidates,'angular_distance':np.arange(len(candidates),dtype=float)}
    family,edits=graph_family(graph,y,pool,.15)
    assert edits['requested_addition_cap']==2 and edits['actual_additions']==2
    assert edits['deleted_count']==2
    assert edits['new_degree'].max()<=2
    np.testing.assert_array_equal(family['add']['additions'],family['both']['additions'])
    np.testing.assert_array_equal(family['delete']['retained_mask'],family['both']['retained_mask'])
    for seed in [400,401,402]:
        np.testing.assert_array_equal(family[f'blind_{seed}']['retained_mask'],edits['retained_mask'])
        assert len(family[f'blind_{seed}']['additions'])==2
        np.testing.assert_array_equal(family[f'same_class_random_{seed}']['retained_mask'],edits['retained_mask'])
        assert np.count_nonzero(~family[f'fully_random_{seed}']['retained_mask'])==2


def test_random_control_infeasible_is_not_silently_smaller():
    edges=np.array([(0,1),(0,2),(0,3)])
    chosen,status=random_additions(edges,3,4,400,attempts=3)
    assert chosen is None and status['status']=='INFEASIBLE_MATCHED_CONTROL'
    chosen,status=random_additions(edges,0,4,400)
    assert chosen.shape==(0,2) and status['status']=='MATCHED'


def record(acc,nmi,fragments,certified=True):
    return {'status':'COMPLETED','trials':[{'seed':seed,'acc':acc,'nmi':nmi} for seed in range(50)],
            'solver':{'certified':certified,'gap':1e-7,'edge_violation':0.,'node_violation':0.,'normalized_L21_movement':.01},
            'graph_diagnostics':{'within_class_excess_fragments':fragments}}


def test_gate_uses_fixed_oracle_deletion_plus_blind_additions():
    records={'delete':record(.5,.6,10),'both':record(.52,.6,7)}
    for seed in [400,401,402]:
        records[f'blind_{seed}']=record(.51,.6,9)
        # Fully random controls are deliberately stronger. They do not replace
        # the user-chosen blind-addition comparator in the promotion gate.
        records[f'fully_random_{seed}']=record(.9,.9,1)
        records[f'same_class_random_{seed}']=record(.51,.6,9)
    gate=gate_dataset(records)
    assert gate['passed'] and gate['decision']=='PASSED'
    assert gate['contrasts']['both_minus_fully_random_mean_acc']['delta_pp']<0
    records['blind_400']['solver']['certified']=False
    assert gate_dataset(records)['passed']
    assert not gate_dataset(records)['blind_control_certification']['blind_400']
    records['delete']['solver']['certified']=False
    assert gate_dataset(records)['decision']=='NOT_EVALUABLE_UNCERTIFIED'
    assert not gate_dataset(records)['passed']
    records.pop('blind_400')
    assert gate_dataset(records)['decision']=='NOT_EVALUABLE_INCOMPLETE'


def test_gate_requires_activity_and_fragment_repair():
    records={'delete':record(.5,.6,10),'both':record(.52,.6,7)}
    records.update({f'blind_{seed}':record(.51,.6,10) for seed in [400,401,402]})
    records['both']['solver']['normalized_L21_movement']=0
    assert not gate_dataset(records)['passed']
    records['both']['solver']['normalized_L21_movement']=.01
    records['both']['graph_diagnostics']['within_class_excess_fragments']=9
    assert not gate_dataset(records)['passed']


def test_paired_bootstrap_and_finite_catalogue():
    result=paired_interval(np.linspace(.6,.7,50),np.linspace(.5,.6,50))
    assert abs(result['delta_pp']-10)<1e-10 and result['ci_lower_pp']>0
    assert result['resamples']==10000 and result['bootstrap_seed']==424242
    tasks=intended_tasks()
    assert len(tasks)==2*(1+4*6+2*13*6)
    assert {r['dataset'] for r in tasks}=={'ORL_att92','YaleB_cropped2414'}
    assert len({r['configuration_id'] for r in tasks})==len(tasks)


def test_SC_graph_arm_alias_reuses_fixed_predictions_and_checkpoint(tmp_path,monkeypatch):
    import experiments.submission_refresh.graph_repair as module
    from experiments.submission_refresh.core import ArtifactStore
    store=ArtifactStore(tmp_path)
    F=np.array([[0.,0.],[.1,0.],[0.,.1],[4.,4.],[4.1,4.],[4.,4.1]])
    y=np.repeat([0,1],3);meta={'K':2,'objects':{'y':store.put(y)}}
    original=module.solve;calls=[]
    def observed(*args,**kwargs):
        calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(module,'solve',observed)
    left=module._solution(F,W([(0,1),(1,2),(2,3),(3,4),(4,5)],6),meta,store,{'implementation_hash':'unit'},gamma=0,fit_cpu_limit=2)
    right=module._solution(F,W([(0,2),(1,3),(2,4)],6),meta,store,{'implementation_hash':'unit'},gamma=0,fit_cpu_limit=2)
    assert len(calls)==1
    assert len(left['trials'])==len(right['trials'])==50
    assert left['objects']['predictions']==right['objects']['predictions']
    assert left['problem']==right['problem']
    store.get(left['objects']['G']);store.get(left['objects']['q'])
