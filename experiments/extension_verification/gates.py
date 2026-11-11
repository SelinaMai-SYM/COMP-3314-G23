"""Predeclared development-only gates; fitting and geometry never import labels."""
import math
import numpy as np
from method_extension.extension_verification.convex import row_norm,rowunit
from .statistics import paired


def radial_geometry(U,G):
    unit=np.any(U!=0,axis=1);delta=G-U;alpha=np.sum(U*delta,axis=1);tangent=delta-alpha[:,None]*U;R=U+tangent;R[~unit]=G[~unit]
    denominator=float(np.sum(delta[unit]**2));angle_mask=unit&(row_norm(G)>1e-12)&(row_norm(R)>1e-12)
    angle=np.full(len(U),np.nan)
    if np.any(angle_mask):
        g=rowunit(G[angle_mask]);r=rowunit(R[angle_mask]);angle[angle_mask]=np.degrees(np.arccos(np.clip(np.sum(g*r,axis=1),-1,1)))
    evaluable=bool(unit.any() and denominator>0 and angle_mask.any())
    geometry={'evaluable':evaluable,'nonzero_anchor_count':int(unit.sum()),'angle_mask_count':int(angle_mask.sum()),'angle_excluded_count':int((~angle_mask).sum()),'movement_energy_denominator':denominator,
        'radial_energy_share':float(np.sum(alpha[unit]**2)/denominator) if denominator>0 else None,
        'inward_radial_energy_share':float(np.sum(np.maximum(-alpha[unit],0)**2)/denominator) if denominator>0 else None,
        'tangential_energy_share':float(np.sum(tangent[unit]**2)/denominator) if denominator>0 else None,
        'RMS_angle_degrees':float(np.sqrt(np.mean(angle[angle_mask]**2))) if angle_mask.any() else None,
        'G_norm_min':float(row_norm(G).min()),'G_norm_max':float(row_norm(G).max()),'R_norm_min':float(row_norm(R).min()),'R_norm_max':float(row_norm(R).max())}
    return R,geometry,{'alpha':alpha,'tangential_displacement':tangent,'angle_mask':angle_mask,'angle_degrees':np.where(angle_mask,angle,0)}


def radial_gate(solver,geometry,ordinary_trials,neutral_trials):
    if ordinary_trials is None or neutral_trials is None:return {'passed':False,'decision':'NOT_EVALUABLE_NUMERICAL_REFERENCE','geometry':geometry}
    acc=paired(neutral_trials,ordinary_trials,'acc');nmi=paired(neutral_trials,ordinary_trials,'nmi')
    conditions={'certified_active_reference':bool(solver['certified'] and solver['numerically_active']),
                'geometry_evaluable':geometry['evaluable'],
                'inward_share_at_least_10_percent':geometry['inward_radial_energy_share'] is not None and geometry['inward_radial_energy_share']>=.1,
                'RMS_angle_at_least_one_degree':geometry['RMS_angle_degrees'] is not None and geometry['RMS_angle_degrees']>=1,
                'adjusted_ACC_lower_positive':acc['lower_pp']>0,'NMI_mean_nonnegative':nmi['delta_pp']>=0}
    passed=all(conditions.values())
    return {'passed':passed,'decision':'PASSED' if passed else 'FAILED' if geometry['evaluable'] else 'NOT_EVALUABLE_GEOMETRY','conditions':conditions,'ACC':acc,'NMI':nmi,'geometry':geometry,'label_use':'Development-only radial-neutralization promotion; two predeclared one-sided contrasts with Bonferroni .025 lower quantile'}


def semantic_gate(triplets,labels):
    labels=np.asarray(labels);triplets=np.asarray(triplets,dtype=int).reshape(-1,3);minimum=max(20,math.ceil(.05*len(labels)));n=len(triplets)
    correct=reverse=0
    if n:
        i,j,k=triplets.T;correct=int(np.sum((labels[i]==labels[j])&(labels[i]!=labels[k])));reverse=int(np.sum((labels[i]==labels[k])&(labels[i]!=labels[j])))
    positive=correct/n if n else None;negative=reverse/n if n else None;ambiguous=(n-correct-reverse)/n if n else None
    conditions={'coverage':n>=minimum,'correct_relation_fraction':positive is not None and positive>=.6,'reversed_relation_fraction':negative is not None and negative<=.1};passed=all(conditions.values())
    return {'passed':passed,'decision':'PASSED' if passed else 'FAILED','conditions':conditions,'triplets':n,'minimum_triplets':minimum,'correct_count':correct,'reversed_count':reverse,'ambiguous_count':n-correct-reverse,'correct_fraction':positive,'reversed_fraction':negative,'ambiguous_fraction':ambiguous,'label_use':'Development-only semantic promotion after triplet identities were frozen; correlated views and reused references are not independent evidence'}
