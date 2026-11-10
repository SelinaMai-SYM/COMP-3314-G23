"""The publication generator preserves scientific endpoints and unavailable values."""
from pathlib import Path
import csv,json
import experiments.submission_refresh.reporting as reporting


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def test_endpoint_formatting_never_attaches_mean_SD_to_native():
    native={'endpoint':'native_best_of_50','acc_mean':91.,'acc_sd':999.}
    mean={'endpoint':'mean_sample_sd_50','acc_mean':42.,'acc_sd':1.2}
    assert reporting.metric(native,'acc')=='91.00'
    assert reporting.metric(mean,'acc')==r'42.00 $\pm$ 1.20'
    assert reporting.metric({'acc_mean':None},'acc')=='--'
    assert reporting.paper_lookup({'rows':[{'benchmark':'AR','method':'pca_spectral','metric':'acc','mean':43.2,'sd':2.1}]})[('AR','pca_sc')]['paper_acc']==43.2


def test_generator_uses_same_authoritative_row_and_records_missing_inputs(tmp_path,monkeypatch):
    monkeypatch.setattr(reporting,'figure',lambda *args:False)
    refresh=tmp_path/'results/submission_refresh'
    historical={'benchmark':'ORL','method':'ssc','endpoint':'mean_sample_sd_50','acc_mean':42.,'acc_sd':1.2,
                'nmi_mean':81.,'nmi_sd':2.3,'paper_ACC':76.,'paper_ACC_SD':1.6,'paper_NMI':88.6,'paper_NMI_SD':1.5,
                'D_max':34.,'D_mean':20.8,'solver_status_current_audit':'ITERATE_CONVERGED_UNCERTIFIED'}
    write_csv(refresh/'joint_metric_selection.csv',[historical])
    write_csv(refresh/'endpoint_comparison.csv',[{**historical,'endpoint':'native_best_of_50','acc_mean':91.,'nmi_mean':92.,'acc_sd':999.,'nmi_sd':999.,'selected_seed':3}])
    manifest=reporting.generate(tmp_path,'2026-11-10')
    main=(tmp_path/'report/tables/refresh_main.tex').read_text()
    appendix=(tmp_path/'report/tables/refresh_appendix.tex').read_text()
    assert r'42.00 $\pm$ 1.20' in main and r'81.00 $\pm$ 2.30' in main
    assert '91.00 & 92.00' in appendix and '999.00' not in appendix
    assert 'counts and selected scores are unavailable' in (tmp_path/'report/tables/refresh_coverage.tex').read_text()
    assert not manifest['inputs']['closest']['available']
    assert manifest['no_score_selection_in_generator']
    assert 'inventory is incomplete' in appendix


def test_missing_aggregation_never_turns_into_performance_zero(tmp_path,monkeypatch):
    monkeypatch.setattr(reporting,'figure',lambda *args:False)
    reporting.generate(tmp_path)
    content=(tmp_path/'report/tables/refresh_main.tex').read_text()
    assert '0.00' not in content
    assert 'unavailable' in (tmp_path/'report/tables/refresh_extension.tex').read_text()
