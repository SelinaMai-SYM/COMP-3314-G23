"""Compact quantitative figures; no representation is changed for display."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import ORDER,METHODS

COLORS={'QSSC':'#6B7280','E1_v2':'#2864A0','E4':'#D17B20','E5':'#318266','E6':'#8457A6'}

def figures(output,points,contrasts,diagnostics):
    folder=output/'figures';folder.mkdir(exist_ok=True);plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'comp3314-extension-round2-v1','savefig.bbox':'tight'})
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
                qualified=[r for r in rows if r['qualified_matched_pair_candidate']];ax.plot([r['actual_movement'] for r in qualified],[r[metric] for r in qualified],color=COLORS[method],lw=.8,label=method)
                for row in rows:ax.plot(row['actual_movement'],row[metric],marker='s' if row['rho']==.05 else 'o',ms=4,color=COLORS[method],markerfacecolor=COLORS[method] if row['qualified_matched_pair_candidate'] else 'white')
            ax.set_title(b);ax.set_xlabel('Actual ||G-H||F / SH');ax.set_ylabel(label+' (%)');ax.grid(alpha=.2)
        axes[0,0].legend(ncol=3,fontsize=8,frameon=False);fig.suptitle(f'Fixed movement path: {label}; squares denote the .05 primary target\nLines join qualified matched points; hollow markers retain other finite outputs',fontsize=11);fig.tight_layout();save(fig,'movement_response_'+label.lower())
    fig,ax=plt.subplots(figsize=(10,4));values=[];lo=[];hi=[]
    for b in ORDER:
        data=diag(lookup[(b,'E1_v2','default',.05)]).get('relative_stopping',{});values.append(data.get('observed_positive_anchor_fraction',np.nan));lo.append(data.get('certain_inside_positive_anchor_fraction',np.nan));hi.append(data.get('possible_inside_positive_anchor_fraction',np.nan))
    values=np.array(values,dtype=float);lo=np.array(lo,dtype=float);hi=np.array(hi,dtype=float);bars=ax.bar(ORDER,100*values,color=COLORS['E1_v2'])
    for bar,b in zip(bars,ORDER):
        if not lookup[(b,'E1_v2','default',.05)]['qualified_matched_pair_candidate']:bar.set_facecolor('white');bar.set_edgecolor(COLORS['E1_v2']);bar.set_hatch('///')
    ax.errorbar(np.arange(8),100*values,yerr=100*np.maximum(0,np.vstack([values-lo,hi-values])),fmt='none',color='#333333',capsize=3);ax.set_ylabel('Positive-anchor edges at/below threshold (%)');ax.set_title('E1_v2 primary stopping tubes; coincident anchor edges excluded\nWhiskers: gap-based bands; hatching: unqualified finite output');fig.tight_layout();save(fig,'mechanism_E1_v2')
    fig,ax=plt.subplots(figsize=(10,4));real=[];random=[]
    for b in ORDER:
        data=diag(lookup[(b,'E4','default',.05)]).get('graph',{});real.append(.25*data.get('exchange_mass',np.nan));values=[.25*diag(lookup[(b,'E4',f'perm{s}',.05)]).get('graph',{}).get('exchange_mass',np.nan) for s in [400,401,402]];random.append(float(np.mean(values)))
    real_bars=ax.bar(np.arange(8)-.18,real,.35,label='Real omitted band',color=COLORS['E4']);control_bars=ax.bar(np.arange(8)+.18,random,.35,label='Mean of all three row permutations',color='#A9B5C4')
    for i,b in enumerate(ORDER):
        if not lookup[(b,'E4','default',.05)]['graph_eligible']:ax.annotate('W0 fallback',(i-.18,0),xytext=(0,3),textcoords='offset points',ha='center',rotation=90,fontsize=7,color=COLORS['E4'])
        if not all(lookup[(b,'E4',f'perm{s}',.05)]['graph_eligible'] for s in [400,401,402]):control_bars[i].set_hatch('///');control_bars[i].set_edgecolor('#68788E')
    ax.set_xticks(np.arange(8),ORDER);ax.set_ylabel('Applied positive exchange / old mass');ax.legend(frameon=False);ax.set_title('E4 applied exchange; default W0 fallbacks are labelled\nHatching: control group includes an ineligible QP');fig.tight_layout();save(fig,'mechanism_E4')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    offsets={'AR':(-13,9),'MSRA50':(6,-7),'ORL':(20,-10),'BinAlpha':(-18,11),'JAFFE':(7,-3),'UMIST':(5,0),'YaleB':(5,3),'USPS':(-4,7)}
    for b in ORDER:
        data=diag(lookup[(b,'E5','default',.05)]);guard=data.get('direction_guard',{});x=guard.get('QSSC_weighted_triangle_slack_over_TV_H');y=guard.get('weighted_triangle_slack_over_TV_H')
        face=COLORS['E5'] if data.get('QSSC_comparison_qualified_and_matched') else 'white'
        if x is not None and y is not None:axes[0].scatter(x,y,facecolors=face,edgecolors=COLORS['E5']);axes[0].annotate(b,(x,y),xytext=offsets[b],textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'-','lw':.5,'color':'#666666'} if b=='ORL' else None)
        if data:axes[1].scatter(data['global_affine_residual_relative'],data.get('distance_from_same_target_QSSC_relative',np.nan),facecolors=face,edgecolors=COLORS['E5']);axes[1].annotate(b,(data['global_affine_residual_relative'],data.get('distance_from_same_target_QSSC_relative',np.nan)),xytext=(4,3),textcoords='offset points',fontsize=8)
    limits=axes[0].get_xlim();axes[0].plot(limits,limits,color='#999999',ls='--',lw=.7);axes[0].set(xlabel='QSSC weighted slack / TV(H)',ylabel='E5 weighted slack / TV(H)');axes[1].set(xlabel='Residual from global scale + translation / SH',ylabel='Distance from same-target QSSC / SH');axes[1].margins(x=.16,y=.12);fig.suptitle('E5: directional slack and shape change relative to QSSC\nFinite primary outputs; hollow markers denote unqualified pairs',fontsize=11);fig.tight_layout();save(fig,'mechanism_E5')
    fig,ax=plt.subplots(figsize=(10,4));q=[];e=[]
    for b in ORDER:
        data=diag(lookup[(b,'E6','default',.05)]).get('directional_floor',{});q.append(data.get('same_target_QSSC_whitened_min_eigenvalue',np.nan));e.append(data.get('whitened_min_eigenvalue',np.nan))
    ax.plot(ORDER,q,'o-',color=COLORS['QSSC'],label='QSSC, same target');ax.plot(ORDER,e,'s-',color=COLORS['E6'],label='E6')
    for i,b in enumerate(ORDER):
        if not lookup[(b,'QSSC','default',.05)]['qualified_matched_pair_candidate']:ax.plot(i,q[i],'o',markerfacecolor='white',markeredgecolor=COLORS['QSSC'])
        if not lookup[(b,'E6','default',.05)]['qualified_matched_pair_candidate']:ax.plot(i,e[i],'s',markerfacecolor='white',markeredgecolor=COLORS['E6'])
    ax.axhline(.5,color='#444444',ls='--',label='Guard ηdir=.5');ax.set_ylabel('Minimum anchor-relative symmetric eigenvalue');ax.set_title('E6 primary constraint activation\nFinite outputs; hollow markers are unqualified; see dual norms and inactivity bounds');ax.legend(frameon=False);fig.tight_layout();save(fig,'mechanism_E6')
