"""Frozen-reference affine hinges, independent of the other two refinements."""
import numpy as np
from .convex import Hinges,Problem,solve,row_norm

def triplet_hinges(U,triplets):
    triplets=np.asarray(triplets,dtype=np.int64).reshape(-1,3)
    if len(triplets)==0:return Hinges.empty(U.shape[1])
    i,j,k=triplets.T;difference=U[k]-U[j];distance=row_norm(difference)
    if np.any(distance<=1e-12):raise ValueError('reference separation is too small')
    margin=.1*distance**2
    beta=(margin+np.sum(U[j]**2,axis=1)-np.sum(U[k]**2,axis=1))/(2*distance)
    return Hinges(i,difference/distance[:,None],beta)

def random_hinges(U,hinges,seed,canonical_ids):
    rng=np.random.Generator(np.random.PCG64(seed));order=sorted(range(len(hinges.anchors)),key=lambda j:canonical_ids[int(hinges.anchors[j])])
    normals=np.empty_like(hinges.normals);redraws=[]
    for t in order:
        while True:
            v=rng.standard_normal(U.shape[1]);length=float(row_norm(v[None])[0])
            if np.isfinite(length) and length>0:break
            redraws.append({'anchor':int(hinges.anchors[t]),'reason':'ZERO_OR_NONFINITE_DIRECTION'})
        normals[t]=v/length
    initial=np.maximum(hinges.apply(U)+hinges.beta,0)
    beta=initial-np.sum(U[hinges.anchors]*normals,axis=1)
    return Hinges(hinges.anchors.copy(),normals,beta),redraws

def solve_relative_neighbors(U,W,gamma,*,hinges,mu=2.,**options):
    return solve(Problem(U,W,gamma,kind='relative_neighbor',hinges=hinges,mu=mu),**options)
