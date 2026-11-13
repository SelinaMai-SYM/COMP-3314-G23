"""Cluster generated samples with Spectral Shrunk Clustering."""
import numpy as np
from sklearn.datasets import make_blobs
from SSC_method import SpectralShrunkClustering


def main():
    X, _ = make_blobs(n_samples=90, centers=3, n_features=4,
                      cluster_std=0.6, random_state=7)
    model = SpectralShrunkClustering(
        n_clusters=3, gamma=1.0, k=5, variant="E8", max_iter=100,
        kmeans_n_init=1, kmeans_random_state=0,
    )
    labels = model.fit_predict(X)
    print("labels:", labels.shape)
    print("F:", model.embedding_.shape, "G:", model.shrunk_.shape)
    print("clusters:", np.unique(labels))


if __name__ == "__main__":
    main()
