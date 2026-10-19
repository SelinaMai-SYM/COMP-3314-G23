# Literature check for the SSC mutual-kNN affinity

This note records papers that were opened, or whose publisher records were opened, while preparing one planned change to Chang et al., AAAI 2015. It ranks no method.

The planned change is one component. After the usual SSC spectral embedding, build the shrinkage affinity `W` with a mutual k-nearest-neighbor graph: keep an edge only when each embedded point is among the other's `k` neighbors, put the usual nonnegative Gaussian weight on each kept edge, and freeze `W` before IRLS. Nonnegative fixed weights are what the convexity argument for Eq. (8) uses. Mutual kNN only deletes edges. It does not add a new convergence theorem.

Self-tuning bandwidth (Zelnik-Manor and Perona, NIPS 2004) is already cited by Chang et al. It is not this extension.

Search used for the overlap question: publisher and proceedings pages for convex clustering, spectral clustering, mutual kNN, self-tuning spectral clustering, adaptive or robust graphs, and graph sparsification, plus the query `"mutual k-nearest" OR "mutual kNN" OR "mutual nearest neighbor"` together with convex clustering, spectral shrunk clustering, or pattern shrinking. No paper found in that search applies mutual kNN to SSC's shrinkage weights, or to the convex-clustering fusion penalty under the mutual (AND) rule.

How to read the labels below:

- **Established technique.** The construction already appears in the cited paper.
- **New combination.** Putting that construction on SSC's spectral embedding, with `W` frozen before IRLS, was not found in the papers below.
- **New experimental evaluation.** A later comparison of this combination with SSC would be an experiment. This note does not report one and does not rank methods.
- **Not a methodological innovation.** No new proof is claimed. Eq. (8) stays convex for the same reason as in Chang et al. whenever `W` is nonnegative and held fixed.

## Target paper

**Paper.** Xiaojun Chang, Feiping Nie, Zhigang Ma, Yi Yang, and Xiaofang Zhou. A Convex Formulation for Spectral Shrunk Clustering.

**Year.** 2015.

**Venue.** AAAI Conference on Artificial Intelligence (AAAI 2015).

**Research problem.** Spectral clustering builds its graph in the original space, then embeds. The authors argue that neighborhood relations in that space need not match the low-dimensional embedding.

**Core method.** Compute the normalized-cut embedding `F` from Eq. (4). On `F`, form a kNN Gaussian affinity `W`. Solve

`min_G ||G - F||_{2,1} + gamma * sum_{ij} W_ij ||g_i - g_j||_2`

by IRLS. Cluster the rows of `G` with K-means. The paper states that the objective is convex.

**Relation to SSC.** This is SSC.

**Relevance to our extension.** Eq. (8) already places a fixed nonnegative kNN weight on the spectral embedding. The extension changes only the support of `W` from the paper's kNN rule to mutual kNN, before IRLS. The paper's kNN sentence does not say mutual.

**Verified source.** https://doi.org/10.1609/aaai.v29i1.9606 and the AAAI PDF read for this project. An open copy is listed at https://arxiv.org/abs/1411.6308.

**Potential overlap.** The whole method. The extension does not replace Eq. (8) or the IRLS solver.

**Label.** Established target method. The mutual-kNN support is a new combination relative to this paper, not a new theorem.

## Mutual kNN and graph construction

**Paper.** M. R. Brito, Edgar Chávez, Adolfo J. Quiróz, and J. E. Yukich. Connectivity of the mutual k-nearest-neighbor graph in clustering and outlier detection.

**Year.** 1997.

**Venue.** Statistics & Probability Letters, 35(1):33–42.

**Research problem.** When does connectivity of a mutual kNN graph detect clusters and outliers?

**Core method.** Connect two sample points only if each is among the other's `k` nearest neighbors. Study connectivity of that graph.

**Relation to SSC.** None. SSC is later and uses a shrinkage objective, not connectivity of a mutual kNN graph.

**Relevance to our extension.** This is the standard definition of the mutual kNN graph. Our extension uses that definition on the SSC embedding.

**Verified source.** https://doi.org/10.1016/S0167-7152(96)00213-1

**Potential overlap.** The graph. Not the SSC objective, and not a weight learned inside IRLS.

**Label.** Established technique.

**Paper.** Ulrike von Luxburg. A Tutorial on Spectral Clustering.

**Year.** 2007.

**Venue.** Statistics and Computing, 17(4):395–416.

