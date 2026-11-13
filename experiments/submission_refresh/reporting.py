"""Build report inputs from committed authoritative CSV/JSON records only.

No fitting, label inspection, selection, or external artifact lookup occurs here.
Missing aggregation is printed explicitly; unavailable values never become zeros.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path
if __package__:
    from .csv_transport import resolve_csv,open_csv
else:
    # Makefile invokes this file directly, including in an uninstalled checkout.
    # Resolve the sibling explicitly: never import an old global project copy or
    # add a checkout to sys.path/PYTHONPATH to make the script work.
    import importlib.util
    import sys
    _transport_path=Path(__file__).resolve().with_name('csv_transport.py')
    _transport_name='comp3314_report_csv_transport_'+hashlib.sha256(str(_transport_path).encode()).hexdigest()[:16]
    _transport_spec=importlib.util.spec_from_file_location(_transport_name,_transport_path)
    if _transport_spec is None or _transport_spec.loader is None:
        raise ImportError('Cannot load own-checkout CSV transport: '+str(_transport_path))
    _transport_module=importlib.util.module_from_spec(_transport_spec)
    sys.modules[_transport_name]=_transport_module
    try:_transport_spec.loader.exec_module(_transport_module)
    except BaseException:
        sys.modules.pop(_transport_name,None)
        raise
    resolve_csv=_transport_module.resolve_csv
    open_csv=_transport_module.open_csv

BENCHMARKS=['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']
ENDPOINTS=['mean_sample_sd_50','native_best_of_50']
def public_presentation_inputs(root):
    """Choose publication style; this never qualifies a numerical result."""
    root=Path(root)
    evidence=root/'configs/submission_refresh/evidence_manifest.json'
    if evidence.is_file() and json.loads(evidence.read_text()).get('schema') in ['submission-scalar-evidence-public-v1','submission-scalar-evidence-public-v2']:
        return {'evidence_manifest':evidence}
    return {}

METHODS={'kmeans':'K-means','sc':'SC','pca_kmeans':'PCA--K-means','pca_spectral':'PCA--SC',
         'pca_sc':'PCA--SC','lda_kmeans':'LDA--K-means','lda_spectral':'LDA--SC',
         'lda_sc':'LDA--SC','llc':'LLC','spls':'SLPS','ssc':'SSC','lda_existing':'LDA existing',
         'lda_reference':'ClustPy reference','lda_adapted':'Ridge LDA (adapted)',
         'lda_adapted_sc':'Ridge LDA--SC (adapted)','raw_sc':'Raw SC',
         'pca_p0_sc':'PCA$_{p_0}$--SC','pca_r_sc':'PCA$_r$--SC'}


def escape(value):
    replacements={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#',
                  '_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(replacements.get(c,c) for c in str(value))


def break_text(value):
    return escape(value).replace(r'\_',r'\_\allowbreak ')


def number(value,digits=2):
    try:
        value=float(value)
        return f'{value:.{digits}f}' if math.isfinite(value) else '--'
    except (ValueError,TypeError):return '--'


def value(row,*keys,default=None):
    for key in keys:
        if row.get(key) not in [None,'']:return row[key]
    return default


def metric(row,metric_name,*,paper=False,native=None):
    m=metric_name.lower();M=m.upper()
    if paper:
        mean=value(row,'paper_'+m,'paper_'+M);sd=value(row,'paper_'+m+'_sd','paper_'+M+'_SD')
    else:
        mean=value(row,m+'_mean','measured_'+M);sd=value(row,m+'_sd','measured_'+M+'_SD')
    if native is None:native=row.get('endpoint')=='native_best_of_50' and not paper
    if number(mean)=='--':return '--'
    return number(mean)+(r' $\pm$ '+number(sd) if not native and number(sd)!='--' else '')


def status_abbreviation(row):
    status=str(value(row,'solver_status_current_audit','solver_status','solver_status_original',default=''))
    if 'UNCERTIFIED' not in status and ('CERTIFIED' in status or 'ANALYTIC' in status):return 'C'
    if 'MAX_ITER' in status or 'TRUNCATED' in status:return 'T'
    if any(s in status for s in ['ITERATE','UNCERTIFIED','CONVERGED_BY']):return 'I'
    if status in ['NOT_APPLICABLE','']:return '--'
    return 'U'


def read_csv(path):
    actual=resolve_csv(path)
    if actual is None:return []
    previous=csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous,64*1024*1024))
        with open_csv(actual,newline='') as f:return list(csv.DictReader(f))
    finally:csv.field_size_limit(previous)


def read_json(path,default=None):
    return json.loads(path.read_text()) if path.exists() else default


def unpack_json(value,default=None):
    if isinstance(value,(dict,list)):return value
    try:return json.loads(value) if value else default
    except (ValueError,TypeError):return default


def table(header,rows,spec,caption=None,label=None,*,long=False):
    env='longtable' if long else 'tabular'
    output=[]
    if not long:output += [r'\begin{table}[ht]',r'\centering']
    output += [r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}',f'\\begin{{{env}}}{{{spec}}}']
    if long and caption:
        output += [f'\\caption{{{caption}}}'+(f'\\label{{{label}}}' if label else '')+r'\\']
    output += [r'\toprule',' & '.join(header)+r' \\',r'\midrule']
    if long:output += [r'\endfirsthead',r'\toprule',' & '.join(header)+r' \\',r'\midrule\endhead']
    output += [(' & '.join(row)+r' \\') if isinstance(row,list) else row for row in rows]
    output += [r'\bottomrule',f'\\end{{{env}}}',r'\endgroup']
    if not long:
        if caption:output += [f'\\caption{{{caption}}}'+(f'\\label{{{label}}}' if label else '')]
        output += [r'\end{table}']
    return '\n'.join(output)+'\n'


def short_setting(row):
    variant=value(row,'variant',default='')
    gamma=value(row,'gamma_nominal',default='')
    init=value(row,'initialization','initialization_exact_name',default='')
    init={'RANDOM':'R','VANILLA_KMEANSPP':'V','SKLEARN_GREEDY_KMEANSPP':'G'}.get(init,init)
    parts=[escape(v) for v in [row.get('prep'),variant] if v]
    if gamma:
        try:parts.append(r'$\gamma='+f'{float(gamma):g}'+r'$')
        except ValueError:parts.append(escape(gamma))
    if init:parts.append(escape(init))
    return ', '.join(parts) or '--'


def paper_lookup(records):
    lookup={}
    for row in (records or {}).get('rows',[]):
        lookup.setdefault((row['benchmark'],row['method']),{})['paper_'+row['metric']]=row['mean']
        lookup[(row['benchmark'],row['method'])]['paper_'+row['metric']+'_sd']=row['sd']
    for (benchmark,method),row in list(lookup.items()):
        if method.endswith('_spectral'):lookup[(benchmark,method.replace('_spectral','_sc'))]=row
    return lookup


def figure(root,rows,papers,winners,catalogue):
    """Export a standard static scientific scatter; no generated raster artwork."""
    destination=root/'report/figures/subset_acc_nmi.pdf'
    valid=[r for r in rows if r.get('endpoint','mean_sample_sd_50')=='mean_sample_sd_50' and number(r.get('acc_mean'))!='--' and number(r.get('nmi_mean'))!='--']
    if not valid:
        if destination.exists():destination.unlink()
        return False
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    fig,axes=plt.subplots(4,2,figsize=(7.1,9.2),layout='constrained')
    candidate_meta={r['candidate_id']:r for r in catalogue}
    def family_of(row):
        meta=candidate_meta.get(row.get('candidate_id'),{})
        return meta.get('parent_id',row.get('family','unspecified')) if row.get('benchmark')=='YaleB' or row.get('family')=='fixed_membership' else row.get('family','unspecified')
    family_names=sorted({family_of(r) for r in valid})
    colors={name:plt.colormaps['tab20'](index%20) for index,name in enumerate(family_names)}
    for benchmark,ax in zip(BENCHMARKS,axes.ravel()):
        group=[r for r in valid if r['benchmark']==benchmark]
        if group:
            for family in sorted({family_of(r) for r in group}):
                for pool in sorted({r.get('pool','specification_compatible') for r in group if family_of(r)==family}):
                    subset=[r for r in group if family_of(r)==family and r.get('pool','specification_compatible')==pool]
                    label=family.replace('UMIST_','').replace('BinAlpha_','').replace('YaleB_','').replace('AR_','').replace('_',' ')
                    if pool!='specification_compatible':label+=' ('+pool+')'
                    ax.scatter([float(r['acc_mean']) for r in subset],[float(r['nmi_mean']) for r in subset],
                               s=8,alpha=.35,color=colors[family],label=label,
                               marker={'adapted':'^','diagnostic':'x'}.get(pool,'.'))
            for selected in [r for r in winners if r.get('benchmark')==benchmark and r.get('endpoint')=='mean_sample_sd_50']:
                ax.scatter(float(selected['acc_mean']),float(selected['nmi_mean']),s=55,facecolors='none',edgecolors='black',linewidths=.8)
            if len({family_of(r) for r in group})<=5:ax.legend(fontsize=5.5,loc='best',frameon=False)
        else:ax.text(.5,.5,'No complete records',ha='center',va='center',transform=ax.transAxes,fontsize=8)
        paper=papers.get((benchmark,'ssc'),{})
        if paper:ax.scatter(paper['paper_acc'],paper['paper_nmi'],marker='*',s=70,color='black',zorder=5,label='Paper')
        ax.set_title(benchmark,fontsize=9);ax.set_xlabel('ACC (%)',fontsize=8);ax.set_ylabel('NMI (%)',fontsize=8)
        ax.tick_params(labelsize=7);ax.grid(alpha=.15)
    destination.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination,metadata={'CreationDate':None,'ModDate':None,'Title':'Retrospective SSC ACC/NMI search distribution'})
    plt.close(fig)
    return True



def significant(value,digits=5):
    """Compact objective/gap display without changing stored precision."""
    try:
        value=float(value)
        return f'{value:.{digits}g}' if math.isfinite(value) else '--'
    except (TypeError,ValueError):return '--'


def _usps_scalar(row,*keys):
    direct=value(row,*keys)
    if direct is not None:return direct
    for field in ['solver','audit_metadata']:
        nested=unpack_json(row.get(field),{}) or {}
        result=value(nested,*keys)
        if result is not None:return result
    return None


def _usps_bool(value):
    if isinstance(value,bool):return value
    if str(value).lower() in ['true','1','yes']:return True
    if str(value).lower() in ['false','0','no']:return False
    return None


def usps_numerical_appendix(original,continuation_fits,continuation_rounding,input_identity=None,*,public=False):
    """Display every locked numerical point, never select by scores or gaps."""
    stages=['IRLS300','uniform_PDHG','diagonal_PDHG','component_dual_flow','diagonal_warm_restart']
    labels={'SC_F':'SC on F','IRLS300':'IRLS300','uniform_PDHG':'Uniform',
            'diagonal_PDHG':'Diagonal','component_dual_flow':'Flow',
            'diagonal_warm_restart':'Warm restart','diagonal_continuation':'Extra restart'}
    pairs=[]
    for row in original+continuation_fits+continuation_rounding:
        pair=unpack_json(row.get('pair_identity'),None)
        if pair is None:pair=(unpack_json(row.get('provenance'),{}) or {}).get('pair_identity')
        if pair:pairs.append(json.dumps(pair,sort_keys=True))
    if len(set(pairs))>1:raise ValueError('USPS appendix cannot combine different frozen F/W pairs')
    def exact(rows,field,key):
        found=[row for row in rows if row.get(field)==key]
        if len(found)>1:raise ValueError('duplicate committed USPS scalar point: '+str(key))
        return found[0] if found else {}
    sc=exact(original,'name','SC_F')
    if not sc:sc=exact(continuation_rounding,'name','SC_F')
    points=[('SC on F',None,sc,sc,'SC_F')]
    for gamma in [1.,1000.]:
        for stage in stages:
            name=f'gamma_{gamma:g}_{stage}';row=exact(original,'name',name)
            points.append((labels[stage],gamma,row,row,stage))
    # The two preregistered attempts remain visible even before their exports.
    extra_ids=[f'usps-continuation-gamma{gamma:g}-v1' for gamma in [1.,1000.]]
    extra_ids+=sorted({row.get('run_id') for row in continuation_fits if row.get('run_id')} - set(extra_ids))
    extra_ids+=sorted({row.get('name') for row in continuation_rounding if row.get('name') and row.get('name')!='SC_F'}-set(extra_ids))
    for run_id in extra_ids:
        fit=exact(continuation_fits,'run_id',run_id);rounding=exact(continuation_rounding,'name',run_id)
        gamma=value(fit,'gamma_effective','gamma_nominal',default=value(rounding,'gamma_effective','gamma_nominal'))
        if gamma is None:
            gamma=1. if run_id=='usps-continuation-gamma1-v1' else 1000. if run_id=='usps-continuation-gamma1000-v1' else None
        points.append(('Extra restart',gamma,fit,rounding,'diagonal_continuation'))
    numerical=[];performance=[]
    for label,gamma,fit,rounding,stage in points:
        numeric=fit or rounding;sc_row=stage=='SC_F'
        status=_usps_scalar(numeric,'solver_status','status')
        if status in [None,'COMPLETED']:
            status=_usps_scalar(rounding,'solver_status') or status or 'UNAVAILABLE'
        flag=_usps_bool(_usps_scalar(numeric,'certified'))
        certified='--' if sc_row or flag is None else 'C' if flag else 'U'
        cpu=_usps_scalar(numeric,'fit_cpu_seconds','solver_cpu_seconds','original_solver_cpu_seconds','original_fit_cpu_seconds')
        if cpu is None and stage=='diagonal_continuation':cpu=value(fit,'cpu_seconds')
        if cpu is None:
            for field in ['solver','audit_metadata']:
                recorded=unpack_json(numeric.get(field),{}) or {}
                if recorded.get('cpu_seconds') is not None:cpu=recorded['cpu_seconds'];break
        numerical.append([label,significant(gamma,4),significant(_usps_scalar(numeric,'primal')),
                          significant(_usps_scalar(numeric,'dual')),
                          significant(_usps_scalar(numeric,'relative_gap','gap'),3),certified,
                          number(cpu,1),break_text(status)])
        count=value(rounding,'n_trials','n')
        scalar_fields_complete=all(number(rounding.get(key))!='--' for key in ['acc_mean','acc_sd','nmi_mean','nmi_sd'])
        complete=rounding.get('status')=='COMPLETED' and str(count)=='50' and scalar_fields_complete
        means=rounding if complete else {}
        historical=_usps_bool(_usps_scalar(rounding,'historical_300_protocol_complete','complete_historical_execution'))
        historical_label=('yes' if historical else 'no' if historical is False else '--') if stage=='IRLS300' else '--'
        outcome=rounding.get('status') or 'ROUNDING_UNAVAILABLE'
        if rounding.get('status')=='COMPLETED' and not complete:
            outcome='INCOMPLETE_SEED_SET' if str(count)!='50' else 'INCOMPLETE_SCALAR_FIELDS'
        performance.append([label,significant(gamma,4),metric(means,'acc',native=False),metric(means,'nmi',native=False),
                            str(count) if count is not None else '--',historical_label,break_text(outcome)])
    text=[r'\subsection{USPS numerical audit on one newly frozen F/W pair}',
          r'These rows use a newly generated, recoverable current USPS representation and its exact shrinkage graph. They do not identify or replace the missing historical selected F/G arrays. Every non-SC point targets unsquared E8 with undirected coefficient $2\gamma w$. All original ten stages remain visible; the two additional restarts are separate numerical attempts, not replacements for the historical finite-iteration winner or subset-search output.',
          r'Tables~\ref{tab:usps-numerical-audit} and~\ref{tab:usps-numerical-rounding} refer to the same stage/gamma rows. C/U denote the recorded certified/uncertified state, with a required relative gap at most $10^{-5}$ and capacity violation at most $10^{-8}$ for certification. A solver stopping status alone is not a certificate. Uncertified points cannot establish that the mathematical objective lacks clustering capacity. Missing exports or saved points stay unavailable.',
          table(['Stage',r'$\gamma$','Primal','Dual','Rel. gap','C/U','CPU (s)','Solver status'],numerical,
                'p{1.65cm}rrrrcrp{2.4cm}',
                ('Same-target numerical evidence. Original rows show fit CPU only where recorded; extra-restart CPU includes the full numerical attempt. A dash means unavailable metadata, not zero cost.' if public else 'Same-target numerical evidence. Original rows show fit CPU only where committed scalar metadata provides it; extra-restart CPU is the full controller attempt, including checks and I/O. A dash means unavailable metadata, not zero cost. The input manifest hashes each scalar source.'),'tab:usps-numerical-audit',long=True),
          r'Clustering metrics below are percent, mean $\pm$ sample SD over the same fifty greedy K-means++/Lloyd seeds 0--49 on each saved G. Both metrics come from one complete endpoint. This is conditional rounding variability, not independent datasets or full-pipeline uncertainty. A native-best assignment is not substituted for a mean, and its single-run value receives no across-run SD.',
          table(['Stage',r'$\gamma$','ACC','NMI','n','IRLS300 complete','Evaluation status'],performance,
                'p{1.65cm}rrrccp{3.0cm}',
                'Paired rounding protocol on the fixed current F/W. The IRLS300 flag refers only to completion of the declared historical-style 300-step protocol, including its iterate stopping rule; it does not certify optimality. Other stages are separate algorithms/restarts.','tab:usps-numerical-rounding',long=True)]
    if not original and not continuation_fits and not continuation_rounding:
        text.insert(1,r'USPS numerical evaluation is unavailable; the rows below contain no inferred objective or clustering values.' if public else r'No committed USPS numerical evaluation export is currently available. The planned rows below contain no inferred objective or clustering values.')
    if input_identity:
        identity_status=input_identity.get('status','UNAVAILABLE')
        same=input_identity.get('same_current_F_W_content_addresses') is True
        identity_text=('The numerical audit and subset USPS representation record exactly matching current F/W content addresses. ' if same else 'Same-input status between the numerical audit and subset USPS representation is not established as a match. ')
        identity_text+='Recorded input-reference status: '+str(identity_status)+'. This is only a comparison of current input references. Each certificate belongs to its own saved continuation G; it does not certify the locked IRLS G, establish a certified closest search result, or recover missing historical F/G arrays.'
        text.insert(2,escape(identity_text))
    else:text.insert(2,r'The committed same-input reference comparison is unavailable. No identity between numerical-audit inputs and subset-search inputs is inferred.')
    return text


def certified_search_appendix(rows,*,public=False):
    output=[r'\subsection{Separate certified-search availability}',
            r'The closest subset matches above belong to the locked finite historical-style IRLS track. A complete 50-start execution does not establish optimality. No comparable certified subset-search track was executed, so no certified closest winner is selected. Separate numerical references, including a continuation on the current USPS input, cannot transfer a certificate to a different saved G. Counts below describe the historical-style coverage only; native rows summarize the same 50-start configuration pool but select one assignment, with no across-run SD.']
    if not rows:
        output.append(r'Comparable certified-search coverage is unavailable; no certified winner or coverage count is inferred.' if public else r'The machine-readable certified-search availability export is not yet available; no certified winner or coverage count is inferred.')
        return output
    seen=set();rendered=[]
    for row in rows:
        key=(row.get('benchmark'),row.get('pool'),row.get('endpoint'))
        if key in seen:raise ValueError('duplicate certified-search availability endpoint')
        seen.add(key)
        if row.get('certified_closest_config_id') or row.get('status')!='UNAVAILABLE_NO_COMPARABLE_CERTIFIED_SEARCH_COVERAGE':
            raise ValueError('unexpected certified closest claim in unavailable search track')
        endpoint={'mean_sample_sd_50':'Mean','native_best_of_50':'Native'}.get(row.get('endpoint'),row.get('endpoint','--'))
        pool={'specification_compatible':'Compatible','adapted':'Adapted'}.get(row.get('pool'),row.get('pool','--'))
        counts=str(row.get('historical_complete_configurations','--'))+' / '+str(row.get('historical_complete_canonical_configurations','--'))
        rendered.append([escape(row.get('benchmark','--')),escape(pool),escape(endpoint),escape(counts),escape(row.get('historical_complete_unique_inputs','--')),'Unavailable'])
    output.append(table(['Data','Pool','Endpoint','Complete / canonical configs','Unique inputs','Certified closest'],rendered,'lllp{3.1cm}rl',
                        r'Explicit availability by intended eligible pool and endpoint. Every row has machine status UNAVAILABLE\_NO\_COMPARABLE\_CERTIFIED\_SEARCH\_COVERAGE in certified\_search\_status.csv; no winner is fabricated. Aliases are shown in the complete count and removed in the canonical count.','tab:certified-search-status',long=True))
    return output










def graph_appendix(results,diagnostics,casebooks,coverage,coverage_manifest,gate,*,public=False):
    """Render the fixed G1--G3 evidence without selecting configurations."""
    datasets=['ORL_att92','YaleB_cropped2414'];gammas=[0.,.001,1.,10.,1000.,1000000.]
    labels={'ORL_att92':'ORL','YaleB_cropped2414':'YaleB cropped'}
    def scalar(value):
        try:
            result=float(value)
            return result if math.isfinite(result) else None
        except (TypeError,ValueError):return None
    def percent(value):
        result=scalar(value)
        return number(100*result) if result is not None else '--'
    def flag(value):
        parsed=_usps_bool(value)
        return 'yes' if parsed is True else 'no' if parsed is False else '--'
    def cert(row):
        parsed=_usps_bool(row.get('certified'))
        return 'C' if parsed is True else 'U' if parsed is False else '--'
    def case_dataset(row):
        if row.get('dataset'):return row['dataset']
        for item in coverage:
            if item.get('phase')!='G1':continue
            for saved in unpack_json(item.get('saved_evidence'),[]) or []:
                if saved.get('path')==row.get('record'):return item.get('dataset','unavailable')
        return 'unavailable'
    def index(rows,key):
        output={}
        for row in rows:
            identity=key(row)
            if identity in output:raise ValueError('ambiguous duplicate graph appendix record: '+str(identity))
            output[identity]=row
        return output
    def point_key(row):
        return (row.get('dataset'),row.get('phase'),row.get('anchor','F0') if row.get('phase')=='G2' else 'F0',
            row.get('graph') if row.get('phase')=='G2' else row.get('arm'),scalar(row.get('gamma')),
            None if row.get('phase')=='G2' else scalar(row.get('addition_fraction')))
    points=index([row for row in results if row.get('phase') in ['G2','G3']],point_key)
    covered=index([row for row in coverage if row.get('phase') in ['G2','G3']],point_key)
    graph_stats=index([row for row in diagnostics if row.get('config_id')],lambda row:(row.get('dataset'),row['config_id']))
    def point_view(key):
        row=points.get(key,{});state=covered.get(key,{})
        complete=row.get('status')=='COMPLETED' and str(value(row,'n','n_trials',default=''))=='50'
        complete=complete and all(number(row.get(field))!='--' for field in ['acc_mean','nmi_mean','acc_sd','nmi_sd'])
        if state and _usps_bool(state.get('point_complete')) is False:complete=False
        if public:
            outcome=str(state.get('saved_output_state') or state.get('status') or row.get('status','UNAVAILABLE'))
        else:outcome='saved '+str(state.get('saved_output_state','unavailable'))+'; controller '+str(state.get('controller_status','unavailable')) if state else str(row.get('status','UNAVAILABLE'))
        stats=graph_stats.get((row.get('dataset'),row.get('config_id')), {})
        return row if complete else {},row,stats,break_text(outcome)
    output=[r'\subsection{Fixed-representation graph evidence: G1--G3}' if public else r'\subsection{New fixed-representation graph evidence: G1--G3}',
        r'This section uses the preregistered full ORL and cropped YaleB inputs, independently of retrospective subset winners. No best gamma, budget, graph or seed is selected here. Means and sample SD use the same fifty paired greedy K-means++/Lloyd seeds 0--49. A dash denotes unavailable evidence. C/U records certified/uncertified solver status; certification does not imply accurate clustering. The source files and hashes are listed in the generated report-input manifest.']
    if coverage:
        total=len(coverage);declared=coverage_manifest.get('intended_tasks','unavailable')
        output.append(escape(f'The graph design contains {total} recorded comparisons across G1, G2 and G3. Scientific outcome and numerical qualification remain distinct.' if public else f'Graph coverage snapshot: {total} committed rows; manifest declares {declared} intended tasks. The full design has 362 tasks (2 G1, 48 G2 and 312 G3). Controller execution and saved scientific output are counted separately; a saved point can survive a failed controller.'))
        counts=[]
        for phase in ['G1','G2','G3']:
            rows=[row for row in coverage if row.get('phase')==phase]
            for kind,key in ([('Scientific output','saved_output_state')] if public else [('Controller','controller_status'),('Saved output','saved_output_state')]):
                counts.extend([phase,kind,break_text(state),str(count)] for state,count in sorted(Counter(row.get(key,'UNAVAILABLE') for row in rows).items()))
        output.append(table(['Phase','Observation','State','Tasks'],counts,'p{1cm}p{2cm}p{8cm}p{.8cm}',
            ('Graph-design coverage, including unsuccessful and unevaluated configurations. Shared mathematical problem identities are aliases, not independent measurements.' if public else 'Full intended graph coverage, including failed, pending and unrun tasks. Shared mathematical problem IDs remain aliases rather than independent reruns.'),'tab:graph-design-coverage',long=True))
    else:output.append(r'Graph-design coverage is unavailable; no additional completed comparison is inferred.' if public else r'The committed 362-task graph coverage inventory is unavailable. Missing launch records are not treated as completed experiments.')
    output.append(r'\paragraph{G1: fixed gamma 1 casebooks.} Casebook correctness uses an optimal assignment separately for each partition. Error-rate means below average the fifty paired rounding outcomes; deltas are SSC minus SC. They describe the fixed data and representation, not independent test datasets.')
    errors=[];performance=[];strata=[];examples=[];pollution=[]
    for row in casebooks:
        if not row.get('record'):continue
        dataset=case_dataset(row);label=escape(labels.get(dataset,dataset));seed_count=scalar(row.get('seed_count'))
        known=row.get('status')=='COMPLETED' and seed_count==50
        sc=unpack_json(row.get('sc_summary'),{}) or {};ssc=unpack_json(row.get('ssc_summary'),{}) or {}
        def summary(summary):return summary if known and str(summary.get('n'))=='50' else {}
        performance.append([label,metric(summary(sc),'acc',native=False),metric(summary(ssc),'acc',native=False),
            metric(summary(sc),'nmi',native=False),metric(summary(ssc),'nmi',native=False),
            break_text(row.get('ssc_solver_status') or 'UNAVAILABLE')])
        before=unpack_json(row.get('sc_pair_errors'),[]) or [];after=unpack_json(row.get('ssc_pair_errors'),[]) or []
        for name,key in [('False merge','false_merge_rate'),('False split','false_split_rate')]:
            left=[scalar(item.get(key)) for item in before];right=[scalar(item.get(key)) for item in after]
            valid=known and len(left)==len(right)==50 and all(item is not None and 0<=item<=1 for item in left+right)
            a=sum(left)/50 if valid else None;b=sum(right)/50 if valid else None
            errors.append([label,name,percent(a),percent(b),number(100*(b-a)) if valid else '--','50' if valid else '--'])
        for item in unpack_json(row.get('strata'),[]) or []:
            strata.append([label,break_text(item.get('variable','--')),escape(item.get('quintile','--')),escape(item.get('samples','--')),
                number(item.get('mean_wrong_edge_count')),number(item.get('mean_wrong_edge_mass'),3),
                percent(item.get('sc_correct_ssc_wrong_fraction')),percent(item.get('sc_wrong_ssc_correct_fraction'))])
        ids=unpack_json(row.get('illustration_sample_ids'),{}) or {}
        for name in ['sc_correct_ssc_wrong','sc_wrong_ssc_correct','both_correct','both_wrong']:
            sample=ids.get(name)
            examples.append([label,break_text(name),str(sample) if isinstance(sample,int) and not isinstance(sample,bool) else '--',escape(row.get('illustrations_seed','--'))])
        for role,field in [('A: input-feature geometry','upstream_A_diagnostics'),('W0: spectral geometry','shrinkage_W0_diagnostics')]:
            stats=unpack_json(row.get(field),{}) or {}
            if not stats and field=='shrinkage_W0_diagnostics':stats=unpack_json(row.get('graph_diagnostics'),{}) or {}
            pollution.append([label,escape(role),significant(stats.get('edges'),6),percent(stats.get('cross_class_edge_fraction')),
                percent(stats.get('cross_class_mass_fraction')),significant(stats.get('within_class_excess_fragments'),6)])
    if errors:
        output.extend([table(['Data','SC ACC','SSC ACC','SC NMI','SSC NMI','SSC solver'],performance,'p{1.2cm}p{1.6cm}p{1.6cm}p{1.6cm}p{1.6cm}p{4cm}',
            'Matched G1 means and sample SD at fixed gamma 1; these are not selected gamma-path maxima.','tab:graph-g1-performance',long=True),
            table(['Data','Pair error','SC (\\%)','SSC (\\%)','Delta (pp)','Pairs of rounds'],errors,'llrrrr',
                'False merges and splits use contingency-count definitions. The averaging unit is a paired rounding seed, not a sample pair treated as an independent replicate.','tab:graph-g1-pair-errors',long=True),
            table(['Data','Graph / length space','Edges','Cross edges (\\%)','Cross mass (\\%)','Excess fragments'],pollution,'p{1.2cm}p{3.5cm}p{.8cm}p{1.8cm}p{1.8cm}p{2cm}',
                'Upstream A and shrinkage W0 contamination remain distinct. An unavailable A field is not replaced with W0 evidence. Fragmentation is class-induced and includes isolates.','tab:graph-g1-contamination',long=True),
            table(['Data','Variable','Bin','n','Wrong degree','Wrong mass','SC right/SSC wrong (\\%)','SC wrong/SSC right (\\%)'],strata or [['--']*8],'p{1cm}p{1.4cm}p{.8cm}p{.7cm}p{1.2cm}p{1.2cm}p{2cm}p{2cm}',
                'Predefined row-norm and weighted-degree quintiles, with original cut points and tie handling. Fractions pool the recorded sample-by-round outcomes within each fixed stratum.','tab:graph-g1-strata',long=True),
            table(['Data','Seed-zero category','Original row ID','Seed'],examples,'lp{5.5cm}rr',
                'Deterministic first original row in each fixed seed-zero correctness category. Missing categories stay unavailable; no private image is embedded.','tab:graph-g1-examples',long=True)])
    else:output.append(r'No committed G1 casebook is available. Pair errors, strata, contamination and illustrative sample IDs are not inferred from G2/G3 execution.')
    g2=[]
    for dataset in datasets:
        for anchor in ['F0','U']:
            for graph in ['W0','Wa']:
                for gamma in gammas:
                    means,row,stats,outcome=point_view((dataset,'G2',anchor,graph,gamma,None))
                    g2.append([escape(labels[dataset]),anchor,graph,significant(gamma,4),metric(means,'acc',native=False),metric(means,'nmi',native=False),
                        cert(row),significant(row.get('normalized_L21_movement'),3),outcome])
    output.append(r'\paragraph{G2: all 48 fixed cells.} F0 is the saved raw spectral anchor; U is its row-normalized version. W0 and Wa are constructed in those respective geometries. Every graph is mass-matched to W0; equal mass does not equalize node forces or movement. Gamma zero is the anchor-only SC endpoint. Cached gamma-zero graph-arm rows are declared aliases, not independent fits.')
    output.append(table(['Data','$H$','$W$',r'$\gamma$','ACC','NMI','C/U','L21 move','Scientific outcome' if public else 'Saved / controller outcome'],g2,'p{1.4cm}p{.6cm}p{.6cm}p{1.1cm}p{1.7cm}p{1.7cm}p{.55cm}p{.9cm}p{2.6cm}',
        'Complete fixed G2 path, including unavailable/failed cells. Movement is sum of row displacements divided by sum of anchor row norms; it is not Frobenius movement.','tab:graph-g2-all-cells',long=True))
    output.append(r'\paragraph{G3: fixed primary budget and gamma.} The following rows use only the 15\% addition budget and effective E8 gamma 1000. Additions come from the already frozen label-blind pool, with at most two newly incident edges per node and median positive W0 edge weight before mass matching. Oracle additions join same-class components after cross-class deletion and are reused unchanged in add-only and both arms. Other gammas and the 5\% budget remain sensitivity records in the full CSVs, not alternative promotion gates.')
    arms=[('none','No edits'),('delete','Oracle delete'),('add','Oracle add'),('both','Oracle delete+completion')]
    arms += [(f'blind_{seed}',f'Fixed delete + blind add {seed}') for seed in [400,401,402]]
    arms += [(f'same_class_random_{seed}',f'Fixed delete + same-class random {seed}') for seed in [400,401,402]]
    arms += [(f'fully_random_{seed}',f'Fully random delete/add {seed}') for seed in [400,401,402]]
    g3=[];conditions=[];contrasts=[]
    for dataset in datasets:
        for arm,label in arms:
            means,row,stats,outcome=point_view((dataset,'G3','F0',arm,1000.,.15))
            g3.append([escape(labels[dataset]),escape(label),metric(means,'acc',native=False),metric(means,'nmi',native=False),cert(row),
                significant(row.get('normalized_L21_movement'),3),significant(stats.get('within_class_excess_fragments'),6),outcome])
        decision=gate.get('datasets',{}).get(dataset,{})
        checks=decision.get('conditions',{}) or {};values=decision.get('contrasts',{}) or {}
        definitions=[('certified_involved_solutions','Delete and both certified','gap <= 1e-5; capacities <= 1e-8'),
            ('active_delete_and_both','Delete and both active','normalized L21 > 1e-6'),
            ('ACC_gain_at_least_1pp','Both minus delete ACC','mean gain >= 1 pp'),('NMI_not_decreased','Both minus delete NMI','mean gain >= 0 pp'),
            ('excess_fragments_reduced_at_least_20pct','Class-induced excess fragments','reduction >= 20 percent'),
            ('ACC_CI_positive_vs_delete','ACC CI versus delete','lower endpoint > 0 pp'),
            ('ACC_CI_positive_vs_mean_blind','ACC CI versus mean blind additions','lower endpoint > 0 pp')]
        for key,label,threshold in definitions:
            conditions.append([escape(labels[dataset]),escape(label),escape(threshold),flag(checks.get(key)),break_text(decision.get('decision','UNAVAILABLE'))])
        reduction=scalar(decision.get('excess_fragment_reduction_fraction'))
        conditions.append([escape(labels[dataset]),'Recorded excess-fragment reduction',percent(reduction)+' percent' if reduction is not None else '--','--',break_text(decision.get('decision','UNAVAILABLE'))])
        for stem,label in [('both_minus_delete','Both minus delete'),('both_minus_blind_mean','Both minus fixed-delete / blind-add mean'),
            ('both_minus_same_class_random_mean','Both minus fixed-delete / same-class-random mean'),('both_minus_fully_random_mean','Both minus fully random edits mean')]:
            for metric_name in ['acc','nmi']:
                recorded=values.get(stem+'_'+metric_name,{})
                contrasts.append([escape(labels[dataset]),escape(label),metric_name.upper(),number(recorded.get('delta_pp')),
                    number(recorded.get('ci_lower_pp')),number(recorded.get('ci_upper_pp'))])
    output.extend([table(['Data','Arm / control','ACC','NMI','C/U','L21 move','Excess fragments','Outcome'],g3,'p{1.1cm}p{2.8cm}p{1.6cm}p{1.6cm}p{.5cm}p{.85cm}p{1.3cm}p{2.3cm}',
        'Fixed primary G3 arms. Blind controls retain exactly the Oracle deletion mask and randomize only additions. Same-class random additions do not prefer separate components. Fully randomized deletion/addition is a separate supplementary control. Infeasible or unrun controls retain their status.','tab:graph-g3-primary',long=True),
        table(['Data','Locked gate condition','Threshold','Satisfied','Decision'],conditions,'p{1.2cm}p{3.8cm}p{3.8cm}p{1.4cm}p{2.2cm}',
            'Preregistered promotion checks. Certification and activity are required for delete and both; blind-control certificate flags remain visible but are not an additional hidden pass condition. At least one development dataset must pass.','tab:graph-g3-gate',long=True),
        table(['Data','Fixed contrast','Metric','Mean delta (pp)',r'95\% lower',r'95\% upper'],contrasts,'p{1.2cm}p{4.5cm}p{.8cm}p{1.8cm}p{1.8cm}p{1.8cm}',
            'Stored paired percentile intervals: 10,000 resamples, bootstrap seed 424242. The three random-control outcomes are averaged within each rounding seed before the contrast. Only ACC intervals versus deletion and the mean blind control enter the gate; supplementary controls and NMI intervals are reported without redefining it.','tab:graph-g3-contrasts',long=True)])
    return output


def generate(root: Path,date: str='2026-11-10'):
    root=root.resolve();refresh=root/'results/submission_refresh';refresh.mkdir(parents=True,exist_ok=True);subset=root/'results/subset_search';out=root/'report/tables';out.mkdir(parents=True,exist_ok=True)
    presentation_inputs=public_presentation_inputs(root)
    public=bool(presentation_inputs)
    names={'historical':refresh/'joint_metric_selection.csv','historical_endpoints':refresh/'endpoint_comparison.csv',
           'historical_all_joint':refresh/'all_joint_configurations.csv','historical_all_native':refresh/'all_native_endpoints.csv',
           'paper':refresh/'paper_reference_verification.json','catalogue':subset/'candidate_catalogue.json',
           'coverage':subset/'coverage_summary.json','execution':(subset/'execution_coverage.public.v1.csv' if (subset/'execution_coverage.public.v1.csv').exists() else subset/'execution_coverage.csv'),
           'joint':subset/'joint_search_summary.csv','native':subset/'native_best_summary.csv','fixed':subset/'fixed_protocol_summary.csv',
           'closest':subset/'closest_matches.csv','confirmation':subset/'rounding_confirmation.csv',
           'baseline':refresh/'baseline_diagnostics.csv','extension':refresh/'extension_results.csv',
           'graph_diagnostics':refresh/'graph_diagnostics.csv','casebooks':refresh/'casebook_summary.csv',
           'graph_execution':refresh/'graph_execution_coverage.csv','graph_coverage_manifest':refresh/'graph_coverage_manifest.json',
           'graph_protocol':root/('configs/submission_refresh/graph_design.public.v1.json' if public else 'configs/submission_refresh/extension_protocol.yaml'),
           'gate':refresh/'extension_gate.json','resource':refresh/'resource_usage.json','cohort':root/'configs/subset_search/executable_cohort.json',
           'repeatability':refresh/'historical_repeatability_summary.csv','repeatability_manifest':refresh/'historical_repeatability_manifest.json',
           'usps_solver_evaluation':refresh/'usps_solver_evaluation.csv',
           'usps_continuation_audit':refresh/'usps_continuation_audit.csv',
           'usps_continuation_evaluation':refresh/'usps_continuation_evaluation.csv',
           'usps_numerical_reference_input_identity':refresh/'usps_numerical_reference_input_identity.json',
           'certified_search_status':subset/'certified_search_status.csv'}
    names.update(presentation_inputs)
    logical_names=dict(names)
    for key,path in names.items():
        if path.suffix=='.csv':names[key]=resolve_csv(path) or path
    def input_record(key,path):
        record={'path':str(path.relative_to(root)),'logical_path':str(logical_names[key].relative_to(root)),
                'available':path.exists(),'sha256':None}
        if record['available']:
            with path.open('rb') as stream:record['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        if logical_names[key].suffix=='.csv':record['transport']=('gzip' if path.suffix=='.gz' else 'plain') if record['available'] else None
        return record
    inputs={key:input_record(key,path) for key,path in names.items()}
    historical=read_csv(names['historical']);hist_endpoints=read_csv(names['historical_endpoints'])
    papers=paper_lookup(read_json(names['paper'],{}));cat=read_json(names['catalogue'],{}).get('candidates',[])
    coverage=read_json(names['coverage'],{});cohort=read_json(names['cohort'],{});joint=read_csv(names['joint']);closest=read_csv(names['closest'])
    baseline=read_csv(names['baseline']);extension=read_csv(names['extension']);gate=read_json(names['gate'],{})
    confirmations=read_csv(names['confirmation']);resources=read_json(names['resource'],{})
    def write(name,text):
        (out/(name+'.tex')).write_text('% Generated from authoritative CSV/JSON records; do not edit.\n'+text)
    selected={r['benchmark']:r for r in historical if r.get('method')=='ssc' and r.get('endpoint')=='mean_sample_sd_50' and number(r.get('acc_mean'))!='--'}
    new_mean=[r for r in closest if r.get('endpoint')=='mean_sample_sd_50']
    main_rows=[]
    for benchmark in (BENCHMARKS if new_mean else ['ORL','JAFFE','YaleB','USPS']):
        if new_mean:
            compatible=next((r for r in new_mean if r['benchmark']==benchmark and r.get('pool')=='specification_compatible'),None)
            row=compatible or next((r for r in new_mean if r['benchmark']==benchmark and r.get('pool')=='adapted'),{})
            row={**papers.get((benchmark,'ssc'),{}),**row}
            label=benchmark+(r'$^\dagger$' if row.get('pool')=='adapted' else '')
        else:
            row=selected.get(benchmark,{**papers.get((benchmark,'ssc'),{}),'benchmark':benchmark});label=benchmark
        main_rows.append([label,metric(row,'acc',paper=True),metric(row,'acc'),metric(row,'nmi',paper=True),metric(row,'nmi'),number(row.get('D_max')),status_abbreviation(row)])
    if new_mean:
        maincaption=(r'Closest evaluated SSC reconstructions under joint $D_{\max}$/$D_{\rm mean}$ matching. This is retrospective numerical selection using labels and paper targets; historical subset identity remains unverified. '
                     r'Means $\pm$ sample SD use one configuration and all 50 seeds. Compatible-pool winners are shown where available; $\dagger$ marks a separately selected adaptation. '
                     r'I: iterate stopping without a gap certificate; T: iteration cap; U: other uncertified state. Exact candidate IDs, counts, signed differences, settings and both pools appear in the appendix. Historical selections are retained separately.')
    else:
        maincaption=(r'Historical SSC scalar records, reselected jointly by $D_{\max}$ then $D_{\rm mean}$; this is a retrospective match, not label-free selection. Means $\pm$ sample SD use one configuration and all 50 seeds. '
                     r'I: iterate stopping without a gap certificate; T: iteration cap. None of these historical $G$ arrays is recoverable, so current solver audits cannot certify their exact outputs. Settings and source versions appear in the appendix.')
    write('refresh_main',table(['Data','Paper ACC','Our ACC','Paper NMI','Our NMI',r'$D_{\max}$','Fit'],main_rows,'lrrrrrc',maincaption,'tab:refresh-main'))
    if names['coverage'].exists():
        coverage_text=(f"The new campaign obtained complete configurations on {coverage.get('complete_unique_candidates','NA')} unique inputs, yielding {coverage.get('complete_unique_configurations','NA')} SSC input/configuration pairs from {coverage.get('intended_candidates',len(cat))} intended catalogue entries. "
                       f"Of these, {coverage.get('inputs_with_complete_30point_ssc_grid','NA')} inputs completed all 30 SSC configurations; {coverage.get('inputs_with_complete_30point_ssc_and_3matched_sc_grid','NA')} inputs completed the full 30-SSC plus three matched-SC design. "
                       f"Aliases remain separate provenance entries; diagnostic parents do not enter the paper-compatible pool. "
                       f"All failed, timed-out and unrun combinations remain in the coverage matrix. ")
    else:
        coverage_text=f"The frozen catalogue contains {len(cat)} intended entries. New execution coverage has not yet been aggregated; current new-campaign counts and selected scores are unavailable. "
    if cohort.get('candidate_ids'):
        coverage_text+=f"The label-blind executable cohort freezes {len(cohort['candidate_ids'])} entries before scoring. "
    coverage_text+=r'The search distribution and locked-winner confirmation are reported separately in the appendix; a larger search may improve numerical matching without resolving historical identity.'
    if public:
        if names['coverage'].exists():
            coverage_text=(f"The evaluated design obtained complete SSC configurations on {coverage.get('complete_unique_candidates','NA')} unique inputs, yielding {coverage.get('complete_unique_configurations','NA')} input/configuration pairs. "
                           f"Of these, {coverage.get('inputs_with_complete_30point_ssc_grid','NA')} inputs completed all 30 SSC settings and {coverage.get('inputs_with_complete_30point_ssc_and_3matched_sc_grid','NA')} completed the 30-SSC plus three matched-SC design. ")
        else:coverage_text='Evaluated source/subset coverage and selected scores are unavailable. '
        coverage_text+='Aliases are provenance entries, and diagnostic parents are excluded from equivalent paper reconstruction. Additional rounding on locked selections measures conditional stability; closer numerical matching does not identify historical data.'
    write('refresh_coverage',r'\noindent '+escape(coverage_text)+'\n')
    complete=[r for r in baseline if r.get('status')=='COMPLETED' and str(r.get('n_trials','50'))=='50' and number(r.get('acc_mean'))!='--']
    if names['baseline'].exists():
        slps=sum(r.get('method')=='spls' for r in complete);lda=sum(r.get('method','').startswith('lda') for r in complete)
        other=len(complete)-slps-lda
        repairs_text=f"The refresh has {slps} complete 50-seed SLPS configurations, {lda} complete 50-seed LDA configurations/control endpoints, and {other} other baseline configurations. Failed/incomplete endpoints remain visible; the appendix reports means/SD and LDA update/termination diagnostics. "
        if not complete:repairs_text+='No new baseline endpoint currently qualifies as a complete measured result. '
    else:repairs_text='The repaired baseline implementations are available; new baseline result aggregation is pending. No additional benchmark result is inferred from implementation tests. '
    repairs_text+='Native 16-by16 MSRA and adapted LDA-to-SC remain separately named adaptations; exact historical LDA-SC remains unavailable.'
    if public:
        repairs_text=(f"The baseline comparison contains {slps} complete 50-seed SLPS configurations, {lda} LDA configurations/control endpoints and {other} other configurations. " if names['baseline'].exists() else 'Baseline measurements are unavailable. ')
        repairs_text+='The appendix retains numerical failures, iteration-limit outcomes and update diagnostics. Native 16-by-16 MSRA and ridge LDA-to-SC are explicitly named adaptations; exact historical LDA-SC remains unresolved.'
    write('refresh_repairs',r'\noindent '+escape(repairs_text)+'\n')
    decision=gate.get('decision','UNAVAILABLE')
    ext_text=f"The fixed oracle graph-intervention criterion is {decision.lower().replace('_',' ')}. Label-assisted graph diagnostics and unsupervised refinement gains are distinct conclusions. The earlier wrong-edge diagnostic remains a separate historical result."

    appendix=[r'\subsection{Jointly reselected historical mean endpoint}',
              (r'Table~\ref{tab:historical-joint} reports the complete 72-cell inventory. ' if len(historical)==72 else f'Historical inventory aggregation currently has {len(historical)} rows; the required72-cell inventory is incomplete. ')+r'Values are percent. Every measured pair uses the same configuration and 50 batch-zero seeds; $\pm$ denotes sample SD. Missing cells retain their identity or method restriction. Historical scalar evidence is separate from new recoverable artifacts. The former ACC-only and fixed-reference tables remain in the committed historical release.']
    hist_rows=[]
    for row in historical:
        benchmark=row.get('benchmark','--');method=row.get('method','--');paper=papers.get((benchmark,method),{})
        row={**paper,**{k:v for k,v in row.items() if v not in [None,'']}}
        label=METHODS.get(method,escape(method));measured=number(row.get('acc_mean'))!='--'
        hist_rows.append([escape(benchmark),label,metric(row,'acc',paper=True),metric(row,'acc'),metric(row,'nmi',paper=True),metric(row,'nmi'),number(row.get('D_max'))])
        if measured:
            source=escape(value(row,'dataset_version','dataset_id',default='unspecified'))
            setting=short_setting(row);solver=escape(value(row,'solver_status_current_audit','solver_status_original',default='not applicable'))
            detail=source+'; '+setting+'; '+solver+r'; $D_{\rm mean}='+number(row.get('D_mean'))+'$.'
        else:detail=escape(value(row,'reason','status',default='Unavailable; no complete eligible configuration'))
        hist_rows.append(r'\multicolumn{7}{p{\dimexpr\textwidth-6pt\relax}}{\scriptsize '+detail+r'} \\')
    if not hist_rows:hist_rows=[['--']*7]
    appendix.append(table(['Data','Method','Paper ACC','Our ACC','Paper NMI','Our NMI',r'$D_{\max}$'],hist_rows,'llrrrrr',
                           'Joint closest historical mean/sample-SD endpoint; unavailable cells are not filled with adapted measurements.','tab:historical-joint',long=True))
    appendix += [r'\subsection{Native-objective-selected endpoint}',
                 r'Within one fixed G, native K-means SSE selects one of 50 assignments. This is a single assignment with no across-run SD. It does not compete with the mean endpoint. Full method-specific endpoint records are in \texttt{results/submission\_refresh/endpoint\_comparison.csv}; LDA cross-subspace native selection is unavailable.']
    native_rows=[]
    for benchmark in BENCHMARKS:
        row=next((r for r in hist_endpoints if r.get('benchmark')==benchmark and r.get('method')=='ssc' and r.get('endpoint')=='native_best_of_50'),{})
        native_rows.append([benchmark,metric(row,'acc',native=True),metric(row,'nmi',native=True),number(row.get('D_max')),number(row.get('D_mean')),escape(value(row,'selected_seed',default='--')),status_abbreviation(row)])
    appendix.append(table(['SSC data','ACC','NMI',r'$D_{\max}$',r'$D_{\rm mean}$','Seed','Fit'],native_rows,'lrrrrrc',long=True))
    appendix += [r'\subsection{Separate historical repeatability batches}',
                 r'Existing multi-batch records are a separate endpoint. Each batch contains 50 disjoint rounding seeds on its fixed input. The following ranges describe variation of batch means and native-selected assignments, without treating a single native assignment as having a within-batch SD. They are not independent datasets, and are not new campaign measurements. All methods and exact configuration IDs are preserved in \texttt{historical\_repeatability\_batches.csv} and its summary/manifest. LDA source-native selection remains diagnostic only.']
    repeatability=read_csv(names['repeatability'])
    repeat_rows=[]
    for row in repeatability:
        if row.get('method')!='ssc':continue
        parts=row['config_id'].split('|');setting=parts[0]+' / '+parts[3]+' / '+parts[4]+' / '+{'RANDOM':'R','SKLEARN_GREEDY_KMEANSPP':'G'}.get(parts[-2],parts[-2])
        ranges=[number(row.get(field+'_min'))+'--'+number(row.get(field+'_max')) for field in ['ACC','NMI','selected_ACC','selected_NMI']]
        repeat_rows.append([break_text(setting),escape(row.get('batches','--')),*ranges])
    if repeat_rows:appendix.append(table(['SSC setting','Batches','Batch ACC','Batch NMI','Native ACC','Native NMI'],repeat_rows,'p{4.0cm}rrrrr',long=True))
    else:appendix.append(r'Multi-batch repeatability evidence is unavailable.' if public else r'No validated multi-batch summary is currently available; no repeatability result is inferred.')
    appendix += [r'\subsection{Dataset-subset matching: both endpoints and eligibility pools}',
                 r'The following rows use complete evaluated configurations only. Paper values are fixed SSC targets. R/V/G denote random, vanilla K-means++ and sklearn greedy K-means++; each is one Lloyd start. Specification-compatible dimensions/counts do not establish historical pixel identity. Adapted rows retain explicit source/resolution/preparation differences. Diagnostic parents cannot win either pool.']
    for endpoint in ENDPOINTS:
        heading='Mean/sample-SD over 50 fixed-G roundings' if endpoint=='mean_sample_sd_50' else 'Single native-best assignment among 50 fixed-G roundings'
        appendix.append(r'\paragraph{'+heading+'}')
        rows=[]
        for benchmark in BENCHMARKS:
            groups=[r for r in closest if r.get('benchmark')==benchmark and r.get('endpoint')==endpoint]
            if not groups:
                groups=[{'benchmark':benchmark,'pool':'no complete eligible result'}]
            for row in groups:
                row={**papers.get((benchmark,'ssc'),{}),**row}
                rows.append([benchmark+' / '+escape(row.get('pool','--')).replace(r'specification\_compatible','compatible'),
                             r'\scriptsize '+break_text(row.get('candidate_id','Unavailable')),
                             metric(row,'acc',paper=True),metric(row,'acc'),metric(row,'nmi',paper=True),metric(row,'nmi'),number(row.get('D_max'))])
                if row.get('candidate_id'):
                    delta_acc=value(row,'acc_delta_pp','delta_acc_pp');delta_nmi=value(row,'nmi_delta_pp','delta_nmi_pp')
                    if delta_acc is None and number(row.get('acc_mean'))!='--':delta_acc=float(row['acc_mean'])-float(row['paper_acc'])
                    if delta_nmi is None and number(row.get('nmi_mean'))!='--':delta_nmi=float(row['nmi_mean'])-float(row['paper_nmi'])
                    detail=(r'$n='+escape(row.get('n_samples','--'))+'$; '+short_setting(row)+'; '+escape(row.get('solver_status','--'))+
                            r'; $\Delta_{\rm ACC}='+number(delta_acc)+r'$ pp; $\Delta_{\rm NMI}='+number(delta_nmi)+r'$ pp; $D_{\rm mean}='+number(row.get('D_mean'))+'$; '+escape(row.get('historical_identity','historical identity unverified'))+'.')
                    if endpoint=='mean_sample_sd_50':
                        detail+=r' $\Delta_{\rm SD,ACC}='+number(row.get('delta_acc_sd_pp'))+r'$ pp; $\Delta_{\rm SD,NMI}='+number(row.get('delta_nmi_sd_pp'))+'$ pp.'
                    rows.append(r'\multicolumn{7}{p{\dimexpr\textwidth-6pt\relax}}{\scriptsize '+detail+r'} \\')
        appendix.append(table(['Data / pool','Selected candidate','Paper ACC','Our ACC','Paper NMI','Our NMI',r'$D_{\max}$'],rows,'p{1.6cm}p{3.3cm}rrrrr',long=True))
    appendix += certified_search_appendix(read_csv(names['certified_search_status']),public=public)
    appendix.append(r'\subsection{Additional rounding on locked winners}')
    if confirmations:
        rows=[]
        for row in confirmations:
            conf=unpack_json(row.get('confirmation'),{}) or {}
            rows.append([escape(row.get('benchmark','--')),escape(row.get('endpoint','--')).replace(r'mean\_sample\_sd\_50','mean').replace(r'native\_best\_of\_50','native'),
                         number(row.get('selection_acc')),number(row.get('selection_nmi')),metric({**conf,'endpoint':row.get('endpoint')},'acc'),metric({**conf,'endpoint':row.get('endpoint')},'nmi'),escape(row.get('status','--'))])
        appendix.append(table(['Data','Endpoint','Select ACC','Select NMI','Confirm ACC','Confirm NMI','Status'],rows,'llrrrrl',long=True))
        appendix.append(r'Additional seeds check rounding on the same samples and saved G. Winners are not reselected. These intervals/SD do not establish historical identity, unseen-data generalization or label-free model selection.')
    else:appendix.append(r'Additional-rounding evidence is unavailable; no stability result is inferred.' if public else r'No completed additional-rounding record is currently aggregated. Winners, if available, remain locked; no stability result is inferred.')
    appendix.append(r'\subsection{Baseline comparisons}' if public else r'\subsection{Complete baseline repair endpoints}')
    if baseline and any(r.get('method') for r in baseline):
        rows=[]
        for row in baseline:
            if not row.get('method'):continue
            name=METHODS.get(row.get('method'),escape(row.get('method')))
            setting='limit '+str(row['max_iter']) if row.get('max_iter') else str(row.get('config_id','')).split('|')[-1].replace('spls__','')
            rows.append([break_text(row.get('dataset','--')).replace(r'MSRA25\_EBSA\_16x16','MSRA16'),name,break_text(setting),metric(row,'acc'),metric(row,'nmi'),break_text(row.get('status','--'))])
            if row.get('termination_counts'):
                stops=row['termination_counts']
                if public:
                    counts=unpack_json(stops,{})
                    if isinstance(counts,dict):stops=', '.join(str(key).replace('_',' ')+' ('+str(count)+')' for key,count in sorted(counts.items()))
                diagnostics=f"Stops: {stops}; failed updates: {row.get('update_failures_total','--')}; zero-success runs: {row.get('no_successful_lda_update_runs','--')}."
                rows.append(r'\multicolumn{6}{p{\dimexpr\textwidth-6pt\relax}}{\scriptsize '+escape(diagnostics)+r'} \\')
        appendix.append(table(['Data','Method','Setting','ACC','NMI','Status'],rows,'p{2.0cm}p{2.1cm}p{2.1cm}rrp{1.7cm}',long=True))
    else:appendix.append(r'No complete baseline endpoint is available.' if public else r'Baseline result aggregation is pending or contains no complete endpoint. Implementation tests do not establish benchmark performance.')
    appendix += usps_numerical_appendix(read_csv(names['usps_solver_evaluation']),read_csv(names['usps_continuation_audit']),read_csv(names['usps_continuation_evaluation']),read_json(names['usps_numerical_reference_input_identity'],{}),public=public)
    appendix += graph_appendix(extension,read_csv(names['graph_diagnostics']),read_csv(names['casebooks']),
        read_csv(names['graph_execution']),read_json(names['graph_coverage_manifest'],{}),gate,public=public)
    appendix.append(r'\subsection{Coverage, solver qualification and cost}')
    if names['coverage'].exists():
        appendix.append(escape(f"Complete-config input coverage means at least one completed SSC configuration on an input, not a finished search design. {coverage.get('complete_unique_candidates','NA')} unique inputs yielded {coverage.get('complete_unique_configurations','NA')} complete SSC input/configuration pairs; {coverage.get('inputs_with_complete_30point_ssc_grid','NA')} inputs completed all 30 SSC points and {coverage.get('inputs_with_complete_30point_ssc_and_3matched_sc_grid','NA')} completed all 30 SSC plus three matched-SC points."))
    if cat:
        summary_rows=[]
        for benchmark in BENCHMARKS:
            intended=[r for r in cat if r.get('benchmark')==benchmark]
            measured=[r for r in joint if r.get('benchmark')==benchmark]
            unique={r.get('alias_of') or r.get('candidate_id') for r in measured}
            summary_rows.append([benchmark,str(len(intended)),str(len({r.get('alias_of') or r['candidate_id'] for r in intended})),str(len(unique)) if names['joint'].exists() else 'NA',str(len(measured)) if names['joint'].exists() else 'NA'])
        appendix.append(table(['Data','Intended aliases','Unique inputs','Measured inputs','Complete configurations'],summary_rows,'lrrrr',long=True))
    if coverage.get('status_counts'):
        appendix.append(table(['Execution status','Intended combinations'],
            [[break_text(status),str(count)] for status,count in sorted(coverage['status_counts'].items())],
            'p{9cm}r',long=True))
    if public and resources:
        hours=resources.get('total_cpu_core_hours')
        if hours is None and resources.get('total_cpu_seconds') is not None:hours=float(resources['total_cpu_seconds'])/3600
        workers=resources.get('max_workers','--');rss=resources.get('rss_target_bytes')
        rss_text=number(float(rss)/(1024**3),1)+' GiB' if rss is not None else 'unavailable'
        appendix.append(escape(f"The recorded charge for retained historical study phases and shared overhead is {number(hours,4)} CPU-core hours, including conservative accounting caps for metadata operations. Experiments used at most {workers} single-thread workers and an aggregate RSS target of {rss_text}. Per-fit measured costs and numerical qualifications are reported separately from clustering performance."))
        costs=resources.get('phase_cpu_seconds',{})
        if costs:appendix.append(table(['Experiment group','CPU seconds'],[[break_text(phase),number(seconds,1)] for phase,seconds in sorted(costs.items())],'lr',long=True))
    elif resources:
        ledger=resources.get('ledger',resources)
        entries=ledger.get('entries',[]);charged=sum(float(r.get('charged_cpu_seconds',0)) for r in entries)/3600
        appendix.append(escape(f"Shared ledger charged {charged:.4f} CPU-core hours as of this aggregation. Limit 36, with 2 reserved for final checks; at most 2 single-thread workers and 8 GiB aggregate RSS target. Active reservations: {len(ledger.get('active',{}))}. This is a snapshot, not a prediction of final resource use."))
    else:appendix.append(r'Computational cost is unavailable.' if public else r'Resource aggregation is not yet available.')
    if gate:appendix.append(r'\paragraph{Graph criterion.} '+escape(f"Oracle intervention criterion: {gate.get('decision','unavailable')}. This is a label-assisted diagnostic on fixed development inputs."))
    plotted=figure(root,joint,papers,closest,cat)
    if plotted:appendix += [r'\begin{figure}[p]\centering\includegraphics[width=\linewidth,height=.86\textheight,keepaspectratio]{figures/subset_acc_nmi.pdf}',
        r'\caption{SSC search distribution for the mean/sample-SD endpoint. Points are complete candidate/configuration records; colors distinguish source/subset families (YaleB colors separate source/resize versions), triangles are adapted rows, crosses are diagnostic rows, stars are published SSC targets and outlines mark the already locked selections within each eligible pool. Eligibility pools and actual locked selections are reported in the tables. More candidates can improve a retrospective match without identifying historical data.}\label{fig:subset-distribution}\end{figure}']
    appendix += [r'\paragraph{Generated-input provenance.} Tables and figures are generated from the authoritative committed CSV/JSON records only. The input hash manifest is \texttt{results/submission\_refresh/report\_input\_manifest.json}. Generated snapshot date: '+escape(date)+'.']
    write('refresh_appendix','\n\n'.join(appendix)+'\n')
    manifest={'schema':'report-inputs-v1','date':date,'inputs':inputs,'outputs':[str(p.relative_to(root)) for p in sorted(out.glob('refresh_*.tex'))],
              'statistical_endpoints_separate':True,'missing_values_are_not_zero':True,'no_score_selection_in_generator':True}
    if public:manifest['presentation']='public-scientific'
    (refresh/'report_input_manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--date',default='2026-11-10',help='Controlled report snapshot date; no wall-clock inference')
    args=parser.parse_args();generate(args.root,args.date)


if __name__=='__main__':main()
