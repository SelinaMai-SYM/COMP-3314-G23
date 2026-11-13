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


def resource_rows(root):
    store=ArtifactStore(root);ledger=ResourceLedger(root).state();jobs=[]
    for e in ledger['entries']:
        job=store.root/'command_jobs'/e['run_id']/'status.json';status=read(job) if job.exists() else {}
        jobs.append({**e,'peak_RSS_bytes':status.get('max_sampled_RSS_bytes'),'wall_seconds':status.get('wall_seconds'),'stop_reason':status.get('stop_reason'),'exit_code':status.get('exit_code'),'cpu_limit_seconds':status.get('cpu_limit'),'terminal_accounting_complete':status.get('terminal_accounting_complete')})
    return ledger,jobs


def export_records(config,root):
    spec,lock,store=locked(root,config)
    if read(store.root/'terminal_evaluation.json')['stage']!='TERMINAL_SCORING_COMPLETE':raise ValueError('terminal evaluation incomplete')
    frozen=read(store.root/'numerical_freeze.json');profiles=[]
    for q in queue():
        r=read(profile_path(store,q['id']));e=read(store.root/'evaluations'/(q['id']+'.json'));a=frozen['qualification'][q['id']]
        # Scalar release contains no matrices, labels or machine paths. Numeric
        # object identities point to the independently recoverable external store.
        p={**q,'status':a['status'] if a['status'] in ['QUALIFICATION_AUDIT_FAILURE','PATH_CPU_PROTOCOL_DEVIATION'] else r['status'],'numerical_status':r['status'],'protocol_compliant':a.get('protocol_compliant',True),'protocol_deviation':a.get('protocol_deviation'),'qualified':a['qualified'],'certified':a['certified'],'certificate':a.get('certificate',r.get('certificate',{})),'lambda':r.get('lambda',r.get('lambda_value')),'source_fingerprint':r.get('source_fingerprint'),'finite':bool(r.get('result')),'result_identity':identity(r['result']) if r.get('result') else None,'G_object':r.get('result',{}).get('G'),'path_CPU_seconds':r.get('path_CPU_seconds'),'distinct_lambdas':r.get('distinct_lambdas'),'evaluation':{k:v for k,v in e.items() if k not in ['panels']}}
        attempts=sorted((store.root/'command_jobs').glob('r3-'+q['id']+'-*'),key=lambda path:int(path.name.rsplit('-',1)[-1]))
        job=read(attempts[-1]/'status.json') if attempts and (attempts[-1]/'status.json').exists() else {}
        p.update(execution_status=job.get('status'),execution_stop_reason=job.get('stop_reason'),execution_run_id=job.get('run_id'),execution_CPU_seconds=job.get('CPU_seconds'),failure_type=r.get('failure_type'))
        p['panels']={panel:{k:v for k,v in value.items() if k!='scientific_objects'} for panel,value in e.get('panels',{}).items()};profiles.append(p)
    from sklearn.metrics import adjusted_rand_score
    planned_lookup={(q['benchmark'],q['method'],q['rho'],q['tau_multiplier']):q for q in queue()}
    profile_lookup={p['id']:p for p in profiles}
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
            other=read(cp);control_profile=profile_lookup[q['id']]
            if p['G_object'] and control_profile['G_object']:
                H=store.get(lock['cohorts'][p['benchmark']]['objects']['H']);scale=float(np.linalg.norm(H-H.mean(axis=0)))
                distance=float(np.linalg.norm(store.get(p['G_object'])-store.get(control_profile['G_object']))/scale) if scale else 0.
                diagnostic=p['evaluation']['mechanism'];diagnostic['embedding_difference_vs_'+control]=distance
                error=p['certificate'].get('movement_error');control_error=control_profile['certificate'].get('movement_error')
                diagnostic['certified_embedding_difference_lower_vs_'+control]=max(0.,distance-error-control_error) if error is not None and control_error is not None and p['certificate'].get('valid_bound') and control_profile['certificate'].get('valid_bound') else None
            for panel,data in raw.get('panels',{}).items():
                od=other.get('panels',{}).get(panel)
                if not data['complete'] or not od or not od['complete']:continue
                agreements=[]
                for a,b in zip(data['scientific_objects'],od['scientific_objects']):
                    agreements.append(adjusted_rand_score(store.get(a['labels']),store.get(b['labels'])))
                p['evaluation']['mechanism'][panel+'_changed_partition_fraction_vs_'+control]=float(np.mean(np.asarray(agreements)<1-1e-12))
                p['evaluation']['mechanism'][panel+'_partition_ARI_vs_'+control]=float(np.mean(agreements))
    ledger,jobs=resource_rows(root)
    return dict(schema='ssc-round3-scalar-release-v1',protocol_sha256=digest(config),effective_protocol_sha256=identity(spec),input_lock_sha256=digest(ROOT/'configs/extension_round3/cohort_lock.json'),numerical_freeze_sha256=digest(store.root/'numerical_freeze.json'),source_fingerprint=lock['source_fingerprint'],numerical_settings={'calibration_max_iterations':spec['calibration']['max_iterations'],'fit_cpu_seconds':600,'path_cpu_seconds':1800},analysis_source_files_at_freeze=frozen.get('analysis_source_files',{}),analysis_source_files_at_export={str((ROOT/'experiments/extension_round3'/n).relative_to(ROOT)):digest(ROOT/'experiments/extension_round3'/n) for n in ['evaluate.py','report.py','release.py']},environment=lock['environment'],cohorts={b:{k:c[k] for k in ['candidate_id','n','K','prep','historical_identity','adaptation_flags','gamma_nominal','gamma_effective','variant']} for b,c in lock['cohorts'].items()},profiles=profiles,resource_usage=jobs,native_path_cost_audit=frozen.get('native_path_cost_audit',[]),budget={k:v for k,v in ledger.items() if k not in ['entries','active']},clock=read(store.root/'clock.json'),selection_qualification=lock['selection_qualification'])


