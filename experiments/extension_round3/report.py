"""Authoritative scalar export, paired contrasts and reproducible scientific tables."""
from __future__ import annotations
import csv,gzip,io,tempfile
import numpy as np
from .common import *

CANDIDATES=['R3_E7_CAVITY','R3_E1_V3_CAVITY','R3_E5_V2_CAVITY']


def write_csv(path,rows,fields=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fields=fields or sorted({k for row in rows for k in row})
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def stats(values):return float(np.mean(values)),float(np.std(values,ddof=1))
def fmt(v):return 'NA' if v is None else f'{v:.3f}' if isinstance(v,(float,np.floating)) else str(v)
def table(rows,columns):
    return '| '+' | '.join(columns)+' |\n|'+'|'.join('---' for _ in columns)+'|\n'+''.join('| '+' | '.join(fmt(r.get(k)) for k in columns)+' |\n' for r in rows)


def export_records(config,root):
    spec,lock,store=locked(root,config)
    if read(store.root/'terminal_evaluation.json')['stage']!='TERMINAL_SCORING_COMPLETE':raise ValueError('terminal evaluation incomplete')
    frozen=read(store.root/'numerical_freeze.json');profiles=[]
    for q in queue():
        r=read(profile_path(store,q['id']));e=read(store.root/'evaluations'/(q['id']+'.json'));a=frozen['qualification'][q['id']]
        # Scalar release contains no matrices, labels or machine paths. Numeric
        # object identities point to the independently recoverable external store.
        p={**q,'status':a['status'] if a['status']=='QUALIFICATION_AUDIT_FAILURE' else r['status'],'qualified':a['qualified'],'certified':a['certified'],'certificate':a.get('certificate',r.get('certificate',{})),'lambda':r.get('lambda',r.get('lambda_value')),'source_fingerprint':r.get('source_fingerprint'),'finite':bool(r.get('result')),'result_identity':identity(r['result']) if r.get('result') else None,'G_object':r.get('result',{}).get('G'),'path_CPU_seconds':r.get('path_CPU_seconds'),'distinct_lambdas':r.get('distinct_lambdas'),'evaluation':{k:v for k,v in e.items() if k not in ['panels']}}
        p['panels']={panel:{k:v for k,v in value.items() if k!='scientific_objects'} for panel,value in e.get('panels',{}).items()};profiles.append(p)
    from sklearn.metrics import adjusted_rand_score
    planned_lookup={(q['benchmark'],q['method'],q['rho'],q['tau_multiplier']):q for q in queue()}
    for p in profiles:
        if p['method'] not in CANDIDATES or not p['evaluation'].get('mechanism'):continue
        raw=read(store.root/'evaluations'/(p['id']+'.json'))
        controls=['QSSC',p['method'].removesuffix('_CAVITY')+'_PILOT']
        if p['method']!='R3_E7_CAVITY':controls+=['TUBE_UNIFORM' if p['method']=='R3_E1_V3_CAVITY' else 'GUARD_UNIFORM']
        for control in controls:
            tau=p['tau_multiplier'] if control.endswith('_PILOT') else 1.
            q=planned_lookup.get((p['benchmark'],control,p['rho'],tau))
            if not q:continue
            cp=store.root/'evaluations'/(q['id']+'.json')
            if not cp.exists():continue
            other=read(cp)
            for panel,data in raw.get('panels',{}).items():
                od=other.get('panels',{}).get(panel)
                if not data['complete'] or not od or not od['complete']:continue
                agreements=[]
                for a,b in zip(data['scientific_objects'],od['scientific_objects']):
                    agreements.append(adjusted_rand_score(store.get(a['labels']),store.get(b['labels'])))
                p['evaluation']['mechanism'][panel+'_changed_partition_fraction_vs_'+control]=float(np.mean(np.asarray(agreements)<1-1e-12))
                p['evaluation']['mechanism'][panel+'_partition_ARI_vs_'+control]=float(np.mean(agreements))
    ledger=ResourceLedger(root).state();jobs=[]
    for e in ledger['entries']:
        job=store.root/'command_jobs'/e['run_id']/'status.json';status=read(job) if job.exists() else {}
        jobs.append({**e,'peak_RSS_bytes':status.get('peak_RSS_bytes',status.get('peak_rss_bytes',status.get('max_sampled_RSS_bytes')))})
    return dict(schema='ssc-round3-scalar-release-v1',protocol_sha256=digest(config),effective_protocol_sha256=identity(spec),input_lock_sha256=digest(ROOT/'configs/extension_round3/cohort_lock.json'),numerical_freeze_sha256=digest(store.root/'numerical_freeze.json'),source_fingerprint=lock['source_fingerprint'],analysis_source_files_at_freeze=frozen.get('analysis_source_files',{}),analysis_source_files_at_export={str((ROOT/'experiments/extension_round3'/n).relative_to(ROOT)):digest(ROOT/'experiments/extension_round3'/n) for n in ['evaluate.py','report.py','release.py']},environment=lock['environment'],cohorts={b:{k:c[k] for k in ['candidate_id','n','K','prep','historical_identity','adaptation_flags','gamma_nominal','gamma_effective','variant']} for b,c in lock['cohorts'].items()},profiles=profiles,resource_usage=jobs,budget={k:v for k,v in ledger.items() if k not in ['entries','active']},clock=read(store.root/'clock.json'),selection_qualification=lock['selection_qualification'])


def contrast_controls(method):
    prefix=method.removesuffix('_CAVITY');controls=['QSSC','SC','SSC_REFERENCE',prefix+'_PILOT']
    if method=='R3_E7_CAVITY':controls+=['UNIFORM_GRAPH_ALIAS',prefix+'_ANCHOR',prefix+'_LEVERAGE']
    else:controls+=['TUBE_UNIFORM' if method=='R3_E1_V3_CAVITY' else 'GUARD_UNIFORM']
    return controls+[prefix+'_SHUFFLE'+str(s) for s in [400,401,402]]


def derive(records):
    metrics=[];coverage=[];mechanisms=[];trials=[];lookup={}
    for p in records['profiles']:
        cert=p['certificate'];coverage.append({**{k:p[k] for k in ['id','benchmark','method','rho','stage','tau_multiplier','status','finite','qualified','certified','lambda','path_CPU_seconds','distinct_lambdas']},'rounding_complete':p['evaluation'].get('complete',False)})
        if p['evaluation'].get('mechanism'):mechanisms.append(p['evaluation']['mechanism'])
        for panel,data in p['panels'].items():
            for t in data['trials']:trials.append(dict(id=p['id'],benchmark=p['benchmark'],method=p['method'],rho=p['rho'],tau_multiplier=p['tau_multiplier'],panel=panel,**t))
            if not data['complete'] or len(data['trials'])!=50:continue
            seeds=[r['seed'] for r in data['trials']]
            if seeds!=list(range(50)):raise ValueError('incomplete or duplicate seed order')
            row={k:p[k] for k in ['id','benchmark','method','rho','stage','tau_multiplier','status','qualified','certified','lambda']};row['panel']=panel;row['n']=50
            for name in ['acc','nmi']:row[name+'_mean'],row[name+'_sd']=stats([r[name] for r in data['trials']])
            for name in ['movement','movement_error','relative_gap','capacity_residual']:row[name]=cert.get(name)
            if row['movement'] is None:row['movement']=p['evaluation'].get('mechanism',{}).get('movement')
            if p['method']=='SC':row['movement_error']=0.
            best=min(data['trials'],key=lambda r:(r['inertia'],r['seed']));row.update(diagnostic_min_inertia_seed=best['seed'],diagnostic_min_inertia_acc=best['acc'],diagnostic_min_inertia_nmi=best['nmi'])
            metrics.append(row);lookup[(p['benchmark'],p['method'],p['rho'],p['tau_multiplier'],panel)]=(p,data,row)
    rng=np.random.Generator(np.random.PCG64(424242));bootstrap=rng.integers(0,50,size=(10000,50));contrasts=[]
    for key,(p,data,row) in lookup.items():
        b,m,rho,tau,panel=key
        if m not in CANDIDATES:continue
        for control in contrast_controls(m):
            crho=0. if control in ['SC','SSC_REFERENCE'] else rho;ctau=1. if control in ['SC','SSC_REFERENCE','QSSC','TUBE_UNIFORM','GUARD_UNIFORM','UNIFORM_GRAPH_ALIAS'] else tau
            found=lookup.get((b,control,crho,ctau,panel))
            alias=control=='UNIFORM_GRAPH_ALIAS' and (rho!=.1 or tau!=1.)
            if alias:found=lookup.get((b,'QSSC',rho,1.,panel))
            out=dict(benchmark=b,candidate=m,control=control,rho=rho,tau_multiplier=tau,panel=panel,candidate_id=p['id'],control_id=found[0]['id'] if found else None,qualified_pair=bool(p['qualified'] and found and found[0]['qualified']),status='COMPLETE' if found else 'CONTROL_UNAVAILABLE',exact_rescaling_alias=alias)
            if found:
                cp,cd,cm=found
                for metric in ['acc','nmi']:
                    diff=np.array([t[metric] for t in data['trials']])-np.array([t[metric] for t in cd['trials']]);means=diff[bootstrap].mean(axis=1)
                    out[metric+'_delta']=float(diff.mean());out[metric+'_delta_sd']=float(diff.std(ddof=1));out[metric+'_lower']=float(np.quantile(means,.025));out[metric+'_upper']=float(np.quantile(means,.975))
            contrasts.append(out)
    macros=[]
    groups=sorted({(r['candidate'],r['control'],r['rho'],r['tau_multiplier'],r['panel']) for r in contrasts})
    for m,c,rho,tau,panel in groups:
        rows=[r for r in contrasts if (r['candidate'],r['control'],r['rho'],r['tau_multiplier'],r['panel'])==(m,c,rho,tau,panel) and r['qualified_pair']]
        mask=sorted(r['benchmark'] for r in rows);macro=dict(candidate=m,control=c,rho=rho,tau_multiplier=tau,panel=panel,paired_n=len(rows),cohort_mask=';'.join(mask),full_eight_cohort=len(rows)==8)
        for metric in ['acc','nmi']:
            values=[r[metric+'_delta'] for r in rows];macro[metric+'_available_case_delta']=float(np.mean(values)) if values else None;macro[metric+'_eight_cohort_delta']=float(np.mean(values)) if len(rows)==8 else None
            macro[metric+'_wins']=sum(v>1e-12 for v in values);macro[metric+'_ties']=sum(abs(v)<=1e-12 for v in values);macro[metric+'_losses']=sum(v< -1e-12 for v in values)
        macro['joint_wins']=sum(r['acc_delta']>=-1e-12 and r['nmi_delta']>=-1e-12 and (r['acc_delta']>1e-12 or r['nmi_delta']>1e-12) for r in rows);macro['joint_losses']=sum(r['acc_delta']< -1e-12 or r['nmi_delta']< -1e-12 for r in rows);macro['joint_ties']=len(rows)-macro['joint_wins']-macro['joint_losses'];macros.append(macro)
    return metrics,coverage,mechanisms,trials,contrasts,macros


def render(records,output,*,plots=True):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);metrics,coverage,mechanisms,trials,contrasts,macros=derive(records)
    write_csv(output/'primary_metrics.csv',[r for r in metrics if r['stage']<=4]);write_csv(output/'secondary_metrics.csv',[r for r in metrics if r['stage']>=5]);write_csv(output/'coverage.csv',coverage);write_csv(output/'mechanism_diagnostics.csv',mechanisms);write_csv(output/'paired_differences.csv',contrasts);write_csv(output/'macro_differences.csv',macros);write_csv(output/'resource_usage.csv',records['resource_usage'])
    text=io.StringIO();fields=['id','benchmark','method','rho','tau_multiplier','panel','seed','acc','nmi','inertia','iterations'];writer=csv.DictWriter(text,fieldnames=fields);writer.writeheader();writer.writerows(trials)
    (output/'trials.csv.gz').write_bytes(gzip.compress(text.getvalue().encode(),mtime=0))
    primary=[r for r in macros if r['rho']==.1 and r['tau_multiplier']==1. and r['control'] in ['QSSC','SSC_REFERENCE','SC']]
    for b in ORDER:
        rows=[r for r in metrics if r['benchmark']==b and r['stage']<=4];(output/'benchmarks').mkdir(exist_ok=True)
        order=['SC','SSC_REFERENCE','HISTORICAL_IRLS','QSSC','UNIFORM_GRAPH_ALIAS','R3_E7_CAVITY','R3_E7_PILOT','R3_E7_ANCHOR','R3_E7_LEVERAGE','R3_E7_SHUFFLE400','R3_E7_SHUFFLE401','R3_E7_SHUFFLE402','TUBE_UNIFORM','R3_E1_V3_CAVITY','R3_E1_V3_PILOT','R3_E1_V3_SHUFFLE400','R3_E1_V3_SHUFFLE401','R3_E1_V3_SHUFFLE402','GUARD_UNIFORM','R3_E5_V2_CAVITY','R3_E5_V2_PILOT','R3_E5_V2_SHUFFLE400','R3_E5_V2_SHUFFLE401','R3_E5_V2_SHUFFLE402'];rows.sort(key=lambda r:(r['panel'],order.index(r['method']) if r['method'] in order else 99))
        text=f'# {b}: fixed-cohort results\n\nConditional development evidence on a retrospectively selected cohort. ACC/NMI and sample SD are percentages from the same 50 starts. Unmatched or uncertified finite outputs are descriptive. Original SSC uses its locked historical gamma; new refinements use movement 0.10.\n\n'+table(rows,['panel','method','acc_mean','acc_sd','nmi_mean','nmi_sd','movement','qualified','status'])
        missing=[r for r in coverage if r['benchmark']==b and r['stage']<=4 and not r['finite']]
        if missing:text+='\n## Unavailable outputs\n\n'+table(missing,['method','status'])
        paired=[r for r in contrasts if r['benchmark']==b and r['rho']==.1 and r['tau_multiplier']==1.]
        text+='\n## Paired candidate contrasts\n\n'+table(paired,['panel','candidate','control','acc_delta','nmi_delta','acc_lower','acc_upper','nmi_lower','nmi_upper','qualified_pair','status'])
        (output/'benchmarks'/f'{b}.md').write_text(text)
    qualified=sum(r['qualified'] for r in coverage if r['stage']in[3,4]);total=sum(r['stage']in[3,4] for r in coverage);finite=sum(r['finite'] for r in coverage);cpu=sum(r['charged_cpu_seconds'] for r in records['resource_usage'])/3600
    intro=f'# Round-three results\n\nThis is conditional development evidence on eight retrospectively selected report cohorts, not an unseen test. Full eight-cohort means are NA whenever an exact contrast lacks any qualified pair. Available-case comparisons with different masks must not be ranked.\n\nThere are {finite}/{len(coverage)} finite declared profiles and {qualified}/{total} qualified primary/control profiles, including exact aliases. Charged CPU at this export: {cpu:.3f} core-hours. Missing, failed, timed-out and unmatched outputs remain in [coverage.csv](coverage.csv).\n\n'
    intro+='## Primary comparisons\n\nChanges are percentage points. Both metrics use one paired cohort mask. Original SSC and movement-matched QSSC answer different questions.\n\n'+table(primary,['panel','candidate','control','paired_n','cohort_mask','acc_eight_cohort_delta','nmi_eight_cohort_delta','acc_available_case_delta','nmi_available_case_delta','joint_wins','joint_losses'])
    intro+='\n## Self-influence falsification\n\nThe decisive control is the same intervention using uncorrected pilot scores. A candidate that does not improve over that control has no demonstrated self-influence benefit.\n\n'+table([r for r in macros if r['rho']==.1 and r['tau_multiplier']==1. and r['control'].endswith('_PILOT')],['panel','candidate','control','paired_n','cohort_mask','acc_available_case_delta','nmi_available_case_delta','joint_wins','joint_losses'])
    intro+='\n[Contribution verdict](contribution_verdict.md) · [All paired contrasts](paired_differences.csv) · [Mechanisms](mechanism_diagnostics.csv) · [Protocol](../../docs/extension_round3/experiment_protocol.md). Bootstrap intervals are conditional on rounding starts, use 10,000 draws with seed 424242, are pointwise and unadjusted across contrasts, and are not a generalization guarantee. All planned controls and secondary rows are listed, including failures.\n'
    (output/'summary.md').write_text(intro)
    log=output/'experiment_log.md'
    lines=['# Scientific experiment log\n','\nThe registered queue and numerical qualifications were frozen before terminal benchmark-label access. Each row records one fixed configuration and seed panel; no score triggers a new fit. Numerical failures are retained, with the next decision fixed to report rather than retune.\n\n']
    for r in coverage:
        matching=[m for m in metrics if m['id']==r['id']]
        if matching:
            for m in matching:lines.append(f"- `{r['id']}` / {m['panel']} / seeds 0–49: ACC {m['acc_mean']:.6f} ± {m['acc_sd']:.6f}, NMI {m['nmi_mean']:.6f} ± {m['nmi_sd']:.6f}; {r['status']}; qualified={r['qualified']}. Interpretation: {'eligible conditional comparison' if r['qualified'] else 'descriptive only; finite reference or numerical/movement limit'}. Next decision: retain in the registered contrast, without reselection.\n")
        else:lines.append(f"- `{r['id']}`: {r['status']}. No complete paired panel. Next decision: report unavailable; no score substituted.\n")
    # Existing log entries are immutable; a new export may only append.
    new=''.join(lines)
    if not log.exists():log.write_text(new)
    elif log.read_text()!=new:
        old=log.read_text();addition='\n## Additional registered export\n\n'+''.join(x for x in lines[3:] if x not in old)
        if addition.strip()!='## Additional registered export':log.write_text(old+addition)
    verdict=['# Contribution verdict\n\n','The numerical identity is inherited from rank-one inversion. The scoped project contribution is its frozen graph evidence and controlled insertion into three SSC objectives. This study does not establish the first graph cross-validation or leave-one-out algorithm.\n\n']
    for candidate in CANDIDATES:
        rows=[r for r in macros if r['candidate']==candidate and r['rho']==.1 and r['tau_multiplier']==1. and r['control']==candidate.removesuffix('_CAVITY')+'_PILOT']
        supported=bool(len(rows)==2 and all(r['paired_n']==8 and r['acc_eight_cohort_delta']>0 and r['nmi_eight_cohort_delta']>=0 for r in rows))
        primary_rows=[r for r in coverage if r['method']==candidate and r['rho']==.1 and r['tau_multiplier']==1.]
        diagnostic=[r for r in mechanisms if r['method']==candidate and r['rho']==.1 and r['tau_multiplier']==1.]
        active=sum(r.get('weighted_rank_difference_from_pilot',0)>1e-10 for r in diagnostic)
        verdict.append(f"## {candidate}\n\nPrimary numerical qualification: {sum(r['qualified'] for r in primary_rows)}/8 profiles. Cavity and pilot allocations differ by more than 10⁻¹⁰ in weighted mean rank on {active}/{len(diagnostic)} finite primary profiles. This descriptive activity check is separate from a clustering benefit.\n\nNumerical validity is profile-specific and recorded separately from mechanism activity and accuracy. {'Both complete panels improve their mean ACC without mean NMI regression versus plain pilot; this remains conditional evidence.' if supported else 'A reliable complete two-panel self-influence benefit is not established.'} The table below preserves improvements, regressions and incomplete masks.\n\n")
        selected=[r for r in macros if r['candidate']==candidate and r['rho']==.1 and r['tau_multiplier']==1. and r['control'] in ['SC','SSC_REFERENCE','QSSC',candidate.removesuffix('_CAVITY')+'_PILOT']]
        verdict.append(table(selected,['panel','control','paired_n','cohort_mask','acc_available_case_delta','nmi_available_case_delta','joint_wins','joint_losses'])+'\n')
    verdict.append('A graph can contain mutually supporting wrong connections or genuine sparse within-class bridges. These are explicit failure conditions for disagreement-based protection. A valid convex optimum or an active coefficient change alone cannot demonstrate class recovery. The MSRA source remains an adapted proxy. Sensitivity rows are not replacements for the primary target.\n')
    (output/'contribution_verdict.md').write_text(''.join(verdict))
    if plots:make_plots(metrics,mechanisms,output/'figures')
    return dict(metrics=len(metrics),trials=len(trials),finite=finite,qualified_primary=qualified,primary_total=total)


