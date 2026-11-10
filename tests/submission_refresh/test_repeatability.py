import csv,json
import pytest
from experiments.submission_refresh.repeatability import build


def source(path,*,overlap=False):
    rows=[]
    for batch in [0,1]:
        start=0 if overlap else batch*50
        rows.append({'config_id':'data|lda_kmeans|reference','batch':batch,'n_trials':50,
                     'ACC':20+batch,'ACC_SD':3,'NMI':80-batch,'NMI_SD':4,
                     'seed_list':json.dumps(list(range(start,start+50))),
                     'selected_seed':start,'selected_ACC':30+batch,'selected_NMI':90-batch})
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)


def test_both_metrics_and_native_batch_endpoint_stay_separate(tmp_path):
    path=tmp_path/'source.csv';source(path);out=tmp_path/'output'
    rows=build(path,out)
    assert rows[0]['ACC_min']==20 and rows[0]['NMI_min']==79
    assert rows[0]['selected_ACC_min']==30 and rows[0]['selected_NMI_min']==89
    assert 'DIAGNOSTIC_ONLY' in rows[0]['native_endpoint_status']
    assert not any('SD' in key for key in rows[0])
    batches=list(csv.DictReader((out/'historical_repeatability_batches.csv').open()))
    assert len(batches)==2 and batches[0]['ACC_SD']=='3'


def test_overlapping_batches_fail_before_writing(tmp_path):
    path=tmp_path/'source.csv';source(path,overlap=True);out=tmp_path/'output'
    with pytest.raises(ValueError,match='overlap'):build(path,out)
    assert not out.exists()


def test_missing_native_assignment_does_not_discard_valid_mean_batches(tmp_path):
    path=tmp_path/'source.csv';source(path)
    rows=list(csv.DictReader(path.open()))
    for row in rows:
        for key in ['selected_seed','selected_ACC','selected_NMI']:row[key]=''
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    rows=build(path,tmp_path/'output')
    assert rows[0]['ACC_min']==20 and rows[0]['NMI_min']==79
    assert rows[0]['selected_ACC_min'] is None and rows[0]['native_batches_available']==0
    assert rows[0]['native_endpoint_status']=='UNAVAILABLE_NATIVE_ENDPOINT'