**Research problem.** How the common spectral clustering pipelines are defined, including the choice of similarity graph.

**Core method.** The tutorial separates three graphs. The kNN graph connects `i` and `j` if either is among the other's `k` neighbors. The mutual kNN graph connects them only if both are. Edges are then weighted by similarity. Section 2.2 states: "The second choice is to connect vertices `v_i` and `v_j` if both `v_i` is among the k-nearest neighbors of `v_j` and `v_j` is among the k-nearest neighbors of `v_i`. The resulting graph is called the mutual k-nearest neighbor graph."

**Relation to SSC.** SSC's affinity sentence ("if `x_i` and `x_j` are k nearest neighbors") matches neither sentence unambiguously. The usual reading in this tutorial, when the word mutual is absent, is the union graph.

**Relevance to our extension.** The extension is the second construction in this section, applied to embedded points, with weights fixed before SSC's IRLS. The tutorial does not discuss SSC or convex clustering.

**Verified source.** https://doi.org/10.1007/s11222-007-9033-z. The mutual-kNN paragraph was read from the tutorial PDF.

**Potential overlap.** Naming and construction of the graph only.

**Label.** Established technique.

**Paper.** Markus Maier, Matthias Hein, and Ulrike von Luxburg. Cluster Identification in Nearest-Neighbor Graphs.

**Year.** 2007.

**Venue.** Algorithmic Learning Theory (ALT). The TCS 2009 reference list gives Springer, pp. 196–210.

**Research problem.** Choose a neighborhood graph so that high-density regions become the connected components.

**Core method.** Finite-sample bounds for mutual kNN and symmetric (union) kNN. The paper's summary: mutual kNN is preferable when the goal is the most significant cluster; symmetric kNN is preferable when many clusters must be identified together, because it is better connected.

**Relation to SSC.** None. Cluster identity here means a connected component, not a shrunk spectral embedding.

**Relevance to our extension.** Directly relevant as a warning. Mutual kNN can remove bridges, and it can also disconnect clusters. That is an empirical risk of the extension, not a reason to call the extension a new graph theorem.

**Verified source.** Author PDF read at https://www.tml.cs.uni-tuebingen.de/team/luxburg/publications/MaiHeiLux07.pdf. Conference listing: https://www-alg.ist.hokudai.ac.jp/~thomas/ALT07/ABS/mhl.html

**Potential overlap.** Mutual versus symmetric kNN. Not SSC.

**Label.** Established technique.

**Paper.** Markus Maier, Ulrike von Luxburg, and Matthias Hein. Influence of graph construction on graph-based clustering measures.

**Year.** 2008.

**Venue.** Advances in Neural Information Processing Systems (NIPS 2008).

**Research problem.** Does the normalized cut depend on whether the graph is a kNN graph or an `r`-neighborhood graph?

**Core method.** The large-sample limit of normalized cut changes with the graph. The paper shows the difference on Gaussian mixtures and on spectral clustering.

**Relation to SSC.** SSC fixes one graph family and then shrinks the embedding. This paper says the graph choice already changes the cut.

**Relevance to our extension.** Replacing union kNN by mutual kNN can change the cut, so it can change `F` if it were applied before the embedding. Our planned component applies it only to the shrinkage weights on an already computed `F`. Those two uses should not be described as the same experiment.

**Verified source.** https://proceedings.neurips.cc/paper_files/paper/2008/file/0a348ede8ac3768875037baca5de6e26-Paper.pdf

**Potential overlap.** Graph choice changes spectral clustering. The 2008 paper compares kNN and `r`-graphs, not SSC shrinkage.

**Label.** Established technique.

**Paper.** Markus Maier, Matthias Hein, and Ulrike von Luxburg. Optimal construction of k-nearest-neighbor graphs for identifying noisy clusters.

**Year.** 2009.

**Venue.** Theoretical Computer Science.

**Research problem.** For level-set clusters, which of mutual kNN and symmetric kNN should be used, and how large should `k` be?

**Core method.** The paper defines `G_mut` by the AND rule and `G_sym` by the OR rule. Bounds say `k` must be large, on the order of `n` rather than `log n`, to maximize identification probability. Mutual kNN helps most when only the strongest cluster is required.

**Relation to SSC.** None.

**Relevance to our extension.** SSC uses `k=5` for every spectral method. Carrying `k=5` unchanged onto a mutual graph can disconnect the embedding graph. The extension's neighbor sweep is an experiment about this known tradeoff, not a new rate.