def make_plots(metrics,mechanisms,folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder.mkdir(parents=True,exist_ok=True);plt.rcParams['svg.fonttype']='none'
    for panel in ['anchor_generated','native']:
        for metric in ['acc','nmi']:
            fig,axs=plt.subplots(2,4,figsize=(13,6),layout='constrained')
            for ax,b in zip(axs.ravel(),ORDER):
                for method in ['QSSC',*CANDIDATES]:
                    rows=sorted([r for r in metrics if r['benchmark']==b and r['method']==method and r['tau_multiplier']==1 and r['panel']==panel],key=lambda r:r['movement'] or 0.)
                    if rows:ax.plot([r['movement'] for r in rows],[r[metric+'_mean'] for r in rows],marker='o',label=method)
                ax.set(title=b,xlabel='Actual movement',ylabel=metric.upper()+' (%)')
            handles,labels=axs.ravel()[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=4,fontsize=7);fig.suptitle('Fixed movement response: '+panel+' (finite outputs; eligibility in tables)');fig.savefig(folder/f'movement_{panel}_{metric}.svg',metadata={'Creator':'Group 23'});plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for method in CANDIDATES:
        rows=[r for r in mechanisms if r['method']==method and r['rho']==.1 and r['tau_multiplier']==1.]
        axs[0].scatter([r.get('leverage_median',0) for r in rows],[r.get('weighted_rank_difference_from_pilot',0) for r in rows],label=method)
        for r in rows:axs[0].annotate(r['benchmark'],(r.get('leverage_median',0),r.get('weighted_rank_difference_from_pilot',0)),fontsize=6)
    first={r['benchmark']:r for r in mechanisms if r['method']=='R3_E7_CAVITY' and r['rho']==.1 and r['tau_multiplier']==1.}
    for b,r in first.items():
        x=r.get('pilot_cross_class_auroc');y=r.get('cavity_cross_class_auroc')
        if x is not None and y is not None:axs[1].scatter(x,y);axs[1].annotate(b,(x,y),fontsize=7)
    axs[0].set(xlabel='Median edge leverage',ylabel='Weighted |cavity rank − pilot rank|',title='Does deletion change the intervention?');axs[1].plot([0,1],[0,1],ls='--',color='grey');axs[1].set(xlabel='Pilot cross-class AUROC',ylabel='Cavity cross-class AUROC',title='Post-fit semantic audit');axs[0].legend(fontsize=6);fig.savefig(folder/'self_influence.svg',metadata={'Creator':'Group 23'});plt.close(fig)


def build(config,root,output):
    records=export_records(config,root);output=Path(output);output.mkdir(parents=True,exist_ok=True);payload=(json.dumps(records,sort_keys=True,allow_nan=False)+'\n').encode();archive=output/'scalar_records.json.gz';archive.write_bytes(gzip.compress(payload,mtime=0));counts=render(records,output)
    files={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p.name!='release_manifest.json'}
    manifest=dict(schema='ssc-round3-release-v1',records='scalar_records.json.gz',compressed_sha256=digest(archive),uncompressed_sha256=__import__('hashlib').sha256(payload).hexdigest(),files=files,counts=counts,numerical_freeze_sha256=records['numerical_freeze_sha256'],source_fingerprint=records['source_fingerprint'])
    atomic_json(output/'release_manifest.json',manifest);return manifest
