"""Deterministic label-free relative-neighbor comparisons from two frozen views."""
import numpy as np
from scipy import sparse
from .convex import row_norm,rowunit


def _neighbors(X,ids,count,block_size=128):
    n=len(X);result=np.empty((n,count),dtype=np.int64);norm=np.sum(X*X,axis=1)
    for start in range(0,n,block_size):
        stop=min(n,start+block_size);dist=norm[start:stop,None]+norm[None,:]-2*(X[start:stop]@X.T);np.maximum(dist,0,out=dist)
        for local,i in enumerate(range(start,stop)):
            row=dist[local];row[i]=np.inf
            part=np.argpartition(row,count-1)[:count];cutoff=np.max(row[part]);strict=np.flatnonzero(row<cutoff);ties=np.flatnonzero(row==cutoff)
            tied=ties[np.argsort(ids[ties],kind='stable')[:count-len(strict)]]
            candidates=np.r_[strict,tied];order=np.lexsort((ids[candidates],row[candidates]));result[i]=candidates[order[:count]]
    return result


def construct(X,U,W,canonical_ids,*,spatial_shape=None,seed=20261111):
    X=np.asarray(X,dtype=float);U=np.asarray(U,dtype=float);ids=np.asarray(canonical_ids,dtype=np.int64)
    if len(ids)!=len(X) or len(set(ids.tolist()))!=len(ids) or len(U)!=len(X):raise ValueError('immutable row identities must be unique and aligned')
    if spatial_shape is not None:
        h,w=map(int,spatial_shape)
        if h*w!=X.shape[1]:raise ValueError('verified spatial shape differs from features')
        parity=np.indices((h,w)).sum(axis=0).ravel()%2;first=np.flatnonzero(parity==0);second=np.flatnonzero(parity==1);mode='VERIFIED_CHECKERBOARD'
    else:
        permutation=np.random.Generator(np.random.PCG64(seed)).permutation(X.shape[1]);first=np.sort(permutation[:X.shape[1]//2]);second=np.sort(permutation[X.shape[1]//2:]);mode='FIXED_BALANCED_FEATURE_SPLIT'
    views=[];norms=[]
    for columns in [first,second]:
        view=X[:,columns].copy();view-=view.mean(axis=1,keepdims=True);length=row_norm(view);norms.append(length);views.append(rowunit(view))
    valid=(norms[0]>1e-12)&(norms[1]>1e-12)&np.any(U!=0,axis=1);pool=np.flatnonzero(valid);pool=pool[np.argsort(ids[pool],kind='stable')]
    nvalid=len(pool);q=min(10,max(0,nvalid-1));Q=min(4*q,max(0,nvalid-1));diagnostics={'view_mode':mode,'spatial_shape':spatial_shape,'feature_split_seed':seed,'n_samples':len(X),'valid_pool_count':nvalid,'zero_U_rows':int(np.sum(~np.any(U!=0,axis=1))),'view1_invalid_rows':int(np.sum(norms[0]<=1e-12)),'view2_invalid_rows':int(np.sum(norms[1]<=1e-12)),'q':q,'Q':Q,'validity_applies_to_all_three_roles':True,'construction_uses_labels':False}
    if nvalid<3:return {'triplets':np.empty((0,3),dtype=np.int64),'diagnostics':{**diagnostics,'selected_triplets':0},'feature_columns':[first,second],'view_norms':np.column_stack(norms),'neighbors':[]}
    neighbors=[pool[_neighbors(view[pool],ids[pool],Q)] for view in views];ranks=[{int(i):{int(j):rank+1 for rank,j in enumerate(neighbors[v][position])} for position,i in enumerate(pool)} for v in range(2)]
    close=[{int(i):set(neighbors[v][position,:q].tolist()) for position,i in enumerate(pool)} for v in range(2)]
    W=sparse.csr_matrix(W);selected=[];mutual_count=0;inversion_count=0;bounded_count=0;cap=np.sin(np.deg2rad(15))
    for i in pool:
        i=int(i);candidates=[j for j in close[0][i]&close[1][i] if i in close[0][j] and i in close[1][j]]
        candidates.sort(key=lambda j:(max(ranks[0][i][j],ranks[1][i][j]),ranks[0][i][j]+ranks[1][i][j],int(ids[j])))
        mutual_count+=len(candidates);begin,end=W.indptr[i:i+2];far=[int(k) for k,w in zip(W.indices[begin:end],W.data[begin:end]) if w>0 and valid[k] and k!=i and int(k) not in ranks[0][i] and int(k) not in ranks[1][i]]
        for j in candidates:
            eligible=[]
            for k in far:
                if k==j:continue
                separation=float(row_norm((U[j]-U[k])[None])[0])
                if separation<=1e-12:continue
                near=float(np.sum((U[i]-U[j])**2));wrong=float(np.sum((U[i]-U[k])**2))
                if not wrong+1e-12<near:continue
                inversion_count+=1;hinge=(.1*separation**2+near-wrong)/(2*separation)
                if hinge<=cap:
                    bounded_count+=1;eligible.append((hinge,int(ids[k]),k))
            if eligible:
                eligible.sort();selected.append((i,int(j),eligible[0][2]));break
    triples=np.asarray(selected,dtype=np.int64).reshape(-1,3)
    reuse={}
    for role,column in [('j',1),('k',2)]:
        values,counts=np.unique(triples[:,column],return_counts=True);total=max(1,int(counts.sum()));reuse[role]={'unique_references':len(values),'maximum_reuse':int(counts.max(initial=0)),'maximum_fraction':float(counts.max(initial=0)/total),'HHI':float(np.sum((counts/total)**2)),'counts_by_original_row_id':{str(int(ids[v])):int(c) for v,c in zip(values,counts)}}
    diagnostics.update(selected_triplets=len(triples),coverage=float(len(triples)/len(X)),mutual_candidates=mutual_count,angular_inversions=inversion_count,bounded_candidates=bounded_count,reference_reuse=reuse)
    return {'triplets':triples,'diagnostics':diagnostics,'feature_columns':[first,second],'view_norms':np.column_stack(norms),'neighbors':neighbors}