**Verified source.** https://doi.org/10.1016/j.tcs.2009.01.009. Definitions were read from the author preprint http://www.tml.cs.uni-tuebingen.de/team/luxburg/publications/MaierHeinLuxburg_TCS_preprint.pdf

**Potential overlap.** Mutual kNN as a clustering graph. Not shrinkage and not SSC.

**Label.** Established technique.

**Paper.** Markus Maier, Ulrike von Luxburg, and Matthias Hein. How the result of graph clustering methods depends on the construction of the graph.

**Year.** 2013.

**Venue.** ESAIM: Probability and Statistics, 17:370–418.

**Research problem.** Limits of normalized cut and Cheeger cut on different random geometric graphs.

**Core method.** The same cut has different limit functionals on different graphs, including neighborhood graphs used by spectral clustering.

**Relation to SSC.** Background for why `W` is not an implementation detail.

**Relevance to our extension.** Supports treating mutual kNN as a real change of `W`, while also showing that the underlying comparison of graph constructions is already studied.

**Verified source.** https://doi.org/10.1051/ps/2012001 and https://numdam.org/item/10.1051/ps/2012001.pdf

**Potential overlap.** Graph-construction theory for cuts. Not SSC.

**Label.** Established technique.

**Paper.** Malong Tan, Shichao Zhang, and Lin Wu. Mutual kNN based spectral clustering.

**Year.** 2020 (published online 2 November 2018).

**Venue.** Neural Computing and Applications, 32:6435–6442.

**Research problem.** Spectral clustering is sensitive to a noisy affinity.

**Core method.** The abstract says the method "uses mutual k nearest neighbor to obtain the affinity matrix by removing the influence of noise," then uses that affinity in a self-representation of high-dimensional data and a further normalization. The full PDF was not available from the open Springer page, so the self-representation step is not described here beyond that sentence.

**Relation to SSC.** This is mutual kNN inside ordinary spectral clustering. The abstract does not mention spectral shrunk clustering, pattern shrinking, or an IRLS weight frozen before a convex shrinkage step.

**Relevance to our extension.** Closest published use of mutual kNN as a spectral affinity. It is not the same combination: SSC already has a spectral embedding from some graph, and the extension changes the later shrinkage graph on that embedding. Tan, Zhang, and Wu change the affinity that defines the spectral step itself. Do not cite them as having done the SSC extension.

**Verified source.** https://doi.org/10.1007/s00521-018-3836-z

**Potential overlap.** Mutual kNN affinity for spectral clustering. Not SSC Eq. (8). Overlap is the graph rule only. The Springer page's comparison language was not copied into this note.

**Label.** Established technique for spectral affinities, plus their own self-representation pipeline. Relative to SSC, it is a different combination.

## Self-tuning bandwidth

**Paper.** Lihi Zelnik-Manor and Pietro Perona. Self-Tuning Spectral Clustering.

**Year.** 2004.

**Venue.** Advances in Neural Information Processing Systems (NIPS 2004), pp. 1601–1608.

**Research problem.** A single global scale fails when clusters have different scales, and the number of groups is often unknown.

**Core method.** Local scale `sigma_i`, typically the distance to a neighbor, in the affinity `exp(-||x_i-x_j||^2 / (sigma_i sigma_j))`, plus a rule that reads the number of groups from the eigenvectors.

**Relation to SSC.** Chang et al. already cite this paper in the introduction and in the reference list. Their own affinity still uses one global `delta`.

**Relevance to our extension.** None as a proposed component. Using local scales would be a second change. It is out of scope.

**Verified source.** https://proceedings.neurips.cc/paper/2004/file/40173ea48d9567f1f393b20c855bb40b-Paper.pdf

**Potential overlap.** Bandwidth selection for spectral affinities. Already prior art for SSC, and not mutual kNN.

**Label.** Established technique. Not a new part of this project.

## Spectral clustering foundations used by the baselines

**Paper.** Jianbo Shi and Jitendra Malik. Normalized Cuts and Image Segmentation.

**Year.** 2000.

**Venue.** IEEE Transactions on Pattern Analysis and Machine Intelligence, 22(8):888–905.

**Research problem.** Graph partition that balances cut value against volume.

**Core method.** Normalized cut, solved through a spectral relaxation.

