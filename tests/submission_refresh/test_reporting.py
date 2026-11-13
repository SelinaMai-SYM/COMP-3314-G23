"""The publication generator preserves scientific endpoints and unavailable values."""
from pathlib import Path
import csv,json
import pytest
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


def test_generator_hashes_certified_availability_and_scopes_same_input_reference(tmp_path,monkeypatch):
    from experiments.subset_search.certified_status import certified_search_status
    monkeypatch.setattr(reporting,'figure',lambda *args:False)
    subset=tmp_path/'results/subset_search';refresh=tmp_path/'results/submission_refresh';refresh.mkdir(parents=True)
    rows=certified_search_status([],{'USPS':{'specification_compatible'}})
    write_csv(subset/'certified_search_status.csv',rows)
    identity={'status':'MATCHING_RECORDED_CURRENT_F_W_OBJECTS','same_current_F_W_content_addresses':True}
    (refresh/'usps_numerical_reference_input_identity.json').write_text(json.dumps(identity))
    manifest=reporting.generate(tmp_path)
    assert manifest['inputs']['certified_search_status']['available']
    assert manifest['inputs']['usps_numerical_reference_input_identity']['available']
    assert all(manifest['inputs'][key]['sha256'] for key in ['certified_search_status','usps_numerical_reference_input_identity'])
    appendix=(tmp_path/'report/tables/refresh_appendix.tex').read_text()
    assert 'Separate certified-search availability' in appendix and 'no certified closest winner is selected' in appendix
    assert 'exactly matching current F/W content addresses' in appendix
    assert 'does not certify the locked IRLS G' in appendix


def graph_fixture():
    record='graph_jobs/g1/fixed/casebook.json'
    casebook={'record':record,'dataset':'ORL_att92','status':'COMPLETED','samples':400,'seed_count':50,
        'sc_summary':{'n':50,'acc_mean':60.,'acc_sd':1.,'nmi_mean':70.,'nmi_sd':2.},
        'ssc_summary':{'n':50,'acc_mean':61.,'acc_sd':.5,'nmi_mean':71.,'nmi_sd':.6},
        'ssc_solver_status':'PRIMAL_DUAL_GAP_CERTIFIED',
        'sc_pair_errors':[{'false_merge_rate':.1,'false_split_rate':.2} for _ in range(50)],
        'ssc_pair_errors':[{'false_merge_rate':.08,'false_split_rate':.25} for _ in range(50)],
        'strata':[{'variable':'row_norm','quintile':0,'samples':80,'mean_wrong_edge_count':2.,'mean_wrong_edge_mass':.123,
            'sc_correct_ssc_wrong_fraction':.25,'sc_wrong_ssc_correct_fraction':.5}],
        'illustrations_seed':0,'illustration_sample_ids':{'sc_correct_ssc_wrong':0,'sc_wrong_ssc_correct':3,'both_correct':None,'both_wrong':1},
        'upstream_A_diagnostics':{'edges':100,'cross_class_edge_fraction':.7,'cross_class_mass_fraction':.8,'within_class_excess_fragments':2},
        'shrinkage_W0_diagnostics':{'edges':80,'cross_class_edge_fraction':.1,'cross_class_mass_fraction':.2,'within_class_excess_fragments':3}}
    g2={'dataset':'ORL_att92','phase':'G2','anchor':'U','graph':'Wa','gamma':10.,'config_id':'g2fixed','status':'COMPLETED',
        'n':50,'acc_mean':42.25,'acc_sd':.3,'nmi_mean':75.5,'nmi_sd':.7,'certified':True,'normalized_L21_movement':.01234}
    both={'dataset':'ORL_att92','phase':'G3','anchor':'F0','arm':'both','gamma':1000.,'addition_fraction':.15,'config_id':'g3both',
        'status':'COMPLETED','n':50,'acc_mean':65.5,'acc_sd':.1,'nmi_mean':66.6,'nmi_sd':.2,'certified':True,'normalized_L21_movement':.002}
    fully={**both,'arm':'fully_random_400','config_id':'g3fully','acc_mean':95.}
    source=Path(__file__).resolve().parents[2]
    tasks=json.loads((source/'configs/submission_refresh/graph_queue.json').read_text())['tasks']
    coverage=[]
    for task in tasks:
        row={**task,'controller_status':'NOT_RUN','saved_output_state':'MISSING_CASEBOOK' if task['phase']=='G1' else 'MISSING_POINT_FILE','point_complete':False}
        if task['phase']=='G2' and task['dataset']=='ORL_att92' and task['anchor']=='U' and task['graph']=='Wa' and task['gamma']==10.:
            row.update(controller_status='TIMEOUT',saved_output_state='POINT_COMPLETE',point_complete=True)
        if task['phase']=='G3' and task['dataset']=='ORL_att92' and task['gamma']==1000. and task['addition_fraction']==.15 and task['arm'] in ['both','fully_random_400']:
            row.update(controller_status='COMPLETED',saved_output_state='POINT_COMPLETE',point_complete=True)
        coverage.append(row)
    conditions={name:True for name in ['certified_involved_solutions','active_delete_and_both','ACC_gain_at_least_1pp','NMI_not_decreased',
        'excess_fragments_reduced_at_least_20pct','ACC_CI_positive_vs_delete','ACC_CI_positive_vs_mean_blind']}
    gate={'decision':'PASSED','datasets':{'ORL_att92':{'decision':'PASSED','conditions':conditions,'excess_fragment_reduction_fraction':.3,
        'contrasts':{'both_minus_delete_acc':{'delta_pp':1.2,'ci_lower_pp':.2,'ci_upper_pp':2.2},
            'both_minus_blind_mean_acc':{'delta_pp':.9,'ci_lower_pp':.1,'ci_upper_pp':1.7},
            'both_minus_fully_random_mean_acc':{'delta_pp':-29.5,'ci_lower_pp':-30.,'ci_upper_pp':-29.}}}}}
    diagnostics=[{'dataset':'ORL_att92','config_id':'g3both','within_class_excess_fragments':7}]
    return [g2,both,fully],diagnostics,[casebook],coverage,{'intended_tasks':362},gate


