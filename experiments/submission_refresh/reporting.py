"""Build report inputs from committed authoritative CSV/JSON records only.

No fitting, label inspection, selection, or external artifact lookup occurs here.
Missing aggregation is printed explicitly; unavailable values never become zeros.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

BENCHMARKS=['AR','JAFFE','ORL','UMIST','BinAlpha','MSRA50','YaleB','USPS']
ENDPOINTS=['mean_sample_sd_50','native_best_of_50']
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
    if not path.exists():return []
    with path.open(newline='') as f:return list(csv.DictReader(f))


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


def generate(root: Path,date: str='2026-11-10'):
    root=root.resolve();refresh=root/'results/submission_refresh';refresh.mkdir(parents=True,exist_ok=True);subset=root/'results/subset_search';out=root/'report/tables';out.mkdir(parents=True,exist_ok=True)
    names={'historical':refresh/'joint_metric_selection.csv','historical_endpoints':refresh/'endpoint_comparison.csv',
           'paper':refresh/'paper_reference_verification.json','catalogue':subset/'candidate_catalogue.json',
           'coverage':subset/'coverage_summary.json','execution':subset/'execution_coverage.csv',
           'joint':subset/'joint_search_summary.csv','fixed':subset/'fixed_protocol_summary.csv',
           'closest':subset/'closest_matches.csv','confirmation':subset/'rounding_confirmation.csv',
           'baseline':refresh/'baseline_diagnostics.csv','extension':refresh/'extension_results.csv',
           'gate':refresh/'extension_gate.json','resource':refresh/'resource_usage.json','cohort':root/'configs/subset_search/executable_cohort.json'}
    inputs={k:{'path':str(p.relative_to(root)),'available':p.exists(),
               'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None} for k,p in names.items()}
    historical=read_csv(names['historical']);hist_endpoints=read_csv(names['historical_endpoints'])
    papers=paper_lookup(read_json(names['paper'],{}));cat=read_json(names['catalogue'],{}).get('candidates',[])
    coverage=read_json(names['coverage'],{});cohort=read_json(names['cohort'],{});joint=read_csv(names['joint']);closest=read_csv(names['closest'])
    baseline=read_csv(names['baseline']);extension=read_csv(names['extension']);gate=read_json(names['gate'],{})
    confirmations=read_csv(names['confirmation']);resources=read_json(names['resource'],{})
    def write(name,text):
        (out/(name+'.tex')).write_text('% Generated from authoritative CSV/JSON records; do not edit.\n'+text)
    selected={r['benchmark']:r for r in historical if r.get('method')=='ssc' and r.get('endpoint')=='mean_sample_sd_50' and number(r.get('acc_mean'))!='--'}
    main_rows=[]
    for benchmark in ['ORL','JAFFE','YaleB','USPS']:
        row=selected.get(benchmark,{**papers.get((benchmark,'ssc'),{}),'benchmark':benchmark})
        main_rows.append([benchmark,metric(row,'acc',paper=True),metric(row,'nmi',paper=True),metric(row,'acc'),metric(row,'nmi'),number(row.get('D_max')),status_abbreviation(row)])
    maincaption=(r'Historical SSC scalar records, reselected jointly by $D_{\max}$ then $D_{\rm mean}$; this is a retrospective match, not label-free selection. Means $\pm$ sample SD use one configuration and all 50 seeds. '
                 r'I: iterate stopping without a gap certificate; T: iteration cap. None of these historical $G$ arrays is recoverable, so current solver audits cannot certify their exact outputs. Settings and source versions appear in the appendix.')
    write('refresh_main',table(['Data','Paper ACC','Paper NMI','Our ACC','Our NMI',r'$D_{\max}$','Fit'],main_rows,'lrrrrrc',maincaption,'tab:refresh-main'))
    if names['coverage'].exists():
        coverage_text=(f"The new campaign completed {coverage.get('complete_unique_candidates','NA')} unique candidates and {coverage.get('complete_unique_configurations','NA')} candidate/configuration pairs from {coverage.get('intended_candidates',len(cat))} intended catalogue entries. "
                       f"Aliases remain separate provenance entries; diagnostic parents do not enter the paper-compatible pool. "
                       f"All failed, timed-out and unrun combinations remain in the coverage matrix. ")
    else:
        coverage_text=f"The frozen catalogue contains {len(cat)} intended entries. New execution coverage has not yet been aggregated; current new-campaign counts and selected scores are unavailable. "
    if cohort.get('candidate_ids'):
        coverage_text+=f"The label-blind executable cohort freezes {len(cohort['candidate_ids'])} entries before scoring. "
    coverage_text+=r'The search distribution and locked-winner confirmation are reported separately in the appendix; a larger search may improve numerical matching without resolving historical identity.'
    write('refresh_coverage',r'\noindent '+escape(coverage_text)+'\n')
    complete=[r for r in baseline if r.get('status')=='COMPLETED' and str(r.get('n_trials','50'))=='50' and number(r.get('acc_mean'))!='--']
    if names['baseline'].exists():
        slps=sum(r.get('method')=='spls' for r in complete);lda=sum(r.get('method','').startswith('lda') for r in complete)
        other=len(complete)-slps-lda
        repairs_text=f"The refresh has {slps} complete 50-seed SLPS configurations, {lda} complete 50-seed LDA configurations/control endpoints, and {other} other baseline configurations. Failed/incomplete endpoints remain visible; the appendix reports means/SD and LDA update/termination diagnostics. "
        if not complete:repairs_text+='No new baseline endpoint currently qualifies as a complete measured result. '
    else:repairs_text='The repaired baseline implementations are available; new baseline result aggregation is pending. No additional benchmark result is inferred from implementation tests. '
    repairs_text+='Native 16-by16 MSRA and adapted LDA-to-SC remain separately named adaptations; exact historical LDA-SC remains unavailable.'
    write('refresh_repairs',r'\noindent '+escape(repairs_text)+'\n')
    if gate:
        decision=gate.get('decision','UNAVAILABLE');g4=gate.get('G4_G5_status','UNAVAILABLE')
        count=sum(r.get('status')=='COMPLETED' for r in extension)
        ext_text=f"New graph-repair coverage: {count} complete configuration records; promotion status {decision}; dependent G4/G5 status {g4}. "
        if gate.get('four_benchmark_ACC_gain_pp') is None:ext_text+='The four-benchmark performance target is unavailable. '
    else:ext_text='G1--G3 are implemented and preregistered; no aggregated new graph-repair result is available. G4/G5 have not been promoted, and the four-benchmark target is unavailable. '
    ext_text+='The earlier 0/4 wrong-edge gate is retained as a historical result; it is not replaced by this protocol.'
    write('refresh_extension',r'\noindent '+escape(ext_text)+'\n')

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
                 r'Within one fixed G, native K-means SSE selects one of50 assignments. This is a single assignment with no across-run SD. It does not compete with the mean endpoint. Full method-specific endpoint records are in \texttt{results/submission\_refresh/endpoint\_comparison.csv}; LDA cross-subspace native selection is unavailable.']
    native_rows=[]
    for benchmark in BENCHMARKS:
        row=next((r for r in hist_endpoints if r.get('benchmark')==benchmark and r.get('method')=='ssc' and r.get('endpoint')=='native_best_of_50'),{})
        native_rows.append([benchmark,metric(row,'acc',native=True),metric(row,'nmi',native=True),number(row.get('D_max')),number(row.get('D_mean')),escape(value(row,'selected_seed',default='--')),status_abbreviation(row)])
    appendix.append(table(['SSC data','ACC','NMI',r'$D_{\max}$',r'$D_{\rm mean}$','Seed','Fit'],native_rows,'lrrrrrc',long=True))
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
                    detail=(r'$n='+escape(row.get('n_samples','--'))+'$; '+short_setting(row)+'; '+escape(row.get('solver_status','--'))+
                            r'; $D_{\rm mean}='+number(row.get('D_mean'))+'$; '+escape(row.get('historical_identity','historical identity unverified'))+'.')
                    rows.append(r'\multicolumn{7}{p{\dimexpr\textwidth-6pt\relax}}{\scriptsize '+detail+r'} \\')
        appendix.append(table(['Data / pool','Selected candidate','Paper ACC','Our ACC','Paper NMI','Our NMI',r'$D_{\max}$'],rows,'p{1.6cm}p{3.3cm}rrrrr',long=True))
    appendix.append(r'\subsection{Additional rounding on locked winners}')
    if confirmations:
        rows=[]
        for row in confirmations:
            conf=unpack_json(row.get('confirmation'),{}) or {}
            rows.append([escape(row.get('benchmark','--')),escape(row.get('endpoint','--')).replace(r'mean\_sample\_sd\_50','mean').replace(r'native\_best\_of\_50','native'),
                         number(row.get('selection_acc')),number(row.get('selection_nmi')),metric({**conf,'endpoint':row.get('endpoint')},'acc'),metric({**conf,'endpoint':row.get('endpoint')},'nmi'),escape(row.get('status','--'))])
        appendix.append(table(['Data','Endpoint','Select ACC','Select NMI','Confirm ACC','Confirm NMI','Status'],rows,'llrrrrl',long=True))
        appendix.append(r'Additional seeds check rounding on the same samples and saved G. Winners are not reselected. These intervals/SD do not establish historical identity, unseen-data generalization or label-free model selection.')
    else:appendix.append(r'No completed additional-rounding record is currently aggregated. Winners, if available, remain locked; no stability result is inferred.')
    appendix.append(r'\subsection{Complete baseline repair endpoints}')
    if baseline and any(r.get('method') for r in baseline):
        rows=[]
        for row in baseline:
            if not row.get('method'):continue
            name=METHODS.get(row.get('method'),escape(row.get('method')))
            setting='limit '+str(row['max_iter']) if row.get('max_iter') else str(row.get('config_id','')).split('|')[-1].replace('spls__','')
            rows.append([break_text(row.get('dataset','--')).replace(r'MSRA25\_EBSA\_16x16','MSRA16'),name,break_text(setting),metric(row,'acc'),metric(row,'nmi'),break_text(row.get('status','--'))])
            if row.get('termination_counts'):
                diagnostics=f"Stops: {row['termination_counts']}; failed updates: {row.get('update_failures_total','--')}; zero-success runs: {row.get('no_successful_lda_update_runs','--')}."
                rows.append(r'\multicolumn{6}{p{\dimexpr\textwidth-6pt\relax}}{\scriptsize '+escape(diagnostics)+r'} \\')
        appendix.append(table(['Data','Method','Setting','ACC','NMI','Status'],rows,'p{2.0cm}p{2.1cm}p{2.1cm}rrp{1.7cm}',long=True))
    else:appendix.append(r'Baseline result aggregation is pending or contains no complete endpoint. Implementation tests do not establish benchmark performance.')
    appendix.append(r'\subsection{Coverage, solver qualification and cost}')
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
    if resources:
        ledger=resources.get('ledger',resources)
        entries=ledger.get('entries',[]);charged=sum(float(r.get('charged_cpu_seconds',0)) for r in entries)/3600
        appendix.append(escape(f"Shared ledger charged {charged:.4f} CPU-core hours as of this aggregation. Limit 36, with 2 reserved for final checks; at most 2 single-thread workers and 8 GiB aggregate RSS target. Active reservations: {len(ledger.get('active',{}))}. This is a snapshot, not a prediction of final resource use."))
    else:appendix.append(r'Resource aggregation is not yet available.')
    if gate:appendix.append(r'\paragraph{Graph gate.} '+escape(f"Promotion status: {gate.get('decision','unavailable')}; dependent experiments: {gate.get('G4_G5_status','unavailable')}. Four-benchmark performance conclusion remains unavailable unless complete valid controls and all four datasets exist."))
    plotted=figure(root,joint,papers,closest,cat)
    if plotted:appendix += [r'\begin{figure}[p]\centering\includegraphics[width=\linewidth,height=.86\textheight,keepaspectratio]{figures/subset_acc_nmi.pdf}',
        r'\caption{SSC search distribution for the mean/sample-SD endpoint. Points are complete candidate/configuration records; colors distinguish source/subset families (YaleB colors separate source/resize versions), triangles are adapted rows, crosses are diagnostic rows, stars are published SSC targets and outlines mark the already locked selections within each eligible pool. Eligibility pools and actual locked selections are reported in the tables. More candidates can improve a retrospective match without identifying historical data.}\label{fig:subset-distribution}\end{figure}']
    appendix += [r'\paragraph{Generated-input provenance.} Tables and figures are generated from the authoritative committed CSV/JSON records only. The input hash manifest is \texttt{results/submission\_refresh/report\_input\_manifest.json}. Generated snapshot date: '+escape(date)+'.']
    write('refresh_appendix','\n\n'.join(appendix)+'\n')
    manifest={'schema':'report-inputs-v1','date':date,'inputs':inputs,'outputs':[str(p.relative_to(root)) for p in sorted(out.glob('refresh_*.tex'))],
              'statistical_endpoints_separate':True,'missing_values_are_not_zero':True,'no_score_selection_in_generator':True}
    (refresh/'report_input_manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--date',default='2026-11-10',help='Controlled report snapshot date; no wall-clock inference')
    args=parser.parse_args();generate(args.root,args.date)


if __name__=='__main__':main()