**Relation to SSC.** Chang et al. say that substituting their normalized Laplacian, Eq. (4), into the spectral objective gives normalized cut.

**Relevance to our extension.** The baseline spectral clustering implements that Laplacian. The extension does not change the normalized-cut step that produces `F`.

**Verified source.** https://doi.org/10.1109/34.868688, also listed in the SSC reference list.

**Potential overlap.** The embedding step only.

**Label.** Established technique.

**Paper.** Andrew Y. Ng, Michael I. Jordan, and Yair Weiss. On Spectral Clustering: Analysis and an Algorithm.

**Year.** 2001.

**Venue.** Advances in Neural Information Processing Systems (NIPS 2001), pp. 849–856.

**Research problem.** Make spectral clustering a short, analyzable procedure.

**Core method.** Eigenvectors of a normalized affinity, row normalization, then K-means.

**Relation to SSC.** SSC's written spectral step is the trace objective with Eq. (4). It does not include the Ng–Jordan–Weiss row normalization. The baseline follows the SSC equations on that point.

**Relevance to our extension.** None beyond the definition of spectral embedding.

**Verified source.** https://proceedings.neurips.cc/paper_files/paper/2001/file/801272ee79cfde7fa5960571fee36b9b-Paper.pdf

**Potential overlap.** A different spectral pipeline. Not used as the SSC baseline.

**Label.** Established technique.

## Convex clustering and fixed nonnegative weights

**Paper.** Toby Hocking, Jean-Philippe Vert, Francis Bach, and Armand Joulin. Clusterpath: an Algorithm for Clustering using Convex Fusion Penalties.

**Year.** 2011.

**Venue.** International Conference on Machine Learning (ICML 2011), pp. 745–752.

**Research problem.** Hierarchical clustering as a convex fusion path.

**Core method.** A convex relaxation that fuses points through a penalty on differences of centroids. The ML anthology abstract describes a family of convex objectives with a geometric interpretation and efficient algorithms.

**Relation to SSC.** Both use a convex fusion-style penalty on pairs. Clusterpath fuses the observations themselves. SSC shrinks spectral embeddings with weights `W_ij` and an `l_{2,1}` fidelity term. Clusterpath is not spectral shrunk clustering.

**Relevance to our extension.** Historical convex clustering. The ICML page that was opened does not describe a mutual kNN weight.

**Verified source.** https://mlanthology.org/icml/2011/hocking2011icml-clusterpath/ and the citation posted by the authors' Clusterpath software at https://clusterpath.r-forge.r-project.org/

**Potential overlap.** Convex fusion penalties. Not mutual kNN on an SSC embedding. The ICML PDF was not re-derived equation by equation in this pass; the bibliographic record and abstract were.

**Label.** Established technique in convex clustering.

**Paper.** Eric C. Chi and Kenneth Lange. Splitting Methods for Convex Clustering.

**Year.** 2015.

**Venue.** Journal of Computational and Graphical Statistics, 24(4):994–1013.

**Research problem.** Compute the convex clustering path and choose its weights.

**Core method.** ADMM and AMA for the sum-of-norms convex clustering model. Section 7.1 of the arXiv copy fixes the weights before the path is computed:

"We set the value of the weight between the ith and jth points to be `w_ij = iota_k{i,j} exp(-phi ||x_i - x_j||^2)`, where `iota_k{i,j}` is 1 if `j` is among `i`'s k-nearest-neighbors or vice versa and 0 otherwise."

The indicator is the union (OR) kNN graph, not the mutual (AND) graph. `phi = 0` gives constant weights on those edges.

**Relation to SSC.** This is the closest weight construction for a convex fusion penalty. It is still not SSC: the variables are cluster centroids of the original points, the penalty is a sum of norms along the regularization path, and the graph is union kNN. Chang et al. put Gaussian kNN weights on the spectral embedding inside Eq. (8).

**Relevance to our extension.** Chi and Lange already treat a sparse kNN Gaussian weight as something chosen before convex optimization, which is the same timing as freezing `W` before IRLS. They do not use the mutual rule. Quoting them as having done the extension would be wrong. The honest relation is: union-kNN Gaussian weights for convex clustering are prior art; mutual kNN on the SSC embedding is a different graph on a different objective.

**Verified source.** https://doi.org/10.1080/10618600.2014.948181 and the text read from https://arxiv.org/pdf/1304.0499

**Potential overlap.** Fixed sparse Gaussian weights in a convex clustering penalty. The overlap stops at the OR neighborhood and at a different objective.

