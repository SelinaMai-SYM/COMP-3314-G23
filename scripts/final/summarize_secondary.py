"""Generate secondary-result summaries from retained scalar records."""
from pathlib import Path
import json,csv
import numpy as np
from scripts.final.analyze_next_round import load,csvwrite
from experiments.next_round.evaluate import paired
R=Path(__file__).resolve().parents[2];O=R/'results/next_round';T=R/'report/tables';D=['ORL_att92','JAFFE','YaleB_cropped2414','USPS']
def esc(s):return str(s).replace('_',r'\_')
def main():
    import pandas as pd
    historical=pd.read_csv(R/'results/v3_reproduction/all_configurations.csv');reference=historical[(historical.dataset_id=='USPS')&(historical.method=='ssc')&(historical.prep=='Y0')&(historical.variant=='E8')&(historical.config_name=='E8|gamma=1e+03')&(historical.initialization=='SKLEARN_GREEDY_KMEANSPP')].iloc[0]
    (T/'secondary_main.tex').write_text(f"The historical USPS gamma=1000 greedy++ point has ACC {100*reference.per_run_acc_mean:.3f}\\% and NMI {100*reference.per_run_nmi_mean:.3f}\\%. Fresh uncertified poor outputs on separately regenerated F/W do not invalidate it. Synthetic bridge tests show damage avoidance shared by static deletion and squared fidelity, with SC already perfect. Geometry stability and Huber MSE changes alone do not establish label gains.\n")
    reps=json.loads((O/'representations.json').read_text());g=next(x for x in reps if x['dataset']=='YaleB_cropped2414' and x['prep']=='Y0')['graph_W']
    (T/'graph_evidence_main.tex').write_text(f"YaleB cropped W has {100*g['cross_class_edge_fraction']:.1f}\\% cross-class edges/{100*g['cross_class_mass_fraction']:.1f}\\% mass. Length AUROC {g['cross_edge_length_AUROC']:.3f} means wrong edges tend to be shorter, challenging long-edge truncation. These are W/F-space diagnostics.\n")
    graphlines=[r'\subsection{Separate A and W audit}',r'Label-assisted fractions and AUROC on the newly generated Y0 representations. W length is measured in F, with cross-class edges positive; values below .5 mean longer edges do not identify errors. A native-input length AUROC is not asserted.',r'\begin{center}\small\begin{tabular}{llrrr}\toprule Dataset & Graph & cross edges (\%) & cross mass (\%) & length AUROC \\\midrule']
    for x in reps:
        if x['prep']!='Y0':continue
        for name in ['A','W']:
            a=x['graph_'+name];graphlines.append(f"{esc(x['dataset'])} & {name} & {100*a['cross_class_edge_fraction']:.2f} & {100*a['cross_class_mass_fraction']:.2f} & {format(a['cross_edge_length_AUROC'],'.3f') if name=='W' else '--'} "+chr(92)*2)
    graphlines += [r'\bottomrule\end{tabular}\end{center}'];(T/'graph_evidence.tex').write_text('\n'.join(graphlines)+'\n')
    jobs=load();lines=[r'\subsection{Synthetic mechanism checks}',r'Synthetic seeds 100--109 are independent instances; each has 50 conditional K-means seeds. Parameters and distance scales are frozen from the unpolluted instance. The full 2-by-2 and static-screening controls are retained, including uncertified inner solves. This intentionally easy geometry can show damage avoidance but is weak evidence of added clustering capacity.',r'\begin{center}\small\begin{tabular}{llrrr}\toprule Scenario & Method & ACC & NMI & qualified / 10 \\\midrule']
    syn=json.loads((O/'synthetic/summary.json').read_text())
    for x in syn:
        if x['scenario'] in ['bridge_0.1','imbalanced_bridge','anchor_0.2'] and x['method'] in ['SC','SSC','radial_capped','squared_linear','static_screen']:
            lines.append(f"{esc(x['scenario'])} & {esc(x['method'])} & {x['ACC']:.3f} & {x['NMI']:.3f} & {x['qualified_seeds']} \\")
    lines += [r'\bottomrule\end{tabular}\end{center}',r'Bridge contamination slightly lowers SSC ACC/NMI; capping, static deletion and squared fidelity all avoid this damage, while SC is already perfect. Capping is therefore neither necessary nor shown to improve beyond SC. At 20\% anchor contamination all methods have 100\% ACC/NMI, yet capping can worsen representation MSE by removing useful correction. The radial-Huber primary pilot changes MSE slightly without label improvement; its full real-data search is not promoted.',r'\subsection{Tiny global reference and initialization dependence}',r'For the documented five-point graph, 1024 active states are enumerated, 960 excluded by a nonnegative constant lower bound, and 64 convex states independently certified. Original primal/dual are approximately 8; capped global primal/dual are 3. The local capped algorithm returns objective 3 (ACC/NMI 100\%) from F, but objective 8 (ACC 60\%, NMI 0) from original SSC. Global certification comes solely from enumeration on this tiny graph.',r'\subsection{Secondary heat ablation}']
    h=[]
    for j in jobs:
        t=j['task']
        if t['phase']!='N2_primary' or j.get('status')!='COMPLETED':continue
        sc=json.loads((O/'sc'/(t['dataset']+'__'+t['prep']+'.json')).read_text());ca=paired(j['trials'],sc['trials']);cn=paired(j['trials'],sc['trials'],'nmi');h.append({**t,'run_id':j['run_id'],'ACC':j['scores']['acc_mean'],'NMI':j['scores']['nmi_mean'],'same_feature_SC_ACC':sc['scores']['acc_mean'],'same_feature_SC_NMI':sc['scores']['nmi_mean'],'qualified':j['qualified_for_method_contrast'],'solver_status':j['solver']['status'],'cpu_seconds':j.get('cpu_seconds'),'iterations':j['solver'].get('iterations'),'gap':j['solver'].get('gap'),'ACC_delta_vs_same_feature_SC':ca['delta_pp'],'NMI_delta_vs_same_feature_SC':cn['delta_pp'],'conditional_ACC_CI':[ca['ci_lower_pp'],ca['ci_upper_pp']]})
    if h:
        csvwrite(O/'heat_primary_summary.csv',h)
        reused=[]
        for j in jobs:
            t=j['task']
            if j.get('status')=='COMPLETED' and t['phase']=='A' and t['dataset'] in D and t['gamma']==1:
                sc=json.loads((O/'sc'/(t['dataset']+'__Y0.json')).read_text());reused.append({**t,'run_id':j['run_id'],'ACC':j['scores']['acc_mean'],'NMI':j['scores']['nmi_mean'],'same_feature_SC_ACC':sc['scores']['acc_mean'],'same_feature_SC_NMI':sc['scores']['nmi_mean'],'qualified':j['qualified_for_method_contrast'],'reused_control':True})
        (O/'heat_primary_reused_controls.json').write_text(json.dumps(reused,indent=2)+'\n')
        lines += [r'The 80-row geometry pilot shows higher projected-heat kNN stability, not label improvement. Primary t=4, r=128 uses the same A, full-spectrum action, fixed projection seed, hard-dimension and W-only controls. Below, each cell is ACC/NMI (percent); common gamma=1 and own $2\gamma_0$ are locked without labels. C/U denote certified/uncertified in that order. Four original gamma=1 controls are reused from Table 2; 28 new fits and their actual gamma/costs are in the scalar release. N2 changes F and cannot substitute for the same-original-F main goal.',r'\begin{center}\scriptsize\begin{tabular}{llrrrl}\toprule Data & Feature & SC ACC/NMI & gamma=1 ACC/NMI & own $2\gamma_0$ ACC/NMI & status \\\midrule']
        for d in D:
            for prep,label in [('Y0','original'),('N2_hard128','hard128'),('N2_heat_t4_r128','heat128'),('N2_W_only_heat','W-only')]:
                rr=[x for x in h+reused if x['dataset']==d and x['prep']==prep];one=next(x for x in rr if x['gamma']==1);own=next(x for x in rr if x['gamma']!=1)
                lines.append(f"{esc(d.replace('_cropped2414','').replace('_att92',''))} & {label} & {one['same_feature_SC_ACC']:.2f}/{one['same_feature_SC_NMI']:.2f} & {one['ACC']:.2f}/{one['NMI']:.2f} & {own['ACC']:.2f}/{own['NMI']:.2f} & {'C' if one['qualified'] else 'U'}/{'C' if own['qualified'] else 'U'} "+chr(92)*2)
        lines += [r'\bottomrule\end{tabular}\end{center}',r'The exact kernel bound applies before projection. Fixed-subset exact-kernel errors and restricted-candidate kNN recall are separate diagnostics, not full-graph guarantees. No t/r/seed tuning or projection sensitivity is claimed.']
    robust=[]
    for p in sorted((O/'full_pipeline_robustness').glob('*.json')):
        r=json.loads(p.read_text());base=next(j for j in jobs if j.get('status')=='COMPLETED' and j['task']['phase']=='A' and j['task']['dataset']==r['dataset'] and j['task']['gamma']==1)
        sc=json.loads((O/'sc'/(r['dataset']+'__Y0.json')).read_text())
        for e in r['endpoints']:
            clean=sc['scores'] if e['method']=='SC' else base['scores'];robust.append({'dataset':r['dataset'],'condition':r['condition_index'],'method':e['method'],'ACC':e['ACC'],'NMI':e['NMI'],'ACC_change_pp':e['ACC']-clean['acc_mean'],'NMI_change_pp':e['NMI']-clean['nmi_mean'],'solver_status':r['solver']['status'] if e['method']=='SSC' else 'NOT_APPLICABLE'})
    if robust:
        csvwrite(O/'corrected_robustness_summary.csv',robust);lines += [r'\subsection{Corrected full-pipeline image conditions}',r'Four fixed image conditions reconstruct A/F/W/SSC at clean gamma=1; USPS uses [-1,1] with full-span brightness steps. Ranges below are descriptive changes in percentage points against each clean method. Conditions are not independent random replicates; no inferential or adaptive-selection claim is made. USPS SSC remains uncertified.',r'\begin{center}\small\begin{tabular}{lrrrr}\toprule Data & SC $\Delta$ACC & SSC $\Delta$ACC & SC $\Delta$NMI & SSC $\Delta$NMI \\\midrule']
        for d in D:
            cells=[]
            for metric in ['ACC_change_pp','NMI_change_pp']:
                for method in ['SC','SSC']:
                    rr=[x for x in robust if x['dataset']==d and x['method']==method];lo=round(min(x[metric] for x in rr),2);hi=round(max(x[metric] for x in rr),2);cells.append(f"[{lo if lo else 0.:.2f},{hi if hi else 0.:.2f}]")
            lines.append(esc(d.replace('_cropped2414','').replace('_att92',''))+' & '+' & '.join(cells)+' '+chr(92)*2)
        lines += [r'\bottomrule\end{tabular}\end{center}']
    lines=[line+chr(92) if line.endswith(chr(92)) and not line.endswith(chr(92)*2) else line for line in lines]
    (T/'secondary_findings.tex').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
