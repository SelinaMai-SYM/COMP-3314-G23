"""Generate secondary-result summaries from retained scalar records."""
from pathlib import Path
import json,csv
import numpy as np
from scripts.final.analyze_next_round import load,csvwrite
from experiments.next_round.evaluate import paired
R=Path(__file__).resolve().parents[2];O=R/'results/next_round';T=R/'report/tables';D=['ORL_att92','JAFFE','YaleB_cropped2414','USPS']
def esc(s):return str(s).replace('_',r'\_')
def main():
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
        sc=json.loads((O/'sc'/(t['dataset']+'__'+t['prep']+'.json')).read_text());ca=paired(j['trials'],sc['trials']);cn=paired(j['trials'],sc['trials'],'nmi');h.append({**t,'run_id':j['run_id'],'ACC':j['scores']['acc_mean'],'NMI':j['scores']['nmi_mean'],'same_feature_SC_ACC':sc['scores']['acc_mean'],'same_feature_SC_NMI':sc['scores']['nmi_mean'],'qualified':j['qualified_for_method_contrast'],'solver_status':j['solver']['status'],'ACC_delta_vs_same_feature_SC':ca['delta_pp'],'NMI_delta_vs_same_feature_SC':cn['delta_pp'],'conditional_ACC_CI':[ca['ci_lower_pp'],ca['ci_upper_pp']]})
    if h:
        csvwrite(O/'heat_primary_summary.csv',h);lines += [r'The geometry pilot shows higher projected-heat kNN stability on fixed graph perturbations; it does not establish clustering improvement. Primary t=4, r=128 uses the same A, full-spectrum exponential action, fixed projection seed, hard-128 and W-only controls. Gamma=1 is common; own $2\gamma_0$ is separately calibrated without labels. These secondary features change the input F and cannot satisfy the same-original-F main extension goal.',r'\begin{center}\scriptsize\begin{tabular}{llrrrrl}\toprule Dataset & Feature/control & gamma & SC ACC & SSC ACC & SSC NMI & status \\\midrule']
        for x in sorted(h,key=lambda x:(x['dataset'],x['prep'],x['gamma'])):
            lines.append(f"{esc(x['dataset'].replace('_cropped2414','').replace('_att92',''))} & {esc(x['prep'].replace('N2_',''))} & {x['gamma']:.3g} & {x['same_feature_SC_ACC']:.2f} & {x['ACC']:.2f} & {x['NMI']:.2f} & {'cert.' if x['qualified'] else 'uncert.'} \\")
        lines += [r'\bottomrule\end{tabular}\end{center}',r'The exact kernel bound applies before random projection. Fixed-subset exact-kernel distance errors and restricted-candidate kNN recall are recorded separately; these are not full-graph guarantees. No t/r/seed oracle tuning or projection sensitivity is claimed from the primary test.']
    robust=[]
    for p in sorted((O/'full_pipeline_robustness').glob('*.json')):
        r=json.loads(p.read_text());base=next(j for j in jobs if j.get('status')=='COMPLETED' and j['task']['phase']=='A' and j['task']['dataset']==r['dataset'] and j['task']['gamma']==1)
        sc=json.loads((O/'sc'/(r['dataset']+'__Y0.json')).read_text())
        for e in r['endpoints']:
            clean=sc['scores'] if e['method']=='SC' else base['scores'];robust.append({'dataset':r['dataset'],'condition':r['condition_index'],'method':e['method'],'ACC':e['ACC'],'NMI':e['NMI'],'ACC_change_pp':e['ACC']-clean['acc_mean'],'NMI_change_pp':e['NMI']-clean['nmi_mean'],'solver_status':r['solver']['status'] if e['method']=='SSC' else 'NOT_APPLICABLE'})
    if robust:
        csvwrite(O/'corrected_robustness_summary.csv',robust);lines += [r'\subsection{Corrected full-pipeline image conditions}',r'Each of four fixed image conditions reconstructs A, F, W and SSC with clean gamma=1; USPS uses [-1,1] and brightness steps scale with full domain width. Both ACC and NMI changes are measured against each method on clean data. These deterministic conditions are descriptive, not independent random perturbation seeds. No inferential CI or adaptive parameter-selection claim is made. USPS uncertified outputs remain uncertified.',r'\begin{center}\small\begin{tabular}{llrrrr}\toprule Dataset & Method & min $\Delta$ACC & max $\Delta$ACC & min $\Delta$NMI & max $\Delta$NMI \\\midrule']
        for d in D:
            for m in ['SC','SSC']:
                rr=[x for x in robust if x['dataset']==d and x['method']==m]
                if rr:lines.append(f"{esc(d.replace('_cropped2414','').replace('_att92',''))} & {m} & {min(x['ACC_change_pp'] for x in rr):.2f} & {max(x['ACC_change_pp'] for x in rr):.2f} & {min(x['NMI_change_pp'] for x in rr):.2f} & {max(x['NMI_change_pp'] for x in rr):.2f} \\")
        lines += [r'\bottomrule\end{tabular}\end{center}']
    lines=[line+chr(92) if line.endswith(chr(92)) and not line.endswith(chr(92)*2) else line for line in lines]
    (T/'secondary_findings.tex').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