**Label.** Established technique. Not the mutual-kNN SSC combination.

**Paper.** Defeng Sun, Kim-Chuan Toh, and Yancheng Yuan. Convex Clustering: Model, Theoretical Guarantee and Efficient Algorithm.

**Year.** 2021.

**Venue.** Journal of Machine Learning Research, 22:1–32.

**Research problem.** Recovery guarantees for weighted convex clustering, and a large-scale solver.

**Core method.** Sufficient conditions for perfect recovery of the weighted sum-of-norms model, plus a semismooth Newton augmented Lagrangian method. In practice they build the edge set by k-nearest neighbors. Remark 6 says the theoretical support only needs positive weights inside true clusters, and that a kNN rule is the practical substitute because the clusters are unknown.

**Relation to SSC.** Weighted convex clustering again. The JMLR paper does not discuss spectral shrunk clustering or mutual kNN. Its bibliography attributes the model to Pelckmans et al. (2005), Lindsten et al. (2011), and Hocking et al. (2011); those first two primary documents were not opened (see the last section).

**Relevance to our extension.** Confirms that kNN support for a convex fusion weight is already a standard, theoretically discussed choice. It does not occupy the mutual-kNN-on-`F` variant of SSC.

**Verified source.** https://jmlr.org/papers/v22/18-694.html

**Potential overlap.** kNN-weighted convex clustering. Not mutual kNN and not SSC.

**Label.** Established technique and later theory for weighted convex clustering.

## Adaptive and robust graphs

**Paper.** Feiping Nie, Xiaoqian Wang, and Heng Huang. Clustering and Projected Clustering with Adaptive Neighbors.

**Year.** 2014.

**Venue.** ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD 2014), pp. 977–986 in the SSC reference list.

**Research problem.** A similarity built before clustering need not be the similarity that clustering wants.

**Core method.** Learn a sparse neighbor assignment and the clustering together. A rank constraint on the Laplacian forces the learned graph to have `k` connected components. A projected version also learns a linear map.

**Relation to SSC.** Both authors include Feiping Nie, and SSC cites this KDD paper. CAN learns the graph during clustering. SSC builds `W` from the embedding and then runs IRLS with that weight.

**Relevance to our extension.** CAN is the alternative we are not implementing. Moving `W` inside the iteration would need its own argument that Eq. (8) remains convex. Freezing a mutual kNN weight avoids that change. Adaptive neighbors are not mutual kNN.

**Verified source.** https://doi.org/10.1145/2623330.2623726

**Potential overlap.** Learning a graph for clustering. The optimization is different, and the neighbors are adaptive probabilities rather than a mutual kNN support.

**Label.** Established technique. A different combination from the planned extension.

**Paper.** Feiping Nie, Xiaoqian Wang, Michael I. Jordan, and Heng Huang. The Constrained Laplacian Rank Algorithm for Graph-Based Clustering.

**Year.** 2016.

**Venue.** AAAI Conference on Artificial Intelligence (AAAI 2016).

**Research problem.** A bad input graph makes graph clustering bad, and a spectral step is still required after the graph is built.

**Core method.** Learn a new affinity whose Laplacian has rank `n - k`, so the graph has `k` components. `L1` and `L2` versions are given. Clustering is read from the components.

**Relation to SSC.** Another learned graph from the same line of work. It is not a post-processing of an SSC embedding.

**Relevance to our extension.** CLR changes the graph while clustering. The planned SSC change does not. Citing CLR as mutual kNN would be incorrect.

**Verified source.** https://doi.org/10.1609/aaai.v30i1.10302

**Potential overlap.** Graph learning for clustering. No mutual kNN rule and no SSC shrinkage term were stated on the AAAI page that was read.

**Label.** Established technique.

**Paper.** Aleksandar Bojchevski, Yves Matkovic, and Stephan Günnemann. Robust Spectral Clustering for Noisy Data: Modeling Sparse Corruptions Improves Latent Embeddings.

**Year.** 2017.

**Venue.** ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD 2017).

**Research problem.** Spectral clustering changes when the similarity graph is corrupted.

**Core method.** Decompose the similarity into a clean graph and a sparse corruption, and learn that decomposition jointly with the spectral embedding. The paper gives algorithms for the unnormalized and normalized spectral objectives.