def contrast_controls(method):
    prefix=method.removesuffix('_CAVITY');controls=['QSSC','SC','SSC_REFERENCE',prefix+'_PILOT']
    if method=='R3_E7_CAVITY':controls+=['UNIFORM_GRAPH_ALIAS',prefix+'_ANCHOR',prefix+'_LEVERAGE']
    else:controls+=['TUBE_UNIFORM' if method=='R3_E1_V3_CAVITY' else 'GUARD_UNIFORM']
    return controls+[prefix+'_SHUFFLE'+str(s) for s in [400,401,402]]


def derive(records):
    metrics=[];coverage=[];mechanisms=[];trials=[];lookup={}
    for p in records['profiles']:
        cert=p['certificate'];coverage.append({**{k:p[k] for k in ['id','benchmark','method','rho','stage','tau_multiplier','status','finite','qualified','certified','lambda','path_CPU_seconds','distinct_lambdas']},**{k:p.get(k) for k in ['numerical_status','protocol_compliant','protocol_deviation','execution_status','execution_stop_reason','execution_run_id','execution_CPU_seconds','failure_type']},'rounding_complete':p['evaluation'].get('complete',False)})
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
    write_csv(output/'native_path_costs.csv',[dict(row,limit_CPU_seconds=1800.) for row in records.get('native_path_cost_audit',[]) if row['native_CPU_seconds']>0],fields=['benchmark','method','tau_multiplier','native_CPU_seconds','limit_CPU_seconds','within_path_cap'])
    text=io.StringIO();fields=['id','benchmark','method','rho','tau_multiplier','panel','seed','acc','nmi','inertia','iterations'];writer=csv.DictWriter(text,fieldnames=fields);writer.writeheader();writer.writerows(trials)
    (output/'trials.csv.gz').write_bytes(gzip.compress(text.getvalue().encode(),mtime=0))
    primary=[r for r in macros if r['rho']==.1 and r['tau_multiplier']==1. and r['control'] in ['QSSC','SSC_REFERENCE','SC']]
    for b in ORDER:
        rows=[r for r in metrics if r['benchmark']==b and r['stage']<=4];(output/'benchmarks').mkdir(exist_ok=True)
        order=['SC','SSC_REFERENCE','HISTORICAL_IRLS','QSSC','UNIFORM_GRAPH_ALIAS','R3_E7_CAVITY','R3_E7_PILOT','R3_E7_ANCHOR','R3_E7_LEVERAGE','R3_E7_SHUFFLE400','R3_E7_SHUFFLE401','R3_E7_SHUFFLE402','TUBE_UNIFORM','R3_E1_V3_CAVITY','R3_E1_V3_PILOT','R3_E1_V3_SHUFFLE400','R3_E1_V3_SHUFFLE401','R3_E1_V3_SHUFFLE402','GUARD_UNIFORM','R3_E5_V2_CAVITY','R3_E5_V2_PILOT','R3_E5_V2_SHUFFLE400','R3_E5_V2_SHUFFLE401','R3_E5_V2_SHUFFLE402'];rows.sort(key=lambda r:(r['panel'],order.index(r['method']) if r['method'] in order else 99))
        c=records['cohorts'][b]
        text=f"# {b}: fixed-cohort results\n\nInput `{c['candidate_id']}`: n={c['n']}, K={c['K']}, preparation {c['prep']}. Historical identity: {c['historical_identity']}. Adaptations: {c['adaptation_flags']}. Locked original SSC: {c['variant']}, nominal gamma {c['gamma_nominal']}, effective gamma {c['gamma_effective']}.\n\nConditional development evidence on a retrospectively selected cohort. ACC/NMI and sample SD are percentages from the same 50 starts. Unmatched or uncertified finite outputs are descriptive. Original SSC uses its locked historical gamma; new refinements use movement 0.10.\n\n"+table(rows,['panel','method','acc_mean','acc_sd','nmi_mean','nmi_sd','movement','qualified','status'])
        missing=[r for r in coverage if r['benchmark']==b and r['stage']<=4 and not r['finite']]
        if missing:text+='\n## Unavailable outputs\n\n'+table(missing,['method','status'])
        paired=[r for r in contrasts if r['benchmark']==b and r['rho']==.1 and r['tau_multiplier']==1.]
        text+='\n## Paired candidate contrasts\n\n'+table(paired,['panel','candidate','control','acc_delta','nmi_delta','acc_lower','acc_upper','nmi_lower','nmi_upper','qualified_pair','status'])
        text+='\nIntervals are pointwise 95% paired bootstrap intervals (10,000 draws, seed 424242), conditional on these fixed embeddings and rounding starts. They are unadjusted for multiple comparisons and do not quantify dataset generalization or solver uncertainty.\n'
        (output/'benchmarks'/f'{b}.md').write_text(text)
    qualified=sum(r['qualified'] for r in coverage if r['stage']in[3,4]);total=sum(r['stage']in[3,4] for r in coverage);finite=sum(r['finite'] for r in coverage);cpu=sum(r['charged_cpu_seconds'] for r in records['resource_usage'])/3600
    intro=f'# Edge-deletion refinement results\n\nThis is conditional development evidence on eight retrospectively selected report cohorts, not an unseen test. Full eight-cohort means are NA whenever an exact contrast lacks any qualified pair. Available-case comparisons with different masks must not be ranked.\n\nThere are {finite}/{len(coverage)} finite declared profiles and {qualified}/{total} qualified primary/control profiles, including exact aliases. Charged CPU at this export: {cpu:.3f} core-hours. Missing, failed, timed-out and unmatched outputs remain in [coverage.csv](coverage.csv).\n\n'
    deviations=[r for r in coverage if not r.get('protocol_compliant',True)]
    if deviations:
        paths=sorted({r['benchmark']+' / '+r['method'] for r in deviations})
        intro+=f"Native CPU costs exceed the declared path cap on {len(paths)} paths ({'; '.join(paths)}). All {len(deviations)} declared profiles on those paths are conservatively descriptive only, even when their numerical certificate passes. Failed work and overruns remain charged globally. [Native path totals](native_path_costs.csv) · [Eligibility and resource limits](../../docs/extension_round3/experiment_protocol.md#eligibility-and-resource-limits).\n\n"
    intro+='## Primary comparisons\n\nChanges are percentage points. Both metrics use one paired cohort mask. Original SSC and movement-matched QSSC answer different questions.\n\n'+table(primary,['panel','candidate','control','paired_n','cohort_mask','acc_eight_cohort_delta','nmi_eight_cohort_delta','acc_available_case_delta','nmi_available_case_delta','joint_wins','joint_losses'])
    intro+='\n## Self-influence falsification\n\nThe decisive control is the same intervention using uncorrected pilot scores. A candidate that does not improve over that control has no demonstrated self-influence benefit.\n\n'+table([r for r in macros if r['rho']==.1 and r['tau_multiplier']==1. and r['control'].endswith('_PILOT')],['panel','candidate','control','paired_n','cohort_mask','acc_available_case_delta','nmi_available_case_delta','joint_wins','joint_losses'])
    intro+='\n[All paired contrasts](paired_differences.csv) · [Mechanisms](mechanism_diagnostics.csv) · [Protocol](../../docs/extension_round3/experiment_protocol.md). Bootstrap intervals are conditional on rounding starts, use 10,000 draws with seed 424242, are pointwise and unadjusted across contrasts, and are not a generalization guarantee. All planned controls and secondary rows are listed, including failures.\n'
    (output/'summary.md').write_text(intro)
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
                    if rows:
                        line,=ax.plot([r['movement'] for r in rows],[r[metric+'_mean'] for r in rows],linewidth=.8,alpha=.7,label=method)
                        for qualified,marker in [(True,'o'),(False,'x')]:
                            points=[r for r in rows if r['qualified']==qualified]
                            ax.scatter([r['movement'] for r in points],[r[metric+'_mean'] for r in points],marker=marker,color=line.get_color(),s=20)
                ax.set(title=b,xlabel='Actual movement',ylabel=metric.upper()+' (%)')
            handles,labels=axs.ravel()[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=4,fontsize=7);fig.suptitle('Fixed movement response: '+panel+' (dots: qualified; ×: descriptive only)');fig.savefig(folder/f'movement_{panel}_{metric}.svg',metadata={'Creator':'Group 23'});plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(15,4),layout='constrained')
    for ax,method,label,color in [(axs[0],'R3_E7_CAVITY','Graph / guard (mass w)','tab:blue'),(axs[1],'R3_E1_V3_CAVITY','Tube (mass w × anchor length)','tab:orange')]:
        rows=[r for r in mechanisms if r['method']==method and r['rho']==.1 and r['tau_multiplier']==1.]
        ax.scatter([r.get('leverage_median',0) for r in rows],[r.get('weighted_rank_difference_from_pilot',0) for r in rows],color=color)
        for r in rows:
            b=r['benchmark'];right=b in ['UMIST','USPS','BinAlpha'];offset=(-3,-10 if b=='BinAlpha' else 5) if right else (4,-9 if b=='JAFFE' else 4)
            ax.annotate(b,(r.get('leverage_median',0),r.get('weighted_rank_difference_from_pilot',0)),xytext=offset,textcoords='offset points',ha='right' if right else 'left',fontsize=7)
        ax.set(xlabel='Median edge leverage',ylabel='Weighted |cavity rank − pilot rank|',title=label)
    first={r['benchmark']:r for r in mechanisms if r['method']=='SC' and r['tau_multiplier']==1.}
    offsets={'UMIST':(4,-13),'MSRA50':(-42,8),'BinAlpha':(4,10),'YaleB':(4,-13),'AR':(4,-12),'ORL':(4,8),'USPS':(-31,-11),'JAFFE':(4,-13)}
    for b,r in first.items():
        x=r.get('pilot_cross_class_auroc');y=r.get('cavity_cross_class_auroc')
        if x is not None and y is not None:axs[2].scatter(x,y);axs[2].annotate(b,(x,y),xytext=offsets.get(b,(4,4)),textcoords='offset points',fontsize=7,arrowprops={'arrowstyle':'-','lw':.4,'color':'0.4'})
    axs[2].plot([0,1],[0,1],ls='--',color='grey');axs[2].set(xlabel='Pilot cross-class AUROC',ylabel='Cavity cross-class AUROC',title='Post-fit semantic audit');fig.savefig(folder/'self_influence.svg',metadata={'Creator':'Group 23'});plt.close(fig)


def build(config,root,output):
    records=export_records(config,root);output=Path(output);output.mkdir(parents=True,exist_ok=True);payload=(json.dumps(records,sort_keys=True,allow_nan=False)+'\n').encode();archive=output/'scalar_records.json.gz';archive.write_bytes(gzip.compress(payload,mtime=0));counts=render(records,output)
    files={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p.name!='release_manifest.json'}
    manifest=dict(schema='ssc-round3-release-v1',records='scalar_records.json.gz',compressed_sha256=digest(archive),uncompressed_sha256=__import__('hashlib').sha256(payload).hexdigest(),files=files,counts=counts,trials={'path':'trials.csv.gz','compressed_sha256':digest(output/'trials.csv.gz'),'uncompressed_sha256':__import__('hashlib').sha256(gzip.decompress((output/'trials.csv.gz').read_bytes())).hexdigest()},numerical_freeze_sha256=records['numerical_freeze_sha256'],source_fingerprint=records['source_fingerprint'])
    atomic_json(output/'release_manifest.json',manifest);return manifest
