"""Compact quantitative figures; no representation is changed for display."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import ORDER,METHODS

COLORS={'QSSC':'#6B7280','E1_v2':'#2864A0','E4':'#D17B20','E5':'#318266','E6':'#8457A6'}

def figures(output,points,contrasts,diagnostics):
    folder=output/'figures';folder.mkdir(exist_ok=True);plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','savefig.bbox':'tight'})
    def save(fig,name):
        fig.savefig(folder/(name+'.svg'),metadata={'Date':None,'Creator':'COMP3314 Group 23'});fig.savefig(folder/(name+'.png'),dpi=180);plt.close(fig)
    lookup={(p['benchmark'],p['method'],p['variant'],p['rho']):p for p in points}
    def diag(row):return diagnostics.get(row['point_id'],{}) if row else {}
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
    for ax,metric in zip(axes,['ACC','NMI']):
        for index,method in enumerate(METHODS[1:]):
            rows=[next((c for c in contrasts if c['benchmark']==b and c['method']==method and c['variant']=='default' and c['rho']==.05 and c['comparison']=='QSSC'),None) for b in ORDER];positions=np.arange(8)+(index-1.5)*.18
            values=np.array([r[metric+'_delta_pp'] if r and r['qualified'] else np.nan for r in rows]);lower=np.array([r[metric+'_lower_pp'] if r and r['qualified'] else np.nan for r in rows]);upper=np.array([r[metric+'_upper_pp'] if r and r['qualified'] else np.nan for r in rows]);ax.bar(positions,values,.17,color=COLORS[method],label=method);ax.errorbar(positions,values,yerr=np.maximum(0,np.vstack([values-lower,upper-values])),fmt='none',ecolor='#333333',capsize=2,lw=.7)
            for x,value in zip(positions,values):
                if not np.isfinite(value):ax.annotate('NA',(x,0),xytext=(0,3),textcoords='offset points',ha='center',rotation=90,fontsize=7,color=COLORS[method])
        ax.axhline(0,color='#666666',lw=.7);ax.set_ylabel(f'Δ{metric} (percentage points)');ax.grid(axis='y',alpha=.2)
    axes[0].legend(ncol=4,frameon=False);axes[1].set_xticks(np.arange(8),ORDER);fig.suptitle('Primary effects versus fresh movement-matched QSSC\nNA means unqualified/missing pair; intervals reflect conditional rounding variability',fontsize=11);fig.tight_layout();save(fig,'primary_deltas')
    for metric,label in [('acc_mean','ACC'),('nmi_mean','NMI')]:
        fig,axes=plt.subplots(4,2,figsize=(11,13))
        for ax,b in zip(axes.ravel(),ORDER):
            for method in METHODS:
                rows=[lookup[(b,method,'default',rho)] for rho in [.02,.05,.1,.2]];rows=[r for r in rows if r[metric] is not None and r['actual_movement'] is not None]
                if not rows:continue
                ax.plot([r['actual_movement'] for r in rows],[r[metric] for r in rows],color=COLORS[method],lw=.8,label=method)
                for row in rows:ax.plot(row['actual_movement'],row[metric],marker='s' if row['rho']==.05 else 'o',ms=4,color=COLORS[method],markerfacecolor=COLORS[method] if row['qualified_matched_pair_candidate'] else 'white')
            ax.set_title(b);ax.set_xlabel('Actual ||G-H||F / SH');ax.set_ylabel(label+' (%)');ax.grid(alpha=.2)
        axes[0,0].legend(ncol=3,fontsize=8,frameon=False);fig.suptitle(f'Fixed movement path: {label}; squares denote the .05 primary target\nHollow markers retain uncertified or unmatched finite outputs',fontsize=11);fig.tight_layout();save(fig,'movement_response_'+label.lower())
    fig,ax=plt.subplots(figsize=(10,4));values=[];lo=[];hi=[]
    for b in ORDER:
        data=diag(lookup[(b,'E1_v2','default',.05)]).get('relative_stopping',{});values.append(data.get('observed_fraction_at_or_below',np.nan));lo.append(data.get('certain_inside_fraction_given_gap',np.nan));hi.append(data.get('possible_inside_fraction_given_gap',np.nan))
    values=np.array(values);lo=np.array(lo);hi=np.array(hi);ax.bar(ORDER,100*values,color=COLORS['E1_v2']);ax.errorbar(np.arange(8),100*values,yerr=100*np.maximum(0,np.vstack([values-lo,hi-values])),fmt='none',color='#333333',capsize=3);ax.set_ylabel('Edges at/below relative threshold (%)');ax.set_title('E1_v2 stopping-tube activation at the primary point\nWhiskers show optimizer-error bands from the numerical gap');fig.tight_layout();save(fig,'mechanism_E1_v2')
    fig,ax=plt.subplots(figsize=(10,4));real=[];random=[]
    for b in ORDER:
        data=diag(lookup[(b,'E4','default',.05)]).get('graph',{});real.append(.25*data.get('exchange_mass',np.nan));values=[.25*diag(lookup[(b,'E4',f'perm{s}',.05)]).get('graph',{}).get('exchange_mass',np.nan) for s in [400,401,402]];random.append(float(np.mean(values)))
    ax.bar(np.arange(8)-.18,real,.35,label='Real omitted band',color=COLORS['E4']);ax.bar(np.arange(8)+.18,random,.35,label='Mean of all three row permutations',color='#A9B5C4');ax.set_xticks(np.arange(8),ORDER);ax.set_ylabel('Applied positive exchange / old mass');ax.legend(frameon=False);ax.set_title('E4 intervention magnitude; read with QP eligibility and alignment contrasts');fig.tight_layout();save(fig,'mechanism_E4')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for b in ORDER:
        data=diag(lookup[(b,'E5','default',.05)]);guard=data.get('direction_guard',{});x=guard.get('QSSC_weighted_triangle_slack_over_TV_H');y=guard.get('weighted_triangle_slack_over_TV_H')
        if x is not None and y is not None:axes[0].scatter(x,y,color=COLORS['E5']);axes[0].annotate(b,(x,y),fontsize=8)
        if data:axes[1].scatter(data['global_affine_residual_relative'],data.get('distance_from_same_target_QSSC_relative',np.nan),color=COLORS['E5']);axes[1].annotate(b,(data['global_affine_residual_relative'],data.get('distance_from_same_target_QSSC_relative',np.nan)),fontsize=8)
    limits=axes[0].get_xlim();axes[0].plot(limits,limits,color='#999999',ls='--',lw=.7);axes[0].set(xlabel='QSSC weighted slack / TV(H)',ylabel='E5 weighted slack / TV(H)');axes[1].set(xlabel='Residual from global scale + translation / SH',ylabel='Distance from same-target QSSC / SH');fig.suptitle('E5: lower directional slack versus genuine shape change\nFinite primary outputs; consult coverage for certification and movement matching',fontsize=11);fig.tight_layout();save(fig,'mechanism_E5')
    fig,ax=plt.subplots(figsize=(10,4));q=[];e=[]
    for b in ORDER:
        data=diag(lookup[(b,'E6','default',.05)]).get('directional_floor',{});q.append(data.get('same_target_QSSC_whitened_min_eigenvalue',np.nan));e.append(data.get('whitened_min_eigenvalue',np.nan))
    ax.plot(ORDER,q,'o-',color=COLORS['QSSC'],label='QSSC, same target');ax.plot(ORDER,e,'s-',color=COLORS['E6'],label='E6');ax.axhline(.5,color='#444444',ls='--',label='Guard ηdir=.5');ax.set_ylabel('Minimum anchor-relative symmetric eigenvalue');ax.set_title('E6 primary constraint activation\nFinite outputs; see qualification, dual norms and inactivity diagnostics');ax.legend(frameon=False);fig.tight_layout();save(fig,'mechanism_E6')
