"""Joint selection from validated frozen scalar trials; no raw data required."""
from __future__ import annotations
import csv,json,tempfile
from pathlib import Path
from experiments.v3_reproduction.release import rebuild,_write_csv,BENCHMARKS,METHODS
from .core import ROOT,atomic_json,digest
from .selection import distances,rank

def rebuild_joint(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='refresh-history-') as tmp:
        rebuild(ROOT/'configs/final/release_manifest.json',Path(tmp)/'validated')
        rows=list(csv.DictReader(open(Path(tmp)/'validated/configuration_table.csv')))
        legacy=list(csv.DictReader(open(Path(tmp)/'validated/closest_to_paper.csv')))
        endpoints=[];candidates=[]
        for source in rows:
            r=dict(source)
            for k in ['measured_ACC','measured_ACC_SD','measured_NMI','measured_NMI_SD','paper_ACC','paper_NMI','paper_ACC_SD','paper_NMI_SD']:r[k]=float(r[k]) if r.get(k) else None
            if r['paper_ACC'] is None or r['paper_NMI'] is None:continue
            dev=json.loads(r['setting_deviations'])
            # Differences from a controlled reference are not all violations of
            # an explicit paper requirement (notably the published gamma grid).
            r['paper_deviations']=sum(v in ['input_l2_normalization','embedding_row_normalization','n_init_not_one'] for v in dev)
            r['preparation_assumptions']=sum(v in ['alternate_dataset_version','iteration_budget_not_300'] for v in dev)
            r.update(acc_mean=r['measured_ACC'],nmi_mean=r['measured_NMI'],acc_sd=r['measured_ACC_SD'],nmi_sd=r['measured_NMI_SD'],endpoint='mean_sample_sd_50',pool='historical_scalar',solver_track='historical_style')
            r=distances(r,{'acc':r['paper_ACC'],'nmi':r['paper_NMI']});r['delta_acc_sd_pp']=r['acc_sd']-r['paper_ACC_SD'];r['delta_nmi_sd_pp']=r['nmi_sd']-r['paper_NMI_SD'];candidates.append(r)
            selected=json.loads(r.get('batch0_selected_statistic','{}'))
            if r['method']=='lda_kmeans':
                endpoints.append({'benchmark':r['benchmark'],'method':r['method'],'config_id':r['config_id'],'endpoint':'native_best_of_50','status':'UNAVAILABLE_CROSS_SUBSPACE_INERTIA_NOT_COMPARABLE'})
            elif 'selected_ACC' in selected:
                e={**r,'endpoint':'native_best_of_50','acc_mean':selected['selected_ACC'],'nmi_mean':selected['selected_NMI'],'acc_sd':None,'nmi_sd':None,'measured_ACC':selected['selected_ACC'],'measured_NMI':selected['selected_NMI'],'measured_ACC_SD':None,'measured_NMI_SD':None,'delta_acc_sd_pp':None,'delta_nmi_sd_pp':None,'selected_seed':selected['selected_seed'],'n_trials':1,'delta_pp':selected['selected_ACC']-r['paper_ACC'],'selection_distance':abs(selected['selected_ACC']-r['paper_ACC'])}
                endpoints.append(distances(e,{'acc':r['paper_ACC'],'nmi':r['paper_NMI']}))
        chosen=[]
        for b in BENCHMARKS:
            for m in METHODS:
                for endpoint,allrows in [('mean_sample_sd_50',candidates),('native_best_of_50',endpoints)]:
                    pool=[r for r in allrows if r['benchmark']==b and r['method']==m and 'D_max'in r and r['subset_status']=='historical_reconstruction']
                    if pool:
                        best=rank(pool)[0];old=next((v for v in legacy if v['benchmark']==b and v['method']==m),{})
                        chosen.append({**best,'eligible_configurations':len(pool),'legacy_acc_only_config_id':old.get('config_id'),'selection_changed':best['config_id']!=old.get('config_id'),'selection_rule':'joint-minimax-v1-frozen-20261110','qualification':'Retrospective numerical match; historical arrays unavailable; no label-free selection claim'})
                    else:chosen.append({'benchmark':b,'method':m,'endpoint':endpoint,'status':'UNAVAILABLE','reason':'No eligible complete measured configuration; historical restrictions remain'})
        _write_csv(out/'joint_metric_selection.csv',[r for r in chosen if r['endpoint']=='mean_sample_sd_50'])
        _write_csv(out/'endpoint_comparison.csv',chosen)
        _write_csv(out/'all_joint_configurations.csv',candidates)
        _write_csv(out/'all_native_endpoints.csv',endpoints)
        from .repeatability import build as build_repeatability
        build_repeatability(Path(tmp)/'validated/batch_repeatability.csv',out)
        atomic_json(out/'historical_joint_manifest.json',{'version':1,'source_manifest_sha256':digest(ROOT/'configs/final/release_manifest.json'),'selection_sha256':digest(ROOT/'configs/submission_refresh/selection.yaml'),'complete_configuration_count':len(candidates),'selected':chosen,'validation':'immutable release checked from compressed and decompressed hashes; all seeds verified before selection'})
        return chosen