**Relation to SSC.** Both want a spectral embedding that is less fragile. RSC changes the graph and the embedding together. SSC keeps the first embedding and shrinks it.

**Relevance to our extension.** A robust graph can be learned; mutual kNN is a fixed filter instead. The KDD paper does not apply that filter to SSC.

**Verified source.** https://doi.org/10.1145/3097983.3098156 and the author PDF https://abojchevski.github.io/assets/pdf/paper_rsc.pdf

**Potential overlap.** Robustness of spectral graphs. Different mechanism.

**Label.** Established technique.

## What was checked and not found

No opened paper applies mutual kNN, or a reliability weight defined by mutual neighborhood, to SSC Eq. (8) or to the IRLS shrinkage weights. Chi and Lange (2015) are the nearest convex-clustering citation, and their displayed weight uses the OR neighborhood. Tan, Zhang, and Wu (2020) are the nearest mutual-kNN spectral citation, and their abstract places mutual kNN on the affinity of spectral clustering, not on an SSC shrinkage step.

The extension should be described as a new combination of an established graph with SSC, together with a new experimental comparison if that comparison is actually run. It should not be described as a new convexity proof or as an unoccupied theoretical gap that mutual kNN had never been studied.

## Bibliographic entries not used as verified method sources

These names appeared in searches or in bibliographies of papers that were opened. The primary paper was not opened, so they are not given method summaries and are not dependencies of the extension claim.

- K. Pelckmans, J. De Brabanter, J. Suykens, and B. De Moor. Convex clustering shrinkage. PASCAL Workshop on Statistics and Optimization of Clustering, 2005. Printed in the JMLR 2021 bibliography. The workshop paper was not retrieved.
- F. Lindsten, H. Ohlsson, and L. Ljung. Clustering using sum-of-norms regularization: With application to particle filter output computation. IEEE Statistical Signal Processing Workshop, 2011, pp. 201–204, as printed in that bibliography. The IEEE paper was not retrieved.
- C. Zhu, H. Xu, C. L. Leng, and S. C. Yan. Convex optimization procedure for clustering: Theoretical revisit. Advances in Neural Information Processing Systems 27, pp. 1619–1627, 2014. Printed in the same bibliography. The NIPS paper was not opened.
- A. Panahi, D. Dubhashi, F. D. Johansson, and C. Bhattacharyya. Clustering by sum of norms: Stochastic incremental algorithm, convergence and cluster recovery. ICML 2017, PMLR volume 70, pp. 2769–2777. Printed in the same bibliography. The paper was not opened.
- K. M. Tan and D. Witten. Statistical properties of convex clustering. Electronic Journal of Statistics, 9(2):2324, 2015, as printed in that bibliography. The paper was not opened.
- Spielman and Srivastava, graph sparsification by effective resistances, was considered for the sparsification section. The primary paper was not opened, so no year or DOI is stated here.
- A robust-graph-learning paper associated in memory with Kang, Pan, Hoi, and Xu was considered and not opened. No bibliographic line is given.
- A search snippet titled "Data Clustering Based on Community Structure in Mutual k-Nearest Neighbor Graph," DOI `10.1109/tsp.2018.8441226`, did not yield confirmed authors and a venue page. It is omitted.
- R. A. Jarvis and E. A. Patrick, IEEE Transactions on Computers, 1973, shared nearest neighbors, appeared only as a reference inside another paper's bibliography. The primary page was not opened.
- Yang, Xu, Nie, Yan, and Zhuang, IEEE Transactions on Image Processing, 2010, 19(10):2761–2773, "Image clustering using local discriminant models and global integration," is printed in the SSC reference list. SSC points to it, together with Wu and Schölkopf, as a local-learning Laplacian. The TIP paper was not read, so LLC was implemented from Wu and Schölkopf only.
- Jialu Liu, Chi Wang, Marina Danilevsky, and Jiawei Han, "Large-scale spectral clustering on graphs," IJCAI 2013, is printed in the SSC reference list. SSC describes it as compressing the graph to a sparse bipartite graph. The IJCAI paper was not read. It is recorded here only so the sparsification citation is not invented and is not treated as mutual kNN.

Hou, Nie, Jiao, Zhang, and Wu, Information Processing & Management, 2013, DOI `10.1016/j.ipm.2013.01.004`, was verified at the publisher and DBLP records. The optimization section was not available, so SPLS is not implemented and is not used as a method source for the extension. The abstract's name for the method is SLPS. SSC writes SPLS.
