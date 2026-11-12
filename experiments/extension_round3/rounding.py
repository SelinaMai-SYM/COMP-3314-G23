"""Label-free Lloyd fits with replayable native or anchor-generated starts."""
import warnings
import numpy as np
from sklearn.cluster import KMeans,kmeans_plusplus
from sklearn.exceptions import ConvergenceWarning


def anchor_indices(H,K):
    x=np.array(H,dtype=np.float64,order='C',copy=True);x-=x.mean(axis=0)
    return np.asarray([kmeans_plusplus(x,n_clusters=K,random_state=s)[1] for s in range(50)],dtype=np.int64)


def fit(G,K,seed,*,indices=None):
    initial=[]
    def initialize(x,n_clusters,random_state):
        centers,rows=kmeans_plusplus(x,n_clusters=n_clusters,random_state=random_state)
        initial.extend(rows.tolist());return centers
    init=initialize if indices is None else np.asarray(G)[indices].copy()
    model=KMeans(n_clusters=K,init=init,n_init=1,algorithm='lloyd',random_state=seed,max_iter=300,tol=1e-4)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning);model.fit(np.asarray(G,dtype=np.float64))
    return {'labels':model.labels_,'centers':model.cluster_centers_,'initial_indices':np.asarray(initial if indices is None else indices,dtype=np.int64),'inertia':float(model.inertia_),'iterations':int(model.n_iter_),'warnings':[str(w.message) for w in caught]}