def test_graph_appendix_renders_fixed_evidence_all_G2_cells_and_separate_controls():
    content='\n'.join(reporting.graph_appendix(*graph_fixture()))
    assert '362 committed rows' in content and 'TIMEOUT' in content and reporting.break_text('NOT_RUN') in content
    assert r'42.25 $\pm$ 0.30' in content and '0.0123' in content
    g2_lines=[line for line in content.splitlines() if line.startswith(('ORL & F0 &','ORL & U &','YaleB cropped & F0 &','YaleB cropped & U &'))]
    assert len(g2_lines)==48
    assert 'False merge & 10.00 & 8.00 & -2.00 & 50' in content
    assert 'False split & 20.00 & 25.00 & 5.00 & 50' in content
    assert 'A: input-feature geometry & 100 & 70.00 & 80.00' in content
    assert 'W0: spectral geometry & 80 & 10.00 & 20.00' in content
    assert 'Original row ID' in content and reporting.break_text('sc_correct_ssc_wrong')+' & 0 & 0' in content
    assert 'Fixed delete + blind add 400' in content
    assert 'Fixed delete + same-class random 400' in content and 'Fully random delete/add 400' in content
    assert 'Both minus delete & ACC & 1.20 & 0.20 & 2.20' in content
    assert 'Both minus fully random edits mean & ACC & -29.50' in content
    assert 'not an additional hidden pass condition' in content


def test_generator_hashes_every_graph_scalar_input_and_embeds_graph_evidence(tmp_path,monkeypatch):
    monkeypatch.setattr(reporting,'figure',lambda *args:False)
    results,diagnostics,casebooks,coverage,coverage_manifest,gate=graph_fixture();refresh=tmp_path/'results/submission_refresh'
    def serialized(rows):
        return [{key:json.dumps(value) if isinstance(value,(dict,list)) else value for key,value in row.items()} for row in rows]
    for name,rows in [('extension_results.csv',results),('graph_diagnostics.csv',diagnostics),('casebook_summary.csv',casebooks),('graph_execution_coverage.csv',coverage)]:
        write_csv(refresh/name,serialized(rows))
    (refresh/'graph_coverage_manifest.json').write_text(json.dumps(coverage_manifest));(refresh/'extension_gate.json').write_text(json.dumps(gate))
    protocol=tmp_path/'configs/submission_refresh/extension_protocol.yaml';protocol.parent.mkdir(parents=True);protocol.write_text('version: fixed\n')
    manifest=reporting.generate(tmp_path)
    for key in ['extension','graph_diagnostics','casebooks','graph_execution','graph_coverage_manifest','graph_protocol','gate']:
        assert manifest['inputs'][key]['available'] and manifest['inputs'][key]['sha256']
    text=(tmp_path/'report/tables/refresh_appendix.tex').read_text()
    assert 'New fixed-representation graph evidence' in text and r'42.25 $\pm$ 0.30' in text
    assert 'tab:graph-g3-contrasts' in text


def test_graph_appendix_does_not_substitute_W_for_missing_A_or_partial_paired_errors():
    fixture=graph_fixture();casebook=fixture[2][0]
    casebook.pop('upstream_A_diagnostics');casebook['sc_pair_errors'].pop()
    content='\n'.join(reporting.graph_appendix(*fixture))
    assert 'A: input-feature geometry & -- & -- & -- & --' in content
    assert 'W0: spectral geometry & 80 & 10.00 & 20.00' in content
    assert 'False merge & -- & -- & -- & --' in content
    assert 'False split & -- & -- & -- & --' in content


def test_casebook_summary_preserves_the_same_matched_G1_task_scalars():
    from experiments.submission_refresh.aggregate import _casebook_summary
    casebook=graph_fixture()[2][0]
    task={'task':{'dataset':'ORL_att92'},'upstream_A_diagnostics':casebook['upstream_A_diagnostics'],
        'shrinkage_W0_diagnostics':casebook['shrinkage_W0_diagnostics'],
        'sc_solution':{'summary':casebook['sc_summary'],'solver':{'status':'ANALYTIC_G_EQUALS_F','certified':True}},
        'ssc_solution':{'summary':casebook['ssc_summary'],'solver':{'status':'PRIMAL_DUAL_GAP_CERTIFIED','certified':True}}}
    output=_casebook_summary(casebook['record'],{key:value for key,value in casebook.items() if key not in ['upstream_A_diagnostics','shrinkage_W0_diagnostics','sc_summary','ssc_summary']},task)
    assert output['dataset']=='ORL_att92' and output['sc_summary']==casebook['sc_summary']
    assert output['ssc_summary']==casebook['ssc_summary']
    assert output['upstream_A_diagnostics']==casebook['upstream_A_diagnostics']
    assert output['shrinkage_W0_diagnostics']==casebook['shrinkage_W0_diagnostics']
    assert output['sc_solver_status']=='ANALYTIC_G_EQUALS_F' and output['ssc_certified'] is True
